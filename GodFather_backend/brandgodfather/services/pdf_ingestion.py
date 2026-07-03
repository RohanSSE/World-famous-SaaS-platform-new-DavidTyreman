from __future__ import annotations

import hashlib
import logging
import re
from pathlib import Path
from typing import Any, Dict, List

import pdfplumber
from elasticsearch.helpers import bulk
from elasticsearch_dsl import connections
from rank_bm25 import BM25Okapi

from document.utils.embedding_service import EmbeddingService
from brandgodfather.documents import BRANDGODFATHER_NODE_2_ALIAS, BrandGodFatherBrandChunkDocument
from utils.retry_azure import with_azure_retry

logger = logging.getLogger(__name__)

CHUNK_TYPE_KEYWORDS = {
    "archetype_definition": [
        "definition",
        "is a",
        "archetype",
        "identity",
        "positioning",
        "core belief",
    ],
    "rejection_example": [
        "bad answer",
        "weak answer",
        "fails",
        "avoid",
        "rejected",
        "wrong",
        "generic",
    ],
    "gold_standard_example": [
        "gold standard",
        "great answer",
        "excellent answer",
        "strong answer",
        "best answer",
        "ideal",
    ],
    "challenge_language": [
        "coach says",
        "challenge",
        "push",
        "probe",
        "ask directly",
        "say this",
    ],
    "manifesto_fragment": [
        "manifesto",
        "line in the sand",
        "promise",
        "we stand for",
        "we reject",
        "our code",
    ],
}

QUESTION_RE = re.compile(r"\bQ\s*([1-9]|[12][0-9]|30)\b", re.IGNORECASE)
QUESTION_WORD_RE = re.compile(
    r"\bquestion\s*([1-9]|[12][0-9]|30)\b", re.IGNORECASE
)
PHASE_RE = re.compile(r"\bphase\s+(i|ii|iii|iv|v|vi|vii|viii|ix|x)\b", re.IGNORECASE)
ALL_CAPS_RE = re.compile(r"^[A-Z0-9][A-Z0-9\s\-:&]{5,}$")
NUMBERED_SECTION_RE = re.compile(r"^\s*\d+(?:\.\d+)*[\).:\-\s]+")


