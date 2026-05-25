"""
Strategic context orchestration — compose context window intentionally (not top-k only).
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from django.conf import settings

from user_sessions.services.rag_intelligence import detect_query_intent
from utils.strategic_tags import STRATEGIC_INTENTS, detect_query_strategic_tags, entity_density

# Context slot roles (knowledge chunks) — defaults; profiles override per intent
CONTEXT_ROLES = {
    "anchor_manifesto": 3,
    "strategic_support": 2,
    "memory_alignment": 1,
}

STRATEGIC_INTENTS = frozenset(
    {"trust", "authority", "positioning", "differentiation", "premium", "manifesto"}
)

STRATEGIC_CATEGORIES = frozenset(
    {"manifesto", "branding", "positioning", "strategy", "strategic", "psychology"}
)

# Conflicting signals across chunks in same context window
CONTEXT_CONFLICT_PAIRS = (
    ("premium", "viral"),
    ("premium", "growth hack"),
    ("trust", "clickbait"),
    ("craftsmanship", "speed"),
    ("authority", "meme"),
    ("restraint", "aggressive growth"),
    ("consistency", "pivot weekly"),
)

STRATEGIC_SENTENCE_MARKERS = re.compile(
    r"\b(trust|manifesto|positioning|premium|authority|differentiation|promise|"
    r"consistency|credibility|narrative|principle|dna|emotional|brand)\b",
    re.I,
)

GENERIC_SENTENCE_MARKERS = re.compile(
    r"\b(be authentic|best practices|engage your audience|build trust|"
    r"world-class|customer-centric|deliver value|stand out)\b",
    re.I,
)


def is_strategic_query(query: str, intent: Optional[str] = None) -> bool:
    intent = intent or detect_query_intent(query)
    if intent in ("manifesto", "trust", "positioning", "differentiation"):
        return True
    tags = set(detect_query_strategic_tags(query))
    return bool(tags & STRATEGIC_INTENTS)


def _chunk_category(chunk: Dict[str, Any]) -> str:
    meta = chunk.get("metadata") or {}
    return (meta.get("category") or chunk.get("category") or "").lower().strip()


def _is_manifesto_chunk(chunk: Dict[str, Any]) -> bool:
    """Brand book anchor chunk (client rename; index category may still be manifesto)."""
    cat = _chunk_category(chunk)
    if cat in ("manifesto", "brand_book", "brandbook") or "brand book" in cat:
        return True
    if chunk.get("_context_role") == "anchor_manifesto":
        return True
    tags = (chunk.get("metadata") or {}).get("strategic_tags") or chunk.get("strategic_tags") or []
    return "manifesto" in tags or "brand_book" in tags


def _chunk_score(chunk: Dict[str, Any]) -> float:
    return float(chunk.get("hybrid_score") or chunk.get("score") or chunk.get("rrf_score") or 0)


def manifesto_alignment_score(chunk: Dict[str, Any]) -> float:
    """0–1 how strongly chunk carries manifesto / identity signal."""
    cat = _chunk_category(chunk)
    text = (chunk.get("text") or "").lower()
    meta = chunk.get("metadata") or {}
    tags = meta.get("strategic_tags") or chunk.get("strategic_tags") or []

    score = 0.0
    if cat in ("manifesto", "brand_book", "brandbook") or "brand book" in cat:
        score += 0.55
    if "manifesto" in tags or "brand_book" in tags:
        score += 0.25
    score += min(0.25, entity_density(text) * 0.5)
    if any(w in text for w in ("principle", "promise", "dna", "core belief", "non-negotiable")):
        score += 0.15
    return round(min(1.0, score), 3)


def apply_manifesto_first_scoring(
    chunks: List[Dict[str, Any]],
    query: str,
    strategic: Optional[bool] = None,
) -> List[Dict[str, Any]]:
    """
    final = hybrid * w_h + manifesto_alignment * w_m  (strategic queries only)
    """
    strategic = strategic if strategic is not None else is_strategic_query(query)
    if not strategic or not chunks:
        return chunks

    w_h = float(getattr(settings, "MANIFESTO_FIRST_HYBRID_WEIGHT", 0.65))
    w_m = float(getattr(settings, "MANIFESTO_FIRST_ALIGNMENT_WEIGHT", 0.35))

    rescored = []
    for c in chunks:
        item = dict(c)
        hybrid = _chunk_score(item)
        align = manifesto_alignment_score(item)
        final = hybrid * w_h + align * w_m
        item["manifesto_alignment"] = align
        item["hybrid_score"] = round(final, 4)
        item["score"] = item["hybrid_score"]
        item["rrf_score"] = item["hybrid_score"]
        reasons = list(item.get("rerank_reason") or [])
        if align >= 0.5 and "manifesto-first scoring" not in reasons:
            reasons.insert(0, "manifesto-first scoring")
        item["rerank_reason"] = reasons[:6]
        rescored.append(item)

    rescored.sort(key=_chunk_score, reverse=True)
    return rescored


def _is_generic_chunk(chunk: Dict[str, Any]) -> bool:
    from utils.chunk_generic_penalty import is_generic_chunk

    flagged, _ = is_generic_chunk(chunk)
    return flagged or bool(chunk.get("generic_chunk_penalty"))


def compose_strategic_chunks(
    pool: List[Dict[str, Any]],
    query: str,
    strategic: Optional[bool] = None,
    memory_snippets: Optional[List[str]] = None,
    context_roles: Optional[Dict[str, int]] = None,
    profile_name: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Role-based context composition (not pure top-k).
    Returns (selected_chunks, composition_meta).
    """
    strategic = strategic if strategic is not None else is_strategic_query(query)
    if context_roles is None:
        from user_sessions.services.context_profiles import get_context_roles_for_query

        profile_name, context_roles = get_context_roles_for_query(query)
    roles = dict(context_roles or CONTEXT_ROLES)
    min_manifesto = int(roles.get("anchor_manifesto", getattr(settings, "MIN_MANIFESTO_CHUNKS", 2)))
    max_slots = sum(roles.values()) + int(roles.get("evidence", 0))

    if not pool:
        return [], {"strategic_query": strategic, "roles_filled": {}}

    pool_sorted = sorted(pool, key=_chunk_score, reverse=True)
    manifesto = [c for c in pool_sorted if _is_manifesto_chunk(c)]
    min_support_align = float(
        getattr(settings, "MIN_STRATEGIC_SUPPORT_ALIGNMENT", 0.35)
    )
    strategic_support = [
        c
        for c in pool_sorted
        if _chunk_category(c) in STRATEGIC_CATEGORIES
        and not _is_manifesto_chunk(c)
        and not _is_generic_chunk(c)
        and manifesto_alignment_score(c) >= min_support_align
    ]
    if not strategic_support:
        strategic_support = [
            c
            for c in pool_sorted
            if _chunk_category(c) in STRATEGIC_CATEGORIES
            and not _is_manifesto_chunk(c)
            and not _is_generic_chunk(c)
        ]
    other = [
        c
        for c in pool_sorted
        if c not in manifesto and c not in strategic_support and not _is_generic_chunk(c)
    ]

    from utils.hybrid_retrieval import _chunk_key

    selected: List[Dict[str, Any]] = []
    used_keys: set = set()

    def _take(source: List[Dict], n: int, role: str):
        count = 0
        for c in source:
            key = _chunk_key(c)
            if key in used_keys:
                continue
            item = dict(c)
            item["_context_role"] = role
            selected.append(item)
            used_keys.add(key)
            count += 1
            if count >= n:
                break
        return count

    roles_filled: Dict[str, int] = {}

    if strategic:
        roles_filled["anchor_manifesto"] = _take(manifesto, min_manifesto, "anchor_manifesto")
        # If not enough manifesto in pool, take best-scoring with manifesto tag
        if roles_filled["anchor_manifesto"] < min_manifesto:
            tagged = [
                c
                for c in pool_sorted
                if _chunk_key(c) not in used_keys
                and "manifesto" in (c.get("metadata") or {}).get("strategic_tags", [])
            ]
            roles_filled["anchor_manifesto"] += _take(
                tagged, min_manifesto - roles_filled["anchor_manifesto"], "anchor_manifesto"
            )

        roles_filled["strategic_support"] = _take(
            strategic_support, roles.get("strategic_support", 2), "strategic_support"
        )
        if roles.get("evidence"):
            roles_filled["evidence"] = _take(other, roles.get("evidence", 0), "evidence")

        # Memory-aligned chunk: session overlap when available, else best strategic/non-generic
        mem_slots = int(roles.get("memory_alignment", 0))
        if mem_slots:
            mem_blob = " ".join(memory_snippets or []).lower()
            if mem_blob:
                aligned = sorted(
                    [c for c in pool_sorted if _chunk_key(c) not in used_keys],
                    key=lambda c: (
                        -sum(
                            1
                            for w in mem_blob.split()[:40]
                            if len(w) > 4 and w in (c.get("text") or "").lower()
                        )
                    ),
                )
                roles_filled["memory_alignment"] = _take(
                    aligned, mem_slots, "memory_alignment"
                )
            if roles_filled.get("memory_alignment", 0) < mem_slots:
                mem_fallback = [
                    c
                    for c in strategic_support + other
                    if _chunk_key(c) not in used_keys and not _is_generic_chunk(c)
                ]
                roles_filled["memory_alignment"] = roles_filled.get("memory_alignment", 0) + _take(
                    mem_fallback,
                    mem_slots - roles_filled.get("memory_alignment", 0),
                    "memory_alignment",
                )
    else:
        roles_filled["anchor_manifesto"] = _take(manifesto, 1, "anchor_manifesto")
        roles_filled["strategic_support"] = _take(
            strategic_support, roles["strategic_support"], "strategic_support"
        )

    # Fill remaining slots by score
    remaining = max_slots - len(selected)
    if remaining > 0:
        for c in pool_sorted:
            key = _chunk_key(c)
            if key in used_keys:
                continue
            item = dict(c)
            item["_context_role"] = item.get("_context_role", "supporting")
            selected.append(item)
            used_keys.add(key)
            remaining -= 1
            if remaining <= 0:
                break

    # Order: manifesto anchors first, then strategic support, then rest
    role_order = {
        "anchor_manifesto": 0,
        "strategic_support": 1,
        "memory_alignment": 2,
        "supporting": 3,
    }
    selected.sort(key=lambda c: (role_order.get(c.get("_context_role"), 9), -_chunk_score(c)))

    return selected, {
        "strategic_query": strategic,
        "context_profile": profile_name or "default",
        "roles_filled": roles_filled,
        "context_roles": roles,
        "pool_size": len(pool),
        "selected_count": len(selected),
    }


