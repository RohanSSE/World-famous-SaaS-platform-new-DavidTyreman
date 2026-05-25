"""Run RAG evaluation dataset — groundedness, citations, retrieval relevance."""
import json
import os
import sys
from pathlib import Path

import django

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
os.environ.setdefault("DJANGO_SKIP_KNOWLEDGE_AUTO", "1")
django.setup()

from user_sessions.services.evaluation_persistence import save_evaluation_run
from user_sessions.services.rag_evaluation import evaluate_rag_response
from user_sessions.services.rag_service import generate_rag_response


def load_cases():
    cases = []
    eval_dir = ROOT / "evaluation"
    for path in sorted(eval_dir.glob("*_queries.json")):
        cases.extend(json.loads(path.read_text(encoding="utf-8")))
    return cases


def source_title_hits(sources, expected_sources):
    if not expected_sources:
        return 1.0
    titles = " ".join(
        (s.get("title") or s.get("file") or "") for s in sources
    ).lower()
    hits = sum(1 for t in expected_sources if t.lower() in titles)
    return hits / len(expected_sources)


def score_case(case, result):
    answer_text = result.get("answer") or ""
    answer = answer_text.lower()
    sources = result.get("sources") or []
    context = result.get("_context") or ""
    chunks = result.get("chunks") or []

    eval_scores = result.get("evaluation") or evaluate_rag_response(
        answer_text, context, sources, chunks, case["query"],
    )

    concepts = case.get("expected_concepts", [])
    concept_hits = sum(1 for c in concepts if c.lower() in answer)
    concept_score = concept_hits / max(len(concepts), 1)

    cats = case.get("expected_categories", [])
    matched_cats = {s.get("category") for s in sources if s.get("category") in cats}
    citation_score = min(1.0, len(matched_cats) / max(len(cats), 1))

    source_title_score = min(1.0, source_title_hits(sources, case.get("expected_sources", [])))

    retrieval_relevance = float(eval_scores.get("retrieval_relevance", 0) or 0)
    if not retrieval_relevance and sources:
        retrieval_relevance = min(1.0, len(sources) / 8)

    tone_ok = True
    for tone in case.get("expected_tone", []):
        if tone.lower() not in answer and len(answer) > 50:
            tone_ok = False
            break

    groundedness = float(eval_scores.get("groundedness", 0) or 0)
    grounded_ratio = float(eval_scores.get("grounded_answer_ratio", 0) or 0)
    hallucination_risk = float(eval_scores.get("hallucination_risk", 1) or 1)

    claim_ratio = float(
        eval_scores.get("claim_grounded_ratio")
        or (eval_scores.get("claim_verification") or {}).get("claim_grounded_ratio")
        or grounded_ratio
    )
    from user_sessions.services.calibration_metrics import evaluate_calibrated_pass

    pass_row = {
        "concept_score": concept_score,
        "claim_grounded_ratio": claim_ratio,
        "grounded_answer_ratio": grounded_ratio,
        "consistency_score": 0.55,
        "hallucination_risk": hallucination_risk,
        "unsupported_count": (eval_scores.get("claim_verification") or {}).get("unsupported_count", 0),
        "unsupported_claim_rate": eval_scores.get("unsupported_claim_rate", 0),
        "overclaim_rate": eval_scores.get("overclaim_rate", 0),
    }
    passed = evaluate_calibrated_pass(pass_row, forbidden_clean=True)

    return {
        "id": case["id"],
        "concept_score": round(concept_score, 2),
        "citation_score": round(citation_score, 2),
        "source_title_score": round(source_title_score, 2),
        "groundedness": round(groundedness, 2),
        "grounded_answer_ratio": round(grounded_ratio, 2),
        "generic_filler_ratio": round(float(eval_scores.get("generic_filler_ratio", 0) or 0), 2),
        "hallucination_risk": round(hallucination_risk, 2),
        "claim_grounded_ratio": round(claim_ratio, 2),
        "unsupported_claim_rate": eval_scores.get("unsupported_claim_rate", 0),
        "high_inference_rate": eval_scores.get("high_inference_rate", 0),
        "retrieval_relevance": round(retrieval_relevance, 2),
        "tone_ok": tone_ok,
        "pass": passed,
    }


def main():
    cases = load_cases()
    print(f"Running {len(cases)} evaluation cases...\n")
    passed = 0
    rows = []
    for case in cases:
        try:
            result = generate_rag_response(
                case["query"],
                agent_id="strategist",
                include_evaluation=True,
                use_cache=False,
            )
            scores = score_case(case, result)
            status = "PASS" if scores["pass"] else "FAIL"
            if scores["pass"]:
                passed += 1
            rows.append(scores)
            print(
                f"[{status}] {case['id']} "
                f"concept={scores['concept_score']} "
                f"ground={scores['groundedness']} "
                f"ratio={scores['grounded_answer_ratio']} "
                f"cite={scores['citation_score']} "
                f"risk={scores['hallucination_risk']}"
            )
        except Exception as e:
            print(f"[ERROR] {case['id']}: {e}")
    print(f"\n{passed}/{len(cases)} passed")
    out = ROOT / "evaluation" / "last_run_results.json"
    out.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(f"Wrote {out}")
    run_id = save_evaluation_run(rows, run_type=os.environ.get("EVAL_RUN_TYPE", "manual"))
    print(f"Persisted EvaluationRun id={run_id}")

    n = len(rows)
    baseline = {
        "run_id": run_id,
        "created_at": __import__("time").strftime("%Y-%m-%dT%H:%M:%SZ", __import__("time").gmtime()),
        "cases": n,
        "passed": passed,
        "metrics": {
            "groundedness": round(sum(r.get("groundedness", 0) for r in rows) / n, 3),
            "grounded_answer_ratio": round(sum(r.get("grounded_answer_ratio", 0) for r in rows) / n, 3),
            "citation_accuracy": round(sum(r.get("citation_score", 0) for r in rows) / n, 3),
            "hallucination_risk": round(sum(r.get("hallucination_risk", 0) for r in rows) / n, 3),
            "retrieval_precision": round(sum(r.get("retrieval_relevance", 0) for r in rows) / n, 3),
        },
        "targets": {
            "groundedness": 0.85,
            "grounded_answer_ratio": 0.75,
            "citation_accuracy": 0.90,
            "hallucination_risk": 0.15,
            "retrieval_precision": 0.80,
        },
    }
    baseline_path = ROOT / "evaluation" / "baseline_metrics.json"
    baseline_path.write_text(json.dumps(baseline, indent=2), encoding="utf-8")
    print(f"Baseline saved: {baseline_path}")
    print(f"  groundedness={baseline['metrics']['groundedness']} (target >0.85)")
    print(f"  citation={baseline['metrics']['citation_accuracy']} (target >0.90)")
    print(f"  hallucination={baseline['metrics']['hallucination_risk']} (target <0.15)")
    print(f"  retrieval={baseline['metrics']['retrieval_precision']} (target >0.80)")


if __name__ == "__main__":
    main()
