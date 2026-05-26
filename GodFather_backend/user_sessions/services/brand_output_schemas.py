"""
Structured brand deliverable schemas — product-facing outputs.
"""
from __future__ import annotations

from typing import Any, Dict, List

BRAND_OUTPUT_SCHEMA: Dict[str, Any] = {
    "brand_dna": {
        "core_beliefs": [],
        "non_negotiables": [],
        "emotional_promise": "",
        "differentiation_anchor": "",
    },
    "tone_rules": {
        "voice": "",
        "energy": "",
        "forbidden": [],
        "preferred": [],
    },
    "messaging_pillars": [],
    "audience_psychology": {
        "primary_persona": "",
        "motivations": [],
        "pain_points": [],
        "desired_identity": "",
    },
    "communication_rules": [],
    "founder_narrative": {
        "origin": "",
        "conviction": "",
        "founder_voice": "",
    },
    "positioning": {
        "category": "",
        "role": "",
        "competitive_frame": "",
    },
    "emotional_identity": {
        "felt_experience": "",
        "aspirational_state": "",
    },
    "campaign_direction": {
        "strategic_theme": "",
        "channels_hint": [],
        "guardrails": [],
    },
}


def empty_brand_output() -> Dict[str, Any]:
    import copy
    return copy.deepcopy(BRAND_OUTPUT_SCHEMA)


def narrative_to_structured_sections(narrative: str, anchors: Dict[str, Any]) -> Dict[str, Any]:
    """Light structuring from narrative + anchors (no extra LLM)."""
    out = empty_brand_output()
    phrases = anchors.get("signature_phrases") or []
    if phrases:
        out["messaging_pillars"] = phrases[:5]
        out["tone_rules"]["preferred"] = phrases[:8]
    if narrative:
        out["brand_dna"]["emotional_promise"] = narrative[:500]
        out["positioning"]["competitive_frame"] = narrative[:300]
    out["tone_rules"]["forbidden"] = [
        "viral", "growth hack", "dominate", "aggressive growth", "10x",
    ]
    out["tone_rules"]["preferred"] = list(
        dict.fromkeys(
            (out["tone_rules"].get("preferred") or [])
            + ["quiet authority", "crafted precision", "earned credibility"]
        )
    )[:10]
    return out
