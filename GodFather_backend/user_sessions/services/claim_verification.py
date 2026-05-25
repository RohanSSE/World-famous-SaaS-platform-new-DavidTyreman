"""
Unsupported claim detection — sentence-level grounding check (Reliable Intelligence v1).
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

from django.conf import settings

from .rag_evaluation import _sentences, _token_set

GENERIC_CLAIM_PATTERNS = (
    re.compile(r"\b(always|never|every brand|all brands|must always)\b", re.I),
    re.compile(r"\b(viral marketing|growth hacks?|10x|guaranteed)\b", re.I),
    re.compile(r"\b(build trust|be authentic|connect with audience|focus on value)\b", re.I),
    re.compile(r"\b(world-class|best practices|customer-centric|unique value proposition)\b", re.I),
)


def _sentence_grounded(sentence: str, context: str, threshold: float = 0.35) -> bool:
    stop = {"the", "a", "an", "is", "are", "and", "or", "to", "of", "in", "it", "you", "your", "that", "this", "be"}
    st = _token_set(sentence) - stop
    if len(st) < 4:
        return True
    ct = _token_set(context)
    overlap = len(st & ct) / len(st)
    return overlap >= threshold


def detect_unsupported_claims(
    answer: str,
    context: str,
    threshold: float = 0.35,
) -> List[Dict[str, Any]]:
    """
    Flag sentences with low overlap to retrieved context.
    Returns list of {unsupported_claim, sentence, overlap_ratio}.
    """
    if not answer or not context:
        return []

    claims: List[Dict[str, Any]] = []
    for sent in _sentences(answer):
        if len(sent) < 20:
            continue
        st = _token_set(sent) - {"the", "a", "an", "is", "are", "and", "or", "to", "of", "in"}
        ct = _token_set(context)
        overlap = len(st & ct) / max(len(st), 1) if st else 1.0

        generic_hit = any(p.search(sent) for p in GENERIC_CLAIM_PATTERNS)
        grounded = _sentence_grounded(sent, context, threshold)

        if not grounded or (generic_hit and overlap < 0.5):
            claims.append(
                {
                    "unsupported_claim": True,
                    "sentence": sent[:280],
                    "overlap_ratio": round(overlap, 3),
                    "generic_pattern": generic_hit,
                }
            )
    return claims[:8]


def verify_answer_against_context(
    answer: str,
    context: str,
    sources: List[Dict[str, Any]] = None,
    chunks: List[Dict[str, Any]] = None,
    query: str = "",
) -> Dict[str, Any]:
    """Verification payload for API / quality pipeline."""
    if getattr(settings, "CLAIM_LEVEL_VERIFICATION_ENABLED", True):
        if getattr(settings, "STRICT_EVIDENCE_MODE", True):
            from .brand_cognition import verify_claims_with_consensus

            return verify_claims_with_consensus(
                answer, context, chunks=chunks or sources, query=query or ""
            )
        from .grounded_generation import verify_claims_at_level

        return verify_claims_at_level(answer, context, chunks=chunks or sources)

    unsupported = detect_unsupported_claims(answer, context)
    total = len(_sentences(answer))
    supported = max(0, total - len(unsupported))
    ratio = supported / total if total else 1.0

    return {
        "unsupported_claims": unsupported,
        "unsupported_count": len(unsupported),
        "verified_sentence_ratio": round(ratio, 3),
        "hallucination_flags": len(unsupported) > 0,
    }
