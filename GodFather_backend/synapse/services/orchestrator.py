from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import instructor
from elasticsearch_dsl import connections
from openai import AzureOpenAI
from pydantic import BaseModel

from document.utils.embedding_service import _normalize_azure_endpoint
from synapse.documents import SYNAPSE_NODE_2_ALIAS
from synapse.services.contradiction_engine import ContradictionEngine
from synapse.services.prompt_assembler import PromptAssembler
from synapse.services.prosody_classifier import get_classifier
from synapse.services.question_router import QuestionRouter
from synapse.services.rag_retrieval import HybridRAGService
from synapse.services.shadow_profile import ShadowProfileService


class LLMResponse(BaseModel):
    status: str
    reply: str
    extracted: Dict[str, Any]
    pressure_used: int
    coach_reasoning: str


class OrchestratorResult(BaseModel):
    status: str
    reply: str
    next_q_id: Optional[str]
    depth_score: float
    session_updated: bool


class QuestionOrchestrator:
    SESSION_INDEX = "synapse_sessions"
    EPISODIC_INDEX = "synapse_episodic"

    def __init__(self) -> None:
        self.es = connections.get_connection(alias=SYNAPSE_NODE_2_ALIAS)
        self.prosody = get_classifier()
        self.contradiction_engine = ContradictionEngine()
        self.shadow_service = ShadowProfileService()
        self.rag_service = HybridRAGService()
        self.prompt_assembler = PromptAssembler()
        self.router = QuestionRouter()
        self.llm = self._build_llm_client()

    def process_answer(self, session_id: str, q_id: str, user_answer: str) -> OrchestratorResult:
        # 1) Load session from ES Node 2
        session_doc_id, session = self._load_session(session_id)
        if not session_doc_id:
            raise ValueError(f"Session not found: {session_id}")

        question_text = self._resolve_question_text(session=session, q_id=q_id)
        current_phase = self.router.get_phase(q_id)

        # 2) Run ProsodyClassifier on answer
        prosody_result = self._run_prosody(answer=user_answer, question=question_text, phase=current_phase)

        # 3) Gate 1 immediate reject on vendor language
        if not bool(prosody_result.get("gate_1_pass", True)):
            vendor_phrases = prosody_result.get("vendor_phrases_found", []) or []
            called_out = vendor_phrases[0] if vendor_phrases else "vendor language"
            reply = (
                f"I hear '{called_out}' in your answer. That's vendor framing, not brand truth. "
                "Say what you believe, not what you offer."
            )
            self._increment_resistance_and_write_episodic(
                session_id=session_id,
                q_id=q_id,
                user_answer=user_answer,
                prosody_result=prosody_result,
                contradiction_result=None,
                pressure_used=int(prosody_result.get("pressure_recommendation", 3) or 3),
                status="REJECT",
                answer_embedding=None,
            )
            return OrchestratorResult(
                status="REJECT",
                reply=reply,
                next_q_id=None,
                depth_score=self._depth_score(prosody_result=prosody_result, session=session, answer=user_answer),
                session_updated=False,
            )

        # 4) Run ContradictionEngine
        contradiction_result = self.contradiction_engine.check_contradiction(
            session_id=session_id,
            q_id=q_id,
            current_answer=user_answer,
            current_embedding=None,
        )

        # 5) Run ShadowProfileService.update_profile()
        updated_shadow = self.shadow_service.update_profile(
            session_id=session_id,
            q_id=q_id,
            prosody_result={**prosody_result, "raw_answer": user_answer},
            answer_embedding=None,
        )

        # 6) Determine pressure_level
        resistance_count = self._get_resistance_count(session_id=session_id, q_id=q_id)
        pressure_reco = int(prosody_result.get("pressure_recommendation", 3) or 3)
        if resistance_count == 0:
            pressure_level = pressure_reco
        else:
            pressure_level = pressure_reco + 1
        pressure_level = max(1, min(5, pressure_level))

        # 7) Run HybridRAGService.get_question_context()
        rag_context = self.rag_service.get_question_context(
            q_id=q_id,
            phase=current_phase,
            user_answer=user_answer,
            pressure_level=pressure_level,
            session=session,
        )

        # 8) Run PromptAssembler.assemble()
        assembled = self.prompt_assembler.assemble(
            session={**session, "shadow_profile": updated_shadow},
            q_id=q_id,
            question_text=question_text,
            user_answer=user_answer,
            prosody_result=prosody_result,
            rag_context=rag_context,
            contradiction_result=contradiction_result,
            pressure_level=pressure_level,
        )

        # 9) Call Azure OpenAI Chat Completion with instructor
        llm_response = self._call_llm(assembled.system_prompt, assembled.user_prompt)

        # 10) Parse LLMResponse (already typed by instructor)
        parsed = llm_response

        # 11) REJECT path
        if str(parsed.status).upper() == "REJECT":
            self._increment_resistance_and_write_episodic(
                session_id=session_id,
                q_id=q_id,
                user_answer=user_answer,
                prosody_result=prosody_result,
                contradiction_result=contradiction_result.model_dump() if hasattr(contradiction_result, "model_dump") else contradiction_result,
                pressure_used=pressure_level,
                status="REJECT",
                answer_embedding=None,
            )
            return OrchestratorResult(
                status="REJECT",
                reply=parsed.reply,
                next_q_id=None,
                depth_score=self._depth_score(prosody_result=prosody_result, session=session, answer=user_answer),
                session_updated=False,
            )

        # 12) PASS path
        cfg = self.router.get_question(q_id)
        next_q_id = cfg.next if cfg else self._next_q_id(q_id)
        extracted = parsed.extracted or {}

        self._write_episodic_entry(
            session_id=session_id,
            q_id=q_id,
            user_answer=user_answer,
            prosody_result=prosody_result,
            contradiction_result=contradiction_result.model_dump() if hasattr(contradiction_result, "model_dump") else contradiction_result,
            pressure_used=pressure_level,
            resistance_count=0,
            status="PASS",
            answer_embedding=None,
        )

        thread_index = dict(session.get("thread_index", {}) or {})
        if extracted.get("brand_seed"):
            thread_index["brand_seed"] = extracted.get("brand_seed")
        if extracted.get("tension"):
            thread_index["tension"] = extracted.get("tension")
        if extracted.get("key_phrase"):
            phrases = list(thread_index.get("key_phrases", []) or [])
            phrases.append(extracted.get("key_phrase"))
            thread_index["key_phrases"] = phrases[-20:]

        all_answers = list(session.get("all_answers", []) or [])
        all_answers.append(
            {
                "q_id": q_id,
                "raw_answer": user_answer,
                "status": "PASS",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

        patch = {
            "thread_index": thread_index,
            "all_answers": all_answers,
            "current_q_id": next_q_id,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        self.es.update(
            index=self.SESSION_INDEX,
            id=session_doc_id,
            body={"doc": patch},
            refresh=True,
        )

        self.router.handle_post_pass(session_id=session_id, q_id=q_id)

        # Refresh shadow profile after session update as required.
        self.shadow_service.update_profile(
            session_id=session_id,
            q_id=q_id,
            prosody_result={**prosody_result, "raw_answer": user_answer},
            answer_embedding=None,
        )

        return OrchestratorResult(
            status="PASS",
            reply=parsed.reply,
            next_q_id=next_q_id,
            depth_score=self._depth_score(prosody_result=prosody_result, session=session, answer=user_answer),
            session_updated=True,
        )

    def _run_prosody(self, answer: str, question: str, phase: str) -> Dict[str, Any]:
        if self.prosody is None:
            # Safe fallback if preload was skipped.
            return {
                "gate_1_pass": True,
                "vendor_phrases_found": [],
                "pressure_recommendation": 3,
                "emotional_weight": 0.5,
                "hedge_score": 0.5,
            }
        result = self.prosody.analyze(answer=answer, question=question, phase=phase)
        if hasattr(result, "model_dump"):
            return result.model_dump()
        if hasattr(result, "dict"):
            return result.dict()
        return dict(result)

    def _call_llm(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        model = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")
        return self.llm.chat.completions.create(
            model=model,
            response_model=LLMResponse,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )

    def _build_llm_client(self):
        endpoint = _normalize_azure_endpoint(os.getenv("AZURE_OPENAI_ENDPOINT", ""))
        api_key = os.getenv("AZURE_OPENAI_API_KEY", "")
        if not endpoint or not api_key:
            raise ValueError("Missing AZURE_OPENAI_ENDPOINT or AZURE_OPENAI_API_KEY")

        client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21"),
        )
        return instructor.patch(client)

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

    def _get_resistance_count(self, session_id: str, q_id: str) -> int:
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
            return 0
        src = hits[0].get("_source", {})
        return int(src.get("resistance_count", 0) or 0)

    def _write_episodic_entry(
        self,
        session_id: str,
        q_id: str,
        user_answer: str,
        prosody_result: Dict[str, Any],
        contradiction_result: Optional[Dict[str, Any]],
        pressure_used: int,
        resistance_count: int,
        status: str,
        answer_embedding: Optional[List[float]],
    ) -> None:
        contradiction_flags = []
        if contradiction_result and contradiction_result.get("conflicting_q_id"):
            contradiction_flags = [str(contradiction_result.get("conflicting_q_id"))]

        doc = {
            "session_id": session_id,
            "q_id": q_id,
            "raw_answer": user_answer,
            "emotional_weight": float(prosody_result.get("emotional_weight", 0.0) or 0.0),
            "resistance_level": str(prosody_result.get("resistance_level", "medium") or "medium"),
            "resistance_count": resistance_count,
            "prosody_flags": self._prosody_flags(prosody_result),
            "key_phrase": self._extract_key_phrase(user_answer),
            "contradiction_flags": contradiction_flags,
            "pressure_level_used": int(pressure_used),
            "brand_seed_echo": self._brand_seed_echo(session_id=session_id, answer=user_answer),
            "answer_embedding": answer_embedding,
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        doc_id = f"{session_id}:{q_id}"
        self.es.update(
            index=self.EPISODIC_INDEX,
            id=doc_id,
            body={"doc": doc, "doc_as_upsert": True},
            refresh=True,
        )

    def _increment_resistance_and_write_episodic(
        self,
        session_id: str,
        q_id: str,
        user_answer: str,
        prosody_result: Dict[str, Any],
        contradiction_result: Optional[Dict[str, Any]],
        pressure_used: int,
        status: str,
        answer_embedding: Optional[List[float]],
    ) -> None:
        current = self._get_resistance_count(session_id=session_id, q_id=q_id)
        self._write_episodic_entry(
            session_id=session_id,
            q_id=q_id,
            user_answer=user_answer,
            prosody_result=prosody_result,
            contradiction_result=contradiction_result,
            pressure_used=pressure_used,
            resistance_count=current + 1,
            status=status,
            answer_embedding=answer_embedding,
        )

    def _resolve_question_text(self, session: Dict[str, Any], q_id: str) -> str:
        cfg = self.router.get_question(q_id)
        if cfg:
            return cfg.prompt
        bank = session.get("question_bank", {})
        if isinstance(bank, dict) and bank.get(q_id):
            return str(bank.get(q_id))
        return f"Question {q_id}"

    @staticmethod
    def _next_q_id(q_id: str) -> Optional[str]:
        m = re.search(r"(\d+)", str(q_id))
        if not m:
            return None
        n = int(m.group(1)) + 1
        if n > 30:
            return None
        return f"Q{n}"

    def _depth_score(self, prosody_result: Dict[str, Any], session: Dict[str, Any], answer: str) -> float:
        emotional_weight = float(prosody_result.get("emotional_weight", 0.0) or 0.0)
        hedge_score = float(prosody_result.get("hedge_score", 1.0) or 1.0)
        brand_seed_echo = 1.0 if self._brand_seed_echo_from_session(session, answer) else 0.0

        score = (emotional_weight * 0.4) + ((1.0 - hedge_score) * 0.3) + (brand_seed_echo * 0.3)
        return round(max(0.0, min(1.0, score)), 4)

    @staticmethod
    def _prosody_flags(prosody_result: Dict[str, Any]) -> List[str]:
        flags = []
        for key in [
            "vendor_language_detected",
            "deflection_detected",
            "passive_voice",
            "question_echo",
            "avoidance_length",
            "money_motivation",
        ]:
            if bool(prosody_result.get(key, False)):
                flags.append(key)
        return flags

    @staticmethod
    def _extract_key_phrase(answer: str) -> str:
        text = (answer or "").strip()
        if not text:
            return ""
        parts = [p.strip() for p in re.split(r"[.!?]", text) if p.strip()]
        if parts:
            parts.sort(key=len, reverse=True)
            return parts[0][:220]
        return text[:220]

    def _brand_seed_echo(self, session_id: str, answer: str) -> bool:
        _, session = self._load_session(session_id)
        return self._brand_seed_echo_from_session(session, answer)

    @staticmethod
    def _brand_seed_echo_from_session(session: Dict[str, Any], answer: str) -> bool:
        seed = str(session.get("brand_seed", "") or "").strip().lower()
        if not seed:
            return False
        return seed in (answer or "").lower()
