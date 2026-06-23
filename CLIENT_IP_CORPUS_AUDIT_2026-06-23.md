# Client IP Corpus Audit

Date: 2026-06-23  
Purpose: Audit Brand Godfather client IP/source assets against David Tyreman's recovery email and show what is indexed, not indexed, missing, or stale.

## Client-Mail Source Of Truth

David explicitly asked whether the team has studied and operationalized his books, intellectual property, methodologies, ORB concepts, Intelligence Framework, Constitution, ORB principles, Transformation Journey, foundational pillars, coaching rules, behavioral framework, and breakthrough recognition criteria.

This audit is intentionally evidence-led. It does not claim a source is operationalized unless a file is present and indexing evidence exists.

## Executive Finding

- Current supported asset files found under `Rag_doc/`, `Rag_docs/`, and `RAG-docsv2/`: **17**.
- Stored `ai_knowledge` state says **191** chunks, and the local `AIKnowledgeChunk` table has **191** rows.
- A dry-run rebuild from currently configured `ai_knowledge` sources produces **191** chunks.
- Rebuild needed: **False** (`up_to_date`).
- `RAG-docsv2/` is configured as an additional `ai_knowledge` source and the current index has been rebuilt against it.
- The four David-shared original PDFs currently present in `Rag_docs/` and `RAG-docsv2/` are indexed. Constitution, ORB principles, Intelligence Framework, Transformation Journey, and foundational pillars are covered by **derived control files** when present; separate original methodology files or David validation are still required for final methodology-complete status.

## Required Client Asset Coverage

| Client Requirement | Current Evidence Status | Indexed Chunks | Dry-Run Chunks | Matched Assets |
|---|---|---|---|---|
| Original source documents shared by David | Indexed | 120 | 120 | GodFather_backend/RAG-docsv2/BrandGodFather_Logic_Schema_v1.2.pdf<br>GodFather_backend/RAG-docsv2/Vessel & Craft FINAL Brand Book.pdf<br>GodFather_backend/Rag_docs/7_Dumbass_Branding_Mistakes_23.pdf<br>GodFather_backend/Rag_docs/World Famous Complete 9-25-08 for MVP.pdf |
| The Constitution | Derived control indexed; separate original methodology source still required or David validation needed | 6 | 6 | GodFather_backend/RAG-docsv2/The_Constitution_Derived_Control.md<br>GodFather_backend/Rag_doc/methodology/the-constitution-derived-control.md |
| ORB principles | Derived control indexed; separate original methodology source still required or David validation needed | 9 | 9 | GodFather_backend/RAG-docsv2/ORB_Principles_Derived_Control.md<br>GodFather_backend/Rag_doc/methodology/orb-principles-derived-control.md |
| Transformation Journey | Derived control indexed; separate original methodology source still required or David validation needed | 6 | 6 | GodFather_backend/RAG-docsv2/Transformation_Journey_Derived_Control.md<br>GodFather_backend/Rag_doc/methodology/transformation-journey-derived-control.md |
| Intelligence Framework | Derived control indexed; separate original methodology source still required or David validation needed | 8 | 8 | GodFather_backend/RAG-docsv2/Intelligence_Framework_Derived_Control.md<br>GodFather_backend/Rag_doc/methodology/intelligence-framework-derived-control.md |
| Brand Godfather foundational pillars | Derived control indexed; separate original methodology source still required or David validation needed | 4 | 4 | GodFather_backend/RAG-docsv2/Foundational_Pillars_Derived_Control.md<br>GodFather_backend/Rag_doc/methodology/foundational-pillars-derived-control.md |
| Breakthrough recognition criteria | Indexed | 45 | 45 | GodFather_backend/RAG-docsv2/BrandGodFather_Logic_Schema_v1.2.pdf |
| Coaching rules and behavioral framework | Indexed | 38 | 38 | GodFather_backend/RAG-docsv2/Intelligence_Framework_Derived_Control.md<br>GodFather_backend/Rag_doc/branding/training-AI-tool.txt<br>GodFather_backend/Rag_doc/methodology/intelligence-framework-derived-control.md |

## Current Asset Inventory

