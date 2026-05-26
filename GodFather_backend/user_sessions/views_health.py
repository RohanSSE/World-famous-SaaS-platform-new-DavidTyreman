"""Production health checks."""
from django.http import JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def api_health(request):
    checks = {"django": "ok", "database": "unknown", "redis": "optional"}
    try:
        from django.db import connection

        connection.ensure_connection()
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {e}"

    try:
        import redis
        from django.conf import settings

        url = getattr(settings, "REDIS_URL", None) or getattr(settings, "CELERY_BROKER_URL", "")
        if url and url.startswith("redis"):
            r = redis.from_url(url, socket_connect_timeout=2)
            r.ping()
            checks["redis"] = "ok"
        else:
            checks["redis"] = "not_configured"
    except Exception:
        checks["redis"] = "unavailable"

    status_code = 200 if checks["database"] == "ok" else 503
    return JsonResponse(
        {"status": "healthy" if status_code == 200 else "degraded", "checks": checks},
        status=status_code,
    )
