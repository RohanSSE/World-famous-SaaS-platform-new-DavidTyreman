"""
Penalize generic / low-information chunks at retrieval time.
"""
from __future__ import annotations

import re
from typing import Any, Dict, Tuple

from django.conf import settings

from .strategic_tags import entity_density

GENERIC_MARKETING_PHRASES = (
    "best practices",
    "world-class",
    "customer-centric",
    "deliver value",
    "engage your audience",
    "strong brand presence",
    "focus on quality",
    "be authentic",
    "build trust",
    "stand out",
    "unique value proposition",
    "drive growth",
    "leverage",
    "synergy",
    "holistic approach",
)


def is_generic_chunk(chunk: Dict[str, Any]) -> Tuple[bool, str]:
    """
    True if chunk is broad marketing filler with weak strategic substance.
    """
    text = (chunk.get("text") or "").strip()
    meta = chunk.get("metadata") or {}
    title = (meta.get("title") or "").lower()

    if len(text) < 80:
        return False, ""

    lower = text.lower()
    generic_hits = sum(1 for p in GENERIC_MARKETING_PHRASES if p in lower)
    density = entity_density(text)

    # High generic phrase count + low strategic noun density
    if generic_hits >= 2 and density < 0.20:
        return True, "generic_phrases"

    if generic_hits >= 1 and density < 0.12:
        return True, "thin_generic"

    if generic_hits >= 1 and density < 0.18 and len(text) < 500:
        return True, "short_generic"

    # Title-only / overview noise
    if any(w in title for w in ("overview", "introduction", "summary")) and density < 0.1:
        if generic_hits >= 1:
            return True, "overview_generic"

    # Repetitive vague tokens
    words = re.findall(r"[a-z']+", lower)
    if words:
        unique_ratio = len(set(words)) / len(words)
        if unique_ratio < 0.35 and generic_hits >= 1:
            return True, "repetitive_vague"

    return False, ""


def apply_generic_chunk_penalty(chunk: Dict[str, Any]) -> Dict[str, Any]:
    """Subtract penalty from hybrid_score when chunk is generic."""
    penalty = float(getattr(settings, "GENERIC_CHUNK_PENALTY", 0.15))
    is_generic, reason = is_generic_chunk(chunk)
    if not is_generic:
        return chunk

    c = dict(chunk)
    base = float(c.get("hybrid_score") or c.get("score") or 0)
    if base > 0:
        adjusted = max(0.0, base - penalty)
        c["hybrid_score"] = round(adjusted, 4)
        c["score"] = adjusted
        c["rrf_score"] = adjusted
    c["generic_chunk_penalty"] = True
    c["generic_penalty_reason"] = reason
    return c
