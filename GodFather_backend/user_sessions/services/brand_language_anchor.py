"""
Brand language anchoring — signature phrases and vocabulary from brand book chunks.
"""
from __future__ import annotations

import re
from collections import Counter
from typing import Any, Dict, List

SIGNATURE_PATTERNS = (
    re.compile(r"\b(quiet authority|crafted precision|earned credibility|"
               r"premium craftsmanship|strategic restraint|brand promise|"
               r"core belief|non-negotiable|brand dna|emotional connection)\b", re.I),
    re.compile(r"\b([A-Z][a-z]+(?:\s+[a-z]+){1,3})\b"),
)

MANDATORY_TONE_RULES = """
MANDATORY TONE ANCHORING (luxury / premium brand book):
- DISALLOW in answers: viral, hack, dominate, aggressive growth, hustle, 10x, meme marketing.
- REQUIRE framing toward: precision, craftsmanship, quiet authority, enduring trust, earned credibility.
- Reuse signature phrases from BRAND LANGUAGE ANCHOR below when they appear in retrieved context.
"""

GENERIC_REPLACEMENTS = {
    "build trust": "earned credibility",
    "be authentic": "quiet authority",
    "stand out": "crafted differentiation",
    "engage your audience": "deep emotional connection",
    "deliver value": "strategic promise kept",
    "focus on quality": "crafted precision",
    "world-class": "premium standard",
    "best practices": "brand-book principles",
    "customer-centric": "audience psychology aligned",
    "drive growth": "strategic restraint growth",
    "leverage": "apply",
    "holistic": "integrated brand cognition",
    "unique value proposition": "distinct brand promise",
}


def extract_brand_language_anchors(
    chunks: List[Dict[str, Any]],
    context: str = "",
    max_phrases: int = 12,
) -> Dict[str, Any]:
    """Extract signature phrases, vocabulary, cadence hints from retrieved chunks."""
    phrase_counts: Counter = Counter()
    vocab: Counter = Counter()

    for ch in chunks or []:
        text = ch.get("text") or ""
        for pat in SIGNATURE_PATTERNS:
            for m in pat.finditer(text):
                p = m.group(0).strip()
                if 8 < len(p) < 60:
                    phrase_counts[p.lower()] += 1
        for w in re.findall(r"\b[a-z]{5,}\b", text.lower()):
            if w not in {"should", "would", "their", "which", "about", "brand", "strategy"}:
                vocab[w] += 1

    ctx_phrases = []
    for pat in SIGNATURE_PATTERNS[:1]:
        for m in pat.finditer(context or ""):
            ctx_phrases.append(m.group(0).strip())

    signature_phrases = [p for p, _ in phrase_counts.most_common(max_phrases)]
    top_vocab = [w for w, _ in vocab.most_common(15)]

    return {
        "signature_phrases": list(dict.fromkeys(signature_phrases + ctx_phrases))[:max_phrases],
        "vocabulary_patterns": top_vocab,
        "generic_replacements": dict(GENERIC_REPLACEMENTS),
        "cadence": "short declarative sentences; restrained adjectives; principle-first",
    }


def format_mandatory_tone_rules() -> str:
    return f"\n{MANDATORY_TONE_RULES}\n"


def format_language_anchor_prompt(anchors: Dict[str, Any]) -> str:
    phrases = ", ".join(anchors.get("signature_phrases") or [])[:400]
    vocab = ", ".join(anchors.get("vocabulary_patterns") or [])[:200]
    base = format_mandatory_tone_rules()
    if not phrases and not vocab:
        return base
    return (
        base
        + "\nBRAND LANGUAGE ANCHOR (MANDATORY reuse where natural — do not invent new slogans):\n"
        f"- Signature phrases: {phrases or 'use brand book wording'}\n"
        f"- Preferred vocabulary: {vocab}\n"
        f"- Cadence: {anchors.get('cadence', 'restrained, authoritative')}\n"
        "- Avoid generic marketing filler; prefer anchored phrases above.\n"
    )


def apply_generic_phrase_replacements(answer: str, anchors: Dict[str, Any]) -> str:
    """Post-process: swap common generic phrases for anchored language when present."""
    replacements = {**GENERIC_REPLACEMENTS, **(anchors.get("generic_replacements") or {})}
    text = answer
    modified = False
    for generic, anchored in replacements.items():
        if generic in text.lower() and anchored:
            pattern = re.compile(re.escape(generic), re.I)
            if pattern.search(text):
                text = pattern.sub(anchored, text, count=1)
                modified = True
    return text, modified
