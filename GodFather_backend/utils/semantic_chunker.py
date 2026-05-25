"""
Semantic chunking for Rag_doc knowledge files.

Splits by headings, principles, bullets, and paragraphs — not flat word windows.
Each chunk stores title, content, and category for better RAG retrieval.
"""
from __future__ import annotations

import re
import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Lines to drop (PDF/slide export noise)
_NOISE_LINE_PATTERNS = (
    re.compile(r"^Sharanya\s+Khemka\s*$", re.I),
    re.compile(r"^SynapseIndia\s*$", re.I),
    re.compile(r"^All Info from both\s*$", re.I),
)

# Markdown / structural headers
_MD_HEADER_RE = re.compile(r"^(#{1,6})\s+(.+)$")
_NUMBERED_SECTION_RE = re.compile(
    r"^(\d+[\.\)]\s+)(.+)$",
)
_PRINCIPLE_HEADER_RE = re.compile(
    r"^(?:principle|step|phase|part)\s*[#\d]*\s*[:\.\-]\s*(.+)$",
    re.I,
)
_PRINCIPLES_SECTION_RE = re.compile(
    r"^\d+\s+principles\b",
    re.I,
)
_SCENARIO_RE = re.compile(
    r"^(\d+[\.\)]\s*)(Crisis|Launch|Customer|Social|Blog|Training|Scenario|New\s)",
    re.I,
)
_BULLET_RE = re.compile(r"^[\-\*\u2022\u2013\u2014]\s+")
_LABEL_LINE_RE = re.compile(
    r"^(Input|Output|David's Pushback|Refined Answer|AI Training Notes|User Input)\s*$",
    re.I,
)

_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


def _is_noise_line(line: str) -> bool:
    s = line.strip()
    if not s or len(s) < 2:
        return True
    return any(p.match(s) for p in _NOISE_LINE_PATTERNS)


def _normalize_raw_text(text: str) -> str:
    """Merge soft line wraps, drop noise lines, normalize whitespace."""
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    cleaned: List[str] = []
    for line in lines:
        if _is_noise_line(line):
            continue
        cleaned.append(line.rstrip())

    merged: List[str] = []
    buf: List[str] = []

    def flush_buf():
        if buf:
            merged.append(" ".join(buf).strip())

    for i, line in enumerate(cleaned):
        stripped = line.strip()
        if not stripped:
            flush_buf()
            buf = []
            merged.append("")
            continue

        if not buf:
            buf.append(stripped)
            continue

        prev = buf[-1]
        # New block: empty line handled above; heading-like short line
        if _looks_like_heading(stripped) and len(stripped) < 100:
            flush_buf()
            buf = [stripped]
            continue

        # Continue same paragraph (PDF line wrap)
        if (
            prev
            and not prev.endswith((".", "!", "?", ":", ";", '"', "'"))
            and stripped[0].islower()
            and len(prev) < 120
        ):
            buf.append(stripped)
        elif len(prev) < 80 and not prev.endswith((".", "!", "?")):
            # Might be title continuation
            buf.append(stripped)
        else:
            flush_buf()
            buf = [stripped]

    flush_buf()
    return "\n".join(merged)


def _looks_like_heading(line: str) -> bool:
    s = line.strip()
    if len(s) < 3 or len(s) > 120:
        return False
    if _MD_HEADER_RE.match(s) or _NUMBERED_SECTION_RE.match(s):
        return True
    if _PRINCIPLE_HEADER_RE.match(s) or _SCENARIO_RE.match(s):
        return True
    if _LABEL_LINE_RE.match(s):
        return True
    # Title Case short line (2+ words, most capitalized)
    words = s.split()
    if 2 <= len(words) <= 12:
        caps = sum(1 for w in words if w[:1].isupper())
        if caps >= len(words) * 0.6 and not s.endswith("."):
            return True
    return False


