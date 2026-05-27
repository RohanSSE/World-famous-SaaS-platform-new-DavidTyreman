"""
Automatic AI knowledge index maintenance.

- Fingerprints Rag_doc (+ optional legacy utils) files
- Rebuilds Elasticsearch `ai_knowledge` when content changes or index is missing
- Triggered on: Django startup, Celery Beat, before retrieval, manual command
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from django.conf import settings

from .ai_knowledge_config import (
    AI_KNOWLEDGE_FILES,
    AI_KNOWLEDGE_INDEX_NAME,
    INCLUDE_LEGACY_UTILS_TXT,
    RAG_DOC_DIR,
    get_knowledge_file_path,
)
from .rag_doc_loader import discover_rag_doc_files, relative_rag_path

logger = logging.getLogger(__name__)

STATE_STATUS_IDLE = "idle"
STATE_STATUS_BUILDING = "building"
STATE_STATUS_READY = "ready"
STATE_STATUS_FAILED = "failed"

BUILD_STALE_MINUTES = 45


def _state_file_path() -> Path:
    try:
        custom = getattr(settings, "AI_KNOWLEDGE_STATE_FILE", None)
        if custom:
            return Path(custom)
        return Path(settings.BASE_DIR) / "data" / "ai_knowledge_index_state.json"
    except Exception:
        from .ai_knowledge_config import BACKEND_DIR

        return BACKEND_DIR / "data" / "ai_knowledge_index_state.json"


def _ensure_state_dir() -> None:
    _state_file_path().parent.mkdir(parents=True, exist_ok=True)


def load_index_state() -> Dict[str, Any]:
    path = _state_file_path()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Could not read knowledge index state: %s", e)
        return {}


def save_index_state(state: Dict[str, Any]) -> None:
    _ensure_state_dir()
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    _state_file_path().write_text(
        json.dumps(state, indent=2),
        encoding="utf-8",
    )


def compute_knowledge_fingerprint() -> str:
    """
    SHA-256 over all knowledge source paths, sizes, and mtimes.
    Changes when files are added, removed, or edited.
    """
    hasher = hashlib.sha256()

    for file_path, category in discover_rag_doc_files():
        try:
            stat = file_path.stat()
        except OSError:
            continue
        rel = relative_rag_path(file_path)
        hasher.update(
            f"rag:{category}:{rel}:{stat.st_size}:{int(stat.st_mtime_ns)}".encode("utf-8")
        )

    if INCLUDE_LEGACY_UTILS_TXT:
        for filename, source in AI_KNOWLEDGE_FILES:
            path = get_knowledge_file_path(filename)
            if not path.exists():
                continue
            stat = path.stat()
            hasher.update(
                f"legacy:{source}:{filename}:{stat.st_size}:{int(stat.st_mtime_ns)}".encode(
                    "utf-8"
                )
            )

    return hasher.hexdigest()


def elasticsearch_index_exists() -> bool:
    try:
        from document.utils.elasticsearch_service import ElasticsearchService

        es = ElasticsearchService()
        return es._index_exists(AI_KNOWLEDGE_INDEX_NAME)
    except Exception as e:
        logger.warning("Could not check ES index %s: %s", AI_KNOWLEDGE_INDEX_NAME, e)
        return False


def _is_build_stale(state: Dict[str, Any]) -> bool:
    if state.get("status") != STATE_STATUS_BUILDING:
        return False
    started = state.get("build_started_at")
    if not started:
        return True
    try:
        started_dt = datetime.fromisoformat(started.replace("Z", "+00:00"))
        if started_dt.tzinfo is None:
            started_dt = started_dt.replace(tzinfo=timezone.utc)
        age_min = (datetime.now(timezone.utc) - started_dt).total_seconds() / 60
        return age_min > BUILD_STALE_MINUTES
    except (ValueError, TypeError):
        return True


def needs_rebuild(force: bool = False) -> Tuple[bool, str]:
    """
    Return (should_rebuild, reason).
    """
    if force:
        return True, "force"

    if not discover_rag_doc_files() and not INCLUDE_LEGACY_UTILS_TXT:
        return False, "no_source_files"

    fingerprint = compute_knowledge_fingerprint()
    state = load_index_state()

    if state.get("status") == STATE_STATUS_BUILDING and not _is_build_stale(state):
        return False, "build_in_progress"

    if not elasticsearch_index_exists():
        return True, "index_missing"

    if state.get("fingerprint") != fingerprint:
        return True, "content_changed"

    if state.get("status") == STATE_STATUS_FAILED:
        return True, "previous_build_failed"

    return False, "up_to_date"


def mark_build_started(fingerprint: str) -> None:
    state = load_index_state()
    state.update(
        {
            "status": STATE_STATUS_BUILDING,
            "fingerprint_pending": fingerprint,
            "build_started_at": datetime.now(timezone.utc).isoformat(),
            "error": None,
        }
    )
    save_index_state(state)


def mark_build_finished(
    success: bool,
    message: str,
    fingerprint: str,
    chunk_count: int = 0,
) -> None:
    state = load_index_state()
    state.update(
        {
            "status": STATE_STATUS_READY if success else STATE_STATUS_FAILED,
            "fingerprint": fingerprint if success else state.get("fingerprint"),
            "chunk_count": chunk_count if success else state.get("chunk_count", 0),
            "last_built_at": datetime.now(timezone.utc).isoformat() if success else state.get(
                "last_built_at"
            ),
            "last_message": message,
            "error": None if success else message,
            "build_started_at": None,
        }
    )
    save_index_state(state)


def run_build_with_state(force: bool = False) -> Tuple[bool, str]:
    """Run full index build and persist state. Used by Celery and management command."""
    from .build_ai_knowledge_index import run_build

    should, reason = needs_rebuild(force=force)
    if not should and not force:
        return True, f"Index up to date ({reason})."

    fingerprint = compute_knowledge_fingerprint()
    mark_build_started(fingerprint)

    try:
        success, message = run_build()
    except Exception as e:
        logger.exception("AI knowledge build crashed")
        mark_build_finished(False, str(e), fingerprint)
        return False, str(e)

    chunk_count = 0
    if success:
        import re

        m = re.search(r"Indexed (\d+)", message)
        if m:
            chunk_count = int(m.group(1))

    mark_build_finished(success, message, fingerprint, chunk_count=chunk_count)
    return success, message


def enqueue_rebuild(force: bool = False) -> bool:
    """Queue Celery rebuild task. Returns True if enqueued."""
    if not getattr(settings, "AI_KNOWLEDGE_AUTO_INDEX", True):
        return False

    should, reason = needs_rebuild(force=force)
    if not should and not force:
        logger.debug("AI knowledge index skip enqueue: %s", reason)
        return False

    try:
        from user_sessions.tasks import rebuild_ai_knowledge_index_task

        rebuild_ai_knowledge_index_task.delay(force=force)
        logger.info("Enqueued AI knowledge index rebuild (reason=%s, force=%s)", reason, force)
        return True
    except Exception as e:
        logger.warning("Celery enqueue failed (%s)", e)
        # Avoid blocking runserver when Redis/Celery is not running (local dev)
        if getattr(settings, "DEBUG", False) or os.environ.get("DJANGO_SKIP_KNOWLEDGE_AUTO") == "1":
            return False
        success, msg = run_build_with_state(force=force)
        return success


def ensure_index_current(
    async_build: bool = True,
    force: bool = False,
) -> Tuple[bool, str]:
    """
    Ensure ai_knowledge index matches Rag_doc content.
    - async_build=True → Celery task (default)
    - async_build=False → blocking build in current process
    """
    if not getattr(settings, "AI_KNOWLEDGE_AUTO_INDEX", True):
        return True, "auto_index_disabled"

    should, reason = needs_rebuild(force=force)
    if not should:
        return True, reason

    if async_build:
        enqueued = enqueue_rebuild(force=force)
        return enqueued, f"enqueued:{reason}"

    return run_build_with_state(force=force)


def should_run_startup_hook() -> bool:
    """Avoid duplicate hooks during migrate / runserver parent process."""
    import sys

    if not getattr(settings, "AI_KNOWLEDGE_AUTO_INDEX_ON_STARTUP", True):
        return False
    if os.environ.get("DJANGO_SKIP_KNOWLEDGE_AUTO") == "1":
        return False
    argv = sys.argv
    skip_commands = {
        "migrate",
        "makemigrations",
        "collectstatic",
        "test",
        "shell",
        "build_ai_knowledge",
    }
    if any(cmd in argv for cmd in skip_commands):
        return False
    if "runserver" in argv and os.environ.get("RUN_MAIN") != "true":
        return False
    return True
