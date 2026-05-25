"""
Brand operating workflows — product-facing intelligence engines.
Architecture frozen; extend queries/aliases only.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .brand_brain import get_brand_brain
from .brand_output_schemas import empty_brand_output, narrative_to_structured_sections
from .brand_language_anchor import extract_brand_language_anchors

# Canonical workflow keys → retrieval query
WORKFLOW_QUERIES = {
    "brand_dna": (
        "Using ONLY retrieved brand book knowledge, produce a complete Brand DNA: "
        "core beliefs, non-negotiables, emotional promise, differentiation anchor, "
        "and audience psychology. Be specific and grounded."
    ),
    "positioning": (
        "From the brand book ONLY, define positioning: category role, competitive frame, "
        "market enemy to ignore, and why this brand wins. Mirror exact brand book phrases. "
        "No generic marketing filler."
    ),
    "positioning_engine": (
        "POSITIONING ENGINE — Using ONLY brand book excerpts: category role, "
        "competitive frame, status signals, and differentiation anchor. "
        "Every sentence must trace to retrieved text."
    ),
    "tone_guide": (
        "Create a tone guide: voice, energy, forbidden phrases, preferred phrases, "
        "and communication laws aligned with the brand book."
    ),
    "messaging_pillars": (
        "Extract 4-6 messaging pillars with proof from retrieved knowledge. "
        "Each pillar must cite a principle from context."
    ),
    "messaging_framework": (
        "MESSAGING FRAMEWORK — Build messaging ladder: brand promise, proof points, "
        "emotional hooks, and pillar hierarchy — all from brand book only."
    ),
    "audience_psychology": (
        "Describe audience psychology: motivations, pain points, desired identity, "
        "fears, desires, and emotional drivers grounded in brand book."
    ),
    "campaign_strategy": (
        "Propose campaign direction: strategic theme, emotional hooks, ad angles, "
        "messaging ladder — all traceable to brand book. Hedge if evidence is thin."
    ),
    "campaign_direction": (
        "CAMPAIGN DIRECTION — Strategic theme, emotional hooks, channel tone, "
        "messaging ladder from brand book only. No viral/growth-hack framing."
    ),
    "content_engine": (
        "Suggest content directions: LinkedIn tone, landing page angle, email voice, "
        "founder voice — consistent with brand book restraint and authority."
    ),
    "founder_narrative": (
        "Summarize founder narrative: origin conviction, personal voice, and brand story "
        "as supported by retrieved documents."
    ),
}

WORKFLOW_ALIASES = {
    "messaging_framework": "messaging_pillars",
    "campaign_direction": "campaign_strategy",
    "positioning_engine": "positioning",
}

PRODUCT_WORKFLOWS = [
    {"id": "brand_dna", "label": "Brand DNA Generator", "priority": "high"},
    {"id": "messaging_framework", "label": "Messaging Framework", "priority": "high"},
    {"id": "tone_guide", "label": "Tone Guide", "priority": "high"},
    {"id": "audience_psychology", "label": "Audience Psychology", "priority": "high"},
    {"id": "campaign_direction", "label": "Campaign Direction", "priority": "high"},
    {"id": "positioning_engine", "label": "Positioning Engine", "priority": "high"},
]

PRODUCT_PACK_WORKFLOWS = [
    "brand_dna",
    "positioning_engine",
    "tone_guide",
    "messaging_framework",
    "audience_psychology",
]

SECTION_MAP = {
    "brand_dna": "brand_dna",
    "positioning": "positioning",
    "positioning_engine": "positioning",
    "tone_guide": "tone_rules",
    "messaging_pillars": "messaging_pillars",
    "messaging_framework": "messaging_pillars",
    "audience_psychology": "audience_psychology",
    "campaign_strategy": "campaign_direction",
    "campaign_direction": "campaign_direction",
    "content_engine": "campaign_direction",
    "founder_narrative": "founder_narrative",
}


def resolve_workflow(workflow: str) -> str:
    w = (workflow or "brand_dna").lower().strip()
    return WORKFLOW_ALIASES.get(w, w)


def list_product_workflows() -> List[Dict[str, Any]]:
    """API discovery — product workflow catalog."""
    return [
        {
            **item,
            "canonical_id": resolve_workflow(item["id"]),
            "endpoint": "POST /api/sessions/{session_id}/brand-workflow/",
        }
        for item in PRODUCT_WORKFLOWS
    ]


def run_brand_workflow(
    workflow: str,
    session_id: Optional[int] = None,
    user=None,
    session=None,
    extra_context: str = "",
    agent_id: str = "branding",
) -> Dict[str, Any]:
    """Execute a named brand workflow and return structured + narrative output."""
    canonical = resolve_workflow(workflow)
    if canonical not in WORKFLOW_QUERIES and workflow not in WORKFLOW_QUERIES:
        return {
            "error": f"Unknown workflow: {workflow}",
            "available": list(WORKFLOW_QUERIES.keys()) + list(WORKFLOW_ALIASES.keys()),
        }

    query = WORKFLOW_QUERIES.get(workflow) or WORKFLOW_QUERIES[canonical]
    if extra_context:
        query = f"{extra_context.strip()}\n\n{query}"

    from user_sessions.services.rag_service import generate_rag_response

    result = generate_rag_response(
        user_query=query,
        user=user,
        session=session,
        session_id=session_id,
        agent_id=agent_id,
        include_evaluation=True,
        use_cache=False,
    )

    chunks = result.get("chunks") or []
    context = result.get("_context") or ""
    anchors = extract_brand_language_anchors(chunks, context)
    structured = narrative_to_structured_sections(result.get("answer") or "", anchors)

    key = SECTION_MAP.get(workflow) or SECTION_MAP.get(canonical, canonical)
    if key in structured and result.get("answer"):
        if isinstance(structured[key], dict):
            structured[key]["narrative"] = result.get("answer", "")[:3000]
        elif isinstance(structured[key], list):
            structured[key] = [{"pillar": result.get("answer", "")[:500]}]

    return {
        "workflow": workflow,
        "canonical_workflow": canonical,
        "query": query,
        "structured": structured,
        "narrative": result.get("answer", ""),
        "sources": result.get("sources", [])[:12],
        "evaluation": result.get("evaluation", {}),
        "brand_brain": get_brand_brain(session_id),
        "language_anchors": anchors,
        "reasoning_path": result.get("reasoning_path", []),
        "strategic_consistency": result.get("strategic_consistency", {}),
        "verification": result.get("verification", {}),
        "explainability": {
            "reasoning_path": result.get("reasoning_path", []),
            "sources": result.get("sources", [])[:8],
            "critique_flags": result.get("critique_flags", []),
            "strategic_consistency": result.get("strategic_consistency", {}),
        },
    }


def run_product_pack(
    session_id: Optional[int] = None,
    user=None,
    session=None,
    workflows: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Run high-priority product workflows in one package."""
    wf_list = workflows or PRODUCT_PACK_WORKFLOWS
    package = empty_brand_output()
    results: Dict[str, Any] = {}

    for wf in wf_list:
        out = run_brand_workflow(wf, session_id=session_id, user=user, session=session)
        results[wf] = out
        struct = out.get("structured") or {}
        for k, v in struct.items():
            if k in package and v:
                package[k] = v

    return {
        "workflows_run": wf_list,
        "brand_operating_system": package,
        "workflow_results": results,
        "brand_brain": get_brand_brain(session_id),
    }


def run_full_brand_operating_system(
    session_id: Optional[int] = None,
    user=None,
    session=None,
) -> Dict[str, Any]:
    """Alias for full product pack."""
    return run_product_pack(session_id=session_id, user=user, session=session)
