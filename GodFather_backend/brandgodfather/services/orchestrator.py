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
from brandgodfather.documents import BRANDGODFATHER_NODE_2_ALIAS
from brandgodfather.services.breakthrough_recognition import BreakthroughRecognitionService
from brandgodfather.services.contradiction_engine import ContradictionEngine
from brandgodfather.services.prompt_assembler import PromptAssembler
from brandgodfather.services.prosody_classifier import HEDGE_WORDS, MONEY_KEYWORDS, VENDOR_PHRASES, get_classifier
from brandgodfather.services.question_router import QuestionRouter
from brandgodfather.services.rag_retrieval import HybridRAGService
from brandgodfather.services.shadow_profile import ShadowProfileService


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
    interruption_type: Optional[str] = None
    challenge_type: Optional[str] = None
    pressure_used: Optional[int] = None
    resistance_count: int = 0
    blocked_phrases: List[str] = []
    prosody_flags: List[str] = []
    emotional_state: str = "neutral"
    tone_mode: str = "direct_challenge"
    contradiction_result: Optional[Dict[str, Any]] = None
    contradiction_message: Optional[str] = None
    breakthrough_detected: bool = False
    breakthrough_score: float = 0.0
    breakthrough_type: Optional[str] = None
    breakthrough_reason: Optional[str] = None
    breakthrough_seed: Optional[str] = None
    breakthrough_criteria: Dict[str, bool] = {}


