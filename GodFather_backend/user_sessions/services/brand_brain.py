"""
Persistent evolving brand brain — unified personality state per session.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from .brand_personality import (
    BRAND_CONSTITUTION,
    DEFAULT_BRAND_PERSONALITY,
    format_constitution_prompt,
    get_brand_personality,
    save_brand_personality,
)

logger = logging.getLogger(__name__)

BRAND_BRAIN_KEY = "brand_brain_state"

DEFAULT_BRAND_BRAIN: Dict[str, Any] = {
    "tone": "authoritative",
    "energy": "calm_premium",
    "communication_style": "minimal",
    "brand_archetype": "visionary",
    "emotional_positioning": "trust through restraint",
    "audience_psychology": [
        "certainty seeking",
        "status through quality",
    ],
    "preferred_language": [],
    "rejected_language": [],
    "strategic_priorities": [],
    "positioning_anchor": "",
    "tone_confidence": 0.72,
    "personality_confidence": 0.70,
    "strategy_stability": 0.68,
    "evolution_history": [],
}


def get_brand_brain(session_id: Optional[int] = None) -> Dict[str, Any]:
    """Load merged brand brain (constitution + personality + session state)."""
    brain = dict(DEFAULT_BRAND_BRAIN)
    brain.update(get_brand_personality(session_id))

    if not session_id:
        return brain

    try:
        from user_sessions.models import BrandMemory

        row = BrandMemory.objects.filter(
            session_id=session_id,
            key=BRAND_BRAIN_KEY,
            memory_type="preference",
        ).first()
        if row and row.value:
            brain.update(row.value)
    except Exception as e:
        logger.debug("Brand brain load skipped: %s", e)

    return brain


def save_brand_brain(session_id: int, brain: Dict[str, Any], user=None) -> Dict[str, Any]:
    if not session_id:
        return brain
    merged = {**DEFAULT_BRAND_BRAIN, **brain}
    try:
        from user_sessions.models import BrandMemory

        BrandMemory.objects.update_or_create(
            session_id=session_id,
            key=BRAND_BRAIN_KEY,
            defaults={
                "memory_type": "preference",
                "content": json.dumps(merged, ensure_ascii=False)[:4000],
                "value": merged,
                "confidence": float(merged.get("personality_confidence", 0.7)),
                "importance_score": 1.0,
                "is_pinned": True,
                "created_by": user if user and getattr(user, "is_authenticated", False) else None,
            },
        )
        save_brand_personality(session_id, merged, user=user)
    except Exception as e:
        logger.debug("Brand brain save skipped: %s", e)
    return merged


def evolve_brand_brain(
    session_id: int,
    answer: str = "",
    consistency: Optional[Dict[str, Any]] = None,
    feedback_delta: Optional[Dict[str, Any]] = None,
    user=None,
) -> Dict[str, Any]:
    """Merge interaction signals into longitudinal brand brain."""
    brain = get_brand_brain(session_id)
    consistency = consistency or {}
    feedback_delta = feedback_delta or {}
    blob = (answer or "").lower()

    if feedback_delta.get("preferred_phrases"):
        pref = list(brain.get("preferred_language") or [])
        for p in feedback_delta["preferred_phrases"]:
            if p and p not in pref:
                pref.append(p)
        brain["preferred_language"] = pref[-20:]

    if feedback_delta.get("rejected_phrases"):
        rej = list(brain.get("rejected_language") or [])
        for p in feedback_delta["rejected_phrases"]:
            if p and p not in rej:
                rej.append(p)
        brain["rejected_language"] = rej[-20:]

    if any(w in blob for w in ("luxury", "premium", "restraint", "crafted")):
        brain["energy"] = "calm_premium"
        brain["emotional_positioning"] = "trust through restraint"
    if any(w in blob for w in ("viral", "aggressive", "hustle", "10x")):
        brain.setdefault("rejected_language", []).append("viral growth framing")

    brain["tone_confidence"] = round(
        min(1.0, max(brain.get("tone_confidence", 0.65), consistency.get("tone_alignment", 0.65))),
        3,
    )
    brain["personality_confidence"] = round(
        min(1.0, max(brain.get("personality_confidence", 0.65), consistency.get("consistency_score", 0.65))),
        3,
    )
    brain["strategy_stability"] = round(
        float(consistency.get("strategy_alignment", brain.get("strategy_stability", 0.65))),
        3,
    )

    history = list(brain.get("evolution_history") or [])
    if feedback_delta:
        history.append(
            {
                "event": "feedback",
                "preferred": feedback_delta.get("preferred_phrases", [])[:3],
                "rejected": feedback_delta.get("rejected_phrases", [])[:3],
            }
        )
    brain["evolution_history"] = history[-30:]

    return save_brand_brain(session_id, brain, user=user)


def format_brand_brain_prompt(brain: Optional[Dict[str, Any]] = None) -> str:
    """Inject before generation — mandatory brand operating system context."""
    b = brain or DEFAULT_BRAND_BRAIN
    constitution = format_constitution_prompt()
    audience = ", ".join(b.get("audience_psychology") or [])[:300]
    preferred = ", ".join((b.get("preferred_language") or [])[:8])
    rejected = ", ".join((b.get("rejected_language") or [])[:8])
    return (
        constitution
        + "\nBRAND BRAIN (persistent — preserve across all turns):\n"
        f"- Tone: {b.get('tone', 'authoritative')} | Energy: {b.get('energy', 'calm_premium')}\n"
        f"- Style: {b.get('communication_style', 'minimal')} | Archetype: {b.get('brand_archetype', 'visionary')}\n"
        f"- Emotional positioning: {b.get('emotional_positioning', '')}\n"
        f"- Audience psychology: {audience or 'strategic buyers'}\n"
        f"- Stability: tone_conf={b.get('tone_confidence', 0.7):.2f} "
        f"personality_conf={b.get('personality_confidence', 0.7):.2f}\n"
        + (f"- PREFERRED language: {preferred}\n" if preferred else "")
        + (f"- REJECTED language (never use): {rejected}\n" if rejected else "")
        + "- If user request conflicts with brand brain, surface the tension and ask whether to evolve direction.\n"
    )
