"""
Heavy AI generation logic for sync views and Celery workers (Phase 6).
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

from django.contrib.auth import get_user_model

from user_sessions.models import AIOutput, Answer, FoundationSummary, Session

from .rag_pipeline_resolver import retrieve_context

logger = logging.getLogger(__name__)
User = get_user_model()


def _openai():
    from user_sessions.views import get_openai_chat_model, get_openai_client
    return get_openai_client(), get_openai_chat_model()


def _parse_summary(raw_text: str) -> Dict[str, Any]:
    from user_sessions.views import _parse_structured_summary
    return _parse_structured_summary(raw_text)


def _summary_structure_instructions() -> str:
    from user_sessions.views import BRAND_SUMMARY_STRUCTURE_INSTRUCTIONS
    return BRAND_SUMMARY_STRUCTURE_INSTRUCTIONS


def _retrieve_brand_book_reference_context(query: str, max_chars: int = 4500) -> Dict[str, Any]:
    """Fetch Vessel & Craft / BrandGodFather RAGv2 reference chunks from the dedicated ES index."""
    try:
        from brandgodfather.services.rag_retrieval import HybridRAGService

        service = HybridRAGService()
        vessel_hits = []
        try:
            vector = service._embed_query(query)
            body = {
                "size": 8,
                "knn": {
                    "field": "dense_vector",
                    "query_vector": vector,
                    "k": 8,
                    "num_candidates": 50,
                    "filter": [
                        {"wildcard": {"chunk_id": "Vessel & Craft FINAL Brand Book.pdf*"}},
                    ],
                },
                "_source": [
                    "chunk_id",
                    "text",
                    "chunk_type",
                    "question_id",
                    "phase",
                    "brand_type",
                    "emotional_register",
                ],
            }
            vessel_hits = service._parse_hits(service.es.search(index=service.INDEX_NAME, body=body))
        except Exception as exc:
            logger.warning("Vessel & Craft vector reference lookup failed: %s", exc)

        general_hits = service._retrieve_context(query_text=query, filters={}, k=24)
        hits = vessel_hits + general_hits
        chunks: List[str] = []
        sources: List[Dict[str, Any]] = []
        seen = set()
        for hit in hits:
            text = str(getattr(hit, "text", "") or "").strip()
            if not text:
                continue
            chunk_id = str(getattr(hit, "chunk_id", "") or "")
            dedupe_key = chunk_id or text[:160]
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            source_title = chunk_id.split("-")[0] if chunk_id else "BrandGodFather RAGv2"
            chunks.append(f"Source: {source_title}\n{text}")
            if chunk_id:
                sources.append({
                    "title": source_title,
                    "source": chunk_id,
                    "type": "brandgodfather_ragv2",
                    "excerpt": text[:260],
                    "relevance_score": round(float(getattr(hit, "score", 0.0) or 0.0), 4),
                })
        context = "\n\n---\n\n".join(chunks).strip()[:max_chars]
        return {"context": context, "sources": sources}
    except Exception as exc:
        logger.warning("Brand Book reference RAGv2 retrieval failed: %s", exc)
        return {"context": "", "sources": []}


def run_manifesto_generation(session_id: int, user_id: int) -> Dict[str, Any]:
    """Generate manifesto with RAG context; updates AIOutput."""
    session = Session.objects.get(pk=session_id)
    user = User.objects.get(pk=user_id)

    ai_output, _ = AIOutput.objects.get_or_create(
        session=session,
        defaults={"status": "pending", "generated_by": user},
    )
    ai_output.status = "processing"
    ai_output.error_message = None
    ai_output.save()

    answers_text = "\n".join(
        [f"{a.question.text}: {a.answer_text}" for a in session.answers.all()]
    )

    retrieval = retrieve_context(
        "brand manifesto principles tone voice structure",
        user=user,
        include_knowledge=True,
        top_k=6,
        max_chars=4000,
    )
    manifesto_knowledge = retrieval["context"]
    sources = retrieval["sources"]

    prompt = f"""Generate a brand manifesto in JSON format based on these answers:
    {answers_text}

    Return a JSON object with this exact structure:
    {{
    "brandName": "string",
    "industryCategory": "string",
    "assumptions": ["string (80-120 words)"],
    "strategicConclusions": ["string (80-120 words)"],
    "coreBelief": "string (50-100 words)",
    "originStory": "string (150-200 words)",
    "brandDNA": ["trait1", "trait2", "trait3"],
    "brandPromise": "string (100-150 words)",
    "emotionalConnectionBefore": "string (80-120 words)",
    "emotionalConnectionAfter": "string (80-120 words)",
    "differentiationStatement": "string (80-120 words)",
    "differentiationHighlight": "string (short highlight)",
    "toneOfVoice": "string",
    "visualMood": "string",
    "designStyle": "string",
    "taglines": ["tagline1", "tagline2", "tagline3"]
    }}

    Respond ONLY with valid JSON, no markdown formatting or backticks."""

    system_content = (
        "You are a brand strategist (David's method). Return only valid JSON without markdown."
    )
    if manifesto_knowledge:
        system_content += (
            "\n\nUse these principles and tone when shaping the manifesto:\n"
            + manifesto_knowledge[:3500]
        )

    try:
        client, model = _openai()
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content.strip()
        json_data = json.loads(content)
        ai_output.json_output = json_data
        ai_output.manifesto = json.dumps(json_data, indent=2)
        ai_output.status = "completed"
        ai_output.save()
        return {
            "success": True,
            "session_id": session_id,
            "sources": sources,
            "ai_output_id": ai_output.id,
        }
    except Exception as e:
        logger.exception("Manifesto generation failed session=%s", session_id)
        ai_output.status = "failed"
        ai_output.error_message = str(e)
        ai_output.save()
        return {"success": False, "error": str(e), "session_id": session_id}


def run_session_summary_generation(session_id: int, user_id: int) -> Dict[str, Any]:
    """Full brand summary with RAG enrichment."""
    session = Session.objects.get(pk=session_id)
    user = User.objects.get(pk=user_id)

    answers = Answer.objects.filter(session=session).select_related("question").order_by(
        "question__order"
    )
    if not answers.exists():
        return {"success": False, "error": "No answers found"}

    qa_text = ""
    for answer in answers:
        qa_text += f"Q: {answer.question.text.strip()}\n"
        qa_text += f"A: {answer.answer_text.strip()}\n\n"

    prompt = f"""
