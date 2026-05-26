#!/usr/bin/env python

"""Permanent golden benchmark — compare every release to baseline."""

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



from scripts.run_rag_evaluation import score_case  # noqa: E402

from user_sessions.services.evaluation_persistence import save_evaluation_run  # noqa: E402

from user_sessions.services.rag_intelligence import detect_query_intent  # noqa: E402

from user_sessions.services.retrieval_metrics import (  # noqa: E402

    aggregate_retrieval_metrics,

    score_manifesto_dominance,

    score_top1_hit,

)

from user_sessions.services.rag_service import generate_rag_response  # noqa: E402





def load_golden():

    path = ROOT / "evaluation" / "golden_set.json"

    return json.loads(path.read_text(encoding="utf-8"))





def score_golden(case, result):

    scores = score_case(case, result)

    answer = (result.get("answer") or "").lower()

    forbidden = case.get("forbidden", [])

    forbidden_hits = [f for f in forbidden if f.lower() in answer]

    scores["forbidden_hits"] = forbidden_hits

    scores["forbidden_clean"] = len(forbidden_hits) == 0

    verification = result.get("verification") or {}

    scores["unsupported_count"] = verification.get("unsupported_count", 0)

    ev = result.get("evaluation") or {}

    scores["source_coverage"] = ev.get("source_coverage", scores.get("citation_score", 0))

    scores["generic_filler_count"] = ev.get("generic_filler_count", 0)



    chunks = result.get("chunks") or []
    context_quality = result.get("context_quality") or {}

    top1 = score_top1_hit(case, chunks)

    manifesto = score_manifesto_dominance(case, chunks, intent=detect_query_intent(case["query"]))

    from user_sessions.services.retrieval_metrics import score_split_retrieval_metrics
    from user_sessions.services.reasoning_drift import score_reasoning_drift

    drift = score_reasoning_drift(result.get("answer") or "", result.get("_context") or "")
    split = score_split_retrieval_metrics(case, chunks, context_quality)

    scores.update(top1)
    scores.update(manifesto)
    scores.update(split)
    scores.update(drift)
    consistency = result.get("strategic_consistency") or {}
    scores["consistency_score"] = consistency.get("consistency_score", 0)
    scores["critique_flags"] = result.get("critique_flags", [])
    repair_m = result.get("repair_metrics") or {}
    scores.update(repair_m)
    scores["context_conflict_score"] = (context_quality or {}).get("context_conflict_score", 0)
    scores["overclaim_suppressed"] = result.get("overclaim_suppressed", False)

    ev = result.get("evaluation") or {}
    claim_v = ev.get("claim_verification") or verification
    scores["claim_grounded_ratio"] = ev.get(
        "claim_grounded_ratio",
        claim_v.get("claim_grounded_ratio", scores.get("grounded_answer_ratio", 0)),
    )
    from user_sessions.services.calibration_metrics import compute_split_hallucination_metrics

    split = compute_split_hallucination_metrics(
        claim_v,
        context_quality=context_quality,
        overclaim_suppressed=scores.get("overclaim_suppressed", False),
        critique_flags=scores.get("critique_flags"),
    )
    scores.update(split)
    scores["concept_score"] = scores.get("concept_score", scores.get("citation_score", 0))
    from user_sessions.services.calibration_metrics import (
        estimate_hallucination_risk_calibrated,
        evaluate_calibrated_pass,
    )

    scores["hallucination_risk"] = estimate_hallucination_risk_calibrated(
        split,
        scores.get("grounded_answer_ratio", 0),
        scores.get("claim_grounded_ratio", 0),
    )
    scores["pass"] = evaluate_calibrated_pass(
        scores,
        forbidden_clean=scores.get("forbidden_clean", True),
    )

    critique = result.get("retrieval_critique") or {}

    scores["retrieval_flags"] = critique.get("flags", [])



    # Top chunks snapshot for failure inspection

    top_chunks = []

    for c in chunks[:3]:

        meta = c.get("metadata") or {}

        top_chunks.append(

            {

                "title": meta.get("title", ""),

                "category": meta.get("category", ""),

                "hybrid_score": c.get("hybrid_score"),

                "rerank_reason": c.get("rerank_reason", []),

                "generic_penalty": bool(c.get("generic_chunk_penalty")),
                "context_role": c.get("_context_role", ""),
            }

        )

    scores["top_chunks"] = top_chunks
    scores["context_quality"] = {
        "manifesto_dominance": context_quality.get("manifesto_dominance"),
        "strategic_density": context_quality.get("strategic_density"),
        "context_coherence": context_quality.get("context_coherence"),
        "context_conflicts": context_quality.get("context_conflicts", []),
    }



    scores["expected_categories"] = bool(case.get("expected_categories"))
    if case.get("expected_categories") and not top1.get("top1_hit"):
        scores["top1_hit"] = False

    return scores





