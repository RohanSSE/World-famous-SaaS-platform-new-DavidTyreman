"""
Retrieval quality critique — gate answer generation when retrieval is weak.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from django.conf import settings

from user_sessions.services.rag_intelligence import detect_query_intent
from user_sessions.services.retrieval_metrics import score_manifesto_dominance, score_top1_hit


def critique_retrieval_quality(
    query: str,
    chunks: List[Dict[str, Any]],
    case: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Rule-based retrieval critique before answer generation.
    Returns flags + optional prompt suffix for conservative answers.
    """
    case = case or {"query": query}
    case["query"] = query

    top1 = score_top1_hit(case, chunks)
    manifesto = score_manifesto_dominance(case, chunks)
    intent = detect_query_intent(query)

    flags: List[str] = []
    prompt_parts: List[str] = []

    if not chunks:
        flags.append("no_chunks")
        prompt_parts.append("No strong knowledge match. Ask a clarifying question; do not invent principles.")
    elif not top1.get("top1_hit") and case.get("expected_categories"):
        flags.append("top1_miss")
        prompt_parts.append(
            "Retrieved anchor chunk may be weak. Ground only in listed excerpts; avoid generic marketing advice."
        )

    if manifesto.get("strategic_query") and not manifesto.get("manifesto_ok"):
        flags.append("low_manifesto_dominance")
        prompt_parts.append(
            "Manifesto-grounded framing is required for this strategic query. Prefer principles from manifesto excerpts."
        )

    top = chunks[0] if chunks else {}
    if top.get("generic_chunk_penalty"):
        flags.append("generic_top_chunk")
        prompt_parts.append("Top retrieved passage may be generic. Prefer specific manifesto/strategy excerpts.")

    neg = top.get("negative_tag_penalty")
    if neg and float(neg) > 0:
        flags.append("negative_signal_top")
        prompt_parts.append("Avoid viral/growth-hack framing inconsistent with premium/trust positioning.")

    avg_score = 0.0
    if chunks:
        scores = [float(c.get("hybrid_score") or c.get("score") or 0) for c in chunks[:5]]
        avg_score = sum(scores) / len(scores) if scores else 0.0

    low_threshold = float(getattr(settings, "RAG_LOW_CONFIDENCE_THRESHOLD", 0.45))
    if avg_score < low_threshold:
        flags.append("low_retrieval_scores")

    needs_reretrieve = (
        "no_chunks" in flags
        or ("top1_miss" in flags and "low_manifesto_dominance" in flags)
    )

    return {
        "flags": flags,
        "needs_reretrieve": needs_reretrieve,
        "top1_hit": top1.get("top1_hit"),
        "manifesto_dominance": manifesto.get("manifesto_dominance"),
        "manifesto_ok": manifesto.get("manifesto_ok"),
        "avg_hybrid_score": round(avg_score, 4),
        "prompt_suffix": "\n".join(prompt_parts).strip(),
        "intent": intent,
    }
