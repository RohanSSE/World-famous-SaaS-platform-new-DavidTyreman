"""
PGVector storage helpers — dual-write companion to Elasticsearch (Phase 14).
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)


def pgvector_knowledge_count() -> int:
    try:
        from ai_knowledge.models import AIKnowledgeChunk

        return AIKnowledgeChunk.objects.count()
    except Exception as e:
        logger.debug("PGVector count skipped: %s", e)
        return 0


def bulk_upsert_knowledge_chunks(chunks: List[Dict[str, Any]]) -> Tuple[int, str]:
    """
    Full rebuild of PGVector knowledge table (mirrors ES index recreate).
    Returns (count, message).
    """
    from ai_knowledge.models import AIKnowledgeChunk

    if not chunks:
        return 0, "No chunks to store in PGVector."

    AIKnowledgeChunk.objects.all().delete()

    rows = []
    for c in chunks:
        meta = c.get("metadata") or {}
        embedding = c.get("embedding")
        if not embedding:
            continue
        rows.append(
            AIKnowledgeChunk(
                chunk_id=int(c["chunk_id"]),
                title=(meta.get("title") or "")[:500],
                content=c.get("text") or meta.get("content") or "",
                embedding=embedding,
                category=meta.get("category") or meta.get("source") or "knowledge",
                metadata=meta,
                document_id=c.get("document_id"),
                page_number=c.get("page_number"),
            )
        )

    if not rows:
        return 0, "No embeddings available for PGVector storage."

    AIKnowledgeChunk.objects.bulk_create(rows, batch_size=100)
    msg = f"Stored {len(rows)} chunks in PGVector (ai_knowledge_chunk)."
    logger.info(msg)
    return len(rows), msg
