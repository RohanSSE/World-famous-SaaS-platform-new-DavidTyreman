from __future__ import annotations

from typing import Any, Dict

from django.contrib.auth import get_user_model

from AdminAITuning.models import AITuningVersion
from user_sessions.services.rag_dev_config import get_rag_dev_config, save_rag_dev_config

PHASE_KEYS = {
    "phase_1_master_prompt",
    "phase_2_master_prompt",
    "phase_3_master_prompt",
    "phase_4_master_prompt",
}

DEFAULT_BASE_CONFIG: Dict[str, Any] = {
    "active_pipeline": "rag_v1",
    "enabled": False,
    "pre_retrieval_prompt": "",
    "system_injection_prompt": "",
    "retrieval_profile_notes": "",
    "phase_1_master_prompt": "",
    "phase_2_master_prompt": "",
    "phase_3_master_prompt": "",
    "phase_4_master_prompt": "",
}


def _serialize_version(row: AITuningVersion) -> Dict[str, Any]:
    return {
        "id": row.id,
        "version_number": row.version_number,
        "action": row.action,
        "section_key": row.section_key,
        "active_pipeline": row.active_pipeline,
        "snapshot": row.snapshot or {},
        "is_default_template": bool(row.is_default_template),
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "created_by": getattr(row.created_by, "email", None) if row.created_by else None,
    }


def _resolve_user(updated_by_email: str | None):
    if not updated_by_email:
        return None
    try:
        user_model = get_user_model()
        return user_model.objects.filter(email=updated_by_email).first()
    except Exception:
        return None


def _extract_phase_parts(value: str | None) -> Dict[str, str]:
    text = str(value or "").strip()
    if not text:
        return {"prompt": "", "goal": "", "criteria": ""}

    prompt_marker = "[Prompt]"
    goal_marker = "[Goal]"
    criteria_marker = "[Evaluation Criteria]"

    if prompt_marker not in text and goal_marker not in text and criteria_marker not in text:
        return {"prompt": text, "goal": "", "criteria": ""}

    def between(src: str, start: str, end: str | None = None) -> str:
        if start not in src:
            return ""
        start_idx = src.index(start) + len(start)
        sliced = src[start_idx:]
        if end and end in sliced:
            sliced = sliced[: sliced.index(end)]
        return sliced.strip()

    return {
        "prompt": between(text, prompt_marker, goal_marker),
        "goal": between(text, goal_marker, criteria_marker),
        "criteria": between(text, criteria_marker, None),
    }


def _build_phase_prompt(payload: Dict[str, Any]) -> str:
    prompt = str(payload.get("prompt") or "").strip()
    goal = str(payload.get("goal") or "").strip()
    criteria = str(payload.get("criteria") or "").strip()
    return (
        f"[Prompt]\n{prompt}\n\n"
        f"[Goal]\n{goal}\n\n"
        f"[Evaluation Criteria]\n{criteria}"
    ).strip()


def _ensure_default_template() -> AITuningVersion:
    row = AITuningVersion.objects.filter(is_default_template=True).order_by("-created_at").first()
    if row:
        return row

    return AITuningVersion.objects.create(
        action="load_default",
        section_key="global",
        active_pipeline=DEFAULT_BASE_CONFIG["active_pipeline"],
        snapshot=dict(DEFAULT_BASE_CONFIG),
        is_default_template=True,
    )


def _record_version(*, action: str, section_key: str, snapshot: Dict[str, Any], updated_by: str | None) -> Dict[str, Any]:
    user_obj = _resolve_user(updated_by)
    row = AITuningVersion.objects.create(
        action=action,
        section_key=section_key if section_key in PHASE_KEYS else "global",
        active_pipeline=str(snapshot.get("active_pipeline") or "rag_v1"),
        snapshot=snapshot,
        created_by=user_obj,
        is_default_template=False,
    )
    return _serialize_version(row)


def get_train_bgf_state(limit: int = 20) -> Dict[str, Any]:
    cfg = get_rag_dev_config()
    default_template = _ensure_default_template()

    versions_qs = AITuningVersion.objects.filter(is_default_template=False).order_by("-created_at")[: max(1, min(limit, 100))]

    return {
        "config": cfg,
        "sections": {
            key: _extract_phase_parts(cfg.get(key, ""))
            for key in sorted(PHASE_KEYS)
        },
        "default_template": _serialize_version(default_template),
        "versions": [_serialize_version(v) for v in versions_qs],
    }


def save_section_tuning(*, section_key: str, section_data: Dict[str, Any], active_pipeline: str | None, updated_by: str | None) -> Dict[str, Any]:
    if section_key not in PHASE_KEYS:
        raise ValueError("Invalid section_key")

    current = get_rag_dev_config()
    payload = {
        "active_pipeline": (active_pipeline or current.get("active_pipeline") or "rag_v1"),
        "enabled": bool(current.get("enabled", False)),
        "pre_retrieval_prompt": str(current.get("pre_retrieval_prompt") or ""),
        "system_injection_prompt": str(current.get("system_injection_prompt") or ""),
        "retrieval_profile_notes": str(current.get("retrieval_profile_notes") or ""),
        "phase_1_master_prompt": str(current.get("phase_1_master_prompt") or ""),
        "phase_2_master_prompt": str(current.get("phase_2_master_prompt") or ""),
        "phase_3_master_prompt": str(current.get("phase_3_master_prompt") or ""),
        "phase_4_master_prompt": str(current.get("phase_4_master_prompt") or ""),
    }
    payload[section_key] = _build_phase_prompt(section_data)

    saved = save_rag_dev_config(payload, updated_by=updated_by)
    version = _record_version(
        action="save",
        section_key=section_key,
        snapshot=saved,
        updated_by=updated_by,
    )
    return {"config": saved, "version": version}


def train_section_tuning(*, section_key: str, section_data: Dict[str, Any], active_pipeline: str | None, updated_by: str | None) -> Dict[str, Any]:
    save_result = save_section_tuning(
        section_key=section_key,
        section_data=section_data,
        active_pipeline=active_pipeline,
        updated_by=updated_by,
    )

    from utils.ai_knowledge_auto import ensure_index_current

    ok, message = ensure_index_current(async_build=True, force=False)

    train_version = _record_version(
        action="train",
        section_key=section_key,
        snapshot=save_result["config"],
        updated_by=updated_by,
    )

    return {
        "section_key": section_key,
        "trained": bool(ok),
        "message": message,
        "config": save_result["config"],
        "version": train_version,
    }


def load_default_tuning(*, updated_by: str | None) -> Dict[str, Any]:
    default_template = _ensure_default_template()
    snapshot = dict(default_template.snapshot or DEFAULT_BASE_CONFIG)
    saved = save_rag_dev_config(snapshot, updated_by=updated_by)

    version = _record_version(
        action="load_default",
        section_key="global",
        snapshot=saved,
        updated_by=updated_by,
    )

    return {
        "config": saved,
        "version": version,
        "default_template": _serialize_version(default_template),
    }
