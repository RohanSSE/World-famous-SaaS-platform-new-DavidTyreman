from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from elasticsearch_dsl import connections

from brandgodfather.documents import BRANDGODFATHER_NODE_2_ALIAS

SESSION_INDEX = "brandgodfather_sessions"
EPISODIC_INDEX = "brandgodfather_episodic"


def _es():
    return connections.get_connection(alias=BRANDGODFATHER_NODE_2_ALIAS)


def load_episodic_memory(session_id: str) -> Dict[str, Any]:
    es = _es()
    body = {
        "size": 1,
        "query": {"bool": {"filter": [{"term": {"session_id": session_id}}]}},
        "sort": [{"timestamp": {"order": "desc", "unmapped_type": "date"}}],
    }
    resp = es.search(index=EPISODIC_INDEX, body=body)
    hits = resp.get("hits", {}).get("hits", [])
    if hits:
        src = hits[0].get("_source", {}) or {}
        return {
            "brand_seed": src.get("brand_seed", ""),
            "thread_index": src.get("thread_index", {}) or {},
            "shadow_profile": src.get("shadow_profile", {}) or {},
            "pressure_level": int((src.get("pressure_state") or {}).get("current", 1) or 1),
            "resistance_count": src.get("resistance_count", {}) or {},
            "three_word_foundation": src.get("three_word_foundation", {}) or {},
        }

    return {
        "brand_seed": "",
        "thread_index": {},
        "shadow_profile": {
            "self_image": "",
            "actual_signal": "",
            "gap_score": 0.0,
            "fear_pattern": "",
            "avoidance_topic": "",
            "readiness_estimate": 5.0,
            "contradictions": [],
        },
        "pressure_level": 1,
        "resistance_count": {},
        "three_word_foundation": {},
    }


def write_memory(
    session_state: Dict[str, Any],
    memory: Dict[str, Any],
    llm_result: Dict[str, Any],
    prosody_result: Dict[str, Any],
    answer_embedding: Optional[list[float]] = None,
) -> str:
    es = _es()
    now = datetime.now(timezone.utc).isoformat()

    session_doc = {
        "session_id": session_state["session_id"],
        "user_id": session_state["user_id"],
        "question_id": int(session_state["current_question"]),
        "raw_answer": session_state["raw_answer"],
        "prosody_flags": prosody_result.get("flags", {}),
        "emotional_weight": float((prosody_result.get("flags") or {}).get("emotional_weight", {}).get("emotional_weight", 0.5)),
        "resistance_level": prosody_result.get("resistance_level", "medium"),
        "brand_seed": memory.get("brand_seed", ""),
        "phase": session_state.get("current_phase", "I"),
        "gate_status": llm_result.get("gate_status", "REJECT"),
        "document_type": "answer",
        "timestamp": now,
    }
    if answer_embedding:
        session_doc["answer_embedding"] = answer_embedding
    result = es.index(index=SESSION_INDEX, document=session_doc, refresh=True)
    es_doc_id = result.get("_id", "")

    episodic_doc = {
        "session_id": session_state["session_id"],
        "memory_type": "session_state",
        "brand_seed": memory.get("brand_seed", ""),
        "thread_index": memory.get("thread_index", {}),
        "shadow_profile": memory.get("shadow_profile", {}),
        "pressure_state": {
            "current": int(memory.get("pressure_level", 1) or 1),
            "by_question": memory.get("resistance_count", {}),
        },
        "resistance_count": memory.get("resistance_count", {}),
        "three_word_foundation": memory.get("three_word_foundation", {}),
        "question_reference": int(session_state["current_question"]),
        "timestamp": now,
    }
    es.index(index=EPISODIC_INDEX, document=episodic_doc, refresh=True)

    return es_doc_id
