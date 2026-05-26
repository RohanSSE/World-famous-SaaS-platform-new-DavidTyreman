# Architecture Frozen — Productization Phase

**Date:** After 15/24 golden pass (projected ~19/24 post sprint)

## Stop adding

- New RAG orchestration layers
- Agent frameworks (LangChain/CrewAI)
- New vector DB plumbing
- Major evaluation systems

## Active work

1. **Product workflows** — `POST /api/sessions/{id}/brand-workflow/`
2. **Human feedback learning** — `GET/POST /api/sessions/{id}/feedback-learning/`
3. **Frontend cognition UX** (next week)
4. **Precision tuning** on 5 remaining golden cases only

## Official baseline

```bash
python scripts/run_golden_evaluation.py
python scripts/reliability_report.py
python scripts/mark_official_baseline.py
```

## Workflow catalog

```bash
GET /api/sessions/brand-workflows/
```

Workflows: `brand_dna`, `messaging_framework`, `tone_guide`, `audience_psychology`, `campaign_direction`, `positioning_engine`, `pack`, `full`
