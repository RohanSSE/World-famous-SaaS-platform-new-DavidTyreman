from __future__ import annotations

from typing import Any, Dict, Tuple

from brandgodfather.services.question_router import QuestionRouter

QUESTION_PROMPTS = {
    int(k[1:]): v["prompt"] for k, v in QuestionRouter.QUESTION_SEQUENCE.items()
}
ENFORCEMENT_RULES = {
    int(k[1:]): v["enforcement_rule"] for k, v in QuestionRouter.QUESTION_SEQUENCE.items()
}
PHASE_MAP = {
    int(k[1:]): v["phase"] for k, v in QuestionRouter.QUESTION_SEQUENCE.items()
}

PRESSURE_INSTRUCTIONS = {
    1: "Reflect their words warmly and ask what they really mean by their key phrase.",
    2: "Offer a deeper interpretation and invite them beyond safe language.",
    3: "Name the avoidance directly and contrast with their stated identity.",
    4: "Explain market cost of this answer and challenge for strategic clarity.",
    5: "Connect current pattern to staying a vendor and ask for explicit commitment.",
}


def get_phase_for_question(q: int) -> str:
    return PHASE_MAP.get(int(q), "I")


def get_question_prompt(q: int) -> str:
    return QUESTION_PROMPTS.get(int(q), "")


def get_enforcement_rule(q: int) -> str:
    return ENFORCEMENT_RULES.get(int(q), "")


def assemble_prompt(
    session_state: Dict[str, Any],
    memory: Dict[str, Any],
    prosody_result: Dict[str, Any],
    chunks: Dict[str, Any],
    rejection_count: int,
) -> Tuple[str, str]:
    pressure = int(memory.get("pressure_level", 1) or 1)
    pressure = max(1, min(5, pressure))

    thread_index = memory.get("thread_index") or {}
    thread_lines = "\n".join(f"Q{k}: {v}" for k, v in thread_index.items()) or "(none yet)"

    system_prompt = f"""
You are BrandGodfather, a Benevolent Authority coach.
Reject vendor-safe language and extract emotional truth.

Current Question: Q{session_state['current_question']} | Phase: {session_state['current_phase']}
Pressure Level: {pressure}/5
Rejection Count: {rejection_count}
Brand Seed: {memory.get('brand_seed', '') or '(not set)'}

Pressure Instruction:
{PRESSURE_INSTRUCTIONS[pressure]}

Thread Index:
{thread_lines}

Output JSON ONLY:
{{
  "gate_status": "PASS|REJECT",
  "ai_reply": "string",
  "extracted_data": {{
    "brand_seed": "string or null",
    "tension": "string or null",
    "key_phrase": "string",
    "thread_addition": "string or null"
  }},
  "pressure_used": {pressure},
  "challenge_type": "string"
}}
""".strip()

    user_prompt = f"""
Question asked: {session_state['question_prompt']}

User answer: {session_state['raw_answer']}

Enforcement rule: {session_state['enforcement_rule']}

Prosody signals: {prosody_result.get('challenge_reason', 'none')}

Rejected example:
{chunks.get('rejection_example', '')}

Gold standard example:
{chunks.get('gold_standard_example', '')}

Challenge language:
{chunks.get('challenge_language', '')}
""".strip()

    return system_prompt, user_prompt
