"""
Source reliability weighting — manifesto/strategy chunks rank above generic marketing noise.
"""
from __future__ import annotations

from typing import Any, Dict

from django.conf import settings

DEFAULT_RELIABILITY = {
    "manifesto": 1.0,
    "strategy": 0.9,
    "strategic": 0.9,
    "positioning": 0.88,
    "branding": 0.85,
    "founder_notes": 0.85,
    "founder": 0.85,
    "brand_memory": 0.8,
    "psychology": 0.8,
    "marketing": 0.65,
    "content": 0.6,
    "sales": 0.6,
    "knowledge": 0.55,
    "generic": 0.4,
}


def get_reliability_map() -> Dict[str, float]:
    custom = getattr(settings, "SOURCE_RELIABILITY", None)
    if isinstance(custom, dict):
        return {**DEFAULT_RELIABILITY, **custom}
    return dict(DEFAULT_RELIABILITY)


def source_reliability_for_chunk(chunk: Dict[str, Any]) -> float:
    meta = chunk.get("metadata") or {}
    cat = (meta.get("category") or chunk.get("category") or "generic").lower().strip()
    title = (meta.get("title") or "").lower()
    file_ref = (meta.get("file") or meta.get("path") or "").lower()

    rel_map = get_reliability_map()

    if "manifesto" in cat or "manifesto" in file_ref:
        return rel_map.get("manifesto", 1.0)
    if any(w in title for w in ("principle", "dna", "differentiation", "trust", "positioning")):
        return max(rel_map.get("branding", 0.85), rel_map.get("strategy", 0.9))
    if cat in rel_map:
        return rel_map[cat]
    if cat in ("branding",):
        return rel_map.get("branding", 0.85)
    return rel_map.get("generic", 0.4)


def apply_source_reliability(chunks: list) -> list:
    """Multiply hybrid_score by reliability; attach source_reliability field."""
    out = []
    for c in chunks:
        item = dict(c)
        rel = source_reliability_for_chunk(item)
        item["source_reliability"] = round(rel, 3)
        base = float(item.get("hybrid_score") or item.get("score") or 0)
        if base > 0:
            adjusted = base * rel
            item["hybrid_score"] = round(adjusted, 4)
            item["score"] = adjusted
            item["rrf_score"] = adjusted
        out.append(item)
    out.sort(key=lambda x: float(x.get("hybrid_score") or 0), reverse=True)
    return out
