"""
Central prompt orchestration — versioned prompts from /prompts (Phase: Prompt Orchestration).
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, Optional

from django.conf import settings

logger = logging.getLogger(__name__)

PROMPTS_ROOT = Path(getattr(settings, "PROMPTS_DIR", Path(settings.BASE_DIR) / "prompts"))

# agent_id → (category folder, default version file)
AGENT_PROMPT_MAP: Dict[str, tuple] = {
    "strategist": ("branding", "system_v1.txt"),
    "manifesto": ("manifesto", "system_v1.txt"),
    "positioning": ("positioning", "system_v1.txt"),
    "content": ("content", "system_v1.txt"),
    "tone": ("tone", "system_v1.txt"),
    "default": ("branding", "system_v1.txt"),
}


def load_prompt(relative_path: str) -> str:
    """Load prompt template from prompts/ directory."""
    path = PROMPTS_ROOT / relative_path.replace("\\", "/")
    if not path.exists():
        logger.warning("Prompt not found: %s", path)
        return ""
    return path.read_text(encoding="utf-8", errors="replace").strip()


def get_agent_system_prompt(agent_id: str = "default", version: Optional[str] = None) -> str:
    """Resolve system prompt for an agent (supports A/B via RAG_PROMPT_VARIANT setting)."""
    variant = version or getattr(settings, "RAG_PROMPT_VARIANT", "v1")
    folder, default_file = AGENT_PROMPT_MAP.get(agent_id, AGENT_PROMPT_MAP["default"])
    if variant != "v1" and default_file.endswith("_v1.txt"):
        candidate = default_file.replace("_v1.txt", f"_{variant}.txt")
        if (PROMPTS_ROOT / folder / candidate).exists():
            default_file = candidate
    template = load_prompt(f"{folder}/{default_file}")
    rules = load_prompt("shared/grounding_rules.txt")
    if rules and "Grounding rules" not in template and "{context}" in template:
        template = template.replace("{context}", rules + "\n\n{context}")
    return template


def render_prompt(template: str, **kwargs) -> str:
    """Safe-ish format for prompt templates."""
    try:
        return template.format(**kwargs)
    except KeyError as e:
        logger.warning("Prompt format missing key %s", e)
        return template
