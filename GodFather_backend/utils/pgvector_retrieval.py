"""
PGVector retrieval — semantic search for knowledge + brand memory (Phase 14).

Hybrid architecture:
  PGVector  → cosine semantic similarity
  Elasticsearch → BM25 keyword + filters
  RRF       → merge ranked lists (see rerank_knowledge.py)
"""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any, Dict, List, Optional

from django.conf import settings
from django.db.models import F
from django.utils import timezone
from pgvector.django import CosineDistance

logger = logging.getLogger(__name__)

# Agent → memory types for scoped recall
AGENT_MEMORY_TYPES = {
    "manifesto": ("decision", "brand_fact", "persona_note", "manifesto_evolution", "brand_voice"),
    "content": ("preference", "tone", "persona_note", "brand_voice", "emotional_pattern"),
    "strategist": ("decision", "rejected_strategy", "brand_fact", "strategic_priority"),
    "positioning": ("decision", "brand_fact", "rejected_strategy", "competitor_positioning"),
    "trust": ("brand_fact", "emotional_pattern", "audience_psychology"),
    "tone": ("tone", "brand_voice", "emotional_language"),
    "default": tuple(),
}


def pgvector_enabled() -> bool:
    return bool(getattr(settings, "PGVECTOR_ENABLED", True))


def _row_to_chunk(row, distance: float) -> Dict[str, Any]:
    """Normalize PGVector row to ES-compatible chunk dict for RRF."""
    dist = float(distance or 0)
    return {
        "chunk_id": row.chunk_id,
        "text": row.content,
        "metadata": row.metadata or {},
        "document_id": row.document_id,
        "page_number": row.page_number,
        "score": max(0.0, 1.0 - dist),
        "pgvector_distance": dist,
        "source": "pgvector",
    }


def search_similar_chunks(
    query_embedding: List[float],
    top_k: int = 8,
    category: Optional[str] = None,
    agent_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Cosine similarity search over AI knowledge chunks."""
    if not query_embedding or not pgvector_enabled():
        return []

    try:
        from ai_knowledge.models import AIKnowledgeChunk

        if not AIKnowledgeChunk.objects.exists():
            logger.warning("PGVector ai_knowledge_chunk is empty. Run build_ai_knowledge.")
            return []

        qs = AIKnowledgeChunk.objects.annotate(
            distance=CosineDistance("embedding", query_embedding)
        ).order_by("distance")
        if category:
            qs = qs.filter(category=category)
        if agent_id:
            qs = qs.filter(metadata__agent_id=agent_id)

        return [_row_to_chunk(row, row.distance) for row in qs[:top_k]]
    except Exception as e:
        logger.exception("PGVector knowledge search failed: %s", e)
        return []


def _freshness_factor(updated_at) -> float:
    """Exponential decay: newer memories rank higher."""
    if not updated_at:
        return 1.0
    try:
        from django.conf import settings

        half_life = int(getattr(settings, "MEMORY_FRESHNESS_HALF_LIFE_DAYS", 14))
        age_days = max(0.0, (timezone.now() - updated_at).total_seconds() / 86400.0)
        return pow(0.5, age_days / max(half_life, 1))
    except Exception:
        return 1.0


def search_brand_memories(
    session_id: int,
    query_embedding: List[float],
    top_k: int = 5,
    agent_id: Optional[str] = None,
    memory_type: Optional[str] = None,
    min_importance: float = 0.1,
) -> List[Dict[str, Any]]:
    """
    Semantic recall of long-term brand memory for a session.
    Optionally scoped by agent memory types.
    """
    if not query_embedding or not session_id or not pgvector_enabled():
        return []

    try:
        from user_sessions.models import BrandMemory

        qs = BrandMemory.objects.filter(
            session_id=session_id,
            embedding__isnull=False,
            importance_score__gte=min_importance,
        )

        memory_types = AGENT_MEMORY_TYPES.get(agent_id or "default")
        if memory_types:
            qs = qs.filter(memory_type__in=memory_types)
        if memory_type:
            qs = qs.filter(memory_type=memory_type)

        rows = (
            qs.annotate(distance=CosineDistance("embedding", query_embedding))
            .order_by("distance")[: top_k * 2]
        )

        results = []
        memory_ids = []
        for row in rows:
            dist = float(row.distance or 0)
            if getattr(row, "is_pinned", False):
                freshness = 1.0
            else:
                freshness = _freshness_factor(row.updated_at)
            freq_factor = min(1.15, 1.0 + (int(getattr(row, "retrieval_count", 0) or 0) * 0.02))
            effective_importance = float(row.importance_score) * freshness * freq_factor
            blended = dist - (effective_importance * 0.15)
            memory_ids.append(row.pk)
            results.append(
                {
                    "type": row.memory_type,
                    "key": row.key,
                    "content": row.content,
                    "importance_score": row.importance_score,
                    "freshness_factor": round(freshness, 3),
                    "effective_importance": round(effective_importance, 3),
                    "is_pinned": bool(getattr(row, "is_pinned", False)),
                    "agent_id": row.agent_id,
                    "score": max(0.0, 1.0 - dist),
                    "blended_rank": blended,
                }
            )

        if memory_ids:
            try:
                from django.db.models import F
                from user_sessions.models import BrandMemory

                BrandMemory.objects.filter(pk__in=memory_ids).update(
                    retrieval_count=F("retrieval_count") + 1
                )
            except Exception:
                pass

        results.sort(key=lambda x: x["blended_rank"])
        return results[:top_k]
    except Exception as e:
        logger.exception("PGVector brand memory search failed: %s", e)
        return []


def apply_importance_decay(days_half_life: int = 30) -> int:
    """
    Decay importance_score for older memories (Day 4 foundation).
    Returns number of rows updated.
    """
    try:
        from user_sessions.models import BrandMemory

        cutoff = timezone.now() - timedelta(days=days_half_life)
        updated = 0
        for mem in BrandMemory.objects.filter(updated_at__lt=cutoff, importance_score__gt=0.05, is_pinned=False):
            mem.importance_score = max(0.05, float(mem.importance_score) * 0.85)
            mem.save(update_fields=["importance_score", "updated_at"])
            updated += 1
        return updated
    except Exception as e:
        logger.warning("Importance decay skipped: %s", e)
        return 0


def compress_session_memories(session_id: int, max_interactions: int = 20) -> Optional[str]:
    """
    Compress many session memories into one strategic summary (stub for nightly Celery).
    Returns compressed summary text or None.
    """
    try:
        from user_sessions.models import BrandMemory

        recent = list(
            BrandMemory.objects.filter(session_id=session_id)
            .order_by("-updated_at")[:max_interactions]
        )
        if len(recent) < max_interactions:
            return None

        combined = "\n".join(f"- [{m.memory_type}] {m.content[:120]}" for m in recent)
        summary = f"Strategic memory summary ({len(recent)} interactions):\n{combined[:2000]}"
        BrandMemory.objects.update_or_create(
            session_id=session_id,
            key="compressed:strategic_summary",
            defaults={
                "memory_type": "decision",
                "content": summary,
                "importance_score": 0.9,
                "agent_id": "strategist",
            },
        )
        return summary
    except Exception as e:
        logger.warning("Memory compression skipped: %s", e)
        return None
