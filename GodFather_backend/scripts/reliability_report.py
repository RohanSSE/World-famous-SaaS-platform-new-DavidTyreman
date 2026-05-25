#!/usr/bin/env python
"""Print enterprise reliability KPI dashboard from golden_baseline.json."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

TARGETS = {
    "pass_rate": (">", 12 / 25),
    "hallucination_risk": ("<", 0.20),
    "unsupported_claim_rate": ("<", 0.25),
    "high_inference_rate": ("<", 0.35),
    "contradiction_rate": ("<", 0.25),
    "grounded_answer_ratio": (">", 0.90),
    "claim_grounded_ratio_avg": (">", 0.85),
    "reasoning_drift_avg": ("<", 0.25),
    "overclaim_rate": ("<", 0.30),
    "manifesto_support_density": (">", 0.60),
    "context_conflict_rate": ("<", 0.25),
    "consistency_score_avg": (">", 0.75),
    "self_repair_success_rate": (">", 0.55),
    "strategic_density_avg": (">", 0.70),
    "retrieval_precision": (">", 0.75),
}


def main():
    path = ROOT / "evaluation" / "golden_baseline.json"
    if not path.exists():
        print("Run: python scripts/run_golden_evaluation.py")
        sys.exit(1)
    data = json.loads(path.read_text(encoding="utf-8"))
    m = data.get("metrics", {})
    cases = data.get("cases") or 0
    passed = data.get("passed") or 0
    if cases:
        m = {**m, "pass_rate": round(passed / cases, 3)}
    rows = data.get("rows") or []
    if rows and "claim_grounded_ratio_avg" not in m:
        ratios = [float(r.get("claim_grounded_ratio") or 0) for r in rows]
        if ratios:
            m["claim_grounded_ratio_avg"] = round(sum(ratios) / len(ratios), 3)
    print("=" * 60)
    print("BRAND COGNITION CALIBRATION DASHBOARD")
    print("=" * 60)
    for key, (op, target) in TARGETS.items():
        val = m.get(key)
        if val is None:
            print(f"  {key}: (not measured)")
            continue
        ok = (val < target) if op == "<" else (val > target)
        status = "OK" if ok else "GAP"
        print(f"  [{status}] {key}: {val} (target {op} {target})")
    print(f"\nCases: {passed}/{cases} passed (target 12+/25)")
    if m.get("pass_rate") is not None:
        ok = passed >= 12
        print(f"  pass_rate: {m['pass_rate']} [{'OK' if ok else 'GAP'}]")


if __name__ == "__main__":
    main()
