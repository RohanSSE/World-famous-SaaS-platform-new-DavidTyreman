#!/usr/bin/env python
"""
CI gate — fail if golden metrics regress below official baseline thresholds.
Usage: python scripts/ci_golden_gate.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
EVAL = BASE / "evaluation"

THRESHOLDS = {
    "pass_rate_min": 12 / 25,  # aligned with reliability_report.py
    "hallucination_risk_max": 0.25,
    "grounded_answer_ratio_min": 0.85,
    "retrieval_precision_min": 0.65,
    "unsupported_claim_rate_max": 0.55,
    "consistency_score_avg_min": 0.60,
}


def load_baseline():
    for name in ("official_baseline.json", "golden_baseline.json"):
        p = EVAL / name
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8")), p.name
    return None, None


def main() -> int:
    data, fname = load_baseline()
    if not data:
        print("CI GATE FAIL: no baseline file in evaluation/")
        return 1

    passed = data.get("passed", 0)
    cases = data.get("cases", 24)
    metrics = data.get("metrics", {})
    pass_rate = passed / cases if cases else 0

    failures = []
    if pass_rate < THRESHOLDS["pass_rate_min"]:
        failures.append(f"pass_rate {pass_rate:.3f} < {THRESHOLDS['pass_rate_min']}")

    checks = [
        ("hallucination_risk", "hallucination_risk_max", "max"),
        ("grounded_answer_ratio", "grounded_answer_ratio_min", "min"),
        ("retrieval_precision", "retrieval_precision_min", "min"),
        ("unsupported_claim_rate", "unsupported_claim_rate_max", "max"),
        ("consistency_score_avg", "consistency_score_avg_min", "min"),
    ]
    for key, thresh_key, mode in checks:
        val = metrics.get(key)
        if val is None:
            continue
        t = THRESHOLDS[thresh_key]
        if mode == "max" and val > t:
            failures.append(f"{key} {val:.3f} > {t}")
        if mode == "min" and val < t:
            failures.append(f"{key} {val:.3f} < {t}")

    print(f"CI golden gate ({fname}): {passed}/{cases} pass_rate={pass_rate:.3f}")
    if failures:
        for f in failures:
            print(f"  FAIL: {f}")
        return 1
    print("CI GATE PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
