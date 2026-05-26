"""
Build (or rebuild) the AI knowledge vector index from utils knowledge files.
Chunks text, generates embeddings, and indexes into Elasticsearch.
Call from management command: python manage.py build_ai_knowledge
"""
import logging
from django.conf import settings

from .ai_knowledge_config import AI_KNOWLEDGE_INDEX_NAME, EMBEDDING_DIMS
from .chunk_knowledge import load_and_chunk_all

logger = logging.getLogger(__name__)


def run_build():
    """Load knowledge files, chunk, embed, and index. Returns (success, message)."""
    from document.utils.elasticsearch_service import ElasticsearchService
    from document.utils.embedding_service import EmbeddingService

    # 1. Chunk
    chunks = load_and_chunk_all()
    if not chunks:
        return False, (
            "No chunks produced. Add .txt/.md/.pdf files under Rag_doc/<category>/ "
            "(branding, manifesto, psychology, strategy, positioning, sales, marketing)."
        )

    # 2. Embeddings
    embedding_service = EmbeddingService()
    texts = [c["text"] for c in chunks]
    try:
        embeddings = embedding_service.generate_embeddings_batch(texts, batch_size=50)
    except Exception as e:
        logger.exception("Embedding failed")
        return False, f"Embedding failed: {e}"

    for c, emb in zip(chunks, embeddings):
        c["embedding"] = emb

    # 3. ES index (same mapping as document index: document_id, chunk_id, text, embedding, page_number, metadata)
    es = ElasticsearchService()
    mapping = {
        "mappings": {
            "properties": {
                "document_id": {"type": "integer"},
                "chunk_id": {"type": "integer"},
                "text": {"type": "text", "analyzer": "standard"},
                "embedding": {
                    "type": "dense_vector",
                    "dims": EMBEDDING_DIMS,
                    "index": True,
                    "similarity": "cosine",
                },
                "page_number": {"type": "integer"},
                "metadata": {"type": "object"},
            }
        },
        "settings": {"number_of_shards": 1, "number_of_replicas": 0},
    }
    try:
        if es._index_exists(AI_KNOWLEDGE_INDEX_NAME):
            es.es.indices.delete(index=AI_KNOWLEDGE_INDEX_NAME)
        es.es.indices.create(
            index=AI_KNOWLEDGE_INDEX_NAME,
            mappings=mapping["mappings"],
            settings=mapping["settings"],
        )
    except Exception as e:
        logger.exception("Index create failed")
        return False, f"Index create failed: {e}"

    # 4. Bulk index
    from elasticsearch.helpers import bulk
    actions = [
        {"_index": AI_KNOWLEDGE_INDEX_NAME, "_id": str(c["chunk_id"]), "_source": c}
        for c in chunks
    ]
    try:
        success, failed = bulk(es.es, actions, raise_on_error=False)
        logger.info("Indexed %s chunks, %s failed", success, len(failed))
    except Exception as e:
        logger.exception("Bulk index failed")
        return False, f"Bulk index failed: {e}"

    chunk_count = len(chunks)
    pg_msg = ""
    if getattr(settings, "PGVECTOR_ENABLED", True):
        try:
            from .pgvector_store import bulk_upsert_knowledge_chunks

            pg_count, pg_msg = bulk_upsert_knowledge_chunks(chunks)
            logger.info("PGVector dual-write: %s", pg_msg)
        except Exception as e:
            logger.exception("PGVector dual-write failed (ES index still built): %s", e)
            pg_msg = f" PGVector write failed: {e}"

    return True, (
        f"Indexed {chunk_count} AI knowledge chunks into {AI_KNOWLEDGE_INDEX_NAME}."
        + (f" {pg_msg}" if pg_msg else "")
    )
