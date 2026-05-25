"""
Simple in-memory rate limiting for RAG endpoints (production: use Redis).
"""
from __future__ import annotations

import time
from collections import defaultdict
from threading import Lock

from django.conf import settings
from django.http import JsonResponse

_lock = Lock()
_buckets: dict = defaultdict(list)


class RagRateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.enabled = getattr(settings, "RAG_RATE_LIMIT_ENABLED", True)
        self.max_requests = getattr(settings, "RAG_RATE_LIMIT_PER_MINUTE", 30)
        self.window = 60.0

    def __call__(self, request):
        if self.enabled and self._should_limit(request):
            key = self._client_key(request)
            if not self._allow(key):
                return JsonResponse(
                    {"detail": "Rate limit exceeded. Try again shortly."},
                    status=429,
                )
        return self.get_response(request)

    def _should_limit(self, request):
        path = request.path or ""
        return request.method == "POST" and (
            "rag-query" in path or "brand-workflow" in path or "brand-export" in path
        )

    def _client_key(self, request):
        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            return f"user:{user.id}"
        ip = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip()
        return f"ip:{ip or request.META.get('REMOTE_ADDR', 'anon')}"

    def _allow(self, key: str) -> bool:
        now = time.time()
        with _lock:
            hits = [t for t in _buckets[key] if now - t < self.window]
            if len(hits) >= self.max_requests:
                _buckets[key] = hits
                return False
            hits.append(now)
            _buckets[key] = hits
        return True
