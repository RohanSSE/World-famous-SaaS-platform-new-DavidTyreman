from __future__ import annotations

import hashlib
import json
import logging
from typing import Iterable, List

from django.utils import timezone

from user_sessions.models import Question

logger = logging.getLogger(__name__)


def source_hash(question: Question) -> str:
    source = f"{question.stage}|{question.order}|{question.text.strip()}"
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


def ensure_refined_questions(questions: Iterable[Question], force: bool = False) -> List[Question]:
    question_list = list(questions)
    stale_questions = [
        question
        for question in question_list
        if question.text.strip()
        and (
            force
            or
            not question.ai_refined_text.strip()
            or question.ai_refined_source_hash != source_hash(question)
        )
    ]

    if not stale_questions:
        return question_list

    try:
        refinements = _generate_refinements(stale_questions, improve_existing=force)
    except Exception:
        logger.exception("AI question refinement failed; returning admin source questions")
        return question_list

    now = timezone.now()
    for question in stale_questions:
        refined_text = (refinements.get(str(question.id)) or "").strip()
        if not refined_text:
            continue
        question.ai_refined_text = refined_text
        question.ai_refined_source_hash = source_hash(question)
        question.ai_refined_at = now
        question.save(
            update_fields=[
                "ai_refined_text",
                "ai_refined_source_hash",
                "ai_refined_at",
                "updated_at",
            ]
        )

    return question_list


def user_facing_question_text(question: Question) -> str:
    if question.ai_refined_text and question.ai_refined_source_hash == source_hash(question):
        return question.ai_refined_text.strip()
    return question.text


def _generate_refinements(questions: List[Question], improve_existing: bool = False) -> dict[str, str]:
    from user_sessions.views import get_openai_chat_model, get_openai_client

    payload = []
    for question in questions:
        item = {
            "id": question.id,
            "stage": question.stage,
            "order": question.order,
            "source_text": question.text.strip(),
        }
        if (
            improve_existing
            and question.ai_refined_text.strip()
            and question.ai_refined_source_hash == source_hash(question)
        ):
            item["previous_text"] = question.ai_refined_text.strip()
        payload.append(item)

    client = get_openai_client()
    response = client.chat.completions.create(
        model=get_openai_chat_model(),
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a senior brand strategist for Brand Godfather. "
                    "Rewrite admin-entered source prompts into polished user-facing "
                    "Brand Book discovery questions. Preserve the strategic intent, "
                    "stage, and order. Make every question clear, specific, warm, "
                    "answerable, and useful for generating a premium brand book. "
                    "If previous_text is provided, improve that wording one step further "
                    "while preserving the source_text intent. "
                    "Use one sentence per question. Do not add numbering, markdown, "
                    "examples, explanations, or extra fields. Return only JSON."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Rewrite these source questions. Return exactly this JSON shape: "
                    '{"questions":[{"id":1,"text":"..."}]}\n\n'
                    f"Source questions:\n{json.dumps(payload, ensure_ascii=True)}"
                ),
            },
        ],
        temperature=0.35,
        max_tokens=2200,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content or "{}"
    data = json.loads(content)
    items = data.get("questions") if isinstance(data, dict) else None
    if not isinstance(items, list):
        return {}

    refinements = {}
    valid_ids = {str(question.id) for question in questions}
    for item in items:
        if not isinstance(item, dict):
            continue
        question_id = str(item.get("id") or "").strip()
        text = str(item.get("text") or "").strip()
        if question_id in valid_ids and text:
            refinements[question_id] = text
    return refinements