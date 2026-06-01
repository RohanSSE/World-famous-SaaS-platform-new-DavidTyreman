from __future__ import annotations

import logging
from datetime import datetime, timezone
from statistics import mean
from typing import Any, Dict, List, Optional, Tuple

from elasticsearch_dsl import connections

from document.utils.embedding_service import EmbeddingService
from brandgodfather.documents import BRANDGODFATHER_NODE_2_ALIAS
from utils.retry_azure import with_azure_retry

logger = logging.getLogger(__name__)


class ShadowProfileService:
    SESSIONS_INDEX = "brandgodfather_sessions"
    EPISODIC_INDEX = "brandgodfather_episodic"

    BRAND_TERMS = {
        "brand",
        "belief",
        "purpose",
        "positioning",
        "identity",
        "manifesto",
        "promise",
        "values",
    }
    VENDOR_TERMS = {
        "service",
        "feature",
        "pricing",
        "deliverable",
        "client satisfaction",
        "offer",
        "package",
        "solution",
    }
    FEAR_PATTERNS = {
        "rejection": ["reject", "rejection", "not chosen", "turned down"],
        "commoditization": ["commodity", "same as others", "generic", "price war"],
        "being misunderstood": ["misunderstood", "not get it", "confused", "misread"],
        "visibility": ["seen", "visible", "judged", "public", "exposure"],
        "commitment": ["commit", "locked in", "stuck", "all in", "long term"],
    }

    def __init__(self) -> None:
        self.es = connections.get_connection(alias=BRANDGODFATHER_NODE_2_ALIAS)
        self.embedding_service = EmbeddingService()

    def update_profile(
        self,
        session_id: str,
        q_id: str,
        prosody_result: Any,
        answer_embedding: Optional[List[float]],
    ) -> Dict[str, Any]:
        session_doc_id, session_source = self._get_session(session_id)
        if not session_doc_id:
            raise ValueError(f"Session not found for session_id={session_id}")

        payload = self._as_dict(prosody_result)
        answer_text = str(payload.get("raw_answer") or payload.get("answer") or "").strip()
        if not answer_text:
            answer_text = self._answer_from_session(session_source=session_source, q_id=q_id)

        if not answer_embedding and answer_text:
            answer_embedding = self._embed_answer(answer_text)

        self._upsert_episodic(
            session_id=session_id,
            q_id=q_id,
            payload=payload,
            answer_text=answer_text,
            answer_embedding=answer_embedding,
        )

        episodic = self._list_episodic(session_id)
        profile = self._build_shadow_profile(session_source=session_source, episodic=episodic)

        now_iso = datetime.now(timezone.utc).isoformat()
        self.es.update(
            index=self.SESSIONS_INDEX,
            id=session_doc_id,
            body={"doc": {"shadow_profile": profile, "updated_at": now_iso}},
            refresh=True,
        )
        return profile

    def _build_shadow_profile(
        self,
        session_source: Dict[str, Any],
        episodic: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        self_image = self._infer_self_image(session_source=session_source, episodic=episodic)

        resistance_vals = [self._resistance_num(e.get("resistance_level")) for e in episodic]
        resistance_vals = [v for v in resistance_vals if v is not None]
        avg_resistance = mean(resistance_vals) if resistance_vals else 2.0

        emotional_vals = [float(e.get("emotional_weight", 0.0) or 0.0) for e in episodic]
        avg_emotional = mean(emotional_vals) if emotional_vals else 0.0

        if avg_resistance > 2.0:
            actual_signal = "vendor-level responses"
        elif avg_emotional > 0.6:
            actual_signal = "authentic brand thinking"
        else:
            actual_signal = "vendor-level responses"

        vendor_like_count = 0
        for e in episodic:
            resistance = self._resistance_num(e.get("resistance_level")) or 2.0
            emotional = float(e.get("emotional_weight", 0.0) or 0.0)
            if resistance >= 2.0 or emotional < 0.6:
                vendor_like_count += 1
        vendor_answer_ratio = vendor_like_count / max(len(episodic), 1)

        claimed_brand_level = 1.0 if self_image == "brand" else 0.0
        gap_score = vendor_answer_ratio - claimed_brand_level
        gap_score = max(0.0, min(1.0, gap_score))

        fear_pattern = self._infer_fear_pattern(episodic)

        low_resistance_ratio = (
            sum(1 for e in episodic if str(e.get("resistance_level", "")).lower() == "low")
            / max(len(episodic), 1)
        )
        brand_seed_echo_ratio = (
            sum(1 for e in episodic if bool(e.get("brand_seed_echo"))) / max(len(episodic), 1)
        )

        readiness_01 = (avg_emotional * 0.4) + (low_resistance_ratio * 0.4) + (brand_seed_echo_ratio * 0.2)
        readiness_estimate = max(1.0, min(10.0, readiness_01 * 10.0))

        return {
            "self_image": self_image,
            "actual_signal": actual_signal,
            "gap_score": round(gap_score, 4),
            "fear_pattern": fear_pattern,
            "avoidance_topic": fear_pattern,
            "readiness_estimate": round(readiness_estimate, 2),
        }

    def _infer_self_image(self, session_source: Dict[str, Any], episodic: List[Dict[str, Any]]) -> str:
        target_q_ids = {"Q2", "Q3", "Q8", "2", "3", "8"}
        texts: List[str] = []

        for ans in session_source.get("all_answers", []) or []:
            q = str(ans.get("q_id", "")).upper().replace(" ", "")
            if q in target_q_ids:
                texts.append(str(ans.get("raw_answer", "")))

        for ep in episodic:
            q = str(ep.get("q_id", "")).upper().replace(" ", "")
            if q in target_q_ids:
                texts.append(str(ep.get("raw_answer", "")))

        joined = " ".join(texts).lower()
        brand_hits = sum(1 for term in self.BRAND_TERMS if term in joined)
        vendor_hits = sum(1 for term in self.VENDOR_TERMS if term in joined)

        if brand_hits >= vendor_hits and brand_hits > 0:
            return "brand"
        if vendor_hits > 0:
            return "vendor"
        return "vendor"

    def _infer_fear_pattern(self, episodic: List[Dict[str, Any]]) -> str:
        scores = {k: 0 for k in self.FEAR_PATTERNS}

        for ep in episodic:
            explicit = str(ep.get("avoidance_topic", "") or "").strip().lower()
            if explicit in scores:
                scores[explicit] += 2

            text = str(ep.get("raw_answer", "") or "").lower()
            for category, keys in self.FEAR_PATTERNS.items():
                if any(k in text for k in keys):
                    scores[category] += 1

        winner = max(scores.items(), key=lambda kv: kv[1])[0]
        return winner

    def _upsert_episodic(
        self,
        session_id: str,
        q_id: str,
        payload: Dict[str, Any],
        answer_text: str,
        answer_embedding: Optional[List[float]],
    ) -> None:
        doc = {
            "session_id": session_id,
            "q_id": q_id,
            "raw_answer": answer_text,
            "emotional_weight": float(payload.get("emotional_weight", 0.0) or 0.0),
            "resistance_level": str(payload.get("resistance_level", "medium") or "medium"),
            "resistance_count": int(payload.get("resistance_count", 0) or 0),
            "prosody_flags": list(payload.get("prosody_flags", []) or []),
            "key_phrase": str(payload.get("key_phrase", "") or ""),
            "contradiction_flags": list(payload.get("contradiction_flags", []) or []),
            "pressure_level_used": int(payload.get("pressure_recommendation", 3) or 3),
            "brand_seed_echo": bool(payload.get("brand_seed_echo", False)),
            "avoidance_topic": str(payload.get("avoidance_topic", "") or ""),
            "answer_embedding": answer_embedding,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        existing_id = self._get_latest_episodic_doc_id(session_id=session_id, q_id=q_id)
        if existing_id:
            self.es.update(
                index=self.EPISODIC_INDEX,
                id=existing_id,
                body={"doc": doc},
                refresh=True,
            )
            return

        self.es.index(index=self.EPISODIC_INDEX, document=doc, refresh=True)

    def _embed_answer(self, text: str) -> List[float]:
        return with_azure_retry(
            lambda: self.embedding_service.generate_embedding(text),
            operation_name="shadow_profile_answer_embedding",
        )

    @staticmethod
    def _answer_from_session(session_source: Dict[str, Any], q_id: str) -> str:
        for item in session_source.get("all_answers", []) or []:
            if str(item.get("q_id", "")) == str(q_id):
                return str(item.get("raw_answer", "") or "").strip()
        return ""

    def _get_session(self, session_id: str) -> Tuple[Optional[str], Dict[str, Any]]:
        body = {
            "size": 1,
            "query": {"bool": {"filter": [{"term": {"session_id": session_id}}]}},
            "sort": [{"updated_at": {"order": "desc", "unmapped_type": "date"}}],
        }
        resp = self.es.search(index=self.SESSIONS_INDEX, body=body)
        hits = resp.get("hits", {}).get("hits", [])
        if not hits:
            return None, {}
        hit = hits[0]
        return hit.get("_id"), hit.get("_source", {})

    def _list_episodic(self, session_id: str) -> List[Dict[str, Any]]:
        body = {
            "size": 500,
            "query": {"bool": {"filter": [{"term": {"session_id": session_id}}]}},
            "sort": [{"timestamp": {"order": "asc", "unmapped_type": "date"}}],
        }
        resp = self.es.search(index=self.EPISODIC_INDEX, body=body)
        return [h.get("_source", {}) for h in resp.get("hits", {}).get("hits", [])]

    def _get_latest_episodic_doc_id(self, session_id: str, q_id: str) -> Optional[str]:
        body = {
            "size": 1,
            "query": {
                "bool": {
                    "filter": [
                        {"term": {"session_id": session_id}},
                        {"term": {"q_id": q_id}},
                    ]
                }
            },
            "sort": [{"timestamp": {"order": "desc", "unmapped_type": "date"}}],
        }
        resp = self.es.search(index=self.EPISODIC_INDEX, body=body)
        hits = resp.get("hits", {}).get("hits", [])
        if not hits:
            return None
        return hits[0].get("_id")

    @staticmethod
    def _as_dict(value: Any) -> Dict[str, Any]:
        if value is None:
            return {}
        if isinstance(value, dict):
            return value
        if hasattr(value, "model_dump"):
            return value.model_dump()
        if hasattr(value, "dict"):
            return value.dict()
        return {}

    @staticmethod
    def _resistance_num(level: Any) -> Optional[float]:
        raw = str(level or "").lower()
        if raw == "low":
            return 1.0
        if raw == "medium":
            return 2.0
        if raw == "high":
            return 3.0
        return None
