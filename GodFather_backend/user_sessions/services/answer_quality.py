"""
Score manifesto / phase answers as too_weak, vendor_thought, or strong.
Thresholds vary by question stage, category, and order (Phase 1 manifesto steps).
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

QUALITY_LABELS = {
    "too_weak": "",
    "vendor_thought": "",
    "strong": "",
}

QUALITY_REASONS = {
    "too_weak": "Your answer has a useful beginning. Add one real feeling, one specific reason, or one behavior so it feels more memorable.",
    "vendor_thought": "You're on the right track. Let's shift it from service language into belief, behavior, and emotional truth.",
    "strong": "This already has something useful. A sharper detail or vivid moment can make it land even better.",
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
    "empowered",
    "potential",
    "meaningful",
    "transform",
}

GENERIC_SUGGESTION_PHRASES = [
    r"\bsee their potential\b",
    r"\btake bold steps\b",
    r"\blife that truly matters\b",
    r"\bmeaningful connections\b",
    r"\btransform their communities\b",
    r"\bfeel seen, valued, and empowered\b",
    r"\binspire people\b",
    r"\bspark the courage\b",
]

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

    phase1_order_index = order - 1 if order > 0 else order
    if stage == 1 and phase1_order_index in PHASE1_ORDER_PROFILES:
        base.update(PHASE1_ORDER_PROFILES[phase1_order_index])
        base["profile_source"] = f"phase1_step:{PHASE1_ORDER_PROFILES[phase1_order_index]['step']}"
    else:
        base["profile_source"] = f"stage:{stage}/category:{category}"

    base["stage"] = stage
    base["order"] = order
    base["order_index"] = phase1_order_index
    base["category"] = category
    base["question_text"] = str(getattr(question, "text", "") or "")
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
        reason = f"Your answer has a useful beginning for {step_name}. Add one real feeling, behavior, or proof so it has more depth."
    elif vendor_hits >= 2 or (vendor_hits >= 1 and vendor_score >= vendor_cutoff and length_score < 0.75):
        quality = "vendor_thought"
        reason = f"Your answer is pointing toward something useful for {step_name}. Let's move it from service language into belief, behavior, and emotional truth."
    elif generic_density >= 0.22 and length_score < 0.65:
        quality = "too_weak"
        reason = f"Your answer is moving in the right direction for {step_name}. Now replace broad words with something only your brand would say."
    elif strength < weak_cutoff:
        quality = "too_weak"
        reason = f"Your answer has a useful beginning for {step_name}. A bit more emotional truth and specificity will make it much sharper."
    elif vendor_score >= vendor_cutoff and specificity_hits == 0:
        quality = "vendor_thought"
        reason = f"You're close for {step_name}. Let's show who you are, not just what you sell."
    else:
        quality = "strong"
        reason = f"Your answer has a strong signal for {step_name}. Add one vivid detail if you want it to land even harder."

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

Classify the user's answer into exactly one quality (you may override heuristic if clearly wrong):
- too_weak -> quality_label ""
- vendor_thought -> quality_label ""
- strong -> quality_label ""

User-facing copy rules:
- Write in English only.
- Never use the word "draft" in reason, title, or suggestion copy; say "your answer" when needed.
- Do not use old quality-heading phrases; keep the reason conversational and respectful.

Then give 2–3 items in "suggestions" — each must be ONLY the final answer sentence the user can paste into the form.
- No coaching wrapper (never start with "Rewrite with", "Try this", or "like '...'").
- too_weak: one strong rewritten answer per suggestion
- vendor_thought: brand-belief rewrite, not service/vendor language
- strong: one polished answer variant

ORB pass criteria for every suggestion:
- It must answer the exact question being asked, not a neighboring Brand Godfather question.
- It must contain a belief, emotional truth, specific change, or observable behavior.
- It must not rely on products, features, services, solutions, quality, or professionalism.
- It must be specific enough that a strategist could infer what the brand stands against or stands for.
- For purpose questions, name the deeper human change the brand exists to create and why that matters.
- For founder/identity questions, name the role or posture the founder embodies without describing an offer.

Do not return a suggestion that the ORB would likely reject for being poetic, vague, generic, or service-led."""


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

    label = QUALITY_LABELS[quality]

    profile = heuristic.get("profile") or {}
    suggestions = result.get("suggestions") or []
    if not isinstance(suggestions, list):
        suggestions = []
    suggestions = []
    for suggestion in (result.get("suggestions") or [])[:4]:
        if suggestion and (text := sanitize_suggestion_text(str(suggestion))):
            if _is_orb_ready_suggestion(text, profile):
                suggestions.append(text)

    if len(suggestions) < 2:
        for fallback in _orb_ready_fallback_suggestions(profile, quality):
            if fallback not in suggestions and _is_orb_ready_suggestion(fallback, profile):
                suggestions.append(fallback)
            if len(suggestions) >= 3:
                break

    reason = (result.get("reason") or heuristic.get("reason") or QUALITY_REASONS.get(quality, "")).strip()
    harsh_markers = [
        "draft",
        "draft is",
        "too brief",
        "too short",
        "too weak",
        "lacks",
        "generic words",
        "vendor pitch",
        "transactional",
        "not a brand truth",
    ]
    if not reason or any(marker in reason.lower() for marker in harsh_markers):
        reason = QUALITY_REASONS.get(quality, reason)
    reason = re.sub(r"\b(the\s+)?draft\b", "your answer", reason, flags=re.I)

    return {
        "quality": quality,
        "quality_label": label,
        "reason": reason,
        "suggestions": suggestions,
        "scores": heuristic.get("scores"),
        "profile_source": profile.get("profile_source"),
    }


