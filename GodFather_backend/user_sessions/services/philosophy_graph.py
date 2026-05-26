"""
Strategic philosophy graph — symbolic consistency for manifesto reasoning.
"""
from __future__ import annotations

from typing import Any, Dict, List, Set

# Parent → child concepts (preserve hierarchy in answers)
PHILOSOPHY_GRAPH: Dict[str, List[str]] = {
    "trust": ["restraint", "craftsmanship", "consistency", "long-term positioning", "promise kept"],
    "premium": ["exclusivity", "craftsmanship", "restraint", "controlled visibility"],
    "authority": ["expertise", "definitive clarity", "credibility", "leadership"],
    "differentiation": ["unique promise", "competitor irrelevant", "distinct narrative"],
    "manifesto": ["core belief", "non-negotiable", "brand promise", "principles"],
}

# Sibling concepts that should not contradict without explicit tension handling
INCOMPATIBLE_SIBLINGS = (
    ("restraint", "viral growth"),
    ("craftsmanship", "speed at all costs"),
    ("consistency", "weekly pivot"),
    ("premium", "race to bottom"),
)


def expand_philosophy_concepts(seed: str) -> Set[str]:
    """All concepts reachable from seed in graph."""
    seed = seed.lower().strip()
    out: Set[str] = {seed}
    for parent, children in PHILOSOPHY_GRAPH.items():
        if parent in seed or seed in parent:
            out.add(parent)
            out.update(c.lower() for c in children)
        for child in children:
            if child.lower() in seed:
                out.add(parent)
                out.update(c.lower() for c in children)
    return out


def preserve_graph_consistency(answer: str, context: str) -> Dict[str, Any]:
    """
    Check answer against philosophy graph — flag breaks in hierarchy.
    """
    a_lower = answer.lower()
    c_lower = context.lower()
    violations: List[Dict[str, str]] = []

    active_roots = []
    for root in PHILOSOPHY_GRAPH:
        if root in c_lower or root in a_lower:
            active_roots.append(root)

    for root in active_roots:
        allowed = expand_philosophy_concepts(root)
        for sib_a, sib_b in INCOMPATIBLE_SIBLINGS:
            if sib_a in allowed and sib_b in a_lower and sib_b not in c_lower:
                violations.append({"root": root, "conflict": f"{sib_a} vs {sib_b}"})

    score = min(1.0, len(violations) * 0.35)
    return {
        "philosophy_violation_score": round(score, 3),
        "philosophy_violations": violations[:5],
        "active_roots": active_roots[:4],
        "graph_consistent": len(violations) == 0,
    }


def philosophy_prompt_suffix(graph_check: Dict[str, Any]) -> str:
    if graph_check.get("graph_consistent", True):
        roots = graph_check.get("active_roots", [])
        if roots:
            children = []
            for r in roots[:2]:
                children.extend(PHILOSOPHY_GRAPH.get(r, [])[:3])
            return (
                f"\nPHILOSOPHY GRAPH: Preserve {', '.join(roots)} through "
                f"{', '.join(children[:4])} — do not contradict these pillars.\n"
            )
        return ""
    return (
        "\nPHILOSOPHY GRAPH: Prior answer may violate strategic pillars. "
        "Re-align with manifesto trust/premium/restraint framing.\n"
    )
