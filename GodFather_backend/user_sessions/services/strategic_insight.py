"""
Autonomous brand strategist — proactive insights from memory + retrieval gaps.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _mem_text(memory_snippets: List[str]) -> str:
    return " ".join(memory_snippets).lower()


def _source_categories(sources: Optional[List[Dict]]) -> str:
    return " ".join((s.get("category") or "") for s in (sources or [])).lower()


def detect_strategic_tensions(
    memory_snippets: List[str],
    graph_concepts: List[str],
    query: str = "",
    sources: Optional[List[Dict]] = None,
) -> List[Dict[str, str]]:
    """
    Detect positioning contradictions, drift, and grounding gaps.
    """
    insights: List[Dict[str, str]] = []
    mem = _mem_text(memory_snippets)
    concepts = " ".join(graph_concepts).lower()
    q = query.lower()
    cats = _source_categories(sources)

    innovation_signals = sum(
        1 for t in (mem, q, concepts) if any(w in t for w in ("innovation", "innovative", "disrupt"))
    )
    trust_signals = sum(
        1 for t in (mem, q, concepts, cats) if any(w in t for w in ("trust", "authority", "credib", "authentic"))
    )

    if innovation_signals >= 2 and trust_signals >= 2:
        insights.append(
            {
                "type": "narrative_alignment",
                "priority": "high",
                "message": (
                    "Potential positioning contradiction detected: "
                    "innovation themes are active while manifesto/knowledge emphasizes trust. "
                    "Should we align those narratives?"
                ),
            }
        )

    if any(w in q for w in ("generic", "bland", "same as everyone", "me-too", "feels generic")):
        insights.append(
            {
                "type": "differentiation",
                "priority": "high",
                "message": (
                    "Generic messaging often signals weak differentiation. "
                    "I can run a manifesto-grounded positioning pass."
                ),
            }
        )

    if any(w in q for w in ("authority", "weak", "credibility", "undermine", "weakens")):
        insights.append(
            {
                "type": "trust_authority",
                "priority": "medium",
                "message": (
                    "Brand authority weakens when promises outpace proof. "
                    "Want to audit manifesto claims against current messaging?"
                ),
            }
        )

    if any(w in q for w in ("competitor", "cheaper", "price", "against", "undercut")):
        insights.append(
            {
                "type": "competitive",
                "priority": "high",
                "message": (
                    "Competing on price erodes premium positioning. "
                    "I can map differentiation that makes cheaper alternatives irrelevant."
                ),
            }
        )

    if "reject" in mem or "rejected" in mem:
        insights.append(
            {
                "type": "strategy_review",
                "priority": "medium",
                "message": (
                    "A previously rejected strategic angle exists in session memory. "
                    "Revisit with a sharper differentiation frame?"
                ),
            }
        )

    if "premium" in q and cats and "manifesto" not in cats:
        insights.append(
            {
                "type": "grounding_gap",
                "priority": "medium",
                "message": (
                    "Premium trust questions usually need manifesto grounding — "
                    "retrieval was branding-heavy. Consider a manifesto-aligned pass."
                ),
            }
        )

    if ("emotional" in mem or "tone" in mem) and "innovation" in concepts and "trust" in concepts:
        insights.append(
            {
                "type": "emotional_inconsistency",
                "priority": "low",
                "message": (
                    "Emotional tone in memory may conflict with innovation/trust themes in knowledge. "
                    "Reconcile voice and positioning?"
                ),
            }
        )

    seen = set()
    out = []
    for ins in insights:
        if ins["type"] not in seen:
            seen.add(ins["type"])
            out.append(ins)
    return out[:4]


def format_proactive_prompt(insights: List[Dict[str, str]]) -> Optional[str]:
    if not insights:
        return None
    lines = [i["message"] for i in insights[:2]]
    return (
        "Proactive strategic observations (weave naturally if relevant):\n"
        + "\n".join(f"- {m}" for m in lines)
    )
