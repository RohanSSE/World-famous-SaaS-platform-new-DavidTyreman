#!/usr/bin/env python
"""
Release regression gate — compare golden_baseline.json vs prior snapshot.

Exit code 1 if metrics regress beyond tolerance.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "evaluation" / "golden_baseline.json"
PRIOR = ROOT / "evaluation" / "baseline_metrics.json"
TOLERANCE = {
    "hallucination_risk": 0.03,  # max increase allowed
    "grounded_answer_ratio": 0.03,  # max decrease allowed
    "retrieval_precision": 0.05,
    "citation_accuracy": 0.05,
    "top1_hit_rate": 0.05,
}
LATENCY_TOLERANCE = 0.20  # max 20% increase in avg_total_ms


def load_metrics(path: Path) -> dict:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("metrics", data)


def main():
    current = load_metrics(GOLDEN)
    prior = load_metrics(PRIOR)

    if not current:
        print("No golden_baseline.json — run: python scripts/run_golden_evaluation.py")
        sys.exit(1)

    print("=" * 60)
    print("REGRESSION CHECK")
    print("=" * 60)
    print(f"Current:  {GOLDEN.name}")
    print(f"Compare:  {PRIOR.name if prior else '(none)'}\n")

    failed = False
    for key, max_delta in TOLERANCE.items():
        cur = current.get(key)
        if cur is None:
            continue
        if not prior or prior.get(key) is None:
            print(f"  {key}: {cur} (no prior)")
            continue
        old = float(prior[key])
        new = float(cur)
        if key == "hallucination_risk":
            delta = new - old
            ok = delta <= max_delta
            rule = f"increase <= {max_delta}"
        else:
            delta = old - new
            ok = delta <= max_delta
            rule = f"drop <= {max_delta}"
        status = "OK" if ok else "FAIL"
        if not ok:
            failed = True
        print(f"  [{status}] {key}: {old:.3f} -> {new:.3f} ({rule})")

    cur_lat = current.get("avg_total_ms")
    prior_lat = prior.get("avg_total_ms") if prior else None
    if cur_lat is not None and prior_lat is not None:
        old_l = float(prior_lat)
        new_l = float(cur_lat)
        if old_l > 0:
            increase = (new_l - old_l) / old_l
            ok = increase <= LATENCY_TOLERANCE
            status = "OK" if ok else "FAIL"
            if not ok:
                failed = True
            print(
                f"  [{status}] avg_total_ms: {old_l:.0f} -> {new_l:.0f} "
                f"(increase <= {LATENCY_TOLERANCE:.0%})"
            )
    elif cur_lat is not None:
        print(f"  avg_total_ms: {cur_lat} (no prior latency baseline)")

    print()
    if failed:
        print("REGRESSION DETECTED — do not deploy until fixed.")
        sys.exit(1)
    print("No regression beyond tolerance.")
    sys.exit(0)


if __name__ == "__main__":
    main()
