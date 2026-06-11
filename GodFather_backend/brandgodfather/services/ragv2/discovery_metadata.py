from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Tuple

import requests
from django.conf import settings
from openai import AzureOpenAI

from brandgodfather.services.session_manager import SessionManager

logger = logging.getLogger(__name__)

BRAND_TYPES = [
    "Luxury",
    "Premium",
    "Aspirational",
    "Disruptive",
    "Authority",
    "Community",
    "Lifestyle",
    "Value",
    "Innovator",
    "Craft",
    "Rebel",
    "Guide",
]

BRAND_ARCHETYPES = [
    "Creator",
    "Explorer",
    "Sage",
    "Hero",
    "Rebel",
    "Caregiver",
    "Entertainer",
    "Visionary",
]

CUSTOMER_ARCHETYPES = [
    "Achiever",
    "Dreamer",
    "Builder",
    "Adventurer",
    "Innovator",
    "Learner",
    "Protector",
    "Status Seeker",
]

BRAND_PERSONA_EXAMPLES = [
    "Apple | Imagination. Design. Innovation.",
    "Aston Martin | Power. Beauty. Soul.",
    "Virgin Atlantic | Rebellious. Champion. Maverick.",
    "New Musical Express | Hip. Young. Gunslingers.",
    "Sex Pistols | Rude. Obnoxious. Anarchists.",
]

BOUNDARY_Q = {4, 9, 19, 29, 30}


def _question_number(q_id: str) -> int:
    m = re.search(r"(\d+)", str(q_id or ""))
    if not m:
        return 1
    return max(1, min(30, int(m.group(1))))


def _phase_segment(q_num: int) -> str:
    if q_num <= 4:
        return "profiling"
    if q_num <= 9:
        return "revealing_themes"
    if q_num <= 19:
        return "identifying_patterns"
    if q_num <= 29:
        return "strategic_opportunities"
    return "synthesis"


def _score_band(score: float) -> str:
    s = max(0.0, min(10.0, float(score or 0.0)))
    if s < 2.0:
        return "weak"
    if s < 4.0:
        return "generic"
    if s < 6.0:
        return "vendor"
    return "strong"


def _fallback_top3(items: List[str], base: float = 3.0) -> List[Dict[str, Any]]:
    out = []
    for idx, name in enumerate(items[:3]):
        conf = round(base - (idx * 0.4), 2)
        out.append({"name": name, "confidence": conf, "band": _score_band(conf)})
    return out


def _normalize_choice(value: str, allowed: List[str], default: str) -> str:
    val = str(value or "").strip().lower()
    for item in allowed:
        if item.lower() == val:
            return item
    for item in allowed:
        if item.lower() in val or val in item.lower():
            return item
    return default


def _fetch_live_questions() -> Dict[str, Any]:
    url = getattr(settings, "PHASE_QUESTIONS_API_URL", "http://localhost:4001/phase-questions/")
    try:
        resp = requests.get(url, timeout=8)
        resp.raise_for_status()
        payload = resp.json()
        if isinstance(payload, dict):
            if isinstance(payload.get("results"), list):
                questions = payload["results"]
            elif isinstance(payload.get("data"), list):
                questions = payload["data"]
            elif isinstance(payload.get("questions"), list):
                questions = payload["questions"]
            else:
                questions = []
        elif isinstance(payload, list):
            questions = payload
        else:
            questions = []

        return {
            "source_url": url,
            "source": "live_4001",
            "ok": True,
            "count": len(questions),
            "questions": questions,
        }
    except Exception as exc:
        logger.warning("Live questions fetch failed: %s", exc)
        return {
            "source_url": url,
            "source": "live_4001",
            "ok": False,
            "count": 0,
            "questions": [],
            "error": str(exc),
        }


