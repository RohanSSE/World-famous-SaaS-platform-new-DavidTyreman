"""
Explainable reasoning path — claim-level cognition graph for enterprise trust.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .answer_attribution import extract_claim_attributions
from .claim_verification import detect_unsupported_claims
from .grounded_generation import verify_claims_at_level


def build_reasoning_path(
    answer: str,
    context: str,
    sources: List[Dict[str, Any]],
    verification: Optional[Dict[str, Any]] = None,
    drift: Optional[Dict[str, Any]] = None,
    graph_concepts: Optional[List[str]] = None,
    memory_snippets: Optional[List[str]] = None,
    chunks: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """
    Per-claim trace: claim, support_chunks, grounded, support_strength.
    """
    verification = verification or verify_claims_at_level(
        answer, context, chunks=chunks or sources
    )
    drift = drift or {}
    claim_records = verification.get("claims") or []

    if claim_records:
        path: List[Dict[str, Any]] = []
        for rec in claim_records:
            grounded = rec.get("grounded", False)
            strength = float(rec.get("support_strength") or 0)
            if not grounded:
                status, risk = "unsupported", 0.65
            elif strength >= 0.55:
                status, risk = "grounded", round(0.12 + (1 - strength) * 0.2, 3)
            else:
                status, risk = "partial", 0.4
            if drift.get("drift_detected") and not grounded:
                status, risk = "drift_risk", 0.5
            path.append(
                {
                    "claim": rec.get("claim", ""),
                    "support_chunks": rec.get("support_chunks", []),
                    "grounded": grounded,
                    "support_strength": strength,
                    "supported_by": rec.get("support_chunks", []),
                    "verification_status": status,
                    "risk": risk,
                }
            )
        return path[:12]

    attributions = extract_claim_attributions(
        answer, context, sources, graph_concepts, memory_snippets
    )
    unsupported_sents = {
        u.get("sentence", u.get("claim", ""))[:200]
        for u in (verification.get("unsupported_claims") or detect_unsupported_claims(answer, context))
    }

    path = []
    for attr in attributions:
        claim = attr.get("claim", "")
        supported = attr.get("supported_by", [])
        is_unattributed = "unattributed" in supported
        is_unsupported = any(claim[:80] in s or s[:80] in claim for s in unsupported_sents)

        if is_unsupported or is_unattributed:
            status, risk = "unsupported", 0.65
        elif drift.get("drift_detected") and is_unattributed:
            status, risk = "drift_risk", 0.45
        elif supported:
            status, risk = "grounded", 0.12
        else:
            status, risk = "partial", 0.35

        path.append(
            {
                "claim": claim,
                "supported_by": supported,
                "verification_status": status,
                "risk": round(risk, 3),
            }
        )

    return path[:12]
