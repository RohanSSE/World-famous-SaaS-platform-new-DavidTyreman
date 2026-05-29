"""
Load knowledge documents from GodFather_backend/Rag_doc/<category>/ and legacy Rag_docs/.
Supports .txt, .md, .pdf (via document PDFProcessor).
"""
import logging
from pathlib import Path
from typing import List, Tuple

from .ai_knowledge_config import (
    RAG_DOC_ADDITIONAL_DIRS,
    RAG_DOC_DIR,
    RAG_DOC_CATEGORIES,
    RAG_DOC_SUPPORTED_EXTENSIONS,
)

logger = logging.getLogger(__name__)


def _infer_category_from_name(file_path: Path) -> str:
    """Infer category for flat legacy Rag_docs files."""
    name = file_path.stem.lower()
    keyword_categories = (
        ("manifesto", "manifesto"),
        ("position", "positioning"),
        ("psycholog", "psychology"),
        ("emotion", "psychology"),
        ("trust", "psychology"),
        ("sales", "sales"),
        ("subscription", "sales"),
        ("pricing", "sales"),
        ("marketing", "marketing"),
        ("campaign", "marketing"),
        ("content", "marketing"),
        ("output mode", "marketing"),
        ("brand book", "branding"),
        ("branding", "branding"),
        ("brand", "branding"),
        ("strategy", "strategy"),
        ("synapse", "strategy"),
        ("logic", "strategy"),
        ("system", "strategy"),
        ("brief", "strategy"),
        ("mvp", "strategy"),
    )

    for keyword, category in keyword_categories:
        if keyword in name:
            return category
    return "branding"


def _is_supported_file(path: Path) -> bool:
    return (
        path.is_file()
        and path.suffix.lower() in RAG_DOC_SUPPORTED_EXTENSIONS
        and not path.name.startswith(".")
    )


def _discover_categorized_root(root: Path, categories: List[str]) -> List[Tuple[Path, str]]:
    found: List[Tuple[Path, str]] = []
    for category in categories:
        category_dir = root / category
        if not category_dir.is_dir():
            continue
        for path in sorted(category_dir.rglob("*")):
            if _is_supported_file(path):
                found.append((path, category))
    return found


def _discover_flat_root(root: Path, categories: List[str]) -> List[Tuple[Path, str]]:
    found = _discover_categorized_root(root, categories)
    categorized_dirs = {category.lower() for category in categories}

    for path in sorted(root.rglob("*")):
        if not _is_supported_file(path):
            continue
        try:
            relative_parts = path.relative_to(root).parts
        except ValueError:
            relative_parts = ()
        if relative_parts and relative_parts[0].lower() in categorized_dirs:
            continue
        found.append((path, _infer_category_from_name(path)))

    return found


def discover_rag_doc_files(
    rag_doc_dir: Path = None,
    categories: List[str] = None,
) -> List[Tuple[Path, str]]:
    """
    Return (file_path, category) for every supported knowledge file.
    Primary layout is Rag_doc/<category>/; legacy Rag_docs/ can be flat.
    """
    cats = categories or RAG_DOC_CATEGORIES
    found: List[Tuple[Path, str]] = []

    if rag_doc_dir is not None:
        root = Path(rag_doc_dir)
        if not root.is_dir():
            logger.warning("Rag_doc directory not found: %s", root)
            return found
        found.extend(_discover_categorized_root(root, cats))
        logger.info("Discovered %d Rag_doc files under %s", len(found), root)
        return found

    if RAG_DOC_DIR.is_dir():
        found.extend(_discover_categorized_root(RAG_DOC_DIR, cats))
    else:
        logger.warning("Rag_doc directory not found: %s", RAG_DOC_DIR)

    for extra_root in RAG_DOC_ADDITIONAL_DIRS:
        extra_root = Path(extra_root)
        if extra_root.is_dir():
            found.extend(_discover_flat_root(extra_root, cats))

    logger.info(
        "Discovered %d RAG knowledge files under %s plus %d additional roots",
        len(found),
        RAG_DOC_DIR,
        len(RAG_DOC_ADDITIONAL_DIRS),
    )
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
    """Path relative to a RAG source root for metadata."""
    roots = [Path(rag_doc_dir)] if rag_doc_dir else [Path(RAG_DOC_DIR), *map(Path, RAG_DOC_ADDITIONAL_DIRS)]
    for root in roots:
        try:
            relative = str(file_path.relative_to(root)).replace("\\", "/")
            return f"{root.name}/{relative}"
        except ValueError:
            continue
    return file_path.name