def score_context_density(context: str) -> float:
    """
    strategic_density = strategic sentences / total sentences
    Target > 0.70
    """
    sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", (context or "").strip()) if len(s.strip()) > 15]
    if not sents:
        return 0.0
    strategic = sum(1 for s in sents if STRATEGIC_SENTENCE_MARKERS.search(s))
    generic = sum(1 for s in sents if GENERIC_SENTENCE_MARKERS.search(s))
    strategic = max(0, strategic - generic // 2)
    return round(min(1.0, strategic / len(sents)), 3)


def score_context_conflict(chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Detect incompatible strategic poles across chunks in the same window.
  """
    texts = [(c.get("text") or "").lower() for c in chunks[:6]]
    conflicts: List[Dict[str, str]] = []
    for pole_a, pole_b in CONTEXT_CONFLICT_PAIRS:
        has_a = any(pole_a in t for t in texts)
        has_b = any(pole_b in t for t in texts)
        if has_a and has_b:
            conflicts.append({"pole_a": pole_a, "pole_b": pole_b})

    score = min(1.0, len(conflicts) * 0.25)
    return {
        "context_conflict_score": round(score, 3),
        "context_conflicts": conflicts,
        "has_conflict": bool(conflicts),
    }


def score_context_coherence(chunks: List[Dict[str, Any]]) -> float:
    """1.0 = no conflicts; lower when chunks fight each other."""
    conflict = score_context_conflict(chunks)
    return round(max(0.0, 1.0 - conflict["context_conflict_score"]), 3)


def validate_context_quality(
    selected: List[Dict[str, Any]],
    pool: List[Dict[str, Any]],
    context_text: str,
    query: str,
    strategic: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    Pre-generation quality gate. Expand manifesto slots if below thresholds.
    """
    from utils.hybrid_retrieval import _chunk_key

    strategic = strategic if strategic is not None else is_strategic_query(query)
    min_dom = float(getattr(settings, "CONTEXT_MIN_MANIFESTO_DOMINANCE", 0.40))
    min_density = float(getattr(settings, "CONTEXT_MIN_STRATEGIC_DENSITY", 0.60))
    min_manifesto = int(getattr(settings, "MIN_MANIFESTO_CHUNKS", 2))

    working = list(selected)
    if not context_text and working:
        context_text = format_composed_context(working)
    manifesto_count = sum(1 for c in working if _is_manifesto_chunk(c))
    dominance = manifesto_count / max(len(working), 1)
    density = score_context_density(context_text)
    conflict = score_context_conflict(working)
    regenerated = False

    if strategic and dominance < min_dom:
        pool_manifesto = [c for c in sorted(pool, key=_chunk_score, reverse=True) if _is_manifesto_chunk(c)]
        used = {_chunk_key(c) for c in working}
        for c in pool_manifesto:
            if _chunk_key(c) in used:
                continue
            item = dict(c)
            item["_context_role"] = "anchor_manifesto"
            working.insert(0, item)
            used.add(_chunk_key(c))
            manifesto_count += 1
            regenerated = True
            if manifesto_count >= min_manifesto and manifesto_count / len(working) >= min_dom:
                break
        # Drop lowest non-manifesto if over slot budget
        max_slots = sum(CONTEXT_ROLES.values())
        while len(working) > max_slots:
            for i in range(len(working) - 1, -1, -1):
                if not _is_manifesto_chunk(working[i]):
                    working.pop(i)
                    break
            else:
                working.pop()

    context_text = format_composed_context(working)
    density = score_context_density(context_text)

    if strategic and density < min_density:
        extra = [
            c
            for c in sorted(pool, key=_chunk_score, reverse=True)
            if _chunk_category(c) in STRATEGIC_CATEGORIES
            and _chunk_key(c) not in {_chunk_key(x) for x in working}
        ]
        for c in extra[:2]:
            item = dict(c)
            item["_context_role"] = "strategic_support"
            working.append(item)
            regenerated = True
        context_text = format_composed_context(working)
        density = score_context_density(context_text)

    manifesto_count = sum(1 for c in working if _is_manifesto_chunk(c))
    dominance = manifesto_count / max(len(working), 1)
    coherence = score_context_coherence(working)

    passed = True
    if strategic:
        passed = dominance >= min_dom and density >= min_density * 0.85

    return {
        "passed": passed,
        "regenerated": regenerated,
        "manifesto_dominance": round(dominance, 3),
        "strategic_density": density,
        "context_coherence": coherence,
        **conflict,
        "chunks": working,
        "context_text": context_text,
        "full_verify_required": conflict["has_conflict"],
    }


def repair_context(
    selected: List[Dict[str, Any]],
    pool: List[Dict[str, Any]],
    context_quality: Dict[str, Any],
    query: str,
    strategic: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    Autonomous context optimization — remove conflicts, replace generic chunks, inject manifesto.
    """
    from utils.hybrid_retrieval import _chunk_key

    strategic = strategic if strategic is not None else is_strategic_query(query)
    working = list(selected)
    repairs: List[str] = []
    conflict_score = float(context_quality.get("context_conflict_score") or 0)
    dominance = float(context_quality.get("manifesto_dominance") or 0)
    conflict_threshold = float(getattr(settings, "CONTEXT_REPAIR_CONFLICT_THRESHOLD", 0.30))
    manifesto_threshold = float(getattr(settings, "CONTEXT_REPAIR_MANIFESTO_THRESHOLD", 0.50))

    # Remove chunks that participate in detected conflicts (keep manifesto anchors)
    conflicts = context_quality.get("context_conflicts") or []
    if conflict_score > conflict_threshold and conflicts:
        poles_to_strip = set()
        for c in conflicts:
            poles_to_strip.add(c.get("pole_b", ""))
        new_working = []
        for chunk in working:
            text = (chunk.get("text") or "").lower()
            is_anchor = chunk.get("_context_role") == "anchor_manifesto"
            has_bad_pole = any(p and p in text for p in poles_to_strip if p not in ("trust", "premium", "authority"))
            if has_bad_pole and not is_anchor:
                repairs.append(f"removed_conflict_chunk:{_chunk_key(chunk)[:40]}")
                continue
            new_working.append(chunk)
        working = new_working

    # Replace generic chunks with strategic/manifesto from pool
    generic_indices = [i for i, c in enumerate(working) if _is_generic_chunk(c)]
    if generic_indices:
        replacements = [
            c
            for c in sorted(pool, key=_chunk_score, reverse=True)
            if not _is_generic_chunk(c) and _chunk_key(c) not in {_chunk_key(x) for x in working}
        ]
        for idx, gen_idx in enumerate(generic_indices):
            if idx < len(replacements):
                rep = dict(replacements[idx])
                rep["_context_role"] = working[gen_idx].get("_context_role", "strategic_support")
                working[gen_idx] = rep
                repairs.append("replaced_generic_chunk")

    # Inject manifesto if dominance still low
    if strategic and dominance < manifesto_threshold:
        used = {_chunk_key(c) for c in working}
        for c in sorted(pool, key=_chunk_score, reverse=True):
            if not _is_manifesto_chunk(c) or _chunk_key(c) in used:
                continue
            item = dict(c)
            item["_context_role"] = "anchor_manifesto"
            working.insert(0, item)
            used.add(_chunk_key(c))
            repairs.append("injected_manifesto")
            manifesto_count = sum(1 for x in working if _is_manifesto_chunk(x))
            if manifesto_count / max(len(working), 1) >= manifesto_threshold:
                break
        max_slots = sum(CONTEXT_ROLES.values())
        while len(working) > max_slots:
            for i in range(len(working) - 1, -1, -1):
                if not _is_manifesto_chunk(working[i]):
                    working.pop(i)
                    break
            else:
                working.pop()

    context_text = format_composed_context(working)
    updated_quality = validate_context_quality(working, pool, context_text, query, strategic=strategic)
    updated_quality["repairs_applied"] = repairs
    updated_quality["context_repaired"] = bool(repairs)

    return updated_quality


def format_composed_context(chunks: List[Dict[str, Any]], max_chars: int = None) -> str:
    """Format role-ordered chunks for GPT context block."""
    from utils.retrieve_ai_knowledge import format_knowledge_context

    max_chars = max_chars or int(getattr(settings, "MAX_CONTEXT_CHARS", 6000))
    if not chunks:
        return ""

    parts = []
    for c in chunks:
        role = c.get("_context_role", "supporting")
        meta = c.get("metadata") or {}
        title = meta.get("title", "")
        prefix = f"[{role}]"
        if title:
            c = dict(c)
            meta = dict(meta)
            meta["title"] = f"{prefix} {title}"
            c["metadata"] = meta
        parts.append(c)

    return format_knowledge_context(parts, max_chars=max_chars)
