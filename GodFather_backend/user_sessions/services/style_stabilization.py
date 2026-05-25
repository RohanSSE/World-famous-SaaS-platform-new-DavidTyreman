"""
Strategic style stabilization — identity continuity across turns.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

DEFAULT_STYLE_VECTOR = {
    "authority": 0.88,
    "restraint": 0.85,
    "clarity": 0.90,
    "aggression": 0.14,
    "warmth": 0.45,
}


def get_style_vector(session_id: Optional[int] = None) -> Dict[str, float]:
    if session_id:
        try:
            from user_sessions.services.strategic_style_memory import get_strategic_style

            style = get_strategic_style(session_id)
            evo = style.get("evolution", {})
            prefs = evo.get("strategic_preferences", style.get("strategic_preferences", {}))
            return {
                "authority": float(prefs.get("authority", 0.88)),
                "restraint": float(prefs.get("trust", 0.85)),
                "clarity": float(evo.get("tone_confidence", 0.9)),
                "aggression": float(prefs.get("playful", 0.14)),
                "warmth": 0.45,
            }
        except Exception:
            pass
    return dict(DEFAULT_STYLE_VECTOR)


def score_style_deviation(answer: str, style_vector: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
    """
    How far answer deviates from stabilized style vector.
    """
    style_vector = style_vector or DEFAULT_STYLE_VECTOR
    a = answer.lower()
    signals = {
        "authority": sum(1 for w in ("authoritative", "definitive", "expert", "command") if w in a),
        "restraint": sum(1 for w in ("restraint", "measured", "disciplined", "controlled") if w in a),
        "clarity": sum(1 for w in ("clear", "clarity", "precise", "specific") if w in a),
        "aggression": sum(1 for w in ("viral", "aggressive", "dominate", "crush", "hustle") if w in a),
        "warmth": sum(1 for w in ("warm", "friendly", "casual", "hey") if w in a),
    }
    # Normalize signals to 0-1
    observed = {k: min(1.0, v / 2.0) for k, v in signals.items()}

    deviation = 0.0
    for dim, target in style_vector.items():
        obs = observed.get(dim, 0.3 if dim in ("authority", "clarity") else 0.1)
        deviation += abs(obs - target)
    deviation /= max(len(style_vector), 1)

    return {
        "style_deviation_score": round(min(1.0, deviation), 3),
        "style_vector": style_vector,
        "observed_signals": observed,
        "style_stable": deviation < 0.35,
    }


def style_stabilization_prompt(deviation: Dict[str, Any]) -> str:
    if deviation.get("style_stable", True):
        sv = deviation.get("style_vector", {})
        return (
            f"\nSTYLE ANCHOR: authority={sv.get('authority', 0.88):.2f}, "
            f"restraint={sv.get('restraint', 0.85):.2f}, aggression={sv.get('aggression', 0.14):.2f}\n"
        )
    return (
        "\nSTYLE CORRECTION: Prior tone drifted from brand identity. "
        "Restore authoritative, restrained, brand-book-grounded voice.\n"
    )
