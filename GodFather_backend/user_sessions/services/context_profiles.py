"""
Dynamic context budgeting — query-type-specific composition profiles.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from user_sessions.services.rag_intelligence import detect_query_intent

# manifesto, memory, strategic, evidence slot counts
CONTEXT_PROFILES: Dict[str, Dict[str, int]] = {
    "positioning": {"manifesto": 3, "memory": 1, "strategic": 2, "evidence": 0},
    "trust": {"manifesto": 3, "memory": 1, "strategic": 2, "evidence": 0},
    "differentiation": {"manifesto": 3, "memory": 1, "strategic": 2, "evidence": 0},
    "premium": {"manifesto": 3, "memory": 1, "strategic": 2, "evidence": 0},
    "authority": {"manifesto": 3, "memory": 1, "strategic": 2, "evidence": 0},
    "manifesto": {"manifesto": 3, "memory": 1, "strategic": 1, "evidence": 0},
    "emotional": {"manifesto": 2, "memory": 2, "strategic": 1, "evidence": 0},
    "content": {"manifesto": 1, "memory": 1, "strategic": 2, "evidence": 1},
    "growth": {"manifesto": 1, "memory": 1, "strategic": 3, "evidence": 0},
    "analytical": {"manifesto": 1, "memory": 0, "strategic": 2, "evidence": 2},
    "operational": {"manifesto": 1, "memory": 1, "strategic": 3, "evidence": 0},
    "general": {"manifesto": 2, "memory": 1, "strategic": 2, "evidence": 0},
}

INTENT_TO_PROFILE = {
    "manifesto": "manifesto",
    "trust": "trust",
    "positioning": "positioning",
    "differentiation": "differentiation",
    "emotional": "emotional",
    "content": "content",
    "general": "general",
}


def detect_context_profile(query: str, intent: Optional[str] = None) -> str:
    intent = intent or detect_query_intent(query)
    q = query.lower()
    if any(w in q for w in ("growth", "scale", "expand", "acquisition")):
        return "growth"
    if any(w in q for w in ("analyze", "metric", "data", "measure", "roi")):
        return "analytical"
    if any(w in q for w in ("operational", "process", "workflow", "team")):
        return "operational"
    if "premium" in q or "luxury" in q:
        return "premium"
    return INTENT_TO_PROFILE.get(intent, "general")


def profile_to_roles(profile: Dict[str, int]) -> Dict[str, int]:
    """Map profile slots to compose_strategic_chunks role keys."""
    return {
        "anchor_manifesto": profile.get("manifesto", 2),
        "strategic_support": profile.get("strategic", 2),
        "memory_alignment": profile.get("memory", 1),
        "evidence": profile.get("evidence", 0),
    }


def get_context_roles_for_query(query: str, intent: Optional[str] = None) -> Tuple[str, Dict[str, int]]:
    profile_name = detect_context_profile(query, intent)
    profile = dict(CONTEXT_PROFILES.get(profile_name, CONTEXT_PROFILES["general"]))
    return profile_name, profile_to_roles(profile)
