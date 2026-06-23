"""
Generate a client IP AI-analysis record from the indexed ai_knowledge corpus.

Usage:
  python scripts/generate_client_ip_analysis_record.py
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter
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

from ai_knowledge.models import AIKnowledgeChunk

REPORT_DATE = datetime.now(timezone.utc).date().isoformat()
REPORT_PATH = REPO_DIR / f"CLIENT_IP_AI_ANALYSIS_RECORD_{REPORT_DATE}.md"
JSON_PATH = REPO_DIR / f"CLIENT_IP_AI_ANALYSIS_RECORD_{REPORT_DATE}.json"

DOCUMENTS = [
    {
        "name": "Original source documents shared by David",
        "paths": ["World Famous", "Dumbass", "Vessel & Craft", "BrandGodFather_Logic_Schema"],
        "source_status": "Indexed original source asset evidence - 4 PDFs present",
        "analysis": "The four David-shared PDFs across Rag_docs/ and RAG-docsv2/ are indexed and available for strategic grounding.",
        "principles": "Loved-brand positioning, category differentiation, customer emotion, specificity, and brand behavior proof.",
        "orb_translation": "Use original source material as support for specificity, transformation, breakthrough criteria, and non-generic brand strategy.",
    },
    {
        "name": "The Constitution",
        "paths": ["the-constitution-derived-control.md"],
        "source_status": "Derived control indexed; original client-authored source still required",
        "analysis": "Operational law for truth-before-copy, challenge-first behavior, contradiction blocking, and breakthrough memory.",
        "principles": "Truth before copy, belief before utility, specificity before abstraction, behavior as proof.",
        "orb_translation": "Prompt governance section requires ORB to challenge weak answers instead of rewriting them.",
    },
    {
        "name": "ORB principles",
        "paths": ["orb-principles-derived-control.md"],
        "source_status": "Derived control indexed; original client-authored source still required",
        "analysis": "Defines ORB as a strategic intelligence layer with interruption, adaptive pressure, memory, and breakthrough capture.",
        "principles": "Interruption is a feature, pressure adapts to resistance, memory creates accountability.",
        "orb_translation": "Prompt governance and regression tests protect challenge-first, contradiction-safe, breakthrough-aware behavior.",
    },
    {
        "name": "Transformation Journey",
        "paths": ["transformation-journey-derived-control.md"],
        "source_status": "Derived control indexed; original client-authored source still required",
        "analysis": "Maps the user journey from surface answer through interruption, strategic demand, resolution, breakthrough, and output.",
        "principles": "Transformation must be felt as identity, confidence, courage, clarity, trust, or behavior change.",
        "orb_translation": "ORB should pass only when an answer can carry forward into memory and non-generic outputs.",
    },
    {
        "name": "Intelligence Framework",
        "paths": ["intelligence-framework-derived-control.md"],
        "source_status": "Derived control indexed; original client-authored source still required",
        "analysis": "Defines answer-quality signals and decision rules for pass, reject, challenge, memory, and escalation.",
        "principles": "Read vendor language, specificity, strategic tension, emotional truth, memory conflict, resistance, and output readiness.",
        "orb_translation": "Prompt layer classifies answers and enforces gates, while API exposes status and metadata.",
    },
    {
        "name": "Brand Godfather foundational pillars",
        "paths": ["foundational-pillars-derived-control.md"],
        "source_status": "Derived control indexed; original client-authored source still required",
        "analysis": "Captures belief, exclusion, felt transformation, consequential language, and memory coherence as pillars.",
        "principles": "Loved brands are built on belief; differentiation requires exclusion; memory makes strategy coherent.",
        "orb_translation": "ORB must challenge, remember, and generate from captured truth rather than decorating weak input.",
    },
]


def chunk_counts_by_file() -> Counter:
    counts: Counter = Counter()
    for chunk in AIKnowledgeChunk.objects.all().iterator():
        metadata = chunk.metadata or {}
        file_ref = str(metadata.get("file") or metadata.get("path") or "unknown")
        counts[file_ref] += 1
    return counts


def matching_count(counts: Counter, patterns: List[str]) -> int:
    total = 0
    for file_ref, count in counts.items():
        normalized = file_ref.lower()
        if any(pattern.lower() in normalized for pattern in patterns):
            total += count
    return total


def build_record() -> Dict[str, object]:
    counts = chunk_counts_by_file()
    rows = []
    for item in DOCUMENTS:
        rows.append(
            {
                **item,
                "indexed_chunk_count": matching_count(counts, item["paths"]),
                "owner_studied_by": "TBD - requires real team assignment before client meeting",
                "human_validation_status": "Pending human owner sign-off",
            }
        )
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "record_scope": "Evidence record for available indexed corpus plus derived methodology controls.",
        "rows": rows,
    }


def table(headers: List[str], rows: List[List[object]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(str(cell).replace("\n", "<br>") for cell in row) + " |")
    return "\n".join(lines)


def write_markdown(record: Dict[str, object]) -> None:
    rows = record["rows"]
    content = f"""# Client IP AI Analysis Record

Date: {REPORT_DATE}  
Purpose: Show what client IP/source material has been analyzed, what is indexed, what has been translated into ORB behavior, and where human ownership is still missing.

## Executive Finding

AI analysis evidence now exists for the four original David-shared PDFs currently present in `Rag_docs/` and `RAG-docsv2/`, plus the derived methodology controls. This does not prove the later Constitution, ORB principles, Transformation Journey, Intelligence Framework, or foundational pillar source files were separately provided as original methodology documents. Those methodology originals still require intake or David validation and owner sign-off.

## Analysis Ledger

{table([
        "Document / Asset",
        "Source Status",
        "Indexed Chunks",
        "Owner / Studied By",
        "AI Analysis Summary",
        "Extracted Principles",
        "ORB Behavior Translation",
        "Human Validation",
    ], [[
        row["name"],
        row["source_status"],
        row["indexed_chunk_count"],
        row["owner_studied_by"],
        row["analysis"],
        row["principles"],
        row["orb_translation"],
        row["human_validation_status"],
    ] for row in rows])}

## Client-Safe Statement

We can say the system now has indexed evidence for the four David-shared original PDFs, plus derived methodology controls that have been translated into ORB prompt governance. We cannot say the team has fully studied separate original Constitution, ORB principles, Transformation Journey, Intelligence Framework, or foundational pillars documents until those methodology originals are supplied or David validates the controls and named owners sign this ledger.
"""
    REPORT_PATH.write_text(content, encoding="utf-8")


def main() -> int:
    record = build_record()
    JSON_PATH.write_text(json.dumps(record, indent=2, ensure_ascii=True), encoding="utf-8")
    write_markdown(record)
    print(f"Wrote {REPORT_PATH}")
    print(f"Wrote {JSON_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