| Asset Path | Root | Configured For ai_knowledge | Category | Indexed Chunks | Dry-Run Chunks | Status |
|---|---|---|---|---|---|---|
| GodFather_backend/RAG-docsv2/BrandGodFather_Logic_Schema_v1.2.pdf | RAG-docsv2 | yes | branding | 45 | 45 | Indexed |
| GodFather_backend/RAG-docsv2/Foundational_Pillars_Derived_Control.md | RAG-docsv2 | yes | methodology | 2 | 2 | Indexed |
| GodFather_backend/RAG-docsv2/Intelligence_Framework_Derived_Control.md | RAG-docsv2 | yes | methodology | 4 | 4 | Indexed |
| GodFather_backend/RAG-docsv2/ORB_Principles_Derived_Control.md | RAG-docsv2 | yes | methodology | 7 | 7 | Indexed |
| GodFather_backend/RAG-docsv2/The_Constitution_Derived_Control.md | RAG-docsv2 | yes | methodology | 3 | 3 | Indexed |
| GodFather_backend/RAG-docsv2/Transformation_Journey_Derived_Control.md | RAG-docsv2 | yes | methodology | 3 | 3 | Indexed |
| GodFather_backend/RAG-docsv2/Vessel & Craft FINAL Brand Book.pdf | RAG-docsv2 | yes | branding | 23 | 23 | Indexed |
| GodFather_backend/Rag_doc/README.md | Rag_doc | no | - | 0 | 0 | Not indexed in ai_knowledge evidence |
| GodFather_backend/Rag_doc/branding/training-AI-tool.txt | Rag_doc | yes | branding | 30 | 30 | Indexed |
| GodFather_backend/Rag_doc/manifesto/after-manifesto-ai-tool.txt | Rag_doc | yes | manifesto | 8 | 8 | Indexed |
| GodFather_backend/Rag_doc/methodology/foundational-pillars-derived-control.md | Rag_doc | yes | methodology | 2 | 2 | Indexed |
| GodFather_backend/Rag_doc/methodology/intelligence-framework-derived-control.md | Rag_doc | yes | methodology | 4 | 4 | Indexed |
| GodFather_backend/Rag_doc/methodology/orb-principles-derived-control.md | Rag_doc | yes | methodology | 2 | 2 | Indexed |
| GodFather_backend/Rag_doc/methodology/the-constitution-derived-control.md | Rag_doc | yes | methodology | 3 | 3 | Indexed |
| GodFather_backend/Rag_doc/methodology/transformation-journey-derived-control.md | Rag_doc | yes | methodology | 3 | 3 | Indexed |
| GodFather_backend/Rag_docs/7_Dumbass_Branding_Mistakes_23.pdf | Rag_docs | yes | branding | 10 | 10 | Indexed |
| GodFather_backend/Rag_docs/World Famous Complete 9-25-08 for MVP.pdf | Rag_docs | yes | strategy | 42 | 42 | Indexed |

## Indexed Metadata For Files Missing From Current Folders

These chunks exist in the local `AIKnowledgeChunk` table, but the matching source file path was not found in the current asset folders. This is a stale-corpus risk and must be resolved before telling the client the corpus is clean.

| Indexed Metadata File | Normalized Expected Path | Indexed Chunks |
|---|---|---|
| None | - | 0 |

## Required Correction Plan

| Priority | Action | Acceptance Evidence |
|---|---|---|
| P0 | Add or recover separate original methodology files for Constitution, ORB principles, Transformation Journey, Intelligence Framework, and foundational pillars, or obtain David validation of the derived controls. The four currently present David-shared PDFs are already indexed. | Original methodology files exist under a configured corpus source folder without derived-control caveat, or David validates the derived controls. |
| P0 | Keep one canonical corpus source path and rebuild after any new source is added. `RAG-docsv2/` is configured now. | Dry-run and stored index both include `RAG-docsv2/` files with per-file counts. |
| P0 | Rebuild `ai_knowledge` after missing IP files are added. | `python manage.py build_ai_knowledge --force --sync` completes and `needs_rebuild` remains false. |
| P0 | Preserve/source metadata for BrandGodFather PDF ingestion outputs. | `brandgodfather_brand_chunks` can be queried by `source_file` and chunk counts by asset are visible. |
| P1 | Produce AI-analysis record for David's IP. | Meeting pack lists document, owner/studied by, AI analysis notes, indexed chunk count, and behavior translated into ORB rules. |

## Honest Client-Facing Language

The currently available configured corpus is indexed, and current evidence proves the four David-shared PDFs, training material, logic-schema material, and derived methodology controls are indexed/searchable. It is still not safe to claim the separate Constitution, ORB principles, Intelligence Framework, Transformation Journey, and foundational pillars originals have been fully studied as original methodology files unless those documents are supplied or David validates the derived controls. The current available configured corpus is indexed and up to date. Derived methodology controls are searchable, but original client-authored methodology files must still replace or validate those controls.
