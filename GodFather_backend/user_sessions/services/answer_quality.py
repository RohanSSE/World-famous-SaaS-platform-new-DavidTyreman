"""
Score manifesto / phase answers as too_weak, vendor_thought, or strong.
Thresholds vary by question stage, category, and order (Phase 1 manifesto steps).
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

QUALITY_LABELS = {
    "too_weak": "This is too weak",
    "vendor_thought": "This is a vendor thought",
    "strong": "This is strong",
}

GENERIC_BUZZWORDS = {
    "quality",
    "professional",
    "innovative",
    "best service",
    "creative",
    "inspiring",
    "helpful",
    "reliable",
    "solutions",
    "leading",
    "world-class",
    "cutting-edge",
    "passionate",
    "dedicated",
    "excellence",
    "trusted partner",
}

VENDOR_PHRASES = [
    r"\bwe provide\b",
    r"\bwe offer\b",
    r"\bour services\b",
    r"\bhelp (businesses|companies|clients|customers)\b",
    r"\bclients? (need|want|require)\b",
    r"\bcustomers? (need|want|require)\b",
    r"\bunmet (market )?needs\b",
    r"\bmarket needs\b",
    r"\bpractical solutions\b",
    r"\bfresh,? practical\b",
    r"\baddress gaps\b",
    r"\bgaps in the market\b",
    r"\bwe deliver\b",
    r"\bwe supply\b",
    r"\bvendor\b",
    r"\bcontractor\b",
    r"\bwhen (they|you) need us\b",
    r"\bhire us\b",
    r"\bour (product|service)s?\b",
    r"\bhigh.?quality (service|product)s?\b",
]

SPECIFICITY_MARKERS = [
    r"\bbecause\b",
    r"\bwhen we\b",
    r"\bwhen i\b",
    r"\bpeople feel\b",
    r"\bour (team|people|culture)\b",
    r"\brefuse to\b",
    r"\bwe believe\b",
    r"\bwe stand for\b",
    r"\bwe won't\b",
    r"\bthat's why\b",
    r"\bin the room\b",
    r"\bshow up\b",
    r"\bmy (father|mother|family|childhood)\b",
    r"\b\d{4}\b",
]

# Phase 1 (stage=1) manifesto steps by order index
PHASE1_ORDER_PROFILES: Dict[int, Dict[str, Any]] = {
    0: {
        "step": "Brand Attitude",
        "min_words": 12,
        "min_chars": 55,
        "vendor_sensitive": 0.9,
        "emotion_required": True,
    },
    1: {
        "step": "Brand Culture",
        "min_words": 11,
        "min_chars": 50,
        "vendor_sensitive": 0.85,
        "emotion_required": True,
    },
    2: {
        "step": "Originality Check",
        "min_words": 13,
        "min_chars": 60,
        "vendor_sensitive": 1.2,
        "emotion_required": False,
    },
    3: {
        "step": "Customer",
        "min_words": 12,
        "min_chars": 55,
        "vendor_sensitive": 1.0,
        "emotion_required": False,
    },
    4: {
        "step": "Legacy & Impact",
        "min_words": 14,
        "min_chars": 65,
        "vendor_sensitive": 0.8,
        "emotion_required": True,
    },
    5: {
        "step": "Brand Discipline",
        "min_words": 10,
        "min_chars": 45,
        "vendor_sensitive": 0.75,
        "emotion_required": False,
    },
    6: {
        "step": "Emotional Anchor",
        "min_words": 11,
        "min_chars": 50,
        "vendor_sensitive": 0.7,
        "emotion_required": True,
    },
    7: {
        "step": "Mapping",
        "min_words": 13,
        "min_chars": 60,
        "vendor_sensitive": 0.85,
        "emotion_required": False,
    },
}

CATEGORY_PROFILES: Dict[str, Dict[str, Any]] = {
    "brand_identity": {"min_words": 12, "min_chars": 55, "vendor_sensitive": 0.9},
    "target_audience": {"min_words": 13, "min_chars": 58, "vendor_sensitive": 1.0},
    "values": {"min_words": 11, "min_chars": 50, "vendor_sensitive": 0.85},
    "messaging": {"min_words": 12, "min_chars": 55, "vendor_sensitive": 1.1},
    "visual": {"min_words": 10, "min_chars": 45, "vendor_sensitive": 0.7},
    "other": {"min_words": 10, "min_chars": 45, "vendor_sensitive": 1.0},
}

STAGE_DEFAULTS: Dict[int, Dict[str, Any]] = {
    1: {"min_words": 11, "min_chars": 50, "vendor_sensitive": 1.0},
    2: {"min_words": 13, "min_chars": 58, "vendor_sensitive": 1.05},
    3: {"min_words": 12, "min_chars": 55, "vendor_sensitive": 0.95},
}


def get_question_profile(question) -> Dict[str, Any]:
    """Merge stage, category, and order-based thresholds for one question."""
    stage = int(getattr(question, "stage", 1) or 1)
    order = int(getattr(question, "order", 0) or 0)
    category = (getattr(question, "category", None) or "other").strip() or "other"

    base = dict(STAGE_DEFAULTS.get(stage, STAGE_DEFAULTS[1]))
    base.update(CATEGORY_PROFILES.get(category, CATEGORY_PROFILES["other"]))

    if stage == 1 and order in PHASE1_ORDER_PROFILES:
        base.update(PHASE1_ORDER_PROFILES[order])
        base["profile_source"] = f"phase1_step:{PHASE1_ORDER_PROFILES[order]['step']}"
    else:
        base["profile_source"] = f"stage:{stage}/category:{category}"

    base["stage"] = stage
    base["order"] = order
    base["category"] = category
    return base


def _word_count(text: str) -> int:
    return len(re.findall(r"\b[\w']+\b", text))


def _count_pattern_hits(text: str, patterns: List[str]) -> int:
    lowered = text.lower()
    return sum(1 for p in patterns if re.search(p, lowered))


def _generic_density(words: List[str]) -> float:
    if not words:
        return 0.0
    hits = sum(1 for w in words if w.lower() in GENERIC_BUZZWORDS)
    return hits / max(len(words), 1)


def score_answer_quality(question, answer_text: str) -> Dict[str, Any]:
    """
    Heuristic quality score used to guide AI and as fallback when AI fails.
    Returns quality key, label, reason, and diagnostic scores.
    """
    text = (answer_text or "").strip()
    profile = get_question_profile(question)
    words = re.findall(r"\b[\w']+\b", text)
    wc = len(words)
    char_len = len(text)

    min_words = int(profile.get("min_words", 10))
    min_chars = int(profile.get("min_chars", 45))
    vendor_sensitive = float(profile.get("vendor_sensitive", 1.0))

    vendor_hits = _count_pattern_hits(text, VENDOR_PHRASES)
    specificity_hits = _count_pattern_hits(text, SPECIFICITY_MARKERS)
    generic_density = _generic_density(words)

    # Normalized sub-scores 0..1
    length_score = min(1.0, wc / max(min_words, 1))
    char_score = min(1.0, char_len / max(min_chars, 1))
    vendor_score = min(1.0, (vendor_hits * 0.45) * vendor_sensitive)
    generic_penalty = min(1.0, generic_density * 2.2)
    specificity_bonus = min(0.35, specificity_hits * 0.12)

    strength = (length_score * 0.35 + char_score * 0.25) - vendor_score * 0.35 - generic_penalty * 0.3 + specificity_bonus

    step_name = profile.get("step") or profile.get("category", "this question")
    reason = ""

    # Classification thresholds (tuned per profile strictness)
    weak_cutoff = 0.38 if min_words >= 13 else 0.42
    vendor_cutoff = 0.32 * vendor_sensitive

    if wc < max(6, min_words - 4) or char_len < max(25, min_chars - 20):
        quality = "too_weak"
        reason = f"Too short for {step_name} — add specific feeling, behavior, or proof (aim for {min_words}+ words)."
    elif vendor_hits >= 2 or (vendor_hits >= 1 and vendor_score >= vendor_cutoff and length_score < 0.75):
        quality = "vendor_thought"
        reason = f"Sounds like a vendor pitch, not a brand truth for {step_name}. Lead with belief and behavior, not services."
    elif generic_density >= 0.22 and length_score < 0.65:
        quality = "too_weak"
        reason = f"Generic words without depth for {step_name} — replace buzzwords with something only your brand would say."
    elif strength < weak_cutoff:
        quality = "too_weak"
        reason = f"Needs more emotional truth and specificity for {step_name}."
    elif vendor_score >= vendor_cutoff and specificity_hits == 0:
        quality = "vendor_thought"
        reason = f"Feels transactional for {step_name} — show who you are, not what you sell."
    else:
        quality = "strong"
        reason = f"Solid direction for {step_name} — specific enough to build on."

    return {
        "quality": quality,
        "quality_label": QUALITY_LABELS[quality],
        "reason": reason,
        "profile": profile,
        "scores": {
            "word_count": wc,
            "min_words": min_words,
            "length_score": round(length_score, 2),
            "vendor_score": round(vendor_score, 2),
            "generic_density": round(generic_density, 2),
            "specificity_hits": specificity_hits,
            "strength": round(strength, 2),
        },
    }


def build_quality_prompt_context(question, answer_text: str, heuristic: Dict[str, Any]) -> str:
    """User prompt appendix for AI classification + recommendations."""
    profile = heuristic.get("profile") or get_question_profile(question)
    step = profile.get("step") or profile.get("category", "general")
    return f"""Question profile: {profile.get('profile_source', 'default')} — {step}
