"""
Multi-step reasoning + planning agent orchestration (Track 2).
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from django.conf import settings

from .rag_agents import AGENT_REGISTRY, get_agent
from .rag_intelligence import detect_query_intent

logger = logging.getLogger(__name__)

REASONING_STAGES = [
    "understand_intent",
    "determine_strategic_goal",
    "retrieve_knowledge",
    "retrieve_persona_memory",
    "build_reasoning_chain",
    "generate_insight",
    "critique",
    "finalize",
]


def understand_intent(query: str) -> Dict[str, Any]:
    intent = detect_query_intent(query)
    return {"intent": intent, "query": query}


def determine_strategic_goal(query: str, intent: str, agent_id: str) -> str:
    agent = get_agent(agent_id)
    goals = {
        "manifesto": "Craft a philosophically grounded brand manifesto insight",
        "differentiation": "Identify unique positioning vs competitors",
        "emotional": "Surface emotional truth and connection strategy",
        "trust": "Strengthen clarity and trust signals",
        "content": "Translate brand DNA into actionable content direction",
        "positioning": "Sharpen market position and audience fit",
    }
    return goals.get(intent, f"Provide strategic brand guidance as {agent['name']}")


def build_reasoning_chain(
    query: str,
    intent: str,
    goal: str,
    context: str,
    memory_snippets: List[str],
    graph_concepts: List[str],
) -> List[str]:
    chain = [
        f"Intent detected: {intent}",
        f"Strategic goal: {goal}",
    ]
    if graph_concepts:
        chain.append(f"Connected concepts: {', '.join(graph_concepts[:5])}")
    if memory_snippets:
        chain.append(f"Brand memory: {'; '.join(memory_snippets[:2])}")
    if context:
        chain.append("Retrieved knowledge supports grounded response")
    else:
        chain.append("Limited retrieval — rely on general David method")
    chain.append(f"User ask: {query[:200]}")
    return chain


def plan_subtasks(query: str, agent_id: str = "strategist") -> Dict[str, Any]:
    """
    strategy_planner_agent: break complex asks into coordinated subtasks.
    """
    intent = detect_query_intent(query)
    subtasks: List[Dict[str, str]] = []

    if intent in ("manifesto", "emotional", "differentiation"):
        subtasks.append({"agent": "manifesto", "task": "Extract core belief and promise angles"})
    if intent in ("differentiation", "positioning"):
        subtasks.append({"agent": "positioning", "task": "Competitive differentiation frame"})
    if intent == "content":
        subtasks.append({"agent": "content", "task": "Content execution recommendations"})
    if not subtasks:
        subtasks.append({"agent": agent_id, "task": "Primary strategic response"})

    subtasks.append({"agent": "tone", "task": "Calibrate David voice on final output"})
    return {
        "planner": "strategy_planner_agent",
        "intent": intent,
        "subtasks": subtasks,
        "merge_strategy": "primary_agent_with_tone_pass",
    }


def run_planner_entry(query: str, agent_id: str = "strategist") -> Dict[str, Any]:
    """
    Main entry: planner selects agents before retrieval + generation.
    """
    plan = plan_subtasks(query, agent_id)
    selected = [s["agent"] for s in plan.get("subtasks", [])]
    primary = selected[0] if selected else agent_id
    if "positioning" in selected:
        primary = "positioning"
    elif "manifesto" in selected and plan.get("intent") in ("manifesto", "emotional"):
        primary = "manifesto"
    return {
        "plan": plan,
        "primary_agent": primary,
        "selected_agents": selected,
        "intent": plan.get("intent"),
    }


def run_reasoning_pipeline(
    query: str,
    context: str,
    agent_id: str = "strategist",
    memory_snippets: Optional[List[str]] = None,
    graph_concepts: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Full reasoning metadata for debug UI and logging."""
    memory_snippets = memory_snippets or []
    graph_concepts = graph_concepts or []

    intent_data = understand_intent(query)
    intent = intent_data["intent"]
    goal = determine_strategic_goal(query, intent, agent_id)
    plan = plan_subtasks(query, agent_id)
    chain = build_reasoning_chain(query, intent, goal, context, memory_snippets, graph_concepts)

    return {
        "stages": REASONING_STAGES,
        "intent": intent,
        "strategic_goal": goal,
        "reasoning_chain": chain,
        "plan": plan,
        "primary_agent": agent_id,
    }


def thinking_messages_for_ui(reasoning: Dict[str, Any]) -> List[str]:
    """Frontend ORB / thinking pipeline labels."""
    intent = reasoning.get("intent", "general")
    labels = {
        "manifesto": "Recalling manifesto principles…",
        "differentiation": "Analyzing differentiation patterns…",
        "emotional": "Understanding your positioning…",
        "trust": "Evaluating trust and clarity signals…",
        "content": "Mapping content strategy patterns…",
        "positioning": "Connecting strategic concepts…",
    }
    return [
        "Understanding your positioning…",
        labels.get(intent, "Analyzing strategic intent…"),
        "Retrieving brand knowledge…",
        "Connecting strategic concepts…",
    ]
