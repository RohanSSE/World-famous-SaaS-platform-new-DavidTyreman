"""
Persistent brand personality — tone, energy, communication laws for stable cognition.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

PERSONALITY_MEMORY_KEY = "brand_personality_profile"

BRAND_CONSTITUTION: Dict[str, Any] = {
    "tone_laws": [
        "Premium authority — never casual hype or viral framing.",
        "Controlled energy — measured conviction, not aggression.",
        "Aspirational restraint — emotion without melodrama.",
        "Identity coherence — today's answer must match prior premium restraint positioning.",
    ],
    "communication_rules": [
        "Every recommendation must trace to brand book or retrieved strategic text.",
        "Prefer precision, craftsmanship, quiet authority, enduring trust.",
        "Hedge when evidence is partial; never invent strategy.",
        "Use short declarative sentences; one emotional anchor per paragraph max.",
        "Mirror founder/brand-book vocabulary — never default to generic marketing cadence.",
    ],
    "forbidden_patterns": [
        "viral", "growth hack", "10x", "dominate", "aggressive growth",
        "guaranteed", "always post", "kill switch", "weaponize",
        "best practices", "world-class", "customer-centric", "leverage",
        "synergy", "holistic", "game-changer", "disrupt", "crush it",
        "be authentic", "engage your audience", "drive growth",
    ],
    "preferred_patterns": [
        "crafted precision", "quiet authority", "earned credibility",
        "enduring trust", "brand promise", "strategic restraint",
        "premium craftsmanship", "principle-led", "manifesto-aligned",
    ],
    "preferred_sentence_structures": [
        "The brand book positions …",
        "Retrieved positioning suggests …",
        "This aligns with [principle] because …",
        "Under premium restraint, …",
    ],
}

DEFAULT_BRAND_PERSONALITY: Dict[str, Any] = {
    "tone": "premium authority",
    "energy": "controlled",
    "emotion": "aspirational restraint",
    "persuasion_style": "strategic clarity",
    "luxury_level": "high",
    "aggressiveness": "low",
    "storytelling_style": "principle-led",
    "communication_laws": [
        "Lead with brand book principles, not generic marketing.",
        "Prefer quiet authority over hype.",
        "Use crafted precision — earned credibility, not loud claims.",
        "Hedge when evidence is partial; never invent strategy.",
        "Preserve emotional restraint and premium framing.",
        "Founder voice: measured conviction, personal principle — never corporate filler.",
        "Sentence style: short declarative lines; one emotional anchor per paragraph.",
    ],
}


def get_brand_personality(session_id: Optional[int] = None) -> Dict[str, Any]:
    if not session_id:
        return dict(DEFAULT_BRAND_PERSONALITY)
    try:
        from user_sessions.models import BrandMemory

        row = BrandMemory.objects.filter(
            session_id=session_id, key=PERSONALITY_MEMORY_KEY, memory_type="preference"
        ).first()
        if row and row.value:
            return {**DEFAULT_BRAND_PERSONALITY, **row.value}
    except Exception as e:
        logger.debug("Brand personality load skipped: %s", e)
    return dict(DEFAULT_BRAND_PERSONALITY)


def save_brand_personality(session_id: int, personality: Dict[str, Any], user=None) -> None:
    if not session_id:
        return
    try:
        from user_sessions.models import BrandMemory

        merged = {**DEFAULT_BRAND_PERSONALITY, **personality}
        BrandMemory.objects.update_or_create(
            session_id=session_id,
            key=PERSONALITY_MEMORY_KEY,
            defaults={
                "memory_type": "preference",
                "content": json.dumps(merged, ensure_ascii=False)[:3000],
                "value": merged,
                "importance_score": 0.95,
                "is_pinned": True,
                "created_by": user if user and getattr(user, "is_authenticated", False) else None,
            },
        )
    except Exception as e:
        logger.debug("Brand personality save skipped: %s", e)


def evolve_personality_from_answer(
    session_id: int,
    answer: str,
    consistency: Optional[Dict[str, Any]] = None,
    user=None,
) -> Dict[str, Any]:
    """Longitudinal tuning — tone, luxury, aggressiveness from interaction patterns."""
    personality = get_brand_personality(session_id)
    blob = (answer or "").lower()
    consistency = consistency or {}

    if any(w in blob for w in ("luxury", "premium", "exclusive", "crafted")):
        personality["luxury_level"] = "high"
        personality["tone"] = "premium authority"
    if any(w in blob for w in ("viral", "aggressive", "hustle", "10x")):
        personality["aggressiveness"] = "low"
        if "viral hype" not in personality.get("communication_laws", []):
            personality.setdefault("communication_laws", []).append(
                "Reject viral hype framing unless explicitly in brand book."
            )
    if consistency.get("tone_alignment", 0) >= 0.7:
        personality["energy"] = "controlled"
    if consistency.get("strategy_alignment", 0) >= 0.65:
        personality["storytelling_style"] = "principle-led"

    personality["tone_confidence"] = round(
        min(1.0, float(consistency.get("tone_alignment", 0.65)) + 0.05), 3
    )
    personality["personality_confidence"] = round(
        min(1.0, float(consistency.get("consistency_score", 0.6)) + 0.05), 3
    )
    personality["strategy_stability"] = round(
        float(consistency.get("strategy_alignment", 0.6)), 3
    )
    personality["emotional_profile"] = personality.get("emotion", "aspirational restraint")

    save_brand_personality(session_id, personality, user=user)
    return personality


def format_constitution_prompt(constitution: Optional[Dict[str, Any]] = None) -> str:
    """Mandatory brand constitution — injected before every generation."""
    c = constitution or BRAND_CONSTITUTION
    tone_laws = "\n".join(f"  - {t}" for t in c.get("tone_laws", []))
    comm_rules = "\n".join(f"  - {r}" for r in c.get("communication_rules", []))
    forbidden = ", ".join(c.get("forbidden_patterns", [])[:18])
    preferred = ", ".join(c.get("preferred_patterns", [])[:12])
    structures = "\n".join(f"  - {s}" for s in c.get("preferred_sentence_structures", [])[:4])
    return (
        "\nBRAND CONSTITUTION (MANDATORY — non-negotiable):\n"
        f"Tone laws:\n{tone_laws}\n"
        f"Communication rules:\n{comm_rules}\n"
        f"NEVER use phrasing like: {forbidden}\n"
        f"PREFER language like: {preferred}\n"
        + (f"Preferred sentence patterns:\n{structures}\n" if structures else "")
    )


def format_personality_prompt(personality: Optional[Dict[str, Any]] = None) -> str:
    p = personality or DEFAULT_BRAND_PERSONALITY
    laws = "\n".join(f"  - {law}" for law in (p.get("communication_laws") or [])[:6])
    return (
        "\nBRAND PERSONALITY (stable — preserve across turns):\n"
        f"- Tone: {p.get('tone', 'premium authority')}\n"
        f"- Energy: {p.get('energy', 'controlled')}\n"
        f"- Emotion: {p.get('emotion', 'aspirational restraint')}\n"
        f"- Persuasion: {p.get('persuasion_style', 'strategic clarity')}\n"
        f"- Luxury level: {p.get('luxury_level', 'high')}\n"
        f"- Storytelling: {p.get('storytelling_style', 'principle-led')}\n"
        f"Communication laws:\n{laws}\n"
    )
