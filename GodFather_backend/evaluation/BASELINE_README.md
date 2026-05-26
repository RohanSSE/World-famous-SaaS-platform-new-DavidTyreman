# RAG Evaluation Baseline (Phase 15)

## Targets (production quality bar)

| Metric | Target |
|--------|--------|
| groundedness (token overlap) | > 0.85 |
| **grounded_answer_ratio** (sentence-level) | **> 0.75** |
| citation accuracy | > 0.90 |
| hallucination risk | < 0.15 |
| retrieval precision | > 0.80 |

**Primary metric for answer quality:** `grounded_answer_ratio` — % of sentences tied to retrieved context.

Current baseline (run id 2): see `baseline_metrics.json`.

## Commands

```powershell
python scripts/validate_ai_quality.py          # retrieval + strategic + SSE + latency
python scripts/validate_ai_quality.py          # includes eval (slow, calls GPT)
python scripts/run_rag_evaluation.py           # full eval suite → DB + last_run_results.json
python scripts/ai_usage_report.py              # cost dashboard (after real queries)
```

## Artifacts

- `evaluation/baseline_metrics.json` — snapshot after `run_rag_evaluation` / validate
- `evaluation/validation_report.json` — latest `validate_ai_quality.py` run
- `evaluation/last_run_results.json` — per-case scores

Compare every release against `baseline_metrics.json`.
