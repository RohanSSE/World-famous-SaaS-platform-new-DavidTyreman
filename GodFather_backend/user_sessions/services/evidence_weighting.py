"""
Evidence weighting — manifesto and verified memory rank above generic knowledge.
"""
from __future__ import annotations

from typing import Any, Dict, List

from django.conf import settings

DEFAULT_SOURCE_WEIGHT = {
    "manifesto": 1.0,
    "verified_memory": 0.9,
    "brand_memory": 0.9,
    "strategy": 0.85,
    "strategic": 0.85,
    "positioning": 0.85,
    "branding": 0.8,
    "psychology": 0.75,
    "founder_notes": 0.85,
    "founder": 0.85,
    "user_document": 0.88,
    "strategy_doc": 0.8,
    "marketing": 0.55,
    "content": 0.5,
    "generic": 0.4,
    "knowledge": 0.45,
}


def get_source_weights() -> Dict[str, float]:
    custom = getattr(settings, "SOURCE_EVIDENCE_WEIGHTS", None)
    if isinstance(custom, dict):
        return {**DEFAULT_SOURCE_WEIGHT, **custom}
    return dict(DEFAULT_SOURCE_WEIGHT)


def evidence_weight_for_chunk(chunk: Dict[str, Any]) -> float:
    meta = chunk.get("metadata") or {}
    cat = (meta.get("category") or chunk.get("category") or "generic").lower()
    role = chunk.get("_context_role", "")
    weights = get_source_weights()

    if role == "anchor_manifesto" or cat == "manifesto":
        return weights.get("manifesto", 1.0)
    if role == "memory_alignment":
        return weights.get("verified_memory", 0.9)
    if cat in weights:
        return weights[cat]
    if chunk.get("generic_chunk_penalty"):
        return weights.get("generic", 0.4)
    return weights.get("knowledge", 0.45)


def apply_evidence_weights(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Attach evidence_weight and blend into score."""
    out = []
    for c in chunks:
        item = dict(c)
        w = evidence_weight_for_chunk(item)
        item["evidence_weight"] = round(w, 3)
        base = float(item.get("hybrid_score") or item.get("score") or 0)
        if base > 0:
            blended = base * (0.7 + 0.3 * w)
            item["hybrid_score"] = round(blended, 4)
            item["score"] = item["hybrid_score"]
        out.append(item)
    out.sort(key=lambda x: float(x.get("hybrid_score") or 0), reverse=True)
    return out


def weighted_source_confidence(sources: List[Dict[str, Any]], chunks: List[Dict[str, Any]]) -> float:
    """Reasoning confidence inherited from source evidence weights."""
    if chunks:
        ws = [evidence_weight_for_chunk(c) for c in chunks[:6]]
        return round(sum(ws) / len(ws), 3) if ws else 0.5
    if sources:
        weights = get_source_weights()
        cats = [(s.get("category") or "knowledge").lower() for s in sources[:5]]
        ws = [weights.get(c, 0.45) for c in cats]
        return round(sum(ws) / len(ws), 3)
    return 0.5
