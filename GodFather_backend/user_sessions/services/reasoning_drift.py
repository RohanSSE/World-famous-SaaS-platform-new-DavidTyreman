"""
Reasoning drift detection — answer concepts diverge from context philosophy.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Set

# Context signal → answer signals that indicate drift
DRIFT_PAIRS = (
    ({"trust", "restraint", "consistency", "credibility"}, {"viral", "growth hack", "clickbait", "hype"}),
    ({"premium", "exclusivity", "craftsmanship"}, {"cheap", "discount", "race to bottom", "viral"}),
    ({"authority", "definitive"}, {"meme", "casual slang", "trending sound"}),
    ({"manifesto", "principle", "promise"}, {"pivot weekly", "growth hack", "algorithm"}),
)

CONCEPT_PATTERN = re.compile(
    r"\b(trust|viral|premium|authority|manifesto|consistency|restraint|"
    r"growth hack|clickbait|craftsmanship|exclusivity|meme|principle|promise)\b",
    re.I,
)


def _extract_concepts(text: str) -> Set[str]:
    if not text:
        return set()
    return {m.lower() for m in CONCEPT_PATTERN.findall(text)}


def score_reasoning_drift(answer: str, context: str) -> Dict[str, Any]:
    """
    Compare answer concepts vs context concepts.
    High drift → hallucination / positioning risk.
    """
    if not answer or not context:
        return {"reasoning_drift_score": 0.0, "drift_detected": False, "drift_pairs": []}

    ctx_c = _extract_concepts(context)
    ans_c = _extract_concepts(answer)
    drifts: List[Dict[str, str]] = []

    for ctx_signals, ans_signals in DRIFT_PAIRS:
        ctx_hit = ctx_c & ctx_signals
        ans_hit = ans_c & ans_signals
        if ctx_hit and ans_hit:
            drifts.append(
                {
                    "context": ", ".join(sorted(ctx_hit)),
                    "answer": ", ".join(sorted(ans_hit)),
                }
            )

    # Answer introduces strong anti-context themes without context support
    orphan_viral = ans_c & {"viral", "clickbait", "growth hack", "meme"} - ctx_c
    if orphan_viral and ctx_c & {"trust", "premium", "authority", "manifesto"}:
        drifts.append({"context": "strategic identity", "answer": ", ".join(orphan_viral)})

    score = min(1.0, len(drifts) * 0.35 + (0.2 if orphan_viral else 0))
    return {
        "reasoning_drift_score": round(score, 3),
        "drift_detected": score >= 0.35,
        "drift_pairs": drifts[:4],
        "context_concepts": sorted(ctx_c)[:12],
        "answer_concepts": sorted(ans_c)[:12],
    }
