from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List

from elasticsearch_dsl import connections
from openai import AzureOpenAI
from pydantic import BaseModel

from brandgodfather.documents import BRANDGODFATHER_NODE_2_ALIAS
from brandgodfather.services.BrandBook_generator import CLICHE_PHRASES, GENERIC_BUZZWORDS
from brandgodfather.services.prosody_classifier import VENDOR_PHRASES
from document.utils.embedding_service import _normalize_azure_endpoint


class FilterResult(BaseModel):
    brand_seed_present: bool
    foundation_energy_present: bool
    generic_filter_pass: bool
    line_in_sand_consistent: bool
    passed: bool
    failures: List[str]


class SocialIdea(BaseModel):
    angle: str
    hook_line: str
    platform_suggestion: str
    brand_seed_connection: str


class CampaignIdea(BaseModel):
    campaign_name: str
    core_message: str
    call_to_action: str
    what_it_protects: str


class OutreachTemplate(BaseModel):
    outreach_type: str
    subject_line: str
    opening: str
    trust_signal: str
    cta: str


class OutputModeEngine:
    SESSION_INDEX = "brandgodfather_sessions"

    def __init__(self) -> None:
        self.es = connections.get_connection(alias=BRANDGODFATHER_NODE_2_ALIAS)
        self.client = self._build_client()

    def generate_weekly_social(self, session_id: str) -> List[SocialIdea]:
        session = self._load_session(session_id)
        trend_context = self._trend_context()
        ideas: List[SocialIdea] = []

        for _ in range(5):
            content = self._generate_social_one(session=session, trend_context=trend_context)
            accepted = self._generate_with_filter(
                content=content,
                session=session,
                generator=self._regenerate_social_one,
            )
            ideas.append(SocialIdea(**accepted))

        return ideas

    def generate_monthly_campaign(self, session_id: str) -> CampaignIdea:
        session = self._load_session(session_id)
        content = self._generate_campaign(session=session)
        accepted = self._generate_with_filter(
            content=content,
            session=session,
            generator=self._regenerate_campaign,
        )
        return CampaignIdea(**accepted)

    def generate_weekly_outreach(self, session_id: str) -> List[OutreachTemplate]:
        session = self._load_session(session_id)
        items: List[OutreachTemplate] = []

        for _ in range(5):
            content = self._generate_outreach_one(session=session)
            accepted = self._generate_with_filter(
                content=content,
                session=session,
                generator=self._regenerate_outreach_one,
            )
            items.append(OutreachTemplate(**accepted))

        return items

    def _brand_filter(self, content: Dict[str, Any], session: Dict[str, Any]) -> FilterResult:
        text = json.dumps(content, ensure_ascii=True).lower()

        brand_seed = self._session_value(session, "brand_seed", "").strip().lower()
        foundation_words = self._foundation_words(session)
        line_in_sand = self._session_value(session, "line_in_sand", "").strip().lower()

        brand_seed_present = bool(brand_seed) and (brand_seed in text)
        if not brand_seed:
            brand_seed_present = True

        foundation_energy_present = any(w.lower() in text for w in foundation_words if w)
        if not foundation_words:
            foundation_energy_present = True

        line_in_sand_consistent = True
        if line_in_sand:
            tokens = [t for t in re.findall(r"[a-zA-Z][a-zA-Z-]+", line_in_sand) if len(t) > 3]
            line_in_sand_consistent = any(tok in text for tok in tokens[:5]) if tokens else True

        generic_filter_pass = self._generic_filter_pass(text)

        failures: List[str] = []
        if not brand_seed_present:
            failures.append("brand_seed_missing")
        if not foundation_energy_present:
            failures.append("foundation_energy_missing")
        if not generic_filter_pass:
            failures.append("generic_filter_failed")
        if not line_in_sand_consistent:
            failures.append("line_in_sand_inconsistent")

        return FilterResult(
            brand_seed_present=brand_seed_present,
            foundation_energy_present=foundation_energy_present,
            generic_filter_pass=generic_filter_pass,
            line_in_sand_consistent=line_in_sand_consistent,
            passed=len(failures) == 0,
            failures=failures,
        )

    def _generate_with_filter(self, content: Dict[str, Any], session: Dict[str, Any], generator) -> Dict[str, Any]:
        attempt = 0
        accepted = dict(content)
        result = self._brand_filter(accepted, session)

        # Max 2 re-generation attempts if any filter check fails.
        while not result.passed and attempt < 2:
            accepted = generator(session=session, prior=accepted, filter_result=result)
            result = self._brand_filter(accepted, session)
            attempt += 1

        accepted["brand_filter_result"] = result.model_dump()
        return accepted

    def _generate_social_one(self, session: Dict[str, Any], trend_context: str) -> Dict[str, Any]:
        line_in_sand = self._session_value(session, "line_in_sand", "")
        prompt = (
            "Create one Social Point of View idea in JSON with keys: "
            "angle, hook_line, platform_suggestion, brand_seed_connection. "
            "Use trend context and filter through the line in the sand. "
            "No generic offer language.\n\n"
            f"Trend context:\n{trend_context}\n\n"
            f"Line in the sand (Q11): {line_in_sand}\n"
            f"Brand seed: {self._session_value(session, 'brand_seed', '')}\n"
            f"Three-word foundation: {self._foundation_words(session)}\n"
        )
        return self._chat_json(prompt)

    def _regenerate_social_one(self, session: Dict[str, Any], prior: Dict[str, Any], filter_result: FilterResult) -> Dict[str, Any]:
        prompt = (
            "Rewrite this Social Point of View JSON to pass all brand filters. "
            "Keep keys: angle, hook_line, platform_suggestion, brand_seed_connection.\n"
            f"Failed checks: {filter_result.failures}\n"
            f"Current content: {json.dumps(prior, ensure_ascii=True)}\n"
            f"Brand seed: {self._session_value(session, 'brand_seed', '')}\n"
            f"Three-word foundation: {self._foundation_words(session)}\n"
            f"Line in the sand: {self._session_value(session, 'line_in_sand', '')}\n"
        )
        return self._chat_json(prompt)

    def _generate_campaign(self, session: Dict[str, Any]) -> Dict[str, Any]:
        wom_trigger = self._session_value(session, "wom_trigger", "")
        prompt = (
            "Create one monthly campaign concept in JSON with keys: "
            "campaign_name, core_message, call_to_action, what_it_protects. "
            "Protect sexy vision, reference WOM trigger, avoid generic offer language.\n\n"
            f"WOM Trigger (Q22): {wom_trigger}\n"
            f"Line in the sand: {self._session_value(session, 'line_in_sand', '')}\n"
            f"Brand seed: {self._session_value(session, 'brand_seed', '')}\n"
            f"Three-word foundation: {self._foundation_words(session)}\n"
        )
        return self._chat_json(prompt)

    def _regenerate_campaign(self, session: Dict[str, Any], prior: Dict[str, Any], filter_result: FilterResult) -> Dict[str, Any]:
        prompt = (
            "Rewrite this campaign JSON to pass all brand filters. "
            "Keep keys: campaign_name, core_message, call_to_action, what_it_protects.\n"
            f"Failed checks: {filter_result.failures}\n"
            f"Current content: {json.dumps(prior, ensure_ascii=True)}\n"
            f"WOM Trigger: {self._session_value(session, 'wom_trigger', '')}\n"
            f"Brand seed: {self._session_value(session, 'brand_seed', '')}\n"
            f"Three-word foundation: {self._foundation_words(session)}\n"
            f"Line in the sand: {self._session_value(session, 'line_in_sand', '')}\n"
        )
        return self._chat_json(prompt)

    def _generate_outreach_one(self, session: Dict[str, Any]) -> Dict[str, Any]:
        wom_trigger = self._session_value(session, "wom_trigger", "")
        fear = self._ideal_client_fear(session)
        prompt = (
            "Create one trust-building outreach template in JSON with keys: "
            "outreach_type, subject_line, opening, trust_signal, cta. "
            "Base it on WOM trigger and ideal client fear.\n\n"
            f"WOM Trigger (Q22): {wom_trigger}\n"
            f"Ideal Client Fear (Q16): {fear}\n"
            f"Brand seed: {self._session_value(session, 'brand_seed', '')}\n"
            f"Three-word foundation: {self._foundation_words(session)}\n"
            f"Line in the sand: {self._session_value(session, 'line_in_sand', '')}\n"
        )
        return self._chat_json(prompt)

    def _regenerate_outreach_one(self, session: Dict[str, Any], prior: Dict[str, Any], filter_result: FilterResult) -> Dict[str, Any]:
        prompt = (
            "Rewrite this outreach JSON to pass all brand filters. "
            "Keep keys: outreach_type, subject_line, opening, trust_signal, cta.\n"
            f"Failed checks: {filter_result.failures}\n"
            f"Current content: {json.dumps(prior, ensure_ascii=True)}\n"
            f"WOM Trigger: {self._session_value(session, 'wom_trigger', '')}\n"
            f"Ideal Client Fear: {self._ideal_client_fear(session)}\n"
            f"Brand seed: {self._session_value(session, 'brand_seed', '')}\n"
            f"Three-word foundation: {self._foundation_words(session)}\n"
            f"Line in the sand: {self._session_value(session, 'line_in_sand', '')}\n"
        )
        return self._chat_json(prompt)

    def _chat_json(self, user_prompt: str) -> Dict[str, Any]:
        completion = self.client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o"),
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an elite brand strategist. Return valid JSON only. "
                        "Never use generic offer language."
                    ),
                },
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=700,
        )
        raw = (completion.choices[0].message.content or "{}").strip()
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            raise ValueError("Model did not return a JSON object")
        return parsed

    def _load_session(self, session_id: str) -> Dict[str, Any]:
        body = {
            "size": 1,
            "query": {"bool": {"filter": [{"term": {"session_id": session_id}}]}},
            "sort": [{"updated_at": {"order": "desc", "unmapped_type": "date"}}],
        }
        resp = self.es.search(index=self.SESSION_INDEX, body=body)
        hits = resp.get("hits", {}).get("hits", [])
        if not hits:
            raise ValueError(f"Session not found: {session_id}")
        return hits[0].get("_source", {})

    @staticmethod
    def _session_value(session: Dict[str, Any], key: str, default: str) -> str:
        value = session.get(key, default)
        if value is None:
            return default
        return str(value)

    def _foundation_words(self, session: Dict[str, Any]) -> List[str]:
        foundation = dict(session.get("three_word_foundation", {}) or {})
        words = [
            str(foundation.get("value1", "") or "").strip(),
            str(foundation.get("value2", "") or "").strip(),
            str(foundation.get("value3", "") or "").strip(),
        ]
        return [w for w in words if w]

    def _ideal_client_fear(self, session: Dict[str, Any]) -> str:
        for ans in session.get("all_answers", []) or []:
            if str(ans.get("q_id", "")).upper() == "Q16":
                return str(ans.get("raw_answer", "") or "").strip()
        return ""

    def _trend_context(self) -> str:
        env_val = os.getenv("BRANDGODFATHER_TREND_CONTEXT", "").strip()
        if env_val:
            return env_val
        now = datetime.now(timezone.utc).strftime("%Y-%m")
        return (
            f"Current period {now}. Focus on trust-first thought leadership, founder POV posts, "
            "anti-generic positioning, and authority through specificity."
        )

    @staticmethod
    def _generic_filter_pass(text: str) -> bool:
        lower = (text or "").lower()
        terms = list(VENDOR_PHRASES) + list(GENERIC_BUZZWORDS) + list(CLICHE_PHRASES)
        return not any(term in lower for term in terms)

    @staticmethod
    def eligible_completed_session(source: Dict[str, Any]) -> bool:
        answers = source.get("all_answers", []) or []
        for item in answers:
            if str(item.get("q_id", "")).upper() == "Q30" and str(item.get("status", "")).upper() == "PASS":
                return True
        return False

    def _build_client(self) -> AzureOpenAI:
        endpoint = _normalize_azure_endpoint(os.getenv("AZURE_OPENAI_ENDPOINT", ""))
        api_key = os.getenv("AZURE_OPENAI_API_KEY", "")
        if not endpoint or not api_key:
            raise ValueError("Missing AZURE_OPENAI_ENDPOINT or AZURE_OPENAI_API_KEY")
        return AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21"),
        )