class QuestionOrchestrator:
    SESSION_INDEX = "brandgodfather_sessions"
    EPISODIC_INDEX = "brandgodfather_episodic"

    def __init__(self) -> None:
        self.es = connections.get_connection(alias=BRANDGODFATHER_NODE_2_ALIAS)
        self.prosody = get_classifier()
        self.breakthrough_service = BreakthroughRecognitionService()
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
        resistance_count = self._get_resistance_count(session_id=session_id, q_id=q_id)
        pressure_level = self._pressure_level(prosody_result=prosody_result, resistance_count=resistance_count)
        challenge_type = self._challenge_type(prosody_result)
        emotional_state = self._emotional_state(answer=user_answer, prosody_result=prosody_result)
        tone_mode = self._tone_mode(emotional_state=emotional_state, challenge_type=challenge_type)
        prosody_result = {**prosody_result, "emotional_state": emotional_state, "tone_mode": tone_mode}

        # 3) Gate 1 immediate reject on vendor language
        if not bool(prosody_result.get("gate_1_pass", True)):
            vendor_phrases = prosody_result.get("vendor_phrases_found", []) or []
            called_out = vendor_phrases[0] if vendor_phrases else "vendor language"
            reply = (
                f"I hear '{called_out}'. That's the vendor trap. People rarely remember vendors. "
                "Give me the brand: what do you stand for, who is it for, and why should they care?"
            )
            reply = self._calibrate_reply_tone(reply=reply, emotional_state=emotional_state)
            self._increment_resistance_and_write_episodic(
                session_id=session_id,
                q_id=q_id,
                user_answer=user_answer,
                prosody_result=prosody_result,
                contradiction_result=None,
                pressure_used=pressure_level,
                status="REJECT",
                answer_embedding=None,
            )
            return OrchestratorResult(
                status="REJECT",
                reply=reply,
                next_q_id=None,
                depth_score=self._depth_score(prosody_result=prosody_result, session=session, answer=user_answer),
                session_updated=False,
                interruption_type="vendor_language",
                challenge_type="vendor_language",
                pressure_used=pressure_level,
                resistance_count=resistance_count + 1,
                blocked_phrases=vendor_phrases,
                prosody_flags=self._prosody_flags(prosody_result),
                emotional_state=emotional_state,
                tone_mode=tone_mode,
            )

        # 4) Run ContradictionEngine
        contradiction_result = self.contradiction_engine.check_contradiction(
            session_id=session_id,
            q_id=q_id,
            current_answer=user_answer,
            current_embedding=None,
        )

        contradiction_payload = (
            contradiction_result.model_dump() if hasattr(contradiction_result, "model_dump") else dict(contradiction_result)
        )

        if bool(contradiction_payload.get("has_contradiction")):
            contradiction_message = self._contradiction_message(contradiction_payload)
            contradiction_message = self._calibrate_reply_tone(
                reply=contradiction_message,
                emotional_state=emotional_state,
            )
            self._increment_resistance_and_write_episodic(
                session_id=session_id,
                q_id=q_id,
                user_answer=user_answer,
                prosody_result=prosody_result,
                contradiction_result=contradiction_payload,
                pressure_used=pressure_level,
                status="REJECT",
                answer_embedding=None,
            )
            return OrchestratorResult(
                status="REJECT",
                reply=contradiction_message,
                next_q_id=None,
                depth_score=self._depth_score(prosody_result=prosody_result, session=session, answer=user_answer),
                session_updated=False,
                interruption_type="contradiction",
                challenge_type="contradiction",
                pressure_used=pressure_level,
                resistance_count=resistance_count + 1,
                prosody_flags=self._prosody_flags(prosody_result),
                emotional_state=emotional_state,
                tone_mode=tone_mode,
                contradiction_result=contradiction_payload,
                contradiction_message=contradiction_message,
            )

        if not bool(prosody_result.get("gate_2_pass", True)):
            adaptive_reply = self._adaptive_coaching_reply(
                user_answer=user_answer,
                pressure_level=pressure_level,
                resistance_count=resistance_count,
                challenge_type=challenge_type,
                emotional_state=emotional_state,
            )
            self._increment_resistance_and_write_episodic(
                session_id=session_id,
                q_id=q_id,
                user_answer=user_answer,
                prosody_result=prosody_result,
                contradiction_result=contradiction_payload,
                pressure_used=pressure_level,
                status="REJECT",
                answer_embedding=None,
            )
            return OrchestratorResult(
                status="REJECT",
                reply=adaptive_reply,
                next_q_id=None,
                depth_score=self._depth_score(prosody_result=prosody_result, session=session, answer=user_answer),
                session_updated=False,
                interruption_type="adaptive_coaching",
                challenge_type=challenge_type,
                pressure_used=pressure_level,
                resistance_count=resistance_count + 1,
                prosody_flags=self._prosody_flags(prosody_result),
                emotional_state=emotional_state,
                tone_mode=tone_mode,
                contradiction_result=contradiction_payload,
            )

        breakthrough_result = self.breakthrough_service.analyze(
            answer=user_answer,
            q_id=q_id,
            question_text=question_text,
            prosody_result=prosody_result,
            contradiction_result=contradiction_payload,
        )
        breakthrough_payload = (
            breakthrough_result.model_dump() if hasattr(breakthrough_result, "model_dump") else breakthrough_result.dict()
        )
        breakthrough_seed = str(breakthrough_payload.get("brand_seed_candidate") or "").strip()
        breakthrough_detected = bool(breakthrough_payload.get("breakthrough_detected"))

        # 5) Run ShadowProfileService.update_profile()
        updated_shadow = self.shadow_service.update_profile(
            session_id=session_id,
            q_id=q_id,
            prosody_result={**prosody_result, "raw_answer": user_answer},
            answer_embedding=None,
        )

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

        # 9) Breakthrough answers are an active PASS gate; otherwise ask the LLM.
        if breakthrough_detected:
            parsed = LLMResponse(
                status="PASS",
                reply="",
                extracted={"brand_seed": breakthrough_seed, "key_phrase": breakthrough_seed},
                pressure_used=pressure_level,
                coach_reasoning="Deterministic breakthrough recognition criteria met.",
            )
        else:
            llm_response = self._call_llm(assembled.system_prompt, assembled.user_prompt)
            parsed = llm_response

        # 11) REJECT path
        if str(parsed.status).upper() == "REJECT":
            reply = self._calibrate_reply_tone(reply=parsed.reply, emotional_state=emotional_state)
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
                reply=reply,
                next_q_id=None,
                depth_score=self._depth_score(prosody_result=prosody_result, session=session, answer=user_answer),
                session_updated=False,
                challenge_type=challenge_type,
                pressure_used=pressure_level,
                resistance_count=resistance_count + 1,
                emotional_state=emotional_state,
                tone_mode=tone_mode,
                contradiction_result=contradiction_payload,
                contradiction_message=self._contradiction_message(contradiction_payload) if contradiction_payload.get("has_contradiction") else None,
            )

        # 12) PASS path
        cfg = self.router.get_question(q_id)
        next_q_id = cfg.next if cfg else self._next_q_id(q_id)
        extracted = parsed.extracted or {}
        reply = parsed.reply
        if breakthrough_detected:
            reply = (
                "That is the truth/edge. Keep that as a brand seed. "
                f"{breakthrough_payload.get('breakthrough_reason')}"
            )

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
            breakthrough_result=breakthrough_payload,
        )

        thread_index = dict(session.get("thread_index", {}) or {})
        brand_seed_value = str(extracted.get("brand_seed") or breakthrough_seed or "").strip()
        if brand_seed_value:
            thread_index["brand_seed"] = brand_seed_value
        if extracted.get("tension"):
            thread_index["tension"] = extracted.get("tension")
        if extracted.get("key_phrase"):
            phrases = list(thread_index.get("key_phrases", []) or [])
            phrases.append(extracted.get("key_phrase"))
            thread_index["key_phrases"] = phrases[-20:]
        if breakthrough_detected:
            breakthrough_moments = list(thread_index.get("breakthrough_moments", []) or [])
            breakthrough_moments.append(
                {
                    "q_id": q_id,
                    "seed": breakthrough_seed,
                    "score": breakthrough_payload.get("breakthrough_score"),
                    "type": breakthrough_payload.get("breakthrough_type"),
                    "reason": breakthrough_payload.get("breakthrough_reason"),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
            thread_index["breakthrough_moments"] = breakthrough_moments[-10:]
            thread_index["latest_breakthrough_seed"] = breakthrough_seed

        all_answers = list(session.get("all_answers", []) or [])
        all_answers.append(
            {
                "q_id": q_id,
                "raw_answer": user_answer,
                "status": "PASS",
                "breakthrough_detected": breakthrough_detected,
                "breakthrough_score": breakthrough_payload.get("breakthrough_score", 0.0),
                "breakthrough_seed": breakthrough_seed if breakthrough_detected else "",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

        patch = {
            "thread_index": thread_index,
            "all_answers": all_answers,
            "current_q_id": next_q_id,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        if brand_seed_value:
            patch["brand_seed"] = brand_seed_value

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
            reply=reply,
            next_q_id=next_q_id,
            depth_score=self._depth_score(prosody_result=prosody_result, session=session, answer=user_answer),
            session_updated=True,
            challenge_type=challenge_type,
            pressure_used=pressure_level,
            resistance_count=0,
            emotional_state=emotional_state,
            tone_mode=tone_mode,
            contradiction_result=contradiction_payload,
            contradiction_message=self._contradiction_message(contradiction_payload) if contradiction_payload.get("has_contradiction") else None,
            breakthrough_detected=breakthrough_detected,
            breakthrough_score=float(breakthrough_payload.get("breakthrough_score", 0.0) or 0.0),
            breakthrough_type=breakthrough_payload.get("breakthrough_type"),
            breakthrough_reason=breakthrough_payload.get("breakthrough_reason"),
            breakthrough_seed=breakthrough_seed if breakthrough_detected else None,
            breakthrough_criteria=dict(breakthrough_payload.get("criteria") or {}),
        )

    @staticmethod
    def _pressure_level(prosody_result: Dict[str, Any], resistance_count: int) -> int:
        pressure_reco = int(prosody_result.get("pressure_recommendation", 3) or 3)
        return max(1, min(5, pressure_reco + max(0, int(resistance_count or 0))))

    @staticmethod
    def _challenge_type(prosody_result: Dict[str, Any]) -> str:
        if bool(prosody_result.get("deflection_detected")):
            return "deflection"
        if bool(prosody_result.get("avoidance_length")):
            return "shallow_answer"
        if bool(prosody_result.get("question_echo")):
            return "question_echo"
        if float(prosody_result.get("hedge_score", 0.0) or 0.0) > 0.15:
            return "hedging"
        if bool(prosody_result.get("money_motivation")):
            return "money_motivation"
        return "adaptive_coaching"

    @staticmethod
    def _emotional_state(answer: str, prosody_result: Dict[str, Any]) -> str:
        lower = (answer or "").lower()
        states = [
            ("confused", ("confused", "unclear", "lost", "stuck", "overwhelmed", "not sure", "don't know", "dont know")),
            ("discouraged", ("discouraged", "frustrated", "tired", "exhausted", "defeated", "hopeless", "struggling")),
            ("afraid", ("afraid", "scared", "fear", "worried", "anxious", "nervous", "terrified", "judged")),
            ("excited", ("excited", "energized", "ready", "inspired", "passionate", "love", "can't wait", "cant wait")),
        ]
        for state, markers in states:
            if any(marker in lower for marker in markers):
                return state
        if bool(prosody_result.get("deflection_detected")) or float(prosody_result.get("hedge_score", 0.0) or 0.0) > 0.15:
            return "avoidant"
        if float(prosody_result.get("emotional_weight", 0.0) or 0.0) >= 0.75:
            return "engaged"
        return "neutral"

    @staticmethod
    def _tone_mode(emotional_state: str, challenge_type: str) -> str:
        if emotional_state == "confused":
            return "clarifying_challenge"
        if emotional_state in {"discouraged", "afraid"}:
            return "supportive_challenge"
        if emotional_state in {"excited", "engaged"}:
            return "energized_challenge"
        if emotional_state == "avoidant" or challenge_type in {"deflection", "question_echo"}:
            return "firm_challenge"
        return "direct_challenge"

    @staticmethod
    def _calibrate_reply_tone(reply: str, emotional_state: str) -> str:
        text = str(reply or "").strip()
        if not text:
            return text
        if emotional_state == "confused":
            return f"Stay with the question. The confusion is useful if we make it specific. {text}"
        if emotional_state in {"discouraged", "afraid"}:
            return f"This may feel uncomfortable, but it is workable. {text}"
        if emotional_state in {"excited", "engaged"}:
            return f"Use that energy with precision. {text}"
        if emotional_state == "avoidant":
            return f"Do not dodge this. {text}"
        return text

    @staticmethod
    def _adaptive_coaching_reply(
        user_answer: str,
        pressure_level: int,
        resistance_count: int,
        challenge_type: str,
        emotional_state: str = "neutral",
    ) -> str:
        pressure = max(1, min(5, int(pressure_level or 3)))
        if pressure >= 5:
            if emotional_state == "confused":
                return (
                    "Slow down. The confusion is useful, but repeating the same surface answer will keep the brand blurry. "
                    "Name the belief, the tension, or the truth you are avoiding."
                )
            if emotional_state in {"discouraged", "afraid"}:
                return (
                    "I can hear the hesitation. I am still not going to soften the standard: "
                    "the market will not see a brand here yet. Name the truth you are afraid to say plainly."
                )
            if emotional_state in {"excited", "engaged"}:
                return (
                    "Use that energy with precision. You are still giving me the same surface answer. "
                    "Name the belief, the tension, or the truth that makes this impossible to ignore."
                )
            return (
                "Stop there. You are giving me the same surface answer again. "
                "At this level, the market will not see a brand; it will see another option. "
                "Name the belief, the tension, or the truth you are avoiding."
            )
        if pressure == 4 or resistance_count > 0:
            if emotional_state == "confused":
                return (
                    "You are circling the question because the point is still fuzzy. "
                    "Make one concrete choice: what truth are you trying to protect here?"
                )
            if emotional_state in {"discouraged", "afraid"}:
                return (
                    "This is the hard part, and that is why it matters. "
                    "Say the uncomfortable truth behind this answer instead of sanding it down."
                )
            if emotional_state in {"excited", "engaged"}:
                return (
                    "Good energy, but it needs an edge. "
                    "Say the point of view underneath this before the language gets cleaner."
                )
            return (
                "You are circling the question, not answering it. "
                "This answer still hides the point of view. Say the uncomfortable truth behind it."
            )
        if challenge_type == "deflection":
            if emotional_state in {"discouraged", "afraid"}:
                return (
                    "This is deflection, and I am not treating that as failure. "
                    "It is the doorway. What do you actually believe here?"
                )
            return (
                "This is deflection. You are describing around the answer instead of revealing it. "
                "What do you actually believe here?"
            )
        if emotional_state == "confused":
            return (
                "You do not need polish yet; you need a sharper choice. "
                "Pick the belief or truth beneath this answer and say it plainly."
            )
        if emotional_state in {"discouraged", "afraid"}:
            return (
                "The hesitation is allowed, but hiding behind a thin answer is not. "
                "Give me the truth a competitor would avoid saying."
            )
        if emotional_state in {"excited", "engaged"}:
            return (
                "There is energy here. Now make it useful. "
                "Go beneath the obvious answer and name the point of view."
            )
        return (
            "This is still too thin to build a brand from. "
            "Go beneath the obvious answer and give me the truth a competitor would not say."
        )

    @staticmethod
    def _contradiction_message(contradiction_result: Dict[str, Any]) -> str:
        previous = str(contradiction_result.get("conflicting_answer") or "your earlier answer").strip()
        current = str(contradiction_result.get("current_answer") or "this answer").strip()
        q_ref = str(contradiction_result.get("conflicting_q_id") or "an earlier question").strip()
        return (
            f"Hold on. In {q_ref}, you said '{previous}'. Now you're saying '{current}'. "
            "Those cannot both lead the brand. Resolve the truth before we move on."
        )

    def _run_prosody(self, answer: str, question: str, phase: str) -> Dict[str, Any]:
        if self.prosody is None:
            # Safe fallback if preload was skipped.
            lower = (answer or "").lower()
            words = re.findall(r"[a-z0-9']+", lower)
            vendor_phrases_found = [phrase for phrase in VENDOR_PHRASES if phrase in lower]
            hedge_hits = sum(1 for hedge in HEDGE_WORDS if hedge in lower)
            feature_words = ("feature", "service", "offer", "provide", "solution", "product", "tool", "platform", "system")
            emotion_words = ("feel", "love", "hate", "fear", "hope", "believe", "care", "passion", "trust", "excited")
            feature_count = sum(1 for word in feature_words if word in lower)
            emotion_count = sum(1 for word in emotion_words if word in lower)
            avoidance_length = len(words) < 15
            deflection_detected = feature_count > emotion_count or lower.strip() in {"i help people", "we help people", "i help clients", "we help clients"}
            question_tokens = set(re.findall(r"[a-z0-9']+", (question or "").lower()))
            answer_tokens = set(words)
            question_echo = bool(answer_tokens) and len(answer_tokens.intersection(question_tokens)) >= max(3, min(6, len(answer_tokens)))
            money_motivation = any(keyword in lower for keyword in MONEY_KEYWORDS)
            signals_fired = sum(
                [
                    bool(vendor_phrases_found),
                    hedge_hits > 0,
                    deflection_detected,
                    question_echo,
                    avoidance_length,
                    money_motivation,
                ]
            )
            resistance_level = "high" if signals_fired >= 4 else "medium" if signals_fired >= 2 else "low"
            pressure_recommendation = 5 if signals_fired >= 4 else 3 if signals_fired >= 2 else 2
            return {
                "gate_1_pass": not bool(vendor_phrases_found),
                "vendor_language_detected": bool(vendor_phrases_found),
                "vendor_phrases_found": vendor_phrases_found,
                "pressure_recommendation": pressure_recommendation,
                "emotional_weight": 0.5,
                "hedge_score": min(1.0, hedge_hits / max(len(words), 1)),
                "deflection_detected": deflection_detected,
                "passive_voice": False,
                "question_echo": question_echo,
                "avoidance_length": avoidance_length,
                "money_motivation": money_motivation,
                "resistance_level": resistance_level,
                "gate_2_pass": signals_fired < 2,
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
        try:
            doc = self.es.get(index=self.SESSION_INDEX, id=session_id)
            source = doc.get("_source", {})
            if source:
                return doc.get("_id"), source
        except Exception:
            pass

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
        breakthrough_result: Optional[Dict[str, Any]] = None,
    ) -> None:
        contradiction_flags = []
        if contradiction_result and contradiction_result.get("conflicting_q_id"):
            contradiction_flags = [str(contradiction_result.get("conflicting_q_id"))]

        doc = {
            "session_id": session_id,
            "q_id": q_id,
            "raw_answer": user_answer,
            "emotional_weight": float(prosody_result.get("emotional_weight", 0.0) or 0.0),
            "emotional_state": str(prosody_result.get("emotional_state", "neutral") or "neutral"),
            "tone_mode": str(prosody_result.get("tone_mode", "direct_challenge") or "direct_challenge"),
            "resistance_level": str(prosody_result.get("resistance_level", "medium") or "medium"),
            "resistance_count": resistance_count,
            "prosody_flags": self._prosody_flags(prosody_result),
            "key_phrase": self._extract_key_phrase(user_answer),
            "contradiction_flags": contradiction_flags,
            "pressure_level_used": int(pressure_used),
            "brand_seed_echo": self._brand_seed_echo(session_id=session_id, answer=user_answer),
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if breakthrough_result:
            doc["breakthrough_detected"] = bool(breakthrough_result.get("breakthrough_detected"))
            doc["breakthrough_score"] = float(breakthrough_result.get("breakthrough_score", 0.0) or 0.0)
            doc["breakthrough_type"] = str(breakthrough_result.get("breakthrough_type") or "none")
            doc["breakthrough_reason"] = str(breakthrough_result.get("breakthrough_reason") or "")
            doc["breakthrough_seed"] = str(breakthrough_result.get("brand_seed_candidate") or "")
            doc["breakthrough_criteria"] = dict(breakthrough_result.get("criteria") or {})
        if answer_embedding:
            doc["answer_embedding"] = answer_embedding

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
        context_data = session.get("context_data", {}) or {}
        if isinstance(context_data, dict):
            bank = context_data.get("question_bank", {}) or {}
            if isinstance(bank, dict) and bank.get(q_id):
                return str(bank.get(q_id))
            if context_data.get("question_text"):
                return str(context_data.get("question_text"))

        bank = session.get("question_bank", {})
        if isinstance(bank, dict) and bank.get(q_id):
            return str(bank.get(q_id))
        cfg = self.router.get_question(q_id)
        if cfg:
            return cfg.prompt
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
        intrinsic_depth = self._intrinsic_depth_score(answer)

        score = (
            (emotional_weight * 0.3)
            + ((1.0 - hedge_score) * 0.2)
            + (brand_seed_echo * 0.2)
            + (intrinsic_depth * 0.3)
        )
        return round(max(0.0, min(1.0, score)), 4)

    @staticmethod
    def _intrinsic_depth_score(answer: str) -> float:
        text = (answer or "").strip().lower()
        if not text:
            return 0.0

        words = re.findall(r"\b[\w']+\b", text)
        word_count = len(words)
        markers = [
            r"\bwe believe\b",
            r"\bi believe\b",
            r"\bwe exist to\b",
            r"\bour purpose is\b",
            r"\bbeyond what we sell\b",
            r"\bbecause\b",
            r"\bso that\b",
            r"\bstand for\b",
            r"\brefuse to\b",
            r"\bpeople feel\b",
            r"\bchange\b",
            r"\btrust\b",
            r"\bconviction\b",
            r"\bclarity\b",
        ]
        vendor_markers = [
            r"\bwe provide\b",
            r"\bwe offer\b",
            r"\bour services\b",
            r"\bsolutions\b",
            r"\bquality\b",
            r"\bprofessional\b",
        ]

        marker_hits = sum(1 for pattern in markers if re.search(pattern, text))
        vendor_hits = sum(1 for pattern in vendor_markers if re.search(pattern, text))
        length_score = min(1.0, word_count / 18)
        marker_score = min(1.0, marker_hits / 3)
        vendor_penalty = min(0.45, vendor_hits * 0.15)

        return round(max(0.0, min(1.0, (length_score * 0.45) + (marker_score * 0.55) - vendor_penalty)), 4)

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
