"""Phase 1 (Questions 1-8) ORB analysis frameworks.

Single source of truth for the per-question ``look_for`` / ``avoid`` criteria
used to fine-tune the Brand Godfather ORB guidance for phase-questions/1.

Consumed by:
- brandgodfather.services.prompt_assembler  -> /brandgodfather/answer/ evaluation
- user_sessions.views.answer_ai_suggestions -> /sessions/<id>/ai-answer-suggestions/

Only Phase 1 (Q1-Q8) is defined here. Other phases fall back to existing behavior.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

# Keyed by ORB question id ("Q1".."Q8"), which mirrors Question.order for stage 1.
PHASE1_FRAMEWORKS: Dict[str, Dict[str, Any]] = {
    "Q1": {
        "question": "What inspired you to start this business?",
        "orb_analysis_framework": {
            "look_for": [
                "founder stories (struggle, breakthrough, or failure)",
                "emotional resonance (frustration, conviction, pride, or protectiveness)",
                "the specific problem they were trying to solve",
                "founder wounds or victories",
            ],
            "avoid": [
                "vendor thinking (e.g., 'I saw a gap in the market' or 'I wanted to be my own boss')",
                "transactional motives (making money or price emphasis)",
                "generic statements of passion without a story as evidence",
                "feature-focused descriptions of what the product does",
            ],
        },
    },
    "Q2": {
        "question": "Beyond what you sell, what is the deeper purpose of your business?",
        "orb_analysis_framework": {
            "look_for": [
                "a core belief, philosophy, or idea they want customers to advocate",
                "focus on transformation (how the business actually improves lives)",
                "future possibility (the better future they are trying to create)",
                "genuine conviction and emotional connection rather than functional utility",
            ],
            "avoid": [
                "descriptions of products or services masquerading as a purpose",
                "polished, jargon-heavy corporate mission statements (generic thinking)",
                "vendor thinking (e.g., 'to provide high quality at a good price')",
                "forced answers lacking genuine conviction (signs of 'brain squeeze')",
            ],
        },
    },
    "Q3": {
        "question": "Do you see your business as a vendor, a specialist, or a distinct brand, and why?",
        "orb_analysis_framework": {
            "look_for": [
                "honest self-assessment (recognizing if they are currently acting like a vendor)",
                "brand thinking markers (focus on meaning, identity, emotional connection, and transformation)",
                "understanding of consistent uniqueness and genuine value",
                "aspirations to escape comparison and become meaningfully different",
            ],
            "avoid": [
                "superficial branding definitions (e.g., believing a logo, website, or marketing campaign makes them a brand)",
                "vendor thinking masquerading as a brand (e.g., 'We are a brand because we offer better prices and features')",
                "defensiveness or forced answers to sound impressive (lack of truth)",
                "defining themselves purely by being 'slightly better' than competitors",
            ],
        },
    },
    "Q4": {
        "question": "What challenges or frustrations do you face within your industry?",
        "orb_analysis_framework": {
            "look_for": [
                "frustration as an emotional signal of unrealized value, opportunity, or potential",
                "specific details about what is fundamentally broken or wrong in their industry",
                "founder frustrations that could naturally evolve into a brand manifesto, movement, or mission",
                "genuine emotional resonance (showing they care deeply about how the industry fails people)",
            ],
            "avoid": [
                "vendor-level complaints about competitors undercutting prices (price emphasis)",
                "superficial complaints about standard business mechanics (e.g., 'marketing is hard' or 'taxes are high')",
                "blaming customers for not understanding their product",
                "generic answers lacking genuine emotion or insight",
            ],
        },
    },
    "Q5": {
        "question": "In what ways do you feel your business is misunderstood?",
        "orb_analysis_framework": {
            "look_for": [
                "hidden value or unique traits the founder possesses but currently dismisses as unimportant",
                "strengths that the founder might actually be apologizing for (e.g., being 'too meticulous')",
                "qualities that feel 'ordinary' to the founder but are actually 'extraordinary' to their customers",
                "contradictions between how the founder sees the business and why customers actually love them",
            ],
            "avoid": [
                "blaming the customer for 'not getting' their complex product features (feature emphasis)",
                "vendor-level complaints about customers just looking for the cheapest price (price emphasis)",
                "dismissive language without exploration (e.g., 'It's probably nothing' or 'Everyone does that')",
                "defensiveness that blocks genuine self-awareness or curiosity",
            ],
        },
    },
    "Q6": {
        "question": "What aspects of your industry or space do you feel are broken or need change?",
        "orb_analysis_framework": {
            "look_for": [
                "identification of a meaningful human or industry problem that needs solving",
                "founder convictions, philosophies, or beliefs about how things should be done differently",
                "seeds of a brand idea (causes, movements, or possibilities)",
                "a vision for creating a better future or actively improving lives",
            ],
            "avoid": [
                "superficial complaints about competitors or pricing wars (price emphasis)",
                "complaints focused on making the business easier to run rather than improving the customer experience",
                "generic industry buzzwords lacking genuine emotional resonance",
                "transactional vendor thinking masquerading as a grand vision",
            ],
        },
    },
    "Q7": {
        "question": "What unique belief or perspective does your business hold that others may not share?",
        "orb_analysis_framework": {
            "look_for": [
                "a distinct philosophy, core belief, or unconventional idea that drives the business",
                "courage and conviction to hold a perspective that stands apart from industry norms",
                "ideas that customers would actually want to believe in, advocate for, or follow",
                "consistency in uniqueness that makes the business meaningfully different, not just comparable",
            ],
            "avoid": [
                "safe, generic statements meant to satisfy everyone or imitate competitors (similarity)",
                "vendor thinking masquerading as a belief (e.g., 'we believe in low prices')",
                "confusing standard business practices (e.g., 'good customer service') with a fundamental brand belief",
                "lack of conviction or apologizing for a perspective that feels 'too different'",
            ],
        },
    },
    "Q8": {
        "question": "What core idea or principle does your business stand for?",
        "orb_analysis_framework": {
            "look_for": [
                "a central idea, belief, or philosophy that is larger than the products or services they sell",
                "an idea that inspires possibility or creates emotional meaning for the customer",
                "evidence of a cause, aspiration, or movement that the brand champions",
                "a principle that endures even if their specific products, services, or technology change over time",
            ],
            "avoid": [
                "focusing on the 'vehicle' (the product or service) rather than the 'destination' (the idea)",
                "transactional vendor thinking masquerading as a principle (e.g., 'we stand for fast delivery')",
                "generic corporate platitudes that lack genuine emotional meaning or founder conviction",
                "ideas that are simply functional solutions to problems rather than overarching beliefs",
            ],
        },
    },
}

# ORB mission + behavioral protocols applied to Phase 1 evaluation. Kept aligned
# with the PASS/REJECT output contract the pipeline already depends on
# (complete -> PASS, incomplete -> REJECT).
ORB_PHASE1_GUIDANCE = (
    "You are ORB, the intelligence engine powering The Brand Godfather. You are not a\n"
    "chatbot or a simple questionnaire; you are a world-class strategist, coach, and\n"
    "guide sitting beside the user. Your ultimate product is the user's transformation\n"
    "from 'vendor thinking' to 'brand thinking'.\n\n"
    "MISSION:\n"
    "1. Analyze the user's latest answer against the look_for and avoid arrays below.\n"
    "2. Seek truth before agreement, and go deeper than the first answer.\n"
    "3. Decide if the user has fully satisfied the look_for criteria with genuine\n"
    "   emotion, story, or brand thinking.\n\n"
    "BEHAVIORAL PROTOCOLS (when the answer is INCOMPLETE, craft ONE counter-question):\n"
    "- THE VENDOR TRAP: If the answer triggers anything in the avoid array (price\n"
    "  emphasis, feature emphasis, generic corporate statements), gently interrupt and\n"
    "  elevate from what they DO (the vehicle) to what they BELIEVE (the destination).\n"
    "- RECOGNITION & PREDICTION: If the user shows vulnerability, frustration, or shares\n"
    "  a story, acknowledge it before the next question ('This feels important',\n"
    "  'Frustration usually means opportunity', 'I suspect this will become your\n"
    "  differentiator').\n"
    "- BRAIN SQUEEZE DETECTION: If the user gives short answers, says 'I don't know', or\n"
    "  seems frustrated, DO NOT apply pressure. Reduce tension, be conversational, and\n"
    "  ask them to explain it as if talking to a friend.\n\n"
    "DECISION MAPPING (keep the required PASS/REJECT schema):\n"
    "- If the answer FULLY satisfies look_for -> status = PASS, reply = a brief,\n"
    "  encouraging acknowledgment of their breakthrough/truth.\n"
    "- If the answer is INCOMPLETE, triggers the avoid list, or needs more digging ->\n"
    "  status = REJECT, reply = your single carefully crafted counter-question.\n"
    "Never invent facts; base the counter-question on the user's own words."
)


def get_framework(q_id: Optional[str]) -> Optional[Dict[str, Any]]:
    """Return the Phase 1 framework entry for a q_id, or None if out of scope."""
    if not q_id:
        return None
    return PHASE1_FRAMEWORKS.get(str(q_id).strip().upper())


def framework_json(q_id: Optional[str]) -> Optional[str]:
    """Return the orb_analysis_framework JSON string for a q_id, or None."""
    entry = get_framework(q_id)
    if not entry:
        return None
    return json.dumps(
        {"orb_analysis_framework": entry["orb_analysis_framework"]},
        indent=2,
        ensure_ascii=False,
    )
