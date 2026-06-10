from __future__ import annotations

from typing import Any, Dict

from brandgodfather.services.ragv2.classifiers import (
    ProsodyClassifierAdapter,
    VendorLanguageFilter,
    vendor_challenge_message,
)
from brandgodfather.services.ragv2.llm_client import call_llm
from brandgodfather.services.ragv2.memory import load_episodic_memory, write_memory
from brandgodfather.services.ragv2.prompts import (
    assemble_prompt,
    get_enforcement_rule,
    get_phase_for_question,
    get_question_prompt,
)
from brandgodfather.services.ragv2.retriever import retrieve_rag_chunks
from brandgodfather.services.ragv2.shadow import check_contradictions, update_shadow_profile


_vendor_filter = VendorLanguageFilter()
_prosody = ProsodyClassifierAdapter()


def run_coaching_pipeline(session_state: Dict[str, Any]) -> Dict[str, Any]:
    raw_answer = str(session_state.get("raw_answer") or "").strip()

    vendor_result = _vendor_filter.check(raw_answer)
    if vendor_result["fail"]:
        return {
            "gate_status": "REJECT",
            "ai_reply": vendor_challenge_message(vendor_result.get("matched_patterns") or []),
            "extracted_data": {
                "brand_seed": None,
                "tension": None,
                "key_phrase": "",
                "thread_addition": None,
            },
            "pressure_used": 1,
            "challenge_type": "vendor_language_hard_block",
            "advance_question": False,
        }

    current_q = int(session_state.get("current_question") or 1)
    question_prompt = get_question_prompt(current_q)
    phase = get_phase_for_question(current_q)

    prosody_result = _prosody.analyze(raw_answer, question_prompt, phase)

    memory = load_episodic_memory(str(session_state["session_id"]))
    memory["shadow_profile"] = update_shadow_profile(
        memory.get("shadow_profile") or {},
        prosody_result,
        raw_answer,
        current_q,
    )

    contradiction = check_contradictions(str(session_state["session_id"]), raw_answer, current_q)
    if contradiction.get("found"):
        prosody_result["should_challenge"] = True
        prosody_result["challenge_reason"] = (
            f"{prosody_result.get('challenge_reason', '')} | {contradiction.get('challenge_addition', '')}"
        ).strip(" |")
        memory["shadow_profile"].setdefault("contradictions", []).extend(contradiction.get("contradictions", []))

    chunks = retrieve_rag_chunks(
        question_id=current_q,
        pressure_level=int(memory.get("pressure_level", 1) or 1),
        query=raw_answer,
        brand_seed=str(memory.get("brand_seed") or ""),
    )

    max_rejections = 5
    rejection_count = 0
    gate_status = "REJECT"
    llm_result: Dict[str, Any] = {}

    while gate_status == "REJECT" and rejection_count < max_rejections:
        assembled_state = {
            **session_state,
            "current_phase": phase,
            "question_prompt": question_prompt,
            "enforcement_rule": get_enforcement_rule(current_q),
        }
        system_prompt, user_prompt = assemble_prompt(
            session_state=assembled_state,
            memory=memory,
            prosody_result=prosody_result,
            chunks=chunks,
            rejection_count=rejection_count,
        )
        llm_result = call_llm(system_prompt, user_prompt)
        gate_status = str(llm_result.get("gate_status") or "REJECT").upper()

        if gate_status == "REJECT":
            rejection_count += 1
            memory["pressure_level"] = min(int(memory.get("pressure_level", 1) or 1) + 1, 5)
            q_key = str(current_q)
            memory.setdefault("resistance_count", {})
            memory["resistance_count"][q_key] = int(memory["resistance_count"].get(q_key, 0) or 0) + 1

    if gate_status == "REJECT" and rejection_count >= max_rejections:
        gate_status = "PASS"
        llm_result["gate_status"] = "PASS"
        llm_result["challenge_type"] = "forced_pass_cap_reached"

    if gate_status == "PASS":
        extracted = llm_result.get("extracted_data") or {}
        if extracted.get("brand_seed"):
            memory["brand_seed"] = str(extracted.get("brand_seed"))
        if extracted.get("thread_addition"):
            memory.setdefault("thread_index", {})
            memory["thread_index"][str(current_q)] = str(extracted.get("thread_addition"))

    session_state = {
        **session_state,
        "current_phase": phase,
    }

    write_memory(session_state, memory, llm_result, prosody_result, answer_embedding=[])

    return {
        "gate_status": gate_status,
        "ai_reply": llm_result.get("ai_reply", "Let's go deeper."),
        "extracted_data": llm_result.get("extracted_data", {}),
        "pressure_used": int(llm_result.get("pressure_used", memory.get("pressure_level", 1)) or 1),
        "challenge_type": llm_result.get("challenge_type", ""),
        "rejection_count": rejection_count,
        "advance_question": gate_status == "PASS",
        "brand_seed": memory.get("brand_seed", ""),
    }
