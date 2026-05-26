"""
Per-user / per-agent rate limits (Track 3).
"""
from __future__ import annotations

import hashlib
from typing import Optional, Tuple

from django.conf import settings
from django.core.cache import cache


def _key(user_id: int, scope: str) -> str:
    return f"rag:rl:{scope}:{user_id}"


def check_rate_limit(
    user_id: Optional[int],
    scope: str = "rag_query",
    limit: Optional[int] = None,
    window_seconds: int = 3600,
) -> Tuple[bool, int]:
    """
    Returns (allowed, remaining).
    """
    if not user_id:
        return True, limit or 999

    limits = getattr(settings, "RAG_RATE_LIMITS", {})
    limit = limit or limits.get(scope, limits.get("default", 60))

    key = _key(user_id, scope)
    try:
        count = cache.get(key, 0)
        if count >= limit:
            return False, 0
        cache.set(key, count + 1, window_seconds)
        return True, limit - count - 1
    except Exception:
        return True, limit


def check_token_quota(user_id: int, tokens: int) -> bool:
    """Daily token budget per user."""
    budget = int(getattr(settings, "RAG_DAILY_TOKEN_BUDGET", 500_000))
    key = f"rag:tokens:{user_id}"
    try:
        used = cache.get(key, 0)
        if used + tokens > budget:
            return False
        cache.set(key, used + tokens, 86400)
        return True
    except Exception:
        return True
