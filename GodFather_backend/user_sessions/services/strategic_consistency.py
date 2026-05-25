"""
Strategic consistency score — longitudinal coherence across manifesto, memory, tone, strategy.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from django.conf import settings

from .reasoning_drift import _extract_concepts
from .rag_evaluation import score_strategic_specificity, _token_set


def _overlap_ratio(a: str, b: str) -> float:
    ta, tb = _token_set(a), _token_set(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / max(len(ta), 1)


def compute_strategic_consistency(
    answer: str,
    context: str,
    memory_snippets: Optional[List[str]] = None,
    style: Optional[Dict[str, Any]] = None,
    session_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    consistency = blend(manifesto_alignment, memory_alignment, tone_alignment, strategy_alignment)
    """
    memory_snippets = memory_snippets or []
    style = style or {}
    mem_text = " ".join(memory_snippets)

    ctx_lower = (context or "").lower()
    brand_book_in_ctx = any(
        t in ctx_lower for t in ("brand book", "brandbook", "manifesto", "brand_book")
    )
    brand_book_alignment = 0.0
    if context and brand_book_in_ctx:
        brand_book_alignment = min(
            1.0,
            _overlap_ratio(answer, context)
            + (0.2 if any(t in answer.lower() for t in ("brand book", "manifesto")) else 0),
        )
    else:
        brand_book_alignment = _overlap_ratio(answer, context) * 0.8

    memory_alignment = _overlap_ratio(answer, mem_text) if mem_text else 0.5

    from .brand_brain import get_brand_brain
    from .brand_personality import BRAND_CONSTITUTION

    personality = get_brand_brain(session_id)
    tone_target = (personality.get("tone") or "authoritative").lower()
    ans_lower = answer.lower()

    tone_alignment = 0.65
    if tone_target.split()[0] in ans_lower:
        tone_alignment += 0.15
    prefers = style.get("prefers", []) or personality.get("communication_laws", [])[:3]
    avoids = style.get("avoids", [])
    if prefers and any(p.lower() in ans_lower for p in prefers):
        tone_alignment += 0.2
    if avoids and any(a.lower() in ans_lower for a in avoids):
        tone_alignment -= 0.3
    preferred_lang = personality.get("preferred_language") or []
    rejected_lang = personality.get("rejected_language") or []
    if preferred_lang and any(p.lower() in ans_lower for p in preferred_lang if isinstance(p, str)):
        tone_alignment += 0.12
    if rejected_lang and any(r.lower() in ans_lower for r in rejected_lang if isinstance(r, str)):
        tone_alignment -= 0.2
    brain_conf = float(personality.get("personality_confidence") or 0.7)
    tone_alignment = min(1.0, tone_alignment * 0.85 + brain_conf * 0.15)
    tone_alignment = max(0.0, min(1.0, tone_alignment))

    strategy_alignment = score_strategic_specificity(answer, context, [])
    strategy_alignment = min(1.0, strategy_alignment * 1.1)
    pref_patterns = BRAND_CONSTITUTION.get("preferred_patterns") or []
    if pref_patterns and any(p.lower() in ans_lower for p in pref_patterns if isinstance(p, str)):
        strategy_alignment = min(1.0, strategy_alignment + 0.08)
    if any(
        p in ans_lower
        for p in ("brand book", "manifesto", "quiet authority", "crafted precision", "strategic restraint")
    ):
        strategy_alignment = min(1.0, strategy_alignment + 0.06)

    w_brand = float(getattr(settings, "CONSISTENCY_BRAND_BOOK_WEIGHT", 0.20))
    w_mem = float(getattr(settings, "CONSISTENCY_MEMORY_WEIGHT", 0.15))
    w_tone = float(getattr(settings, "CONSISTENCY_TONE_WEIGHT", 0.38))
    w_strat = float(getattr(settings, "CONSISTENCY_STRATEGY_WEIGHT", 0.27))

    score = round(
        w_brand * brand_book_alignment
        + w_mem * memory_alignment
        + w_tone * tone_alignment
        + w_strat * strategy_alignment,
        3,
    )

    return {
        "consistency_score": score,
        "brand_book_alignment": round(brand_book_alignment, 3),
        "manifesto_alignment": round(brand_book_alignment, 3),
        "memory_alignment": round(memory_alignment, 3),
        "tone_alignment": round(tone_alignment, 3),
        "strategy_alignment": round(strategy_alignment, 3),
    }
