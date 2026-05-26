"""
Reliable Brand Cognition — evidence-bound generation, inference control, adaptive confidence.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from django.conf import settings

from .rag_evaluation import _sentences, _token_set

STRICT_EVIDENCE_MODE = True

STRICT_EVIDENCE_RULES = """
STRICT EVIDENCE MODE (mandatory):
- Generate ONLY strategic recommendations directly inferable from:
  * retrieved brand book excerpts
  * verified session memory (if present)
  * grounded support chunks listed in context
- Do NOT synthesize new campaigns, channels, or tactics unless explicitly stated in context.
- Do NOT extrapolate from one principle to unrelated business actions.
- If combining multiple chunks, each recommendation must be traceable to at least one source phrase.
- Prefer quoting or closely mirroring brand book language over creative paraphrase.
"""

INFERENCE_EXTRAPOLATION_MARKERS = re.compile(
    r"\b(campaign|influencer|tiktok|viral|launch a|run ads|10x|growth hack|"
    r"guaranteed roi|always post|every brand should)\b",
    re.I,
)

STRATEGIC_CLAIM_INTENTS = frozenset(
    {"trust", "positioning", "differentiation", "emotional_branding", "audience_psychology"}
)


def strict_evidence_prompt() -> str:
    if not getattr(settings, "STRICT_EVIDENCE_MODE", STRICT_EVIDENCE_MODE):
        return ""
    return STRICT_EVIDENCE_RULES


def inference_distance_score(claim: str, context: str, chunk_texts: List[str]) -> float:
    """
    0 = directly inferable from context/chunks; 1 = high extrapolation / synthesis leap.
    """
    if not claim:
        return 0.0
    stop = {"the", "a", "an", "is", "are", "and", "or", "to", "of", "in", "it", "you", "your", "that", "this", "be"}
    ct = claim_tokens = _token_set(claim) - stop
    if len(claim_tokens) < 4:
        return 0.0

    ctx_tokens = _token_set(context)
    direct_overlap = len(claim_tokens & ctx_tokens) / len(claim_tokens)

    chunk_overlaps = []
    for t in chunk_texts:
        if not t:
            continue
        chunk_overlaps.append(len(claim_tokens & _token_set(t)) / len(claim_tokens))
    best_chunk = max(chunk_overlaps) if chunk_overlaps else 0.0

    direct_support = max(direct_overlap, best_chunk)
    distance = 1.0 - direct_support

    if INFERENCE_EXTRAPOLATION_MARKERS.search(claim) and direct_support < 0.45:
        distance = min(1.0, distance + 0.25)
    return round(max(0.0, min(1.0, distance)), 3)


def count_supporting_chunks(
    claim: str,
    chunks: List[Dict[str, Any]],
    threshold: float = None,
) -> Tuple[int, List[str]]:
    threshold = threshold or float(getattr(settings, "CLAIM_GROUNDING_THRESHOLD", 0.40))
    supporting = []
    for ch in chunks or []:
        text = ch.get("text") or ""
        if not text:
            continue
        stop = {"the", "a", "an", "is", "are", "and", "or", "to", "of", "in", "it", "you", "your", "that", "this", "be"}
        ct = _token_set(claim) - stop
        if len(ct) < 3:
            continue
        overlap = len(ct & _token_set(text)) / len(ct)
        if overlap >= threshold:
            meta = ch.get("metadata") or {}
            supporting.append((meta.get("title") or ch.get("title") or "chunk")[:50])
    return len(supporting), supporting


def is_strategic_recommendation_claim(claim: str, query: str = "") -> bool:
    blob = f"{claim} {query}".lower()
    return bool(
        re.search(
            r"\b(should|must|recommend|focus on|prioritize|position|differentiat|"
            r"trust|audience|emotion|identity|promise)\b",
            blob,
        )
    )


def verify_claims_with_consensus(
    answer: str,
    context: str,
    chunks: Optional[List[Dict[str, Any]]] = None,
    query: str = "",
    threshold: float = None,
) -> Dict[str, Any]:
    """
    Enhanced claim verification: grounding + inference distance + multi-chunk consensus.
    """
    from .grounded_generation import DEFINITIVE_STRATEGIC_PATTERNS, _overlap_to_chunk

    threshold = threshold if threshold is not None else float(
        getattr(settings, "CLAIM_GROUNDING_THRESHOLD", 0.40)
    )
    min_strength = float(getattr(settings, "MIN_CLAIM_SUPPORT_STRENGTH", 0.55))
    min_chunks = int(getattr(settings, "MIN_SUPPORTING_CHUNKS", 2))
    min_chunks_strategic = int(getattr(settings, "MIN_SUPPORTING_CHUNKS_STRATEGIC", 2))
    max_inference = float(getattr(settings, "MAX_INFERENCE_DISTANCE", 0.55))
    chunks = chunks or []
    chunk_texts = [c.get("text") or "" for c in chunks if c.get("text")]

    claim_records: List[Dict[str, Any]] = []
    unsupported: List[Dict[str, Any]] = []
    high_inference: List[Dict[str, Any]] = []

    for sent in _sentences(answer):
        if len(sent) < 18:
            continue

        best_strength = 0.0
        best_chunks: List[str] = []
        best_chunk_ids: List[str] = []
        for idx, ctext in enumerate(chunk_texts):
            strength = _overlap_to_chunk(sent, ctext)
            if strength > best_strength:
                best_strength = strength
                ch = chunks[idx] if idx < len(chunks) else {}
                meta = ch.get("metadata") or {}
                best_chunks = [(meta.get("title") or ch.get("title") or f"chunk_{idx}")[:50]]
                best_chunk_ids = [
                    str(ch.get("chunk_id") or meta.get("chunk_id") or f"chunk_{idx}")
                ]

        ctx_strength = _overlap_to_chunk(sent, context) if context else 0.0
        if ctx_strength > best_strength:
            best_strength = ctx_strength
            best_chunks = ["context_block"]

        n_support, support_keys = count_supporting_chunks(sent, chunks, threshold=threshold * 0.85)
        infer_dist = inference_distance_score(sent, context, chunk_texts)
        generic_hit = bool(DEFINITIVE_STRATEGIC_PATTERNS.search(sent))
        needs_consensus = is_strategic_recommendation_claim(sent, query)

        grounded = best_strength >= threshold
        inferable = infer_dist <= max_inference
        required_chunks = min_chunks_strategic if needs_consensus else 1
        consensus_ok = (n_support >= required_chunks) or best_strength >= 0.52

        if generic_hit and best_strength < min_strength:
            grounded = False
        if not inferable:
            grounded = False
        if needs_consensus and not consensus_ok:
            grounded = False

        rec = {
            "claim": sent[:280],
            "support_chunks": support_keys or best_chunks,
            "support_chunk_ids": best_chunk_ids,
            "supporting_chunk_count": n_support,
            "grounded": grounded,
            "inferable": inferable,
            "support_strength": round(best_strength, 3),
            "inference_distance_score": infer_dist,
            "generic_definitive": generic_hit,
            "requires_consensus": needs_consensus,
        }
        claim_records.append(rec)
        if not grounded:
            unsupported.append(rec)
        if infer_dist > max_inference:
            high_inference.append(rec)

    total = len(claim_records) or 1
    grounded_count = sum(1 for r in claim_records if r["grounded"])
    ratio = grounded_count / total
    avg_inference = sum(r["inference_distance_score"] for r in claim_records) / total

    return {
        "claims": claim_records[:15],
        "unsupported_claims": unsupported[:8],
        "high_inference_claims": high_inference[:6],
        "unsupported_count": len(unsupported),
        "high_inference_count": len(high_inference),
        "claim_grounded_ratio": round(ratio, 3),
        "avg_inference_distance": round(avg_inference, 3),
        "hallucination_flags": len(unsupported) > 0 or len(high_inference) > 0,
        "verified_sentence_ratio": round(ratio, 3),
        "force_exploratory_mode": avg_inference > float(
            getattr(settings, "INFERENCE_FORCE_EXPLORATORY_THRESHOLD", 0.42)
        ),
    }


def adaptive_confidence_prefix(confidence_score: float) -> str:
    """Dynamic hedging language by confidence band."""
    high = float(getattr(settings, "ENTERPRISE_CONFIDENCE_HIGH", 0.78))
    moderate = float(getattr(settings, "ENTERPRISE_CONFIDENCE_MODERATE", 0.55))
    if confidence_score >= high:
        return "The brand book strongly supports that "
    if confidence_score >= moderate:
        return "The current strategic direction suggests that "
    return "Based on limited supporting context, "


def apply_adaptive_confidence_language(
    answer: str,
    confidence_score: float,
    claim_verification: Optional[Dict[str, Any]] = None,
) -> Tuple[str, bool]:
    """
    Prefix paragraphs with calibrated confidence when overall support is weak.
    """
    if not answer or confidence_score >= float(getattr(settings, "ENTERPRISE_CONFIDENCE_HIGH", 0.78)):
        return answer, False

    verification = claim_verification or {}
    weak_claims = [
        c for c in (verification.get("claims") or [])
        if not c.get("grounded") or float(c.get("support_strength") or 0) < 0.5
    ]
    if not weak_claims and confidence_score >= 0.6:
        return answer, False

    prefix = adaptive_confidence_prefix(confidence_score)
    lines = answer.strip().split("\n\n")
    if lines and not lines[0].lower().startswith(
        ("the brand book", "the current strategic", "based on limited", "it appears")
    ):
        lines[0] = prefix + lines[0][0].lower() + lines[0][1:] if lines[0] else lines[0]
        return "\n\n".join(lines), True
    return answer, False


def build_inference_repair_instructions(verification: Dict[str, Any]) -> str:
    lines = [
        "INFERENCE REPAIR (mandatory):",
        "Remove or hedge claims that extrapolate beyond retrieved brand book evidence.",
    ]
    for u in (verification.get("high_inference_claims") or [])[:5]:
        lines.append(
            f"- HIGH INFERENCE (distance {u.get('inference_distance_score')}): "
            f"\"{u.get('claim', '')[:160]}\""
        )
    for u in (verification.get("unsupported_claims") or [])[:4]:
        if u not in (verification.get("high_inference_claims") or []):
            lines.append(
                f"- LOW SUPPORT (strength {u.get('support_strength')}): "
                f"\"{u.get('claim', '')[:160]}\""
            )
    lines.append(strict_evidence_prompt())
    return "\n".join(lines)


def should_regenerate_for_cognition(verification: Dict[str, Any]) -> bool:
    max_unsupported = int(getattr(settings, "MAX_UNSUPPORTED_CLAIMS_BEFORE_REGEN", 0))
    max_inference = int(getattr(settings, "MAX_HIGH_INFERENCE_BEFORE_REGEN", 1))
    return (
        int(verification.get("unsupported_count") or 0) > max_unsupported
        or int(verification.get("high_inference_count") or 0) > max_inference
    )
