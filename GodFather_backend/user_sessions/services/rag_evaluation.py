"""
Automatic RAG evaluation metrics — enterprise trust layer.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from django.conf import settings

GENERIC_FILLER_PHRASES = (
    "be authentic",
    "stay consistent",
    "focus on innovation",
    "build trust",
    "unique value",
    "stand out",
    "engage your audience",
    "deliver value",
    "customer-centric",
    "focus on quality",
    "strong brand presence",
    "best practices",
    "world-class",
    "customer-centric approach",
)


def _token_set(text: str) -> set:
    return set(re.findall(r"[a-z0-9']+", text.lower()))


def _sentences(text: str) -> List[str]:
    parts = re.split(r"(?<=[.!?])\s+", (text or "").strip())
    return [p.strip() for p in parts if len(p.strip()) > 12]


def score_groundedness(answer: str, context: str) -> float:
    if not answer or not context:
        return 0.0
    stop = {"the", "a", "an", "is", "are", "and", "or", "to", "of", "in", "it", "you", "your", "that", "this"}
    a_tokens = _token_set(answer) - stop
    c_tokens = _token_set(context)
    if not a_tokens:
        return 0.0
    return round(min(1.0, len(a_tokens & c_tokens) / len(a_tokens)), 3)


def score_grounded_answer_ratio(answer: str, context: str) -> float:
    sents = _sentences(answer)
    if not sents or not context:
        return 0.0
    c_tokens = _token_set(context)
    grounded = sum(
        1
        for sent in sents
        if len(_token_set(sent) - {"the", "a", "an", "is", "are", "and", "or", "to", "of", "in"}) >= 4
        and len(_token_set(sent) & c_tokens) / max(len(_token_set(sent)), 1) >= 0.35
    )
    return round(grounded / len(sents), 3)


def detect_ungrounded_generic_filler(answer: str, context: str) -> List[Dict[str, Any]]:
    """
    Generic phrase appears in answer WITHOUT sufficient context overlap.
    Drives critique rewrite when generic_filler_score > 0.
    """
    if not answer or not context:
        return []
    ctx = context.lower()
    hits = []
    for phrase in GENERIC_FILLER_PHRASES:
        if phrase not in answer.lower():
            continue
        # phrase must not be substantively present in context
        if phrase not in ctx and not any(w in ctx for w in phrase.split() if len(w) > 4):
            hits.append({"phrase": phrase, "grounded_in_context": False})
    return hits


def score_generic_filler_penalty(answer: str, context: str) -> float:
    """
    Count of ungrounded generic phrases (integer-like score for pipeline).
    Lower is better. Normalized 0-1 for metrics.
    """
    hits = detect_ungrounded_generic_filler(answer, context)
    return round(min(1.0, len(hits) / max(len(_sentences(answer)), 1)), 3)


def score_source_coverage(answer: str, sources: List[Dict[str, Any]]) -> float:
    """
    used_sources / retrieved_sources — detects model ignoring good retrieval.
    Target > 0.70
    """
    if not sources:
        return 0.0
    a_lower = answer.lower()
    used = 0
    for s in sources:
        title = (s.get("title") or s.get("document_title") or "").lower()
        cat = (s.get("category") or "").lower()
        file_ref = (s.get("file") or "").lower()
        if cat and cat in a_lower:
            used += 1
            continue
        if title and any(w in a_lower for w in title.split()[:3] if len(w) > 3):
            used += 1
            continue
        if file_ref and any(part in a_lower for part in file_ref.split("/")[-1].split(".")[:1] if part):
            used += 1
    return round(min(1.0, used / len(sources)), 3)


def score_citation_coverage(answer: str, sources: List[Dict[str, Any]]) -> float:
    return score_source_coverage(answer, sources)


def score_retrieval_relevance(chunks: List[Dict[str, Any]]) -> float:
    if not chunks:
        return 0.0
    scores = [
        float(c.get("hybrid_score") or c.get("score") or c.get("rrf_score") or 0)
        for c in chunks[:5]
    ]
    if not scores:
        return 0.0
    avg = sum(scores) / len(scores)
    return round(min(1.0, avg if avg <= 1 else avg / 10), 3)


STRATEGIC_NOUNS = (
    "trust", "authority", "positioning", "manifesto", "premium", "differentiation",
    "consistency", "narrative", "credibility", "promise", "emotion", "dna",
)


def score_strategic_specificity(
    answer: str,
    context: str,
    sources: List[Dict[str, Any]],
    memory_snippets: List[str] = None,
) -> float:
    """
    Higher = concrete strategic language grounded in knowledge/memory (not abstract filler).
    """
    if not answer:
        return 0.0
    a_lower = answer.lower()
    signals = 0.0

    # Named strategic concepts
    noun_hits = sum(1 for n in STRATEGIC_NOUNS if n in a_lower)
    signals += min(0.35, noun_hits * 0.06)

    # Manifesto / source references
    for s in sources or []:
        title = (s.get("title") or "").lower()
        cat = (s.get("category") or "").lower()
        if cat and cat in a_lower:
            signals += 0.12
            break
        if title and any(w in a_lower for w in title.split()[:4] if len(w) > 4):
            signals += 0.10
            break

    if "manifesto" in a_lower or "principle" in a_lower:
        signals += 0.12

    # Memory overlap
    mem = " ".join(memory_snippets or []).lower()
    if mem:
        mem_tokens = _token_set(mem)
        a_tokens = _token_set(answer)
        if mem_tokens and a_tokens:
            overlap = len(mem_tokens & a_tokens) / max(len(a_tokens), 1)
            signals += min(0.2, overlap * 0.5)

    # Context overlap (retrieval grounding)
    if context:
        ctx_tokens = _token_set(context)
        a_tokens = _token_set(answer) - {"the", "a", "an", "is", "are", "and", "or", "to", "of", "in"}
        if a_tokens:
            signals += min(0.25, len(a_tokens & ctx_tokens) / len(a_tokens) * 0.35)

    # Penalize abstract-only sentences
    abstract_only = sum(
        1
        for phrase in ("be authentic", "build trust", "focus on quality", "engage your audience")
        if phrase in a_lower
    )
    signals -= min(0.2, abstract_only * 0.08)

    return round(max(0.0, min(1.0, signals)), 3)


def estimate_hallucination_risk(
    answer: str,
    context: str,
    sources: List[Dict],
    grounded_ratio: float = 0.0,
    claim_verification: Optional[Dict[str, Any]] = None,
    split_metrics: Optional[Dict[str, float]] = None,
    overclaim_suppressed: bool = False,
    critique_flags: Optional[List[str]] = None,
    context_quality: Optional[Dict[str, Any]] = None,
) -> float:
    gr = grounded_ratio or score_grounded_answer_ratio(answer, context)
    claim_ratio = float((claim_verification or {}).get("claim_grounded_ratio") or gr)

    if getattr(settings, "CALIBRATED_HALLUCINATION_METRIC", True):
        from .calibration_metrics import (
            compute_split_hallucination_metrics,
            estimate_hallucination_risk_calibrated,
        )

        split = split_metrics or compute_split_hallucination_metrics(
            claim_verification,
            context_quality=context_quality,
            overclaim_suppressed=overclaim_suppressed,
            critique_flags=critique_flags,
        )
        return estimate_hallucination_risk_calibrated(split, gr, claim_ratio)

    g = score_groundedness(answer, context)
    c = score_source_coverage(answer, sources)
    filler = score_generic_filler_penalty(answer, context)
    safety = 0.30 * g + 0.25 * c + 0.25 * gr + 0.20 * (1.0 - filler)
    return round(max(0.0, min(1.0, 1.0 - safety)), 3)


def evaluate_rag_response(
    answer: str,
    context: str,
    sources: List[Dict[str, Any]],
    chunks: List[Dict[str, Any]],
    query: str = "",
    memory_snippets: List[str] = None,
    graph_concepts: List[str] = None,
) -> Dict[str, Any]:
    from .answer_attribution import extract_claim_attributions

    groundedness = score_groundedness(answer, context)
    grounded_answer_ratio = score_grounded_answer_ratio(answer, context)
    generic_filler_ratio = score_generic_filler_penalty(answer, context)
    ungrounded_filler = detect_ungrounded_generic_filler(answer, context)
    source_coverage = score_source_coverage(answer, sources)
    citation_coverage = source_coverage
    retrieval_relevance = score_retrieval_relevance(chunks)
    from .claim_verification import verify_answer_against_context

    claim_verify = verify_answer_against_context(answer, context, sources, chunks=chunks, query=query)
    from .calibration_metrics import compute_split_hallucination_metrics

    split_hallucination = compute_split_hallucination_metrics(claim_verify)
    hallucination_risk = estimate_hallucination_risk(
        answer,
        context,
        sources,
        grounded_answer_ratio,
        claim_verification=claim_verify,
        split_metrics=split_hallucination,
    )
    claim_attributions = extract_claim_attributions(
        answer, context, sources, graph_concepts, memory_snippets
    )
    unattributed = sum(1 for a in claim_attributions if "unattributed" in a.get("supported_by", []))
    strategic_specificity = score_strategic_specificity(
        answer, context, sources, memory_snippets
    )

    passes = (
        float(claim_verify.get("claim_grounded_ratio", 0)) >= 0.45
        and grounded_answer_ratio >= 0.4
        and hallucination_risk <= float(getattr(settings, "PASS_MAX_HALLUCINATION_RISK", 0.45))
        and generic_filler_ratio <= 0.5
        and strategic_specificity >= 0.2
    )

    return {
        "groundedness": groundedness,
        "grounded_answer_ratio": grounded_answer_ratio,
        "generic_filler_ratio": generic_filler_ratio,
        "ungrounded_generic_phrases": ungrounded_filler,
        "generic_filler_count": len(ungrounded_filler),
        "source_coverage": source_coverage,
        "citation_coverage": citation_coverage,
        "retrieval_relevance": retrieval_relevance,
        "hallucination_risk": hallucination_risk,
        **split_hallucination,
        "claim_attributions": claim_attributions,
        "claim_verification": claim_verify,
        "claim_grounded_ratio": claim_verify.get("claim_grounded_ratio", grounded_answer_ratio),
        "unattributed_claims": unattributed,
        "strategic_specificity_score": strategic_specificity,
        "passes_quality_gate": passes,
    }
