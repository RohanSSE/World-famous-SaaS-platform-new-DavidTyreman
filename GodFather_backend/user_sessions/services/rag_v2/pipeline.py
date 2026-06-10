from __future__ import annotations

from typing import Any, Dict, Generator, Optional

from user_sessions.services import rag_service
from user_sessions.services.rag_dev_config import get_rag_dev_config
from user_sessions.services.rag_phase_artifacts import (
    get_phase_artifact_map,
    resolve_phase_from_session,
    save_phase_artifact,
)

_PHASE_DEFAULTS = {
    "phase_1": (
        "Phase 1 Discovery goal: extract audience, tension, category reality, and key constraints "
        "with evidence-backed clarity."
    ),
    "phase_2": (
        "Phase 2 Brand Book and Playbook goal: codify brand DNA, manifesto alignment, voice, and "
        "positioning rules that are executable."
    ),
    "phase_3": (
        "Phase 3 Brand Promotion goal: produce channel-ready, differentiated promotion strategy "
        "anchored in trust and manifesto consistency."
    ),
    "phase_4": (
        "Phase 4 Strategic Guidance and Content Creation goal: deliver high-confidence strategic "
        "guidance and concrete content outputs with explicit rationale."
    ),
}


def _phase_prompt(config: Dict[str, Any], phase_key: str) -> str:
    stored = str(config.get(f"{phase_key}_master_prompt") or "").strip()
    return stored or _PHASE_DEFAULTS[phase_key]


def resolve_phase(user_query: str, session=None) -> str:
    if session is not None:
        return resolve_phase_from_session(session)

    text = (user_query or "").lower()

    if any(token in text for token in ("brand book", "brandbook", "playbook", "brand dna", "voice")):
        return "phase_2"
    if any(token in text for token in ("promotion", "campaign", "launch", "social", "distribution")):
        return "phase_3"
    if any(token in text for token in ("strategic guidance", "strategy", "content plan", "content creation")):
        return "phase_4"

    # Session stage fallback can be upgraded later; current implementation stays deterministic.
    return "phase_1"


def _merge_injection(prompt_injection: Optional[Dict[str, str]], config: Dict[str, Any], phase_key: str) -> Dict[str, str]:
    base = dict(prompt_injection or {})

    existing_pre = str(base.get("pre_retrieval_prompt") or "").strip()
    existing_system = str(base.get("system_injection_prompt") or "").strip()

    phase_goal = _phase_prompt(config, phase_key)

    pre_parts = [
        f"RAGv2 {phase_key.replace('_', ' ').title()} focus: {phase_goal}",
        existing_pre,
    ]
    base["pre_retrieval_prompt"] = "\n\n".join(part for part in pre_parts if part).strip()

    system_parts = [
        f"RAGv2 {phase_key.replace('_', ' ').title()} Master Prompt:\n{phase_goal}",
        existing_system,
    ]
    base["system_injection_prompt"] = "\n\n".join(part for part in system_parts if part).strip()
    return base


def _artifact_payload(phase_key: str, result: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "completed": True,
        "phase_key": phase_key,
        "answer": str(result.get("answer") or "")[:6000],
        "sources": result.get("sources") or [],
        "retrieval_confidence": result.get("retrieval_confidence") or {},
        "reasoning_path": result.get("reasoning_path") or {},
    }


def retrieve_context(user_query: str, **kwargs):
    config = get_rag_dev_config()
    session = kwargs.get("session")
    phase_key = resolve_phase(user_query, session)
    kwargs["prompt_injection"] = _merge_injection(kwargs.get("prompt_injection"), config, phase_key)

    context = rag_service.retrieve_context(user_query, **kwargs)
    if isinstance(context, dict):
        context["rag_phase"] = phase_key
        context["active_pipeline"] = "rag_v2"
        if session is not None:
            context["phase_artifacts"] = get_phase_artifact_map(session.id)
    return context


def generate_rag_response(user_query: str, **kwargs):
    config = get_rag_dev_config()
    session = kwargs.get("session")
    phase_key = resolve_phase(user_query, session)
    kwargs["prompt_injection"] = _merge_injection(kwargs.get("prompt_injection"), config, phase_key)

    result = rag_service.generate_rag_response(user_query, **kwargs)
    if isinstance(result, dict):
        result["active_pipeline"] = "rag_v2"
        result["rag_phase"] = phase_key
        result["phase_master_prompt"] = _phase_prompt(config, phase_key)

        if session is not None:
            saved = save_phase_artifact(
                session.id,
                phase_key,
                artifact=_artifact_payload(phase_key, result),
                summary=str(result.get("answer") or "")[:500],
                source_count=len(result.get("sources") or []),
                updated_by=kwargs.get("user"),
            )
            result["phase_artifact"] = saved
            result["phase_artifacts"] = get_phase_artifact_map(session.id)

    return result


def stream_rag_response(user_query: str, **kwargs) -> Generator[Dict[str, Any], None, None]:
    config = get_rag_dev_config()
    session = kwargs.get("session")
    phase_key = resolve_phase(user_query, session)
    kwargs["prompt_injection"] = _merge_injection(kwargs.get("prompt_injection"), config, phase_key)

    for event in rag_service.stream_rag_response(user_query, **kwargs):
        if isinstance(event, dict) and event.get("type") == "done":
            event.setdefault("active_pipeline", "rag_v2")
            event.setdefault("rag_phase", phase_key)

            if session is not None:
                done_payload = {
                    "answer": event.get("answer") or "",
                    "sources": event.get("sources") or [],
                    "retrieval_confidence": event.get("retrieval_confidence") or {},
                    "reasoning_path": event.get("reasoning_path") or {},
                }
                save_phase_artifact(
                    session.id,
                    phase_key,
                    artifact=_artifact_payload(phase_key, done_payload),
                    summary=str(event.get("answer") or "")[:500],
                    source_count=len(event.get("sources") or []),
                    updated_by=kwargs.get("user"),
                )
                event.setdefault("phase_artifacts", get_phase_artifact_map(session.id))
        yield event
