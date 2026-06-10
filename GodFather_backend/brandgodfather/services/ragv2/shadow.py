from __future__ import annotations

import re
from typing import Any, Dict

from brandgodfather.services.ragv2.llm_client import call_llm

SELF_IMAGE_RE = re.compile(r"\b(i am|i have|i always|my brand is)\b(.+)", re.IGNORECASE)


def update_shadow_profile(shadow: Dict[str, Any], prosody_result: Dict[str, Any], raw_answer: str, question_id: int) -> Dict[str, Any]:
    s = dict(shadow or {})
    s.setdefault("self_image", "")
    s.setdefault("actual_signal", "")
    s.setdefault("gap_score", 0.0)
    s.setdefault("fear_pattern", "")
    s.setdefault("avoidance_topic", "")
    s.setdefault("readiness_estimate", 5.0)
    s.setdefault("contradictions", [])

    m = SELF_IMAGE_RE.search(raw_answer or "")
    if m:
        s["self_image"] = (m.group(0) or "").strip()[:280]

    resistance = prosody_result.get("resistance_level", "medium")
    flags = prosody_result.get("flags", {}) or {}

    if resistance == "high" or bool(flags.get("deflection")):
        s["actual_signal"] = "vendor-level thinking detected"
    elif resistance == "low":
        s["actual_signal"] = "brand-level clarity emerging"

    gap_raw = 1.0 if "vendor" in str(s.get("actual_signal", "")).lower() else 0.0
    s["gap_score"] = round(float(s.get("gap_score", 0.0)) * 0.7 + (gap_raw * 0.3), 2)

    if bool(flags.get("avoidance_length")):
        s["fear_pattern"] = f"avoidance of depth on Q{question_id}"

    ew = float((flags.get("emotional_weight") or {}).get("emotional_weight", 0.5) or 0.5)
    new_est = float(s.get("readiness_estimate", 5.0)) * 0.8 + (ew * 10 * 0.2)
    s["readiness_estimate"] = round(max(1.0, min(10.0, new_est)), 1)
    return s


def check_contradictions(session_id: str, raw_answer: str, current_question: int) -> Dict[str, Any]:
    # Lightweight contradiction probe using targeted LLM check.
    # Historical retrieval can be extended with ES similarity in next iteration.
    probe = {
        "found": False,
        "contradictions": [],
        "challenge_addition": "",
    }
    if not raw_answer or len(raw_answer.split()) < 8:
        return probe

    system = "You detect strategic contradictions. Respond in strict JSON only."
    user = (
        "Given this single answer and no history, return JSON: "
        '{"contradicts": false, "reason": ""}. '
        f"Answer on Q{current_question}: {raw_answer}"
    )
    out = call_llm(system, user)
    if str(out.get("gate_status", "")).upper() == "REJECT":
        probe["found"] = True
        reason = str(out.get("challenge_type") or "potential contradiction")
        probe["contradictions"].append(
            {
                "q_current": int(current_question),
                "q_previous": 0,
                "reason": reason,
            }
        )
        probe["challenge_addition"] = f"Possible contradiction — {reason}"
    return probe
