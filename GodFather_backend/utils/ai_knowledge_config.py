"""
AI knowledge base configuration.
Primary sources: GodFather_backend/Rag_doc/<category>/
Legacy fallback: utils/*.txt (optional)
"""
import os
from pathlib import Path

# Base dirs
UTILS_DIR = Path(__file__).resolve().parent
BACKEND_DIR = UTILS_DIR.parent

# Rag_doc — categorized knowledge library (primary source)
RAG_DOC_DIR = BACKEND_DIR / "Rag_doc"
RAG_DOC_ADDITIONAL_DIRS = [
    BACKEND_DIR / "Rag_docs",
]
RAG_DOC_CATEGORIES = [
    "branding",
    "manifesto",
    "psychology",
    "strategy",
    "positioning",
    "sales",
    "marketing",
]
RAG_DOC_SUPPORTED_EXTENSIONS = frozenset({".txt", ".md", ".markdown", ".pdf"})

# Elasticsearch index name for AI knowledge
AI_KNOWLEDGE_INDEX_NAME = "ai_knowledge"

# Legacy utils/*.txt (set True only if you keep masters only under utils/, not Rag_doc/)
INCLUDE_LEGACY_UTILS_TXT = False
AI_KNOWLEDGE_FILES = [
    ("training-AI-tool.txt", "branding"),
    ("after-manifesto-ai-tool.txt", "manifesto"),
]

# Semantic chunking: split by headings/sections; only split further if section exceeds max words
AI_KNOWLEDGE_SEMANTIC_MAX_WORDS = 350
AI_KNOWLEDGE_SEMANTIC_OVERLAP = 40

# Legacy flat chunking (deprecated — kept for reference)
AI_KNOWLEDGE_CHUNK_SIZE = 400
AI_KNOWLEDGE_CHUNK_OVERLAP = 80

# Default retrieval: top-k chunks to inject into prompts
AI_KNOWLEDGE_TOP_K = 8

# Embedding: text-embedding-3-small (1536 dimensions)
EMBEDDING_DIMS = 1536
EMBEDDING_MODEL = "text-embedding-3-small"


def get_knowledge_file_path(filename: str) -> Path:
    """Return full path to a knowledge file in utils."""
    return UTILS_DIR / filename
