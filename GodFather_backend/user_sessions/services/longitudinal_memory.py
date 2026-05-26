"""
Longitudinal conversation memory — strategic positions preserved across weeks.
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from .cross_session_contradiction import detect_cross_session_contradiction

POSITION_MEMORY_KEY = "longitudinal_positions"

RESTRAINT_MARKERS = (
    "restrained luxury", "premium restraint", "quiet authority", "crafted precision",
    "calm premium", "enduring trust", "strategic restraint", "premium exclusivity",
)
AGGRESSIVE_MARKERS = (
    "viral", "aggressive growth", "dominate", "growth hack", "mass market", "10x",
    "hustle", "disrupt", "cheap", "discount", "race to bottom", "tiktok trend",
)
PREMIUM_IDENTITY_MARKERS = ("premium", "luxury", "exclusive", "authority", "restraint", "crafted")


def record_strategic_position(
    session_id: int,
    user_message: str,
    ai_summary: str = "",
    user=None,
) -> None:
    """Pin strategic positions stated by user or AI for future contradiction checks."""
    if not session_id:
        return
    blob = f"{user_message} {ai_summary}".lower()
    positions: List[str] = []
    for m in RESTRAINT_MARKERS + AGGRESSIVE_MARKERS:
        if m in blob:
            positions.append(m)
    if sum(1 for m in PREMIUM_IDENTITY_MARKERS if m in blob) >= 2:
        if "premium identity" not in positions:
            positions.append("premium identity")

    if not positions:
        return

    try:
        from user_sessions.models import BrandMemory

        existing = BrandMemory.objects.filter(
            session_id=session_id, key=POSITION_MEMORY_KEY
        ).first()
        history = []
        if existing and existing.value:
            history = list(existing.value.get("positions") or [])

        for p in positions:
            if p not in history:
                history.append(p)

        BrandMemory.objects.update_or_create(
            session_id=session_id,
            key=POSITION_MEMORY_KEY,
            defaults={
                "memory_type": "strategic_priority",
                "content": json.dumps({"positions": history[-20]}, ensure_ascii=False)[:4000],
                "value": {"positions": history[-20], "last_user": user_message[:500]},
                "importance_score": 1.0,
                "is_pinned": True,
                "created_by": user if user and getattr(user, "is_authenticated", False) else None,
            },
        )
    except Exception:
        pass


def get_longitudinal_positions(session_id: Optional[int]) -> List[str]:
    if not session_id:
        return []
    try:
        from user_sessions.models import BrandMemory

        row = BrandMemory.objects.filter(
            session_id=session_id, key=POSITION_MEMORY_KEY
        ).first()
        if row and row.value:
            return list(row.value.get("positions") or [])
    except Exception:
        pass
    return []


def check_longitudinal_conflict(
    current_query: str,
    current_answer: str = "",
    session_id: Optional[int] = None,
    memory_snippets: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Detect if current request/answer conflicts with prior pinned strategic positions.
    Returns user-facing message when conflict detected.
    """
    positions = get_longitudinal_positions(session_id)
    history_snippets = list(memory_snippets or [])
    if positions:
        history_snippets.append("Prior positions: " + "; ".join(positions))

    base = detect_cross_session_contradiction(
        current_answer or current_query,
        session_id,
        history_snippets,
    )

    q_lower = (current_query or "").lower()
    conflict_msg = ""
    if base.get("has_contradiction"):
        prior = (base.get("contradictions") or [{}])[0].get("prior", "prior positioning")
        conflict_msg = (
            f"This request may conflict with your earlier strategic direction ({prior}). "
            "Would you like to evolve the brand direction or preserve the existing identity?"
        )
    elif any(m in " ".join(positions).lower() for m in RESTRAINT_MARKERS + ("premium identity",)):
        if any(m in q_lower for m in AGGRESSIVE_MARKERS):
            conflict_msg = (
                "You previously emphasized restrained luxury positioning. "
                "This request sounds more aggressive/viral. "
                "Should we evolve the brand direction or keep existing premium restraint?"
            )
            base["has_contradiction"] = True
            base["cross_session_contradiction_score"] = 0.5

    ans_lower = (current_answer or "").lower()
    if positions and not base.get("has_contradiction"):
        if "premium identity" in positions or any(m in " ".join(positions) for m in RESTRAINT_MARKERS):
            if any(m in ans_lower for m in AGGRESSIVE_MARKERS):
                conflict_msg = (
                    "Answer drifts from prior premium restraint identity. "
                    "Realign tone to quiet authority or explicitly note a strategic pivot."
                )
                base["has_contradiction"] = True
                base["identity_drift"] = True
                base["cross_session_contradiction_score"] = 0.45

    base["longitudinal_positions"] = positions
    base["user_message"] = conflict_msg
    return base


def longitudinal_prompt_suffix(conflict: Dict[str, Any]) -> str:
    positions = conflict.get("longitudinal_positions") or []
    if conflict.get("has_contradiction"):
        msg = conflict.get("user_message") or ""
        return f"\nLONGITUDINAL MEMORY ALERT:\n{msg}\nSurface this tension explicitly in your response.\n"
    if positions:
        pinned = "; ".join(positions[:6])
        return (
            f"\nLONGITUDINAL BRAND IDENTITY (pinned): {pinned}\n"
            "- Preserve this identity unless the user explicitly requests evolution.\n"
        )
    return ""
