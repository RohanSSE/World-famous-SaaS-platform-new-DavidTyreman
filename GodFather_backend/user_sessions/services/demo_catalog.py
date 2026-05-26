"""
Demo brand packs — investor/client one-click demos (no new cognition architecture).
"""
from __future__ import annotations

from typing import Any, Dict, List

DEMO_BRANDS: Dict[str, Dict[str, Any]] = {
    "luxury": {
        "id": "luxury",
        "label": "Luxury Heritage Brand",
        "tagline": "Quiet authority · Crafted permanence",
        "brand_operating_system": {
            "brand_dna": {
                "narrative": "We believe luxury is restraint made visible — never loud, never disposable.",
                "core_beliefs": ["Craft over scale", "Trust over hype", "Enduring over viral"],
                "emotional_promise": "Calm confidence for those who already have everything.",
            },
            "positioning": {
                "narrative": "Category: refined heritage house. Enemy: mass-premium noise. Win: manifesto-true scarcity.",
                "category_role": "Authoritative craft brand",
            },
            "tone_rules": {
                "narrative": "Voice: measured, declarative. Forbidden: hustle, 10x, viral. Preferred: crafted, enduring, trust.",
            },
            "messaging_pillars": {
                "pillars": [
                    {"pillar": "Manifesto-first truth"},
                    {"pillar": "Precision over persuasion"},
                    {"pillar": "Premium without performance"},
                ],
            },
            "audience_psychology": {
                "narrative": "Audience seeks identity confirmation, not novelty — they buy belonging to a standard.",
            },
            "campaign_direction": {
                "narrative": "Theme: The long game. Hooks: legacy, tactile proof, founder conviction.",
            },
        },
        "explainability": {
            "reasoning_path": [
                {"claim": "Luxury = restraint", "verification_status": "grounded", "risk": 0.12},
                {"claim": "Trust over hype", "verification_status": "grounded", "risk": 0.15},
            ],
            "strategic_consistency": {"consistency_score": 0.88},
        },
    },
    "d2c": {
        "id": "d2c",
        "label": "Premium D2C Brand",
        "tagline": "Direct relationship · Transparent craft",
        "brand_operating_system": {
            "brand_dna": {
                "narrative": "We sell directly so the story stays honest — no retail dilution.",
                "core_beliefs": ["Transparency", "Repeat purchase trust", "Founder voice"],
            },
            "positioning": {
                "narrative": "Accessible premium — not mass, not elitist. Win on clarity and proof.",
            },
            "messaging_pillars": {
                "pillars": [{"pillar": "Proof in every touchpoint"}, {"pillar": "Founder-led narrative"}],
            },
        },
        "explainability": {"strategic_consistency": {"consistency_score": 0.82}},
    },
    "agency_client": {
        "id": "agency_client",
        "label": "Agency Client Rebrand",
        "tagline": "Strategic reset · Evidence-led",
        "brand_operating_system": {
            "brand_dna": {"narrative": "Reposition from commodity to category authority in 18 months."},
            "campaign_direction": {"narrative": "Launch arc: reveal → proof → community of practice."},
        },
        "explainability": {},
    },
    "startup": {
        "id": "startup",
        "label": "Founder-Led Startup",
        "tagline": "Conviction-first · Category creation",
        "brand_operating_system": {
            "brand_dna": {"narrative": "We are building the standard others will benchmark — not follow trends."},
            "tone_rules": {"narrative": "Bold but grounded. No empty superlatives."},
            "audience_psychology": {"narrative": "Early adopters want signal of seriousness, not hype."},
        },
        "explainability": {},
    },
}


def list_demo_brands() -> List[Dict[str, Any]]:
    return [
        {
            "id": k,
            "label": v["label"],
            "tagline": v.get("tagline", ""),
            "workflows_included": list((v.get("brand_operating_system") or {}).keys()),
        }
        for k, v in DEMO_BRANDS.items()
    ]


def get_demo_pack(demo_id: str) -> Dict[str, Any]:
    key = (demo_id or "luxury").lower().strip()
    if key not in DEMO_BRANDS:
        return {"error": f"Unknown demo: {demo_id}", "available": list(DEMO_BRANDS.keys())}
    pack = DEMO_BRANDS[key]
    narrative = (pack.get("brand_operating_system") or {}).get("brand_dna", {}).get("narrative", "")
    return {
        "demo": True,
        "demo_id": key,
        "workflow": "pack",
        "canonical_workflow": "pack",
        "brand_operating_system": pack["brand_operating_system"],
        "narrative": narrative,
        "explainability": pack.get("explainability", {}),
        "evaluation": {"consistency_score": pack.get("explainability", {}).get("strategic_consistency", {}).get("consistency_score", 0.85)},
        "sources": [],
        "message": "Demo pack — connect a real session for evidence-grounded generation.",
    }
