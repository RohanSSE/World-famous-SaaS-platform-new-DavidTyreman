"""
Chunk quality audit — weak, duplicate, generic detection (retrieval bottleneck tooling).
"""
from __future__ import annotations

import re
from collections import Counter
from typing import Any, Dict, List

GENERIC_PATTERNS = re.compile(
    r"\b(in today's world|leverage|synergy|best-in-class|cutting-edge|"
    r"holistic|empower|disrupt|game.?changer|world.?class|innovative solution)\b",
    re.I,
)
WEAK_PATTERNS = re.compile(
    r"\b(important|various|many|several|things|stuff|etc\.?|and so on)\b",
    re.I,
)


def _generic_score(text: str) -> float:
    if not text:
        return 1.0
    hits = len(GENERIC_PATTERNS.findall(text)) + len(WEAK_PATTERNS.findall(text))
    words = max(len(text.split()), 1)
    return min(1.0, hits / words * 8)


def _normalize_snippet(text: str, n: int = 120) -> str:
    t = re.sub(r"\s+", " ", (text or "").lower().strip())
    return t[:n]


def audit_chunks(limit: int = 500, generic_threshold: float = 0.35) -> Dict[str, Any]:
    from ai_knowledge.models import AIKnowledgeChunk

    qs = AIKnowledgeChunk.objects.all().order_by("chunk_id")[:limit]
    rows = list(qs)
    snippets = [_normalize_snippet(c.content) for c in rows]
    dup_counter = Counter(snippets)
    duplicates = [s for s, n in dup_counter.items() if n > 1 and s]

    weak: List[Dict[str, Any]] = []
    generic: List[Dict[str, Any]] = []
    for c in rows:
        g = _generic_score(c.content)
        short = len((c.content or "").strip()) < 80
        if g >= generic_threshold:
            generic.append(
                {
                    "chunk_id": c.chunk_id,
                    "title": c.title,
                    "category": c.category,
                    "generic_score": round(g, 3),
                }
            )
        if short or g >= 0.5:
            weak.append(
                {
                    "chunk_id": c.chunk_id,
                    "title": c.title,
                    "reason": "short" if short else "generic",
                    "generic_score": round(g, 3),
                }
            )

    return {
        "chunks_scanned": len(rows),
        "duplicate_snippet_count": len(duplicates),
        "duplicate_examples": duplicates[:10],
        "weak_chunk_count": len(weak),
        "weak_chunks": weak[:25],
        "generic_chunk_count": len(generic),
        "generic_chunks": generic[:25],
        "recommendation": (
            "Deprioritize generic chunks in rerank; merge duplicates; expand thin manifesto chunks."
            if generic or duplicates
            else "Chunk corpus quality acceptable for pilot."
        ),
    }
