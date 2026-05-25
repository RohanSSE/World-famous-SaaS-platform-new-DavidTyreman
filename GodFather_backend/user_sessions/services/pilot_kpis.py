"""
Pilot validation KPIs — business metrics from real usage signals.
"""
from __future__ import annotations

from collections import Counter
from datetime import timedelta
from typing import Any, Dict, List, Optional

from django.utils import timezone


def _events_for_session(session_id: int) -> List[Dict[str, Any]]:
    try:
        from user_sessions.models import BrandMemory

        row = BrandMemory.objects.filter(session_id=session_id, key="product_signals").first()
        return list((row.value or {}).get("events", [])) if row else []
    except Exception:
        return []


def get_session_pilot_kpis(session_id: int) -> Dict[str, Any]:
    events = _events_for_session(session_id)
    counts = Counter(e.get("signal") for e in events)

    exports = counts.get("export", 0)
    edits = counts.get("feedback_edit", 0) + counts.get("user_edit", 0)
    workflow_runs = counts.get("workflow_run", 0)
    regenerations = counts.get("workflow_rerun", 0)
    demo_runs = counts.get("demo_pack", 0)

    export_audit = 0
    feedback_profile = False
    try:
        from user_sessions.models import BrandMemory

        ex = BrandMemory.objects.filter(session_id=session_id, key="export_audit").first()
        if ex:
            export_audit = len((ex.value or {}).get("entries", []))
        feedback_profile = BrandMemory.objects.filter(
            session_id=session_id, key="feedback_learning_profile"
        ).exists()
    except Exception:
        pass

    traces = 0
    avg_ms = 0
    try:
        from user_sessions.models import AIRequestTrace
        from django.db.models import Avg

        qs = AIRequestTrace.objects.filter(session_id=session_id)
        traces = qs.count()
        avg_ms = int(qs.aggregate(a=Avg("total_ms"))["a"] or 0)
    except Exception:
        pass

    checklist = {
        "knowledge_uploaded": counts.get("document_upload", 0) > 0,
        "onboarding_started": counts.get("onboarding_step", 0) > 0,
        "workflow_generated": workflow_runs > 0 or demo_runs > 0,
        "export_downloaded": exports > 0 or export_audit > 0,
        "feedback_saved": edits > 0 or feedback_profile,
        "learning_applied": feedback_profile,
    }
    completed = sum(1 for v in checklist.values() if v)

    return {
        "session_id": session_id,
        "export_downloads": max(exports, export_audit),
        "user_edits": edits,
        "workflow_runs": workflow_runs,
        "regeneration_count": regenerations,
        "demo_pack_runs": demo_runs,
        "ai_requests": traces,
        "avg_latency_ms": avg_ms,
        "feedback_learning_active": feedback_profile,
        "pilot_checklist": checklist,
        "pilot_completion_pct": round(100 * completed / max(len(checklist), 1)),
        "engagement_score": min(
            100,
            exports * 15 + edits * 20 + workflow_runs * 10 + (20 if feedback_profile else 0),
        ),
    }


def get_user_pilot_summary(user_id: int, days: int = 30) -> Dict[str, Any]:
    from user_sessions.models import Session, BrandMemory

    since = timezone.now() - timedelta(days=days)
    sessions = Session.objects.filter(created_by_id=user_id, updated_at__gte=since)
    session_ids = list(sessions.values_list("id", flat=True)[:50])

    totals = Counter()
    for sid in session_ids:
        for e in _events_for_session(sid):
            totals[e.get("signal", "unknown")] += 1

    export_rows = BrandMemory.objects.filter(key="export_audit", session_id__in=session_ids)
    total_exports = 0
    for row in export_rows:
        total_exports += len((row.value or {}).get("entries", []))

    return {
        "period_days": days,
        "active_sessions": len(session_ids),
        "total_exports": total_exports + totals.get("export", 0),
        "total_edits": totals.get("feedback_edit", 0),
        "total_workflow_runs": totals.get("workflow_run", 0),
        "total_regenerations": totals.get("workflow_rerun", 0),
        "signal_breakdown": dict(totals),
    }
