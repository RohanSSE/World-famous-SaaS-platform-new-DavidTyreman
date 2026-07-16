"""Phase 2 (Questions 1-12) ORB analysis frameworks.

Single source of truth for the per-question discovery IDs, confidence
thresholds, and ``look_for`` / ``avoid`` criteria used by phase-questions/2.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, Optional


PHASE2_FRAMEWORKS: Dict[str, Dict[str, Any]] = {
    "Q1": {
        "question": "What belief drives this idea?",
        "associated_discovery_id": "D_2.1_BRAND_BELIEF",
        "target_confidence_threshold": 85,
        "orb_analysis_framework": {
            "look_for": [
                "a distinct philosophy, conviction, or overarching idea that transcends the product itself",
                "alignment between the founder's worldview and the business's existence",
                "an idea that inspires possibility or creates emotional meaning for the customer",
                "courage to hold a perspective that stands apart from standard industry norms",
            ],
            "avoid": [
                "transactional vendor thinking (e.g., 'we believe in fast delivery')",
                "generic corporate platitudes or mission statements lacking genuine conviction",
                "focusing on the functional 'vehicle' (the product) rather than the 'destination' (the idea)",
                "safe statements meant to satisfy everyone",
            ],
        },
    },
    "Q2": {
        "question": "What changes for your customer?",
        "associated_discovery_id": "D_4.1_CUSTOMER_TRANSFORMATION",
        "target_confidence_threshold": 85,
        "orb_analysis_framework": {
            "look_for": [
                "focus on true transformation (how the brand improves the customer's life or identity)",
                "a clear 'before and after' emotional or psychological state",
                "evidence that the customer is buying meaning, certainty, or aspiration",
                "an understanding of the human being rather than a demographic profile",
            ],
            "avoid": [
                "functional product benefits or feature lists",
                "superficial transactional outcomes (e.g., 'they save 10% on their bill')",
                "vendor logic masquerading as transformation",
                "descriptions of the service delivery process",
            ],
        },
    },
    "Q3": {
        "question": "What do you stand against?",
        "associated_discovery_id": "D_5.1_BRAND_ENEMY",
        "target_confidence_threshold": 80,
        "orb_analysis_framework": {
            "look_for": [
                "a clear 'enemy' (e.g., the status quo, an outdated industry standard, a limiting mindset)",
                "passionate, authentic disagreement with a prevailing norm",
                "beliefs that inherently draw a line in the sand and polarize the market",
                "a cause or movement that customers would eagerly advocate for",
            ],
            "avoid": [
                "petty grievances or bashing specific competitor companies",
                "vendor-level complaints about pricing wars",
                "complaints focused on making the business easier to run rather than improving the customer experience",
                "bland, universally agreed-upon evils (e.g., 'we stand against bad quality')",
            ],
        },
    },
    "Q4": {
        "question": "What are your non-negotiables?",
        "associated_discovery_id": "D_2.3_CORE_VALUES",
        "target_confidence_threshold": 85,
        "orb_analysis_framework": {
            "look_for": [
                "hard lines drawn in the sand regarding how the business operates",
                "principles the founder would willingly lose money over to uphold",
                "behavioral proof of values demonstrated through past actions",
                "boundaries that protect the brand's integrity and strategic identity",
            ],
            "avoid": [
                "cliche corporate values ('honesty', 'integrity', 'excellence') lacking specific behavioral evidence",
                "flexible standards that shift depending on the client or payout",
                "generic business practices masquerading as deep moral stances",
                "answers that lack emotional conviction or founder stories",
            ],
        },
    },
    "Q5": {
        "question": "What energy do you bring?",
        "associated_discovery_id": "D_2.4_BRAND_ENERGY_ARCHETYPE",
        "target_confidence_threshold": 80,
        "orb_analysis_framework": {
            "look_for": [
                "authentic emotional resonance rooted in the founder's natural disposition",
                "a distinct 'vibe' or personality that customers immediately feel",
                "consistency in tone that separates them from the sterile corporate standard",
                "emotional states they actively project (e.g., rebellious, nurturing, intense, calming)",
            ],
            "avoid": [
                "mimicking successful competitors' personalities",
                "trying to be 'everything to everyone' (resulting in a diluted presence)",
                "safe, bland, or overly polished corporate tones",
                "inconsistency between what they say their energy is and how they actually communicate",
            ],
        },
    },
    "Q6": {
        "question": "How would you describe your brand?",
        "associated_discovery_id": "D_6.1_BRAND_IDENTITY_FOUNDATION",
        "target_confidence_threshold": 80,
        "orb_analysis_framework": {
            "look_for": [
                "strategic positioning that relies on meaning, emotion, and identity",
                "descriptors that highlight transformation, philosophy, or specific differentiation",
                "a coherent narrative that unites the founder, the business, and the customer",
                "confidence in their strategic identity beyond visual assets",
            ],
            "avoid": [
                "describing the logo, colors, or visual marketing materials",
                "listing the literal products or services sold",
                "vendor thinking (e.g., 'we are an affordable option for X')",
                "industry jargon that lacks unique meaning",
            ],
        },
    },
    "Q7": {
        "question": "Who do you serve best?",
        "associated_discovery_id": "D_3.1_CUSTOMER_EMPATHY",
        "target_confidence_threshold": 85,
        "orb_analysis_framework": {
            "look_for": [
                "deep psychographic understanding (mindsets, worldviews, values)",
                "a specific niche of people whose internal problems align perfectly with the brand's belief",
                "genuine empathy for the customer as a human being",
                "recognition of the specific emotional state the customer is currently trapped in",
            ],
            "avoid": [
                "broad, generic demographic profiles (e.g., 'women 18-35 in urban areas')",
                "the fear-driven 'everyone' or 'anyone with a budget' answer",
                "viewing customers purely as transactional buyers",
                "descriptions based solely on the customer's need for the physical product",
            ],
        },
    },
    "Q8": {
        "question": "Your Customers What are they worried about?",
        "associated_discovery_id": "D_3.2_CUSTOMER_FEARS",
        "target_confidence_threshold": 85,
        "orb_analysis_framework": {
            "look_for": [
                "deep-seated anxieties, internal fears, and emotional pain points",
                "the underlying psychological 'why' behind their frustration",
                "what keeps the customer up at night regarding their identity, status, or security",
                "founder stories or examples proving they truly listen to their audience",
            ],
            "avoid": [
                "superficial functional complaints (e.g., 'shipping takes too long')",
                "assumptions lacking true empathy or evidence",
                "blaming the customer for not understanding the industry",
                "surface-level price objections",
            ],
        },
    },
    "Q9": {
        "question": "How should they feel?",
        "associated_discovery_id": "D_3.3_CUSTOMER_ASPIRATIONS",
        "target_confidence_threshold": 85,
        "orb_analysis_framework": {
            "look_for": [
                "the target emotional end-state (e.g., empowered, relieved, validated, safe)",
                "identity elevation or a sense of belonging to a specific community",
                "how the brand experience changes the customer's internal narrative",
                "emotional coherence with the brand's overarching purpose",
            ],
            "avoid": [
                "rational satisfaction metrics (e.g., 'they feel like they got a good deal')",
                "transactional vendor goals ('they feel satisfied with the product')",
                "generic positive emotions that lack specific connection to the brand's unique value",
                "focusing on the business's success rather than the customer's emotional outcome",
            ],
        },
    },
    "Q10": {
        "question": "Why are you different?",
        "associated_discovery_id": "D_5.2_STRATEGIC_UNIQUENESS",
        "target_confidence_threshold": 85,
        "orb_analysis_framework": {
            "look_for": [
                "characteristics, perspectives, or methodologies that competitors cannot easily replicate",
                "uncopyable founder traits or unique combinations of skills",
                "creating a new category or entirely new set of rules for the industry",
                "distinction built on philosophy, vision, or extreme specialization",
            ],
            "avoid": [
                "comparison metrics ('we are faster, cheaper, or have better quality')",
                "standard expectations masquerading as differentiation ('we have great customer service')",
                "vendor logic that can be easily undercut by a competitor with a bigger budget",
                "listing product features",
            ],
        },
    },
    "Q11": {
        "question": "What won't you compete on?",
        "associated_discovery_id": "D_5.3_COMPETITIVE_BOUNDARIES",
        "target_confidence_threshold": 80,
        "orb_analysis_framework": {
            "look_for": [
                "intentional strategic sacrifices to protect brand integrity",
                "refusing to enter the 'race to the bottom' (explicitly refusing to compete on price)",
                "opting out of standard industry games or metric battles",
                "courage to let competitors win lower-tier or misaligned business",
            ],
            "avoid": [
                "unwillingness to sacrifice anything (trying to win every metric)",
                "fear of missing out on market share",
                "vendor thinking (e.g., 'we won't compete on quality because ours is the best')",
                "answers indicating they let competitors dictate their strategy",
            ],
        },
    },
    "Q12": {
        "question": "Who is not for you?",
        "associated_discovery_id": "D_3.4_ANTI_AVATAR",
        "target_confidence_threshold": 80,
        "orb_analysis_framework": {
            "look_for": [
                "the courage to actively alienate the wrong fit",
                "crystal clarity on mindsets, values, or behaviors that clash with the brand",
                "recognizing that a strong brand must repel as much as it attracts",
                "protecting the brand's energy, culture, and preferred customer base",
            ],
            "avoid": [
                "fear of losing sales leading to 'we can help anyone' statements",
                "generic disqualifiers (e.g., 'people who can't afford us')",
                "lack of conviction in defining boundaries",
                "viewing disqualification as a failure rather than a strategic necessity",
            ],
        },
    },
}


ORB_PHASE2_FRAMEWORK: Dict[str, Dict[str, Any]] = {
    entry["question"]: {
        "associated_discovery_id": entry["associated_discovery_id"],
        "target_confidence_threshold": entry["target_confidence_threshold"],
        "look_for": entry["orb_analysis_framework"]["look_for"],
        "avoid": entry["orb_analysis_framework"]["avoid"],
    }
    for entry in PHASE2_FRAMEWORKS.values()
}


def _normalize_phase2_question_text(question_text: str) -> str:
    text = str(question_text or "").strip().lower()
    text = text.replace("won't", "wont")
    text = re.sub(r"^\s*(?:q(?:uestion)?\.?\s*)?\d+\s*[\).:-]?\s*", "", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def match_phase2_orb_framework(question_text: Optional[str]) -> Optional[Dict[str, Any]]:
    """Return the Phase 2 ORB framework matching a DB or frontend question."""
    normalized_question = _normalize_phase2_question_text(question_text or "")
    if not normalized_question:
        return None

    for q_id, entry in PHASE2_FRAMEWORKS.items():
        canonical_question = entry["question"]
        normalized_canonical = _normalize_phase2_question_text(canonical_question)
        if normalized_canonical in normalized_question or normalized_question in normalized_canonical:
            framework = entry["orb_analysis_framework"]
            return {
                "phase": 2,
                "q_id": q_id,
                "question": canonical_question,
                "associated_discovery_id": entry["associated_discovery_id"],
                "target_confidence_threshold": entry["target_confidence_threshold"],
                "look_for": framework["look_for"],
                "avoid": framework["avoid"],
            }
    return None


def get_phase2_framework(q_id: Optional[str]) -> Optional[Dict[str, Any]]:
    """Return the Phase 2 framework entry for a q_id, or None if out of scope."""
    if not q_id:
        return None
    return PHASE2_FRAMEWORKS.get(str(q_id).strip().upper())


def phase2_framework_json(q_id: Optional[str]) -> Optional[str]:
    """Return the Phase 2 orb_analysis_framework JSON string for a q_id."""
    entry = get_phase2_framework(q_id)
    if not entry:
        return None
    return json.dumps(
        {"orb_analysis_framework": entry["orb_analysis_framework"]},
        indent=2,
        ensure_ascii=False,
    )