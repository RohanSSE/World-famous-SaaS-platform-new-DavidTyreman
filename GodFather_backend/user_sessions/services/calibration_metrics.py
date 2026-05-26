"""
Calibration & stability — split hallucination components and calibrated pass rules.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from django.conf import settings


def compute_split_hallucination_metrics(
    claim_verification: Optional[Dict[str, Any]] = None,
    context_quality: Optional[Dict[str, Any]] = None,
    overclaim_suppressed: bool = False,
    critique_flags: Optional[List[str]] = None,
) -> Dict[str, float]:
    """
    Split hallucination into interpretable rates (inference != hallucination).
    """
    cv = claim_verification or {}
    cq = context_quality or {}
    flags = critique_flags or []
    claims = cv.get("claims") or []
    total = max(len(claims), 1)

    unsupported_claim_rate = round(
        int(cv.get("unsupported_count") or 0) / total,
        3,
    )
    high_inference_claims = cv.get("high_inference_claims") or []
    high_inference_rate = round(
        len(high_inference_claims) / total,
        3,
    )
    if not high_inference_claims and cv.get("high_inference_count"):
        high_inference_rate = round(
            int(cv["high_inference_count"]) / total,
            3,
        )

    contradiction_rate = round(
        float(cq.get("context_conflict_score") or 0),
        3,
    )
    if contradiction_rate == 0 and cq.get("context_conflicts"):
        contradiction_rate = min(1.0, len(cq["context_conflicts"]) * 0.25)

    overclaim_rate = 0.0
    if overclaim_suppressed or "low_confidence_overclaim" in flags:
        overclaim_rate = 1.0 if overclaim_suppressed else 0.5
    overclaim_rate = round(overclaim_rate, 3)

    return {
        "unsupported_claim_rate": unsupported_claim_rate,
        "high_inference_rate": high_inference_rate,
        "contradiction_rate": contradiction_rate,
        "overclaim_rate": overclaim_rate,
    }


def estimate_hallucination_risk_calibrated(
    split: Dict[str, float],
    grounded_answer_ratio: float = 0.0,
    claim_grounded_ratio: float = 0.0,
) -> float:
    """
    Calibrated composite — does NOT treat high_inference as full hallucination.
    """
    w_unsup = float(getattr(settings, "HALLUCINATION_WEIGHT_UNSUPPORTED", 0.50))
    w_contra = float(getattr(settings, "HALLUCINATION_WEIGHT_CONTRADICTION", 0.30))
    w_over = float(getattr(settings, "HALLUCINATION_WEIGHT_OVERCLAIM", 0.20))

    score = (
        split.get("unsupported_claim_rate", 0) * w_unsup
        + split.get("contradiction_rate", 0) * w_contra
        + split.get("overclaim_rate", 0) * w_over
    )

    # Grounding reduces perceived risk (system is evidence-bound)
    grounding_bonus = 0.5 * max(claim_grounded_ratio, grounded_answer_ratio)
    score = max(0.0, score - grounding_bonus * 0.35)

    return round(min(1.0, score), 3)


def evaluate_calibrated_pass(
    scores: Dict[str, Any],
    forbidden_clean: bool = True,
) -> bool:
    """
    Golden / eval pass — aligned with calibrated cognition (not legacy groundedness only).
    """
    if not forbidden_clean:
        return False

    claim_ratio = float(
        scores.get("claim_grounded_ratio")
        if scores.get("claim_grounded_ratio") is not None
        else scores.get("grounded_answer_ratio") or 0
    )
    consistency = float(scores.get("consistency_score", 0) or 0)
    hallucination = float(
        scores["hallucination_risk"] if "hallucination_risk" in scores else 1.0
    )
    unsupported = int(scores.get("unsupported_count", 0) or 0)
    unsupported_rate = float(scores.get("unsupported_claim_rate", 0) or 0)
    overclaim = float(scores.get("overclaim_rate", 0) or 0)

    min_claim = float(getattr(settings, "PASS_MIN_CLAIM_GROUNDED_RATIO", 0.45))
    min_consistency = float(getattr(settings, "PASS_MIN_CONSISTENCY", 0.50))
    max_hallucination = float(getattr(settings, "PASS_MAX_HALLUCINATION_RISK", 0.50))
    max_unsupported = int(getattr(settings, "PASS_MAX_UNSUPPORTED_COUNT", 6))
    max_unsupported_rate = float(getattr(settings, "PASS_MAX_UNSUPPORTED_RATE", 0.55))
    max_overclaim = float(getattr(settings, "PASS_MAX_OVERCLAIM_RATE", 0.55))

    if claim_ratio < min_claim:
        return False
    if consistency < min_consistency:
        return False
    if hallucination > max_hallucination:
        return False
    grounded_ratio = float(scores.get("grounded_answer_ratio") or claim_ratio)
    if unsupported > max_unsupported and claim_ratio < 0.55 and grounded_ratio < 0.85:
        return False
    if unsupported_rate > max_unsupported_rate and claim_ratio < 0.50 and grounded_ratio < 0.80:
        return False
    if overclaim > max_overclaim and hallucination > 0.25:
        return False

    if scores.get("expected_categories") and scores.get("top1_hit") is False:
        return False

    concept = float(scores.get("concept_score") or scores.get("citation_score") or 0)
    if concept < 0.2:
        return False

    return True
