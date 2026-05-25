"""
Enterprise product observability — golden metrics + runtime signals.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from django.conf import settings


def get_product_observability_dashboard() -> Dict[str, Any]:
    """Dashboard payload for admin / ops — no new architecture."""
    root = Path(settings.BASE_DIR) / "evaluation"
    official = root / "official_baseline.json"
    golden = root / "golden_baseline.json"
    path = official if official.exists() else golden

    metrics: Dict[str, Any] = {}
    passed = 0
    cases = 0
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        metrics = data.get("metrics", {})
        passed = data.get("passed", 0)
        cases = data.get("cases", 0)

    trace_stats = {"total_traces_24h": 0, "avg_latency_ms": 0, "avg_hallucination_risk": None}
    try:
        from django.db.models import Avg, Count
        from django.utils import timezone
        from datetime import timedelta
        from user_sessions.models import AIRequestTrace

        since = timezone.now() - timedelta(hours=24)
        qs = AIRequestTrace.objects.filter(created_at__gte=since)
        trace_stats["total_traces_24h"] = qs.count()
        agg = qs.aggregate(avg_ms=Avg("total_ms"), avg_hall=Avg("hallucination_risk"))
        trace_stats["avg_latency_ms"] = int(agg["avg_ms"] or 0)
        trace_stats["avg_hallucination_risk"] = round(float(agg["avg_hall"] or 0), 3) if agg["avg_hall"] else None
        trace_stats["pipeline_breakdown"] = list(
            qs.values("pipeline").annotate(c=Count("id")).order_by("-c")[:8]
        )
    except Exception:
        pass

    targets = {
        "pass_rate": 0.75,
        "hallucination_risk": 0.20,
        "grounded_answer_ratio": 0.90,
        "retrieval_precision": 0.75,
        "unsupported_claim_rate": 0.25,
        "consistency_score_avg": 0.75,
    }

    health = []
    pr = (passed / cases) if cases else 0
    health.append({"metric": "pass_rate", "value": round(pr, 3), "target": targets["pass_rate"], "ok": pr >= 0.75})
    for key, (op, tgt) in [
        ("hallucination_risk", ("<", targets["hallucination_risk"])),
        ("grounded_answer_ratio", (">", targets["grounded_answer_ratio"])),
        ("retrieval_precision", (">", targets["retrieval_precision"])),
        ("unsupported_claim_rate", ("<", targets["unsupported_claim_rate"])),
        ("consistency_score_avg", (">", targets["consistency_score_avg"])),
    ]:
        val = metrics.get(key)
        if val is None:
            continue
        ok = (val < tgt) if op == "<" else (val > tgt)
        health.append({"metric": key, "value": val, "target": tgt, "ok": ok})

    learning_stats = {"feedback_sessions": 0, "export_count_7d": 0}
    try:
        from user_sessions.models import BrandMemory

        learning_stats["feedback_sessions"] = BrandMemory.objects.filter(
            key="feedback_learning_profile"
        ).count()
        learning_stats["export_count_7d"] = BrandMemory.objects.filter(key="export_audit").count()
    except Exception:
        pass

    workflow_usage = {}
    try:
        from user_sessions.services.admin_cognition_api import get_workflow_usage_stats

        workflow_usage = get_workflow_usage_stats(days=7)
    except Exception:
        pass

    return {
        "phase": "productization",
        "architecture_frozen": True,
        "golden_passed": passed,
        "golden_cases": cases,
        "metrics": metrics,
        "targets": targets,
        "health": health,
        "runtime_24h": trace_stats,
        "baseline_file": str(path.name) if path.exists() else None,
        "learning": learning_stats,
        "workflow_usage": workflow_usage,
    }
