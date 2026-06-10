from __future__ import annotations

from typing import Any, Dict

from brandgodfather.services.rag_retrieval import HybridRAGService


def retrieve_rag_chunks(question_id: int, pressure_level: int, query: str, brand_seed: str) -> Dict[str, Any]:
    service = HybridRAGService()
    qid = f"Q{int(question_id)}"
    phase = _phase_from_question(question_id)

    ctx = service.get_question_context(
        q_id=qid,
        phase=phase,
        user_answer=f"{query} {brand_seed}".strip(),
        pressure_level=int(pressure_level or 1),
        session={"brand_type": "general"},
    )

    return {
        "all_chunks": (ctx.question_chunks or []) + (ctx.challenge_chunks or []),
        "gold_standard_example": ctx.gold_standard or "",
        "rejection_example": ctx.rejection_example or "",
        "challenge_language": (ctx.challenge_chunks or [""])[0] if ctx.challenge_chunks else "",
        "archetype_context": "",
    }


def _phase_from_question(question_id: int) -> str:
    q = int(question_id)
    if q <= 5:
        return "I"
    if q <= 7:
        return "II"
    if q <= 11:
        return "III"
    if q <= 14:
        return "IV"
    if q <= 17:
        return "V"
    if q <= 20:
        return "VI"
    if q <= 22:
        return "VII"
    if q <= 24:
        return "VIII"
    return "IX"
