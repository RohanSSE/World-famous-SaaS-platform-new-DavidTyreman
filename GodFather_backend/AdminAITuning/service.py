from __future__ import annotations

from typing import Any, Dict
from pathlib import Path

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
    "phase_1_base_prompt": "",
    "phase_1_admin_injection_prompt": "",
    "phase_1_admin_injection_goal": "",
    "phase_1_admin_injection_criteria": "",
    "phase_1_master_prompt": "",
    "phase_2_master_prompt": "",
    "phase_3_master_prompt": "",
    "phase_4_master_prompt": "",
}


def _load_brand_discovery_prompt() -> str:
    base_dir = Path(__file__).resolve().parents[1]
    prompt_path = base_dir / "prompts" / "RAGv2Prompts" / "BrandDiscoveryPrompt.md"
    try:
        return prompt_path.read_text(encoding="utf-8").strip()
    except Exception:
        return ""


def _compose_phase_1_prompt(base_prompt: str, section_data: Dict[str, Any]) -> str:
    mandatory = str(base_prompt or "").strip()
    prompt = str(section_data.get("prompt") or "").strip()
    goal = str(section_data.get("goal") or "").strip()
    criteria = str(section_data.get("criteria") or "").strip()

    if not mandatory:
        return _build_phase_prompt(section_data)

    blocks = [mandatory]
    if prompt or goal or criteria:
        blocks.append(
            (
                "[Admin Optional Injection]\n"
                f"[Prompt]\n{prompt}\n\n"
                f"[Goal]\n{goal}\n\n"
                f"[Evaluation Criteria]\n{criteria}"
            ).strip()
        )
    return "\n\n".join(blocks)