def _is_orb_ready_suggestion(text: str, profile: Dict[str, Any]) -> bool:
    lowered = (text or "").strip().lower()
    if not lowered:
        return False

    words = re.findall(r"\b[\w']+\b", lowered)
    if len(words) < 14:
        return False
    if _count_pattern_hits(lowered, VENDOR_PHRASES) > 0:
        return False
    if _count_pattern_hits(lowered, GENERIC_SUGGESTION_PHRASES) > 0:
        return False

    question_text = str(profile.get("question_text") or "").lower()
    step = str(profile.get("step") or "").lower()
    is_purpose_question = any(marker in question_text for marker in ["beyond what you sell", "deeper purpose", "purpose of your business"]) or "culture" in step

    belief_hits = _count_pattern_hits(lowered, [
        r"\bwe believe\b",
        r"\bwe exist to\b",
        r"\bour purpose is\b",
        r"\bour brand stands for\b",
        r"\bwe stand for\b",
        r"\bwe refuse to\b",
        r"\bbeyond what we sell\b",
    ])
    depth_hits = _count_pattern_hits(lowered, [
        r"\bbecause\b",
        r"\bso that\b",
        r"\bfrom .+ to\b",
        r"\bshift\b",
        r"\bchange\b",
        r"\btrust\b",
        r"\bconviction\b",
        r"\bclarity\b",
        r"\bbrave\b",
        r"\bfeel\b",
        r"\bact\b",
    ])

    if is_purpose_question:
        return belief_hits >= 1 and depth_hits >= 2
    return belief_hits + depth_hits >= 2


def _orb_ready_fallback_suggestions(profile: Dict[str, Any], quality: str) -> List[str]:
    question_text = str(profile.get("question_text") or "").lower()
    step = str(profile.get("step") or "").lower()
    is_purpose_question = any(marker in question_text for marker in ["beyond what you sell", "deeper purpose", "purpose of your business"]) or "culture" in step

    if is_purpose_question:
        return [
            "Beyond what we sell, our purpose is to move people from uncertainty to conviction, because a brand should change how they choose, trust, and act.",
            "We exist to help people feel clear enough to reject the ordinary option and brave enough to choose the standard they actually believe in.",
            "Our purpose is to turn scattered ambition into focused belief, so people leave with more clarity, more trust, and a stronger reason to move.",
        ]

    if quality == "vendor_thought":
        return [
            "We believe people remember the brands that change how they feel and act, so every decision we make must create trust before it creates a transaction.",
            "Our brand stands for refusing the easy, forgettable answer and building the kind of clarity people can feel in the room.",
        ]
    if quality == "strong":
        return [
            "We carry this belief into the way we show up: direct enough to create clarity, warm enough to earn trust, and disciplined enough to repeat it every time.",
        ]
    return [
        "We believe our work should leave people feeling clearer, braver, and less willing to accept the ordinary version of what they came for.",
        "The deeper reason we exist is to turn uncertainty into conviction, so people can move forward with a standard they actually believe in.",
    ]