class PDFIngestionService:
    def __init__(self) -> None:
        self.embedding_service = EmbeddingService()
        self.es = connections.get_connection(alias=BRANDGODFATHER_NODE_2_ALIAS)

        corpus = [" ".join(tokens) for tokens in CHUNK_TYPE_KEYWORDS.values()]
        tokenized = [self._tokenize(text) for text in corpus]
        self._bm25 = BM25Okapi(tokenized)
        self._bm25_labels = list(CHUNK_TYPE_KEYWORDS.keys())

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        return re.findall(r"[a-z0-9]+", text.lower())

    @staticmethod
    def _split_sentences(text: str) -> List[str]:
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        return [s.strip() for s in sentences if s.strip()]

    def extract_text(self, pdf_path: str) -> str:
        """Extract text from a PDF, Markdown, or text source file."""
        source_path = Path(pdf_path)
        if source_path.suffix.lower() in {".md", ".markdown", ".txt"}:
            return source_path.read_text(encoding="utf-8", errors="replace").strip()

        pages: List[str] = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                txt = (page.extract_text() or "").strip()
                if txt:
                    pages.append(txt)

        raw = "\n\n".join(pages).strip()
        if raw:
            return raw

        # Fallback parser for image-heavy PDFs.
        try:
            from unstructured.partition.pdf import partition_pdf

            elements = partition_pdf(filename=pdf_path)
            fallback = "\n".join(str(el).strip() for el in elements if str(el).strip())
            return fallback.strip()
        except Exception:
            return ""

    def detect_sections(self, text: str) -> List[Dict[str, str]]:
        """Split on semantic headers: markdown headers, numbered sections, ALL CAPS lines."""
        lines = [line.rstrip() for line in text.splitlines()]
        sections: List[Dict[str, str]] = []
        current_title = "INTRO"
        current_lines: List[str] = []

        def flush() -> None:
            content = "\n".join(current_lines).strip()
            if content:
                sections.append({"title": current_title, "content": content})

        for raw_line in lines:
            line = raw_line.strip()
            if not line:
                current_lines.append("")
                continue

            is_header = (
                line.startswith("##")
                or bool(NUMBERED_SECTION_RE.match(line))
                or bool(ALL_CAPS_RE.match(line))
            )
            if is_header:
                flush()
                current_title = line.lstrip("#").strip()
                current_lines = []
                continue

            current_lines.append(line)

        flush()
        return sections

    def classify_chunk(self, text: str) -> str:
        """Classify chunk_type using keyword/BM25 scoring (no LLM)."""
        lower = text.lower()

        # Exact keyword hits first.
        best_label = "challenge_language"
        best_hits = -1
        for label, keys in CHUNK_TYPE_KEYWORDS.items():
            hits = sum(1 for key in keys if key in lower)
            if hits > best_hits:
                best_hits = hits
                best_label = label

        if best_hits > 0:
            return best_label

        # BM25 fallback for weak/no direct phrase matches.
        tokens = self._tokenize(text)
        if not tokens:
            return "challenge_language"

        scores = self._bm25.get_scores(tokens)
        winner = max(range(len(scores)), key=lambda i: scores[i])
        return self._bm25_labels[winner]

    def detect_question_tags(self, text: str) -> List[str]:
        """Detect Q1-Q30 references; if none found return ['general']."""
        tags = {
            f"Q{m.group(1)}"
            for m in QUESTION_RE.finditer(text)
        }
        tags.update(
            f"Q{m.group(1)}"
            for m in QUESTION_WORD_RE.finditer(text)
        )

        if not tags:
            return ["general"]

        return sorted(tags, key=lambda x: int(x[1:]))

    @staticmethod
    def _detect_phase(text: str) -> str:
        m = PHASE_RE.search(text)
        if not m:
            return "general"
        return m.group(1).upper()

    @staticmethod
    def _detect_brand_type(text: str, metadata: Dict[str, Any]) -> str:
        if metadata.get("brand_type"):
            return str(metadata["brand_type"])

        lower = text.lower()
        for candidate in [
            "sage",
            "rebel",
            "hero",
            "creator",
            "caregiver",
            "ruler",
            "jester",
            "innocent",
            "everyman",
            "explorer",
            "magician",
            "lover",
        ]:
            if candidate in lower:
                return candidate

        return "unknown"

    @staticmethod
    def _detect_emotional_register(text: str, metadata: Dict[str, Any]) -> str:
        if metadata.get("emotional_register"):
            return str(metadata["emotional_register"])

        lower = text.lower()
        if any(k in lower for k in ["fear", "risk", "threat", "danger"]):
            return "high_tension"
        if any(k in lower for k in ["confidence", "clarity", "conviction", "certainty"]):
            return "confident"
        if any(k in lower for k in ["inspire", "dream", "hope", "possibility"]):
            return "aspirational"
        return "neutral"

    def chunk_document(self, pdf_path: str, metadata: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
        """
        Semantic chunking strategy:
        1) section boundary detection
        2) chunk type classification
        3) question tagging
        4) one sentence overlap for adjacent chunks in same section
        """
        meta = metadata or {}
        raw_text = self.extract_text(pdf_path)
        if not raw_text:
            return []

        sections = self.detect_sections(raw_text)
        chunks: List[Dict[str, Any]] = []
        source_name = Path(pdf_path).name

        for section_idx, section in enumerate(sections):
            paragraphs = [p.strip() for p in re.split(r"\n\s*\n", section["content"]) if p.strip()]
            if not paragraphs:
                continue

            prev_sentences: List[str] = []
            for para_idx, paragraph in enumerate(paragraphs):
                sentences = self._split_sentences(paragraph)
                overlap = prev_sentences[-1] if prev_sentences else ""
                text = f"{overlap} {paragraph}".strip() if overlap else paragraph
                prev_sentences = sentences

                question_ids = self.detect_question_tags(text)
                chunk_hash = hashlib.sha1(
                    f"{source_name}:{section_idx}:{para_idx}:{text}".encode("utf-8")
                ).hexdigest()[:16]

                chunk = {
                    "chunk_id": f"{source_name}-{chunk_hash}",
                    "text": text,
                    "chunk_type": self.classify_chunk(text),
                    "phase": self._detect_phase(text),
                    "question_id": question_ids,
                    "brand_type": self._detect_brand_type(text, meta),
                    "emotional_register": self._detect_emotional_register(text, meta),
                    "metadata": {
                        "source_file": source_name,
                        "source_path": str(pdf_path),
                        "section_title": section["title"],
                        "section_index": section_idx,
                        "paragraph_index": para_idx,
                    },
                }
                chunks.append(chunk)

        return chunks

    def embed_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not chunks:
            return chunks

        texts = [c["text"] for c in chunks]

        embeddings = with_azure_retry(
            lambda: self.embedding_service.generate_embeddings_batch(texts, batch_size=50),
            max_attempts=5,
            base_delay=2.0,
        )

        for chunk, vector in zip(chunks, embeddings):
            chunk["dense_vector"] = vector

        return chunks

    def ingest_to_es(self, chunks: List[Dict[str, Any]]) -> Dict[str, int]:
        if not chunks:
            return {"success": 0, "failed": 0}

        actions = []
        for chunk in chunks:
            payload = {
                "chunk_id": chunk["chunk_id"],
                "text": chunk["text"],
                "dense_vector": chunk["dense_vector"],
                "chunk_type": chunk["chunk_type"],
                "phase": chunk["phase"],
                "question_id": chunk["question_id"],
                "brand_type": chunk["brand_type"],
                "emotional_register": chunk["emotional_register"],
                "metadata": chunk.get("metadata", {}),
            }
            actions.append(
                {
                    "_index": BrandGodFatherBrandChunkDocument.Index.name,
                    "_id": chunk["chunk_id"],
                    "_source": payload,
                }
            )

        success, failed_items = bulk(self.es, actions, raise_on_error=False)
        failed = len(failed_items)
        if failed:
            logger.warning("BrandGodFather ingest completed with failures: success=%s failed=%s", success, failed)
        return {"success": success, "failed": failed}
