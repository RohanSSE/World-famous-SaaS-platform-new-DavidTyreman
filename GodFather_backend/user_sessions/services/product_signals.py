"""
Real-user product signals — adoption moat analytics (no new cognition architecture).
"""
from __future__ import annotations

from datetime import timedelta
from typing import Any, Dict

from django.db.models import Avg, Count
from django.utils import timezone


def record_product_signal(session_id: int, signal: str, meta: Dict[str, Any] | None = None) -> None:
    try:
        from user_sessions.models import BrandMemory
        import json

        key = "product_signals"
        row = BrandMemory.objects.filter(session_id=session_id, key=key).first()
        events = list((row.value or {}).get("events", [])) if row else []
        events.append(
            {
                "signal": signal,
                "meta": meta or {},
                "at": timezone.now().isoformat(),
            }
        )
        events = events[-200:]
        BrandMemory.objects.update_or_create(
            session_id=session_id,
            key=key,
            defaults={
                "memory_type": "preference",
                "content": json.dumps(events[-1], ensure_ascii=False)[:500],
                "value": {"events": events},
                "importance_score": 0.6,
            },
        )
    except Exception:
        pass


def get_product_signals_dashboard(days: int = 14) -> Dict[str, Any]:
    from user_sessions.models import BrandMemory, AIRequestTrace, Session

    since = timezone.now() - timedelta(days=days)
    export_rows = BrandMemory.objects.filter(key="export_audit", updated_at__gte=since)
    feedback_rows = BrandMemory.objects.filter(key="feedback_learning_profile")
    signal_rows = BrandMemory.objects.filter(key="product_signals", updated_at__gte=since)

    export_count = 0
    export_by_format: Dict[str, int] = {}
    for row in export_rows:
        for e in (row.value or {}).get("entries", []):
            export_count += 1
            fmt = e.get("format", "unknown")
            export_by_format[fmt] = export_by_format.get(fmt, 0) + 1

    feedback_sessions = feedback_rows.count()
    traces = AIRequestTrace.objects.filter(created_at__gte=since)
    trace_agg = traces.aggregate(
        avg_ms=Avg("total_ms"),
        avg_hall=Avg("hallucination_risk"),
        count=Count("id"),
    )

    signal_counts: Dict[str, int] = {}
    for row in signal_rows:
        for ev in (row.value or {}).get("events", []):
            s = ev.get("signal", "unknown")
            signal_counts[s] = signal_counts.get(s, 0) + 1

    active_sessions = Session.objects.filter(updated_at__gte=since).count()

    return {
        "period_days": days,
        "active_sessions": active_sessions,
        "export_count": export_count,
        "export_by_format": export_by_format,
        "feedback_learning_sessions": feedback_sessions,
        "ai_requests": trace_agg.get("count") or 0,
        "avg_latency_ms": int(trace_agg.get("avg_ms") or 0),
        "avg_hallucination_risk": round(float(trace_agg.get("avg_hall") or 0), 3),
        "product_signal_counts": signal_counts,
    }
