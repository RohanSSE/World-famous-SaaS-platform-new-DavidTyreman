# Manual RAG Failure Log

**Sprint goal:** Reliable Strategic Intelligence v1

| Metric | Baseline | Next goal |
|--------|----------|-----------|
| hallucination risk | 0.34 | < 0.20 |
| retrieval precision | 0.57 | > 0.75 |
| citation accuracy | 0.57 | > 0.80 |
| grounded_answer_ratio | 0.82 | > 0.90 |

## Failure types (use exactly one per row)

| Type | When to use |
|------|-------------|
| `hallucination` | Claim not in retrieved context |
| `generic_advice` | Unsupported filler ("be authentic") |
| `wrong_citation` | Source doesn't match answer |
| `weak_retrieval` | Meta/admin chunk in top results |
| `planner_error` | Wrong agents for intent |
| `memory_conflict` | Stale or wrong memory |
| `latency_spike` | Slow embed / first token |
| `contradiction_missed` | Tension not surfaced |
| `unsupported_claim` | Flagged by verification layer |

## Session log

| Date | Prompt | failure_type | Notes | Fixed? |
|------|--------|--------------|-------|--------|
| | | | | |

## Weekly rollup

Run after 20–30 prompts:

```
hallucination: __
generic_advice: __
weak_retrieval: __
...
```

Compare `python scripts/run_golden_evaluation.py` vs `evaluation/golden_baseline.json`.

## Rebuild index after filter changes

```powershell
python manage.py build_ai_knowledge --force
```
