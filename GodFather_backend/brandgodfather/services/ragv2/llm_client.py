from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict

import requests
from django.conf import settings
from openai import AzureOpenAI

logger = logging.getLogger(__name__)

_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE | re.MULTILINE)


def _strip_fences(text: str) -> str:
    return _FENCE_RE.sub("", (text or "")).strip()


def _safe_default() -> Dict[str, Any]:
    return {
        "gate_status": "REJECT",
        "ai_reply": "Let us go deeper on that. Can you tell me more about what that means to you?",
        "extracted_data": {
            "brand_seed": None,
            "tension": None,
            "key_phrase": "",
            "thread_addition": None,
        },
        "pressure_used": 1,
        "challenge_type": "parse_fallback",
    }


def _extract_content(payload: Dict[str, Any]) -> str:
    choices = payload.get("choices") or []
    if choices:
        msg = choices[0].get("message") or {}
        content = msg.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return "".join(part.get("text", "") for part in content if isinstance(part, dict))
    return str(payload.get("content") or "")


def _call_via_generic_endpoint(system_prompt: str, user_prompt: str, max_tokens: int, temperature: float) -> Dict[str, Any]:
    endpoint = getattr(settings, "LLM_API_ENDPOINT", "")
    api_key = getattr(settings, "LLM_API_KEY", "")
    model_name = getattr(settings, "LLM_MODEL_NAME", "")
    if not endpoint or not api_key or not model_name:
        raise RuntimeError("LLM_API_* settings are incomplete")

    body = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    resp = requests.post(endpoint, headers=headers, json=body, timeout=60)
    resp.raise_for_status()
    return resp.json()


def _call_via_azure(system_prompt: str, user_prompt: str, max_tokens: int, temperature: float) -> Dict[str, Any]:
    endpoint = (getattr(settings, "AZURE_OPENAI_ENDPOINT", "") or "").strip()
    api_key = (getattr(settings, "AZURE_OPENAI_API_KEY", "") or "").strip()
    deployment = (getattr(settings, "AZURE_OPENAI_DEPLOYMENT_NAME", "") or "gpt-4o").strip()
    if not endpoint or not api_key:
        raise RuntimeError("Azure OpenAI settings are incomplete")

    client = AzureOpenAI(
        azure_endpoint=endpoint,
        api_key=api_key,
        api_version=getattr(settings, "AZURE_OPENAI_API_VERSION", "2024-02-01"),
    )
    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return response.model_dump()


def call_llm(system_prompt: str, user_prompt: str) -> Dict[str, Any]:
    max_tokens = int(getattr(settings, "LLM_MAX_TOKENS", 1000) or 1000)

    try:
        try:
            payload = _call_via_generic_endpoint(system_prompt, user_prompt, max_tokens=max_tokens, temperature=0.4)
        except Exception:
            payload = _call_via_azure(system_prompt, user_prompt, max_tokens=max_tokens, temperature=0.4)

        content = _strip_fences(_extract_content(payload))
        return json.loads(content)
    except Exception:
        logger.exception("call_llm failed; returning fallback")
        return _safe_default()


def call_llm_for_brandbook(system_prompt: str, user_prompt: str) -> Dict[str, Any]:
    try:
        try:
            payload = _call_via_generic_endpoint(system_prompt, user_prompt, max_tokens=3000, temperature=0.6)
        except Exception:
            payload = _call_via_azure(system_prompt, user_prompt, max_tokens=3000, temperature=0.6)

        content = _strip_fences(_extract_content(payload))
        return json.loads(content)
    except Exception:
        logger.exception("call_llm_for_brandbook failed")
        return {"error": True, "raw": ""}
