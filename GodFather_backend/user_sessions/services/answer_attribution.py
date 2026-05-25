"""
Explainable claim attribution — map recommendations to sources/memory/graph.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

from .rag_evaluation import _sentences, _token_set

CLAIM_PATTERNS = (
    re.compile(r"\b(should|must|need to|recommend|focus on|prioritize)\b", re.I),
)


def _source_keys(sources: List[Dict[str, Any]]) -> List[str]:
    keys = []
    for s in sources:
        cat = (s.get("category") or "knowledge").lower()
        title = (s.get("title") or s.get("file") or "")[:40].lower()
        if title:
            keys.append(f"{cat}:{title.split()[0]}")
        else:
            keys.append(cat)
    return keys


def extract_claim_attributions(
    answer: str,
    context: str,
    sources: List[Dict[str, Any]],
    graph_concepts: List[str] = None,
    memory_snippets: List[str] = None,
) -> List[Dict[str, Any]]:
    """
    Heuristic claim → supported_by mapping for explainable AI.
    """
    graph_concepts = graph_concepts or []
    memory_snippets = memory_snippets or []
    ctx_lower = (context or "").lower()
    mem_text = " ".join(memory_snippets).lower()
    attributions: List[Dict[str, Any]] = []

    for sent in _sentences(answer):
        if len(sent) < 25:
            continue
        if not any(p.search(sent) for p in CLAIM_PATTERNS):
            continue

        supported_by: List[str] = []
        sent_lower = sent.lower()
        st = _token_set(sent)

        for s in sources:
            cat = (s.get("category") or "").lower()
            title = (s.get("title") or "").lower()
            reasons = s.get("retrieval_reasons") or []
            if cat and cat in ctx_lower and any(w in sent_lower for w in cat.split() if len(w) > 3):
                supported_by.append(f"source:{cat}")
            if title and any(w in sent_lower for w in title.split()[:4] if len(w) > 4):
                supported_by.append(f"source:{title[:30]}")
            for r in reasons:
                if any(w in sent_lower for w in r.lower().split() if len(w) > 4):
                    supported_by.append(f"retrieval:{r[:40]}")

        for c in graph_concepts:
            if c.lower() in sent_lower or c.lower() in ctx_lower:
                supported_by.append(f"graph:{c}")

        if mem_text:
            overlap = len(st & _token_set(mem_text)) / max(len(st), 1)
            if overlap >= 0.3:
                supported_by.append("memory:session")

        if any(t in ctx_lower for t in ("brand book", "manifesto", "brandbook")) and any(
            t in sent_lower for t in ("brand book", "manifesto", "brandbook")
        ):
            supported_by.append("brand_book_alignment")

        supported_by = list(dict.fromkeys(supported_by))[:5]
        attributions.append(
            {
                "claim": sent[:200],
                "supported_by": supported_by if supported_by else ["unattributed"],
            }
        )

    return attributions[:10]
