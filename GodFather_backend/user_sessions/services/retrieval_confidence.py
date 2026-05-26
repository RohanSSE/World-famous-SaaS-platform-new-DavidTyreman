"""
Retrieval confidence gating — conservative answers when knowledge match is weak.
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

from django.conf import settings

LOW_THRESHOLD = float(getattr(settings, "RAG_LOW_CONFIDENCE_THRESHOLD", 0.45))
MODERATE_THRESHOLD = float(getattr(settings, "RAG_MODERATE_CONFIDENCE_THRESHOLD", 0.65))

LOW_CONFIDENCE_PROMPT = """
RETRIEVAL CONFIDENCE: LOW
Retrieved knowledge is weak for this query. Avoid strong strategic conclusions.
Prefer exploratory recommendations, clarifying questions, and explicit uncertainty.
Do not invent frameworks or principles not present in the retrieved knowledge.
"""

MODERATE_CONFIDENCE_PROMPT = """
RETRIEVAL CONFIDENCE: MODERATE
Ground recommendations in retrieved knowledge; flag uncertainty where evidence is thin.
"""


def assess_retrieval_confidence(chunks: List[Dict[str, Any]]) -> Tuple[str, float, str]:
    """
    Returns (mode, avg_hybrid_score, prompt_suffix).
    mode: high_confidence | moderate | low_confidence
    """
    if not chunks:
        return "low_confidence", 0.0, LOW_CONFIDENCE_PROMPT

    scores = [
        float(c.get("hybrid_score") or c.get("score") or 0)
        for c in chunks[:5]
    ]
    avg = sum(scores) / len(scores) if scores else 0.0

    if avg < LOW_THRESHOLD:
        return "low_confidence", round(avg, 4), LOW_CONFIDENCE_PROMPT
    if avg < MODERATE_THRESHOLD:
        return "moderate", round(avg, 4), MODERATE_CONFIDENCE_PROMPT
    return "high_confidence", round(avg, 4), ""


def confidence_label(mode: str) -> str:
    return {
        "high_confidence": "High Confidence",
        "moderate": "Moderate Confidence",
        "low_confidence": "Low Confidence",
    }.get(mode, "Moderate Confidence")
