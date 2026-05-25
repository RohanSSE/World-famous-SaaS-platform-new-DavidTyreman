"""
Observable system health for RAG stack (Phase 15).
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from django.conf import settings

logger = logging.getLogger(__name__)

INTELLIGENCE_MODES = {
    "full": "Full Intelligence",
    "reduced": "Reduced Intelligence",
    "memory_offline": "Memory Offline",
    "retrieval_offline": "Retrieval Offline",
}


def check_redis() -> bool:
    try:
        from user_sessions.services.rag_resilience import cache_available

        return cache_available()
    except Exception:
        return False


def check_elasticsearch() -> bool:
    try:
        from user_sessions.services.rag_resilience import es_available

        return es_available()
    except Exception:
        return False


def check_pgvector() -> bool:
    try:
        from utils.pgvector_store import pgvector_knowledge_count

        return pgvector_knowledge_count() > 0
    except Exception:
        return False


def check_cross_encoder() -> bool:
    if not getattr(settings, "RAG_CROSS_ENCODER_ENABLED", False):
        return False
    try:
        from utils.rerank_knowledge import _get_cross_encoder

        model = _get_cross_encoder()
        return bool(model) and model is not False
    except Exception:
        return False


def get_system_health() -> Dict[str, Any]:
    redis_ok = check_redis()
    es_ok = check_elasticsearch()
    pg_ok = check_pgvector()
    ce_ok = check_cross_encoder()

    if es_ok and pg_ok and redis_ok:
        mode = "full"
    elif pg_ok or es_ok:
        mode = "reduced"
    elif not pg_ok and not es_ok:
        mode = "retrieval_offline"
    else:
        mode = "reduced"

    if not getattr(settings, "PGVECTOR_ENABLED", True):
        if mode == "full":
            mode = "memory_offline"

    return {
        "redis": bool(redis_ok),
        "elasticsearch": bool(es_ok),
        "pgvector": bool(pg_ok),
        "cross_encoder": bool(ce_ok),
        "intelligence_mode": str(mode),
        "intelligence_label": str(INTELLIGENCE_MODES.get(mode, mode)),
    }


def log_health_snapshot():
    h = get_system_health()
    logger.info("System health: %s", h)
