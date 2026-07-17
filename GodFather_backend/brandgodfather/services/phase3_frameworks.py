"""Phase 3 (Questions 1-10) ORB analysis frameworks.

Single source of truth for the per-question discovery IDs, confidence
thresholds, and ``look_for`` / ``avoid`` criteria used by phase-questions/3.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, Optional


PHASE3_FRAMEWORKS: Dict[str, Dict[str, Any]] = {
    "Q1": {
        "question": "What can customers expect from your business?",
        "associated_discovery_id": "D_6.2_BRAND_PROMISE",
        "target_confidence_threshold": 85,
        "orb_analysis_framework": {
            "look_for": [
                "a consistent emotional guarantee or psychological outcome",
                "commitments that transcend the functional delivery of the product or service",
                "promises rooted in the founder's core beliefs and values",
                "evidence of a standard they would willingly lose money to uphold",
            ],
            "avoid": [
                "vendor-level functional promises (e.g., 'we will deliver on time', 'good quality')",
                "generic corporate guarantees ('100% satisfaction')",
                "promises that any competitor in the space could easily claim",
                "focusing on the mechanics of the service rather than the meaning of the experience",
            ],
        },
    },
    "Q2": {
        "question": "Why will people recommend you?",
        "associated_discovery_id": "D_4.2_BRAND_ADVOCACY",
        "target_confidence_threshold": 85,
        "orb_analysis_framework": {
            "look_for": [
                "customers advocating for a shared belief, cause, or movement",
                "exceptional emotional transformation that the customer wants others to experience",
                "the customer feeling deeply understood and validated as a human being",
                "word-of-mouth driven by strategic uniqueness and distinct brand energy",
            ],
            "avoid": [
                "transactional referral incentives (e.g., 'they get $10 off for referring')",
                "vendor thinking (e.g., 'because we are cheaper or faster')",
                "generic satisfaction ('because we did a good job')",
                "assuming the physical product features alone will drive advocacy",
            ],
        },
    },
    "Q3": {
        "question": "What will people say about you?",
        "associated_discovery_id": "D_8.2_BRAND_REPUTATION",
        "target_confidence_threshold": 85,
        "orb_analysis_framework": {
            "look_for": [
                "legacy thinking and long-term strategic positioning",
                "reputation tied to a specific stance, philosophy, or unconventional method",
                "emotional resonance in how the market perceives their identity",
                "being known for changing the industry or improving lives",
            ],
            "avoid": [
                "purely functional descriptions ('they make good software')",
                "safe, universally agreeable praise ('they are nice people to work with')",
                "vendor-centric praise ('they have the best prices')",
                "lack of clarity or vision regarding their long-term market perception",
            ],
        },
    },
    "Q4": {
        "question": "What work do you want more/less of?",
        "associated_discovery_id": "D_9.1_STRATEGIC_ALIGNMENT",
        "target_confidence_threshold": 80,
        "orb_analysis_framework": {
            "look_for": [
                "actively seeking work that aligns with their purpose and desired customer transformation",
                "identifying misaligned revenue streams to shed",
                "clear boundaries that protect the brand's energy and strategic focus",
                "prioritizing high-value, high-meaning work over transactional volume",
            ],
            "avoid": [
                "fear-based hoarding ('we want all the work we can get')",
                "inability to distinguish between profitable work and brand-building work",
                "vendor thinking (valuing any paying customer regardless of fit)",
                "lack of strategic direction regarding their product or service suite",
            ],
        },
    },
    "Q5": {
        "question": "What are you avoiding?",
        "associated_discovery_id": "D_1.3_CURRENT_STRATEGIC_REALITY",
        "target_confidence_threshold": 80,
        "orb_analysis_framework": {
            "look_for": [
                "honest admission of strategic blind spots, limiting beliefs, or fears",
                "emotional vulnerability regarding difficult decisions (e.g., firing bad clients, raising prices)",
                "acknowledging the discomfort of moving from vendor thinking to brand leadership",
                "recognition of inherited industry assumptions they have been afraid to challenge",
            ],
            "avoid": [
                "superficial operational complaints (e.g., 'I am avoiding doing my taxes')",
                "defensiveness or claiming they are avoiding nothing",
                "blaming external factors (competitors, economy) rather than internal hesitation",
                "lack of introspection or self-awareness",
            ],
        },
    },
    "Q6": {
        "question": "Where are you playing small?",
        "associated_discovery_id": "D_8.1_VISION_AND_POTENTIAL",
        "target_confidence_threshold": 85,
        "orb_analysis_framework": {
            "look_for": [
                "recognizing untapped potential and undervalued assets",
                "acknowledging where they have let competitors dictate their strategy or pricing",
                "realizing they have been competing as a commodity rather than a distinct brand",
                "a desire for long-term strategic growth over short-term tactical survival",
            ],
            "avoid": [
                "arrogance or denial ('we aren't playing small, we are the best')",
                "focusing on minor operational constraints (e.g., 'our office is too small')",
                "fear of charging appropriately disguised as 'helping people'",
                "satisfaction with the status quo if it conflicts with their stated purpose",
            ],
        },
    },
    "Q7": {
        "question": "Are you willing to stand out?",
        "associated_discovery_id": "D_5.1_STRATEGIC_COURAGE",
        "target_confidence_threshold": 85,
        "orb_analysis_framework": {
            "look_for": [
                "courage to polarize the market and alienate the wrong fit",
                "commitment to holding an unconventional perspective or philosophy",
                "willingness to abandon the safety of looking and sounding like competitors",
                "embracing a distinct brand energy and identity",
            ],
            "avoid": [
                "the desire to stand out while simultaneously pleasing everyone",
                "seeking safe or generic differentiation (e.g., 'we stand out with our quality')",
                "fear of criticism or rejection from industry peers",
                "viewing differentiation as a purely visual marketing exercise",
            ],
        },
    },
    "Q8": {
        "question": "What will you stop doing?",
        "associated_discovery_id": "D_9.3_STRATEGIC_SACRIFICE",
        "target_confidence_threshold": 85,
        "orb_analysis_framework": {
            "look_for": [
                "intentional strategic sacrifices to protect brand integrity",
                "commitment to shedding vendor habits (e.g., price matching, competing on features)",
                "firing misaligned clients or abandoning misaligned services",
                "understanding that strategy is as much about what you say 'no' to as what you say 'yes' to",
            ],
            "avoid": [
                "superficial operational stops (e.g., 'I will stop checking email so late')",
                "unwillingness to sacrifice any revenue for the sake of the brand",
                "vague promises without specific behavioral changes attached",
                "fear of letting go of legacy systems that no longer serve the vision",
            ],
        },
    },
    "Q9": {
        "question": "How ready are you (1-10)?",
        "associated_discovery_id": "D_1.4_STRATEGIC_READINESS",
        "target_confidence_threshold": 90,
        "orb_analysis_framework": {
            "look_for": [
                "honest, introspective assessment of their emotional and strategic readiness",
                "understanding that the journey will require challenging deep-seated assumptions",
                "demonstrating curiosity, openness, and a willingness to learn",
                "commitment to the transformation process over quick fixes",
            ],
            "avoid": [
                "artificial '10s' given without understanding the required effort or sacrifice",
                "treating the question like a superficial survey metric",
                "defensiveness or impatience to 'just get the brand book finished'",
                "signs of high emotional resistance or vendor-level focus on speed",
            ],
        },
    },
    "Q10": {
        "question": "Are you ready to proceed?",
        "associated_discovery_id": "D_STAGE_TRANSITION",
        "target_confidence_threshold": 90,
        "orb_analysis_framework": {
            "look_for": [
                "a clear, demonstrated cognitive shift from tactical vendor thinking to strategic brand thinking",
                "authentic curiosity replacing previous assumptions",
                "explicit commitment to discovering truth rather than just collecting answers",
                "alignment between the founder's emotional readiness and the strategic requirements of the next stage",
            ],
            "avoid": [
                "hesitation masked as compliance",
                "wanting to proceed merely because the question flow is complete",
                "unresolved contradictions in their core identity or purpose",
                "viewing ORB as a questionnaire rather than a strategic advisor",
            ],
        },
    },
}


ORB_PHASE3_FRAMEWORK: Dict[str, Dict[str, Any]] = {
    entry["question"]: {
        "associated_discovery_id": entry["associated_discovery_id"],
        "target_confidence_threshold": entry["target_confidence_threshold"],
        "look_for": entry["orb_analysis_framework"]["look_for"],
        "avoid": entry["orb_analysis_framework"]["avoid"],
    }
    for entry in PHASE3_FRAMEWORKS.values()
}


def _normalize_phase3_question_text(question_text: str) -> str:
    text = str(question_text or "").strip().lower()
    text = text.replace("won't", "wont")
    text = text.replace("1-10", "1 10")
    text = re.sub(r"^\s*(?:q(?:uestion)?\.?\s*)?\d+\s*[\).:-]?\s*", "", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def match_phase3_orb_framework(question_text: Optional[str]) -> Optional[Dict[str, Any]]:
    """Return the Phase 3 ORB framework matching a DB or frontend question."""
    normalized_question = _normalize_phase3_question_text(question_text or "")
    if not normalized_question:
        return None

    for q_id, entry in PHASE3_FRAMEWORKS.items():
        canonical_question = entry["question"]
        normalized_canonical = _normalize_phase3_question_text(canonical_question)
        if normalized_canonical in normalized_question or normalized_question in normalized_canonical:
            framework = entry["orb_analysis_framework"]
            return {
                "phase": 3,
                "q_id": q_id,
                "question": canonical_question,
                "associated_discovery_id": entry["associated_discovery_id"],
                "target_confidence_threshold": entry["target_confidence_threshold"],
                "look_for": framework["look_for"],
                "avoid": framework["avoid"],
            }
    return None


def get_phase3_framework(q_id: Optional[str]) -> Optional[Dict[str, Any]]:
    """Return the Phase 3 framework entry for a q_id, or None if out of scope."""
    if not q_id:
        return None
    return PHASE3_FRAMEWORKS.get(str(q_id).strip().upper())


def phase3_framework_json(q_id: Optional[str]) -> Optional[str]:
    """Return the Phase 3 orb_analysis_framework JSON string for a q_id."""
    entry = get_phase3_framework(q_id)
    if not entry:
        return None
    return json.dumps(
        {"orb_analysis_framework": entry["orb_analysis_framework"]},
        indent=2,
        ensure_ascii=False,
    )