def _split_oversized_content(
    title: str,
    content: str,
    max_words: int,
    overlap_words: int,
) -> List[Tuple[str, str]]:
    """Split long content by sentences; keep same title with part suffix."""
    words = content.split()
    if len(words) <= max_words:
        return [(title, content)]

    sentences = _SENTENCE_END.split(content.strip())
    sentences = [s.strip() for s in sentences if s.strip()]
    if not sentences:
        return [(title, content)]

    parts: List[str] = []
    current: List[str] = []
    current_len = 0

    for sent in sentences:
        sw = len(sent.split())
        if current_len + sw > max_words and current:
            parts.append(" ".join(current))
            # overlap: keep last sentences up to overlap_words
            overlap_sents: List[str] = []
            olen = 0
            for s in reversed(current):
                olen += len(s.split())
                overlap_sents.insert(0, s)
                if olen >= overlap_words:
                    break
            current = overlap_sents
            current_len = sum(len(s.split()) for s in current)
        current.append(sent)
        current_len += sw

    if current:
        parts.append(" ".join(current))

    if len(parts) <= 1:
        return [(title, content)]

    return [
        (f"{title} (part {i + 1})", part)
        for i, part in enumerate(parts)
    ]


def _make_chunk(
    title: str,
    content: str,
    category: str,
    chunk_type: str,
    extra_metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    title = (title or "General").strip()
    content = (content or "").strip()
    if not content or len(content) < 20:
        return None

    # Embed title + content so vector search matches section topics
    text = f"{title}\n\n{content}"

    metadata = {
        "title": title,
        "content": content,
        "category": category,
        "source": category,
        "chunk_type": chunk_type,
        "word_count": len(content.split()),
        **(extra_metadata or {}),
    }

    return {
        "chunk_id": 0,
        "text": text,
        "metadata": metadata,
        "document_id": 0,
        "page_number": 0,
    }


def _parse_bullet_block(lines: List[str]) -> Optional[Dict[str, Any]]:
    """Group consecutive bullet lines into one chunk."""
    bullets = []
    for line in lines:
        m = _BULLET_RE.match(line.strip())
        if m:
            bullets.append(_BULLET_RE.sub("", line.strip()).strip())
        elif line.strip():
            bullets.append(line.strip())
    if not bullets:
        return None
    content = "\n".join(f"• {b}" for b in bullets)
    return {"content": content, "chunk_type": "bullets"}


def _extract_md_sections(text: str) -> List[Tuple[str, str, str]]:
    """Return list of (title, body, chunk_type) from markdown headers."""
    sections: List[Tuple[str, str, str]] = []
    current_title = "Introduction"
    current_lines: List[str] = []
    chunk_type = "section"

    for line in text.split("\n"):
        hm = _MD_HEADER_RE.match(line.strip())
        if hm:
            body = "\n".join(current_lines).strip()
            if body:
                sections.append((current_title, body, chunk_type))
            level = len(hm.group(1))
            current_title = hm.group(2).strip()
            current_lines = []
            chunk_type = "heading" if level <= 2 else "subsection"
            continue
        current_lines.append(line)

    body = "\n".join(current_lines).strip()
    if body:
        sections.append((current_title, body, chunk_type))
    return sections


def _split_title_body_on_line(line: str) -> Tuple[str, str]:
    """
    Split merged PDF lines: 'Find & Live Your Brand DNA brands need a distinct...'
    → title + body on same physical line.
    """
    line = line.strip()
    if len(line) < 40:
        return line, ""

    words = line.split()
    if len(words) < 5:
        return line, ""

    _CONNECTORS = frozenset({
        "for", "and", "or", "the", "a", "an", "of", "in", "on", "to", "your", "&",
    })

    def _title_capital_count(prefix_words: List[str]) -> int:
        count = 0
        for w in prefix_words:
            clean = re.sub(r"^[^\w]+|[^\w]+$", "", w)
            if not clean:
                continue
            if clean[0].isupper() or clean in ("&",):
                count += 1
            elif clean.lower() in _CONNECTORS:
                continue
            else:
                break
        return count

    for i in range(3, min(len(words), 18)):
        w = words[i]
        if not w or not w[0].islower():
            continue
        if w.lower() in _CONNECTORS:
            continue
        title = " ".join(words[:i])
        body = " ".join(words[i:])
        if _title_capital_count(words[:i]) >= 3 and len(title) >= 12 and len(body) >= 20:
            return title, body

    return line, ""


def _is_title_continuation(line: str, accumulated_title: str) -> bool:
    """Next line is part of a wrapped multi-line heading."""
    s = line.strip()
    if not s or len(s) > 90:
        return False
    if s.endswith((".", "!", "?", ";")):
        return False
    if _BULLET_RE.match(s) or _NUMBERED_SECTION_RE.match(s):
        return False
    # Continuation: short fragment (e.g. "DNA" after "Find & Live Your Brand")
    return len(accumulated_title) < 100 and len(s.split()) <= 8


def _is_principle_continuation(line: str) -> bool:
    """Sentence that continues the previous principle (not a new titled block)."""
    s = line.strip()
    if not s or _split_title_body_on_line(s)[1]:
        return False
    if _PRINCIPLES_SECTION_RE.match(s) or _NUMBERED_SECTION_RE.match(s):
        return False
    words = s.split()
    if len(words) < 4:
        return False
    caps = sum(1 for w in words if w[:1].isupper())
    # e.g. "Being genuine matters more..." or "To succeed, you need..."
    if caps <= 2:
        return True
    if words[0].islower():
        return True
    return False


def _has_upcoming_title_body_principles(lines: List[str], index: int, window: int = 8) -> bool:
    """True when upcoming lines are 'Title Case... lowercase body' principle rows."""
    for j in range(index + 1, min(index + window, len(lines))):
        nxt = lines[j].strip()
        if not nxt:
            continue
        _, body = _split_title_body_on_line(nxt)
        if body:
            return True
    return False


def _looks_like_principle_title(line: str, lines: List[str], index: int) -> bool:
    """Title line for David-style principle blocks (short + body follows)."""
    s = line.strip()
    if not s or len(s) < 8 or len(s) > 140:
        return False
    if _BULLET_RE.match(s) or _LABEL_LINE_RE.match(s):
        return False
    if s.endswith(".") and len(s) > 60:
        return False

    # Must have following substantive content
    following = []
    for j in range(index + 1, min(index + 4, len(lines))):
        if lines[j].strip():
            following.append(lines[j].strip())
    if not following:
        return False

    if _looks_like_heading(s):
        return True

    # Title Case multi-word without ending period
    words = s.split()
    if 2 <= len(words) <= 14:
        caps = sum(1 for w in words if w[:1].isupper() or w in ("&", "-", "—"))
        if caps >= max(2, len(words) // 2) and not s.endswith("."):
            return True
    return False


def _split_line_stream(lines: List[str]) -> List[Tuple[str, str, str]]:
    """
    Line-by-line parser for principle/section documents (PDF exports).
    Each title + following body becomes one unit.
    """
    units: List[Tuple[str, str, str]] = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i].strip()
        if not line:
            i += 1
            continue

        if _BULLET_RE.match(line):
            bullet_lines = []
            while i < n and lines[i].strip() and (
                _BULLET_RE.match(lines[i].strip()) or bullet_lines
            ):
                if lines[i].strip() and not _BULLET_RE.match(lines[i].strip()):
                    if _looks_like_principle_title(lines[i].strip(), lines, i):
                        break
                bullet_lines.append(lines[i])
                i += 1
            parsed = _parse_bullet_block(bullet_lines)
            if parsed:
                units.append(("Key points", parsed["content"], "bullets"))
            continue

        if _PRINCIPLES_SECTION_RE.match(line):
            units.append((
                line,
                f"{line}. Core principles from David's branding framework.",
                "section",
            ))
            i += 1
            continue

        if _NUMBERED_SECTION_RE.match(line) or _SCENARIO_RE.match(line):
            title = line
            i += 1
            body_lines = []
            while i < n:
                nxt = lines[i].strip()
                if not nxt:
                    i += 1
                    if body_lines:
                        break
                    continue
                if _NUMBERED_SECTION_RE.match(nxt) or _SCENARIO_RE.match(nxt):
                    break
                if _looks_like_principle_title(nxt, lines, i) and body_lines:
                    break
                body_lines.append(lines[i])
                i += 1
            body = _normalize_paragraph("\n".join(body_lines))
            if body:
                units.append((title, body, "section"))
            continue

        if _LABEL_LINE_RE.match(line):
            label = line
            i += 1
            body_lines = []
            while i < n:
                nxt = lines[i].strip()
                if _LABEL_LINE_RE.match(nxt) or _looks_like_principle_title(nxt, lines, i):
                    break
                if not nxt:
                    i += 1
                    if body_lines:
                        break
                    continue
                body_lines.append(lines[i])
                i += 1
            body = _normalize_paragraph("\n".join(body_lines))
            if body:
                units.append((label, body, "labeled_block"))
            continue

        title_on_line, body_on_line = _split_title_body_on_line(line)
        if body_on_line:
            body_parts = [body_on_line]
            i += 1
            while i < n:
                nxt = lines[i].strip()
                if not nxt:
                    break
                if _split_title_body_on_line(nxt)[1]:
                    break
                if _PRINCIPLES_SECTION_RE.match(nxt) or _NUMBERED_SECTION_RE.match(nxt):
                    break
                if (
                    _looks_like_principle_title(nxt, lines, i)
                    and len(nxt.split()) >= 3
                    and not _is_principle_continuation(nxt)
                ):
                    break
                body_parts.append(nxt)
                i += 1
            units.append((
                title_on_line,
                _normalize_paragraph(" ".join(body_parts)),
                "principle",
            ))
            continue

        if _looks_like_principle_title(line, lines, i):
            _, inline_on_self = _split_title_body_on_line(line)
            if not inline_on_self and _has_upcoming_title_body_principles(lines, i):
                # Intro line before title+body principles — fall through to paragraph
                pass
            else:
                title = line
                i += 1
                while i < n and lines[i].strip() and _is_title_continuation(lines[i], title):
                    title = f"{title} {lines[i].strip()}"
                    i += 1
                body_lines = []
                if i < n:
                    _, inline_body = _split_title_body_on_line(lines[i].strip())
                    if inline_body:
                        body_lines.append(inline_body)
                        i += 1
                while i < n:
                    nxt = lines[i].strip()
                    if not nxt:
                        i += 1
                        if body_lines:
                            break
                        continue
                    _, split_body = _split_title_body_on_line(nxt)
                    if split_body:
                        break
                    if _looks_like_principle_title(nxt, lines, i):
                        break
                    if _NUMBERED_SECTION_RE.match(nxt) or _LABEL_LINE_RE.match(nxt):
                        break
                    body_lines.append(lines[i])
                    i += 1
                body = _normalize_paragraph("\n".join(body_lines))
                if body:
                    ctype = "principle" if re.search(
                        r"principle|dna|authenticity|brand|story|purpose|clarity|differentiation",
                        title,
                        re.I,
                    ) else "section"
                    units.append((title, body, ctype))
                continue

        # Plain paragraph (intro text before structured principles)
        para_lines = []
        start_i = i
        while i < n:
            nxt = lines[i].strip()
            if not nxt:
                break
            if _split_title_body_on_line(nxt)[1]:
                break
            if _looks_like_principle_title(nxt, lines, i) and not (
                i == start_i and _has_upcoming_title_body_principles(lines, i)
            ):
                break
            if _PRINCIPLES_SECTION_RE.match(nxt) or _NUMBERED_SECTION_RE.match(nxt):
                break
            para_lines.append(lines[i])
            i += 1
        if i < n and not lines[i].strip():
            i += 1
        if i == start_i:
            i += 1
        body = _normalize_paragraph("\n".join(para_lines))
        if body and len(body) > 40:
            units.append(("Overview", body, "paragraph"))

    return units


def _split_block_into_units(block: str) -> List[Tuple[str, str, str]]:
    """
    Split a text block into (title, content, chunk_type) units.
    Handles principles, numbered sections, label groups, bullets, paragraphs.
    """
    lines = block.split("\n")
    units: List[Tuple[str, str, str]] = []
    i = 0

    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue

        # Numbered section / scenario (e.g. "1. Crisis Response")
        nm = _NUMBERED_SECTION_RE.match(line)
        sm = _SCENARIO_RE.match(line)
        if nm or sm:
            title = (nm or sm).group(0).strip()
            i += 1
            body_lines = []
            while i < len(lines):
                nxt = lines[i].strip()
                if not nxt:
                    i += 1
                    if body_lines:
                        break
                    continue
                if _looks_like_heading(nxt) and _NUMBERED_SECTION_RE.match(nxt):
                    break
                if _NUMBERED_SECTION_RE.match(nxt) and len(nxt) < 80:
                    break
                body_lines.append(lines[i])
                i += 1
            body = _normalize_paragraph("\n".join(body_lines))
            if body:
                units.append((title, body, "principle" if "principle" in title.lower() else "section"))
            continue

        # Label + following content (manifesto scenarios)
        if _LABEL_LINE_RE.match(line):
            label = line
            i += 1
            body_lines = []
            while i < len(lines):
                nxt = lines[i].strip()
                if _LABEL_LINE_RE.match(nxt):
                    break
                if _looks_like_heading(nxt) and len(body_lines) > 0:
                    break
                body_lines.append(lines[i])
                i += 1
            body = _normalize_paragraph("\n".join(body_lines))
            if body:
                units.append((label, body, "labeled_block"))
            continue

        # Bullet run
        if _BULLET_RE.match(line):
            bullet_lines = []
            while i < len(lines) and (
                _BULLET_RE.match(lines[i].strip())
                or (lines[i].strip() and bullet_lines and not _looks_like_heading(lines[i].strip()))
            ):
                if lines[i].strip():
                    bullet_lines.append(lines[i])
                i += 1
            parsed = _parse_bullet_block(bullet_lines)
            if parsed:
                units.append(("Key points", parsed["content"], parsed["chunk_type"]))
            continue

        # Heading + following body (principle / section pattern)
        if _looks_like_heading(line):
            title = line
            i += 1
            body_lines = []
            while i < len(lines):
                nxt = lines[i].strip()
                if not nxt:
                    if body_lines:
                        i += 1
                        break
                    i += 1
                    continue
                if _looks_like_heading(nxt) and len(body_lines) > 0:
                    break
                if _NUMBERED_SECTION_RE.match(nxt):
                    break
                if _BULLET_RE.match(nxt) and body_lines:
                    break
                body_lines.append(lines[i])
                i += 1
            body = _normalize_paragraph("\n".join(body_lines))
            if body:
                ctype = "principle" if re.search(r"principle|dna|authenticity", title, re.I) else "section"
                units.append((title, body, ctype))
            elif len(title) > 10:
                units.append((title, title, "heading"))
            continue

        # Plain paragraph accumulation until blank or heading
        para_lines = []
        while i < len(lines):
            nxt = lines[i].strip()
            if not nxt:
                break
            if _looks_like_heading(nxt) and para_lines:
                break
            if _NUMBERED_SECTION_RE.match(nxt) and para_lines:
                break
            if _BULLET_RE.match(nxt) and para_lines:
                break
            para_lines.append(lines[i])
            i += 1
        if i < len(lines) and not lines[i].strip():
            i += 1
        body = _normalize_paragraph("\n".join(para_lines))
        if body and len(body) > 30:
            units.append(("Overview", body, "paragraph"))

    return units


def _normalize_paragraph(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\n", " ")).strip()


def semantic_chunk_document(
    raw_text: str,
    category: str,
    extra_metadata: Optional[Dict[str, Any]] = None,
    max_words: int = 350,
    overlap_words: int = 40,
) -> List[Dict[str, Any]]:
    """
    Chunk one document using semantic structure.
    Returns list of ES-ready chunk dicts with title/content in metadata.
    """
    if not raw_text or not raw_text.strip():
        return []

    normalized = _normalize_raw_text(raw_text)
    if not normalized.strip():
        return []

    all_units: List[Tuple[str, str, str]] = []

    # Markdown files: split on # headers first
    if "#" in normalized and _MD_HEADER_RE.search(normalized):
        md_sections = _extract_md_sections(normalized)
        for title, body, ctype in md_sections:
            all_units.extend(_split_block_into_units(f"{title}\n{body}"))
    else:
        # Primary: line-stream parser (best for PDF-export training docs)
        lines = normalized.split("\n")
        stream_units = _split_line_stream(lines)
        if stream_units:
            all_units.extend(stream_units)
        else:
            blocks = re.split(r"\n\s*\n+", normalized)
            for block in blocks:
                block = block.strip()
                if len(block) < 25:
                    continue
                all_units.extend(_split_block_into_units(block))

    if not all_units:
        all_units = [("Document", _normalize_paragraph(normalized), "paragraph")]

    chunks: List[Dict[str, Any]] = []
    for title, content, chunk_type in all_units:
        for part_title, part_content in _split_oversized_content(
            title, content, max_words, overlap_words
        ):
            chunk = _make_chunk(
                part_title,
                part_content,
                category,
                chunk_type,
                extra_metadata,
            )
            if chunk:
                chunks.append(chunk)

    return chunks
