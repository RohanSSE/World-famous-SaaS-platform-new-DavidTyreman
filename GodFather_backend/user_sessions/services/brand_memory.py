"""
Long-term brand memory with prioritized retrieval layers (Phase 15).
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from django.conf import settings

logger = logging.getLogger(__name__)

PINNED_MEMORY_TYPES = (
    "manifesto_evolution",
    "strategic_priority",
    "founder_personality",
    "decision",
)

MEMORY_TYPES = (
    "brand_fact",
    "preference",
    "tone",
    "decision",
    "rejected_strategy",
    "persona_note",
    "manifesto_evolution",
    "emotional_language",
    "competitor_mention",
    "strategic_priority",
    "brand_voice",
    "emotional_pattern",
    "competitor_positioning",
    "founder_personality",
    "audience_psychology",
)

# Retrieval layer order (highest priority first)
MEMORY_LAYER_ORDER = (
    ("strategic", ("strategic_priority", "decision", "rejected_strategy", "competitor_positioning")),
    ("emotional", ("emotional_pattern", "emotional_language", "tone", "brand_voice")),
    ("session", ("brand_fact", "preference", "persona_note", "manifesto_evolution", "founder_personality", "audience_psychology", "competitor_mention")),
)


def _generate_memory_embedding(content: str, embedding_service=None) -> Optional[List[float]]:
    if not content or not getattr(settings, "PGVECTOR_ENABLED", True):
        return None
    try:
        if embedding_service is None:
            from document.utils.embedding_service import EmbeddingService

            embedding_service = EmbeddingService()
        return embedding_service.generate_embedding(content[:8000])
    except Exception as e:
        logger.debug("Memory embedding skipped: %s", e)
        return None


def get_session_memory(session_id: int, limit: int = 20, memory_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    try:
        from user_sessions.models import BrandMemory

        qs = BrandMemory.objects.filter(session_id=session_id)
        if memory_types:
            qs = qs.filter(memory_type__in=memory_types)
        rows = qs.order_by("-importance_score", "-updated_at")[:limit]
        return [
            {
                "type": r.memory_type,
                "key": r.key,
                "content": r.content,
                "value": getattr(r, "value", None) or {},
                "confidence": float(getattr(r, "confidence", r.importance_score)),
                "importance_score": r.importance_score,
                "agent_id": r.agent_id,
            }
            for r in rows
        ]
    except Exception as e:
        logger.debug("Brand memory fetch skipped: %s", e)
        return []


def build_layered_memory_context(
    session_id: int,
    query: str,
    agent_id: Optional[str] = None,
    embedding_service=None,
    limit_per_layer: int = 4,
) -> str:
    """
    Priority-ordered memory for RAG:
    strategic_memory → emotional_memory → session_memory
    """
    if not session_id:
        return ""

    semantic_hits: List[Dict[str, Any]] = []
    if query and getattr(settings, "PGVECTOR_ENABLED", True):
        try:
            emb = _generate_memory_embedding(query, embedding_service)
            if emb:
                from utils.pgvector_retrieval import search_brand_memories

                semantic_hits = search_brand_memories(
                    session_id, emb, top_k=limit_per_layer * 3, agent_id=agent_id
                )
        except Exception as e:
            logger.debug("Semantic memory layer skipped: %s", e)

    sections: List[str] = []
    used_keys = set()

    for layer_name, type_group in MEMORY_LAYER_ORDER:
        layer_lines: List[str] = []
        for hit in semantic_hits:
            hit_key = hit.get("key") or f"{hit.get('type')}:{hit.get('content', '')[:40]}"
            if hit.get("type") in type_group and hit_key not in used_keys:
                layer_lines.append(f"- [{hit['type']}] {hit['content'][:280]}")
                used_keys.add(hit_key)
        if len(layer_lines) < limit_per_layer:
            for mem in get_session_memory(session_id, limit=limit_per_layer * 2, memory_types=list(type_group)):
                if mem["key"] not in used_keys:
                    layer_lines.append(f"- [{mem['type']}] {mem['content'][:280]}")
                    used_keys.add(mem["key"])
                if len(layer_lines) >= limit_per_layer:
                    break
        if layer_lines:
            sections.append(f"### {layer_name.replace('_', ' ').title()} memory\n" + "\n".join(layer_lines[:limit_per_layer]))

    if not sections:
        return ""
    return "--- Brand memory (priority layers) ---\n" + "\n\n".join(sections) + "\n--- End brand memory ---"


def format_memory_context_block(
    session_id: int,
    query: str,
    agent_id: Optional[str] = None,
    embedding_service=None,
    limit: int = 6,
) -> str:
    return build_layered_memory_context(session_id, query, agent_id, embedding_service, limit_per_layer=limit)


def memory_snippets_for_retrieval(
    session_id: Optional[int],
    query: Optional[str] = None,
    agent_id: Optional[str] = None,
    embedding_service=None,
    limit: int = 5,
) -> List[str]:
    limit = min(limit, int(getattr(settings, "MAX_MEMORY_SNIPPETS", 8)))
    if not session_id:
        return []
    block = build_layered_memory_context(session_id, query or "", agent_id, embedding_service, limit_per_layer=2)
    if not block:
        return []
    return [line for line in block.split("\n") if line.strip().startswith("-")][:limit]


def upsert_memory(
    session_id: int,
    memory_type: str,
    key: str,
    content: str,
    weight: float = 1.0,
    importance_score: Optional[float] = None,
    confidence: Optional[float] = None,
    value: Optional[Dict[str, Any]] = None,
    agent_id: str = "",
    user=None,
    embedding_service=None,
) -> None:
    try:
        from user_sessions.models import BrandMemory

        imp = importance_score if importance_score is not None else min(1.0, max(0.1, weight * 0.5))
        conf = confidence if confidence is not None else imp
        embedding = _generate_memory_embedding(content, embedding_service)
        defaults = {
            "memory_type": memory_type,
            "content": content,
            "weight": weight,
            "importance_score": imp,
            "agent_id": agent_id or "",
            "embedding": embedding,
            "created_by": user,
            "confidence": conf,
            "value": value or {},
            "is_pinned": memory_type in PINNED_MEMORY_TYPES or (value or {}).get("pinned", False),
        }
        BrandMemory.objects.update_or_create(session_id=session_id, key=key, defaults=defaults)
    except Exception as e:
        logger.warning("Brand memory upsert failed: %s", e)


def learn_from_rag_interaction(
    session_id: Optional[int],
    query: str,
    answer: str,
    sources: List[Dict],
    user=None,
    agent_id: str = "strategist",
    embedding_service=None,
) -> None:
    if not session_id or not answer:
        return
    q = query[:100]
    if sources and len(sources) >= 2:
        upsert_memory(
            session_id,
            "strategic_priority",
            f"topic:{q[:60]}",
            f"Explored: {q}. Strategic direction reinforced.",
            importance_score=0.65,
            value={"query": q, "source_count": len(sources)},
            agent_id=agent_id,
            user=user,
            embedding_service=embedding_service,
        )
    if any(w in query.lower() for w in ("tone", "voice", "sound")):
        upsert_memory(
            session_id,
            "brand_voice",
            f"tone_pref:{q[:40]}",
            f"Tone discussion: {answer[:200]}",
            importance_score=0.75,
            agent_id="tone",
            user=user,
            embedding_service=embedding_service,
        )
    if any(w in query.lower() for w in ("reject", "not", "avoid", "won't")):
        upsert_memory(
            session_id,
            "rejected_strategy",
            f"rejected:{q[:50]}",
            f"Rejected angle: {answer[:180]}",
            importance_score=0.85,
            agent_id=agent_id,
            user=user,
            embedding_service=embedding_service,
        )
