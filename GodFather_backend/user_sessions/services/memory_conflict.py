"""
Strategic memory conflict detection — long-term coherence via contradiction graph.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Set, Tuple

# Conflicting strategic poles (memory pole A ↔ answer signal B)
CONTRADICTION_GRAPH: List[Tuple[str, str, str]] = [
    ("trust", "clickbait", "tone_mismatch"),
    ("trust", "viral", "narrative_drift"),
    ("premium", "playful", "tone_mismatch"),
    ("premium", "discount", "positioning_conflict"),
    ("authority", "casual meme", "tone_mismatch"),
    ("authority", "meme", "tone_mismatch"),
    ("craftsmanship", "speed", "value_conflict"),
    ("craftsmanship", "viral", "value_conflict"),
    ("manifesto", "growth hack", "strategy_conflict"),
    ("consistency", "pivot weekly", "strategy_conflict"),
]

TONE_CONFLICTS = (
    ("premium", "viral"),
    ("premium", "playful discount"),
    ("trust", "clickbait"),
    ("authority", "casual meme"),
    ("manifesto", "growth hack"),
)


def _signals_in_text(text: str, pole: str) -> bool:
    pole = pole.lower().strip()
    if pole in text:
        return True
    aliases = {
        "craftsmanship": ("craft", "artisan", "quality craft"),
        "consistency": ("consistent", "coherent", "aligned"),
        "authority": ("authoritative", "expert", "leader"),
    }
    for alt in aliases.get(pole, ()):
        if alt in text:
            return True
    return False


def detect_graph_conflicts(mem_text: str, answer_text: str) -> List[Dict[str, Any]]:
    conflicts: List[Dict[str, Any]] = []
    seen: Set[str] = set()

    for pole_a, pole_b, ctype in CONTRADICTION_GRAPH:
        if ctype in seen:
            continue
        if _signals_in_text(mem_text, pole_a) and _signals_in_text(answer_text, pole_b):
            seen.add(ctype)
            conflicts.append(
                {
                    "memory_conflict": True,
                    "conflict_type": ctype,
                    "poles": [pole_a, pole_b],
                    "message": (
                        f"Session memory emphasizes '{pole_a}' but the answer leans toward '{pole_b}'. "
                        "Align with established strategic positioning?"
                    ),
                }
            )
    return conflicts


def detect_memory_conflicts(
    answer: str,
    memory_snippets: List[str],
    query: str = "",
) -> List[Dict[str, Any]]:
    conflicts: List[Dict[str, Any]] = []
    if not answer or not memory_snippets:
        return conflicts

    mem = " ".join(memory_snippets).lower()
    ans = answer.lower()
    q = query.lower()

    conflicts.extend(detect_graph_conflicts(mem, ans))

    for a, b in TONE_CONFLICTS:
        if a in mem and b in ans:
            conflicts.append(
                {
                    "memory_conflict": True,
                    "conflict_type": "tone_mismatch",
                    "message": (
                        f"Session memory emphasizes '{a}' but the answer leans toward '{b}'. "
                        "Should we align tone with established brand positioning?"
                    ),
                }
            )

    if "reject" in mem and any(w in ans for w in ("you should try", "recommend using", "best approach is")):
        if any(w in ans for w in ("playful", "viral", "trending")):
            conflicts.append(
                {
                    "memory_conflict": True,
                    "conflict_type": "rejected_strategy_resurface",
                    "message": (
                        "A previously rejected strategic angle may conflict with this recommendation. "
                        "Revisit with manifesto-grounded framing?"
                    ),
                }
            )

    if "trust" in mem and "innovation" in ans and "trust" not in ans[:200]:
        if "speed" in ans or "viral" in ans:
            conflicts.append(
                {
                    "memory_conflict": True,
                    "conflict_type": "narrative_drift",
                    "message": (
                        "Memory emphasizes trust while the answer pushes speed/viral themes. "
                        "Potential narrative drift."
                    ),
                }
            )

    seen = set()
    out = []
    for c in conflicts:
        if c["conflict_type"] not in seen:
            seen.add(c["conflict_type"])
            out.append(c)
    return out[:4]
