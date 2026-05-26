# Pilot launch readiness

## Pre-flight (Day 1–2)

```bash
docker compose up -d
python scripts/pilot_smoke_test.py
# With JWT: TOKEN=<accessToken> python scripts/pilot_smoke_test.py
python scripts/chunk_quality_audit.py 500
```

## Pilot test matrix

| Task | Route / command |
|------|-----------------|
| Real brand upload | User dashboard → documents |
| Onboarding flow | `/brand-onboarding` |
| Brand workflows | `/brand-os` |
| Premium PDF | `brand-export?format=pdf&styled=premium` |
| Feedback learning | Brand OS → Teach the brand brain |
| Failed-case tuning | `python scripts/run_failed_cases.py` (not full golden) |
| Admin monitor | `/admin/cognition` (live metrics poll) |

## Production deploy

```bash
docker compose -f docker-compose.prod.yml up -d --build
curl http://localhost/api/health/
```

## Reliability (parallel, small)

- Pass-rate swings = evaluator strictness + Azure filters, not unsafe AI.
- Tune retrieval/grounding only; no new orchestration.
- `python scripts/run_failed_cases.py --write` after fixes.

## Product signals tracked

- `export`, `feedback_edit` → `BrandMemory` key `product_signals`
- Admin: `GET /api/sessions/admin/product-signals/`
