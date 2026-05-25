"""
Reranking utilities for AI knowledge retrieval (Phase 7 + production hybrid).
- Intent-weighted hybrid fusion (vector + keyword + graph)
- Cross-encoder reranking (sentence-transformers)
"""
from __future__ import annotations

import logging
import threading
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

DEFAULT_RRF_K = 60
DEFAULT_MIN_SCORE = 0.01

_cross_encoder_model = None
_cross_encoder_lock = threading.Lock()


def _chunk_key(chunk: Dict[str, Any]) -> str:
    meta = chunk.get("metadata") or {}
    return str(
        chunk.get("chunk_id")
        or meta.get("file")
        or chunk.get("text", "")[:80]
    )


def reciprocal_rank_fusion(
    ranked_lists: List[List[Dict[str, Any]]],
    k: int = DEFAULT_RRF_K,
    top_n: Optional[int] = None,
) -> List[Dict[str, Any]]:
    if not ranked_lists:
        return []
    if len(ranked_lists) == 1:
        return ranked_lists[0][:top_n] if top_n else ranked_lists[0]

    scores: Dict[str, float] = {}
    by_key: Dict[str, Dict[str, Any]] = {}

    for result_list in ranked_lists:
        for rank, chunk in enumerate(result_list, start=1):
            key = _chunk_key(chunk)
            scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank)
            if key not in by_key:
                by_key[key] = chunk

    merged = []
    for key, rrf_score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
        item = dict(by_key[key])
        item["score"] = rrf_score
        item["rrf_score"] = rrf_score
        merged.append(item)

    return merged[:top_n] if top_n else merged


def _dedupe_chunks(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicate chunks by content prefix."""
    seen = set()
    out = []
    for c in chunks:
        text = (c.get("text") or "")[:120]
        key = (_chunk_key(c), text)
        if key in seen:
            continue
        seen.add(key)
        out.append(c)
    return out


def filter_by_score_threshold(
    chunks: List[Dict[str, Any]],
    min_score: float = DEFAULT_MIN_SCORE,
) -> List[Dict[str, Any]]:
    if min_score <= 0:
        return chunks
    return [
        c
        for c in chunks
        if float(c.get("score") or c.get("hybrid_score") or c.get("rrf_score") or 0) >= min_score
    ]


def _get_cross_encoder():
    """Thread-safe singleton load (avoids meta-tensor races on concurrent warmup + retrieval)."""
    global _cross_encoder_model
    from django.conf import settings

    if _cross_encoder_model is not False and _cross_encoder_model is not None:
        return _cross_encoder_model
    if _cross_encoder_model is False:
        return False

    with _cross_encoder_lock:
        if _cross_encoder_model is not False and _cross_encoder_model is not None:
            return _cross_encoder_model
        if _cross_encoder_model is False:
            return False
        try:
            from sentence_transformers import CrossEncoder

            model_name = getattr(
                settings,
                "RAG_CROSS_ENCODER_MODEL",
                "cross-encoder/ms-marco-MiniLM-L-6-v2",
            )
            device = (getattr(settings, "RAG_CROSS_ENCODER_DEVICE", None) or "").strip()
            if not device:
                try:
                    import torch

                    device = "cuda" if torch.cuda.is_available() else "cpu"
                except Exception:
                    device = "cpu"
            _cross_encoder_model = CrossEncoder(model_name, device=device)
            logger.info("Cross-encoder loaded: %s (device=%s)", model_name, device)
        except Exception as e:
            logger.warning(
                "Cross-encoder load failed: %s — pip install sentence-transformers "
                "or set RAG_CROSS_ENCODER_ENABLED=false",
                e,
            )
            _cross_encoder_model = False
    return _cross_encoder_model


def cross_encoder_rerank(
    query: str,
    chunks: List[Dict[str, Any]],
    top_n: Optional[int] = None,
) -> List[Dict[str, Any]]:
    from django.conf import settings

    if not chunks:
        return []
    if not getattr(settings, "RAG_CROSS_ENCODER_ENABLED", False):
        return chunks[:top_n] if top_n else chunks

    model = _get_cross_encoder()
    if not model:
        return chunks[:top_n] if top_n else chunks

    ce_weight = float(getattr(settings, "RAG_CROSS_ENCODER_BLEND", 0.15))
    texts = []
    for c in chunks:
        meta = c.get("metadata") or {}
        body = (c.get("text") or meta.get("content") or "")[:512]
        texts.append(body)

    try:
        pairs = [[query, t] for t in texts]
        ce_scores = model.predict(pairs)
        rescored = []
        for chunk, ce_raw in zip(chunks, ce_scores):
            c = dict(chunk)
            ce = float(ce_raw)
            # normalize CE logits to 0–1 sigmoid-ish
            ce_norm = 1.0 / (1.0 + pow(2.718, -ce)) if ce != ce else 0.5
            base = float(c.get("hybrid_score") or c.get("score") or c.get("rrf_score") or 0.01)
            final = base * (1.0 - ce_weight) + ce_norm * ce_weight
            c["cross_encoder_score"] = round(ce_norm, 4)
            c["score"] = round(final, 4)
            c["rerank_score"] = c["score"]
            reasons = list(c.get("rerank_reason") or [])
            if ce_norm >= 0.5 and "cross-encoder relevance" not in reasons:
                reasons.append("cross-encoder relevance")
            c["rerank_reason"] = reasons[:5]
            rescored.append(c)
        rescored.sort(key=lambda x: float(x.get("score") or 0), reverse=True)
        return rescored[:top_n] if top_n else rescored
    except Exception as e:
        logger.warning("Cross-encoder predict failed: %s", e)
        return chunks[:top_n] if top_n else chunks


def rerank_knowledge_chunks(
    query: str,
    vector_chunks: List[Dict[str, Any]],
    keyword_chunks: List[Dict[str, Any]],
    top_k: int = 8,
    min_score: float = DEFAULT_MIN_SCORE,
    rrf_k: int = DEFAULT_RRF_K,
    graph_concepts: Optional[List[str]] = None,
    intent: Optional[str] = None,
    use_weighted_hybrid: bool = True,
) -> List[Dict[str, Any]]:
    """
    Production pipeline: weighted hybrid → threshold → cross-encoder.
    Falls back to RRF if use_weighted_hybrid=False.
    """
    from django.conf import settings

    pre_k = int(getattr(settings, "MAX_RERANK_CHUNKS_BEFORE", 12))
    post_k = top_k or int(getattr(settings, "MAX_RERANK_CHUNKS_AFTER", 6))

    if use_weighted_hybrid and getattr(settings, "RAG_WEIGHTED_HYBRID_ENABLED", True):
        from utils.hybrid_retrieval import weighted_hybrid_merge

        fused = weighted_hybrid_merge(
            query,
            vector_chunks,
            keyword_chunks,
            graph_concepts=graph_concepts,
            intent=intent,
            top_n=pre_k,
        )
    else:
        fused = reciprocal_rank_fusion(
            [vector_chunks, keyword_chunks],
            k=rrf_k,
            top_n=pre_k,
        )

    filtered = filter_by_score_threshold(fused, min_score=min_score)
    deduped = _dedupe_chunks(filtered)
    reranked = cross_encoder_rerank(query, deduped, top_n=pre_k)

    from utils.diversity_rerank import apply_diversity_selection

    return apply_diversity_selection(reranked, top_n=post_k)
