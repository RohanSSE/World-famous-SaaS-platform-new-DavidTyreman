"""
Retrieval quality metrics — top-1 hit rate, manifesto dominance, per-case scoring.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from user_sessions.services.rag_intelligence import detect_query_intent

STRATEGIC_INTENTS_FOR_MANIFESTO = frozenset(
    {"trust", "authority", "positioning", "differentiation", "premium", "manifesto"}
)


def _chunk_category(chunk: Dict[str, Any]) -> str:
    meta = chunk.get("metadata") or {}
    return (meta.get("category") or chunk.get("category") or "").lower().strip()


def _chunk_title(chunk: Dict[str, Any]) -> str:
    meta = chunk.get("metadata") or {}
    return (meta.get("title") or meta.get("document_title") or "").lower()


def _chunk_text(chunk: Dict[str, Any]) -> str:
    return (chunk.get("text") or "").lower()


def score_top1_hit(case: Dict[str, Any], chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    top1_hit_rate component: was rank-1 chunk strategically correct?
    """
    if not chunks:
        return {"top1_hit": False, "top1_category": "", "top1_title": ""}

    top = chunks[0]
    cat = _chunk_category(top)
    title = _chunk_title(top)
    text = _chunk_text(top)

    expected_cats = [c.lower() for c in case.get("expected_categories", [])]
    expected_sources = [s.lower() for s in case.get("expected_sources", [])]
    concepts = [c.lower() for c in case.get("expected_concepts", [])]

    hit = False
    if expected_cats and cat in expected_cats:
        hit = True
    if not hit and expected_sources:
        if any(s in title or s in text for s in expected_sources):
            hit = True
    if not hit and concepts:
        concept_hits = sum(1 for c in concepts if len(c) > 3 and c in text)
        if concept_hits >= max(1, len(concepts) // 3):
            hit = True
    if not hit and expected_cats and "manifesto" in expected_cats and "manifesto" in cat:
        hit = True

    return {
        "top1_hit": hit,
        "top1_category": cat,
        "top1_title": title[:80],
        "top1_generic_penalty": bool(top.get("generic_chunk_penalty")),
        "top1_rerank_reason": top.get("rerank_reason", []),
    }


def score_manifesto_dominance(
    case: Dict[str, Any],
    chunks: List[Dict[str, Any]],
    intent: Optional[str] = None,
) -> Dict[str, Any]:
    """
    manifesto_ratio = manifesto_chunks_in_top5 / min(5, len(chunks))
    Only scored for strategic intents.
    """
    intent = intent or detect_query_intent(case.get("query", ""))
    tags = case.get("strategic_tags") or []
    is_strategic = (
        intent in ("manifesto", "trust", "positioning", "differentiation")
        or "manifesto" in [c.lower() for c in case.get("expected_categories", [])]
        or any(t in STRATEGIC_INTENTS_FOR_MANIFESTO for t in tags)
    )

    top5 = chunks[:5]
    if not top5:
        return {"manifesto_dominance": 0.0, "manifesto_in_top5": 0, "strategic_query": is_strategic}

    from user_sessions.services.context_orchestration import _is_manifesto_chunk

    manifesto_count = sum(1 for c in top5 if _is_manifesto_chunk(c))
    ratio = manifesto_count / len(top5)

    return {
        "manifesto_dominance": round(ratio, 3),
        "manifesto_in_top5": manifesto_count,
        "strategic_query": is_strategic,
        "manifesto_ok": (ratio >= 0.6) if is_strategic else True,
    }


def score_split_retrieval_metrics(
    case: Dict[str, Any],
    chunks: List[Dict[str, Any]],
    context_composition: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Three-metric visibility (replaces broad retrieval_precision alone).
    """
    top1 = score_top1_hit(case, chunks)
    manifesto = score_manifesto_dominance(case, chunks)
    comp = context_composition or {}

    return {
        "top1_anchor_accuracy": 1.0 if top1.get("top1_hit") else 0.0,
        "manifesto_support_density": comp.get(
            "manifesto_dominance", manifesto.get("manifesto_dominance", 0)
        ),
        "context_coherence": comp.get("context_coherence", 1.0),
        "strategic_density": comp.get("strategic_density", 0.0),
        "context_conflict_score": comp.get("context_conflict_score", 0.0),
    }


def aggregate_retrieval_metrics(rows: List[Dict[str, Any]]) -> Dict[str, float]:
    n = len(rows) or 1
    top1_hits = sum(1 for r in rows if r.get("top1_hit"))
    strategic = [r for r in rows if r.get("strategic_query")]
    manifesto_ok = sum(1 for r in strategic if r.get("manifesto_ok"))
    return {
        "top1_hit_rate": round(top1_hits / n, 3),
        "top1_anchor_accuracy": round(top1_hits / n, 3),
        "manifesto_dominance_avg": round(
            sum(r.get("manifesto_dominance", 0) for r in rows) / n, 3
        ),
        "manifesto_support_density": round(
            sum(
                r.get("manifesto_support_density", r.get("manifesto_dominance", 0))
                for r in rows
            )
            / n,
            3,
        ),
        "manifesto_dominance_strategic_avg": round(
            sum(r.get("manifesto_dominance", 0) for r in strategic) / max(len(strategic), 1),
            3,
        ),
        "manifesto_ok_rate": round(manifesto_ok / max(len(strategic), 1), 3),
        "context_coherence_avg": round(
            sum(r.get("context_coherence", 1.0) for r in rows) / n, 3
        ),
        "strategic_density_avg": round(
            sum(r.get("strategic_density", 0) for r in rows) / n, 3
        ),
        "reasoning_drift_avg": round(
            sum(r.get("reasoning_drift_score", 0) for r in rows) / n, 3
        ),
    }
