from __future__ import annotations

from typing import Any, Dict, Generator, Optional

from user_sessions.services.rag_dev_config import get_rag_dev_config
from user_sessions.services.rag_v1 import pipeline as rag_v1_pipeline
from user_sessions.services.rag_v2 import pipeline as rag_v2_pipeline

_ALLOWED_PIPELINES = {"rag_v1", "rag_v2"}


def get_active_pipeline_name(override: Optional[str] = None) -> str:
    selected = str(override or "").strip().lower()
    if selected in _ALLOWED_PIPELINES:
        return selected

    cfg = get_rag_dev_config()
    configured = str(cfg.get("active_pipeline") or "rag_v1").strip().lower()
    return configured if configured in _ALLOWED_PIPELINES else "rag_v1"


def _pipeline_module(name: str):
    if name == "rag_v2":
        return rag_v2_pipeline
    return rag_v1_pipeline


def retrieve_context(user_query: str, pipeline: Optional[str] = None, **kwargs) -> Dict[str, Any]:
    resolved = get_active_pipeline_name(pipeline)
    result = _pipeline_module(resolved).retrieve_context(user_query, **kwargs)
    if isinstance(result, dict):
        result.setdefault("active_pipeline", resolved)
    return result


def generate_rag_response(user_query: str, pipeline: Optional[str] = None, **kwargs) -> Dict[str, Any]:
    resolved = get_active_pipeline_name(pipeline)
    result = _pipeline_module(resolved).generate_rag_response(user_query, **kwargs)
    if isinstance(result, dict):
        result.setdefault("active_pipeline", resolved)
    return result


def stream_rag_response(
    user_query: str,
    pipeline: Optional[str] = None,
    **kwargs,
) -> Generator[Dict[str, Any], None, None]:
    resolved = get_active_pipeline_name(pipeline)
    for event in _pipeline_module(resolved).stream_rag_response(user_query, **kwargs):
        if isinstance(event, dict) and event.get("type") == "done":
            event.setdefault("active_pipeline", resolved)
        yield event
