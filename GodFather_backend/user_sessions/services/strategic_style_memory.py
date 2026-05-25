"""
Strategic style memory — persistent persuasion/tone preferences per session.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

STYLE_MEMORY_KEY = "strategic_style_profile"

DEFAULT_STYLE = {
    "tone": "authoritative",
    "emotional_intensity": "measured",
    "persuasion_style": "strategic clarity",
    "prefers": ["trust", "consistency", "brand-book-grounded"],
    "avoids": ["playful", "viral", "clickbait"],
}


def get_strategic_style(session_id: Optional[int]) -> Dict[str, Any]:
    if not session_id:
        return dict(DEFAULT_STYLE)
    try:
        from user_sessions.models import BrandMemory

        row = BrandMemory.objects.filter(
            session_id=session_id, key=STYLE_MEMORY_KEY, memory_type="preference"
        ).first()
        if row and row.value:
            return {**DEFAULT_STYLE, **row.value}
    except Exception as e:
        logger.debug("Strategic style load skipped: %s", e)
    return dict(DEFAULT_STYLE)


EVOLUTION_KEY = "strategic_memory_evolution"


def evolve_strategic_memory_profile(
    session_id: int,
    answer: str,
    memory_snippets: List[str],
    consistency: Optional[Dict[str, Any]] = None,
    user=None,
) -> Dict[str, Any]:
    """
    Evolving profile: tone_confidence, positioning_stability, strategic_preferences weights.
    """
    if not session_id:
        return {}

    style = get_strategic_style(session_id)
    consistency = consistency or {}
    blob = " ".join(memory_snippets).lower() + " " + (answer or "").lower()

    prefs = {
        "authority": style.get("strategic_preferences", {}).get("authority", 0.7),
        "trust": style.get("strategic_preferences", {}).get("trust", 0.75),
        "premium": style.get("strategic_preferences", {}).get("premium", 0.6),
        "playful": style.get("strategic_preferences", {}).get("playful", 0.15),
    }
    if "authority" in blob or "authoritative" in blob:
        prefs["authority"] = min(1.0, prefs["authority"] + 0.05)
    if "trust" in blob:
        prefs["trust"] = min(1.0, prefs["trust"] + 0.04)
    if any(w in blob for w in ("playful", "viral", "meme")):
        prefs["playful"] = min(1.0, prefs["playful"] + 0.08)

    evolution = {
        "tone_confidence": round(
            min(1.0, consistency.get("tone_alignment", 0.7) + 0.1), 3
        ),
        "positioning_stability": round(
            consistency.get("consistency_score", 0.75), 3
        ),
        "strategic_preferences": {k: round(v, 3) for k, v in prefs.items()},
    }
    style["evolution"] = evolution

    try:
        from user_sessions.models import BrandMemory

        BrandMemory.objects.update_or_create(
            session_id=session_id,
            key=EVOLUTION_KEY,
            defaults={
                "memory_type": "preference",
                "content": json.dumps(evolution, ensure_ascii=False)[:2000],
                "value": evolution,
                "importance_score": 0.9,
                "is_pinned": True,
                "created_by": user if user and getattr(user, "is_authenticated", False) else None,
            },
        )
    except Exception as e:
        logger.debug("Memory evolution save skipped: %s", e)

    return evolution


def update_strategic_style_from_interaction(
    session_id: int,
    answer: str,
    memory_snippets: List[str],
    user=None,
) -> Dict[str, Any]:
    """
    Infer style deltas from tone memory + answer patterns; persist merged profile.
    """
    if not session_id:
        return DEFAULT_STYLE

    style = get_strategic_style(session_id)
    blob = " ".join(memory_snippets).lower() + " " + (answer or "").lower()

    if any(w in blob for w in ("premium", "luxury", "exclusive")):
        if "premium" not in style.get("prefers", []):
            style.setdefault("prefers", []).append("premium")
    if any(w in blob for w in ("trust", "credibility", "integrity")):
        style["tone"] = "authoritative"
        if "trust" not in style.get("prefers", []):
            style.setdefault("prefers", []).append("trust")
    if any(w in blob for w in ("playful", "viral", "meme", "trending")):
        for w in ("playful", "viral"):
            if w not in style.get("avoids", []):
                style.setdefault("avoids", []).append(w)

    try:
        from user_sessions.models import BrandMemory

        BrandMemory.objects.update_or_create(
            session_id=session_id,
            key=STYLE_MEMORY_KEY,
            defaults={
                "memory_type": "preference",
                "content": json.dumps(style, ensure_ascii=False)[:2000],
                "value": style,
                "importance_score": 0.85,
                "is_pinned": True,
                "created_by": user if user and getattr(user, "is_authenticated", False) else None,
            },
        )
    except Exception as e:
        logger.debug("Strategic style save skipped: %s", e)

    return style


def format_style_prompt(style: Dict[str, Any]) -> str:
    if not style:
        return ""
    prefers = ", ".join(style.get("prefers", [])[:5])
    avoids = ", ".join(style.get("avoids", [])[:5])
    return (
        f"\nSTRATEGIC STYLE MEMORY:\n"
        f"- Preferred tone: {style.get('tone', 'authoritative')}\n"
        f"- Emotional intensity: {style.get('emotional_intensity', 'measured')}\n"
        f"- Prefers framing: {prefers or 'strategic clarity'}\n"
        f"- Avoid messaging: {avoids or 'generic hype'}\n"
    )
