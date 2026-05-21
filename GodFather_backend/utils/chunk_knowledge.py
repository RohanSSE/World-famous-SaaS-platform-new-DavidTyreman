"""
Chunk plain-text knowledge files for embedding and vector search.
Produces chunks with metadata (source, section) for optimized retrieval.
"""
import re
import logging
from pathlib import Path
from typing import List, Dict, Any

from .ai_knowledge_config import (
    AI_KNOWLEDGE_FILES,
    get_knowledge_file_path,
    AI_KNOWLEDGE_CHUNK_SIZE,
    AI_KNOWLEDGE_CHUNK_OVERLAP,
)

logger = logging.getLogger(__name__)


def _normalize_text(text: str) -> str:
    """Collapse whitespace, keep structure."""
    return re.sub(r'\s+', ' ', text).strip()


def _split_into_sections(content: str) -> List[str]:
    """Split content into sections by double newline or clear headings."""
    sections = []
    for block in re.split(r'\n\s*\n', content):
        block = block.strip()
        if len(block) > 50:  # skip tiny fragments
            sections.append(block)
    return sections


def _chunk_section(
    section_text: str,
    source: str,
    chunk_size: int,
    chunk_overlap: int,
) -> List[Dict[str, Any]]:
    """Split a section into word-based chunks with overlap."""
    words = section_text.split()
    chunks = []
    start = 0
    chunk_id = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk_words = words[start:end]
        chunk_text = ' '.join(chunk_words)
        if not chunk_text.strip():
            start = end
            continue
        chunks.append({
            "chunk_id": chunk_id,
            "text": chunk_text,
            "metadata": {
                "source": source,
                "word_count": len(chunk_words),
            },
            "document_id": 0,  # single knowledge base
            "page_number": 0,
        })
        chunk_id += 1
        start = end - chunk_overlap if end < len(words) else end
    return chunks


def load_and_chunk_all(
    chunk_size: int = AI_KNOWLEDGE_CHUNK_SIZE,
    chunk_overlap: int = AI_KNOWLEDGE_CHUNK_OVERLAP,
) -> List[Dict[str, Any]]:
    """
    Load all configured knowledge files, split into sections, then into chunks.
    Returns list of chunk dicts (without embeddings) ready for embedding + indexing.
    """
    all_chunks = []
    global_chunk_id = 0

    for filename, source in AI_KNOWLEDGE_FILES:
        path = get_knowledge_file_path(filename)
        if not path.exists():
            logger.warning("Knowledge file not found: %s", path)
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            logger.error("Failed to read %s: %s", path, e)
            continue

        sections = _split_into_sections(content)
        for section in sections:
            section_chunks = _chunk_section(
                section, source, chunk_size, chunk_overlap
            )
            for c in section_chunks:
                c["chunk_id"] = global_chunk_id
                global_chunk_id += 1
                all_chunks.append(c)

    logger.info("Chunked %s files into %d chunks", len(AI_KNOWLEDGE_FILES), len(all_chunks))
    return all_chunks
