"""
AI Operations intelligence — admin layer for pilot validation.
"""
from __future__ import annotations

from typing import Any, Dict, List

from django.db.models import Avg, Count
from django.utils import timezone
from datetime import timedelta


def get_ops_intelligence(days: int = 14) -> Dict[str, Any]:
    from user_sessions.models import AIRequestTrace, BrandMemory
    from user_sessions.services.chunk_quality_audit import audit_chunks

    since = timezone.now() - timedelta(days=days)
    traces = AIRequestTrace.objects.filter(created_at__gte=since)

    high_repair_sessions: List[Dict[str, Any]] = []
    by_session: Dict[int, Dict[str, Any]] = {}
    for t in traces[:500]:
        sid = t.session_id or 0
        if sid not in by_session:
            by_session[sid] = {"session_id": sid, "requests": 0, "repairs": 0, "high_hall": 0}
        by_session[sid]["requests"] += 1
        stages = t.stages or {}
        by_session[sid]["repairs"] += int(stages.get("repair_count") or 0)
        if (t.hallucination_risk or 0) >= 0.2:
            by_session[sid]["high_hall"] += 1

    for v in sorted(by_session.values(), key=lambda x: x["repairs"], reverse=True)[:10]:
        if v["repairs"] >= 1:
            high_repair_sessions.append(v)

    workflow_failures = list(
        traces.filter(hallucination_risk__gte=0.25)
        .values("pipeline", "agent_id")
        .annotate(c=Count("id"), avg_hall=Avg("hallucination_risk"))
        .order_by("-c")[:8]
    )

    edited_outputs = []
    for row in BrandMemory.objects.filter(key="feedback_learning_profile").order_by("-updated_at")[:15]:
        prof = row.value or {}
        edited_outputs.append(
            {
                "session_id": row.session_id,
                "preferred_phrases": (prof.get("preferred_phrases") or [])[:5],
                "rejected_phrases": (prof.get("rejected_phrases") or [])[:5],
                "edit_count": prof.get("edit_count", 0),
            }
        )

    chunk_audit = audit_chunks(limit=300)
    weak_alerts = (chunk_audit.get("generic_chunks") or [])[:8]

    consistency_drift = list(
        traces.exclude(confidence_score__isnull=True)
        .order_by("-created_at")[:20]
        .values("session_id", "confidence_score", "hallucination_risk", "created_at")
    )

    export_hot = []
    for row in BrandMemory.objects.filter(key="export_audit").order_by("-updated_at")[:10]:
        entries = (row.value or {}).get("entries", [])
        export_hot.append({"session_id": row.session_id, "export_count": len(entries), "last": entries[-1] if entries else None})

    return {
        "period_days": days,
        "high_repair_sessions": high_repair_sessions,
        "workflows_needing_attention": workflow_failures,
        "most_edited_outputs": edited_outputs,
        "weak_chunk_alerts": weak_alerts,
        "consistency_drift_sample": consistency_drift,
        "top_export_sessions": export_hot,
        "chunk_audit_summary": {
            "weak": chunk_audit.get("weak_chunk_count"),
            "generic": chunk_audit.get("generic_chunk_count"),
            "duplicates": chunk_audit.get("duplicate_snippet_count"),
        },
    }
