from __future__ import annotations

import logging
import math
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple

from elasticsearch_dsl import connections
from pydantic import BaseModel

from document.utils.embedding_service import EmbeddingService
from brandgodfather.documents import BRANDGODFATHER_NODE_2_ALIAS
from utils.retry_azure import with_azure_retry

logger = logging.getLogger(__name__)

TOPICS: Dict[str, Sequence[str]] = {
    "motivation": ("why", "motivation", "drive", "reason", "purpose"),
    "identity": ("identity", "who i am", "who we are", "self", "brand self"),
    "market_position": ("market", "position", "category", "space", "niche"),
    "client_definition": ("client", "audience", "customer", "buyer", "who for"),
    "differentiation": ("different", "unique", "edge", "advantage", "distinct"),
    "values": ("value", "belief", "principle", "stand for", "non-negotiable"),
    "transformation": ("transform", "change", "outcome", "result", "before after"),
    "vision": ("vision", "future", "legacy", "long term", "destination"),
}

NEGATION_WORDS = {"not", "never", "no", "none", "cannot", "can't", "won't", "don't", "doesn't"}
AFFIRM_WORDS = {"is", "are", "do", "does", "will", "can", "yes", "always"}


class ContradictionResult(BaseModel):
    has_contradiction: bool
    conflicting_q_id: Optional[str]
    contradiction_summary: Optional[str]
    topic: str


