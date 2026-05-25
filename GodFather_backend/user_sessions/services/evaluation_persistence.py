"""Persist RAG evaluation runs to the database (Phase 15)."""
from __future__ import annotations

from typing import Any, Dict, List


def save_evaluation_run(
    rows: List[Dict[str, Any]],
    run_type: str = "manual",
    status: str = "completed",
) -> int:
    from user_sessions.models import EvaluationResult, EvaluationRun

    if not rows:
        run = EvaluationRun.objects.create(
            run_type=run_type,
            status=status,
            total_cases=0,
            passed_cases=0,
            summary={"message": "no cases"},
        )
        return run.pk

    passed = sum(1 for r in rows if r.get("pass"))
    n = len(rows)
    avg_g = sum(r.get("groundedness", 0) for r in rows) / n
    avg_h = sum(r.get("hallucination_risk", 0) for r in rows) / n
    avg_c = sum(r.get("citation_score", 0) for r in rows) / n
    avg_r = sum(r.get("retrieval_relevance", 0) for r in rows) / n

    run = EvaluationRun.objects.create(
        run_type=run_type,
        status=status,
        total_cases=n,
        passed_cases=passed,
        avg_groundedness=round(avg_g, 4),
        avg_hallucination_risk=round(avg_h, 4),
        avg_citation_accuracy=round(avg_c, 4),
        avg_retrieval_precision=round(avg_r, 4),
        summary={"pass_rate": round(passed / n, 3)},
    )

    EvaluationResult.objects.bulk_create(
        [
            EvaluationResult(
                run=run,
                case_id=r["id"],
                groundedness=r.get("groundedness", 0),
                hallucination_risk=r.get("hallucination_risk", 0),
                citation_accuracy=r.get("citation_score", 0),
                tone_consistent=bool(r.get("tone_ok", True)),
                retrieval_precision=r.get("retrieval_relevance", 0),
                passed=bool(r.get("pass")),
                metrics=r,
            )
            for r in rows
        ]
    )
    return run.pk