You are THE BRAND GODFATHER. Synthesize all Q&A into a structured Brand Book.

QUESTIONS & ANSWERS:

{qa_text}
"""

    retrieval = retrieve_context(
        "final structured Brand Book sections brand story big idea promise audience vision mission commentary application Vessel & Craft reference",
        user=user,
        session=session,
        include_knowledge=True,
        agent_id="manifesto",
        top_k=8,
        max_chars=4000,
    )

    brand_book_reference = _retrieve_brand_book_reference_context(
        "Vessel & Craft final brand book structure sections Brand Story Big Idea Promise Audience Vision Mission Godfather Standard Application why this works how to apply"
    )

    david_system_prompt = """You are THE BRAND GODFATHER — speaking with David's voice and wisdom.
Generate a final structured Brand Book from all provided answers. Bold, direct, no jargon.
Each Brand Book section must stand alone and include practical Brand Godfather commentary.
"""
    david_system_prompt += _summary_structure_instructions()
    if retrieval["context"]:
        david_system_prompt += "\n\nReference tone and method:\n" + retrieval["context"]
    if brand_book_reference["context"]:
        david_system_prompt += (
            "\n\nVessel & Craft Brand Book reference structure from BrandGodFather RAGv2. "
            "Use this for structure, section quality, Godfather Standard style, and application logic. "
            "Do not copy the client's brand language; adapt only the structure and level of specificity:\n"
            + brand_book_reference["context"]
        )

    try:
        client, model = _openai()
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": david_system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=6000,
            response_format={"type": "json_object"},
        )
        raw_summary = completion.choices[0].message.content.strip()
        summary = _parse_summary(raw_summary)
        sources = (retrieval.get("sources") or []) + (brand_book_reference.get("sources") or [])
        return {
            "success": True,
            "summary": summary,
            "total_questions_answered": answers.count(),
            "sources": sources,
            "brand_book_reference_sources": brand_book_reference.get("sources") or [],
        }
    except Exception as e:
        logger.exception("Summary generation failed session=%s", session_id)
        return {"success": False, "error": str(e)}


def run_foundation_summary_generation(session_id: int, user_id: int) -> Dict[str, Any]:
    """Foundation-stage summary; updates FoundationSummary model."""
    session = Session.objects.get(pk=session_id)
    user = User.objects.get(pk=user_id)

    answers = Answer.objects.filter(
        session=session,
        question__stage=1,
        question__is_active=True,
    ).select_related("question").order_by("question__order")

    if not answers.exists():
        return {"success": False, "error": "No Foundation answers found"}

    qa_text = ""
    for answer in answers:
        qa_text += f"Q: {answer.question.text.strip()}\n"
        qa_text += f"A: {answer.answer_text.strip()}\n\n"

    summary_obj, _ = FoundationSummary.objects.get_or_create(
        session=session,
        defaults={"status": "processing", "generated_by": user},
    )
    summary_obj.status = "processing"
    summary_obj.error_message = None
    summary_obj.save()

    prompt = f"""
You are THE BRAND GODFATHER. Analyze Foundation Q&A and return a structured Brand Book preview.

QUESTIONS & ANSWERS:

{qa_text}
"""

    david_system_prompt = """You are THE BRAND GODFATHER — speaking with David's voice and wisdom.
"""
    david_system_prompt += _summary_structure_instructions()

    retrieval = retrieve_context(
        "foundation brand identity emotional truth structured brand book sections commentary application",
        user=user,
        session=session,
        include_knowledge=True,
        agent_id="manifesto",
        top_k=8,
        max_chars=4000,
    )
    brand_book_reference = _retrieve_brand_book_reference_context(
        "Vessel & Craft final brand book structure Brand Story Big Idea Promise Audience commentary application"
    )
    if retrieval["context"]:
        david_system_prompt += "\n\nReference:\n" + retrieval["context"]
    if brand_book_reference["context"]:
        david_system_prompt += (
            "\n\nBrand Book reference structure from BrandGodFather RAGv2. Use this for section structure and commentary style only:\n"
            + brand_book_reference["context"]
        )

    try:
        client, model = _openai()
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": david_system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
            max_tokens=6000,
            response_format={"type": "json_object"},
        )
        raw_summary = completion.choices[0].message.content.strip()
        summary = _parse_summary(raw_summary)
        summary_obj.summary_text = json.dumps(summary)
        summary_obj.status = "completed"
        summary_obj.save()
        return {
            "success": True,
            "summary": summary,
            "sources": (retrieval.get("sources") or []) + (brand_book_reference.get("sources") or []),
            "brand_book_reference_sources": brand_book_reference.get("sources") or [],
        }
    except Exception as e:
        logger.exception("Foundation summary failed session=%s", session_id)
        summary_obj.status = "failed"
        summary_obj.error_message = str(e)
        summary_obj.save()
        return {"success": False, "error": str(e)}
