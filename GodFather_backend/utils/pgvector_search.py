"""
PGVector semantic search helper.

Usage (Django shell):
    from utils.pgvector_search import search_similar_chunks
    search_similar_chunks("brand trust")
"""
from __future__ import annotations

from typing import List, Union

from document.utils.embedding_service import EmbeddingService
from utils.pgvector_retrieval import search_similar_chunks as _search_by_embedding


def search_similar_chunks(
    query: Union[str, List[float]],
    top_k: int = 8,
    category: str | None = None,
) -> List[dict]:
    """
    Search ai_knowledge_chunk by query text or precomputed embedding vector.
    """
    if isinstance(query, str):
        embedding = EmbeddingService().generate_embedding(query)
    else:
        embedding = query
    return _search_by_embedding(embedding, top_k=top_k, category=category)
