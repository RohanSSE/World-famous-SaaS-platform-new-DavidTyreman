"""Redis-backed cache for RAG pipeline (embeddings, retrieval, GPT responses)."""
from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Optional

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def make_cache_key(prefix: str, *parts: str) -> str:
    payload = "|".join(str(p) for p in parts)
    return f"rag:{prefix}:{_sha256(payload)}"


def cache_get(key: str) -> Optional[Any]:
    try:
        raw = cache.get(key)
        if raw is None:
            return None
        if isinstance(raw, (dict, list)):
            return raw
        return json.loads(raw)
    except Exception as e:
        logger.debug("RAG cache get failed (%s): %s", key, e)
        return None


def cache_set(key: str, value: Any, ttl_seconds: int) -> None:
    try:
        cache.set(key, value, timeout=ttl_seconds)
    except Exception as e:
        logger.debug("RAG cache set failed (%s): %s", key, e)


def embedding_cache_key(text: str) -> str:
    return make_cache_key("emb", text.strip().lower())


def retrieval_cache_key(query: str, scope: str = "knowledge", user_id: Optional[int] = None) -> str:
    uid = str(user_id or 0)
    return make_cache_key("ret", scope, uid, query.strip().lower())


def gpt_response_cache_key(query: str, context_hash: str) -> str:
    return make_cache_key("gpt", query.strip().lower(), context_hash)


def ttl_embedding() -> int:
    return int(getattr(settings, "RAG_CACHE_TTL_EMBEDDING", 300))


def ttl_retrieval() -> int:
    return int(getattr(settings, "RAG_CACHE_TTL_RETRIEVAL", 300))


def ttl_gpt() -> int:
    return int(getattr(settings, "RAG_CACHE_TTL_GPT", 900))
