"""
Diversity-aware selection — breadth over redundant near-duplicate chunks.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Set

from django.conf import settings


def _chunk_doc_key(chunk: Dict[str, Any]) -> str:
    meta = chunk.get("metadata") or {}
    return (
        meta.get("file")
        or meta.get("path")
        or meta.get("title")
        or str(chunk.get("chunk_id", ""))
    )[:120]


def _token_set(text: str) -> Set[str]:
    return set(re.findall(r"[a-z0-9']+", (text or "").lower()))


def semantic_similarity_jaccard(a: str, b: str) -> float:
    """Fast proxy for chunk similarity (no extra embeddings)."""
    ta, tb = _token_set(a), _token_set(b)
    if not ta or not tb:
        return 0.0
    inter = len(ta & tb)
    union = len(ta | tb)
    return inter / union if union else 0.0


def apply_diversity_selection(
    chunks: List[Dict[str, Any]],
    top_n: int = None,
) -> List[Dict[str, Any]]:
    """
    - Max N chunks per source document
    - Skip chunks too similar to already-selected (Jaccard >= threshold)
    """
    if not chunks:
        return []

    max_per_doc = int(getattr(settings, "MAX_CHUNKS_PER_DOCUMENT", 2))
    max_sim = float(getattr(settings, "MAX_CHUNK_SEMANTIC_SIMILARITY", 0.92))
    top_n = top_n or len(chunks)

    selected: List[Dict[str, Any]] = []
    doc_counts: Dict[str, int] = {}
    rejected: List[Dict[str, Any]] = []

    for chunk in chunks:
        doc = _chunk_doc_key(chunk)
        if doc_counts.get(doc, 0) >= max_per_doc:
            c = dict(chunk)
            c["_diversity_reject"] = "max_per_document"
            rejected.append(c)
            continue

        text = (chunk.get("text") or "")[:600]
        too_similar = False
        for sel in selected:
            sel_text = (sel.get("text") or "")[:600]
            if semantic_similarity_jaccard(text, sel_text) >= max_sim:
                too_similar = True
                break

        if too_similar:
            c = dict(chunk)
            c["_diversity_reject"] = "semantic_duplicate"
            rejected.append(c)
            continue

        selected.append(chunk)
        doc_counts[doc] = doc_counts.get(doc, 0) + 1
        if len(selected) >= top_n:
            break

    # Attach rejected list on first selected chunk for trace (optional)
    if selected and rejected:
        selected[0]["_diversity_rejected"] = [
            {"title": (r.get("metadata") or {}).get("title", ""), "reason": r.get("_diversity_reject")}
            for r in rejected[:8]
        ]

    return selected
