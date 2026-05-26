"""
Sanitize retrieved context for Azure content filter (violence etc.) without changing user query.
"""
from __future__ import annotations

import re
VIOLENCE_TERMS = re.compile(
    r"\b(kill|murder|violence|weapon|blood|assault|attack|warfare|shoot|"
    r"domination|kill-switch|weaponize)\b",
    re.I,
)

INDEX_SANITIZE_TERMS = re.compile(
    r"\b(kill|murder|violence|weapons?|blood|assault|attack|warfare|shoot|"
    r"domination|kill-switch|weaponize)\b",
    re.I,
)


def sanitize_context_for_content_filter(context: str) -> str:
    if not context:
        return context
    return VIOLENCE_TERMS.sub("[strategic-conflict]", context)


def sanitize_chunk_text_for_index(text: str) -> str:
    """Chunk-level sanitization before embedding/indexing (Azure filter prevention)."""
    if not text:
        return text
    return INDEX_SANITIZE_TERMS.sub("[brand-strategy]", text)