Expected depth: at least {profile.get('min_words')} words, {profile.get('min_chars')} characters.
Heuristic classification: {heuristic.get('quality')} ({heuristic.get('quality_label')})
Heuristic reason: {heuristic.get('reason')}

Score signals: {heuristic.get('scores')}

Classify the user's draft into exactly one quality (you may override heuristic if clearly wrong):
- too_weak → label "This is too weak"
- vendor_thought → label "This is a vendor thought"
- strong → label "This is strong"

Then give 2–3 items in "suggestions" — each must be ONLY the final answer sentence the user can paste into the form.
- No coaching wrapper (never start with "Rewrite with", "Try this", or "like '...'").
- too_weak: one strong rewritten answer per suggestion
- vendor_thought: brand-belief rewrite, not service/vendor language
- strong: one polished answer variant"""


def sanitize_suggestion_text(raw: str) -> str:
    """Return paste-ready answer text without coaching wrappers."""
    text = (raw or "").strip()
    if not text:
        return ""

    like_quoted = re.search(r"\blike\s+['\"]([^'\"]+)['\"]\s*\.?$", text, re.I)
    if like_quoted:
        return like_quoted.group(1).strip()

    wrapped = re.match(r"^['\"](.+)['\"]\s*\.?$", text, re.S)
    if wrapped:
        return wrapped.group(1).strip()

    if re.match(r"^(rewrite|try|instead|consider|say|use|example|suggestion|you could)", text, re.I) and ":" in text:
        after = ":".join(text.split(":")[1:]).strip()
        nested = sanitize_suggestion_text(after)
        if nested and len(nested) < len(text):
            return nested

    text = re.sub(r"^rewrite\s+with\s+[^,]+,\s*like\s+", "", text, flags=re.I)
    text = re.sub(r"^try\s+this\s+instead:\s*", "", text, flags=re.I)
    text = re.sub(r"^you\s+could\s+(also\s+)?say:\s*", "", text, flags=re.I)
    return text.strip()


def normalize_ai_quality_response(result: dict, heuristic: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure API payload always has quality fields and suggestions list."""
    quality = (result.get("quality") or heuristic.get("quality") or "too_weak").strip().lower()
    if quality not in QUALITY_LABELS:
        quality = heuristic.get("quality", "too_weak")

    label = result.get("quality_label") or QUALITY_LABELS.get(quality, QUALITY_LABELS["too_weak"])
    if label not in QUALITY_LABELS.values():
        label = QUALITY_LABELS[quality]

    suggestions = result.get("suggestions") or []
    if not isinstance(suggestions, list):
        suggestions = []
    suggestions = [
        t
        for s in suggestions[:4]
        if s and (t := sanitize_suggestion_text(str(s)))
    ]

    reason = (result.get("reason") or heuristic.get("reason") or "").strip()

    return {
        "quality": quality,
        "quality_label": label,
        "reason": reason,
        "suggestions": suggestions,
        "scores": heuristic.get("scores"),
        "profile_source": (heuristic.get("profile") or {}).get("profile_source"),
    }
