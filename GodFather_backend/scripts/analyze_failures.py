#!/usr/bin/env python
"""
Auto failure mining — cluster patterns from golden baseline + evaluation DB.

Usage:
  python scripts/analyze_failures.py
  python scripts/analyze_failures.py --write evaluation/failure_clusters_auto.md
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os_environ = __import__("os")
os_environ.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
os_environ.environ.setdefault("DJANGO_SKIP_KNOWLEDGE_AUTO", "1")

import django  # noqa: E402

django.setup()

FAILURE_CLUSTERS = [
    "generic_reasoning",
    "weak_manifesto_grounding",
    "planner_over_routing",
    "memory_conflict",
    "low_confidence_overclaim",
    "irrelevant_chunk_dominance",
    "citation_mismatch",
    "retrieval_precision_low",
]


def optimize_next_sprint_targets(rows: list, counter: Counter) -> dict:
    """Failure-driven continuous optimization recommendations."""
    n = len(rows) or 1
    metrics = {}
    golden_path = ROOT / "evaluation" / "golden_baseline.json"
    if golden_path.exists():
        metrics = json.loads(golden_path.read_text(encoding="utf-8")).get("metrics", {})

    recommendations = []
    top_cluster = counter.most_common(1)[0][0] if counter else "generic_reasoning"

    if metrics.get("reasoning_drift_avg", 0) > 0.30:
        recommendations.append("Tighten reasoning_drift repair + manifesto slot reservation")
    if metrics.get("manifesto_support_density", 1) < 0.60:
        recommendations.append("Increase MIN_MANIFESTO_CHUNKS and context repair thresholds")
    if metrics.get("hallucination_risk", 1) > 0.25:
        recommendations.append("Enable overclaim suppression + full verify on low confidence")
    if counter.get("low_confidence_overclaim", 0) > n * 0.3:
        recommendations.append("Lower OVERCLAIM_CONFIDENCE_THRESHOLD to 0.55")
    if counter.get("context_conflict", 0) > 2:
        recommendations.append("Strengthen repair_context conflict removal")
    if not recommendations:
        recommendations.append(f"Address top cluster: {top_cluster}")

    return {
        "generated_from": "analyze_failures",
        "top_failure_cluster": top_cluster,
        "cluster_counts": dict(counter.most_common(8)),
        "current_metrics": metrics,
        "recommendations": recommendations,
        "priority_order": [
            "manifesto_support_density",
            "reasoning_drift_avg",
            "low_confidence_overclaim",
            "strategic_density_avg",
            "context_coherence_avg",
        ],
    }


def classify_row(row: dict) -> list:
    tags = []
    if row.get("generic_filler_ratio", 0) > 0.1 or row.get("generic_filler_count", 0) > 0:
        tags.append("generic_reasoning")
    if row.get("retrieval_relevance", 1) < 0.35:
        tags.append("retrieval_precision_low")
    if row.get("grounded_answer_ratio", 1) < 0.65:
        tags.append("weak_manifesto_grounding")
    if row.get("citation_score", 1) < 0.5:
        tags.append("citation_mismatch")
    if row.get("hallucination_risk", 0) > 0.4:
        tags.append("low_confidence_overclaim")
    if row.get("unsupported_count", 0) > 3:
        tags.append("low_confidence_overclaim")
    if row.get("source_coverage", 1) < 0.4:
        tags.append("citation_mismatch")
    if row.get("reasoning_drift_score", 0) > 0.35:
        tags.append("reasoning_drift")
    if row.get("consistency_score", 1) < 0.55:
        tags.append("weak_manifesto_grounding")
    return tags or ["generic_reasoning"]


def load_golden_rows() -> list:
    golden = ROOT / "evaluation" / "golden_baseline.json"
    if not golden.exists():
        return []
    data = json.loads(golden.read_text(encoding="utf-8"))
    return data.get("rows", [])


def load_db_failures() -> list:
    try:
        from user_sessions.models import EvaluationResult

        return list(
            EvaluationResult.objects.filter(passed=False)
            .order_by("-id")[:100]
            .values("case_id", "metrics", "passed")
        )
    except Exception:
        return []


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", type=str, default="", help="Write markdown summary to path")
    args = parser.parse_args()

    rows = load_golden_rows()
    counter: Counter = Counter()
    failed_cases = []

    for row in rows:
        if not row.get("pass", True):
            tags = list(dict.fromkeys(classify_row(row)))
            for t in tags:
                counter[t] += 1
            failed_cases.append(
                {
                    "id": row.get("id"),
                    "tags": tags,
                    "hallucination_risk": row.get("hallucination_risk"),
                    "retrieval_relevance": row.get("retrieval_relevance"),
                }
            )

    total_fail = len(failed_cases) or 1
    print("=" * 60)
    print("FAILURE CLUSTER ANALYSIS")
    print("=" * 60)
    print(f"Failed cases (golden): {len(failed_cases)} / {len(rows)}\n")
    print("Top failure clusters:")
    for cluster, count in counter.most_common():
        pct = round(100 * count / total_fail, 1)
        print(f"  - {cluster}: {count} ({pct}%)")

    print("\nWorst 5 cases:")
    worst = sorted(
        failed_cases,
        key=lambda x: float(x.get("hallucination_risk") or 0),
        reverse=True,
    )[:5]
    for w in worst:
        print(f"  {w['id']}: {', '.join(w['tags'])} risk={w.get('hallucination_risk')}")

    db_rows = load_db_failures()
    if db_rows:
        print(f"\nDB evaluation failures (recent): {len(db_rows)}")

    heatmap_script = ROOT / "scripts" / "build_retrieval_heatmap.py"
    if heatmap_script.exists():
        import subprocess

        subprocess.run([sys.executable, str(heatmap_script)], cwd=str(ROOT), check=False)

    from user_sessions.services.autonomous_eval_clusters import (
        cluster_evaluation_failures,
        format_cluster_report,
    )

    clusters = cluster_evaluation_failures(rows)
    clusters_path = ROOT / "evaluation" / "eval_clusters.json"
    clusters_path.write_text(json.dumps(clusters, indent=2), encoding="utf-8")
    print("\n--- Autonomous eval clusters ---")
    print(format_cluster_report(clusters))

    sprint = optimize_next_sprint_targets(rows, counter)
    print("\n--- Next sprint targets (auto) ---")
    for line in sprint.get("recommendations", []):
        print(f"  • {line}")

    targets_path = ROOT / "evaluation" / "sprint_targets.json"
    targets_path.write_text(json.dumps(sprint, indent=2), encoding="utf-8")
    print(f"\nWrote {targets_path}")

    if args.write:
        out_path = Path(args.write)
        if not out_path.is_absolute():
            out_path = ROOT / out_path
        lines = [
            "# Auto failure mining\n",
            f"Source: golden_baseline.json ({len(rows)} cases)\n",
            "## Cluster distribution\n",
            "| Cluster | Count | % of failures |\n",
            "|---------|-------|----------------|\n",
        ]
        for cluster, count in counter.most_common():
            pct = round(100 * count / total_fail, 1)
            lines.append(f"| `{cluster}` | {count} | {pct}% |\n")
        lines.append("\n## Worst cases\n")
        for w in worst:
            lines.append(f"- **{w['id']}**: {', '.join(w['tags'])}\n")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text("".join(lines), encoding="utf-8")
        print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