def _llm_json(system_prompt: str, user_prompt: str, default: Dict[str, Any]) -> Dict[str, Any]:
    endpoint = (getattr(settings, "LLM_API_ENDPOINT", "") or "").strip()
    key = (getattr(settings, "LLM_API_KEY", "") or "").strip()
    model = (getattr(settings, "LLM_MODEL_NAME", "") or "").strip()

    try:
        if endpoint and key and model:
            body = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.3,
                "max_tokens": 1200,
            }
            headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
            data = requests.post(endpoint, headers=headers, json=body, timeout=35).json()
            content = ((data.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
            content = str(content).replace("```json", "").replace("```", "").strip()
            return json.loads(content)
    except Exception:
        logger.exception("Generic LLM JSON call failed")

    try:
        az_endpoint = (getattr(settings, "AZURE_OPENAI_ENDPOINT", "") or "").strip()
        az_key = (getattr(settings, "AZURE_OPENAI_API_KEY", "") or "").strip()
        deployment = (getattr(settings, "AZURE_OPENAI_DEPLOYMENT_NAME", "") or "gpt-4o").strip()
        if az_endpoint and az_key:
            client = AzureOpenAI(
                azure_endpoint=az_endpoint,
                api_key=az_key,
                api_version=getattr(settings, "AZURE_OPENAI_API_VERSION", "2024-02-01"),
            )
            resp = client.chat.completions.create(
                model=deployment,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                max_tokens=1200,
            )
            content = ((resp.model_dump().get("choices") or [{}])[0].get("message") or {}).get("content") or ""
            content = str(content).replace("```json", "").replace("```", "").strip()
            return json.loads(content)
    except Exception:
        logger.exception("Azure LLM JSON call failed")

    return default


def _default_metadata(q_num: int, boundary: bool, live_q: Dict[str, Any]) -> Dict[str, Any]:
    low = 2.0
    arche_brand = _fallback_top3(BRAND_ARCHETYPES, 2.6)
    arche_customer = _fallback_top3(CUSTOMER_ARCHETYPES, 2.6)
    return {
        "question_number": q_num,
        "phase_1_segment": _phase_segment(q_num),
        "boundary_checkpoint": boundary,
        "live_questions": {
            "source": live_q.get("source", "live_4001"),
            "source_url": live_q.get("source_url"),
            "fetch_ok": bool(live_q.get("ok")),
            "count": int(live_q.get("count") or 0),
        },
        "brand_type": {"name": "Aspirational", "confidence": low, "band": _score_band(low)},
        "vision": {"value": "Provisional: vision needs more depth.", "confidence": low, "band": _score_band(low), "provisional": q_num < 30},
        "mission": {"value": "Provisional: mission needs more specificity.", "confidence": low, "band": _score_band(low), "provisional": q_num < 30},
        "brand_promise": {"value": "Provisional: promise is still forming.", "confidence": low, "band": _score_band(low), "provisional": q_num < 30},
        "brand_story": {"value": "Provisional: story arc is still emerging.", "confidence": low, "band": _score_band(low), "provisional": q_num < 30},
        "customer_profiles": {
            "demographics": {
                "age": "unknown",
                "gender": "unknown",
                "income": "unknown",
                "occupation": "unknown",
                "location": "unknown",
            },
            "psychographics": {
                "values": [],
                "beliefs": [],
                "aspirations": [],
                "frustrations": [],
                "motivations": [],
                "emotional_drivers": [],
            },
            "confidence": low,
            "band": _score_band(low),
            "provisional": q_num < 30,
        },
        "strategic_opportunities": {"items": [], "confidence": low, "band": _score_band(low), "provisional": q_num < 30},
        "campaign_recommendations": {"items": [], "confidence": low, "band": _score_band(low), "provisional": q_num < 30},
        "archetypes": {
            "brand": arche_brand,
            "customer": arche_customer,
        },
        "three_word_persona": {
            "value": [],
            "examples": BRAND_PERSONA_EXAMPLES,
            "confidence": low,
            "band": _score_band(low),
        },
        "orb_quote": {
            "enabled": boundary,
            "quote": "",
            "confidence": low,
            "band": _score_band(low),
        },
        "mandatory": {
            "vision": True,
            "mission": True,
            "customer_profiles": True,
        },
    }


def build_discovery_metadata(session_id: str, q_id: str, raw_answer: str) -> Dict[str, Any]:
    q_num = _question_number(q_id)
    boundary = q_num in BOUNDARY_Q
    live_q = _fetch_live_questions()
    data = _default_metadata(q_num, boundary, live_q)

    manager = SessionManager()
    session = None
    context: Dict[str, Any] = {}
    answers: List[Dict[str, Any]] = []
    try:
        session = manager.get_session(session_id)
        context = session.context_data if session else {}
        answers = list((session.all_answers if session else []) or [])
    except Exception as exc:
        logger.warning("Session read for discovery metadata failed: %s", exc)
    answers.append({"q_id": q_id, "raw_answer": raw_answer})

    answers_blob = "\n".join(
        f"{item.get('q_id', '')}: {item.get('raw_answer', '')}" for item in answers[-30:]
    )

    system_prompt = (
        "You are a strict brand discovery metadata engine. Return JSON only with no markdown. "
        "Use only provided taxonomy constraints."
    )
    user_prompt = f"""
Question number: {q_num}
Boundary checkpoint: {boundary}
Brand type must be one of: {BRAND_TYPES}
Brand archetypes candidates: {BRAND_ARCHETYPES}
Customer archetypes candidates: {CUSTOMER_ARCHETYPES}

Context data: {json.dumps(context, ensure_ascii=False)}
Answers: {answers_blob}

Return JSON with keys:
- brand_type {{name, confidence_0_10}}
- vision {{value, confidence_0_10}}
- mission {{value, confidence_0_10}}
- brand_promise {{value, confidence_0_10}}
- brand_story {{value, confidence_0_10}}
- customer_profiles {{ demographics{{age, gender, income, occupation, location}}, psychographics{{values, beliefs, aspirations, frustrations, motivations, emotional_drivers}}, confidence_0_10 }}
- strategic_opportunities {{items, confidence_0_10}}
- campaign_recommendations {{items, confidence_0_10}}
- archetypes {{brand:[{{name, confidence_0_10}}], customer:[{{name, confidence_0_10}}]}}
- three_word_persona {{value:[word1, word2, word3], confidence_0_10}}
- orb_quote {{quote, confidence_0_10}}
""".strip()

    parsed = _llm_json(system_prompt, user_prompt, default={})

    if parsed:
        bt = _normalize_choice((parsed.get("brand_type") or {}).get("name", ""), BRAND_TYPES, "Aspirational")
        bt_conf = float((parsed.get("brand_type") or {}).get("confidence_0_10", 2.0) or 2.0)
        data["brand_type"] = {"name": bt, "confidence": round(max(0.0, min(10.0, bt_conf)), 2), "band": _score_band(bt_conf)}

        for key in ["vision", "mission", "brand_promise", "brand_story"]:
            obj = parsed.get(key) or {}
            conf = float(obj.get("confidence_0_10", 2.0) or 2.0)
            data[key] = {
                "value": str(obj.get("value") or data[key]["value"]).strip(),
                "confidence": round(max(0.0, min(10.0, conf)), 2),
                "band": _score_band(conf),
                "provisional": q_num < 30,
            }

        cp = parsed.get("customer_profiles") or {}
        cp_conf = float(cp.get("confidence_0_10", 2.0) or 2.0)
        data["customer_profiles"] = {
            "demographics": (cp.get("demographics") or data["customer_profiles"]["demographics"]),
            "psychographics": (cp.get("psychographics") or data["customer_profiles"]["psychographics"]),
            "confidence": round(max(0.0, min(10.0, cp_conf)), 2),
            "band": _score_band(cp_conf),
            "provisional": q_num < 30,
        }

        for key in ["strategic_opportunities", "campaign_recommendations"]:
            obj = parsed.get(key) or {}
            conf = float(obj.get("confidence_0_10", 2.0) or 2.0)
            items = obj.get("items") if isinstance(obj.get("items"), list) else []
            data[key] = {
                "items": [str(i).strip() for i in items if str(i).strip()],
                "confidence": round(max(0.0, min(10.0, conf)), 2),
                "band": _score_band(conf),
                "provisional": q_num < 30,
            }

        arc = parsed.get("archetypes") or {}
        brand_arc = arc.get("brand") if isinstance(arc.get("brand"), list) else []
        cust_arc = arc.get("customer") if isinstance(arc.get("customer"), list) else []

        def norm_arc(items: List[Dict[str, Any]], allowed: List[str], fallback: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            out: List[Dict[str, Any]] = []
            for item in items[:6]:
                if not isinstance(item, dict):
                    continue
                name = _normalize_choice(item.get("name", ""), allowed, "")
                if not name:
                    continue
                conf = float(item.get("confidence_0_10", 2.0) or 2.0)
                out.append({
                    "name": name,
                    "confidence": round(max(0.0, min(10.0, conf)), 2),
                    "band": _score_band(conf),
                })
            if not out:
                return fallback
            out.sort(key=lambda x: x["confidence"], reverse=True)
            return out[:3]

        data["archetypes"]["brand"] = norm_arc(brand_arc, BRAND_ARCHETYPES, _fallback_top3(BRAND_ARCHETYPES, 2.6))
        data["archetypes"]["customer"] = norm_arc(cust_arc, CUSTOMER_ARCHETYPES, _fallback_top3(CUSTOMER_ARCHETYPES, 2.6))

        twp = parsed.get("three_word_persona") or {}
        twp_val = twp.get("value") if isinstance(twp.get("value"), list) else []
        twp_val = [str(v).strip() for v in twp_val if str(v).strip()][:3]
        twp_conf = float(twp.get("confidence_0_10", 2.0) or 2.0)
        data["three_word_persona"] = {
            "value": twp_val,
            "examples": BRAND_PERSONA_EXAMPLES,
            "confidence": round(max(0.0, min(10.0, twp_conf)), 2),
            "band": _score_band(twp_conf),
        }

        quote_obj = parsed.get("orb_quote") or {}
        quote_conf = float(quote_obj.get("confidence_0_10", 2.0) or 2.0)
        data["orb_quote"] = {
            "enabled": boundary,
            "quote": str(quote_obj.get("quote") or "").strip() if boundary else "",
            "confidence": round(max(0.0, min(10.0, quote_conf)), 2),
            "band": _score_band(quote_conf),
        }

    if session:
        try:
            manager.update_session(session_id, {"discovery_metadata_latest": data})
        except Exception as exc:
            logger.warning("Session write for discovery metadata failed: %s", exc)

    return data
