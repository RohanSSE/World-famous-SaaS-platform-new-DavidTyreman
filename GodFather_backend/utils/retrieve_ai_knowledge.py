"""
Retrieve relevant AI knowledge chunks for RAG (prompt context).
Uses the ai_knowledge Elasticsearch index and optional hybrid search.
"""
import logging
from typing import List, Optional

from .ai_knowledge_config import AI_KNOWLEDGE_INDEX_NAME, AI_KNOWLEDGE_TOP_K

logger = logging.getLogger(__name__)


def retrieve_ai_knowledge(
    query_text: str,
    query_embedding: Optional[List[float]] = None,
    top_k: int = AI_KNOWLEDGE_TOP_K,
    search_type: str = "hybrid",
    embedding_service=None,
    es_service=None,
) -> List[dict]:
    """
    Retrieve top-k relevant chunks from the AI knowledge index.
    - query_text: user question or current topic (used for keyword + optional vector).
    - query_embedding: if provided and search_type in ('vector','hybrid'), used for vector search.
    - top_k: number of chunks to return.
    - search_type: 'vector', 'keyword', or 'hybrid'.
    - embedding_service: used to generate query embedding if not provided and vector/hybrid.
    - es_service: ElasticsearchService instance.
    Returns list of chunk dicts with 'text', 'metadata', etc.
    """
    if es_service is None:
        from document.utils.elasticsearch_service import ElasticsearchService
        es_service = ElasticsearchService()

    if not es_service.es.indices.exists(index=AI_KNOWLEDGE_INDEX_NAME):
        logger.warning("AI knowledge index %s does not exist. Run build_ai_knowledge.", AI_KNOWLEDGE_INDEX_NAME)
        return []

    if search_type in ("vector", "hybrid") and query_embedding is None and embedding_service:
        try:
            query_embedding = embedding_service.generate_embedding(query_text)
        except Exception as e:
            logger.warning("Could not generate embedding for AI knowledge retrieval: %s", e)
            query_embedding = None
            if search_type == "vector":
                search_type = "keyword"

    try:
        if search_type == "keyword":
            results = es_service.keyword_search(
                AI_KNOWLEDGE_INDEX_NAME, query_text, top_k=top_k
            )
        elif search_type == "vector" and query_embedding:
            results = es_service.vector_search(
                AI_KNOWLEDGE_INDEX_NAME, query_embedding, top_k=top_k
            )
        elif search_type == "hybrid" and query_embedding:
            results = es_service.hybrid_search(
                AI_KNOWLEDGE_INDEX_NAME,
                query_text,
                query_embedding,
                top_k=top_k,
                vector_weight=0.7,
            )
        else:
            results = es_service.keyword_search(
                AI_KNOWLEDGE_INDEX_NAME, query_text, top_k=top_k
            )
    except Exception as e:
        logger.exception("AI knowledge search failed: %s", e)
        return []

    return results


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
        text = c.get("text", "").strip()
        meta = c.get("metadata", {})
        source = meta.get("source", "knowledge")
        block = f"[{source}] {text}"
        if total + len(block) > max_chars:
            remaining = max_chars - total - 50
            if remaining > 100:
                block = block[:remaining] + "..."
            parts.append(block)
            break
        parts.append(block)
        total += len(block)
    return "\n\n".join(parts)
