"""AI cost & latency dashboard metrics (Phase 15)."""
from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from typing import Any, Dict, List

from django.db.models import Avg, Count, Max, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone


def get_ai_cost_dashboard(days: int = 1) -> Dict[str, Any]:
    from user_sessions.models import AIUsageLog

    since = timezone.now() - timedelta(days=max(1, days))
    qs = AIUsageLog.objects.filter(created_at__gte=since)
    total_requests = qs.count()

    if total_requests == 0:
        return {
            "period_days": days,
            "total_requests": 0,
            "total_tokens": 0,
            "embedding_tokens": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "estimated_cost_usd": "0",
            "cache_hits": 0,
            "cache_savings_estimate_usd": "0",
            "avg_latency_ms": 0,
            "slowest_agents": [],
            "by_agent": [],
            "by_day": [],
        }

    agg = qs.aggregate(
        total_cost=Sum("estimated_cost_usd"),
        prompt=Sum("prompt_tokens"),
        completion=Sum("completion_tokens"),
        embedding=Sum("embedding_tokens"),
        total_tokens=Sum("total_tokens"),
        avg_latency=Avg("latency_ms"),
        max_latency=Max("latency_ms"),
    )
    cache_hits = qs.filter(cache_hit=True).count()
    total_cost = agg["total_cost"] or Decimal("0")
    cache_ratio = cache_hits / total_requests if total_requests else 0
    cache_savings = (total_cost * Decimal(str(cache_ratio * 0.85))).quantize(Decimal("0.0001"))

    by_agent: List[Dict[str, Any]] = list(
        qs.values("agent_id")
        .annotate(
            requests=Count("id"),
            tokens=Sum("total_tokens"),
            cost=Sum("estimated_cost_usd"),
            avg_latency_ms=Avg("latency_ms"),
            max_latency_ms=Max("latency_ms"),
        )
        .order_by("-cost")[:15]
    )

    slowest = sorted(
        [
            {
                "agent_id": row["agent_id"],
                "avg_latency_ms": round(float(row["avg_latency_ms"] or 0), 1),
                "max_latency_ms": int(row["max_latency_ms"] or 0),
                "requests": row["requests"],
            }
            for row in by_agent
        ],
        key=lambda x: x["avg_latency_ms"],
        reverse=True,
    )[:5]

    by_day = list(
        qs.annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(
            requests=Count("id"),
            tokens=Sum("total_tokens"),
            cost=Sum("estimated_cost_usd"),
            embedding_tokens=Sum("embedding_tokens"),
        )
        .order_by("day")
    )
    by_day = [
        {
            "date": str(row["day"]),
            "requests": row["requests"],
            "total_tokens": row["tokens"] or 0,
            "embedding_tokens": row["embedding_tokens"] or 0,
            "estimated_cost_usd": str(row["cost"] or 0),
        }
        for row in by_day
    ]

    return {
        "period_days": days,
        "total_requests": total_requests,
        "total_tokens": agg["total_tokens"] or 0,
        "embedding_tokens": agg["embedding"] or 0,
        "prompt_tokens": agg["prompt"] or 0,
        "completion_tokens": agg["completion"] or 0,
        "estimated_cost_usd": str(total_cost),
        "cache_hits": cache_hits,
        "cache_savings_estimate_usd": str(cache_savings),
        "avg_latency_ms": round(float(agg["avg_latency"] or 0), 1),
        "max_latency_ms": int(agg["max_latency"] or 0),
        "slowest_agents": slowest,
        "by_agent": [
            {
                "agent_id": r["agent_id"],
                "requests": r["requests"],
                "tokens": r["tokens"] or 0,
                "estimated_cost_usd": str(r["cost"] or 0),
                "avg_latency_ms": round(float(r["avg_latency_ms"] or 0), 1),
            }
            for r in by_agent
        ],
        "by_day": by_day,
    }
