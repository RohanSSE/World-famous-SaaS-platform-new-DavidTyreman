"""
Multi-agent definitions sharing one RAG backbone (Phase 13).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

AGENT_REGISTRY: Dict[str, Dict[str, Any]] = {
    "strategist": {
        "name": "Brand Strategist",
        "role": "Brand direction and DNA coaching",
        "prompt_key": "strategist",
        "categories": ["branding", "strategy"],
        "temperature": 0.7,
    },
    "manifesto": {
        "name": "Manifesto AI",
        "role": "Philosophy, core belief, brand promise",
        "prompt_key": "manifesto",
        "categories": ["manifesto", "branding"],
        "temperature": 0.6,
    },
    "content": {
        "name": "Content AI",
        "role": "Social media and campaign execution",
        "prompt_key": "content",
        "categories": ["marketing", "content"],
        "temperature": 0.75,
    },
    "positioning": {
        "name": "Positioning AI",
        "role": "Market differentiation",
        "prompt_key": "positioning",
        "categories": ["positioning", "strategy"],
        "temperature": 0.65,
    },
    "research": {
        "name": "Research AI",
        "role": "Competitor and market analysis framing",
        "prompt_key": "positioning",
        "categories": ["strategy", "positioning", "sales"],
        "temperature": 0.5,
    },
    "memory": {
        "name": "Memory AI",
        "role": "User history and session continuity",
        "prompt_key": "strategist",
        "categories": ["branding"],
        "temperature": 0.4,
    },
    "tone": {
        "name": "Tone Coach",
        "role": "David voice calibration",
        "prompt_key": "tone",
        "categories": ["branding", "manifesto"],
        "temperature": 0.7,
    },
}


def get_agent(agent_id: str) -> Dict[str, Any]:
    return AGENT_REGISTRY.get(agent_id, AGENT_REGISTRY["strategist"])


def list_agents() -> List[Dict[str, Any]]:
    return [{"id": k, **v} for k, v in AGENT_REGISTRY.items()]


def resolve_query_for_agent(agent_id: str, query: str) -> str:
    """Intent hint appended to query based on agent role."""
    agent = get_agent(agent_id)
    cats = " ".join(agent.get("categories", []))
    return f"{query} [{agent['role']}; focus: {cats}]"
