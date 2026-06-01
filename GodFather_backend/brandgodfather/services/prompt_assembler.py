from __future__ import annotations

from string import Template
from typing import Any, Dict, Optional

from pydantic import BaseModel


class AssembledPrompt(BaseModel):
    system_prompt: str
    user_prompt: str
    expected_output_schema: Dict[str, Any]


class PromptAssembler:
    CORE_IDENTITY_TEXT = (
        "You are BrandGodFather, a Benevolent Authority created by\n"
        "The Brand Godfather. You do not apologize for\n"
        "challenging the user. You never defer your authority\n"
        "back to them. You speak with precision and warmth.\n"
        "You are not a chatbot. You are a coach who has\n"
        "seen a thousand founders avoid this exact question."
    )

    PRESSURE_RULES = {
        1: (
            "Gently reflect their words back.\n"
            "Ask what's underneath."
        ),
        2: (
            "Reframe their answer. Offer an alternative\n"
            "interpretation. Ask if it fits better."
        ),
        3: (
            "Directly name the pattern you see.\n"
            "'It sounds like you're describing what you DO,\n"
            "not what you BELIEVE.' Then ask again."
        ),
        4: (
            "State explicitly what their answer reveals\n"
            "about their current positioning. Connect it\n"
            "to brand invisibility."
        ),
        5: (
            "Tell them exactly what staying at this level\n"
            "of thinking costs them in market terms.\n"
            "Be direct. Do not soften."
        ),
    }

    OUTPUT_SCHEMA = {
        "status": "PASS | REJECT",
        "reply": "what the user sees",
        "extracted": {
            "brand_seed": "only on Q1 if PASS",
            "tension": "only on Q4 if PASS",
            "key_phrase": "the most emotionally loaded phrase",
        },
        "pressure_used": "int",
        "coach_reasoning": "internal note, never shown to user",
    }

    def assemble(
        self,
        session: Any,
        q_id: str,
        question_text: str,
        user_answer: str,
        prosody_result: Any,
        rag_context: Any,
        contradiction_result: Any,
        pressure_level: int,
    ) -> AssembledPrompt:
        normalized_pressure = self._normalize_pressure(pressure_level)

        sections = [
            self._section_header(1, "Core Identity"),
            self._core_identity_section(),
            self._section_header(2, "Current Session State"),
            self._session_state_section(session=session, q_id=q_id),
            self._section_header(3, "Shadow Profile Injection"),
            self._shadow_profile_section(session=session),
            self._section_header(4, "Prosody Context"),
            self._prosody_context_section(prosody_result=prosody_result),
            self._section_header(5, "Contradiction Injection"),
            self._contradiction_section(contradiction_result=contradiction_result),
            self._section_header(6, "RAG Context"),
            self._rag_context_section(rag_context=rag_context),
            self._section_header(7, "Thread Index"),
            self._thread_index_section(session=session),
            self._section_header(8, "Pressure Level Instructions"),
            self._pressure_section(pressure_level=normalized_pressure),
            self._section_header(9, "Enforcement Rule"),
            self._enforcement_rule_section(q_id=q_id),
            self._section_header(10, "Output Format Requirement"),
            self._output_requirement_section(),
        ]

        system_prompt = "\n\n".join(sections).strip()
        user_prompt = self._user_prompt_section(question_text=question_text, user_answer=user_answer)

        return AssembledPrompt(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            expected_output_schema=self.OUTPUT_SCHEMA,
        )

    @staticmethod
    def _section_header(order: int, title: str) -> str:
        return "[{order}] {title}".format(order=order, title=title)

    def _core_identity_section(self) -> str:
        return self.CORE_IDENTITY_TEXT

    def _session_state_section(self, session: Any, q_id: str) -> str:
        template = Template(
            "brand_seed: $brand_seed\n"
            "phase: $phase\n"
            "q_id: $q_id"
        )
        data = {
            "brand_seed": self._session_value(session, "brand_seed", "unknown"),
            "phase": self._session_value(session, "current_phase", "unknown"),
            "q_id": q_id,
        }
        return template.safe_substitute(data)

    def _shadow_profile_section(self, session: Any) -> str:
        shadow = self._session_value(session, "shadow_profile", {})
        if not isinstance(shadow, dict):
            shadow = {}

        template = Template(
            "self_image: $self_image\n"
            "actual_signal: $actual_signal\n"
            "gap_score: $gap_score\n"
            "fear_pattern: $fear_pattern\n"
            "readiness_estimate: $readiness_estimate"
        )
        data = {
            "self_image": shadow.get("self_image", "unknown"),
            "actual_signal": shadow.get("actual_signal", "unknown"),
            "gap_score": shadow.get("gap_score", "unknown"),
            "fear_pattern": shadow.get("fear_pattern", "unknown"),
            "readiness_estimate": shadow.get("readiness_estimate", "unknown"),
        }
        return template.safe_substitute(data)

    def _prosody_context_section(self, prosody_result: Any) -> str:
        result = self._as_dict(prosody_result)
        template = Template(
            "vendor_language_detected: $vendor_language_detected\n"
            "vendor_phrases_found: $vendor_phrases_found\n"
            "hedge_score: $hedge_score\n"
            "deflection_detected: $deflection_detected\n"
            "passive_voice: $passive_voice\n"
            "question_echo: $question_echo\n"
            "avoidance_length: $avoidance_length\n"
            "money_motivation: $money_motivation\n"
            "emotional_weight: $emotional_weight\n"
            "resistance_level: $resistance_level\n"
            "gate_1_pass: $gate_1_pass\n"
            "gate_2_pass: $gate_2_pass\n"
            "pressure_recommendation: $pressure_recommendation"
        )
        data = {
            "vendor_language_detected": result.get("vendor_language_detected", "unknown"),
            "vendor_phrases_found": result.get("vendor_phrases_found", []),
            "hedge_score": result.get("hedge_score", "unknown"),
            "deflection_detected": result.get("deflection_detected", "unknown"),
            "passive_voice": result.get("passive_voice", "unknown"),
            "question_echo": result.get("question_echo", "unknown"),
            "avoidance_length": result.get("avoidance_length", "unknown"),
            "money_motivation": result.get("money_motivation", "unknown"),
            "emotional_weight": result.get("emotional_weight", "unknown"),
            "resistance_level": result.get("resistance_level", "unknown"),
            "gate_1_pass": result.get("gate_1_pass", "unknown"),
            "gate_2_pass": result.get("gate_2_pass", "unknown"),
            "pressure_recommendation": result.get("pressure_recommendation", "unknown"),
        }
        return template.safe_substitute(data)

    def _contradiction_section(self, contradiction_result: Any) -> str:
        result = self._as_dict(contradiction_result)
        has_contradiction = bool(result.get("has_contradiction", False))

        if not has_contradiction:
            return "No contradiction found for this turn."

        template = Template(
            "has_contradiction: true\n"
            "conflicting_q_id: $conflicting_q_id\n"
            "topic: $topic\n"
            "instruction: $summary"
        )
        data = {
            "conflicting_q_id": result.get("conflicting_q_id", "unknown"),
            "topic": result.get("topic", "unknown"),
            "summary": result.get("contradiction_summary", "No summary provided."),
        }
        return template.safe_substitute(data)

    def _rag_context_section(self, rag_context: Any) -> str:
        result = self._as_dict(rag_context)

        template = Template(
            "question_chunks: $question_chunks\n"
            "challenge_chunks: $challenge_chunks\n"
            "gold_standard: $gold_standard\n"
            "rejection_example: $rejection_example"
        )
        data = {
            "question_chunks": result.get("question_chunks", []),
            "challenge_chunks": result.get("challenge_chunks", []),
            "gold_standard": result.get("gold_standard", None),
            "rejection_example": result.get("rejection_example", None),
        }
        return template.safe_substitute(data)

    def _thread_index_section(self, session: Any) -> str:
        thread_index = self._session_value(session, "thread_index", {})
        if not thread_index:
            return "No thread index anchors available yet."

        return "emotional_anchors: {anchors}".format(anchors=thread_index)

    def _pressure_section(self, pressure_level: int) -> str:
        template = Template(
            "pressure_level: $pressure_level\n"
            "rule:\n$rule"
        )
        return template.safe_substitute(
            {
                "pressure_level": pressure_level,
                "rule": self.PRESSURE_RULES[pressure_level],
            }
        )

    def _enforcement_rule_section(self, q_id: str) -> str:
        template = Template(
            "Enforce the exact acceptance criteria for $q_id.\n"
            "If criteria are not met, return status=REJECT, apply pressure rule, and re-ask with precision.\n"
            "Do not soften challenge if contradiction, vendor language, or deflection is detected."
        )
        return template.safe_substitute({"q_id": q_id})

    def _output_requirement_section(self) -> str:
        template = Template(
            "Return ONLY valid JSON:\n"
            "{\n"
            "  \"status\": \"PASS\" | \"REJECT\",\n"
            "  \"reply\": \"what the user sees\",\n"
            "  \"extracted\": {\n"
            "    \"brand_seed\": \"only on Q1 if PASS\",\n"
            "    \"tension\": \"only on Q4 if PASS\",\n"
            "    \"key_phrase\": \"the most emotionally loaded phrase\"\n"
            "  },\n"
            "  \"pressure_used\": int,\n"
            "  \"coach_reasoning\": \"internal note, never shown to user\"\n"
            "}"
        )
        return template.safe_substitute({})

    def _user_prompt_section(self, question_text: str, user_answer: str) -> str:
        template = Template(
            "question_text:\n"
            "$question_text\n\n"
            "user_current_answer:\n"
            "$user_answer"
        )
        return template.safe_substitute(
            {
                "question_text": question_text.strip(),
                "user_answer": user_answer.strip(),
            }
        )

    @staticmethod
    def _normalize_pressure(level: int) -> int:
        if level < 1:
            return 1
        if level > 5:
            return 5
        return int(level)

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
    def _session_value(session: Any, key: str, default: Optional[Any] = None) -> Any:
        if session is None:
            return default
        if isinstance(session, dict):
            return session.get(key, default)
        return getattr(session, key, default)
