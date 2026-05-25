#!/usr/bin/env python
"""
Verify PGVector knowledge chunks + semantic search (Phase 14).

Usage:
  python scripts/verify_pgvector_data.py
  python scripts/verify_pgvector_data.py "What creates brand trust?"
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
os.environ.setdefault("DJANGO_SKIP_KNOWLEDGE_AUTO", "1")

import django

django.setup()

from django.conf import settings
from ai_knowledge.models import AIKnowledgeChunk
from document.utils.embedding_service import EmbeddingService
from utils.pgvector_retrieval import search_similar_chunks


def main():
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "What creates brand trust?"

    print("=" * 60)
    print("PGVector data verification")
    print("=" * 60)
    print(f"EMBEDDING_MODEL (settings): {getattr(settings, 'EMBEDDING_MODEL', 'n/a')}")

    count = AIKnowledgeChunk.objects.count()
    print(f"\n1. AIKnowledgeChunk count: {count}")
    if count == 0:
        print("   -> Run: python manage.py build_ai_knowledge --force")
        return 1

    row = AIKnowledgeChunk.objects.first()
    emb = row.embedding
    if emb is None:
        print("2. embedding: NULL (rebuild required)")
        return 1

    preview = list(emb)[:5] if hasattr(emb, "__iter__") else []
    print(f"2. sample embedding (first 5 dims): {preview}")
    print(f"   title: {row.title[:60] if row.title else row.chunk_id}")
    print(f"   category: {row.category}")

    print(f"\n3. semantic search: {query!r}")
    svc = EmbeddingService()
    print(f"   active deployment: {svc.model}")
    q_emb = svc.generate_embedding(query)
    hits = search_similar_chunks(q_emb, top_k=5)
    if not hits:
        print("   -> no hits (check PGVECTOR_ENABLED and index)")
        return 1

    for i, h in enumerate(hits, 1):
        meta = h.get("metadata") or {}
        title = meta.get("title") or h.get("text", "")[:50]
        score = h.get("score", "n/a")
        dist = h.get("pgvector_distance", "n/a")
        print(f"   [{i}] score={score} distance={dist} | {title}")

    print("\n" + "=" * 60)
    print("PGVector OK")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
