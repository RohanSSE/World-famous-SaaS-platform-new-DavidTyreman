"""Test RAG retrieval for sample branding questions."""
import os
import sys

import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
django.setup()

from user_sessions.services.rag_service import retrieve_knowledge_chunks  # noqa: E402
from utils.retrieve_ai_knowledge import format_knowledge_context  # noqa: E402

QUERIES = [
    "How can a brand create emotional connection?",
    "How to differentiate from competitors?",
    "What creates brand trust?",
    "How should manifesto positioning work?",
]


def main():
    out = sys.stdout.buffer
    for q in QUERIES:
        out.write(b"\nQUESTION: " + q.encode("utf-8") + b"\n")
        out.write(b"=" * 50 + b"\n")

        chunks = retrieve_knowledge_chunks(q, search_type="hybrid", use_rerank=True)
        if not chunks:
            out.write(b"  (no results - check ES + build_ai_knowledge)\n")
            continue

        out.write(f"  hits: {len(chunks)}\n".encode())
        for i, c in enumerate(chunks[:3], 1):
            meta = c.get("metadata") or {}
            title = meta.get("title", "?")
            cat = meta.get("category", "?")
            score = c.get("hybrid_score", c.get("score", c.get("rrf_score", "n/a")))
            vs = c.get("vector_score", "-")
            ks = c.get("keyword_score", "-")
            gs = c.get("graph_score", "-")
            out.write(
                f"  [{i}] hybrid={score} v={vs} k={ks} g={gs} | {cat} | {title[:50]}\n".encode(
                    "utf-8", errors="replace"
                )
            )

        context = format_knowledge_context(chunks)
        preview = context[:1200] if context else "(empty context)"
        out.write(b"\nCONTEXT PREVIEW:\n")
        out.write(preview.encode("utf-8", errors="replace"))
        out.write(b"\n" + b"-" * 80 + b"\n")


if __name__ == "__main__":
    main()
