"""
Human feedback learning — adaptive brand intelligence from client edits.
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from .brand_brain import evolve_brand_brain, get_brand_brain
from .rag_evaluation import _token_set, _sentences

FEEDBACK_MEMORY_KEY = "feedback_learning_profile"
ACCEPTED_PHRASES_KEY = "feedback_accepted_phrases"

REJECT_SIGNALS = re.compile(
    r"\b(viral|growth hack|10x|dominate|aggressive|hustle|cheap|discount|mass market)\b",
    re.I,
)
PREFER_SIGNALS = re.compile(
    r"\b(crafted|precision|quiet authority|premium|trust|restraint|enduring|manifesto|brand book)\b",
    re.I,
)
EMOTIONAL_PREFER = re.compile(
    r"\b(restraint|calm|premium|trust|authority|crafted|enduring|quiet|confidence)\b",
    re.I,
)
TONE_PREFER = re.compile(
    r"\b(authoritative|minimal|direct|measured|principle|declarative)\b",
    re.I,
)


def _extract_phrase_signals(text: str) -> Dict[str, List[str]]:
    lower = (text or "").lower()
    preferred = list(dict.fromkeys(PREFER_SIGNALS.findall(lower)))[:10]
    rejected = list(dict.fromkeys(REJECT_SIGNALS.findall(lower)))[:10]
    return {"preferred_phrases": preferred, "rejected_phrases": rejected}


def _diff_signals(original: str, edited: str) -> Dict[str, Any]:
    """What user added vs removed — tone, positioning, emotional preference."""
    orig_t = _token_set(original)
    edit_t = _token_set(edited)
    added = edit_t - orig_t
    removed = orig_t - edit_t

    preferred = [w for w in added if len(w) > 4 and w not in ("should", "would", "their")]
    rejected = [w for w in removed if len(w) > 4]

    orig_sig = _extract_phrase_signals(original)
    edit_sig = _extract_phrase_signals(edited)
    edited_blob = edited.lower()

    accepted_phrases = []
    for sent in _sentences(edited):
        if len(sent) > 25 and sent.lower() not in (original or "").lower():
            accepted_phrases.append(sent[:120])
    accepted_phrases = accepted_phrases[:5]

    return {
        "preferred_phrases": list(
            dict.fromkeys(preferred[:8] + edit_sig["preferred_phrases"])
        )[:12],
        "rejected_phrases": list(
            dict.fromkeys(rejected[:8] + orig_sig["rejected_phrases"] + edit_sig["rejected_phrases"])
        )[:12],
        "rejected_positioning": list(dict.fromkeys(REJECT_SIGNALS.findall(edited_blob)))[:8],
        "tone_preference": list(dict.fromkeys(TONE_PREFER.findall(edited_blob)))[:6],
        "emotional_preference": list(dict.fromkeys(EMOTIONAL_PREFER.findall(edited_blob)))[:6],
        "accepted_phrases": accepted_phrases,
        "tokens_added": len(added),
        "tokens_removed": len(removed),
        "edit_ratio": round(len(edit_t) / max(len(orig_t), 1), 3),
    }


def _accumulate_accepted_phrases(session_id: int, new_phrases: List[str], user=None) -> List[str]:
    try:
        from user_sessions.models import BrandMemory

        row = BrandMemory.objects.filter(session_id=session_id, key=ACCEPTED_PHRASES_KEY).first()
        existing = []
        if row and row.value:
            existing = list(row.value.get("phrases") or [])

        for p in new_phrases:
            if p and p not in existing:
                existing.append(p)

        existing = existing[-30:]
        BrandMemory.objects.update_or_create(
            session_id=session_id,
            key=ACCEPTED_PHRASES_KEY,
            defaults={
                "memory_type": "preference",
                "content": json.dumps(existing[-5], ensure_ascii=False)[:500],
                "value": {"phrases": existing},
                "importance_score": 0.88,
                "is_pinned": True,
                "created_by": user if user and getattr(user, "is_authenticated", False) else None,
            },
        )
        return existing
    except Exception:
        return new_phrases


def get_feedback_learning_profile(session_id: Optional[int]) -> Dict[str, Any]:
    """Read accumulated human feedback for a session."""
    if not session_id:
        return {}
    brain = get_brand_brain(session_id)
    profile = {}
    accepted = []
    try:
        from user_sessions.models import BrandMemory

        row = BrandMemory.objects.filter(session_id=session_id, key=FEEDBACK_MEMORY_KEY).first()
        if row and row.value:
            profile = row.value
        acc = BrandMemory.objects.filter(session_id=session_id, key=ACCEPTED_PHRASES_KEY).first()
        if acc and acc.value:
            accepted = list(acc.value.get("phrases") or [])
    except Exception:
        pass

    return {
        "preferred_language": brain.get("preferred_language") or [],
        "rejected_language": brain.get("rejected_language") or [],
        "tone_preference": profile.get("delta", {}).get("tone_preference", []),
        "emotional_preference": profile.get("delta", {}).get("emotional_preference", []),
        "accepted_phrases": accepted,
        "rejected_positioning": profile.get("delta", {}).get("rejected_positioning", []),
        "last_edit": profile.get("edited_preview", "")[:200],
        "evolution_history": brain.get("evolution_history") or [],
    }


def learn_from_human_edit(
    session_id: int,
    original_ai_text: str,
    edited_text: str,
    context: str = "",
    user=None,
    source: str = "answer_edit",
) -> Dict[str, Any]:
    """
    Client edited AI output → update brand brain + brand memory preferences.
    """
    if not session_id or not edited_text:
        return {"learned": False}

    delta = _diff_signals(original_ai_text or "", edited_text)
    brain = evolve_brand_brain(session_id, edited_text, feedback_delta=delta, user=user)
    accepted = _accumulate_accepted_phrases(session_id, delta.get("accepted_phrases", []), user=user)

    try:
        from user_sessions.models import BrandMemory

        profile = {
            "source": source,
            "delta": delta,
            "original_preview": (original_ai_text or "")[:400],
            "edited_preview": edited_text[:400],
            "accepted_phrases_total": accepted[-10:],
        }
        BrandMemory.objects.update_or_create(
            session_id=session_id,
            key=FEEDBACK_MEMORY_KEY,
            defaults={
                "memory_type": "preference",
                "content": f"Feedback: +{delta.get('preferred_phrases', [])} -{delta.get('rejected_phrases', [])}",
                "value": profile,
                "importance_score": 0.9,
                "is_pinned": True,
                "created_by": user if user and getattr(user, "is_authenticated", False) else None,
            },
        )

        for phrase in delta.get("rejected_phrases", [])[:5]:
            BrandMemory.objects.update_or_create(
                session_id=session_id,
                key=f"rejected:{phrase[:40]}",
                defaults={
                    "memory_type": "rejected_strategy",
                    "content": f"User rejected: {phrase}",
                    "value": {"phrase": phrase},
                    "importance_score": 0.85,
                    "is_pinned": True,
                },
            )

        for phrase in delta.get("preferred_phrases", [])[:5]:
            BrandMemory.objects.update_or_create(
                session_id=session_id,
                key=f"preferred:{phrase[:40]}",
                defaults={
                    "memory_type": "preference",
                    "content": f"User preferred: {phrase}",
                    "value": {"phrase": phrase},
                    "importance_score": 0.8,
                },
            )
    except Exception:
        pass

    return {
        "learned": True,
        "feedback_delta": delta,
        "brand_brain": brain,
        "profile": get_feedback_learning_profile(session_id),
    }


def feedback_learning_prompt(session_id: Optional[int]) -> str:
    """Inject learned preferences into generation."""
    if not session_id:
        return ""
    profile = get_feedback_learning_profile(session_id)
    rejected = profile.get("rejected_language") or []
    preferred = profile.get("preferred_language") or []
    accepted = profile.get("accepted_phrases") or []
    if not rejected and not preferred and not accepted:
        return ""
    lines = ["\nHUMAN FEEDBACK LEARNING (from prior client edits):"]
    if preferred:
        lines.append(f"- Prefer language: {', '.join(preferred[:8])}")
    if accepted:
        lines.append(f"- Client-approved phrasing: {' | '.join(accepted[:3])}")
    if rejected:
        lines.append(f"- Never use: {', '.join(rejected[:8])}")
    if profile.get("emotional_preference"):
        lines.append(f"- Emotional preference: {', '.join(profile['emotional_preference'][:5])}")
    if profile.get("tone_preference"):
        lines.append(f"- Tone preference: {', '.join(profile['tone_preference'][:5])}")
    return "\n".join(lines) + "\n"
