#!/usr/bin/env python
"""
Build retrieval failure heatmap by strategic intent.

Reads golden_results.json or golden_baseline.json → evaluation/retrieval_heatmap.json
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

INTENT_FROM_CASE = {
    "trust": "trust",
    "premium": "premium",
    "differentiation": "differentiation",
    "authority": "authority",
    "manifesto": "manifesto",
    "positioning": "positioning",
    "emotional": "emotional",
    "tone": "tone",
    "competitor": "differentiation",
    "crisis": "trust",
    "dna": "manifesto",
}


def infer_intent(case_id: str, row: dict) -> str:
    cid = case_id.lower()
    for key, intent in INTENT_FROM_CASE.items():
        if key in cid:
            return intent
    if row.get("strategic_query"):
        return "strategic"
    return "general"


def main():
    for name in ("golden_results.json", "golden_baseline.json"):
        path = ROOT / "evaluation" / name
        if path.exists():
            break
    else:
        print("No golden_results.json or golden_baseline.json — run golden eval first.")
        sys.exit(1)

    data = json.loads(path.read_text(encoding="utf-8"))
    rows = data.get("rows", [])
    if not rows and data.get("results"):
        rows = [r.get("scores", r) for r in data["results"] if r.get("scores")]
    if not rows:
        print("No rows in golden file.")
        sys.exit(1)

    by_intent: dict = defaultdict(lambda: {"total": 0, "failed": 0, "top1_miss": 0, "low_manifesto": 0})

    for row in rows:
        intent = infer_intent(row.get("id", ""), row)
        bucket = by_intent[intent]
        bucket["total"] += 1
        if not row.get("pass", True):
            bucket["failed"] += 1
        if row.get("top1_hit") is False:
            bucket["top1_miss"] += 1
        if row.get("strategic_query") and not row.get("manifesto_ok", True):
            bucket["low_manifesto"] += 1

    heatmap = {}
    for intent, stats in sorted(by_intent.items(), key=lambda x: -x[1]["failed"]):
        t = stats["total"] or 1
        heatmap[intent] = {
            "cases": stats["total"],
            "failure_rate": round(stats["failed"] / t, 3),
            "top1_miss_rate": round(stats["top1_miss"] / t, 3),
            "low_manifesto_rate": round(stats["low_manifesto"] / t, 3),
        }

    out = {
        "source": path.name,
        "intents": heatmap,
        "weakest_intent": max(heatmap.items(), key=lambda x: x[1]["failure_rate"])[0] if heatmap else None,
    }

    out_path = ROOT / "evaluation" / "retrieval_heatmap.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")
    print(f"Weakest intent: {out.get('weakest_intent')}")
    for intent, stats in heatmap.items():
        print(
            f"  {intent}: failure={stats['failure_rate']:.0%} "
            f"top1_miss={stats['top1_miss_rate']:.0%} "
            f"low_manifesto={stats['low_manifesto_rate']:.0%}"
        )


if __name__ == "__main__":
    main()
