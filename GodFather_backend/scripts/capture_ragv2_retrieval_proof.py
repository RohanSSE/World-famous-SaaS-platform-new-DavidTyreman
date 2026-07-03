"""
Capture live RAGv2 retrieval proof from brandgodfather_brand_chunks.

Usage:
  python scripts/capture_ragv2_retrieval_proof.py
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

django.setup()

from elasticsearch_dsl import connections

from brandgodfather.documents import BRANDGODFATHER_NODE_2_ALIAS

PROOF_DATE = datetime.now(timezone.utc).date().isoformat()
REPORT_PATH = REPO_DIR / f"RAGV2_RETRIEVAL_PROOF_{PROOF_DATE}.md"
JSON_PATH = REPO_DIR / f"RAGV2_RETRIEVAL_PROOF_{PROOF_DATE}.json"
INDEX_NAME = "brandgodfather_brand_chunks"

QUERIES = [
    {
        "requirement": "The Constitution",
        "query": "Constitution truth before copy ORB governance vendor interruption contradiction breakthrough seed",
        "expected_source_file": "The_Constitution_Derived_Control.md",
    },
    {
        "requirement": "ORB principles",
        "query": "ORB principles strategic intelligence layer interruption adaptive pressure breakthrough capture memory accountability",
        "expected_source_file": "ORB_Principles_Derived_Control.md",
    },
    {
        "requirement": "Intelligence Framework",
        "query": "Intelligence Framework decision rules answer quality contradiction emotional truth memory conflict output readiness",
        "expected_source_file": "Intelligence_Framework_Derived_Control.md",
    },
    {
        "requirement": "Transformation Journey",
        "query": "Transformation Journey transformation stages surface answer strategic demand breakthrough brand seed complete user journey",
        "expected_source_file": "Transformation_Journey_Derived_Control.md",
    },
    {
        "requirement": "Foundational pillars",
        "query": "Foundational pillars loved brands belief differentiation exclusion felt transformation memory coherence",
        "expected_source_file": "Foundational_Pillars_Derived_Control.md",
    },
]


def compact(text: str, size: int = 260) -> str:
    value = " ".join((text or "").split())
    return value if len(value) <= size else value[: size - 3] + "..."


def run_query(es, query_text: str) -> List[Dict[str, object]]:
    body = {
        "size": 8,
        "query": {
            "multi_match": {
                "query": query_text,
                "fields": ["text^4", "metadata.source_file^5", "chunk_type", "phase"],
                "type": "best_fields",
            }
        },
        "_source": ["chunk_id", "text", "chunk_type", "phase", "question_id", "metadata"],
    }
    resp = es.search(index=INDEX_NAME, body=body)
    hits = []
    for hit in resp.get("hits", {}).get("hits", []):
        source = hit.get("_source", {})
        metadata = source.get("metadata") or {}
        hits.append(
            {
                "score": hit.get("_score"),
                "chunk_id": source.get("chunk_id"),
                "source_file": metadata.get("source_file", "unknown"),
                "source_path": metadata.get("source_path", "unknown"),
                "chunk_type": source.get("chunk_type"),
                "phase": source.get("phase"),
                "question_id": source.get("question_id"),
                "snippet": compact(source.get("text", "")),
            }
        )
    return hits


def build_proof() -> Dict[str, object]:
    es = connections.get_connection(alias=BRANDGODFATHER_NODE_2_ALIAS)
    rows = []
    for item in QUERIES:
        hits = run_query(es, item["query"])
        expected_found = any(
            str(hit.get("source_file", "")).lower() == item["expected_source_file"].lower()
            for hit in hits
        )
        rows.append(
            {
                **item,
                "retrieval_status": "PASS" if expected_found else "FAIL",
                "source_status": "Derived RAGv2 control; original client-authored source still requires intake or validation",
                "hits": hits,
            }
        )
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "index": INDEX_NAME,
        "proof_scope": "Live keyword retrieval against RAGv2 BrandGodFather Elasticsearch chunks.",
        "rows": rows,
    }


def table(headers: List[str], rows: List[List[object]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(str(cell).replace("\n", "<br>") for cell in row) + " |")
    return "\n".join(lines)


def write_markdown(proof: Dict[str, object]) -> None:
    summary_rows = []
    details = []
    for row in proof["rows"]:
        top_files = [f"{hit['source_file']} ({hit['chunk_id']})" for hit in row["hits"][:5]]
        summary_rows.append(
            [
                row["requirement"],
                row["retrieval_status"],
                row["expected_source_file"],
                row["source_status"],
                "<br>".join(top_files) if top_files else "No hits",
            ]
        )
        details.append(f"### {row['requirement']}\n")
        for hit in row["hits"][:5]:
            details.append(
                f"- `{hit['source_file']}` chunk `{hit['chunk_id']}` score `{hit['score']}`: {hit['snippet']}"
            )
        if not row["hits"]:
            details.append("- No RAGv2 hit found.")
        details.append("")

    content = f"""# RAGv2 Retrieval Proof

Date: {PROOF_DATE}  
Index: `{proof['index']}`  
Purpose: Prove RAGv2 retrieval can find Constitution, ORB principles, Intelligence Framework, Transformation Journey, and foundational pillar content from `RAG-docsv2/` ingestion.

## Executive Finding

This proof checks live Elasticsearch retrieval from `brandgodfather_brand_chunks`. Passing rows mean RAGv2 can retrieve the derived methodology controls now. This still does not prove original client-authored methodology files were supplied; those must be added or validated by David before final original-IP completion is claimed.

## Retrieval Summary

{table(["Requirement", "Retrieval Status", "Expected Source", "Source Status", "Top Retrieved Chunks"], summary_rows)}

## Retrieved Evidence

{chr(10).join(details)}
"""
    REPORT_PATH.write_text(content, encoding="utf-8")


def main() -> int:
    proof = build_proof()
    JSON_PATH.write_text(json.dumps(proof, indent=2, ensure_ascii=True), encoding="utf-8")
    write_markdown(proof)
    print(f"Wrote {REPORT_PATH}")
    print(f"Wrote {JSON_PATH}")
    failed = [row["requirement"] for row in proof["rows"] if row["retrieval_status"] != "PASS"]
    if failed:
        print("FAILED retrieval requirements: " + ", ".join(failed))
        return 1
    print("All RAGv2 retrieval requirements passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
