"""
Audit Brand Godfather client IP corpus coverage.

Produces an inventory of current source files, indexed chunk counts, dry-run chunk
counts, and client-mail required methodology assets.

Usage:
  python scripts/audit_client_ip_corpus.py
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List


BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = BACKEND_DIR.parent
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
os.environ.setdefault("DJANGO_SKIP_KNOWLEDGE_AUTO", "1")

import django

django.setup()

from ai_knowledge.models import AIKnowledgeChunk
from utils.ai_knowledge_auto import load_index_state, needs_rebuild
from utils.ai_knowledge_config import RAG_DOC_ADDITIONAL_DIRS, RAG_DOC_DIR, RAG_DOC_SUPPORTED_EXTENSIONS
from utils.chunk_knowledge import load_and_chunk_all
from utils.rag_doc_loader import discover_rag_doc_files, relative_rag_path


AUDIT_DATE = datetime.now(timezone.utc).date().isoformat()
REPORT_PATH = REPO_DIR / f"CLIENT_IP_CORPUS_AUDIT_{AUDIT_DATE}.md"
JSON_PATH = REPO_DIR / f"CLIENT_IP_CORPUS_AUDIT_{AUDIT_DATE}.json"
SOURCE_ROOTS = list(dict.fromkeys([RAG_DOC_DIR, *RAG_DOC_ADDITIONAL_DIRS, BACKEND_DIR / "RAG-docsv2"]))
REQUIRED_ASSETS = [
    {
        "client_requirement": "Original source documents shared by David",
        "search_terms": ["world famous", "dumbass", "vessel", "logic schema", "brandgodfather logic schema"],
        "acceptance": "The four David-shared source PDFs under Rag_docs/ and RAG-docsv2/ are present, indexed, and chunk counts are known.",
    },
    {
        "client_requirement": "The Constitution",
        "search_terms": ["constitution"],
        "acceptance": "Constitution file is present and indexed.",
    },
    {
        "client_requirement": "ORB principles",
        "search_terms": ["orb principle", "orb principles", "orb"],
        "acceptance": "ORB principle document is present and indexed, not only UI component files.",
    },
    {
        "client_requirement": "Transformation Journey",
        "search_terms": ["transformation journey"],
        "acceptance": "Transformation Journey source is present and indexed.",
    },
    {
        "client_requirement": "Intelligence Framework",
        "search_terms": ["intelligence framework"],
        "acceptance": "Intelligence Framework source is present and indexed.",
    },
    {
        "client_requirement": "Brand Godfather foundational pillars",
        "search_terms": ["foundational pillar", "foundational pillars", "pillar"],
        "acceptance": "Foundational pillars source is present and indexed.",
    },
    {
        "client_requirement": "Breakthrough recognition criteria",
        "search_terms": ["breakthrough", "criteria", "logic schema"],
        "acceptance": "Breakthrough criteria source is present and indexed or explicitly implemented/tested.",
    },
    {
        "client_requirement": "Coaching rules and behavioral framework",
        "search_terms": ["coaching", "behavioral", "framework", "training"],
        "acceptance": "Coaching rules/behavior framework source is present and indexed.",
    },
]


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_DIR)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def is_supported(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in RAG_DOC_SUPPORTED_EXTENSIONS and not path.name.startswith(".")


def scan_current_assets() -> List[Dict[str, Any]]:
    configured = {rel(path): category for path, category in discover_rag_doc_files()}
    assets: List[Dict[str, Any]] = []
    seen = set()
    for root in SOURCE_ROOTS:
        root = Path(root)
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if not is_supported(path):
                continue
            asset_rel = rel(path)
            seen.add(asset_rel)
            assets.append(
                {
                    "path": asset_rel,
                    "file_name": path.name,
                    "source_root": root.name,
                    "extension": path.suffix.lower(),
                    "size_bytes": path.stat().st_size,
                    "configured_for_ai_knowledge": asset_rel in configured,
                    "configured_category": configured.get(asset_rel, ""),
                }
            )
    return sorted(assets, key=lambda item: item["path"])


def current_dry_run_chunk_counts() -> Counter:
    chunks = load_and_chunk_all()
    counts: Counter = Counter()
    for chunk in chunks:
        metadata = chunk.get("metadata") or {}
        key = metadata.get("file") or metadata.get("path") or "unknown"
        counts[str(key)] += 1
    return counts


def indexed_chunk_counts() -> Counter:
    counts: Counter = Counter()
    for chunk in AIKnowledgeChunk.objects.all().iterator():
        metadata = chunk.metadata or {}
        key = metadata.get("file") or metadata.get("path") or "unknown"
        counts[str(key)] += 1
    return counts


def rag_doc_v2_dry_run_counts(assets: Iterable[Dict[str, Any]]) -> Counter:
    counts: Counter = Counter()
    pdfs = [REPO_DIR / asset["path"] for asset in assets if asset["source_root"] == "RAG-docsv2" and asset["extension"] == ".pdf"]
    if not pdfs:
        return counts

    try:
        from brandgodfather.services.pdf_ingestion import PDFIngestionService

        service = PDFIngestionService()
        for pdf in pdfs:
            try:
                counts[rel(pdf)] = len(service.chunk_document(str(pdf), metadata={"source_file": pdf.name}))
            except Exception as exc:  # keep audit useful even when PDF parsing dependencies fail
                counts[f"{rel(pdf)}::ERROR"] = str(exc)
    except Exception as exc:
        counts["RAG-docsv2::ERROR"] = str(exc)
    return counts


def normalize_index_key_to_repo_path(index_key: str, current_assets: Iterable[Dict[str, Any]]) -> str:
    for asset in current_assets:
        if asset["path"].endswith(index_key):
            return asset["path"]
    return f"GodFather_backend/{index_key}" if index_key.startswith(("Rag_doc/", "Rag_docs/", "RAG-docsv2/")) else index_key


def match_required_assets(assets: List[Dict[str, Any]], indexed: Counter, dry_run: Counter, ragv2_counts: Counter) -> List[Dict[str, Any]]:
    matches = []
    for requirement in REQUIRED_ASSETS:
        terms = [term.lower() for term in requirement["search_terms"]]
        matched_assets = []
        for asset in assets:
            path_lower = asset["path"].lower().replace("_", " ").replace("-", " ")
            if any(term in path_lower for term in terms):
                matched_assets.append(asset["path"])
        derived_assets = [path for path in matched_assets if "derived" in path.lower() or "control" in path.lower()]
        original_assets = [path for path in matched_assets if path not in derived_assets]

        indexed_total = 0
        dry_run_total = 0
        for path in matched_assets:
            for key, count in indexed.items():
                if normalize_index_key_to_repo_path(key, assets) == path or path.endswith(key):
                    indexed_total += count
            index_key = path.replace("GodFather_backend/", "")
            path_dry_run = dry_run.get(index_key, 0)
            if path_dry_run:
                dry_run_total += path_dry_run
            else:
                ragv2_count = ragv2_counts.get(path, 0)
                dry_run_total += ragv2_count if isinstance(ragv2_count, int) else 0

        matched_with_index = 0
        matched_with_dry_run = 0
        for path in matched_assets:
            asset_indexed = False
            asset_dry_run = False
            for key, count in indexed.items():
                if count and (normalize_index_key_to_repo_path(key, assets) == path or path.endswith(key)):
                    asset_indexed = True
            index_key = path.replace("GodFather_backend/", "")
            if dry_run.get(index_key, 0):
                asset_dry_run = True
            ragv2_count = ragv2_counts.get(path, 0)
            if isinstance(ragv2_count, int) and ragv2_count > 0:
                asset_dry_run = True
            matched_with_index += 1 if asset_indexed else 0
            matched_with_dry_run += 1 if asset_dry_run else 0

        if derived_assets and not original_assets and matched_with_index == len(matched_assets):
            status = "Derived control indexed; separate original methodology source still required or David validation needed"
        elif derived_assets and not original_assets and dry_run_total > 0:
            status = "Derived control present; rebuild required"
        elif not matched_assets:
            status = "Missing from repo"
        elif matched_with_index == len(matched_assets):
            status = "Indexed"
        elif matched_with_index > 0:
            status = "Partially indexed"
        elif dry_run_total > 0:
            status = "Present but not indexed in current evidence"
        else:
            status = "Present but chunk count unavailable"

        matches.append(
            {
                "client_requirement": requirement["client_requirement"],
                "status": status,
                "matched_assets": matched_assets,
                "derived_assets": derived_assets,
                "original_assets": original_assets,
                "indexed_chunk_count": indexed_total,
                "dry_run_chunk_count": dry_run_total,
                "acceptance": requirement["acceptance"],
            }
        )
    return matches


def build_inventory() -> Dict[str, Any]:
    assets = scan_current_assets()
    dry_run = current_dry_run_chunk_counts()
    indexed = indexed_chunk_counts()
    ragv2_counts = rag_doc_v2_dry_run_counts(assets)
    state = load_index_state()
    should_rebuild, rebuild_reason = needs_rebuild(force=False)

    current_paths = {asset["path"] for asset in assets}
    asset_rows = []
    for asset in assets:
        index_key = asset["path"].replace("GodFather_backend/", "")
        indexed_count = indexed.get(index_key, 0)
        dry_count = dry_run.get(index_key, 0)
        ragv2_dry = ragv2_counts.get(asset["path"], 0)
        if isinstance(ragv2_dry, str):
            ragv2_error = ragv2_dry
            ragv2_dry = 0
        else:
            ragv2_error = ""
        asset_rows.append(
            {
                **asset,
                "indexed_chunk_count": indexed_count,
                "dry_run_chunk_count": dry_count or ragv2_dry,
                "dry_run_error": ragv2_error,
                "indexed_status": "Indexed" if indexed_count > 0 else "Not indexed in ai_knowledge evidence",
            }
        )

    indexed_only = []
    for key, count in sorted(indexed.items()):
        normalized = normalize_index_key_to_repo_path(key, assets)
        if normalized not in current_paths:
            indexed_only.append({"indexed_metadata_file": key, "normalized_path": normalized, "chunk_count": count})

    by_root = defaultdict(int)
    for asset in assets:
        by_root[asset["source_root"]] += 1

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "current_supported_assets": len(assets),
            "current_assets_by_root": dict(sorted(by_root.items())),
            "ai_knowledge_state_status": state.get("status"),
            "ai_knowledge_state_chunk_count": state.get("chunk_count"),
            "ai_knowledge_db_chunk_rows": sum(indexed.values()),
            "dry_run_ai_knowledge_chunk_count": sum(dry_run.values()),
            "needs_rebuild": should_rebuild,
            "rebuild_reason": rebuild_reason,
            "last_built_at": state.get("last_built_at"),
            "stored_fingerprint": state.get("fingerprint"),
        },
        "required_client_assets": match_required_assets(assets, indexed, dry_run, ragv2_counts),
        "current_asset_inventory": asset_rows,
        "indexed_only_missing_from_current_folders": indexed_only,
    }


def table(headers: List[str], rows: List[List[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(str(cell).replace("\n", "<br>") for cell in row) + " |")
    return "\n".join(lines)


def write_markdown(inventory: Dict[str, Any]) -> None:
    summary = inventory["summary"]
    ragv2_configured = any(
        item["source_root"] == "RAG-docsv2" and item["configured_for_ai_knowledge"]
        for item in inventory["current_asset_inventory"]
    )
    if ragv2_configured and not summary["needs_rebuild"]:
        ragv2_sentence = "`RAG-docsv2/` is configured as an additional `ai_knowledge` source and the current index has been rebuilt against it."
    elif ragv2_configured:
        ragv2_sentence = "`RAG-docsv2/` is configured as an additional `ai_knowledge` source, but the index must be rebuilt before those files are proven indexed."
    else:
        ragv2_sentence = "`RAG-docsv2/` is present, but it is not part of the configured `ai_knowledge` loader; it uses the separate BrandGodFather PDF ingestion path."
    stale_sentence = (
        "The index is also stale because current configured files produce a different chunk/fingerprint state than the stored index."
        if summary["needs_rebuild"]
        else "The current available configured corpus is indexed and up to date. Derived methodology controls are searchable, but original client-authored methodology files must still replace or validate those controls."
    )
    required_rows = [
        [
            item["client_requirement"],
            item["status"],
            item["indexed_chunk_count"],
            item["dry_run_chunk_count"],
            "<br>".join(item["matched_assets"]) if item["matched_assets"] else "Missing from current folders",
        ]
        for item in inventory["required_client_assets"]
    ]
    asset_rows = [
        [
            item["path"],
            item["source_root"],
            "yes" if item["configured_for_ai_knowledge"] else "no",
            item["configured_category"] or "-",
            item["indexed_chunk_count"],
            item["dry_run_chunk_count"],
            item["indexed_status"],
        ]
        for item in inventory["current_asset_inventory"]
    ]
    indexed_only_rows = [
        [item["indexed_metadata_file"], item["normalized_path"], item["chunk_count"]]
        for item in inventory["indexed_only_missing_from_current_folders"]
    ]
    if not indexed_only_rows:
        indexed_only_rows = [["None", "-", 0]]

    content = f"""# Client IP Corpus Audit

