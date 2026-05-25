#!/usr/bin/env python
"""
Run only golden cases that failed in the last saved baseline — fast iteration.

Usage:
  python scripts/run_failed_cases.py
  python scripts/run_failed_cases.py --ids golden_differentiation_1 golden_positioning_1
  python scripts/run_failed_cases.py --write  # merge results into golden_baseline.json rows
"""
from __future__ import annotations

import argparse
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

from scripts.run_golden_evaluation import load_golden, score_golden  # noqa: E402
from user_sessions.services.rag_service import generate_rag_response  # noqa: E402

DEFAULT_FAILED = (
    "golden_trust_premium_1",
    "golden_differentiation_1",
    "golden_positioning_1",
    "golden_trust_clarity_1",
    "golden_dna_1",
    "golden_competitor_irrelevant_1",
    "golden_rejected_angle_1",
    "golden_narrative_conflict_1",
    "golden_audience_psychology_1",
)


def failed_ids_from_baseline() -> list:
    path = ROOT / "evaluation" / "golden_baseline.json"
    if not path.exists():
        return list(DEFAULT_FAILED)
    data = json.loads(path.read_text(encoding="utf-8"))
    return [r["id"] for r in data.get("rows", []) if not r.get("pass")]


def main():
    parser = argparse.ArgumentParser(description="Re-run failed golden cases only")
    parser.add_argument("--ids", nargs="*", help="Explicit case ids")
    parser.add_argument("--write", action="store_true", help="Patch golden_baseline.json rows")
    parser.add_argument("--summary", action="store_true", help="Print cluster diagnosis only")
    args = parser.parse_args()

    all_cases = {c["id"]: c for c in load_golden()}
    ids = args.ids or failed_ids_from_baseline()
    cases = [all_cases[i] for i in ids if i in all_cases]
    if not cases:
        print("No matching cases.")
        sys.exit(1)

    print(f"Failed-case rerun: {len(cases)} cases\n")
    passed = 0
    results = []

    for idx, case in enumerate(cases, start=1):
        print(f"--- {idx}/{len(cases)}: {case['id']} ---", flush=True)
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
            print(
                f"[{status}] unsupported_rate={scores.get('unsupported_claim_rate')} "
                f"claim_ratio={scores.get('claim_grounded_ratio')} "
                f"retrieval={scores.get('retrieval_relevance')} "
                f"consistency={scores.get('consistency_score')}",
                flush=True,
            )
            results.append({"id": case["id"], "scores": scores})
        except Exception as e:
            print(f"[ERROR] {case['id']}: {e}", flush=True)
            results.append({"id": case["id"], "error": str(e)})

    print(f"\n{passed}/{len(cases)} passed on failed-cluster rerun")

    if args.summary or results:
        clusters = {"claim_grounding": 0, "retrieval": 0, "other": 0}
        for item in results:
            sc = item.get("scores") or {}
            cgr = sc.get("claim_grounded_ratio") or 0
            retr = sc.get("retrieval_relevance") or 0
            if cgr < 0.5:
                clusters["claim_grounding"] += 1
            elif retr < 0.65:
                clusters["retrieval"] += 1
            else:
                clusters["other"] += 1
        print("Cluster diagnosis:", clusters)
        print("Tip: use chunk_quality_audit.py before retrieval tuning.")

    out = ROOT / "evaluation" / "failed_cases_results.json"
    out.write_text(json.dumps({"results": results}, indent=2), encoding="utf-8")
    print(f"Saved {out}")

    if args.write:
        baseline_path = ROOT / "evaluation" / "golden_baseline.json"
        if baseline_path.exists():
            data = json.loads(baseline_path.read_text(encoding="utf-8"))
            by_id = {r["id"]: r for r in data.get("rows", [])}
            for item in results:
                if "scores" in item:
                    by_id[item["id"]] = {**by_id.get(item["id"], {}), **item["scores"]}
            data["rows"] = list(by_id.values())
            baseline_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            print(f"Patched rows in {baseline_path}")


if __name__ == "__main__":
    main()
