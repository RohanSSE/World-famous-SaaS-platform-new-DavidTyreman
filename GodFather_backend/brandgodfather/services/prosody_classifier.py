"""
Gate 1 + Gate 2 prosody analysis layer for the BrandGodFather coaching system.

Gate 1 (hard reject):  vendor language detected
Gate 2 (soft signal):  2+ NLP signals fired

Loaded once in BrandGodFatherConfig.ready() and held in module-level singleton.
"""
from __future__ import annotations

import re
from functools import lru_cache
from typing import List, Optional

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Word / phrase lists
# ---------------------------------------------------------------------------

HEDGE_WORDS: List[str] = [
    "kind of", "maybe", "i guess", "sort of", "basically",
    "i think", "perhaps", "somewhat", "a bit", "might be",
    "could be", "i suppose", "not sure but", "hopefully",
]

VENDOR_PHRASES: List[str] = [
    "we provide", "we offer", "our services", "i provide", "quality service",
    "professional service", "quality professional service", "reliable solutions",
    "competitive pricing", "tailored solutions", "we specialize",
    "our team", "client satisfaction", "deliverables", "best service",
    "high quality", "world-class", "trusted partner", "one-stop solution",
]

MONEY_KEYWORDS: List[str] = [
    "profit", "income", "making a living", "revenue",
    "financial", "money", "earn", "sales target",
]

PHASE_MIN_WORDS = {"I": 15, "II": 15, "III": 15}
DEFAULT_MIN_WORDS = 8

# ---------------------------------------------------------------------------
# Pydantic result model
# ---------------------------------------------------------------------------

class ProsodyResult(BaseModel):
    vendor_language_detected: bool
    vendor_phrases_found: List[str]
    hedge_score: float = Field(ge=0.0, le=1.0)
    deflection_detected: bool
    passive_voice: bool
    question_echo: bool
    avoidance_length: bool
    money_motivation: bool
    emotional_weight: float = Field(ge=0.0, le=1.0)
    resistance_level: str                # low | medium | high
    gate_1_pass: bool
    gate_2_pass: bool
    pressure_recommendation: int = Field(ge=1, le=5)


# ---------------------------------------------------------------------------
# Classifier
# ---------------------------------------------------------------------------

