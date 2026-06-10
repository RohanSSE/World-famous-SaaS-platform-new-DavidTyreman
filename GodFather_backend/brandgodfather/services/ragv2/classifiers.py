from __future__ import annotations

import hashlib
from typing import Any, Dict, List

from brandgodfather.services.prosody_classifier import get_classifier

HARD_FAIL_PATTERNS = [
    "we offer",
    "quality service",
    "competitive pricing",
    "best in class",
    "one stop shop",
    "full service",
    "industry leading",
    "passionate about",
    "results-driven",
    "innovative solutions",
    "seamless experience",
    "synergy",
    "leverage",
    "holistic approach",
    "customer-centric",
]


class VendorLanguageFilter:
    def check(self, text: str) -> Dict[str, Any]:
        lower = (text or "").lower()
        matched = [p for p in HARD_FAIL_PATTERNS if p in lower]
        return {"fail": bool(matched), "matched_patterns": matched}


class ProsodyClassifierAdapter:
    """Adapter around the existing BrandGodFather classifier to match RAGv2 schema."""

    def __init__(self) -> None:
        self._classifier = get_classifier()

    def analyze(self, answer: str, question_prompt: str, phase: str) -> Dict[str, Any]:
        if self._classifier is None:
            return {
                "flags": {
                    "hedging": False,
                    "deflection": False,
                    "avoidance_length": False,
                    "passive_voice": False,
                    "question_echo": False,
                    "money_motivation": False,
                    "emotional_weight": {"dominant_emotion": "neutral", "emotional_weight": 0.5},
                },
                "resistance_level": "low",
                "should_challenge": False,
                "challenge_reason": "classifier_unavailable",
            }

        result = self._classifier.analyze(answer=answer, question=question_prompt, phase=phase)
        data = result.model_dump() if hasattr(result, "model_dump") else dict(result)

        signals = {
            "hedging": bool(float(data.get("hedge_score", 0)) > 0.15),
            "deflection": bool(data.get("deflection_detected", False)),
            "avoidance_length": bool(data.get("avoidance_length", False)),
            "passive_voice": bool(data.get("passive_voice", False)),
            "question_echo": bool(data.get("question_echo", False)),
            "money_motivation": bool(data.get("money_motivation", False)),
            "emotional_weight": {
                "dominant_emotion": "neutral",
                "emotional_weight": float(data.get("emotional_weight", 0.5) or 0.5),
            },
        }

        fired = sum(
            int(bool(v))
            for k, v in signals.items()
            if k != "emotional_weight"
        )
        resistance = "low" if fired == 0 else ("medium" if fired <= 2 else "high")
        should_challenge = resistance in {"medium", "high"}

        reason = data.get("vendor_phrases_found") or []
        reason_text = ", ".join(reason[:3]) if reason else "insufficient_depth"

        return {
            "flags": signals,
            "resistance_level": resistance,
            "should_challenge": should_challenge,
            "challenge_reason": reason_text,
            "pressure_recommendation": int(data.get("pressure_recommendation", 3) or 3),
        }


def vendor_challenge_message(matched_patterns: List[str]) -> str:
    variants = [
        "That language belongs to a brochure, not a brand. Strip away what you offer and tell me what you believe.",
        "You are describing services, not conviction. Name the belief beneath the offer.",
        "This sounds vendor-safe. I need the emotional truth, not packaged positioning.",
        "Feature language keeps you replaceable. Tell me what you stand for instead.",
        "This answer protects comfort, not clarity. State the principle you refuse to compromise.",
    ]
    key = "|".join(sorted(matched_patterns))
    index = int(hashlib.sha1(key.encode("utf-8")).hexdigest(), 16) % len(variants)
    return variants[index]