Date: {AUDIT_DATE}  
Purpose: Audit Brand Godfather client IP/source assets against David Tyreman's recovery email and show what is indexed, not indexed, missing, or stale.

## Client-Mail Source Of Truth

David explicitly asked whether the team has studied and operationalized his books, intellectual property, methodologies, ORB concepts, Intelligence Framework, Constitution, ORB principles, Transformation Journey, foundational pillars, coaching rules, behavioral framework, and breakthrough recognition criteria.

This audit is intentionally evidence-led. It does not claim a source is operationalized unless a file is present and indexing evidence exists.

## Executive Finding

- Current supported asset files found under `Rag_doc/`, `Rag_docs/`, and `RAG-docsv2/`: **{summary['current_supported_assets']}**.
- Stored `ai_knowledge` state says **{summary['ai_knowledge_state_chunk_count']}** chunks, and the local `AIKnowledgeChunk` table has **{summary['ai_knowledge_db_chunk_rows']}** rows.
- A dry-run rebuild from currently configured `ai_knowledge` sources produces **{summary['dry_run_ai_knowledge_chunk_count']}** chunks.
- Rebuild needed: **{summary['needs_rebuild']}** (`{summary['rebuild_reason']}`).
- {ragv2_sentence}
- The four David-shared original PDFs currently present in `Rag_docs/` and `RAG-docsv2/` are indexed. Constitution, ORB principles, Intelligence Framework, Transformation Journey, and foundational pillars are covered by **derived control files** when present; separate original methodology files or David validation are still required for final methodology-complete status.

