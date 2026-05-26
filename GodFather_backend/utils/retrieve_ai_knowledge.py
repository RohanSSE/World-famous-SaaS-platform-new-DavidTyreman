"""
Retrieve relevant AI knowledge chunks for RAG (prompt context).

Phase 14 hybrid: PGVector semantic + Elasticsearch keyword + RRF reranking.
Elasticsearch is NOT removed — it handles keyword search and filters.
"""
import logging
from typing import List, Optional

from django.conf import settings

from .ai_knowledge_config import AI_KNOWLEDGE_INDEX_NAME, AI_KNOWLEDGE_TOP_K
from .rerank_knowledge import rerank_knowledge_chunks

logger = logging.getLogger(__name__)


def _use_pgvector_hybrid() -> bool:
    return bool(getattr(settings, "PGVECTOR_ENABLED", True))


def retrieve_ai_knowledge(
    query_text: str,
    query_embedding: Optional[List[float]] = None,
    top_k: int = AI_KNOWLEDGE_TOP_K,
    search_type: str = "hybrid",
    embedding_service=None,
    es_service=None,
) -> List[dict]:
    """
    Retrieve top-k relevant chunks from AI knowledge.
    Hybrid (default): PGVector cosine + ES keyword + RRF when PGVECTOR_ENABLED.
    Fallback: ES vector/keyword/hybrid when PGVector unavailable.
    """
    if es_service is None:
        from document.utils.elasticsearch_service import ElasticsearchService
        es_service = ElasticsearchService()

    try:
        from .ai_knowledge_auto import ensure_index_current

        ensure_index_current(async_build=True, force=False)
    except Exception as e:
        logger.debug("AI knowledge auto-ensure skipped: %s", e)

    pgvector_ok = _use_pgvector_hybrid()
    if pgvector_ok:
        try:
            from .pgvector_store import pgvector_knowledge_count

            pgvector_ok = pgvector_knowledge_count() > 0
        except Exception:
            pgvector_ok = False

    es_index_ok = es_service.es.indices.exists(index=AI_KNOWLEDGE_INDEX_NAME)
    if not es_index_ok and not pgvector_ok:
        logger.warning(
            "No AI knowledge in ES or PGVector. Run: python manage.py build_ai_knowledge"
        )
        return []

    if search_type in ("vector", "hybrid") and query_embedding is None and embedding_service:
        try:
            query_embedding = embedding_service.generate_embedding(query_text)
        except Exception as e:
            logger.warning("Could not generate embedding for AI knowledge retrieval: %s", e)
            query_embedding = None
            if search_type == "vector":
                search_type = "keyword"

    min_score = float(getattr(settings, "RAG_MIN_SCORE_THRESHOLD", 0.01))

    try:
        # Phase 14: PGVector semantic + ES keyword + RRF
        if search_type == "hybrid" and query_embedding and pgvector_ok:
            from .pgvector_retrieval import search_similar_chunks

            vector_results = search_similar_chunks(
                query_embedding, top_k=top_k * 2
            )
            keyword_results = []
            if es_index_ok:
                keyword_results = es_service.keyword_search(
                    AI_KNOWLEDGE_INDEX_NAME, query_text, top_k=top_k * 2
                )
            if vector_results or keyword_results:
                from user_sessions.services.rag_intelligence import detect_query_intent
                from utils.knowledge_graph import get_related_concepts

                return rerank_knowledge_chunks(
                    query_text,
                    vector_results,
                    keyword_results,
                    top_k=top_k,
                    min_score=min_score,
                    graph_concepts=get_related_concepts(query_text),
                    intent=detect_query_intent(query_text),
                )

        if search_type == "vector" and query_embedding and pgvector_ok:
            from .pgvector_retrieval import search_similar_chunks

            return search_similar_chunks(query_embedding, top_k=top_k)

        if search_type == "keyword" and es_index_ok:
            return es_service.keyword_search(
                AI_KNOWLEDGE_INDEX_NAME, query_text, top_k=top_k
            )

        if search_type == "vector" and query_embedding and es_index_ok:
            return es_service.vector_search(
                AI_KNOWLEDGE_INDEX_NAME, query_embedding, top_k=top_k
            )

        if search_type == "hybrid" and query_embedding and es_index_ok:
            return es_service.hybrid_search(
                AI_KNOWLEDGE_INDEX_NAME,
                query_text,
                query_embedding,
                top_k=top_k,
                vector_weight=0.7,
            )

        if es_index_ok:
            return es_service.keyword_search(
                AI_KNOWLEDGE_INDEX_NAME, query_text, top_k=top_k
            )
    except Exception as e:
        logger.exception("AI knowledge search failed: %s", e)
        return []

    return []


def format_knowledge_context(chunks: List[dict], max_chars: int = 6000) -> str:
    """
    Format retrieved chunks into a single context string for the system prompt.
    Truncates if total length exceeds max_chars.
    """
    if not chunks:
        return ""
    parts = []
    total = 0
    for i, c in enumerate(chunks, 1):
        meta = c.get("metadata", {}) or {}
        title = meta.get("title", "").strip()
        content = meta.get("content", "").strip() or c.get("text", "").strip()
        category = meta.get("category") or meta.get("source", "knowledge")
        file_ref = meta.get("file", "")
        label = f"{category}/{file_ref}" if file_ref else category
        if title and title.lower() not in ("overview", "general", "untitled", "introduction"):
            block = f"[{label} | {title}]\n{content}"
        else:
            block = f"[{label}]\n{content}"
        if total + len(block) > max_chars:
            remaining = max_chars - total - 50
            if remaining > 100:
                block = block[:remaining] + "..."
            parts.append(block)
            break
        parts.append(block)
        total += len(block)
    return "\n\n".join(parts)