class ProsodyClassifier:
    """
    Loads models once; call analyze() per user answer.
    """

    def __init__(
        self,
        spacy_model,          # pre-loaded spacy nlp object
        sentence_model,       # pre-loaded SentenceTransformer
        emotion_pipeline,     # pre-loaded HF pipeline
    ) -> None:
        self.nlp = spacy_model
        self.sentence_model = sentence_model
        self.emotion_pipeline = emotion_pipeline

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def analyze(self, answer: str, question: str, phase: str) -> ProsodyResult:
        lower = answer.lower()
        words = answer.split()

        # 1. Vendor language (Gate 1)
        vendor_phrases_found = [p for p in VENDOR_PHRASES if p in lower]
        vendor_language_detected = bool(vendor_phrases_found)

        # 2. Hedge score
        hedge_hits = sum(1 for h in HEDGE_WORDS if h in lower)
        hedge_score = min(hedge_hits / max(len(words), 1), 1.0)

        # 3. Passive voice via spacy dependency parse
        passive_voice = self._detect_passive(answer)

        # 4. Question echo via cosine similarity
        question_echo = self._detect_question_echo(answer, question)

        # 5. Deflection: more features/services than emotions + passive/echo
        deflection_detected = self._detect_deflection(
            answer, passive_voice, question_echo
        )

        # 6. Avoidance / length
        avoidance_length = self._detect_avoidance_length(words, phase)

        # 7. Money motivation
        money_motivation = any(k in lower for k in MONEY_KEYWORDS)

        # 8. Emotional weight
        emotional_weight = self._score_emotional_weight(answer)

        # 9. Resistance logic
        signals = [
            vendor_language_detected,
            hedge_score > 0.15,
            deflection_detected,
            passive_voice,
            question_echo,
            avoidance_length,
            money_motivation,
        ]
        signals_fired = sum(signals)

        resistance_level, pressure_recommendation = self._resistance(signals_fired)

        gate_1_pass = not vendor_language_detected
        gate_2_pass = signals_fired < 2

        return ProsodyResult(
            vendor_language_detected=vendor_language_detected,
            vendor_phrases_found=vendor_phrases_found,
            hedge_score=round(hedge_score, 4),
            deflection_detected=deflection_detected,
            passive_voice=passive_voice,
            question_echo=question_echo,
            avoidance_length=avoidance_length,
            money_motivation=money_motivation,
            emotional_weight=round(emotional_weight, 4),
            resistance_level=resistance_level,
            gate_1_pass=gate_1_pass,
            gate_2_pass=gate_2_pass,
            pressure_recommendation=pressure_recommendation,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _detect_passive(self, text: str) -> bool:
        doc = self.nlp(text)
        for token in doc:
            if token.dep_ in ("nsubjpass", "auxpass"):
                return True
        return False

    def _detect_question_echo(self, answer: str, question: str) -> bool:
        try:
            import numpy as np

            vecs = self.sentence_model.encode([answer, question], convert_to_numpy=True)
            a, b = vecs[0], vecs[1]
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)
            if norm_a == 0 or norm_b == 0:
                return False
            cosine = float(np.dot(a, b) / (norm_a * norm_b))
            return cosine > 0.65
        except Exception:
            return False

    def _detect_deflection(
        self, text: str, passive_voice: bool, question_echo: bool
    ) -> bool:
        lower = text.lower()
        feature_words = [
            "feature", "service", "offer", "provide", "solution",
            "product", "tool", "platform", "system", "capability",
        ]
        emotion_words = [
            "feel", "love", "hate", "fear", "hope", "believe",
            "care", "passion", "trust", "afraid", "excited",
        ]
        feature_count = sum(1 for w in feature_words if w in lower)
        emotion_count = sum(1 for w in emotion_words if w in lower)
        feature_heavy = feature_count > emotion_count + 1
        return feature_heavy or passive_voice or question_echo

    def _detect_avoidance_length(self, words: List[str], phase: str) -> bool:
        count = len(words)
        if count < DEFAULT_MIN_WORDS:
            return True
        min_words = PHASE_MIN_WORDS.get(phase.upper(), 0)
        if min_words and count < min_words:
            return True
        return False

    def _score_emotional_weight(self, text: str) -> float:
        try:
            results = self.emotion_pipeline(
                text[:512],
                top_k=None,
            )
            scores = {item["label"].lower(): item["score"] for item in results[0]}
            positive = scores.get("joy", 0.0) + scores.get("surprise", 0.0)
            # emotion-english-distilroberta-base has no explicit "trust" label
            negative = (
                scores.get("fear", 0.0)
                + scores.get("disgust", 0.0)
                + scores.get("sadness", 0.0)
                + scores.get("anger", 0.0)
            )
            raw = positive - negative  # range: -2 to +1 approximately
            normalized = (raw + 2.0) / 3.0  # shift to 0-1
            return max(0.0, min(1.0, normalized))
        except Exception:
            return 0.5

    @staticmethod
    def _resistance(signals_fired: int):
        if signals_fired <= 1:
            return "low", 2
        if signals_fired <= 3:
            return "medium", 3
        return "high", 5


# ---------------------------------------------------------------------------
# Module-level singleton (populated by AppConfig.ready())
# ---------------------------------------------------------------------------

_classifier_instance: Optional[ProsodyClassifier] = None


def get_classifier() -> Optional[ProsodyClassifier]:
    return _classifier_instance


def set_classifier(instance: ProsodyClassifier) -> None:
    global _classifier_instance
    _classifier_instance = instance
