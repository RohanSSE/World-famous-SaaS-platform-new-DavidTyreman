"""Build structured reasoning trace for AIRequestTrace debugging."""
from __future__ import annotations

from typing import Any, Dict, List, Optional


def build_reasoning_trace(
    planner: Optional[Dict[str, Any]] = None,
    chunks: Optional[List[Dict[str, Any]]] = None,
    sources: Optional[List[Dict[str, Any]]] = None,
    memory_snippets: Optional[List[str]] = None,
    verification: Optional[Dict[str, Any]] = None,
    rejected_chunks: Optional[List[Dict[str, Any]]] = None,
    pipeline: str = "",
) -> Dict[str, Any]:
    planner = planner or {}
    chunks = chunks or []
    sources = sources or []

    selected = []
    for c in chunks[:8]:
        meta = c.get("metadata") or {}
        selected.append(
            {
                "title": meta.get("title", ""),
                "category": meta.get("category", ""),
                "file": meta.get("file", ""),
                "strategic_tags": meta.get("strategic_tags") or c.get("strategic_tags", []),
                "hybrid_score": c.get("hybrid_score"),
                "generic_penalty": bool(c.get("generic_chunk_penalty")),
            }
        )

    rejected = rejected_chunks or []
    if not rejected and chunks:
        first = chunks[0] if chunks else {}
        rejected = first.get("_diversity_rejected") or []

    return {
        "planner_agents": planner.get("selected_agents") or [],
        "primary_agent": planner.get("primary_agent"),
        "selected_chunks": selected,
        "rejected_chunks": rejected[:10],
        "memory_used": (memory_snippets or [])[:6],
        "verification_flags": {
            "unsupported_count": (verification or {}).get("unsupported_count", 0),
            "hallucination_flags": (verification or {}).get("hallucination_flags", False),
        },
        "pipeline": pipeline,
        "source_count": len(sources),
    }