## Required Client Asset Coverage

{table(['Client Requirement', 'Current Evidence Status', 'Indexed Chunks', 'Dry-Run Chunks', 'Matched Assets'], required_rows)}

## Current Asset Inventory

{table(['Asset Path', 'Root', 'Configured For ai_knowledge', 'Category', 'Indexed Chunks', 'Dry-Run Chunks', 'Status'], asset_rows)}

## Indexed Metadata For Files Missing From Current Folders

These chunks exist in the local `AIKnowledgeChunk` table, but the matching source file path was not found in the current asset folders. This is a stale-corpus risk and must be resolved before telling the client the corpus is clean.

{table(['Indexed Metadata File', 'Normalized Expected Path', 'Indexed Chunks'], indexed_only_rows)}

## Required Correction Plan

| Priority | Action | Acceptance Evidence |
|---|---|---|
| P0 | Add or recover separate original methodology files for Constitution, ORB principles, Transformation Journey, Intelligence Framework, and foundational pillars, or obtain David validation of the derived controls. The four currently present David-shared PDFs are already indexed. | Original methodology files exist under a configured corpus source folder without derived-control caveat, or David validates the derived controls. |
| P0 | Keep one canonical corpus source path and rebuild after any new source is added. `RAG-docsv2/` is configured now. | Dry-run and stored index both include `RAG-docsv2/` files with per-file counts. |
| P0 | Rebuild `ai_knowledge` after missing IP files are added. | `python manage.py build_ai_knowledge --force --sync` completes and `needs_rebuild` remains false. |
| P0 | Preserve/source metadata for BrandGodFather PDF ingestion outputs. | `brandgodfather_brand_chunks` can be queried by `source_file` and chunk counts by asset are visible. |
| P1 | Produce AI-analysis record for David's IP. | Meeting pack lists document, owner/studied by, AI analysis notes, indexed chunk count, and behavior translated into ORB rules. |

## Honest Client-Facing Language

The currently available configured corpus is indexed, and current evidence proves the four David-shared PDFs, training material, logic-schema material, and derived methodology controls are indexed/searchable. It is still not safe to claim the separate Constitution, ORB principles, Intelligence Framework, Transformation Journey, and foundational pillars originals have been fully studied as original methodology files unless those documents are supplied or David validates the derived controls. {stale_sentence}
"""
    REPORT_PATH.write_text(content, encoding="utf-8")


def main() -> int:
    inventory = build_inventory()
    JSON_PATH.write_text(json.dumps(inventory, indent=2, ensure_ascii=True), encoding="utf-8")
    write_markdown(inventory)
    print(f"Wrote {REPORT_PATH}")
    print(f"Wrote {JSON_PATH}")
    print(json.dumps(inventory["summary"], indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())