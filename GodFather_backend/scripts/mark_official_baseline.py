#!/usr/bin/env python
"""Snapshot golden_baseline.json as official release baseline after full golden run."""
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "evaluation" / "golden_baseline.json"
DST = ROOT / "evaluation" / "official_baseline.json"
META = ROOT / "evaluation" / "official_baseline_meta.json"


def main():
    if not SRC.exists():
        print("Run first: python scripts/run_golden_evaluation.py")
        raise SystemExit(1)

    data = json.loads(SRC.read_text(encoding="utf-8"))
    shutil.copy2(SRC, DST)

    meta = {
        "marked_at": datetime.now(timezone.utc).isoformat(),
        "cases": data.get("cases"),
        "passed": data.get("passed"),
        "pass_rate": round((data.get("passed") or 0) / max(data.get("cases") or 1, 1), 3),
        "metrics": data.get("metrics", {}),
        "note": "Official baseline — architecture frozen after this point.",
    }
    META.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print(f"Official baseline saved: {DST}")
    print(f"Pass rate: {meta['passed']}/{meta['cases']} ({meta['pass_rate']})")
    print(f"Metrics: retrieval={meta['metrics'].get('retrieval_precision')} "
          f"hallucination={meta['metrics'].get('hallucination_risk')} "
          f"grounded={meta['metrics'].get('grounded_answer_ratio')}")


if __name__ == "__main__":
    main()
