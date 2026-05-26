"""
Enterprise reliability KPIs — repair success, overclaim rate, conflict rate.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


def score_repair_success(
    drift_before: float,
    drift_after: float,
    confidence_before: float,
    confidence_after: float,
    repaired: bool,
    critique_flags_before: Optional[List[str]] = None,
    critique_flags_after: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Did self-repair actually improve the answer?
    """
    repair_gain = round(confidence_after - confidence_before, 3)
    drift_improved = drift_after < drift_before - 0.05
    conf_improved = repair_gain > 0.03
    flags_reduced = (
        len(critique_flags_after or [])
        < len(critique_flags_before or [])
    ) if critique_flags_before is not None else False

    repair_success = repaired and (drift_improved or conf_improved or flags_reduced)

    return {
        "repair_gain": repair_gain,
        "drift_before": round(drift_before, 3),
        "drift_after": round(drift_after, 3),
        "confidence_before": round(confidence_before, 3),
        "confidence_after": round(confidence_after, 3),
        "repair_success": repair_success,
        "drift_improved": drift_improved,
    }


def estimate_confidence_proxy(
    context_quality: Dict[str, Any],
    verification: Dict[str, Any],
    drift: Dict[str, Any],
) -> float:
    """Lightweight confidence without full enterprise engine."""
    base = 0.65
    base += float(context_quality.get("strategic_density") or 0) * 0.15
    base += float(context_quality.get("manifesto_dominance") or 0) * 0.1
    base -= float(context_quality.get("context_conflict_score") or 0) * 0.2
    base -= float(drift.get("reasoning_drift_score") or 0) * 0.25
    base -= int(verification.get("unsupported_count") or 0) * 0.05
    return round(max(0.0, min(1.0, base)), 3)


def aggregate_reliability_kpis(rows: List[Dict[str, Any]]) -> Dict[str, float]:
    """Aggregate golden / eval rows into reliability dashboard metrics."""
    n = len(rows) or 1
    repaired_rows = [r for r in rows if r.get("repaired")]
    repair_successes = sum(1 for r in rows if r.get("repair_success"))

    return {
        "reasoning_drift_avg": round(
            sum(r.get("reasoning_drift_score", 0) for r in rows) / n, 3
        ),
        "overclaim_rate": round(
            sum(1 for r in rows if r.get("overclaim_suppressed") or "low_confidence_overclaim" in (r.get("critique_flags") or []))
            / n,
            3,
        ),
        "manifesto_support_density": round(
            sum(r.get("manifesto_support_density", r.get("manifesto_dominance", 0)) for r in rows) / n,
            3,
        ),
        "context_conflict_rate": round(
            sum(1 for r in rows if float(r.get("context_conflict_score", 0)) > 0.25) / n,
            3,
        ),
        "consistency_score_avg": round(
            sum(r.get("consistency_score", 0) for r in rows) / n, 3
        ),
        "self_repair_success_rate": round(
            repair_successes / max(len(repaired_rows), 1), 3
        ) if repaired_rows else 0.0,
        "repair_gain_avg": round(
            sum(r.get("repair_gain", 0) for r in rows) / n, 3
        ),
        "strategic_density_avg": round(
            sum(r.get("strategic_density", 0) for r in rows) / n, 3
        ),
    }
