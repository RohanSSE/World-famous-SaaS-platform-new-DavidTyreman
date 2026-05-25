"""
Adaptive self-repair — detect weaknesses and regenerate with constraints.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from django.conf import settings

from .claim_verification import detect_unsupported_claims, verify_answer_against_context
from .rag_evaluation import detect_ungrounded_generic_filler, score_strategic_specificity
from .reasoning_drift import score_reasoning_drift

CRITIQUE_FLAGS = (
    "weak_manifesto_support",
    "generic_reasoning",
    "reasoning_drift",
    "unsupported_claim",
    "context_conflict",
    "low_strategic_density",
    "low_confidence_overclaim",
)

REASONING_CONSTRAINTS = {
    "must_reference_brand_book": True,
    "must_reference_manifesto": True,
    "avoid_generic_advice": True,
    "preserve_strategic_identity": True,
    "avoid_unattributed_claims": True,
}

OVERCLAIM_HEDGE_PREFIX = (
    "Based on the retrieved brand book and strategic context, "
)

CONSERVATIVE_PHRASES = (
    "it appears",
    "the current strategic direction suggests",
    "based on the available context",
    "the evidence in your knowledge base indicates",
)

DEFINITIVE_PATTERNS = re.compile(
    r"\b(you must always|guaranteed|definitely will|never fail|"
    r"the only way is|every brand should|without exception)\b",
    re.I,
)


def detect_critique_flags(
    draft: str,
    context: str,
    context_quality: Optional[Dict[str, Any]] = None,
    verification: Optional[Dict[str, Any]] = None,
    drift: Optional[Dict[str, Any]] = None,
    retrieval_critique: Optional[Dict[str, Any]] = None,
    confidence_score: Optional[float] = None,
    strategic_query: bool = False,
) -> List[str]:
    """Rule-based weakness detection for self-repair loop."""
    flags: List[str] = []
    context_quality = context_quality or {}
    verification = verification or {}
    drift = drift or {}
    retrieval_critique = retrieval_critique or {}

    dom = float(context_quality.get("manifesto_dominance") or 0)
    density = float(context_quality.get("strategic_density") or 1)
    conflict = float(context_quality.get("context_conflict_score") or 0)

    if strategic_query and dom < float(getattr(settings, "CONTEXT_REPAIR_MANIFESTO_THRESHOLD", 0.50)):
        flags.append("weak_manifesto_support")
    if density < float(getattr(settings, "CONTEXT_MIN_STRATEGIC_DENSITY", 0.60)):
        flags.append("low_strategic_density")
    if conflict > float(getattr(settings, "CONTEXT_REPAIR_CONFLICT_THRESHOLD", 0.30)):
        flags.append("context_conflict")

    filler = detect_ungrounded_generic_filler(draft, context)
    if len(filler) >= 1:
        flags.append("generic_reasoning")
    if score_strategic_specificity(draft, context, []) < 0.30:
        flags.append("generic_reasoning")

    if drift.get("drift_detected") or float(drift.get("reasoning_drift_score") or 0) >= 0.35:
        flags.append("reasoning_drift")

    unsupported = verification.get("unsupported_claims") or detect_unsupported_claims(draft, context)
    if unsupported or int(verification.get("unsupported_count") or 0) > 1:
        flags.append("unsupported_claim")
    if int(verification.get("high_inference_count") or 0) > 0:
        flags.append("unsupported_claim")

    rc_flags = retrieval_critique.get("flags") or []
    if "context_conflict" in rc_flags and "context_conflict" not in flags:
        flags.append("context_conflict")

    conf = confidence_score if confidence_score is not None else 1.0
    if conf < float(getattr(settings, "OVERCLAIM_CONFIDENCE_THRESHOLD", 0.60)):
        flags.append("low_confidence_overclaim")

    return list(dict.fromkeys(flags))


def build_reasoning_constraints_prompt(
    flags: List[str],
    constraints: Optional[Dict[str, bool]] = None,
) -> str:
    """Inject into improve/repair stage."""
    constraints = constraints or REASONING_CONSTRAINTS
    lines = ["REASONING CONSTRAINTS (mandatory):"]

    if constraints.get("must_reference_brand_book") or constraints.get("must_reference_manifesto") or "weak_manifesto_support" in flags:
        lines.append("- Anchor every recommendation in the brand book or retrieved strategic excerpts.")
    if constraints.get("avoid_generic_advice") or "generic_reasoning" in flags:
        lines.append("- Remove generic marketing filler; use named concepts from context only.")
    if constraints.get("preserve_strategic_identity") or "reasoning_drift" in flags:
        lines.append("- Preserve trust/premium/authority framing; do not drift to viral or hype tactics.")
    if constraints.get("avoid_unattributed_claims") or "unsupported_claim" in flags:
        lines.append("- Do not state principles not present in context; hedge or omit unsupported claims.")
    if "context_conflict" in flags:
        lines.append("- Resolve mixed signals toward brand-book-grounded consistency.")
    if "low_confidence_overclaim" in flags:
        lines.append(
            '- Use calibrated language: "it appears", "the strategic direction suggests" — '
            "no definitive guarantees."
        )
    if "low_strategic_density" in flags:
        lines.append("- Increase strategic specificity; cite brand book principles explicitly.")

    return "\n".join(lines)


def build_repair_instructions(flags: List[str]) -> str:
    """Human-readable repair directives for improve_draft."""
    parts = [build_reasoning_constraints_prompt(flags)]
    if "weak_manifesto_support" in flags:
        parts.append("REPAIR: Strengthen brand book grounding — reference core beliefs and promise kept.")
    if "generic_reasoning" in flags:
        parts.append("REPAIR: Replace abstract advice with context-specific strategic language.")
    if "reasoning_drift" in flags:
        parts.append("REPAIR: Align tone with trust/consistency; remove conflicting growth-hack framing.")
    if "unsupported_claim" in flags:
        parts.append("REPAIR: Remove or rewrite unsupported sentences.")
    return "\n\n".join(parts)


def apply_overclaim_suppression(answer: str, confidence_score: float) -> Tuple[str, bool]:
    """
    Soften definitive claims when confidence is low.
    Returns (answer, was_modified).
    """
    threshold = float(getattr(settings, "OVERCLAIM_CONFIDENCE_THRESHOLD", 0.60))
    if not answer or confidence_score >= threshold:
        return answer, False

    text = answer.strip()
    modified = False

    if not any(p in text.lower()[:120] for p in CONSERVATIVE_PHRASES):
        text = OVERCLAIM_HEDGE_PREFIX + text[0].lower() + text[1:] if text else text
        modified = True

    def _soften(match):
        return "often " + match.group(0).lower()

    softened, n = DEFINITIVE_PATTERNS.subn(_soften, text)
    if n:
        text = softened
        modified = True

    return text, modified


def run_self_repair_pass(
    client,
    model: str,
    query: str,
    context: str,
    draft: str,
    flags: List[str],
    temperature: float = 0.5,
    max_tokens: int = 1200,
) -> Tuple[str, Dict[str, Any]]:
    """
    Regenerate answer with repair constraints when critique flags present.
    """
    from .rag_quality_pipeline import improve_draft

    if not flags:
        return draft, {"repaired": False, "flags": []}

    instructions = build_repair_instructions(flags)
    repaired = improve_draft(client, model, query, context, draft, instructions)
    return repaired, {"repaired": True, "flags": flags, "repair_instructions": instructions[:500]}
