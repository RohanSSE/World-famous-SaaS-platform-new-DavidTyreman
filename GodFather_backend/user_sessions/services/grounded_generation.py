"""
Grounded strategic reasoning — claim fidelity, context mirroring, unsupported suppression.

Phase: Groundedness & Hallucination Suppression Sprint.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from django.conf import settings

from .rag_evaluation import _sentences, _token_set

# Strict grounded generation mode (pre-final answer)
GROUNDING_CONSTRAINTS: Dict[str, bool] = {
    "every_major_claim_must_map_to_context": True,
    "avoid_unattributed_strategy_claims": True,
    "avoid_extrapolated_business_assertions": True,
    "prefer_context_language": True,
}

BRAND_BOOK_LABEL = "brand book"

# Categories/tags treated as brand book (client rename; index may still use manifesto)
BRAND_BOOK_CATEGORIES = frozenset({"manifesto", "brand_book", "brandbook", "brand book"})

DEFINITIVE_STRATEGIC_PATTERNS = re.compile(
    r"\b(you must|you should always|always|never|guaranteed|definitely will|"
    r"the only way|without exception|every brand must|will certainly)\b",
    re.I,
)

HEDGE_PREFIX = "The retrieved positioning suggests "

FORBIDDEN_GENERIC_CLAIM_PHRASES = (
    "build trust",
    "be authentic",
    "connect with audience",
    "connect with your audience",
    "focus on value",
    "deliver value",
    "engage your audience",
    "world-class",
    "best practices",
    "customer-centric",
    "unique value proposition",
    "drive growth",
    "leverage",
    "holistic approach",
)

EMOTIONAL_VOCAB_PATTERN = re.compile(
    r"\b(restraint|crafted|quiet authority|premium|trust|precision|enduring|"
    r"confidence|exclusivity|manifesto|brand promise|differentiation)\b",
    re.I,
)


def is_brand_book_category(category: str) -> bool:
    return (category or "").lower().strip().replace(" ", "_") in {
        "manifesto",
        "brand_book",
        "brandbook",
    } or "brand book" in (category or "").lower()


def build_grounding_constraints_prompt(
    constraints: Optional[Dict[str, bool]] = None,
    context_phrases: Optional[List[str]] = None,
) -> str:
    """Inject before draft / repair — forces answer fidelity to retrieved context."""
    c = {**GROUNDING_CONSTRAINTS, **(constraints or {})}
    lines = [
        "GROUNDED STRATEGIC REASONING (mandatory):",
        "- Every major recommendation MUST map to a phrase or principle in RETRIEVED KNOWLEDGE.",
        "- Do NOT add business assertions, guarantees, or strategy claims absent from context.",
        "- Prefer exact terminology from the brand book / positioning excerpts (light paraphrase only).",
        '- When evidence is partial, use: "it appears", "the retrieved positioning suggests".',
        "- Do NOT use: must, always, guaranteed, definitive claims unless the same wording exists in context.",
        "- Suppress generic marketing filler; reuse brand-book phrases from context verbatim where possible.",
        "- Each paragraph needs at least one traceable phrase from RETRIEVED KNOWLEDGE.",
    ]
    if c.get("prefer_context_language"):
        lines.append(
            "- Reuse key phrases from retrieved chunks (brand book language, positioning terms)."
        )
    if context_phrases:
        sample = "; ".join(context_phrases[:8])
        lines.append(f"- Mirror vocabulary where natural: {sample}")
    return "\n".join(lines)


def extract_context_phrases(context: str, chunks: Optional[List[Dict[str, Any]]] = None) -> List[str]:
    """Key phrases from context for mirroring bias."""
    phrases: List[str] = []
    text = context or ""
    for m in re.finditer(
        r"\b([A-Z][a-z]+(?:\s+[A-Z]?[a-z]+){0,4})\b|"
        r"(brand book|positioning|differentiation|trust|premium|authority|promise|DNA|consistency)",
        text,
        re.I,
    ):
        p = m.group(0).strip()
        if len(p) > 4 and p.lower() not in phrases:
            phrases.append(p if p[0].isupper() else p.title())
    if chunks:
        for ch in chunks[:6]:
            meta = ch.get("metadata") or {}
            title = (meta.get("title") or ch.get("title") or "").strip()
            if title and len(title) > 5:
                phrases.append(title[:60])
    return list(dict.fromkeys(phrases))[:12]


def extract_top_context_vocabulary(
    context: str,
    chunks: Optional[List[Dict[str, Any]]] = None,
    max_terms: int = 10,
) -> List[str]:
    """Emotional + positioning vocabulary to mirror in final answer."""
    terms: List[str] = []
    blob = context or ""
    for ch in chunks or []:
        blob += " " + (ch.get("text") or "")[:400]
    for m in EMOTIONAL_VOCAB_PATTERN.finditer(blob):
        t = m.group(0).strip().lower()
        if t not in terms:
            terms.append(t)
    for p in extract_context_phrases(context, chunks):
        pl = p.lower()
        if pl not in terms and len(pl) > 3:
            terms.append(pl)
    return terms[:max_terms]


def build_sentence_mirror_prompt(
    context: str,
    chunks: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """Pre-final vocabulary lock — reduces wording drift vs context."""
    vocab = extract_top_context_vocabulary(context, chunks)
    if not vocab:
        return ""
    joined = ", ".join(vocab[:8])
    return (
        "\nSENTENCE-LEVEL MIRRORING (mandatory before final answer):\n"
        f"- Use this vocabulary from retrieved brand book: {joined}\n"
        "- Match emotional language (restraint, authority, precision) — do NOT drift to viral/hype tone.\n"
        "- Each strategic sentence must reuse at least one listed term or an exact phrase from context.\n"
    )


def unsupported_claim_rate(verification: Dict[str, Any]) -> float:
    claims = verification.get("claims") or []
    if not claims:
        return 0.0
    unsupported = len(verification.get("unsupported_claims") or [])
    return round(unsupported / len(claims), 3)


def should_force_hard_claim_regen(verification: Dict[str, Any]) -> bool:
    """Hard regen when claim grounding is critically weak."""
    rate_thresh = float(getattr(settings, "HARD_REGEN_UNSUPPORTED_RATE", 0.40))
    ratio_thresh = float(getattr(settings, "HARD_REGEN_MIN_CLAIM_RATIO", 0.55))
    rate = unsupported_claim_rate(verification)
    ratio = float(verification.get("claim_grounded_ratio") or 1.0)
    count = int(verification.get("unsupported_count") or 0)
    min_count = int(getattr(settings, "HARD_REGEN_MIN_UNSUPPORTED_COUNT", 3))
    return rate > rate_thresh or ratio < ratio_thresh or count >= min_count


def _overlap_to_chunk(sentence: str, chunk_text: str) -> float:
    stop = {"the", "a", "an", "is", "are", "and", "or", "to", "of", "in", "it", "you", "your", "that", "this", "be"}
    st = _token_set(sentence) - stop
    if len(st) < 3:
        return 1.0
    ct = _token_set(chunk_text)
    return len(st & ct) / len(st)


def verify_claims_at_level(
    answer: str,
    context: str,
    chunks: Optional[List[Dict[str, Any]]] = None,
    threshold: float = None,
) -> Dict[str, Any]:
    """
    Per-claim verification with support_chunks and support_strength.
    """
    from .claim_verification import detect_unsupported_claims

    threshold = threshold if threshold is not None else float(
        getattr(settings, "CLAIM_GROUNDING_THRESHOLD", 0.40)
    )
    min_strength = float(getattr(settings, "MIN_CLAIM_SUPPORT_STRENGTH", 0.55))
    chunks = chunks or []
    chunk_texts = [(c.get("text") or "", c) for c in chunks if c.get("text")]

    claim_records: List[Dict[str, Any]] = []
    unsupported: List[Dict[str, Any]] = []

    for sent in _sentences(answer):
        if len(sent) < 18:
            continue
        best_strength = 0.0
        best_chunks: List[str] = []
        best_key = ""

        best_chunk_id = ""
        for idx, (ctext, ch) in enumerate(chunk_texts):
            strength = _overlap_to_chunk(sent, ctext)
            if strength > best_strength:
                best_strength = strength
                meta = ch.get("metadata") or {}
                best_key = (meta.get("title") or ch.get("title") or f"chunk_{idx}")[:50]
                best_chunks = [best_key]
                best_chunk_id = str(ch.get("chunk_id") or meta.get("chunk_id") or f"chunk_{idx}")

        ctx_strength = _overlap_to_chunk(sent, context) if context else 0.0
        if ctx_strength > best_strength:
            best_strength = ctx_strength
            best_chunks = ["context_block"]

        generic_hit = bool(DEFINITIVE_STRATEGIC_PATTERNS.search(sent))
        grounded = best_strength >= threshold
        if generic_hit and best_strength < min_strength:
            grounded = False

        rec = {
            "claim": sent[:280],
            "support_chunks": best_chunks,
            "support_chunk_ids": [best_chunk_id] if best_chunk_id else [],
            "grounded": grounded,
            "support_strength": round(best_strength, 3),
            "generic_definitive": generic_hit,
        }
        claim_records.append(rec)
        if not grounded:
            unsupported.append(rec)

    total = len(claim_records) or 1
    grounded_count = sum(1 for r in claim_records if r["grounded"])
    ratio = grounded_count / total

    return {
        "claims": claim_records[:15],
        "unsupported_claims": unsupported[:8],
        "unsupported_count": len(unsupported),
        "claim_grounded_ratio": round(ratio, 3),
        "hallucination_flags": len(unsupported) > 0,
        "verified_sentence_ratio": round(ratio, 3),
    }


def suppress_unsupported_strategic_language(
    answer: str,
    claim_verification: Dict[str, Any],
    min_strength: float = None,
) -> Tuple[str, bool]:
    """
    Soften or prefix sentences with low support_strength and definitive phrasing.
    """
    min_strength = min_strength or float(getattr(settings, "MIN_CLAIM_SUPPORT_STRENGTH", 0.55))
    if not answer:
        return answer, False

    modified = False
    lines_out: List[str] = []
    claims_by_sent = {c["claim"][:200]: c for c in claim_verification.get("claims") or []}

    for para in answer.split("\n\n"):
        new_para_parts = []
        for sent in _sentences(para):
            rec = None
            for k, v in claims_by_sent.items():
                if k[:80] in sent or sent[:80] in k:
                    rec = v
                    break
            strength = float(rec.get("support_strength") or 0) if rec else 1.0
            generic = bool(rec.get("generic_definitive")) if rec else False
            rewrite_thresh = float(getattr(settings, "SENTENCE_REWRITE_MAX_STRENGTH", 0.50))
            lower_sent = sent.lower()
            has_forbidden_generic = any(g in lower_sent for g in FORBIDDEN_GENERIC_CLAIM_PHRASES)
            needs_hedge = (strength < min_strength) or has_forbidden_generic or (
                generic and strength < float(getattr(settings, "DEFINITIVE_ALLOWED_STRENGTH", 0.70))
            )
            if has_forbidden_generic and strength < rewrite_thresh:
                from .brand_language_anchor import GENERIC_REPLACEMENTS

                for g, rep in GENERIC_REPLACEMENTS.items():
                    if g in lower_sent:
                        sent = re.sub(re.escape(g), rep, sent, count=1, flags=re.I)
                        modified = True
            if needs_hedge and DEFINITIVE_STRATEGIC_PATTERNS.search(sent):
                sent = DEFINITIVE_STRATEGIC_PATTERNS.sub(
                    lambda m: "often " + m.group(0).lower(), sent, count=2
                )
                if not sent.lower().startswith(("it appears", "the retrieved", "based on")):
                    sent = HEDGE_PREFIX + sent[0].lower() + sent[1:]
                modified = True
            new_para_parts.append(sent)
        lines_out.append(" ".join(new_para_parts))
    return "\n\n".join(lines_out), modified


def rewrite_weak_claim_sentences(
    answer: str,
    verification: Dict[str, Any],
    context: str = "",
    chunks: Optional[List[Dict[str, Any]]] = None,
) -> Tuple[str, bool]:
    """
    Sentence-level repair — rewrite only claims with support_strength < threshold.
    Does NOT regenerate the whole answer.
    """
    rewrite_thresh = float(getattr(settings, "SENTENCE_REWRITE_MAX_STRENGTH", 0.50))
    vocab = extract_top_context_vocabulary(context, chunks)
    anchor_term = vocab[0] if vocab else "brand book positioning"
    modified = False
    text = answer

    for rec in verification.get("claims") or []:
        strength = float(rec.get("support_strength") or 1.0)
        if strength >= rewrite_thresh and rec.get("grounded"):
            continue
        claim = (rec.get("claim") or "").strip()
        if not claim or claim not in text:
            continue

        replacement = claim
        lower = replacement.lower()
        for generic in FORBIDDEN_GENERIC_CLAIM_PHRASES:
            if generic in lower:
                replacement = re.sub(
                    re.escape(generic),
                    anchor_term,
                    replacement,
                    count=1,
                    flags=re.I,
                )
                modified = True

        if strength < rewrite_thresh:
            if not replacement.lower().startswith(
                ("the brand book", "the retrieved", "based on", "it appears")
            ):
                replacement = (
                    f"The retrieved brand book suggests {replacement[0].lower()}{replacement[1:]}"
                )
                modified = True
            if vocab and not any(v in replacement.lower() for v in vocab[:3]):
                replacement = f"{replacement.rstrip('.')}, aligned with {anchor_term}."
                modified = True

        if replacement != claim:
            text = text.replace(claim, replacement, 1)

    return text, modified


def should_regenerate_for_claims(verification: Dict[str, Any]) -> bool:
    max_unsupported = int(getattr(settings, "MAX_UNSUPPORTED_CLAIMS_BEFORE_REGEN", 2))
    if int(verification.get("unsupported_count") or 0) > max_unsupported:
        return True
    return should_force_hard_claim_regen(verification)


def build_hard_claim_regeneration_instructions(
    verification: Dict[str, Any],
    context_phrases: Optional[List[str]] = None,
) -> str:
    lines = [
        "HARD CLAIM REGENERATION (mandatory):",
        "- ONLY use concepts explicitly present in the retrieved brand book / context below.",
        "- Do NOT introduce new strategic claims, channels, tactics, or guarantees.",
        "- Mirror the exact emotional and positioning vocabulary from context.",
        "- Keep paragraph structure; replace unsupported sentences with context-bound wording.",
    ]
    for u in (verification.get("unsupported_claims") or [])[:8]:
        ids = ", ".join(u.get("support_chunk_ids") or u.get("support_chunks") or [])[:80]
        lines.append(
            f"- REWRITE (strength {u.get('support_strength', 0)}, chunks {ids}): "
            f"\"{u.get('claim', '')[:160]}\""
        )
    lines.append(build_grounding_constraints_prompt(context_phrases=context_phrases))
    if context_phrases:
        lines.append(f"- Required mirror terms: {'; '.join(context_phrases[:8])}")
    return "\n".join(lines)


def build_claim_regeneration_instructions(
    verification: Dict[str, Any],
    context_phrases: Optional[List[str]] = None,
) -> str:
    if should_force_hard_claim_regen(verification):
        return build_hard_claim_regeneration_instructions(verification, context_phrases)
    lines = [
        "CLAIM GROUNDING REPAIR (mandatory):",
        "Rewrite ONLY unsupported claims. Keep grounded claims unchanged.",
        "Do not introduce new strategic claims.",
    ]
    for u in (verification.get("unsupported_claims") or [])[:6]:
        lines.append(
            f"- UNSUPPORTED (strength {u.get('support_strength', 0)}): "
            f"\"{u.get('claim', '')[:180]}\""
        )
    lines.append(build_grounding_constraints_prompt(context_phrases=context_phrases))
    return "\n".join(lines)
