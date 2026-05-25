# Enterprise delivery layer

Architecture is **frozen**. This document covers productization only.

## Golden freeze (Day 1)

```bash
python scripts/run_golden_evaluation.py
python scripts/reliability_report.py
python scripts/mark_official_baseline.py
python scripts/ci_golden_gate.py
```

## Brand exports

`GET|POST /api/sessions/<id>/brand-export/?workflow=pack&format=pdf|pptx|json&styled=premium`

Requires `python-pptx` for PPTX. Premium PDF = cover, TOC, DNA map table.

## Pilot & commercialization

See `docs/PILOT_LAUNCH.md`. Fast reliability iteration:

```bash
python scripts/run_failed_cases.py
python scripts/chunk_quality_audit.py
python scripts/pilot_smoke_test.py
```

Production: `docker compose -f docker-compose.prod.yml up -d`

## Observability (admin)

- `GET /api/sessions/admin/cognition-dashboard/`
- `GET /api/sessions/admin/cognition-traces/`
- `GET /api/sessions/admin/feedback-review/`

Frontend: `/admin/cognition`, `/admin/review` (use main app JWT in `localStorage.accessToken`).

## Health & rate limits

- `GET /api/health/`
- `RAG_RATE_LIMIT_ENABLED`, `RAG_RATE_LIMIT_PER_MINUTE` in env
- `REDIS_URL` for production Celery/cache

## Azure retries

Use `utils.retry_azure.with_azure_retry()` for transient OpenAI/Azure calls.
