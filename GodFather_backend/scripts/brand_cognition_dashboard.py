#!/usr/bin/env python
"""Enterprise observability — hallucination, consistency, drift, repair KPIs."""
import json
import os
import sys
from pathlib import Path

import django

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
django.setup()

GOLDEN = ROOT / "evaluation" / "golden_baseline.json"
HEATMAP = ROOT / "evaluation" / "retrieval_heatmap.json"


def main():
    if not GOLDEN.exists():
        print("Run: python scripts/run_golden_evaluation.py")
        sys.exit(1)

    data = json.loads(GOLDEN.read_text(encoding="utf-8"))
    m = data.get("metrics", {})
    rows = data.get("rows", [])

    print("=" * 60)
    print("BRAND COGNITION OBSERVABILITY")
    print("=" * 60)
    print(f"Cases passed: {data.get('passed')}/{data.get('cases')}\n")

    panels = [
        ("hallucination_risk", m.get("hallucination_risk"), "< 0.20"),
        ("grounded_answer_ratio", m.get("grounded_answer_ratio"), "> 0.90"),
        ("consistency_score_avg", m.get("consistency_score_avg"), "> 0.75"),
        ("reasoning_drift_avg", m.get("reasoning_drift_avg"), "< 0.25"),
        ("overclaim_rate", m.get("overclaim_rate"), "< 0.30"),
        ("manifesto_support_density", m.get("manifesto_support_density"), "> 0.60"),
        ("retrieval_precision", m.get("retrieval_precision"), "> 0.75"),
        ("self_repair_success_rate", m.get("self_repair_success_rate"), "> 0.55"),
        ("repair_gain_avg", m.get("repair_gain_avg"), "higher"),
    ]
    for name, val, target in panels:
        status = "[OK]" if val is not None else "[--]"
        if name == "hallucination_risk" and val is not None and val < 0.20:
            status = "[OK]"
        elif name == "hallucination_risk" and val is not None:
            status = "[GAP]"
        elif name == "grounded_answer_ratio" and val is not None and val >= 0.90:
            status = "[OK]"
        elif name == "grounded_answer_ratio" and val is not None:
            status = "[GAP]"
        elif name == "consistency_score_avg" and val is not None and val >= 0.75:
            status = "[OK]"
        elif name == "consistency_score_avg" and val is not None:
            status = "[GAP]"
        print(f"  {status} {name}: {val} (target {target})")

    if rows:
        high_risk = sorted(rows, key=lambda r: float(r.get("hallucination_risk") or 0), reverse=True)[:5]
        print("\nTop hallucination risk cases:")
        for r in high_risk:
            print(f"  - {r.get('id')}: risk={r.get('hallucination_risk')} ground={r.get('groundedness')}")

    if HEATMAP.exists():
        hm = json.loads(HEATMAP.read_text(encoding="utf-8"))
        print("\nRetrieval heatmap (weakest intents):")
        intents = hm.get("intents", {})
        for intent, stats in sorted(intents.items(), key=lambda x: x[1].get("failure_rate", 0), reverse=True)[:5]:
            print(
                f"  - {intent}: failure={stats.get('failure_rate', 0):.0%} "
                f"low_manifesto={stats.get('low_manifesto_rate', 0):.0%}"
            )

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
