from __future__ import annotations

from typing import Any, Dict, Optional

from user_sessions.models import RAGPhaseArtifact, Session

_PHASE_ORDER = ["phase_1", "phase_2", "phase_3", "phase_4"]


def phase_index(phase_key: str) -> int:
    try:
        return _PHASE_ORDER.index(phase_key)
    except ValueError:
        return 0


def get_phase_artifact_map(session_id: int) -> Dict[str, Dict[str, Any]]:
    rows = RAGPhaseArtifact.objects.filter(session_id=session_id).order_by("phase_key")
    out: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        out[row.phase_key] = {
            "phase_key": row.phase_key,
            "artifact": row.artifact or {},
            "summary": row.summary or "",
            "source_count": row.source_count,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        }
    return out


def get_latest_completed_phase(session_id: int) -> Optional[str]:
    rows = RAGPhaseArtifact.objects.filter(session_id=session_id)
    latest: Optional[str] = None
    latest_idx = -1

    for row in rows:
        artifact = row.artifact or {}
        completed = bool(artifact.get("completed", True))
        if not completed:
            continue
        idx = phase_index(row.phase_key)
        if idx > latest_idx:
            latest = row.phase_key
            latest_idx = idx
    return latest


def resolve_phase_from_session(session: Optional[Session]) -> str:
    if not session:
        return "phase_1"

    latest = get_latest_completed_phase(session.id)
    if latest:
        next_idx = min(phase_index(latest) + 1, len(_PHASE_ORDER) - 1)
        return _PHASE_ORDER[next_idx]

    stage = session.get_current_stage() if hasattr(session, "get_current_stage") else 1
    if stage <= 1:
        return "phase_1"
    if stage == 2:
        return "phase_2"
    if stage == 3:
        return "phase_3"
    return "phase_4"


def save_phase_artifact(
    session_id: int,
    phase_key: str,
    artifact: Dict[str, Any],
    summary: str = "",
    source_count: int = 0,
    updated_by=None,
) -> Dict[str, Any]:
    row, _ = RAGPhaseArtifact.objects.get_or_create(session_id=session_id, phase_key=phase_key)
    row.artifact = artifact or {}
    row.summary = (summary or "").strip()
    row.source_count = int(max(source_count or 0, 0))
    if updated_by is not None:
        row.updated_by = updated_by
    row.save()

    return {
        "phase_key": row.phase_key,
        "artifact": row.artifact,
        "summary": row.summary,
        "source_count": row.source_count,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }
