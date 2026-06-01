from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from elasticsearch_dsl import connections
from pydantic import BaseModel

from synapse.documents import SYNAPSE_NODE_2_ALIAS


class SynapseSession(BaseModel):
    session_id: str
    user_id: str
    current_phase: str
    current_q_id: str
    brand_seed: str = ""
    tension: str = ""
    thread_index: Dict[str, Any] = {}
    shadow_profile: Dict[str, Any] = {}
    all_answers: List[Dict[str, Any]] = []
    context_data: Dict[str, Any] = {}
    created_at: str
    updated_at: str


class SessionManager:
    SESSION_INDEX = "synapse_sessions"
    EPISODIC_INDEX = "synapse_episodic"

    def __init__(self) -> None:
        self.es = connections.get_connection(alias=SYNAPSE_NODE_2_ALIAS)

    def create_session(self, user_id: str, context_data: Dict[str, Any]) -> SynapseSession:
        session_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        payload = {
            "session_id": session_id,
            "user_id": user_id,
            "current_phase": "I",
            "current_q_id": "Q1",
            "brand_seed": "",
            "tension": "",
            "thread_index": {},
            "shadow_profile": {
                "self_image": "unknown",
                "actual_signal": "unknown",
                "gap_score": 0.0,
                "fear_pattern": "unknown",
                "readiness_estimate": 1.0,
            },
            "all_answers": [],
            "context_data": context_data or {},
            "created_at": now,
            "updated_at": now,
        }

        self.es.index(index=self.SESSION_INDEX, id=session_id, document=payload, refresh=True)
        return SynapseSession(**payload)

    def get_session(self, session_id: str) -> Optional[SynapseSession]:
        doc_id, source = self._load_session(session_id)
        if not doc_id:
            return None
        return SynapseSession(**source)

    def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        doc_id, _ = self._load_session(session_id)
        if not doc_id:
            return False

        patch = dict(updates or {})
        patch["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.es.update(index=self.SESSION_INDEX, id=doc_id, body={"doc": patch}, refresh=True)
        return True

    def advance_question(self, session_id: str) -> Optional[str]:
        from synapse.services.question_router import QuestionRouter

        session = self.get_session(session_id)
        if not session:
            return None

        router = QuestionRouter()
        cfg = router.get_question(session.current_q_id)
        next_q_id = cfg.next if cfg else None
        if next_q_id:
            self.update_session(
                session_id,
                {
                    "current_q_id": next_q_id,
                    "current_phase": router.get_phase(next_q_id),
                },
            )
        return next_q_id

    def get_depth_history(self, session_id: str) -> List[float]:
        body = {
            "size": 200,
            "query": {"bool": {"filter": [{"term": {"session_id": session_id}}]}},
            "sort": [{"timestamp": {"order": "asc", "unmapped_type": "date"}}],
            "_source": ["emotional_weight", "prosody_flags", "brand_seed_echo"],
        }
        resp = self.es.search(index=self.EPISODIC_INDEX, body=body)

        history: List[float] = []
        for hit in resp.get("hits", {}).get("hits", []):
            src = hit.get("_source", {})
            emotional_weight = float(src.get("emotional_weight", 0.0) or 0.0)
            flags = list(src.get("prosody_flags", []) or [])
            hedge_score = 1.0 if "hedge_score_high" in flags else 0.4 if "hedge_detected" in flags else 0.0
            brand_seed_echo = 1.0 if bool(src.get("brand_seed_echo", False)) else 0.0
            depth = (emotional_weight * 0.4) + ((1.0 - hedge_score) * 0.3) + (brand_seed_echo * 0.3)
            history.append(round(max(0.0, min(1.0, depth)), 4))

        return history

    def _load_session(self, session_id: str) -> Tuple[Optional[str], Dict[str, Any]]:
        body = {
            "size": 1,
            "query": {"bool": {"filter": [{"term": {"session_id": session_id}}]}},
            "sort": [{"updated_at": {"order": "desc", "unmapped_type": "date"}}],
        }
        resp = self.es.search(index=self.SESSION_INDEX, body=body)
        hits = resp.get("hits", {}).get("hits", [])
        if not hits:
            return None, {}
        hit = hits[0]
        return hit.get("_id"), hit.get("_source", {})
