"""
Knowledge graph foundation — concept relations + query expansion (Phase 11).
"""
from __future__ import annotations

from typing import Dict, List, Set

# Concept → related concepts (for expansion at retrieval time)
CONCEPT_GRAPH: Dict[str, List[str]] = {
    "brand dna": ["trust", "positioning", "storytelling", "emotional resonance", "authenticity"],
    "trust": ["clarity", "consistency", "authenticity", "brand promise"],
    "positioning": ["differentiation", "competitors", "unique promise", "audience"],
    "storytelling": ["emotional connection", "origin story", "mission", "vulnerability"],
    "emotional resonance": ["feel", "behavior", "promise kept", "connection"],
    "manifesto": ["core belief", "brand promise", "differentiation", "tone of voice"],
    "differentiation": ["me-too", "competitors irrelevant", "unique", "positioning"],
    "authenticity": ["fancy packaging", "genuine", "behavior proof"],
}

# Reverse index for lookup
_REVERSE: Dict[str, Set[str]] = {}


def _build_reverse_index() -> None:
    global _REVERSE
    if _REVERSE:
        return
    for concept, related in CONCEPT_GRAPH.items():
        _REVERSE.setdefault(concept.lower(), set()).add(concept)
        for r in related:
            _REVERSE.setdefault(r.lower(), set()).add(concept)


def expand_query_with_graph(query: str, max_terms: int = 6) -> str:
    """
    Append related concepts from knowledge graph to improve retrieval recall.
    """
    _build_reverse_index()
    q_lower = query.lower()
    extras: List[str] = []
    seen: Set[str] = set()

    for concept, related in CONCEPT_GRAPH.items():
        if concept in q_lower:
            for r in related:
                if r not in seen:
                    extras.append(r)
                    seen.add(r)
        for r in related:
            if r in q_lower and concept not in seen:
                extras.append(concept)
                seen.add(concept)

    for token in q_lower.split():
        if token in _REVERSE:
            for parent in _REVERSE[token]:
                if parent not in seen:
                    extras.append(parent)
                    seen.add(parent)

    if not extras:
        return query
    return query + " " + " ".join(extras[:max_terms])


def get_related_concepts(query: str) -> List[str]:
    """Return concepts linked to query (for debug / UI)."""
    _build_reverse_index()
    q_lower = query.lower()
    found: List[str] = []
    for concept in CONCEPT_GRAPH:
        if concept in q_lower or any(r in q_lower for r in CONCEPT_GRAPH[concept]):
            found.append(concept)
    return found[:8]
