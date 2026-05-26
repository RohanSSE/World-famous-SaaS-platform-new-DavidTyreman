"""
Production hybrid retrieval scoring: vector + keyword + graph + cross-encoder.

final_score = vector*w_v + keyword*w_k + graph*w_g (+ cross-encoder blended in rerank stage)
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

from django.conf import settings

logger = logging.getLogger(__name__)

# Intent profile → channel weights (must sum ~1.0)
HYBRID_WEIGHT_PROFILES: Dict[str, Dict[str, float]] = {
    "manifesto": {"vector": 0.75, "keyword": 0.10, "graph": 0.15},
    "trust": {"vector": 0.78, "keyword": 0.12, "graph": 0.10},
    "differentiation": {"vector": 0.74, "keyword": 0.11, "graph": 0.15},
    "strategic": {"vector": 0.72, "keyword": 0.12, "graph": 0.16},
    "branding": {"vector": 0.60, "keyword": 0.25, "graph": 0.15},
    "tone": {"vector": 0.50, "keyword": 0.40, "graph": 0.10},
    "default": {"vector": 0.65, "keyword": 0.20, "graph": 0.15},
}

# Map detect_query_intent() → hybrid profile
INTENT_TO_PROFILE = {
    "manifesto": "manifesto",
    "differentiation": "differentiation",
    "positioning": "strategic",
    "emotional": "branding",
    "trust": "trust",
    "content": "tone",
    "general": "default",
}

DEFAULT_CE_BLEND = 0.15
MANIFESTO_CATEGORY_BOOST = 0.08
STRATEGIC_MANIFESTO_BOOST = 0.10
STRATEGIC_QUERY_TAGS = frozenset(
    {
        "trust", "authority", "positioning", "premium", "differentiation",
        "manifesto", "brand_book", "audience_psychology",
    }
)


def detect_hybrid_profile(query: str, intent: Optional[str] = None) -> str:
    q = query.lower()
    if intent is None:
        from user_sessions.services.rag_intelligence import detect_query_intent

        intent = detect_query_intent(query)
    if any(w in q for w in ("tone", "voice", "sound like", "writing style")):
        return "tone"
    return INTENT_TO_PROFILE.get(intent, "default")


def get_hybrid_weights(query: str, intent: Optional[str] = None) -> Dict[str, float]:
    profile = detect_hybrid_profile(query, intent)
    custom = getattr(settings, "RAG_HYBRID_WEIGHTS", None)
    if isinstance(custom, dict) and profile in custom:
        return dict(custom[profile])
    return dict(HYBRID_WEIGHT_PROFILES.get(profile, HYBRID_WEIGHT_PROFILES["default"]))


def _chunk_key(chunk: Dict[str, Any]) -> str:
    meta = chunk.get("metadata") or {}
    return str(
        chunk.get("chunk_id")
        or meta.get("file")
        or chunk.get("text", "")[:80]
    )


def _normalize_rank_scores(chunks: List[Dict[str, Any]]) -> Dict[str, float]:
    """Map chunk key → 0–1 score from rank position or existing score."""
    if not chunks:
        return {}
    raw: Dict[str, float] = {}
    for rank, chunk in enumerate(chunks, start=1):
        key = _chunk_key(chunk)
        dist = chunk.get("pgvector_distance")
        score_val = chunk.get("score")
        if dist is not None:
            raw[key] = max(0.0, 1.0 - float(dist))
        elif score_val is not None:
            try:
                s = float(score_val)
                raw[key] = s if s > 0 else 1.0 / rank
            except (TypeError, ValueError):
                raw[key] = 1.0 / rank
        else:
            raw[key] = 1.0 / rank
    max_s = max(raw.values()) or 1.0
    return {k: v / max_s for k, v in raw.items()}


def _graph_match_score(chunk: Dict[str, Any], graph_concepts: List[str]) -> float:
    if not graph_concepts:
        return 0.0
    meta = chunk.get("metadata") or {}
    text = (
        (chunk.get("text") or "")
        + " "
        + (meta.get("title") or "")
        + " "
        + (meta.get("category") or "")
    ).lower()
    hits = sum(1 for c in graph_concepts if c.lower() in text)
    return min(1.0, hits / max(len(graph_concepts), 1))


def weighted_hybrid_merge(
    query: str,
    vector_chunks: List[Dict[str, Any]],
    keyword_chunks: List[Dict[str, Any]],
    graph_concepts: Optional[List[str]] = None,
    intent: Optional[str] = None,
    top_n: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Fuse vector + keyword lists with intent-weighted channel scores.
    Sets chunk['vector_score'], ['keyword_score'], ['graph_score'], ['hybrid_score'].
    """
    weights = get_hybrid_weights(query, intent)
    v_norm = _normalize_rank_scores(vector_chunks)
    k_norm = _normalize_rank_scores(keyword_chunks)
    graph_concepts = graph_concepts or []

    by_key: Dict[str, Dict[str, Any]] = {}
    for lst in (vector_chunks, keyword_chunks):
        for c in lst:
            k = _chunk_key(c)
            if k not in by_key:
                by_key[k] = dict(c)

    from utils.strategic_tags import (
        build_rerank_reasons,
        detect_query_strategic_tags,
        negative_tag_penalty,
        strategic_tag_overlap_boost,
    )

    query_tags = detect_query_strategic_tags(query)

    merged: List[Dict[str, Any]] = []
    for key, chunk in by_key.items():
        c = dict(chunk)
        vs = v_norm.get(key, 0.0)
        ks = k_norm.get(key, 0.0)
        gs = _graph_match_score(c, graph_concepts)
        hybrid = (
            vs * weights["vector"]
            + ks * weights["keyword"]
            + gs * weights["graph"]
        )
        meta = c.get("metadata") or {}
        cat = (meta.get("category") or c.get("category") or "").lower()
        if cat in ("manifesto", "brand_book", "brandbook"):
            hybrid += float(getattr(settings, "RAG_MANIFESTO_CATEGORY_BOOST", MANIFESTO_CATEGORY_BOOST))
            if query_tags and STRATEGIC_QUERY_TAGS.intersection(set(query_tags)):
                hybrid += float(
                    getattr(settings, "RAG_STRATEGIC_MANIFESTO_BOOST", STRATEGIC_MANIFESTO_BOOST)
                )

        chunk_tags = meta.get("strategic_tags") or c.get("strategic_tags") or []
        tag_boost = strategic_tag_overlap_boost(query_tags, chunk_tags)
        if tag_boost:
            hybrid += tag_boost
            c["strategic_tag_boost"] = round(tag_boost, 4)

        weak_intents = {
            "trust", "differentiation", "brand_book", "manifesto",
            "audience_psychology", "emotional_positioning", "emotional_branding",
            "founder_story", "positioning", "competitor", "market_enemy",
            "positioning_archetype", "audience_fear", "audience_desire", "identity_signal",
        }
        q_weak = weak_intents.intersection(set(query_tags))
        if query_tags and q_weak:
            hybrid += float(getattr(settings, "WEAK_INTENT_RERANK_BOOST", 0.10))
            if q_weak & {"differentiation", "positioning", "audience_psychology"}:
                hybrid += float(getattr(settings, "WEAK_CLUSTER_EXTRA_BOOST", 0.04))
        if cat in ("manifesto", "brand_book", "branding", "positioning", "strategy") and query_tags:
            hybrid += float(getattr(settings, "RAG_STRATEGIC_CATEGORY_BOOST", 0.06))

        chunk_text = c.get("text") or ""
        neg_pen = negative_tag_penalty(query_tags, chunk_text, chunk_tags)
        if neg_pen:
            hybrid = max(0.0, hybrid - neg_pen)
            c["negative_tag_penalty"] = round(neg_pen, 4)

        c["vector_score"] = round(vs, 4)
        c["keyword_score"] = round(ks, 4)
        c["graph_score"] = round(gs, 4)
        c["hybrid_score"] = round(hybrid, 4)
        c["score"] = hybrid
        c["rrf_score"] = hybrid
        merged.append(c)

    merged.sort(key=lambda x: float(x.get("hybrid_score") or 0), reverse=True)
    merged = merged[:top_n] if top_n else merged

    from utils.source_reliability import apply_source_reliability
    from utils.chunk_generic_penalty import apply_generic_chunk_penalty

    merged = apply_source_reliability(merged)
    out = []
    for c in merged:
        item = apply_generic_chunk_penalty(c)
        item["rerank_reason"] = build_rerank_reasons(
            item,
            query_tags,
            tag_boost=float(item.get("strategic_tag_boost") or 0),
            generic_penalty=bool(item.get("generic_chunk_penalty")),
            negative_penalty=float(item.get("negative_tag_penalty") or 0),
        )
        out.append(item)
    return out
