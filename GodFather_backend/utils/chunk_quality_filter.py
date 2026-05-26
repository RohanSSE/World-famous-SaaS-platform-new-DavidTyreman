"""
Index-time chunk quality gate — removes pollution before embedding (Reliable Intelligence v1).
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Tuple

from django.conf import settings

logger = logging.getLogger(__name__)

# Title/file patterns that indicate meta/admin noise (not strategic knowledge)
META_TITLE_PATTERNS = (
    re.compile(r"source\s+mapping", re.I),
    re.compile(r"categorization\s+break", re.I),
    re.compile(r"index\s+state", re.I),
    re.compile(r"^overview$", re.I),
    re.compile(r"debug", re.I),
    re.compile(r"^\s*logs?\s*$", re.I),
)


def _repetitive_ratio(text: str) -> float:
    """High ratio = mostly repeated tokens (low information)."""
    words = re.findall(r"[a-z0-9']+", (text or "").lower())
    if len(words) < 8:
        return 0.0
    unique = len(set(words))
    return 1.0 - (unique / len(words))


def _chunk_category(chunk: Dict[str, Any]) -> str:
    meta = chunk.get("metadata") or {}
    return (meta.get("category") or chunk.get("category") or "").lower().strip()


def _chunk_text(chunk: Dict[str, Any]) -> str:
    return (chunk.get("text") or "").strip()


def should_reject_chunk(chunk: Dict[str, Any]) -> Tuple[bool, str]:
    """Return (reject, reason)."""
    min_chars = int(getattr(settings, "MIN_CHUNK_CHARS", 120))
    max_rep = float(getattr(settings, "MAX_CHUNK_REPETITIVE_RATIO", 0.4))
    excluded = set(
        getattr(
            settings,
            "EXCLUDED_CHUNK_CATEGORIES",
            ["admin", "meta", "logs", "debug"],
        )
    )

    text = _chunk_text(chunk)
    if len(text) < min_chars:
        return True, "too_short"

    cat = _chunk_category(chunk)
    if cat in excluded:
        return True, "excluded_category"

    meta = chunk.get("metadata") or {}
    title = (meta.get("title") or "").strip()
    file_ref = (meta.get("file") or meta.get("path") or "").lower()

    for pat in META_TITLE_PATTERNS:
        if pat.search(title) or pat.search(file_ref):
            return True, "meta_title"

    if any(x in file_ref for x in ("/admin/", "\\admin\\", "debug", "meta/")):
        return True, "meta_path"

    rep = _repetitive_ratio(text)
    if rep > max_rep:
        return True, f"repetitive_{rep:.2f}"

    return False, ""


def filter_chunks_for_index(chunks: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """Filter chunks before embedding; returns (kept, rejection_stats)."""
    kept: List[Dict[str, Any]] = []
    stats: Dict[str, int] = {"rejected": 0, "kept": 0}

    for chunk in chunks:
        reject, reason = should_reject_chunk(chunk)
        if reject:
            stats["rejected"] = stats.get("rejected", 0) + 1
            stats[reason] = stats.get(reason, 0) + 1
            logger.debug("Rejected chunk %s: %s", chunk.get("chunk_id"), reason)
        else:
            kept.append(chunk)

    stats["kept"] = len(kept)
    logger.info(
        "Chunk quality filter: kept=%s rejected=%s (%s)",
        stats["kept"],
        stats["rejected"],
        {k: v for k, v in stats.items() if k not in ("kept", "rejected")},
    )
    return kept, stats
