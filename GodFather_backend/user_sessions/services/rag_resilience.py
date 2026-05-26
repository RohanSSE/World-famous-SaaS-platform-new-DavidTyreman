"""
Graceful degradation when ES / Redis / GPT fail (Track 3).
"""
from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


def es_available(es_service=None) -> bool:
    try:
        if es_service is None:
            from document.utils.elasticsearch_service import ElasticsearchService
            es_service = ElasticsearchService()
        from utils.ai_knowledge_config import AI_KNOWLEDGE_INDEX_NAME
        return es_service._index_exists(AI_KNOWLEDGE_INDEX_NAME)
    except Exception:
        return False


def cache_available() -> bool:
    try:
        from django.core.cache import cache
        cache.set("_rag_ping", 1, 5)
        return cache.get("_rag_ping") == 1
    except Exception:
        return False


def safe_retrieve(
    retrieve_fn: Callable,
    fallback_chunks: Optional[List[Dict]] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Try retrieval; return empty context on failure instead of crashing."""
    try:
        return retrieve_fn(**kwargs)
    except Exception as e:
        logger.warning("Retrieval degraded: %s", e)
        return {
            "chunks": fallback_chunks or [],
            "context": "",
            "sources": [],
            "context_used": False,
            "documents_searched": 0,
            "degraded": True,
            "degrade_reason": str(e)[:200],
        }


def safe_gpt_call(call_fn: Callable, fallback_message: str) -> Dict[str, Any]:
    try:
        return call_fn()
    except Exception as e:
        logger.exception("GPT call failed, returning fallback")
        return {
            "answer": fallback_message,
            "degraded": True,
            "degrade_reason": str(e)[:200],
        }
