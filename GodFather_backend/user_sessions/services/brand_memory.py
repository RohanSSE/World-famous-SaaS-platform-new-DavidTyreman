"""
Long-term brand memory with prioritized retrieval layers (Phase 15).
"""
from __future__ import annotations

import logging
import json
from typing import Any, Dict, List, Optional

from django.conf import settings

logger = logging.getLogger(__name__)

PINNED_MEMORY_TYPES = (
    "manifesto_evolution",
    "strategic_priority",
    "founder_personality",
    "decision",
)

MEMORY_TYPES = (
    "brand_fact",
    "preference",
    "tone",
    "decision",
    "rejected_strategy",
    "persona_note",
    "manifesto_evolution",
    "emotional_language",
    "competitor_mention",
    "strategic_priority",
    "brand_voice",
    "emotional_pattern",
    "competitor_positioning",
    "founder_personality",
    "audience_psychology",
)

# Retrieval layer order (highest priority first)
MEMORY_LAYER_ORDER = (
    ("strategic", ("strategic_priority", "decision", "rejected_strategy", "competitor_positioning")),
    ("emotional", ("emotional_pattern", "emotional_language", "tone", "brand_voice")),
    ("session", ("brand_fact", "preference", "persona_note", "manifesto_evolution", "founder_personality", "audience_psychology", "competitor_mention")),
)


def _generate_memory_embedding(content: str, embedding_service=None) -> Optional[List[float]]:
    if not content or not getattr(settings, "PGVECTOR_ENABLED", True):
        return None
    try:
        if embedding_service is None:
            from document.utils.embedding_service import EmbeddingService

            embedding_service = EmbeddingService()
        return embedding_service.generate_embedding(content[:8000])
    except Exception as e:
        logger.debug("Memory embedding skipped: %s", e)
        return None


