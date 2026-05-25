"""Log AI token usage and estimated cost."""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, Dict, Optional

from django.conf import settings

logger = logging.getLogger(__name__)

# Rough USD per 1K tokens (adjust per deployment)
COST_PER_1K = {
    "gpt-4o": {"prompt": Decimal("0.0025"), "completion": Decimal("0.01")},
    "embedding": Decimal("0.00002"),
    "default": {"prompt": Decimal("0.001"), "completion": Decimal("0.003")},
}


def estimate_cost(
    prompt_tokens: int,
    completion_tokens: int,
    embedding_tokens: int = 0,
    model: str = "gpt-4o",
) -> Decimal:
    rates = COST_PER_1K.get(model, COST_PER_1K["default"])
    if isinstance(rates, dict):
        cost = (
            Decimal(prompt_tokens) / 1000 * rates["prompt"]
            + Decimal(completion_tokens) / 1000 * rates["completion"]
        )
    else:
        cost = Decimal(0)
    cost += Decimal(embedding_tokens) / 1000 * COST_PER_1K["embedding"]
    return cost.quantize(Decimal("0.000001"))


def log_ai_usage(
    user,
    agent_id: str,
    endpoint: str,
    token_usage: Dict[str, int],
    latency_ms: int = 0,
    session_id: Optional[int] = None,
    cache_hit: bool = False,
    degraded: bool = False,
    model: str = "gpt-4o",
) -> None:
    if not getattr(settings, "AI_USAGE_LOGGING", True):
        return
    try:
        from user_sessions.models import AIUsageLog

        pt = token_usage.get("prompt_tokens", 0)
        ct = token_usage.get("completion_tokens", 0)
        et = token_usage.get("embedding_tokens", 0)
        total = token_usage.get("total_tokens", pt + ct + et)
        cost = estimate_cost(pt, ct, et, model)
        if cost > Decimal("2"):
            logger.warning(
                "AI cost alert: estimated $%s for agent=%s endpoint=%s (tokens=%s)",
                cost,
                agent_id,
                endpoint,
                total,
            )
        AIUsageLog.objects.create(
            user=user if user and getattr(user, "is_authenticated", False) else None,
            session_id=session_id,
            agent_id=agent_id,
            endpoint=endpoint,
            prompt_tokens=pt,
            completion_tokens=ct,
            embedding_tokens=et,
            total_tokens=total,
            estimated_cost_usd=cost,
            latency_ms=latency_ms,
            cache_hit=cache_hit,
            degraded=degraded,
        )
    except Exception as e:
        logger.warning("AIUsageLog failed: %s", e)