def _ensure_brand_discovery_in_config(cfg: Dict[str, Any], updated_by: str | None = None) -> Dict[str, Any]:
    base_prompt = str(cfg.get("phase_1_base_prompt") or "").strip()
    if base_prompt:
        if not str(cfg.get("phase_1_master_prompt") or "").strip():
            cfg["phase_1_master_prompt"] = _compose_phase_1_prompt(
                base_prompt,
                {
                    "prompt": cfg.get("phase_1_admin_injection_prompt") or "",
                    "goal": cfg.get("phase_1_admin_injection_goal") or "",
                    "criteria": cfg.get("phase_1_admin_injection_criteria") or "",
                },
            )
        return cfg

    fallback = _load_brand_discovery_prompt()
    if not fallback:
        return cfg

    cfg["phase_1_base_prompt"] = fallback
    cfg["phase_1_master_prompt"] = _compose_phase_1_prompt(
        fallback,
        {
            "prompt": cfg.get("phase_1_admin_injection_prompt") or "",
            "goal": cfg.get("phase_1_admin_injection_goal") or "",
            "criteria": cfg.get("phase_1_admin_injection_criteria") or "",
        },
    )
    return save_rag_dev_config(cfg, updated_by=updated_by)


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
        snapshot = dict(row.snapshot or {})
        if not snapshot.get("phase_1_base_prompt"):
            base_prompt = _load_brand_discovery_prompt()
            if base_prompt:
                snapshot["phase_1_base_prompt"] = base_prompt
                snapshot["phase_1_master_prompt"] = _compose_phase_1_prompt(
                    base_prompt,
                    {
                        "prompt": snapshot.get("phase_1_admin_injection_prompt") or "",
                        "goal": snapshot.get("phase_1_admin_injection_goal") or "",
                        "criteria": snapshot.get("phase_1_admin_injection_criteria") or "",
                    },
                )
                row.snapshot = snapshot
                row.save(update_fields=["snapshot"])
        return row

    base_prompt = _load_brand_discovery_prompt()
    snapshot = dict(DEFAULT_BASE_CONFIG)
    snapshot["phase_1_base_prompt"] = base_prompt
    snapshot["phase_1_master_prompt"] = _compose_phase_1_prompt(base_prompt, {"prompt": "", "goal": "", "criteria": ""})

    return AITuningVersion.objects.create(
        action="load_default",
        section_key="global",
        active_pipeline=DEFAULT_BASE_CONFIG["active_pipeline"],
        snapshot=snapshot,
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
    cfg = _ensure_brand_discovery_in_config(get_rag_dev_config())
    default_template = _ensure_default_template()

    versions_qs = AITuningVersion.objects.filter(is_default_template=False).order_by("-created_at")[: max(1, min(limit, 100))]

    return {
        "config": cfg,
        "sections": {
            key: (
                {
                    "mandatory_prompt": str(cfg.get("phase_1_base_prompt") or ""),
                    "prompt": str(cfg.get("phase_1_admin_injection_prompt") or ""),
                    "goal": str(cfg.get("phase_1_admin_injection_goal") or ""),
                    "criteria": str(cfg.get("phase_1_admin_injection_criteria") or ""),
                }
                if key == "phase_1_master_prompt"
                else _extract_phase_parts(cfg.get(key, ""))
            )
            for key in sorted(PHASE_KEYS)
        },
        "default_template": _serialize_version(default_template),
        "versions": [_serialize_version(v) for v in versions_qs],
    }


def activate_engine_tuning(*, active_pipeline: str | None, enabled: bool = True, updated_by: str | None) -> Dict[str, Any]:
    pipeline = str(active_pipeline or "").strip().lower()
    if pipeline not in {"rag_v1", "rag_v2"}:
        raise ValueError("Invalid active_pipeline")

    current = _ensure_brand_discovery_in_config(get_rag_dev_config(), updated_by=updated_by)
    payload = {
        "active_pipeline": pipeline,
        "enabled": bool(enabled),
        "pre_retrieval_prompt": str(current.get("pre_retrieval_prompt") or ""),
        "system_injection_prompt": str(current.get("system_injection_prompt") or ""),
        "retrieval_profile_notes": str(current.get("retrieval_profile_notes") or ""),
        "phase_1_base_prompt": str(current.get("phase_1_base_prompt") or _load_brand_discovery_prompt()),
        "phase_1_admin_injection_prompt": str(current.get("phase_1_admin_injection_prompt") or ""),
        "phase_1_admin_injection_goal": str(current.get("phase_1_admin_injection_goal") or ""),
        "phase_1_admin_injection_criteria": str(current.get("phase_1_admin_injection_criteria") or ""),
        "phase_1_master_prompt": str(current.get("phase_1_master_prompt") or ""),
        "phase_2_master_prompt": str(current.get("phase_2_master_prompt") or ""),
        "phase_3_master_prompt": str(current.get("phase_3_master_prompt") or ""),
        "phase_4_master_prompt": str(current.get("phase_4_master_prompt") or ""),
    }

    saved = save_rag_dev_config(payload, updated_by=updated_by)
    version = _record_version(
        action="save",
        section_key="global",
        snapshot=saved,
        updated_by=updated_by,
    )
    return {
        "config": saved,
        "version": version,
        "mapped_endpoints": [
            "/api/sessions/rag-query/",
            "/api/sessions/<session_id>/rag-query/",
            "/api/sessions/rag-query/stream/",
            "/api/sessions/<session_id>/rag-query/stream/",
            "/api/sessions/<session_id>/generate-manifesto/",
            "/api/sessions/<session_id>/generate-summary/",
            "/api/sessions/<session_id>/generate-foundation-summary/",
            "/api/sessions/<session_id>/brand-workflow/",
        ],
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
        "phase_1_base_prompt": str(current.get("phase_1_base_prompt") or _load_brand_discovery_prompt()),
        "phase_1_admin_injection_prompt": str(current.get("phase_1_admin_injection_prompt") or ""),
        "phase_1_admin_injection_goal": str(current.get("phase_1_admin_injection_goal") or ""),
        "phase_1_admin_injection_criteria": str(current.get("phase_1_admin_injection_criteria") or ""),
        "phase_1_master_prompt": str(current.get("phase_1_master_prompt") or ""),
        "phase_2_master_prompt": str(current.get("phase_2_master_prompt") or ""),
        "phase_3_master_prompt": str(current.get("phase_3_master_prompt") or ""),
        "phase_4_master_prompt": str(current.get("phase_4_master_prompt") or ""),
    }
    if section_key == "phase_1_master_prompt":
        # Phase 1 base prompt is immutable and always loaded from DB state.
        payload["phase_1_admin_injection_prompt"] = str(section_data.get("prompt") or "").strip()
        payload["phase_1_admin_injection_goal"] = str(section_data.get("goal") or "").strip()
        payload["phase_1_admin_injection_criteria"] = str(section_data.get("criteria") or "").strip()
        payload["phase_1_master_prompt"] = _compose_phase_1_prompt(
            payload["phase_1_base_prompt"],
            {
                "prompt": payload["phase_1_admin_injection_prompt"],
                "goal": payload["phase_1_admin_injection_goal"],
                "criteria": payload["phase_1_admin_injection_criteria"],
            },
        )
    else:
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