def get_session_memory(session_id: int, limit: int = 20, memory_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    try:
        from user_sessions.models import BrandMemory

        qs = BrandMemory.objects.filter(session_id=session_id)
        if memory_types:
            qs = qs.filter(memory_type__in=memory_types)
        rows = qs.order_by("-importance_score", "-updated_at")[:limit]
        return [
            {
                "type": r.memory_type,
                "key": r.key,
                "content": r.content,
                "value": getattr(r, "value", None) or {},
                "confidence": float(getattr(r, "confidence", r.importance_score)),
                "importance_score": r.importance_score,
                "agent_id": r.agent_id,
            }
            for r in rows
        ]
    except Exception as e:
        logger.debug("Brand memory fetch skipped: %s", e)
        return []


def build_layered_memory_context(
    session_id: int,
    query: str,
    agent_id: Optional[str] = None,
    embedding_service=None,
    limit_per_layer: int = 4,
) -> str:
    """
    Priority-ordered memory for RAG:
    strategic_memory → emotional_memory → session_memory
    """
    if not session_id:
        return ""

    semantic_hits: List[Dict[str, Any]] = []
    if query and getattr(settings, "PGVECTOR_ENABLED", True):
        try:
            emb = _generate_memory_embedding(query, embedding_service)
            if emb:
                from utils.pgvector_retrieval import search_brand_memories

                semantic_hits = search_brand_memories(
                    session_id, emb, top_k=limit_per_layer * 3, agent_id=agent_id
                )
        except Exception as e:
            logger.debug("Semantic memory layer skipped: %s", e)

    sections: List[str] = []
    used_keys = set()

    for layer_name, type_group in MEMORY_LAYER_ORDER:
        layer_lines: List[str] = []
        for hit in semantic_hits:
            hit_key = hit.get("key") or f"{hit.get('type')}:{hit.get('content', '')[:40]}"
            if hit.get("type") in type_group and hit_key not in used_keys:
                layer_lines.append(f"- [{hit['type']}] {hit['content'][:280]}")
                used_keys.add(hit_key)
        if len(layer_lines) < limit_per_layer:
            for mem in get_session_memory(session_id, limit=limit_per_layer * 2, memory_types=list(type_group)):
                if mem["key"] not in used_keys:
                    layer_lines.append(f"- [{mem['type']}] {mem['content'][:280]}")
                    used_keys.add(mem["key"])
                if len(layer_lines) >= limit_per_layer:
                    break
        if layer_lines:
            sections.append(f"### {layer_name.replace('_', ' ').title()} memory\n" + "\n".join(layer_lines[:limit_per_layer]))

    if not sections:
        return ""
    return "--- Brand memory (priority layers) ---\n" + "\n\n".join(sections) + "\n--- End brand memory ---"


def format_memory_context_block(
    session_id: int,
    query: str,
    agent_id: Optional[str] = None,
    embedding_service=None,
    limit: int = 6,
) -> str:
    return build_layered_memory_context(session_id, query, agent_id, embedding_service, limit_per_layer=limit)


def memory_snippets_for_retrieval(
    session_id: Optional[int],
    query: Optional[str] = None,
    agent_id: Optional[str] = None,
    embedding_service=None,
    limit: int = 5,
) -> List[str]:
    limit = min(limit, int(getattr(settings, "MAX_MEMORY_SNIPPETS", 8)))
    if not session_id:
        return []
    block = build_layered_memory_context(session_id, query or "", agent_id, embedding_service, limit_per_layer=2)
    if not block:
        return []
    return [line for line in block.split("\n") if line.strip().startswith("-")][:limit]


def upsert_memory(
    session_id: int,
    memory_type: str,
    key: str,
    content: str,
    weight: float = 1.0,
    importance_score: Optional[float] = None,
    confidence: Optional[float] = None,
    value: Optional[Dict[str, Any]] = None,
    agent_id: str = "",
    user=None,
    embedding_service=None,
) -> None:
    try:
        from user_sessions.models import BrandMemory

        imp = importance_score if importance_score is not None else min(1.0, max(0.1, weight * 0.5))
        conf = confidence if confidence is not None else imp
        embedding = _generate_memory_embedding(content, embedding_service)
        defaults = {
            "memory_type": memory_type,
            "content": content,
            "weight": weight,
            "importance_score": imp,
            "agent_id": agent_id or "",
            "embedding": embedding,
            "created_by": user,
            "confidence": conf,
            "value": value or {},
            "is_pinned": memory_type in PINNED_MEMORY_TYPES or (value or {}).get("pinned", False),
        }
        BrandMemory.objects.update_or_create(session_id=session_id, key=key, defaults=defaults)
    except Exception as e:
        logger.warning("Brand memory upsert failed: %s", e)


def record_answer_acceptance_memory(answer, user=None, embedding_service=None) -> Dict[str, Any]:
    if not answer or not getattr(answer, "is_ai_accepted", False):
        return {"recorded": False}

    question_text = (getattr(answer.question, "text", "") or "").strip()
    answer_text = (answer.answer_text or "").strip()
    if not question_text or not answer_text:
        return {"recorded": False}

    value = {
        "answer_id": answer.id,
        "question_id": answer.question_id,
        "question": question_text,
        "answer": answer_text,
        "ai_suggestion": answer.ai_suggestion or answer_text,
        "source": "accepted_ai_answer",
    }
    gist = f"Episodic Q&A gist: Q: {question_text} A: {answer_text}"

    upsert_memory(
        answer.session_id,
        "brand_fact",
        f"episodic:answer:{answer.question_id}",
        gist,
        weight=1.6,
        importance_score=0.88,
        confidence=0.9,
        value=value,
        agent_id="manifesto",
        user=user,
        embedding_service=embedding_service,
    )
    upsert_memory(
        answer.session_id,
        "decision",
        f"accepted_ai_answer:{answer.question_id}",
        f"Client accepted AI answer for '{question_text}': {answer_text}",
        weight=1.8,
        importance_score=0.92,
        confidence=0.9,
        value=value,
        agent_id="strategist",
        user=user,
        embedding_service=embedding_service,
    )
    update_accepted_qa_gist(answer.session_id, user=user, embedding_service=embedding_service)
    return {"recorded": True, "keys": [f"episodic:answer:{answer.question_id}", f"accepted_ai_answer:{answer.question_id}"]}


def update_accepted_qa_gist(session_id: int, user=None, embedding_service=None) -> Optional[str]:
    try:
        from user_sessions.models import Answer

        answers = (
            Answer.objects.filter(session_id=session_id, is_ai_accepted=True)
            .select_related("question")
            .order_by("question__order", "question_id")
        )
        if not answers.exists():
            return None

        items = []
        for answer in answers:
            question_text = (answer.question.text or "").strip()
            answer_text = (answer.answer_text or "").strip()
            if question_text and answer_text:
                items.append({"question": question_text, "answer": answer_text})

        content = "Accepted AI Q&A memory gist:\n" + "\n".join(
            f"- {item['question']}: {item['answer']}" for item in items
        )
        upsert_memory(
            session_id,
            "manifesto_evolution",
            "accepted_qa_gist",
            content[:4000],
            weight=2.0,
            importance_score=0.96,
            confidence=0.92,
            value={"accepted_answers": items, "source": "accepted_ai_qna"},
            agent_id="manifesto",
            user=user,
            embedding_service=embedding_service,
        )
        return content
    except Exception as e:
        logger.warning("Accepted Q&A gist update failed: %s", e)
        return None


def record_content_generation_memory(session_id: int, social_content: Dict[str, Any], user=None, embedding_service=None) -> Dict[str, Any]:
    if not session_id or not isinstance(social_content, dict):
        return {"recorded": False}

    brand_voice = social_content.get("brand_voice") or {}
    captions = social_content.get("social_captions") or []
    post_ideas = social_content.get("post_ideas") or []
    preview_parts = []
    if brand_voice:
        preview_parts.append(f"Brand voice: {json.dumps(brand_voice, ensure_ascii=False)[:900]}")
    if captions:
        preview_parts.append("Caption direction: " + " | ".join(str(c.get("hook_line") or c.get("caption") or "")[:160] for c in captions[:3] if isinstance(c, dict)))
    if post_ideas:
        preview_parts.append("Post ideas: " + " | ".join(str(p.get("title") or p.get("description") or "")[:120] for p in post_ideas[:5] if isinstance(p, dict)))

    content = "Content generation guidance from accepted brand memory:\n" + "\n".join(p for p in preview_parts if p)
    if not content.strip():
        return {"recorded": False}

    upsert_memory(
        session_id,
        "brand_voice",
        "content_generation_guidance",
        content[:4000],
        weight=1.5,
        importance_score=0.82,
        confidence=0.78,
        value={"source": "content_generation", "brand_voice": brand_voice},
        agent_id="content",
        user=user,
        embedding_service=embedding_service,
    )
    return {"recorded": True, "key": "content_generation_guidance"}


def learn_from_rag_interaction(
    session_id: Optional[int],
    query: str,
    answer: str,
    sources: List[Dict],
    user=None,
    agent_id: str = "strategist",
    embedding_service=None,
) -> None:
    if not session_id or not answer:
        return
    q = query[:100]
    if sources and len(sources) >= 2:
        upsert_memory(
            session_id,
            "strategic_priority",
            f"topic:{q[:60]}",
            f"Explored: {q}. Strategic direction reinforced.",
            importance_score=0.65,
            value={"query": q, "source_count": len(sources)},
            agent_id=agent_id,
            user=user,
            embedding_service=embedding_service,
        )
    if any(w in query.lower() for w in ("tone", "voice", "sound")):
        upsert_memory(
            session_id,
            "brand_voice",
            f"tone_pref:{q[:40]}",
            f"Tone discussion: {answer[:200]}",
            importance_score=0.75,
            agent_id="tone",
            user=user,
            embedding_service=embedding_service,
        )
    if any(w in query.lower() for w in ("reject", "not", "avoid", "won't")):
        upsert_memory(
            session_id,
            "rejected_strategy",
            f"rejected:{q[:50]}",
            f"Rejected angle: {answer[:180]}",
            importance_score=0.85,
            agent_id=agent_id,
            user=user,
            embedding_service=embedding_service,
        )
