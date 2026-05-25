"""Failure type taxonomy for manual QA and roadmap prioritization."""
from __future__ import annotations

from typing import Dict, List

FAILURE_TYPES = [
    "hallucination",
    "generic_advice",
    "wrong_citation",
    "weak_retrieval",
    "planner_error",
    "memory_conflict",
    "latency_spike",
    "contradiction_missed",
    "unsupported_claim",
]

FAILURE_DESCRIPTIONS = {
    "hallucination": "Claim not supported by retrieved context",
    "generic_advice": "Filler advice (e.g. be authentic) without grounding",
    "wrong_citation": "Source card does not match answer substance",
    "weak_retrieval": "Irrelevant or meta chunks in top results",
    "planner_error": "Wrong agent(s) selected for query intent",
    "memory_conflict": "Stale or conflicting brand memory applied",
    "latency_spike": "First token or retrieval unusually slow",
    "contradiction_missed": "Strategic tension not surfaced",
    "unsupported_claim": "Flagged by claim verification layer",
}


def empty_failure_counts() -> Dict[str, int]:
    return {t: 0 for t in FAILURE_TYPES}


def aggregate_failures(rows: List[Dict]) -> Dict[str, int]:
    """rows: list of {failure_type: str} from manual log."""
    counts = empty_failure_counts()
    for row in rows:
        ft = row.get("failure_type")
        if ft in counts:
            counts[ft] += 1
    return counts
