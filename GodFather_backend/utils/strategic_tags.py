"""
Strategic intent tagging for chunks and queries — improves retrieval precision.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Set

STRATEGIC_INTENTS = (
    "trust",
    "authority",
    "positioning",
    "premium",
    "differentiation",
    "emotional_branding",
    "manifesto",
    "brand_book",
    "audience_psychology",
)

# Intent → keyword signals (content + query detection)
INTENT_SIGNALS: Dict[str, tuple] = {
    "trust": (
        "trust", "credibility", "reliable", "integrity", "promise kept", "authenticity",
        "transparency", "loyalty",
    ),
    "authority": (
        "authority", "expert", "leadership", "command", "definitive", "expertise",
        "thought leader", "credibility",
    ),
    "positioning": (
        "position", "positioning", "category", "market space", "niche", "occupy",
        "own the", "frame",
    ),
    "premium": (
        "premium", "luxury", "exclusive", "exclusivity", "high-end", "prestige",
        "elite", "refined",
    ),
    "differentiation": (
        "differentiat", "unique", "distinct", "stand out", "only one", "competitor",
        "unlike", "separate",
    ),
    "emotional_branding": (
        "emotion", "feel", "felt", "connection", "story", "heart", "passion",
        "vivid", "human",
    ),
    "manifesto": (
        "manifesto", "brand book", "core belief", "brand promise", "principle", "dna",
        "non-negotiable", "foundation", "creed",
    ),
    "brand_book": (
        "brand book", "brand bible", "core belief", "brand promise", "principle", "dna",
    ),
    "audience_psychology": (
        "audience", "psychology", "persona", "customer mindset", "buyer", "motivation",
        "pain point", "desire", "identity", "emotional driver",
    ),
    "founder_story": (
        "founder", "origin story", "why we started", "founding", "journey",
        "personal narrative", "founder voice",
    ),
    "emotional_positioning": (
        "emotional positioning", "felt experience", "how we want to feel",
        "emotional territory", "brand feeling",
    ),
    "competitor": (
        "competitor", "competitive", "versus", "vs ", "price comparison",
        "market rival", "alternative brand",
    ),
    "positioning_archetype": (
        "archetype", "brand archetype", "ruler", "creator", "sage", "hero",
        "positioning frame", "category role",
    ),
    "market_enemy": (
        "competitor", "market enemy", "alternative", "versus", "vs ", "price war",
        "cheaper", "irrelevant competitor", "race to bottom",
    ),
    "status_signal": (
        "status", "prestige", "exclusivity", "elite", "premium signal", "luxury signal",
    ),
    "audience_fear": (
        "fear", "anxiety", "risk", "uncertainty", "doubt", "skepticism", "pain point",
    ),
    "audience_desire": (
        "desire", "aspiration", "want", "seeking", "motivation", "identity", "belonging",
    ),
    "identity_signal": (
        "identity", "who we are", "self-image", "persona", "buyer identity", "tribe",
    ),
}

_STRATEGIC_NOUNS = re.compile(
    r"\b(trust|authority|positioning|premium|differentiation|manifesto|"
    r"brand promise|consistency|narrative|emotion|credibility)\b",
    re.I,
)


def detect_strategic_tags(text: str, category: str = "") -> List[str]:
    """Tag chunk or query with strategic intents (0–4 tags)."""
    if not text:
        return []
    blob = f"{text} {category}".lower()
    tags: List[str] = []
    for intent, signals in INTENT_SIGNALS.items():
        if any(sig in blob for sig in signals):
            tags.append(intent)
    cat = (category or "").lower()
    if cat in ("manifesto", "brand_book", "brandbook") and "brand_book" not in tags:
        tags.append("brand_book")
        if "manifesto" not in tags:
            tags.append("manifesto")
    return tags[:4]


def detect_query_strategic_tags(query: str) -> List[str]:
    return detect_strategic_tags(query or "")


def strategic_tag_overlap_boost(query_tags: List[str], chunk_tags: List[str]) -> float:
    """
    Boost hybrid score when query intents align with chunk tags.
    Max boost ~0.12 (2+ overlapping tags).
    """
    if not query_tags or not chunk_tags:
        return 0.0
    qs: Set[str] = set(query_tags)
    cs: Set[str] = set(chunk_tags)
    overlap = len(qs & cs)
    weak = {
        "trust", "differentiation", "positioning", "audience_psychology",
        "emotional_branding", "market_enemy", "positioning_archetype",
        "audience_fear", "audience_desire", "identity_signal",
    }
    if overlap >= 2:
        return 0.14 if qs & weak else 0.12
    if overlap == 1:
        return 0.08 if qs & weak else 0.06
    return 0.0


def attach_strategic_tags(chunk: Dict[str, Any]) -> Dict[str, Any]:
    """Mutate chunk metadata with strategic_tags at index time."""
    meta = chunk.setdefault("metadata", {})
    text = chunk.get("text") or meta.get("content") or ""
    cat = meta.get("category") or chunk.get("category") or ""
    tags = detect_strategic_tags(text, cat)
    meta["strategic_tags"] = tags
    chunk["strategic_tags"] = tags
    return chunk


# Query intent → chunk signals that should be penalized (negative retrieval)
NEGATIVE_TAGS: Dict[str, tuple] = {
    "premium": ("viral", "cheap", "discount", "growth hack", "growth hacks", "tiktok", "meme", "trend chasing"),
    "trust": ("clickbait", "viral stunt", "growth hack", "fake urgency", "hype cycle"),
    "authority": ("meme", "viral trend", "clickbait", "casual slang", "growth hack"),
    "manifesto": ("seo trick", "algorithm hack", "growth hack", "viral marketing"),
    "positioning": ("me-too", "copy competitor", "race to bottom", "cheapest"),
    "differentiation": ("be like everyone", "generic marketing", "best practices only", "me too"),
    "audience_psychology": ("generic persona", "one size fits all", "everyone is our customer"),
    "competitor": ("copy competitor", "price war", "cheapest wins", "undercut"),
    "emotional_branding": ("manipulative urgency", "clickbait"),
}

NEGATIVE_TAG_PENALTY = 0.12


def negative_tag_penalty(query_tags: List[str], chunk_text: str, chunk_tags: List[str] = None) -> float:
    """
    Penalize hybrid score when chunk conflicts with query strategic intent.
    """
    if not query_tags:
        return 0.0
    blob = (chunk_text or "").lower()
    if chunk_tags:
        blob += " " + " ".join(chunk_tags).lower()

    penalty = 0.0
    for qtag in query_tags:
        negatives = NEGATIVE_TAGS.get(qtag, ())
        hits = sum(1 for n in negatives if n in blob)
        if hits:
            penalty += NEGATIVE_TAG_PENALTY * min(hits, 2)
    return min(penalty, 0.25)


def build_rerank_reasons(
    chunk: Dict[str, Any],
    query_tags: List[str],
    tag_boost: float = 0.0,
    generic_penalty: bool = False,
    negative_penalty: float = 0.0,
) -> List[str]:
    """Human-readable rerank explanations for debug panel."""
    reasons: List[str] = []
    meta = chunk.get("metadata") or {}
    cat = (meta.get("category") or "").lower()
    chunk_tags = meta.get("strategic_tags") or chunk.get("strategic_tags") or []

    if tag_boost > 0:
        overlap = set(query_tags) & set(chunk_tags)
        if overlap:
            reasons.append(f"strategic tag overlap ({', '.join(sorted(overlap))})")
    if cat == "manifesto":
        reasons.append("manifesto alignment")
    if chunk.get("strategic_tag_boost"):
        reasons.append("intent-weighted boost")
    rel = chunk.get("source_reliability")
    if rel and float(rel) >= 0.9:
        reasons.append("high source reliability")
    if chunk.get("_matched_concepts"):
        reasons.append("knowledge graph concept match")
    if float(chunk.get("cross_encoder_score") or 0) > 0.55:
        reasons.append("cross-encoder relevance")
    if generic_penalty:
        reasons.append("generic chunk penalized")
    if negative_penalty > 0:
        reasons.append("negative intent signal penalty")
    if not reasons:
        vs = chunk.get("vector_score")
        if vs and float(vs) > 0.5:
            reasons.append("semantic similarity")
        else:
            reasons.append("hybrid rank fusion")
    return reasons[:5]


def entity_density(text: str) -> float:
    """Rough strategic noun density 0–1."""
    words = re.findall(r"[a-z']+", (text or "").lower())
    if len(words) < 10:
        return 0.0
    hits = len(_STRATEGIC_NOUNS.findall(text or ""))
    return min(1.0, hits / max(len(words) / 20, 1))
