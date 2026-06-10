from __future__ import annotations

from typing import Any, Dict

from django.contrib.auth import get_user_model

from user_sessions.models import RAGDevConfig

_DEFAULT_CONFIG: Dict[str, Any] = {
    "active_pipeline": "rag_v1",
    "enabled": False,
    "pre_retrieval_prompt": "",
    "system_injection_prompt": "",
    "retrieval_profile_notes": "",
    "phase_1_master_prompt": "",
    "phase_2_master_prompt": "",
    "phase_3_master_prompt": "",
    "phase_4_master_prompt": "",
    "updated_at": None,
    "updated_by": None,
}


def _normalize(raw: Dict[str, Any] | None) -> Dict[str, Any]:
    cfg = dict(_DEFAULT_CONFIG)
    if isinstance(raw, dict):
        cfg.update(raw)

    active_pipeline = str(cfg.get("active_pipeline") or "rag_v1").strip().lower()
    cfg["active_pipeline"] = active_pipeline if active_pipeline in {"rag_v1", "rag_v2"} else "rag_v1"
    cfg["enabled"] = bool(cfg.get("enabled", False))
    cfg["pre_retrieval_prompt"] = str(cfg.get("pre_retrieval_prompt") or "").strip()
    cfg["system_injection_prompt"] = str(cfg.get("system_injection_prompt") or "").strip()
    cfg["retrieval_profile_notes"] = str(cfg.get("retrieval_profile_notes") or "").strip()
    cfg["phase_1_master_prompt"] = str(cfg.get("phase_1_master_prompt") or "").strip()
    cfg["phase_2_master_prompt"] = str(cfg.get("phase_2_master_prompt") or "").strip()
    cfg["phase_3_master_prompt"] = str(cfg.get("phase_3_master_prompt") or "").strip()
    cfg["phase_4_master_prompt"] = str(cfg.get("phase_4_master_prompt") or "").strip()
    cfg["updated_by"] = cfg.get("updated_by")
    cfg["updated_at"] = cfg.get("updated_at")
    return cfg


def get_rag_dev_config() -> Dict[str, Any]:
    try:
        row = RAGDevConfig.objects.filter(key="global").select_related("updated_by").first()
        if not row:
            return dict(_DEFAULT_CONFIG)

        data = {
            "active_pipeline": row.active_pipeline,
            "enabled": row.enabled,
            "pre_retrieval_prompt": row.pre_retrieval_prompt,
            "system_injection_prompt": row.system_injection_prompt,
            "retrieval_profile_notes": row.retrieval_profile_notes,
            "phase_1_master_prompt": row.phase_1_master_prompt,
            "phase_2_master_prompt": row.phase_2_master_prompt,
            "phase_3_master_prompt": row.phase_3_master_prompt,
            "phase_4_master_prompt": row.phase_4_master_prompt,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None,
            "updated_by": getattr(row.updated_by, "email", None) if row.updated_by else None,
        }
    except Exception:
        return dict(_DEFAULT_CONFIG)

    return _normalize(data)


def save_rag_dev_config(payload: Dict[str, Any], updated_by: str | None = None) -> Dict[str, Any]:
    cfg = _normalize(payload)

    user_obj = None
    if updated_by:
        try:
            user_model = get_user_model()
            user_obj = user_model.objects.filter(email=updated_by).first()
        except Exception:
            user_obj = None

    row, _ = RAGDevConfig.objects.get_or_create(key="global")
    row.active_pipeline = cfg["active_pipeline"]
    row.enabled = cfg["enabled"]
    row.pre_retrieval_prompt = cfg["pre_retrieval_prompt"]
    row.system_injection_prompt = cfg["system_injection_prompt"]
    row.retrieval_profile_notes = cfg["retrieval_profile_notes"]
    row.phase_1_master_prompt = cfg["phase_1_master_prompt"]
    row.phase_2_master_prompt = cfg["phase_2_master_prompt"]
    row.phase_3_master_prompt = cfg["phase_3_master_prompt"]
    row.phase_4_master_prompt = cfg["phase_4_master_prompt"]
    row.updated_by = user_obj
    row.save()

    return {
        "active_pipeline": row.active_pipeline,
        "enabled": row.enabled,
        "pre_retrieval_prompt": row.pre_retrieval_prompt,
        "system_injection_prompt": row.system_injection_prompt,
        "retrieval_profile_notes": row.retrieval_profile_notes,
        "phase_1_master_prompt": row.phase_1_master_prompt,
        "phase_2_master_prompt": row.phase_2_master_prompt,
        "phase_3_master_prompt": row.phase_3_master_prompt,
        "phase_4_master_prompt": row.phase_4_master_prompt,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        "updated_by": getattr(row.updated_by, "email", updated_by or "admin") if row.updated_by else (updated_by or "admin"),
    }
