"""
AI knowledge base configuration.
All AI-related knowledge files and vector index settings live here.
"""
import os
from pathlib import Path

# Base dir for utils (this file lives in utils/)
UTILS_DIR = Path(__file__).resolve().parent

# Elasticsearch index name for AI knowledge (training + after-manifesto content)
AI_KNOWLEDGE_INDEX_NAME = "ai_knowledge"

# Knowledge source files (relative to UTILS_DIR)
AI_KNOWLEDGE_FILES = [
    ("training-AI-tool.txt", "training"),   # (filename, source tag)
    ("after-manifesto-ai-tool.txt", "after_manifesto"),
]

# Chunking for better retrieval: ~400 words per chunk, 80 word overlap
AI_KNOWLEDGE_CHUNK_SIZE = 400
AI_KNOWLEDGE_CHUNK_OVERLAP = 80

# Default retrieval: top-k chunks to inject into prompts
AI_KNOWLEDGE_TOP_K = 8

# Embedding dimension (OpenAI text-embedding-ada-002)
EMBEDDING_DIMS = 1536


def get_knowledge_file_path(filename: str) -> Path:
    """Return full path to a knowledge file in utils."""
    return UTILS_DIR / filename