class ContradictionEngine:
    SESSION_INDEX = "brandgodfather_sessions"
    EPISODIC_INDEX = "brandgodfather_episodic"

    def __init__(self) -> None:
        self.es = connections.get_connection(alias=BRANDGODFATHER_NODE_2_ALIAS)
        self.embedding_service = EmbeddingService()

    def check_contradiction(
        self,
        session_id: str,
        q_id: str,
        current_answer: str,
        current_embedding: Optional[List[float]],
    ) -> ContradictionResult:
        topic = self._detect_topic(current_answer)
        if current_embedding is None:
            current_embedding = self._embed_answer(current_answer)

        previous = self._fetch_previous_answers(session_id=session_id, exclude_q_id=q_id)
        same_topic = [row for row in previous if self._row_topic(row) == topic]

        best_conflict_q: Optional[str] = None
        best_conflict_text: Optional[str] = None
        best_similarity: float = 1.0
        direct_conflict = False

        for row in same_topic:
            prev_text = str(row.get("raw_answer", "") or "")
            prev_emb = row.get("answer_embedding")
            if not prev_emb:
                prev_emb = self._embed_answer(prev_text)
                self._update_episodic_fields(
                    doc_id=row.get("_id", ""),
                    fields={"answer_embedding": prev_emb},
                )

            similarity = self._cosine_similarity(current_embedding, prev_emb)
            logical_conflict = self._direct_logical_conflict(current_answer, prev_text)

            if logical_conflict:
                direct_conflict = True

            if logical_conflict or similarity < 0.25:
                if similarity < best_similarity:
                    best_similarity = similarity
                    best_conflict_q = str(row.get("q_id", ""))
                    best_conflict_text = prev_text

        has_contradiction = best_conflict_q is not None
        normalized_conflict_q = self._normalize_q_label(best_conflict_q) if has_contradiction else None
        summary = None

        if has_contradiction:
            summary = (
                f"User said '{best_conflict_text}' in {normalized_conflict_q} but now says "
                f"'{current_answer}'. Use this specific contradiction to deepen the challenge."
            )

        # Persist current answer embedding/topic + contradiction flags in episodic memory.
        flags = [normalized_conflict_q] if has_contradiction and normalized_conflict_q else []
        self._upsert_current_episodic(
            session_id=session_id,
            q_id=q_id,
            answer=current_answer,
            embedding=current_embedding,
            topic=topic,
            contradiction_flags=flags,
        )

        return ContradictionResult(
            has_contradiction=has_contradiction,
            conflicting_q_id=normalized_conflict_q,
            contradiction_summary=summary,
            topic=topic,
        )

    def _fetch_previous_answers(self, session_id: str, exclude_q_id: str) -> List[Dict[str, Any]]:
        body = {
            "size": 500,
            "query": {
                "bool": {
                    "must": [{"term": {"session_id": session_id}}],
                    "must_not": [{"term": {"q_id": exclude_q_id}}],
                }
            },
            "sort": [{"timestamp": {"order": "asc"}}],
        }
        resp = self.es.search(index=self.EPISODIC_INDEX, body=body)

        rows: List[Dict[str, Any]] = []
        for h in resp.get("hits", {}).get("hits", []):
            src = h.get("_source", {})
            src["_id"] = h.get("_id")
            rows.append(src)
        return rows

    def _upsert_current_episodic(
        self,
        session_id: str,
        q_id: str,
        answer: str,
        embedding: List[float],
        topic: str,
        contradiction_flags: List[str],
    ) -> None:
        doc_id = f"{session_id}:{q_id}"
        doc = {
            "session_id": session_id,
            "q_id": q_id,
            "raw_answer": answer,
            "answer_embedding": embedding,
            "topic": topic,
            "contradiction_flags": contradiction_flags,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        self.es.update(
            index=self.EPISODIC_INDEX,
            id=doc_id,
            body={"doc": doc, "doc_as_upsert": True},
            refresh="wait_for",
        )

    def _update_episodic_fields(self, doc_id: str, fields: Dict[str, Any]) -> None:
        if not doc_id:
            return
        self.es.update(
            index=self.EPISODIC_INDEX,
            id=doc_id,
            body={"doc": fields},
            refresh=False,
        )

    @staticmethod
    def _detect_topic(text: str) -> str:
        lower = text.lower()
        best_topic = "identity"
        best_hits = -1
        for topic, keywords in TOPICS.items():
            hits = sum(1 for kw in keywords if kw in lower)
            if hits > best_hits:
                best_hits = hits
                best_topic = topic
        return best_topic

    def _row_topic(self, row: Dict[str, Any]) -> str:
        topic = str(row.get("topic", "") or "").strip().lower()
        if topic in TOPICS:
            return topic
        return self._detect_topic(str(row.get("raw_answer", "") or ""))

    def _embed_answer(self, text: str) -> List[float]:
        if not text:
            return []
        return with_azure_retry(
            lambda: self.embedding_service.generate_embedding(text),
            operation_name="contradiction_answer_embedding",
        )

    @staticmethod
    def _cosine_similarity(v1: Sequence[float], v2: Sequence[float]) -> float:
        if not v1 or not v2:
            return 0.0
        if len(v1) != len(v2):
            return 0.0

        dot = 0.0
        n1 = 0.0
        n2 = 0.0
        for a, b in zip(v1, v2):
            dot += float(a) * float(b)
            n1 += float(a) * float(a)
            n2 += float(b) * float(b)

        if n1 == 0.0 or n2 == 0.0:
            return 0.0
        return dot / (math.sqrt(n1) * math.sqrt(n2))

    def _direct_logical_conflict(self, current: str, previous: str) -> bool:
        cur = self._normalize_tokens(current)
        prev = self._normalize_tokens(previous)

        shared = set(cur["content_tokens"]).intersection(prev["content_tokens"])
        if len(shared) < 2:
            return False

        polarity_flip = (cur["is_negative"] and prev["is_affirmative"]) or (
            prev["is_negative"] and cur["is_affirmative"]
        )
        return polarity_flip

    @staticmethod
    def _normalize_tokens(text: str) -> Dict[str, Any]:
        tokens = re.findall(r"[a-z0-9']+", text.lower())
        content = [t for t in tokens if t not in NEGATION_WORDS and t not in AFFIRM_WORDS]

        return {
            "content_tokens": content,
            "is_negative": any(t in NEGATION_WORDS for t in tokens),
            "is_affirmative": any(t in AFFIRM_WORDS for t in tokens),
        }

    @staticmethod
    def _normalize_q_label(raw_q_id: Optional[str]) -> Optional[str]:
        if not raw_q_id:
            return None
        m = re.search(r"(\d+)", str(raw_q_id))
        if not m:
            return str(raw_q_id)
        return f"Q{int(m.group(1))}"
