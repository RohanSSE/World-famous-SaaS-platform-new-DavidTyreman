# Pilot execution + business validation

Architecture is frozen. Validate with **real brands**, not golden obsession.

## 5–10 pilot runs (per brand)

| Step | Action | KPI tracked |
|------|--------|-------------|
| 1 | Upload PDFs, site copy, founder notes | `document_upload` |
| 2 | `/brand-onboarding` | `onboarding_step` |
| 3 | `/brand-os` workflows | `workflow_run` |
| 4 | Premium PDF export | `export` |
| 5 | Edit + feedback learning | `feedback_edit` |
| 6 | Re-run workflow | `workflow_rerun` |
| 7 | Check pilot checklist in Brand OS sidebar | `pilot_completion_pct` |

## APIs

- `GET /api/sessions/<id>/pilot-kpis/`
- `POST /api/sessions/<id>/pilot-event/` — body: `{ "signal": "document_upload", "meta": {} }`
- `POST /api/sessions/<id>/demo-pack/` — body: `{ "demo_id": "luxury" }`
- `GET /api/sessions/demo-brands/`

## Demo (investor / client)

Brand OS → **One-Click Demo** → luxury | D2C | agency | startup packs (instant, no Azure).

For evidence-grounded output: use real session + **Full Brand Pack**.

## Reliability (small sprint only)

```bash
python scripts/run_failed_cases.py
python scripts/chunk_quality_audit.py
```

Do **not** run full golden daily.

## Admin

- `/admin/cognition` — live cognition
- `/admin/ops` — repairs, weak chunks, edited outputs

## Deploy

```bash
docker compose -f docker-compose.prod.yml up -d --build
```
