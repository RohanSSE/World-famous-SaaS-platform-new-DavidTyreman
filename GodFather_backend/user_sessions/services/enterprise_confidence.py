"""
Enterprise confidence engine — multi-signal trust score for UX and gating.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from django.conf import settings

from .retrieval_confidence import confidence_label

RETRIEVAL_MODE_SCORE = {
    "high_confidence": 0.92,
    "moderate": 0.72,
    "low_confidence": 0.48,
}


def compute_enterprise_confidence(
    retrieval_mode: str,
    avg_hybrid_score: float,
    sources: List[Dict[str, Any]],
    evaluation: Optional[Dict[str, Any]] = None,
    verification: Optional[Dict[str, Any]] = None,
    memory_conflicts: Optional[List[Dict[str, Any]]] = None,
    context_quality: Optional[Dict[str, Any]] = None,
    reasoning_drift: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    confidence =
      retrieval_confidence × source_reliability × grounded_ratio ×
      unsupported_penalty × memory_conflict_penalty × specificity
    """
    evaluation = evaluation or {}
    verification = verification or {}
    memory_conflicts = memory_conflicts or []
    context_quality = context_quality or {}
    reasoning_drift = reasoning_drift or {}

    rc = RETRIEVAL_MODE_SCORE.get(retrieval_mode, 0.65)
    if avg_hybrid_score > 0:
        rc = min(1.0, rc * (0.85 + 0.15 * min(1.0, avg_hybrid_score)))

    reliabilities = [
        float(s.get("source_reliability") or 0.7) for s in (sources or [])[:5]
    ]
    rel = sum(reliabilities) / len(reliabilities) if reliabilities else 0.65

    grounded = float(
        evaluation.get("grounded_answer_ratio")
        or evaluation.get("groundedness")
        or 0.5
    )
    specificity = float(evaluation.get("strategic_specificity_score") or 0.5)

    unsupported = int(verification.get("unsupported_count") or 0)
    unsupported_penalty = max(0.5, 1.0 - unsupported * 0.08)

    conflict_penalty = max(0.7, 1.0 - len(memory_conflicts) * 0.12)

    ctx_conflict = float(context_quality.get("context_conflict_score") or 0)
    context_penalty = max(0.75, 1.0 - ctx_conflict * 0.5)

    drift = float(reasoning_drift.get("reasoning_drift_score") or 0)
    drift_penalty = max(0.7, 1.0 - drift * 0.45)

    density = float(context_quality.get("strategic_density") or specificity)
    density_factor = max(0.75, min(1.0, density + 0.15))

    filler = float(evaluation.get("generic_filler_ratio") or 0)
    filler_penalty = max(0.75, 1.0 - filler * 0.4)

    raw = (
        rc
        * rel
        * grounded
        * unsupported_penalty
        * conflict_penalty
        * context_penalty
        * drift_penalty
        * filler_penalty
        * density_factor
    )
    raw = raw * (0.7 + 0.3 * specificity)

    score = round(max(0.0, min(1.0, raw)), 3)

    if score >= float(getattr(settings, "ENTERPRISE_CONFIDENCE_HIGH", 0.78)):
        label = "High Confidence"
    elif score >= float(getattr(settings, "ENTERPRISE_CONFIDENCE_MODERATE", 0.55)):
        label = "Moderate Confidence"
    else:
        label = "Low Confidence"

    return {
        "confidence_score": score,
        "confidence_label": label,
        "retrieval_mode": retrieval_mode,
        "retrieval_mode_label": confidence_label(retrieval_mode),
        "components": {
            "retrieval": round(rc, 3),
            "source_reliability": round(rel, 3),
            "grounded_ratio": round(grounded, 3),
            "specificity": round(specificity, 3),
            "unsupported_penalty": round(unsupported_penalty, 3),
            "memory_conflict_penalty": round(conflict_penalty, 3),
            "filler_penalty": round(filler_penalty, 3),
            "context_conflict_penalty": round(context_penalty, 3),
            "reasoning_drift_penalty": round(drift_penalty, 3),
            "strategic_density_factor": round(density_factor, 3),
        },
    }
