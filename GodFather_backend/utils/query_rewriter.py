"""
Strategic query rewriting — expand queries before retrieval for precision.
"""
from __future__ import annotations

from typing import List, Set

from user_sessions.services.rag_intelligence import detect_query_intent
from utils.strategic_tags import STRATEGIC_INTENTS, detect_query_strategic_tags

# Intent → internal retrieval phrases (not shown to user)
INTENT_EXPANSIONS = {
    "trust": (
        "premium positioning",
        "brand authority",
        "trust consistency",
        "manifesto credibility",
        "promise kept",
    ),
    "authority": (
        "brand authority",
        "expert positioning",
        "credibility",
        "manifesto principles",
    ),
    "positioning": (
        "category positioning",
        "market frame",
        "differentiation",
        "strategic narrative",
    ),
    "premium": (
        "premium positioning",
        "exclusivity",
        "luxury brand trust",
        "controlled visibility",
    ),
    "differentiation": (
        "unique positioning",
        "competitor irrelevant",
        "manifesto differentiation",
        "distinct promise",
        "why we win",
        "category role",
    ),
    "audience_psychology": (
        "audience motivation",
        "buyer psychology",
        "emotional driver",
        "persona desire",
        "brand book audience",
    ),
    "competitor": (
        "competitive frame",
        "irrelevant competitor noise",
        "differentiation anchor",
        "manifesto positioning",
    ),
    "market_enemy": (
        "market enemy",
        "competitive alternative",
        "positioning against",
    ),
    "audience_fear": ("audience fear", "buyer anxiety", "pain point"),
    "audience_desire": ("audience desire", "aspiration", "identity seeking"),
    "identity_signal": ("identity signal", "buyer identity", "tribe"),
    "positioning_archetype": ("positioning archetype", "category role", "brand archetype"),
    "status_signal": ("status signal", "prestige", "exclusivity"),
    "emotional": (
        "emotional branding",
        "brand felt",
        "story connection",
        "authentic resonance",
    ),
    "emotional_branding": (
        "emotional connection",
        "brand story",
        "felt experience",
    ),
    "manifesto": (
        "brand manifesto",
        "core beliefs",
        "brand promise",
        "principles",
    ),
    "general": (
        "strategic branding",
        "brand clarity",
    ),
}

# Map detect_query_intent() → expansion key
INTENT_KEY_MAP = {
    "manifesto": "manifesto",
    "differentiation": "differentiation",
    "emotional": "emotional",
    "trust": "trust",
    "content": "general",
    "positioning": "positioning",
    "audience_psychology": "audience_psychology",
    "competitor": "competitor",
    "general": "general",
}


def rewrite_query_for_retrieval(query: str, intent: str = None) -> str:
    """
    Append strategic expansion terms for embedding + keyword search.
    Chained after graph expansion in rag_service.
    """
    if not query or not query.strip():
        return query

    intent = intent or detect_query_intent(query)
    key = INTENT_KEY_MAP.get(intent, "general")
    tags = detect_query_strategic_tags(query)

    extras: List[str] = []
    seen: Set[str] = set()

    for phrase in INTENT_EXPANSIONS.get(key, ()):
        pl = phrase.lower()
        if pl not in seen and pl not in query.lower():
            extras.append(phrase)
            seen.add(pl)

    for tag in tags:
        for phrase in INTENT_EXPANSIONS.get(tag, ()):
            pl = phrase.lower()
            if pl not in seen and pl not in query.lower():
                extras.append(phrase)
                seen.add(pl)

    if not extras:
        return query.strip()

    return f"{query.strip()} {' '.join(extras[:8])}"
