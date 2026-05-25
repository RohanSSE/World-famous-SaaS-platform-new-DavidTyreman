"""
Uncertainty-aware generation — exploratory vs authoritative modes.
"""
from __future__ import annotations

from typing import Any, Dict, Tuple

from django.conf import settings

EXPLORATORY_THRESHOLD = 0.50
MODERATE_THRESHOLD = 0.65


def select_generation_mode(confidence_score: float) -> str:
    if confidence_score < float(getattr(settings, "UNCERTAINTY_EXPLORATORY_THRESHOLD", EXPLORATORY_THRESHOLD)):
        return "exploratory"
    if confidence_score < float(getattr(settings, "UNCERTAINTY_MODERATE_THRESHOLD", MODERATE_THRESHOLD)):
        return "calibrated"
    return "authoritative"


def generation_mode_prompt(mode: str, confidence_score: float) -> str:
    if mode == "exploratory":
        return (
            f"\nGENERATION MODE: EXPLORATORY (confidence {confidence_score:.2f})\n"
            "- Do NOT state definitive strategic guarantees.\n"
            "- Use: 'it appears', 'the available context suggests', 'one plausible reading is'.\n"
            "- Ask one clarifying question if context is thin.\n"
            "- Prefer manifesto-grounded hypotheses over generic advice.\n"
        )
    if mode == "calibrated":
        return (
            f"\nGENERATION MODE: CALIBRATED (confidence {confidence_score:.2f})\n"
            "- Ground claims in retrieved knowledge; hedge where evidence is partial.\n"
            "- Avoid viral/growth-hack framing unless explicitly in context.\n"
        )
    return (
        f"\nGENERATION MODE: AUTHORITATIVE (confidence {confidence_score:.2f})\n"
        "- Speak with strategic clarity while staying manifesto-grounded.\n"
        "- No generic marketing filler.\n"
    )


def apply_uncertainty_to_temperature(
    mode: str,
    base_temperature: float = 0.7,
) -> float:
    if mode == "exploratory":
        return float(getattr(settings, "UNCERTAINTY_EXPLORATORY_TEMPERATURE", 0.2))
    if mode == "authoritative":
        return max(0.4, base_temperature - 0.15)
    return max(0.35, base_temperature - 0.1)


def uncertainty_generation_config(confidence_score: float) -> Dict[str, Any]:
    mode = select_generation_mode(confidence_score)
    return {
        "generation_mode": mode,
        "confidence_score": round(confidence_score, 3),
        "mode_prompt": generation_mode_prompt(mode, confidence_score),
        "temperature_adjustment": apply_uncertainty_to_temperature(mode),
    }
