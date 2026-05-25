"""
Institutional failure memory — learn from recurring weaknesses.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from django.conf import settings

logger = logging.getLogger(__name__)

FAILURE_MEMORY_FILE = "failure_memory.json"


def _memory_path() -> Path:
    base = getattr(settings, "BASE_DIR", Path(__file__).resolve().parents[2])
    return Path(base) / "evaluation" / FAILURE_MEMORY_FILE


def _load_store() -> Dict[str, Any]:
    path = _memory_path()
    if not path.exists():
        return {"patterns": []}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"patterns": []}


def _save_store(data: Dict[str, Any]) -> None:
    path = _memory_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _pattern_id(flags: List[str]) -> str:
    return "_".join(sorted(flags)[:4]) or "unknown_failure"


def record_failure_event(
    critique_flags: List[str],
    query: str = "",
    severity: float = 0.5,
    recommended_fix: str = "",
    session_id: Optional[int] = None,
) -> None:
    """Increment failure pattern frequency."""
    if not critique_flags:
        return
    if not getattr(settings, "FAILURE_MEMORY_ENABLED", True):
        return

    store = _load_store()
    patterns = {p["failure_pattern"]: p for p in store.get("patterns", [])}
    pid = _pattern_id(critique_flags)

    if pid not in patterns:
        patterns[pid] = {
            "failure_pattern": pid,
            "flags": list(critique_flags),
            "frequency": 0,
            "severity": severity,
            "recommended_fix": recommended_fix or _default_fix(critique_flags),
            "last_seen": "",
            "example_queries": [],
        }

    p = patterns[pid]
    p["frequency"] = int(p.get("frequency", 0)) + 1
    p["last_seen"] = datetime.now(timezone.utc).isoformat()
    p["severity"] = max(float(p.get("severity", 0)), severity)
    if query and query[:120] not in (p.get("example_queries") or []):
        p.setdefault("example_queries", []).append(query[:120])
        p["example_queries"] = p["example_queries"][-5:]

    store["patterns"] = sorted(
        patterns.values(), key=lambda x: x.get("frequency", 0), reverse=True
    )[:50]
    _save_store(store)

    if session_id:
        try:
            from user_sessions.models import BrandMemory

            BrandMemory.objects.update_or_create(
                session_id=session_id,
                key=f"failure_warn:{pid}",
                defaults={
                    "memory_type": "preference",
                    "content": json.dumps(p, ensure_ascii=False)[:1500],
                    "value": p,
                    "importance_score": min(1.0, 0.5 + severity * 0.4),
                },
            )
        except Exception as e:
            logger.debug("Session failure memory skipped: %s", e)


def _default_fix(flags: List[str]) -> str:
    fixes = {
        "weak_manifesto_support": "increase_manifesto_density",
        "generic_reasoning": "tighten_strategic_specificity",
        "reasoning_drift": "preserve_philosophy_graph",
        "unsupported_claim": "full_verify_and_hedge",
        "context_conflict": "repair_context_remove_conflicts",
        "low_strategic_density": "expand_manifesto_chunks",
        "low_confidence_overclaim": "exploratory_mode_overclaim_suppress",
    }
    return fixes.get(flags[0], "run_self_repair")


def get_top_failure_patterns(limit: int = 5) -> List[Dict[str, Any]]:
    store = _load_store()
    return list(store.get("patterns", []))[:limit]


def inject_known_failure_warnings(
    critique_flags: List[str] = None,
    query: str = "",
    session_id: Optional[int] = None,
) -> str:
    """
    Inject institutional warnings before generation based on learned failures.
    """
    if not getattr(settings, "FAILURE_MEMORY_ENABLED", True):
        return ""

    lines: List[str] = []
    patterns = get_top_failure_patterns(5)

    for p in patterns:
        overlap = set(p.get("flags", [])) & set(critique_flags or [])
        if critique_flags and not overlap:
            continue
        if p.get("frequency", 0) < 2:
            continue
        lines.append(
            f"- Recurring weakness '{p['failure_pattern']}' (seen {p['frequency']}x): "
            f"{p.get('recommended_fix', 'apply repair')}"
        )

    if not lines and patterns:
        top = patterns[0]
        lines.append(
            f"- System-wide pattern: {top['failure_pattern']} — {top.get('recommended_fix', '')}"
        )

    if not lines:
        return ""

    return (
        "\nINSTITUTIONAL FAILURE MEMORY (avoid repeating known weaknesses):\n"
        + "\n".join(lines[:4])
    )
