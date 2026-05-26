"""Persist AI request latency breakdown."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from django.conf import settings

logger = logging.getLogger(__name__)


def log_ai_request_trace(
    user,
    query: str,
    agent_id: str,
    latency: Dict[str, int],
    retrieval_confidence: str = "",
    hallucination_risk: Optional[float] = None,
    pipeline: str = "",
    session_id: Optional[int] = None,
    stages: Optional[Dict[str, Any]] = None,
    confidence_score: Optional[float] = None,
    reasoning_trace: Optional[Dict[str, Any]] = None,
) -> None:
    if not getattr(settings, "AI_REQUEST_TRACE_LOGGING", True):
        return
    try:
        from user_sessions.models import AIRequestTrace

        AIRequestTrace.objects.create(
            user=user if user and getattr(user, "is_authenticated", False) else None,
            session_id=session_id,
            query=(query or "")[:2000],
            embedding_ms=int(latency.get("embedding_ms", 0)),
            retrieval_ms=int(latency.get("retrieval_ms", 0)),
            rerank_ms=int(latency.get("rerank_ms", 0)),
            generation_ms=int(latency.get("generation_ms", 0)),
            verification_ms=int(latency.get("verification_ms", 0)),
            total_ms=int(latency.get("total_ms", 0)),
            retrieval_confidence=retrieval_confidence or "",
            hallucination_risk=hallucination_risk,
            confidence_score=confidence_score,
            pipeline=(pipeline or "")[:64],
            agent_id=(agent_id or "default")[:64],
            stages=stages or {},
            reasoning_trace=reasoning_trace or {},
        )
    except Exception as e:
        logger.warning("AIRequestTrace save failed: %s", e)
