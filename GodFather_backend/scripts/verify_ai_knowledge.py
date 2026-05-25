"""
Verify AI knowledge indexing without loading full URLconf.
Usage: python scripts/verify_ai_knowledge.py
"""
import json
import os
import sys

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
os.environ.setdefault("DJANGO_SKIP_KNOWLEDGE_AUTO", "1")

import django

django.setup()

from utils.rag_doc_loader import discover_rag_doc_files
from utils.chunk_knowledge import load_and_chunk_all
from utils.ai_knowledge_auto import (
    compute_knowledge_fingerprint,
    elasticsearch_index_exists,
    load_index_state,
    needs_rebuild,
)
from utils.ai_knowledge_config import AI_KNOWLEDGE_INDEX_NAME


def query_es_stats():
    try:
        from elasticsearch import Elasticsearch

        hosts = ["http://localhost:9200"]
        es = Elasticsearch(hosts)
        if not es.indices.exists(index=AI_KNOWLEDGE_INDEX_NAME):
            return {"exists": False}
        count = es.count(index=AI_KNOWLEDGE_INDEX_NAME)["count"]
        sample = es.search(index=AI_KNOWLEDGE_INDEX_NAME, size=1)
        hits = sample.get("hits", {}).get("hits", [])
        first = hits[0]["_source"] if hits else {}
        return {
            "exists": True,
            "doc_count": count,
            "sample_chunk_id": first.get("chunk_id"),
            "sample_source": (first.get("metadata") or {}).get("source"),
            "sample_file": (first.get("metadata") or {}).get("file"),
            "has_embedding": bool(first.get("embedding")),
            "embedding_dims": len(first.get("embedding") or []),
        }
    except Exception as e:
        return {"exists": None, "error": str(e)}


def main():
    print("=" * 60)
    print("AI KNOWLEDGE INDEX VERIFICATION")
    print("=" * 60)

    files = discover_rag_doc_files()
    print(f"\n1. Rag_doc source files: {len(files)}")
    for path, cat in files:
        print(f"   - [{cat}] {path.name}")

    chunks = load_and_chunk_all()
    print(f"\n2. Chunks if built now: {len(chunks)}")
    by_cat = {}
    for c in chunks:
        s = c.get("metadata", {}).get("source", "?")
        by_cat[s] = by_cat.get(s, 0) + 1
    print(f"   By category: {by_cat}")

    fp = compute_knowledge_fingerprint()
    state = load_index_state()
    should, reason = needs_rebuild(force=False)
    print(f"\n3. Fingerprint: {fp[:24]}...")
    print(f"   Stored fingerprint: {(state.get('fingerprint') or 'none')[:24]}")
    print(f"   State status: {state.get('status', 'unknown')}")
    print(f"   Stored chunk_count: {state.get('chunk_count', 0)}")
    print(f"   Last built: {state.get('last_built_at', 'never')}")
    print(f"   Last message: {state.get('last_message', '-')}")
    if state.get("error"):
        print(f"   Last error: {state.get('error')}")
    print(f"   Needs rebuild: {should} ({reason})")

    print(f"\n4. Elasticsearch index '{AI_KNOWLEDGE_INDEX_NAME}':")
    es_ok = elasticsearch_index_exists()
    print(f"   Index exists (django ES client): {es_ok}")
    stats = query_es_stats()
    print(f"   ES stats: {json.dumps(stats, indent=2)}")

    print("\n" + "=" * 60)
    if stats.get("exists") and stats.get("doc_count", 0) > 0 and stats.get("has_embedding"):
        print("RESULT: OK — index has chunks with embeddings")
    elif not es_ok and not stats.get("exists"):
        print("RESULT: NOT INDEXED — run: python manage.py build_ai_knowledge --force --sync")
    else:
        print("RESULT: CHECK — index missing data or embeddings")
    print("=" * 60)


if __name__ == "__main__":
    main()
