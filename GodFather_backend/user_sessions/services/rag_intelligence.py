"""
Knowledge intelligence: weighted categories, persona boosts, conversational memory (Phase 10).
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from django.conf import settings

# Default category boosts (manifesto questions → manifesto chunks)
DEFAULT_CATEGORY_WEIGHTS: Dict[str, float] = {
    "manifesto": 1.0,
    "branding": 1.0,
    "psychology": 1.0,
    "strategy": 1.0,
    "positioning": 1.0,
    "sales": 1.0,
    "marketing": 1.0,
    "user_document": 1.2,
}

# Query-intent → category multiplier overrides
INTENT_CATEGORY_BOOSTS: Dict[str, Dict[str, float]] = {
    "manifesto": {"manifesto": 2.0, "branding": 1.4, "positioning": 1.3},
    "differentiation": {"positioning": 1.8, "strategy": 1.5, "branding": 1.3},
    "emotional": {"branding": 1.6, "psychology": 1.8, "manifesto": 1.2},
    "trust": {"manifesto": 1.6, "branding": 1.5, "psychology": 1.4},
    "content": {"marketing": 1.8, "content": 1.8, "branding": 1.2},
    "positioning": {"positioning": 2.0, "strategy": 1.5, "manifesto": 1.4},
    "audience_psychology": {"psychology": 2.0, "branding": 1.5, "manifesto": 1.3},
    "competitor": {"positioning": 1.8, "strategy": 1.6, "manifesto": 1.4},
}

# Persona → category preference
PERSONA_CATEGORY_WEIGHTS: Dict[str, Dict[str, float]] = {
    "founder": {"branding": 1.5, "manifesto": 1.4, "psychology": 1.3, "sales": 0.8},
    "investor": {"strategy": 1.6, "positioning": 1.5, "sales": 1.4, "psychology": 0.7},
    "agency": {"marketing": 1.5, "content": 1.5, "branding": 1.2},
    "default": {},
}


def detect_query_intent(query: str) -> str:
    q = query.lower()
    if any(w in q for w in ("manifesto", "core belief", "brand promise")):
        return "manifesto"
    if any(w in q for w in ("audience psych", "persona", "buyer mindset", "customer psychology")):
        return "audience_psychology"
    if any(w in q for w in ("competitor", "compete", "price war", "cheaper", "irrelevant")):
        return "competitor"
    if any(w in q for w in ("differentiate", "unique", "stand out", "me-too", "me too")):
        return "differentiation"
    if any(w in q for w in ("positioning", "category role", "market frame")):
        return "positioning"
    if any(w in q for w in ("emotion", "feel", "connection", "story")):
        return "emotional"
    if any(w in q for w in ("trust", "clarity", "authentic")):
        return "trust"
    if any(w in q for w in ("conflict", "contradict", "inconsistent", "narrative clash")):
        return "manifesto"
    if any(w in q for w in ("social", "content", "caption", "campaign")):
        return "content"
    if "position" in q:
        return "positioning"
    return "general"


def get_category_weights(query: str, persona: Optional[str] = None) -> Dict[str, float]:
    """Combined weights from settings, intent, and persona."""
    weights = dict(getattr(settings, "RAG_CATEGORY_WEIGHTS", None) or DEFAULT_CATEGORY_WEIGHTS)
    intent = detect_query_intent(query)
    for cat, mult in INTENT_CATEGORY_BOOSTS.get(intent, {}).items():
        weights[cat] = weights.get(cat, 1.0) * mult
    persona_key = (persona or "default").lower()
    for cat, mult in PERSONA_CATEGORY_WEIGHTS.get(persona_key, {}).items():
        weights[cat] = weights.get(cat, 1.0) * mult
    return weights


def apply_category_boosts(
    chunks: List[Dict[str, Any]],
    query: str,
    persona: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Re-score chunks by category weight after retrieval."""
    weights = get_category_weights(query, persona)
    boosted = []
    for chunk in chunks:
        c = dict(chunk)
        meta = c.get("metadata") or {}
        cat = meta.get("category") or meta.get("source") or "knowledge"
        base = float(c.get("score") or c.get("rrf_score") or 0.01)
        w = weights.get(cat, 1.0)
        c["score"] = base * w
        c["category_boost"] = w
        boosted.append(c)
    boosted.sort(key=lambda x: float(x.get("score") or 0), reverse=True)
    return boosted


def build_conversational_query(
    query: str,
    conversation_messages: Optional[List[Dict[str, str]]] = None,
    session_summary: Optional[str] = None,
    max_history: int = 5,
) -> str:
    """
    Expand query with last N messages + optional session summary (Conversational RAG).
    """
    parts = [query.strip()]
    if session_summary:
        parts.insert(0, f"Session context: {session_summary[:500]}")
    if conversation_messages:
        recent = conversation_messages[-max_history:]
        hist = " | ".join(
            f"{m.get('role', 'user')}: {m.get('content', '')[:200]}"
            for m in recent
            if m.get("content")
        )
        if hist:
            parts.append(f"Recent conversation: {hist}")
    return "\n".join(parts)


def compress_context(context: str, max_chars: int = 6000) -> str:
    """Light compression: trim whitespace, cap length."""
    text = re.sub(r"\n{3,}", "\n\n", context.strip())
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3] + "..."
