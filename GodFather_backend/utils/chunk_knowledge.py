"""
Chunk knowledge for embedding and vector search.
Uses semantic chunking (headings, principles, bullets, sections).
"""
import logging
from typing import List, Dict, Any

from .ai_knowledge_config import (
    AI_KNOWLEDGE_FILES,
    INCLUDE_LEGACY_UTILS_TXT,
    get_knowledge_file_path,
    AI_KNOWLEDGE_SEMANTIC_MAX_WORDS,
    AI_KNOWLEDGE_SEMANTIC_OVERLAP,
    RAG_DOC_DIR,
)
from .rag_doc_loader import (
    discover_rag_doc_files,
    extract_text_from_rag_file,
    relative_rag_path,
)
from .semantic_chunker import semantic_chunk_document

logger = logging.getLogger(__name__)


def load_and_chunk_rag_doc(
    max_words: int = AI_KNOWLEDGE_SEMANTIC_MAX_WORDS,
    overlap_words: int = AI_KNOWLEDGE_SEMANTIC_OVERLAP,
) -> List[Dict[str, Any]]:
    """Load all files from configured RAG document sources and return chunks."""
    all_chunks: List[Dict[str, Any]] = []
    files = discover_rag_doc_files()

    for file_path, category in files:
        try:
            raw = extract_text_from_rag_file(file_path)
            from user_sessions.services.content_safety import sanitize_chunk_text_for_index

            raw = sanitize_chunk_text_for_index(raw)
        except Exception as e:
            logger.error("Failed to read Rag_doc file %s: %s", file_path, e)
            continue

        rel = relative_rag_path(file_path)
        file_chunks = semantic_chunk_document(
            raw,
            category=category,
            extra_metadata={"file": rel, "path": rel},
            max_words=max_words,
            overlap_words=overlap_words,
        )
        if file_chunks:
            titles = [c["metadata"].get("title", "?") for c in file_chunks[:3]]
            logger.info(
                "Semantic chunk %s → %d chunks (e.g. %s)",
                rel,
                len(file_chunks),
                ", ".join(titles),
            )
        all_chunks.extend(file_chunks)

    return all_chunks


def load_and_chunk_legacy_utils(
    max_words: int = AI_KNOWLEDGE_SEMANTIC_MAX_WORDS,
    overlap_words: int = AI_KNOWLEDGE_SEMANTIC_OVERLAP,
) -> List[Dict[str, Any]]:
    """Load legacy utils/*.txt knowledge files with semantic chunking."""
    all_chunks: List[Dict[str, Any]] = []

    for filename, source in AI_KNOWLEDGE_FILES:
        path = get_knowledge_file_path(filename)
        if not path.exists():
            logger.warning("Legacy knowledge file not found: %s", path)
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            logger.error("Failed to read %s: %s", path, e)
            continue

        file_chunks = semantic_chunk_document(
            content,
            category=source,
            extra_metadata={"file": filename, "legacy": True},
            max_words=max_words,
            overlap_words=overlap_words,
        )
        all_chunks.extend(file_chunks)

    return all_chunks


def load_and_chunk_all(
    max_words: int = AI_KNOWLEDGE_SEMANTIC_MAX_WORDS,
    overlap_words: int = AI_KNOWLEDGE_SEMANTIC_OVERLAP,
) -> List[Dict[str, Any]]:
    """
    Load Rag_doc categories + optional legacy utils txt files.
    Assigns global chunk_id across all sources.
    """
    combined: List[Dict[str, Any]] = []

    combined.extend(load_and_chunk_rag_doc(max_words, overlap_words))

    if INCLUDE_LEGACY_UTILS_TXT:
        combined.extend(load_and_chunk_legacy_utils(max_words, overlap_words))

    global_chunk_id = 0
    for c in combined:
        c["chunk_id"] = global_chunk_id
        global_chunk_id += 1

    from .chunk_quality_filter import filter_chunks_for_index
    from .strategic_tags import attach_strategic_tags

    combined, filter_stats = filter_chunks_for_index(combined)
    for c in combined:
        attach_strategic_tags(c)

    logger.info(
        "Total semantic knowledge chunks: %d (Rag_doc: %s) filter_stats=%s",
        len(combined),
        RAG_DOC_DIR,
        filter_stats,
    )
    return combined
