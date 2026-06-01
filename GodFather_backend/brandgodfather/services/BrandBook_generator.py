from __future__ import annotations

import json
import os
import re
from string import Template
from typing import Any, Dict, List, Optional

from elasticsearch_dsl import connections
from openai import AzureOpenAI
from pydantic import BaseModel

from document.utils.embedding_service import _normalize_azure_endpoint
from brandgodfather.documents import BRANDGODFATHER_NODE_2_ALIAS
from brandgodfather.services.prosody_classifier import VENDOR_PHRASES

GENERIC_BUZZWORDS = [
    "innovative",
    "passionate",
    "results-driven",
    "cutting-edge",
    "world-class",
    "synergy",
    "leverage",
    "holistic",
    "seamless",
    "empower",
    "disruptive",
    "transformative",
    "best-in-class",
]

CLICHE_PHRASES = [
    "at the end of the day",
    "game changer",
    "move the needle",
    "think outside the box",
    "value proposition",
    "low-hanging fruit",
]

SECTION_SOURCES = {
    "The Origin Spark": ["Q1"],
    "The Edge": ["Q6", "Q7"],
    "The Big Idea": ["Q8", "Q9", "Q10"],
    "The Foundation": ["Q12", "Q13", "Q14"],
    "The Truth": ["Q15", "Q16", "Q17"],
    "The Difference": ["Q18", "Q19", "Q20"],
    "The Promise": ["Q21", "Q22"],
    "The Vision": ["Q23", "Q24"],
    "The Line in the Sand": ["Q11"],
    "The Authority Statement": ["Q30"],
}


class FilterResult(BaseModel):
    passed: bool
    flagged_terms: List[str]
    flagged_sections: List[str]


class BrandBookResult(BaseModel):
    BrandBook_sections: Dict[str, str]
    brand_kit: Dict[str, Any]
    generic_filter_passes: int
    final_score: float


