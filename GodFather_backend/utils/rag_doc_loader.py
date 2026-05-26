"""
Load knowledge documents from GodFather_backend/Rag_doc/<category>/.
Supports .txt, .md, .pdf (via document PDFProcessor).
"""
import logging
from pathlib import Path
from typing import List, Tuple

from .ai_knowledge_config import (
    RAG_DOC_DIR,
    RAG_DOC_CATEGORIES,
    RAG_DOC_SUPPORTED_EXTENSIONS,
)

logger = logging.getLogger(__name__)


def discover_rag_doc_files(
    rag_doc_dir: Path = None,
    categories: List[str] = None,
) -> List[Tuple[Path, str]]:
    """
    Return (file_path, category) for every supported file under Rag_doc/<category>/.
    Walks subdirectories recursively.
    """
    root = Path(rag_doc_dir or RAG_DOC_DIR)
    cats = categories or RAG_DOC_CATEGORIES
    found: List[Tuple[Path, str]] = []

    if not root.is_dir():
        logger.warning("Rag_doc directory not found: %s", root)
        return found

    for category in cats:
        category_dir = root / category
        if not category_dir.is_dir():
            continue
        for path in sorted(category_dir.rglob("*")):
            if not path.is_file():
                continue
            if path.suffix.lower() not in RAG_DOC_SUPPORTED_EXTENSIONS:
                continue
            if path.name.startswith("."):
                continue
            found.append((path, category))

    logger.info("Discovered %d Rag_doc files under %s", len(found), root)
    return found


def extract_text_from_rag_file(file_path: Path) -> str:
    """Extract plain text from a Rag_doc file."""
    suffix = file_path.suffix.lower()

    if suffix == ".pdf":
        from document.utils.pdf_processor import PDFProcessor

        processor = PDFProcessor()
        pages = processor.extract_text_from_pdf(str(file_path))
        parts = []
        for page in pages:
            text = (page.get("text") or "").strip()
            if text:
                parts.append(text)
        return "\n\n".join(parts)

    return file_path.read_text(encoding="utf-8", errors="replace")


def relative_rag_path(file_path: Path, rag_doc_dir: Path = None) -> str:
    """Path relative to Rag_doc root for metadata (e.g. branding/playbook.txt)."""
    root = Path(rag_doc_dir or RAG_DOC_DIR)
    try:
        return str(file_path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return file_path.name
