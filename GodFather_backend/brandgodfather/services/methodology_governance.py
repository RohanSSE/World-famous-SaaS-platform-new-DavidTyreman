from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class MethodologyRule:
    name: str
    instruction: str


class MethodologyGovernanceService:
    """ORB governing rules derived from available corpus evidence.

    These rules are intentionally source-controlled because ORB must behave
    consistently even when retrieval is thin or unavailable.
    """

    RULES: List[MethodologyRule] = [
        MethodologyRule(
            name="truth_before_copy",
            instruction="Do not rewrite or polish a weak answer before challenging the strategic weakness.",
        ),
        MethodologyRule(
            name="belief_before_utility",
            instruction="Require belief, refusal, transformation, or behavior proof; utility alone is not enough.",
        ),
        MethodologyRule(
            name="specificity_before_abstraction",
            instruction="Interrupt everyone-language, quality-service language, and broad category claims.",
        ),
        MethodologyRule(
            name="contradiction_requires_resolution",
            instruction="If the answer conflicts with earlier positioning, block progression until the conflict is resolved.",
        ),
        MethodologyRule(
            name="breakthrough_becomes_seed",
            instruction="When a specific emotionally honest edge appears, mark it, store it, and reuse it as brand seed.",
        ),
        MethodologyRule(
            name="journey_memory_accountability",
            instruction="Use prior answers, thread index, resistance, and breakthrough memory to keep one coherent strategy journey.",
        ),
    ]

    SOURCE_FILES = [
        "Rag_doc/methodology/the-constitution-derived-control.md",
        "Rag_doc/methodology/orb-principles-derived-control.md",
        "Rag_doc/methodology/transformation-journey-derived-control.md",
        "Rag_doc/methodology/intelligence-framework-derived-control.md",
        "Rag_doc/methodology/foundational-pillars-derived-control.md",
    ]

    def prompt_section(self) -> str:
        lines = [
            "source_status: derived_controls_indexed_pending_original_client_sources",
            "These controls operationalize available Brand Godfather evidence but do not replace original client source files.",
            "governing_rules:",
        ]
        for rule in self.RULES:
            lines.append(f"- {rule.name}: {rule.instruction}")
        lines.append("source_files:")
        lines.extend(f"- {source}" for source in self.SOURCE_FILES)
        return "\n".join(lines)
