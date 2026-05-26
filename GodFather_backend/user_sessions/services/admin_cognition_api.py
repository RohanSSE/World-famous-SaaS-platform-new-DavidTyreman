"""
Admin cognition & review APIs — traces, feedback, exports (architecture frozen).
"""
from __future__ import annotations

from typing import Any, Dict, List

from django.db.models import Avg, Count
from django.utils import timezone
from datetime import timedelta


def get_cognition_traces(limit: int = 50) -> List[Dict[str, Any]]:
    from user_sessions.models import AIRequestTrace

    rows = AIRequestTrace.objects.order_by("-created_at")[:limit]
    return [
        {
            "id": t.id,
            "session_id": t.session_id,
            "agent_id": t.agent_id,
            "pipeline": t.pipeline,
            "query_preview": (t.query or "")[:120],
            "total_ms": t.total_ms,
            "hallucination_risk": t.hallucination_risk,
            "confidence_score": t.confidence_score,
            "retrieval_confidence": t.retrieval_confidence,
            "created_at": t.created_at.isoformat(),
        }
        for t in rows
    ]


def get_feedback_review(limit: int = 50) -> List[Dict[str, Any]]:
    from user_sessions.models import BrandMemory

    qs = BrandMemory.objects.filter(
        key__in=("feedback_learning_profile", "export_audit")
    ).order_by("-updated_at", "-created_at")[:limit]

    out = []
    for m in qs:
        out.append(
            {
                "session_id": m.session_id,
                "key": m.key,
                "memory_type": m.memory_type,
                "preview": (m.content or "")[:200],
                "value": m.value,
                "updated_at": getattr(m, "updated_at", m.created_at).isoformat()
                if hasattr(m, "updated_at")
                else m.created_at.isoformat(),
            }
        )
    return out


def get_failed_traces_high_risk(limit: int = 30) -> List[Dict[str, Any]]:
    from user_sessions.models import AIRequestTrace

    qs = (
        AIRequestTrace.objects.filter(hallucination_risk__gte=0.2)
        .order_by("-created_at")[:limit]
    )
    return get_cognition_traces_from_qs(qs)


def get_cognition_traces_from_qs(qs) -> List[Dict[str, Any]]:
    return [
        {
            "id": t.id,
            "session_id": t.session_id,
            "query_preview": (t.query or "")[:100],
            "hallucination_risk": t.hallucination_risk,
            "total_ms": t.total_ms,
            "pipeline": t.pipeline,
            "created_at": t.created_at.isoformat(),
        }
        for t in qs
    ]


def get_workflow_usage_stats(days: int = 7) -> Dict[str, Any]:
    """Proxy: agent_id branding / pipeline tags from traces."""
    from user_sessions.models import AIRequestTrace

    since = timezone.now() - timedelta(days=days)
    qs = AIRequestTrace.objects.filter(created_at__gte=since)
    by_agent = list(
        qs.values("agent_id").annotate(count=Count("id"), avg_ms=Avg("total_ms")).order_by("-count")[:12]
    )
    by_pipeline = list(
        qs.values("pipeline").annotate(count=Count("id")).order_by("-count")[:12]
    )
    return {
        "period_days": days,
        "total_requests": qs.count(),
        "by_agent": by_agent,
        "by_pipeline": by_pipeline,
    }


def get_live_cognition_metrics(minutes: int = 60) -> Dict[str, Any]:
    """Real-time cognition monitor — last N minutes of traces."""
    from user_sessions.models import AIRequestTrace

    since = timezone.now() - timedelta(minutes=minutes)
    qs = AIRequestTrace.objects.filter(created_at__gte=since).order_by("-created_at")
    traces = list(qs[:100])

    unsupported_est = 0
    repair_count = 0
    low_conf = 0
    hall_sum = 0.0
    hall_n = 0
    conf_labels: Dict[str, int] = {}

    for t in traces:
        stages = t.stages or {}
        verification = stages.get("verification") or {}
        unsupported_est += int(verification.get("unsupported_count") or 0)
        repair_count += int(stages.get("repair_count") or stages.get("repairs") or 0)
        rc = (t.retrieval_confidence or "").lower()
        conf_labels[rc] = conf_labels.get(rc, 0) + 1
        if rc in ("low", "weak", ""):
            low_conf += 1
        if t.hallucination_risk is not None:
            hall_sum += float(t.hallucination_risk)
            hall_n += 1

    export_success = 0
    try:
        from user_sessions.models import BrandMemory

        for row in BrandMemory.objects.filter(key="export_audit").order_by("-updated_at")[:20]:
            for e in (row.value or {}).get("entries", []):
                export_success += 1
    except Exception:
        pass

    return {
        "window_minutes": minutes,
        "request_count": len(traces),
        "avg_hallucination_risk": round(hall_sum / hall_n, 3) if hall_n else None,
        "estimated_unsupported_claims": unsupported_est,
        "repair_count": repair_count,
        "low_retrieval_confidence": low_conf,
        "retrieval_confidence_breakdown": conf_labels,
        "recent_exports": export_success,
        "avg_latency_ms": int(
            sum(t.total_ms for t in traces) / len(traces)
        )
        if traces
        else 0,
        "high_risk_queries": [
            {
                "id": t.id,
                "session_id": t.session_id,
                "hallucination_risk": t.hallucination_risk,
                "preview": (t.query or "")[:80],
            }
            for t in traces
            if (t.hallucination_risk or 0) >= 0.2
        ][:10],
    }