class BrandBook:
    SESSION_INDEX = "brandgodfather_sessions"

    def __init__(self) -> None:
        self.es = connections.get_connection(alias=BRANDGODFATHER_NODE_2_ALIAS)
        self.client = self._build_client()
        self._filter_section_context = ""

    def generate(self, session_id: str) -> BrandBookResult:
        session_doc_id, session = self._load_session(session_id)
        if not session_doc_id:
            raise ValueError(f"Session not found: {session_id}")

        answers_by_q = self._answers_by_q(session.get("all_answers", []) or [])
        brand_seed = str(session.get("brand_seed", "") or "").strip()
        thread_index = dict(session.get("thread_index", {}) or {})

        sections: Dict[str, str] = {}
        generic_filter_passes = 0
        section_flags: Dict[str, List[str]] = {}

        for section_name, q_ids in SECTION_SOURCES.items():
            relevant_answers = {q_id: answers_by_q.get(q_id, "") for q_id in q_ids}
            section_text = self._generate_section(
                section_name=section_name,
                all_answers=answers_by_q,
                relevant_answers=relevant_answers,
                brand_seed=brand_seed,
                thread_index=thread_index,
            )

            attempts = 0
            while attempts < 3:
                self._filter_section_context = section_name
                filter_result = self._run_generic_filter(section_text)
                if filter_result.passed:
                    generic_filter_passes += 1
                    break
                section_flags[section_name] = filter_result.flagged_terms
                section_text = self._regenerate_section(
                    section_name=section_name,
                    flagged_text=section_text,
                    brand_seed=brand_seed,
                )
                attempts += 1

            sections[section_name] = section_text.strip()

        brand_kit = self._build_brand_kit(session=session, answers_by_q=answers_by_q, sections=sections)
        final_score = self._compute_final_score(sections=sections, generic_filter_passes=generic_filter_passes)

        result = BrandBookResult(
            BrandBook_sections=sections,
            brand_kit=brand_kit,
            generic_filter_passes=generic_filter_passes,
            final_score=final_score,
        )

        self.es.update(
            index=self.SESSION_INDEX,
            id=session_doc_id,
            body={
                "doc": {
                    "brandbook_result": result.model_dump(),
                    "output_mode": "brandbook",
                }
            },
            refresh=True,
        )
        return result

    def _generate_section(
        self,
        section_name: str,
        all_answers: Dict[str, str],
        relevant_answers: Dict[str, str],
        brand_seed: str,
        thread_index: Dict[str, Any],
    ) -> str:
        prompt = Template(
            "Generate the BrandBook section '$section_name'.\n"
            "Use only the user's answers, Brand Seed, and thread index.\n"
            "You must synthesize from the full interview, while weighting the section-relevant answers most heavily.\n"
            "Write with authority, specificity, and zero generic marketing language.\n\n"
            "Brand Seed: $brand_seed\n"
            "Full Interview Answers:\n$all_answers\n\n"
            "Relevant Answers:\n$relevant_answers\n\n"
            "Thread Index:\n$thread_index\n\n"
            "Output only the section text."
        ).safe_substitute(
            {
                "section_name": section_name,
                "brand_seed": brand_seed or "unknown",
                "all_answers": json.dumps(all_answers, ensure_ascii=True, indent=2),
                "relevant_answers": json.dumps(relevant_answers, ensure_ascii=True, indent=2),
                "thread_index": json.dumps(thread_index, ensure_ascii=True, indent=2),
            }
        )
        return self._chat(prompt)

    def _run_generic_filter(self, text: str) -> FilterResult:
        lower = (text or "").lower()
        flagged_terms: List[str] = []

        for term in VENDOR_PHRASES:
            if term in lower:
                flagged_terms.append(term)
        for term in GENERIC_BUZZWORDS:
            if term in lower:
                flagged_terms.append(term)
        for term in CLICHE_PHRASES:
            if term in lower:
                flagged_terms.append(term)

        deduped = []
        seen = set()
        for item in flagged_terms:
            if item not in seen:
                seen.add(item)
                deduped.append(item)

        flagged_sections = [self._filter_section_context] if deduped and self._filter_section_context else []

        return FilterResult(
            passed=len(deduped) == 0,
            flagged_terms=deduped,
            flagged_sections=flagged_sections,
        )

    def _regenerate_section(self, section_name: str, flagged_text: str, brand_seed: str) -> str:
        prompt = Template(
            "Rewrite this BrandBook section only: $section_name\n\n"
            "Current text:\n$flagged_text\n\n"
            "Rewrite this section using ONLY the user's own words and the Brand Seed: $brand_seed.\n"
            "Remove all generic language.\n"
            "Output only the rewritten section text."
        ).safe_substitute(
            {
                "section_name": section_name,
                "flagged_text": flagged_text,
                "brand_seed": brand_seed or "unknown",
            }
        )
        return self._chat(prompt)

    def _build_brand_kit(
        self,
        session: Dict[str, Any],
        answers_by_q: Dict[str, str],
        sections: Dict[str, str],
    ) -> Dict[str, Any]:
        three_word_foundation = session.get("three_word_foundation") or {}
        foundation_list = [
            str(three_word_foundation.get("value1", "") or "").strip(),
            str(three_word_foundation.get("value2", "") or "").strip(),
            str(three_word_foundation.get("value3", "") or "").strip(),
        ]
        foundation_list = [item for item in foundation_list if item]
        if not foundation_list:
            foundation_list = self._extract_three_words(sections.get("The Foundation", ""))

        return {
            "brand_seed": str(session.get("brand_seed", "") or "").strip(),
            "three_word_foundation": foundation_list[:3],
            "brand_promise": str(session.get("brand_promise", "") or "").strip() or sections.get("The Promise", ""),
            "line_in_sand": str(session.get("line_in_sand", "") or "").strip() or sections.get("The Line in the Sand", ""),
            "wom_trigger": str(session.get("wom_trigger", "") or "").strip() or answers_by_q.get("Q22", ""),
            "ideal_client_profile": answers_by_q.get("Q15", ""),
            "brand_type": self._infer_brand_type(session=session, sections=sections),
        }

    def _compute_final_score(self, sections: Dict[str, str], generic_filter_passes: int) -> float:
        completion_ratio = sum(1 for text in sections.values() if text.strip()) / max(len(sections), 1)
        filter_ratio = generic_filter_passes / max(len(sections), 1)
        score = (completion_ratio * 0.6) + (filter_ratio * 0.4)
        return round(max(0.0, min(1.0, score)), 4)

    def _answers_by_q(self, all_answers: List[Dict[str, Any]]) -> Dict[str, str]:
        out: Dict[str, str] = {}
        for row in all_answers:
            q_id = str(row.get("q_id", "") or "").upper()
            answer = str(row.get("raw_answer", "") or "").strip()
            if q_id and answer:
                out[q_id] = answer
        return out

    def _load_session(self, session_id: str):
        body = {
            "size": 1,
            "query": {"bool": {"filter": [{"term": {"session_id": session_id}}]}},
        }
        resp = self.es.search(index=self.SESSION_INDEX, body=body)
        hits = resp.get("hits", {}).get("hits", [])
        if not hits:
            return None, {}
        hit = hits[0]
        return hit.get("_id"), hit.get("_source", {})

    def _chat(self, user_prompt: str) -> str:
        completion = self.client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o"),
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert brand strategist. Write in precise, non-generic language using only the user's source material.",
                },
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=500,
        )
        return (completion.choices[0].message.content or "").strip()

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

    @staticmethod
    def _extract_three_words(text: str) -> List[str]:
        words = re.findall(r"[A-Za-z][A-Za-z-]+", text)
        unique: List[str] = []
        for word in words:
            w = word.lower()
            if w not in unique:
                unique.append(w)
            if len(unique) == 3:
                break
        return unique

    @staticmethod
    def _infer_brand_type(session: Dict[str, Any], sections: Dict[str, str]) -> str:
        shadow = dict(session.get("shadow_profile", {}) or {})
        existing = str(shadow.get("self_image", "") or "").strip()
        if existing and existing != "unknown":
            return existing
        edge = (sections.get("The Edge", "") + " " + sections.get("The Big Idea", "")).lower()
        archetypes = [
            "sage",
            "rebel",
            "hero",
            "creator",
            "caregiver",
            "ruler",
            "jester",
            "innocent",
            "everyman",
            "explorer",
            "magician",
            "lover",
        ]
        for item in archetypes:
            if item in edge:
                return item
        return "unknown"
