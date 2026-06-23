"""
Capture retrieval proof for client IP methodology terms from ai_knowledge chunks.

Usage:
  python scripts/capture_client_ip_retrieval_proof.py
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List


BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = BACKEND_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
os.environ.setdefault("DJANGO_SKIP_KNOWLEDGE_AUTO", "1")

import django
from django.db.models import Q

django.setup()

from ai_knowledge.models import AIKnowledgeChunk

PROOF_DATE = datetime.now(timezone.utc).date().isoformat()
REPORT_PATH = REPO_DIR / f"CLIENT_IP_RETRIEVAL_PROOF_{PROOF_DATE}.md"
JSON_PATH = REPO_DIR / f"CLIENT_IP_RETRIEVAL_PROOF_{PROOF_DATE}.json"

QUERIES = [
    {
        "requirement": "The Constitution",
        "terms": ["constitution", "truth before copy", "operating law"],
        "expected_control_file": "the-constitution-derived-control.md",
    },
    {
        "requirement": "ORB principles",
        "terms": ["orb principles", "strategic intelligence layer", "interruption is a feature"],
        "expected_control_file": "orb-principles-derived-control.md",
    },
    {
        "requirement": "Transformation Journey",
        "terms": ["transformation journey", "journey stages", "surface answer"],
        "expected_control_file": "transformation-journey-derived-control.md",
    },
    {
        "requirement": "Intelligence Framework",
        "terms": ["intelligence framework", "decision rules", "answer-quality signals"],
        "expected_control_file": "intelligence-framework-derived-control.md",
    },
    {
        "requirement": "Brand Godfather foundational pillars",
        "terms": ["foundational pillars", "loved brands are built on belief", "differentiation requires exclusion"],
        "expected_control_file": "foundational-pillars-derived-control.md",
    },
]


def chunk_file(chunk: AIKnowledgeChunk) -> str:
    metadata = chunk.metadata or {}
    return str(metadata.get("file") or metadata.get("path") or "unknown")


def snippet(text: str, size: int = 240) -> str:
    compact = " ".join((text or "").split())
    if len(compact) <= size:
        return compact
    return compact[: size - 3] + "..."


def search_chunks(terms: List[str]) -> List[Dict[str, object]]:
    query = Q()
    for term in terms:
        query |= Q(content__icontains=term) | Q(title__icontains=term)

    results = []
    seen_files = set()
    for chunk in AIKnowledgeChunk.objects.filter(query).order_by("chunk_id")[:12]:
        file_ref = chunk_file(chunk)
        if file_ref in seen_files and len(results) >= 5:
            continue
        seen_files.add(file_ref)
        results.append(
            {
                "chunk_id": chunk.chunk_id,
                "title": chunk.title,
                "category": chunk.category,
                "file": file_ref,
                "derived_control": "derived-control" in file_ref or "derived" in file_ref,
                "snippet": snippet(chunk.content),
            }
        )
    return results


def build_proof() -> Dict[str, object]:
    rows = []
    for query in QUERIES:
        hits = search_chunks(query["terms"])
        expected_found = any(query["expected_control_file"].lower() in hit["file"].lower() for hit in hits)
        rows.append(
            {
                **query,
                "retrieval_status": "Retrieved derived control" if expected_found else "No expected control retrieved",
                "original_source_status": "Original client-authored source not present in repo evidence",
                "hits": hits,
            }
        )
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "proof_scope": "Keyword retrieval proof from indexed ai_knowledge chunks.",
        "rows": rows,
    }


def table(headers: List[str], rows: List[List[object]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(str(cell).replace("\n", "<br>") for cell in row) + " |")
    return "\n".join(lines)


def write_markdown(proof: Dict[str, object]) -> None:
    rows = proof["rows"]
    summary_rows = []
    detail_sections = []
    for row in rows:
        hit_files = []
        for hit in row["hits"][:5]:
            hit_files.append(f"{hit['file']} (chunk {hit['chunk_id']})")
        summary_rows.append(
            [
                row["requirement"],
                row["retrieval_status"],
                row["original_source_status"],
                row["expected_control_file"],
                "<br>".join(hit_files) if hit_files else "No hits",
            ]
        )
        detail_sections.append(f"### {row['requirement']}\n")
        for hit in row["hits"][:5]:
            detail_sections.append(
                f"- `{hit['file']}` chunk `{hit['chunk_id']}` ({hit['category']}): {hit['snippet']}"
            )
        if not row["hits"]:
            detail_sections.append("- No indexed chunk hit found.")
        detail_sections.append("")

    content = f"""# Client IP Retrieval Proof

Date: {PROOF_DATE}  
Purpose: Prove whether client IP methodology terms retrieve indexed `ai_knowledge` chunks.

## Executive Finding

The proof distinguishes retrieved derived methodology controls from the four original David-shared PDFs already present in the corpus. A retrieved derived control means the ORB can ground prompt behavior now, but final methodology-source completion still requires the separate original methodology files or David validation.

## Retrieval Summary

{table(["Client Requirement", "Retrieval Status", "Original Source Status", "Expected Control File", "Retrieved Chunks"], summary_rows)}

## Retrieved Evidence

{chr(10).join(detail_sections)}
"""
    REPORT_PATH.write_text(content, encoding="utf-8")


def main() -> int:
    proof = build_proof()
    JSON_PATH.write_text(json.dumps(proof, indent=2, ensure_ascii=True), encoding="utf-8")
    write_markdown(proof)
    print(f"Wrote {REPORT_PATH}")
    print(f"Wrote {JSON_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
