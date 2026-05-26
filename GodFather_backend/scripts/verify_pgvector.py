#!/usr/bin/env python
"""
Verify PGVector setup (Phase 14).

Usage:
  python scripts/verify_pgvector.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

import django

django.setup()

from django.db import connection


def main():
    print("=" * 60)
    print("PGVector verification")
    print("=" * 60)

    with connection.cursor() as cur:
        cur.execute("SELECT extname FROM pg_extension WHERE extname = 'vector';")
        ext = cur.fetchone()
        print(f"1. vector extension: {'OK' if ext else 'MISSING — run migrate'}")

        cur.execute(
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'ai_knowledge_chunk');"
        )
        table_ok = cur.fetchone()[0]
        print(f"2. ai_knowledge_chunk table: {'OK' if table_ok else 'MISSING'}")

        if table_ok:
            cur.execute("SELECT COUNT(*) FROM ai_knowledge_chunk;")
            count = cur.fetchone()[0]
            print(f"3. chunk count: {count}")
            if count:
                cur.execute(
                    "SELECT chunk_id, left(embedding::text, 40) FROM ai_knowledge_chunk LIMIT 1;"
                )
                row = cur.fetchone()
                print(f"4. sample embedding prefix: {row[1] if row else 'empty'}...")
            else:
                print("4. sample embedding: (empty — run: python manage.py build_ai_knowledge)")

        cur.execute(
            "SELECT EXISTS (SELECT 1 FROM information_schema.columns "
            "WHERE table_name = 'user_sessions_brandmemory' AND column_name = 'embedding');"
        )
        bm_ok = cur.fetchone()[0]
        print(f"5. brand memory embedding column: {'OK' if bm_ok else 'MISSING'}")

    try:
        from utils.pgvector_store import pgvector_knowledge_count

        print(f"6. Django PGVector count: {pgvector_knowledge_count()}")
    except Exception as e:
        print(f"6. Django PGVector count: ERROR — {e}")

    print("=" * 60)
    print("Done. ES is still required for keyword search (hybrid architecture).")
    print("=" * 60)


if __name__ == "__main__":
    main()
