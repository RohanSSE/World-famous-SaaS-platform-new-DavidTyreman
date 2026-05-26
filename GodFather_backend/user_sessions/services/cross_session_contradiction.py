"""
Cross-session contradiction detection — longitudinal strategic coherence.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

CONTRADICTION_PAIRS = (
    ("premium restraint", "mass aggressive virality"),
    ("premium", "viral marketing"),
    ("trust and consistency", "growth hack"),
    ("authoritative", "playful meme"),
    ("craftsmanship", "move fast break things"),
    ("long-term positioning", "pivot weekly"),
)


def _extract_positions(text: str) -> List[str]:
    if not text:
        return []
    sents = re.split(r"(?<=[.!?])\s+", text.strip())
    return [s.strip() for s in sents if len(s.strip()) > 20][:20]


def detect_cross_session_contradiction(
    current_answer: str,
    session_id: Optional[int],
    memory_snippets: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Compare current answer against pinned session memory + recent strategic decisions.
    """
    if not session_id and not memory_snippets:
        return {"cross_session_contradiction_score": 0.0, "contradictions": []}

    history_parts: List[str] = list(memory_snippets or [])

    if session_id:
        try:
            from user_sessions.models import BrandMemory

            rows = BrandMemory.objects.filter(
                session_id=session_id,
                is_pinned=True,
            ).order_by("-updated_at")[:12]
            for r in rows:
                history_parts.append(r.content)
                if r.value and isinstance(r.value, dict):
                    history_parts.append(str(r.value))
        except Exception:
            pass

    history = " ".join(history_parts).lower()
    current = current_answer.lower()
    if not history or len(history) < 30:
        return {"cross_session_contradiction_score": 0.0, "contradictions": []}

    contradictions: List[Dict[str, str]] = []
    for pos_a, pos_b in CONTRADICTION_PAIRS:
        if pos_a in history and pos_b in current:
            contradictions.append({"prior": pos_a, "current": pos_b})
        if pos_b in history and pos_a in current:
            contradictions.append({"prior": pos_b, "current": pos_a})

    score = min(1.0, len(contradictions) * 0.4)
    return {
        "cross_session_contradiction_score": round(score, 3),
        "contradictions": contradictions[:4],
        "has_contradiction": bool(contradictions),
    }
