"""
Autonomous evaluation clustering — prioritize failures by intent and type.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Dict, List

INTENT_FROM_CASE = {
    "trust": "trust",
    "premium": "premium",
    "differentiation": "differentiation",
    "authority": "authority",
    "manifesto": "manifesto",
    "positioning": "positioning",
    "emotional": "emotional",
    "tone": "tone",
    "competitor": "differentiation",
    "crisis": "trust",
    "dna": "manifesto",
}


def infer_intent(case_id: str, row: dict) -> str:
    cid = case_id.lower()
    for key, intent in INTENT_FROM_CASE.items():
        if key in cid:
            return intent
    return "general"


def cluster_evaluation_failures(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Cluster failures by intent, drift, contradiction, hallucination, context weakness.
    """
    failed = [r for r in rows if not r.get("pass", True)]
    by_intent: Counter = Counter()
    by_drift: Counter = Counter()
    by_hallucination: Counter = Counter()
    by_context: Counter = Counter()
    by_repair: Counter = Counter()

    for row in failed:
        iid = row.get("id", "")
        by_intent[infer_intent(iid, row)] += 1
        if float(row.get("reasoning_drift_score", 0)) > 0.35:
            by_drift["high_drift"] += 1
        elif float(row.get("reasoning_drift_score", 0)) > 0.2:
            by_drift["moderate_drift"] += 1
        if float(row.get("hallucination_risk", 0)) > 0.4:
            by_hallucination["high_hallucination"] += 1
        if float(row.get("manifesto_support_density", row.get("manifesto_dominance", 1))) < 0.5:
            by_context["weak_manifesto_context"] += 1
        if float(row.get("context_conflict_score", 0)) > 0.25:
            by_context["context_conflict"] += 1
        if row.get("overclaim_suppressed") or "low_confidence_overclaim" in (row.get("critique_flags") or []):
            by_hallucination["overclaim"] += 1
        if row.get("repair_success"):
            by_repair["repair_success"] += 1
        elif row.get("repaired"):
            by_repair["repair_failed"] += 1

    highest_intent = by_intent.most_common(1)[0][0] if by_intent else "general"
    highest_failure_cluster = f"{highest_intent}_queries"

    return {
        "highest_failure_cluster": highest_failure_cluster,
        "by_intent": dict(by_intent.most_common(10)),
        "by_drift_type": dict(by_drift),
        "by_hallucination_type": dict(by_hallucination),
        "by_context_weakness": dict(by_context),
        "by_repair_outcome": dict(by_repair),
        "failed_count": len(failed),
        "total_count": len(rows),
        "failure_rate": round(len(failed) / max(len(rows), 1), 3),
    }


def format_cluster_report(clusters: Dict[str, Any]) -> str:
    lines = [
        f"Highest failure cluster: {clusters.get('highest_failure_cluster')}",
        f"Failure rate: {clusters.get('failure_rate', 0):.0%}",
        "",
        "By intent:",
    ]
    for k, v in (clusters.get("by_intent") or {}).items():
        lines.append(f"  {k}: {v}")
    lines.append("\nContext weaknesses:")
    for k, v in (clusters.get("by_context_weakness") or {}).items():
        lines.append(f"  {k}: {v}")
    lines.append("\nRepair outcomes:")
    for k, v in (clusters.get("by_repair_outcome") or {}).items():
        lines.append(f"  {k}: {v}")
    return "\n".join(lines)
