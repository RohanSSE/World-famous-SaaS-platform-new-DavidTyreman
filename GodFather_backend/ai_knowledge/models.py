"""
PGVector-backed AI knowledge chunks — semantic memory store (Phase 14).

Elasticsearch remains the keyword / filter / ranking layer; PGVector is the
semantic source of truth for cosine similarity search.
"""
from django.db import models
from pgvector.django import HnswIndex, VectorField

from utils.ai_knowledge_config import EMBEDDING_DIMS


class AIKnowledgeChunk(models.Model):
    chunk_id = models.IntegerField(unique=True, db_index=True)
    title = models.CharField(max_length=500, blank=True, default="")
    content = models.TextField()
    embedding = VectorField(dimensions=EMBEDDING_DIMS)
    category = models.CharField(max_length=100, db_index=True, default="knowledge")
    metadata = models.JSONField(default=dict, blank=True)
    document_id = models.IntegerField(null=True, blank=True)
    page_number = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ai_knowledge_chunk"
        ordering = ["chunk_id"]
        indexes = [
            HnswIndex(
                name="ai_knowledge_embedding_idx",
                fields=["embedding"],
                m=16,
                ef_construction=64,
                opclasses=["vector_cosine_ops"],
            ),
        ]

    def __str__(self):
        return f"{self.category}:{self.title[:40] or self.chunk_id}"