def main():

    cases = load_golden()

    prior_metrics = {}

    golden_path = ROOT / "evaluation" / "golden_baseline.json"

    if golden_path.exists():

        prior_metrics = json.loads(golden_path.read_text(encoding="utf-8")).get("metrics", {})



    print(f"Golden set: {len(cases)} cases\n")

    if prior_metrics:

        print("Prior baseline:")

        print(f"  retrieval_precision={prior_metrics.get('retrieval_precision')}")

        print(f"  hallucination_risk={prior_metrics.get('hallucination_risk')}")

        print(f"  grounded_answer_ratio={prior_metrics.get('grounded_answer_ratio')}")

        print(f"  top1_hit_rate={prior_metrics.get('top1_hit_rate')}\n")



    passed = 0

    rows = []

    detailed = []



    n_cases = len(cases)
    for idx, case in enumerate(cases, start=1):
        print(f"--- Case {idx}/{n_cases}: {case['id']} (Azure RAG, may take 1-3 min) ---", flush=True)

        try:

            result = generate_rag_response(

                case["query"],

                agent_id="strategist",

                include_evaluation=True,

                use_cache=False,

            )

            scores = score_golden(case, result)

            status = "PASS" if scores["pass"] else "FAIL"

            if scores["pass"]:

                passed += 1

            rows.append(scores)

            detailed.append(

                {

                    "case": case,

                    "scores": scores,

                    "answer_preview": (result.get("answer") or "")[:400],

                    "retrieval_critique": result.get("retrieval_critique"),

                }

            )

            print(

                f"[{status}] {case['id']} ground={scores['groundedness']} "

                f"ratio={scores.get('grounded_answer_ratio')} "

                f"risk={scores['hallucination_risk']} "

                f"top1={scores.get('top1_hit')} "

                f"manifesto_dom={scores.get('manifesto_support_density', scores.get('manifesto_dominance'))} "
                f"density={scores.get('strategic_density')} "
                f"drift={scores.get('reasoning_drift_score')}"

            )

        except Exception as e:

            print(f"[ERROR] {case['id']}: {e}")

            detailed.append({"case": case, "error": str(e)})



    n = len(rows)

    retrieval_agg = aggregate_retrieval_metrics(rows)
    from user_sessions.services.reliability_metrics import aggregate_reliability_kpis

    reliability_kpis = aggregate_reliability_kpis(rows)



    prior_path = ROOT / "evaluation" / "golden_baseline_prior.json"

    if golden_path.exists():

        prior_path.write_text(golden_path.read_text(encoding="utf-8"), encoding="utf-8")



    baseline = {

        "suite": "golden_set",

        "cases": n,

        "passed": passed,

        "metrics": {

            "groundedness": round(sum(r.get("groundedness", 0) for r in rows) / max(n, 1), 3),

            "grounded_answer_ratio": round(

                sum(r.get("grounded_answer_ratio", 0) for r in rows) / max(n, 1), 3

            ),

            "hallucination_risk": round(sum(r.get("hallucination_risk", 0) for r in rows) / max(n, 1), 3),
            "unsupported_claim_rate": round(
                sum(r.get("unsupported_claim_rate", 0) for r in rows) / max(n, 1), 3
            ),
            "high_inference_rate": round(
                sum(r.get("high_inference_rate", 0) for r in rows) / max(n, 1), 3
            ),
            "contradiction_rate": round(
                sum(r.get("contradiction_rate", 0) for r in rows) / max(n, 1), 3
            ),

            "retrieval_precision": round(sum(r.get("retrieval_relevance", 0) for r in rows) / max(n, 1), 3),

            "citation_accuracy": round(sum(r.get("citation_score", 0) for r in rows) / max(n, 1), 3),

            "forbidden_clean_rate": round(

                sum(1 for r in rows if r.get("forbidden_clean")) / max(n, 1), 3

            ),

            "source_coverage": round(

                sum(r.get("source_coverage", 0) for r in rows) / max(n, 1), 3

            ),

            "avg_unsupported_count": round(

                sum(r.get("unsupported_count", 0) for r in rows) / max(n, 1), 2

            ),

            **retrieval_agg,
            **reliability_kpis,

        },

        "targets": {

            "grounded_answer_ratio": 0.90,

            "hallucination_risk": 0.20,

            "retrieval_precision": 0.75,

            "citation_accuracy": 0.80,

            "forbidden_clean_rate": 0.95,

            "top1_hit_rate": 0.70,

            "manifesto_dominance_strategic_avg": 0.60,
            "manifesto_support_density": 0.60,
            "strategic_density_avg": 0.70,
            "context_coherence_avg": 0.80,
            "reasoning_drift_avg": 0.25,

        },

        "comparison": {

            "prior": prior_metrics,

            "delta": {},

        },

    }



    for key in ("retrieval_precision", "hallucination_risk", "grounded_answer_ratio", "top1_hit_rate"):

        if prior_metrics.get(key) is not None and baseline["metrics"].get(key) is not None:

            baseline["comparison"]["delta"][key] = round(

                baseline["metrics"][key] - prior_metrics[key], 3

            )



    out = ROOT / "evaluation" / "golden_baseline.json"

    out.write_text(json.dumps({"rows": rows, **baseline}, indent=2), encoding="utf-8")



    results_path = ROOT / "evaluation" / "golden_results.json"

    results_path.write_text(

        json.dumps({"results": detailed, "metrics": baseline["metrics"]}, indent=2),

        encoding="utf-8",

    )



    save_evaluation_run(rows, run_type="golden")

    print(f"\n{passed}/{n} passed")

    print(f"top1_hit_rate={baseline['metrics'].get('top1_hit_rate')}")

    print(f"manifesto_dominance_strategic_avg={baseline['metrics'].get('manifesto_dominance_strategic_avg')}")

    if baseline["comparison"]["delta"]:

        print(f"Delta vs prior: {baseline['comparison']['delta']}")

    print(f"Saved {out}")

    print(f"Saved {results_path}")





if __name__ == "__main__":

    main()

