# Failure Cluster Analysis

Metrics are symptoms. Clusters are root causes for the roadmap.

## Clusters

| Cluster | Description | Fix lever |
|---------|-------------|-----------|
| `generic_reasoning` | Filler advice without retrieval evidence | Filler detector + critique rewrite |
| `weak_manifesto_grounding` | Trust/positioning queries miss manifesto chunks | Reliability weights + category filter |
| `planner_over_routing` | Too many agents for simple queries | Planner simplification |
| `memory_conflict` | Answer contradicts session memory | Memory conflict detector |
| `low_confidence_overclaim` | Strong claims when retrieval weak | Confidence gating + conservative prompt |
| `irrelevant_chunk_dominance` | Meta/admin chunks rank high | Index quality filter (done) |
| `citation_mismatch` | Sources don't match answer substance | Source coverage + claim attribution |

## Sprint focus: strategic learning & autonomous reliability (current)

**Phase 1 — measure only (run before adding features):**
```bash
python scripts/run_golden_evaluation.py
python scripts/reliability_report.py
python scripts/analyze_failures.py
```

Core KPIs: `self_repair_success_rate`, `reasoning_drift_avg`, `overclaim_rate`, `manifesto_support_density`, `context_conflict_rate`, `consistency_score_avg`

Artifacts: `evaluation/failure_memory.json`, `evaluation/eval_clusters.json`, `evaluation/sprint_targets.json`

## Prior: adaptive self-healing

- `CRITIQUE_FLAGS` → self-repair loop
- `repair_context()` — conflict removal, generic replacement, manifesto inject
- Multi-pass: interpret → draft → repair → verify → drift repair
- `reasoning_path`, `strategic_consistency`, overclaim suppression
- Nightly: `python scripts/analyze_failures.py` → `evaluation/sprint_targets.json`

## Prior: strategic context orchestration

Problem shifted from retrieval → **context composition**.
- `MIN_MANIFESTO_CHUNKS=2` slot reservation for strategic queries
- Role-based compose: `anchor_manifesto` ×2, `strategic_support` ×2, `memory_alignment` ×1
- Metrics: `strategic_density`, `context_coherence`, `reasoning_drift_score`

Re-run: `python scripts/run_golden_evaluation.py`

## Prior sprint: retrieval precision

Current retrieval_precision ~0.54 (target >0.75). Levers deployed:
- `strategic_tags` on chunks + query-tag boost
- `GENERIC_CHUNK_PENALTY` on generic marketing chunks
- Diversity rerank (`MAX_CHUNKS_PER_DOCUMENT=2`, similarity cap 0.92)

**Re-index required after tag changes:** `python manage.py build_ai_knowledge --force`

## Golden run snapshot (latest)

| Metric | Prior (7-case) | Golden (24-case) | Sprint goal |
|--------|----------------|------------------|-------------|
| hallucination_risk | 0.34 | **0.326** | < 0.20 |
| grounded_answer_ratio | 0.82 | **0.848** | > 0.90 |
| retrieval_precision | 0.57 | **0.535** | > 0.75 |
| citation_accuracy | 0.57 | **0.875** | > 0.80 |
| pass rate | 5/7 | **10/24** | — |

## Worst cases to inspect manually

| Case ID | Issue cluster | Notes |
|---------|---------------|-------|
| golden_premium_exclusivity_1 | weak_manifesto_grounding | ratio 0.53, risk 0.37 |
| golden_narrative_conflict_1 | generic_reasoning | Should surface tension explicitly |
| golden_crisis_tone_1 | low_confidence_overclaim | ratio 0.53 |
| golden_differentiation_1 | retrieval_precision 0.12 | Weak chunk match |
| golden_post_manifesto_1 | ERROR | Azure content filter — prompt sanitize |

## Session log (fill during manual testing)

| Date | Prompt | cluster | Example | Fixed? |
|------|--------|---------|---------|--------|
| | | | | |

## Weekly rollup

```
generic_reasoning: __
weak_manifesto_grounding: __
memory_conflict: __
low_confidence_overclaim: __
citation_mismatch: __
```

Compare: `python scripts/check_regression.py`
