from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class BreakthroughResult(BaseModel):
    breakthrough_detected: bool
    breakthrough_score: float
    breakthrough_type: str
    breakthrough_reason: str
    brand_seed_candidate: str
    criteria: Dict[str, bool]
    evidence: List[str]


class BreakthroughRecognitionService:
    VENDOR_PATTERNS = [
        r"\bwe provide\b",
        r"\bwe offer\b",
        r"\bour services\b",
        r"\bsolutions\b",
        r"\bquality\b",
        r"\bprofessional\b",
        r"\binnovative\b",
        r"\bbest service\b",
    ]

    SPECIFICITY_PATTERNS = [
        r"\bfounders like me\b",
        r"\bpeople like us\b",
        r"\bfor [a-z0-9' -]+ who\b",
        r"\bwhen [a-z0-9' -]+\b",
        r"\bbecause\b",
        r"\bmy\b",
        r"\bour\b",
        r"\bnot for\b",
    ]

    EMOTIONAL_TRUTH_PATTERNS = [
        r"\bafraid\b",
        r"\bfear\b",
        r"\bashamed\b",
        r"\bhide\b",
        r"\bhiding\b",
        r"\bseen\b",
        r"\bbelong\b",
        r"\btrust\b",
        r"\btruth\b",
        r"\bcourage\b",
        r"\blonely\b",
        r"\bproud\b",
        r"\blove\b",
    ]

    TENSION_PATTERNS = [
        r"\bbut\b",
        r"\byet\b",
        r"\binstead of\b",
        r"\bnot [a-z0-9' -]+ but\b",
        r"\brefuse to\b",
        r"\bhide behind\b",
        r"\bafraid to\b",
        r"\bline in the sand\b",
        r"\bno longer\b",
    ]

    BEHAVIOR_PATTERNS = [
        r"\bshow up\b",
        r"\bdo differently\b",
        r"\bbehave\b",
        r"\bchoose\b",
        r"\bbuilt this because\b",
        r"\bhide behind\b",
        r"\bstand for\b",
        r"\brefuse to\b",
        r"\bso they can\b",
        r"\bso that\b",
    ]

    def analyze(
        self,
        *,
        answer: str,
        q_id: str,
        question_text: str,
        prosody_result: Dict[str, Any],
        contradiction_result: Optional[Dict[str, Any]] = None,
    ) -> BreakthroughResult:
        text = (answer or "").strip()
        lowered = text.lower()
        words = re.findall(r"\b[\w']+\b", lowered)
        vendor_hits = self._hits(lowered, self.VENDOR_PATTERNS)

        criteria = {
            "specificity": bool(self._hits(lowered, self.SPECIFICITY_PATTERNS)) and len(words) >= 10,
            "emotional_truth": bool(self._hits(lowered, self.EMOTIONAL_TRUTH_PATTERNS)),
            "strategic_tension": bool(self._hits(lowered, self.TENSION_PATTERNS)),
            "behavior_proof": bool(self._hits(lowered, self.BEHAVIOR_PATTERNS)),
            "vendor_language_removed": not vendor_hits and bool(prosody_result.get("gate_1_pass", True)),
            "contradiction_resolved": not bool((contradiction_result or {}).get("has_contradiction")),
        }

        weights = {
            "specificity": 0.2,
            "emotional_truth": 0.24,
            "strategic_tension": 0.18,
            "behavior_proof": 0.18,
            "vendor_language_removed": 0.12,
            "contradiction_resolved": 0.08,
        }
        raw_score = sum(weight for key, weight in weights.items() if criteria.get(key))
        depth_bonus = min(0.08, max(0, len(words) - 12) * 0.01)
        penalty = 0.2 if bool(prosody_result.get("avoidance_length")) else 0.0
        score = round(max(0.0, min(1.0, raw_score + depth_bonus - penalty)), 4)

        detected = (
            score >= 0.72
            and criteria["specificity"]
            and criteria["emotional_truth"]
            and criteria["vendor_language_removed"]
            and not bool(prosody_result.get("question_echo"))
        )

        seed = self._seed_candidate(text)
        evidence = self._evidence(criteria)
        reason = self._reason(detected=detected, score=score, seed=seed, evidence=evidence)
        breakthrough_type = "emotional_truth_edge" if detected else "none"

        return BreakthroughResult(
            breakthrough_detected=detected,
            breakthrough_score=score,
            breakthrough_type=breakthrough_type,
            breakthrough_reason=reason,
            brand_seed_candidate=seed if detected else "",
            criteria=criteria,
            evidence=evidence,
        )

    @staticmethod
    def _hits(text: str, patterns: List[str]) -> List[str]:
        return [pattern for pattern in patterns if re.search(pattern, text)]

    @staticmethod
    def _seed_candidate(answer: str) -> str:
        parts = [part.strip() for part in re.split(r"[.!?]", answer or "") if part.strip()]
        if not parts:
            return (answer or "").strip()[:220]
        parts.sort(key=len, reverse=True)
        return parts[0][:220]

    @staticmethod
    def _evidence(criteria: Dict[str, bool]) -> List[str]:
        labels = {
            "specificity": "specific audience or context",
            "emotional_truth": "emotional truth",
            "strategic_tension": "strategic tension",
            "behavior_proof": "behavioral proof",
            "vendor_language_removed": "vendor language removed",
            "contradiction_resolved": "no unresolved contradiction",
        }
        return [label for key, label in labels.items() if criteria.get(key)]

    @staticmethod
    def _reason(*, detected: bool, score: float, seed: str, evidence: List[str]) -> str:
        if detected:
            return (
                "It has "
                f"{', '.join(evidence[:4])} and gives the brand a seed to remember: {seed}"
            )
        return f"No breakthrough yet. Score {score:.2f}; keep pushing for specificity, emotional truth, tension, and behavior."