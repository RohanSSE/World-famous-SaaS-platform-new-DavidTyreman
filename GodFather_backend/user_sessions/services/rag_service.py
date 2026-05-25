"""
Central RAG service: intelligent retrieval → quality pipeline → GPT with observability.

Phases 1–13 unified entry point.
"""
from __future__ import annotations

import hashlib
import logging
from typing import Any, Dict, Generator, List, Optional, Tuple

from django.conf import settings

from utils.knowledge_graph import expand_query_with_graph, get_related_concepts
from utils.retrieve_ai_knowledge import format_knowledge_context, retrieve_ai_knowledge
from utils.rerank_knowledge import rerank_knowledge_chunks

from . import rag_cache
from .prompt_orchestrator import get_agent_system_prompt, render_prompt
from .rag_agents import get_agent, resolve_query_for_agent
from .rag_evaluation import evaluate_rag_response
from .rag_intelligence import (
    apply_category_boosts,
    build_conversational_query,
    compress_context,
    detect_query_intent,
)
from .rag_observability import (
    RAGTimer,
    RetrievalTrace,
    chunk_debug_row,
    log_rag_query,
)
from .rag_quality_pipeline import run_quality_pipeline, stream_draft_tokens
from .rag_resilience import cache_available, es_available, safe_retrieve
from .reasoning_orchestrator import run_planner_entry, run_reasoning_pipeline, thinking_messages_for_ui
from .brand_memory import learn_from_rag_interaction, memory_snippets_for_retrieval
from .ai_usage_log import log_ai_usage

logger = logging.getLogger(__name__)


def _default_embedding_service():
    from document.utils.embedding_service import EmbeddingService
    return EmbeddingService()


def _default_es_service():
    from document.utils.elasticsearch_service import ElasticsearchService
    return ElasticsearchService()


def _default_openai_client():
    from user_sessions.views import get_openai_client
    return get_openai_client()


def _default_chat_model():
    from user_sessions.views import get_openai_chat_model
    return get_openai_chat_model()


def _context_hash(context: str) -> str:
    return hashlib.sha256(context.encode("utf-8")).hexdigest()[:16]


def extract_sources(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Sources for API/UI with hybrid retrieval scores and retrieval reasons."""
    seen = set()
    sources: List[Dict[str, Any]] = []
    for chunk in chunks:
        meta = chunk.get("metadata") or {}
        file_ref = meta.get("file") or meta.get("path") or ""
        category = meta.get("category") or meta.get("source") or "knowledge"
        title = meta.get("title") or ""
        doc_title = chunk.get("_source_title") or meta.get("document_title") or ""
        key = (file_ref, category, title, doc_title)
        if key in seen:
            continue
        seen.add(key)
        entry: Dict[str, Any] = {"category": category}
        if file_ref:
            entry["file"] = file_ref
        if title:
            entry["title"] = title
        if doc_title:
            entry["document_title"] = doc_title

        vs = chunk.get("vector_score")
        ks = chunk.get("keyword_score")
        gs = chunk.get("graph_score")
        hs = chunk.get("hybrid_score") or chunk.get("score") or chunk.get("rrf_score")
        if vs is not None:
            entry["vector_score"] = round(float(vs), 4)
        if ks is not None:
            entry["keyword_score"] = round(float(ks), 4)
        if gs is not None:
            entry["graph_score"] = round(float(gs), 4)
        if hs is not None:
            entry["hybrid_score"] = round(float(hs), 4)
            entry["relevance_score"] = entry["hybrid_score"]
        rel = chunk.get("source_reliability")
        if rel is not None:
            entry["source_reliability"] = round(float(rel), 3)
        entry["retrieval_reasons"] = _retrieval_reasons(chunk, category)
        sources.append(entry)
    return sources


def _retrieval_reasons(chunk: Dict[str, Any], category: str) -> List[str]:
    """Human-readable reasons for source cards (UX trust)."""
    reasons: List[str] = []
    meta = chunk.get("metadata") or {}
    title = (meta.get("title") or chunk.get("_source_title") or "").lower()
    text = (chunk.get("text") or "")[:200].lower()
    concepts = chunk.get("_matched_concepts") or []

    vs = float(chunk.get("vector_score") or 0)
    ks = float(chunk.get("keyword_score") or 0)
    gs = float(chunk.get("graph_score") or 0)
    ce = float(chunk.get("cross_encoder_score") or 0)

    if vs >= 0.55:
        reasons.append("Strong semantic relevance")
    elif vs >= 0.35:
        reasons.append("Semantic relevance match")

    if ks >= 0.45:
        reasons.append("Keyword alignment")
    if gs >= 0.25:
        reasons.append("Strategic concept relation")
    if ce >= 0.6:
        reasons.append("Cross-encoder relevance boost")

    if category == "manifesto" or "manifesto" in title:
        reasons.append("Manifesto alignment")
    if category in ("branding", "strategy") or "brand" in title:
        reasons.append("Branding framework match")
    if category == "positioning" or any(w in text for w in ("differentiat", "competitor", "position")):
        reasons.append("Differentiation strategy match")
    if any(w in text for w in ("trust", "authority", "credib", "authentic")):
        reasons.append("Trust concept match")
    if any(w in text for w in ("tone", "voice", "emotional")):
        reasons.append("Emotional language match")

    for c in concepts[:2]:
        reasons.append(f"Graph: {c}")

    seen = set()
    unique = []
    for r in reasons:
        if r not in seen:
            seen.add(r)
            unique.append(r)
    return unique[:5] if unique else ["Hybrid retrieval match"]


def build_retrieval_debug(
    planner: Dict[str, Any],
    chunks: List[Dict[str, Any]],
    sources: List[Dict[str, Any]],
    memory_snippets: List[str],
    graph_concepts: List[str],
    trace: Optional[RetrievalTrace] = None,
    agent_id: str = "default",
) -> Dict[str, Any]:
    """Debug payload for frontend tuning panel."""
    ranked = []
    for i, c in enumerate(chunks[:10], 1):
        meta = c.get("metadata") or {}
        ranked.append(
            {
                "rank": i,
                "category": meta.get("category") or c.get("category"),
                "title": (meta.get("title") or "")[:80],
                "hybrid_score": c.get("hybrid_score"),
                "vector_score": c.get("vector_score"),
                "keyword_score": c.get("keyword_score"),
                "graph_score": c.get("graph_score"),
                "cross_encoder_score": c.get("cross_encoder_score"),
                "retrieval_reasons": c.get("rerank_reason")
                or _retrieval_reasons(c, meta.get("category") or "knowledge"),
                "rerank_reason": c.get("rerank_reason", []),
            }
        )
    debug = {
        "agent_id": agent_id,
        "planner": planner.get("plan") if isinstance(planner, dict) else planner,
        "selected_agents": planner.get("selected_agents", []) if isinstance(planner, dict) else [],
        "primary_agent": planner.get("primary_agent") if isinstance(planner, dict) else agent_id,
        "intent": planner.get("intent") if isinstance(planner, dict) else None,
        "chunks_ranked": ranked,
        "sources": sources,
        "memory_snippets": memory_snippets[: int(getattr(settings, "MAX_MEMORY_SNIPPETS", 8))],
        "graph_concepts": graph_concepts,
    }
    if trace:
        debug["latency_ms"] = trace.latency_ms
        debug["cache_hits"] = {
            "embedding": trace.cache_hit_embedding,
            "retrieval": trace.cache_hit_retrieval,
            "gpt": trace.cache_hit_gpt,
        }
        if trace.vector_scores:
            debug["vector_scores_top"] = trace.vector_scores
        if trace.rerank_scores:
            debug["rerank_scores_top"] = trace.rerank_scores
    return debug


INTENT_CATEGORY_MAP = {
    "manifesto": "manifesto",
    "differentiation": "positioning",
    "positioning": "positioning",
    "emotional": "branding",
    "trust": "branding",
    "content": "branding",
}


def _category_filter_for_intent(intent: str, persona: Optional[str] = None) -> Optional[str]:
    """Metadata filter for PGVector knowledge search."""
    return INTENT_CATEGORY_MAP.get(intent)


def get_cached_embedding(text: str, embedding_service=None, trace: Optional[RetrievalTrace] = None) -> List[float]:
    embedding_service = embedding_service or _default_embedding_service()
    key = rag_cache.embedding_cache_key(text)
    cached = rag_cache.cache_get(key)
    if cached is not None:
        if trace:
            trace.cache_hit_embedding = True
        return cached
    vector = embedding_service.generate_embedding(text)
    rag_cache.cache_set(key, vector, rag_cache.ttl_embedding())
    return vector


def retrieve_knowledge_chunks(
    query: str,
    top_k: int = None,
    search_type: str = "hybrid",
    use_rerank: bool = True,
    persona: Optional[str] = None,
    embedding_service=None,
    es_service=None,
    trace: Optional[RetrievalTrace] = None,
) -> List[Dict[str, Any]]:
    top_k = top_k or int(getattr(settings, "AI_KNOWLEDGE_TOP_K", 6))
    pre_k = int(getattr(settings, "MAX_RERANK_CHUNKS_BEFORE", 12))
    embedding_service = embedding_service or _default_embedding_service()
    es_service = es_service or _default_es_service()
    min_score = float(getattr(settings, "RAG_MIN_SCORE_THRESHOLD", 0.01))

    intent = detect_query_intent(query)
    from utils.query_rewriter import rewrite_query_for_retrieval

    rewritten = rewrite_query_for_retrieval(query, intent=intent)
    expanded_query = expand_query_with_graph(rewritten)
    graph_concepts = get_related_concepts(query)
    if trace:
        trace.reasoning_trace = trace.reasoning_trace or {}
        trace.reasoning_trace["query_rewrite"] = rewritten
        trace.reasoning_trace["query_expanded"] = expanded_query
    category_filter = _category_filter_for_intent(intent, persona)
    cache_key = rag_cache.retrieval_cache_key(expanded_query, "knowledge")
    cached = rag_cache.cache_get(cache_key)
    if cached is not None:
        if trace:
            trace.cache_hit_retrieval = True
        return cached

    vector_results: List[Dict] = []
    keyword_results: List[Dict] = []

    if use_rerank and search_type == "hybrid":
        from utils.ai_knowledge_config import AI_KNOWLEDGE_INDEX_NAME

        query_embedding = get_cached_embedding(expanded_query, embedding_service, trace)
        pgvector_ok = bool(getattr(settings, "PGVECTOR_ENABLED", True))
        if pgvector_ok:
            try:
                from utils.pgvector_store import pgvector_knowledge_count

                pgvector_ok = pgvector_knowledge_count() > 0
            except Exception:
                pgvector_ok = False

        if pgvector_ok:
            from utils.pgvector_retrieval import search_similar_chunks

            vector_results = search_similar_chunks(
                query_embedding, top_k=pre_k, category=category_filter
            )
        else:
            vector_results = es_service.vector_search(
                AI_KNOWLEDGE_INDEX_NAME, query_embedding, top_k=top_k * 2
            )
        keyword_results = es_service.keyword_search(
            AI_KNOWLEDGE_INDEX_NAME, expanded_query, top_k=pre_k
        )
        if trace:
            trace.vector_scores = [
                round(float(c.get("score") or 0), 4) for c in vector_results[:top_k]
            ]
            trace.keyword_scores = [
                round(float(c.get("score") or 0), 4) for c in keyword_results[:top_k]
            ]
        chunks = rerank_knowledge_chunks(
            expanded_query,
            vector_results,
            keyword_results,
            top_k=top_k,
            min_score=min_score,
            graph_concepts=graph_concepts,
            intent=intent,
        )
        if trace and chunks:
            rejected = chunks[0].get("_diversity_rejected") or []
            if rejected:
                trace.rejected_chunks = rejected
        if trace:
            trace.rerank_scores = [
                round(float(c.get("score") or c.get("rrf_score") or 0), 4) for c in chunks
            ]
        for c in chunks:
            if graph_concepts:
                c["_matched_concepts"] = [
                    g for g in graph_concepts
                    if g.lower() in ((c.get("text") or "") + str(c.get("metadata", ""))).lower()
                ][:3]
    else:
        chunks = retrieve_ai_knowledge(
            expanded_query,
            embedding_service=embedding_service,
            es_service=es_service,
            search_type=search_type,
            top_k=top_k,
        )

    chunks = apply_category_boosts(chunks, query, persona)
    rag_cache.cache_set(cache_key, chunks, rag_cache.ttl_retrieval())
    return chunks


def retrieve_user_document_chunks(
    user,
    query: str,
    top_k: int = 10,
    document_ids: Optional[List[int]] = None,
    embedding_service=None,
    es_service=None,
    trace: Optional[RetrievalTrace] = None,
) -> Tuple[List[Dict[str, Any]], int]:
    from document.models import Document

    embedding_service = embedding_service or _default_embedding_service()
    es_service = es_service or _default_es_service()

    cache_key = rag_cache.retrieval_cache_key(query, "user_docs", getattr(user, "id", None))
    cached = rag_cache.cache_get(cache_key)
    if cached is not None:
        if trace:
            trace.cache_hit_retrieval = True
        return cached.get("chunks", []), cached.get("documents_searched", 0)

    qs = Document.objects.filter(is_indexed=True, uploaded_by=user)
    if document_ids:
        qs = qs.filter(id__in=document_ids)

    indexed_docs = qs.only("id", "title", "elastic_index_name")
    documents_searched = indexed_docs.count()
    if documents_searched == 0:
        return [], 0

    embedding = get_cached_embedding(query, embedding_service, trace)
    all_hits: List[Dict[str, Any]] = []

    for doc in indexed_docs.iterator():
        try:
            hits = es_service.hybrid_search(
                index_name=doc.elastic_index_name,
                query_text=query,
                query_embedding=embedding,
                top_k=top_k,
            )
            for hit in hits:
                hit["_source_title"] = doc.title
                hit.setdefault("metadata", {})
                hit["metadata"]["document_id"] = doc.id
                hit["metadata"]["document_title"] = doc.title
                hit["metadata"]["category"] = "user_document"
            all_hits.extend(hits)
        except Exception as e:
            logger.warning("User doc search failed %s: %s", doc.elastic_index_name, e)

    all_hits.sort(key=lambda x: float(x.get("score") or 0), reverse=True)
    chunks = all_hits[:top_k]
    rag_cache.cache_set(
        cache_key,
        {"chunks": chunks, "documents_searched": documents_searched},
        rag_cache.ttl_retrieval(),
    )
    return chunks, documents_searched


def retrieve_context(
    query: str,
    user=None,
    session=None,
    include_knowledge: bool = True,
    include_user_docs: bool = False,
    document_ids: Optional[List[int]] = None,
    top_k: int = None,
    max_chars: int = 6000,
    conversation_messages: Optional[List[Dict[str, str]]] = None,
    session_summary: Optional[str] = None,
    agent_id: str = "default",
    embedding_service=None,
    es_service=None,
    trace: Optional[RetrievalTrace] = None,
) -> Dict[str, Any]:
    timer = RAGTimer()
    persona = getattr(session, "persona", None) if session else None

    conv_query = build_conversational_query(
        query, conversation_messages, session_summary
    )
    agent_query = resolve_query_for_agent(agent_id, conv_query)

    if trace:
        trace.query = query
        trace.agent_id = agent_id
        trace.intent = detect_query_intent(query)

    graph_concepts = get_related_concepts(query)
    top_k = top_k or int(getattr(settings, "AI_KNOWLEDGE_TOP_K", 8))
    embedding_service = embedding_service or _default_embedding_service()
    es_service = es_service or _default_es_service()

    all_chunks: List[Dict[str, Any]] = []
    documents_searched = 0

    from .context_orchestration import (
        apply_manifesto_first_scoring,
        compose_strategic_chunks,
        is_strategic_query,
        repair_context,
        validate_context_quality,
    )

    intent = detect_query_intent(query)
    strategic = is_strategic_query(query, intent)
    pool_k = int(getattr(settings, "CONTEXT_RETRIEVAL_POOL_SIZE", 12))

    knowledge_pool: List[Dict[str, Any]] = []
    composed_chunks: List[Dict[str, Any]] = []
    composition_meta: Dict[str, Any] = {}
    context_quality: Dict[str, Any] = {}

    if include_knowledge:
        knowledge_pool = retrieve_knowledge_chunks(
            agent_query,
            top_k=pool_k,
            persona=persona,
            embedding_service=embedding_service,
            es_service=es_service,
            trace=trace,
        )
        if strategic:
            knowledge_pool = apply_manifesto_first_scoring(knowledge_pool, agent_query, strategic=True)

    memory_context = ""
    memory_snippets_list: List[str] = []
    if session:
        from .brand_memory import build_layered_memory_context, get_session_memory

        memory_context = build_layered_memory_context(
            session.pk, query, agent_id=agent_id, embedding_service=embedding_service
        )
        memory_snippets_list = [
            m.get("content", "") for m in get_session_memory(session.pk, limit=8) if m.get("content")
        ]

    if knowledge_pool:
        from user_sessions.services.evidence_weighting import apply_evidence_weights

        knowledge_pool = apply_evidence_weights(knowledge_pool)

        composed_chunks, composition_meta = compose_strategic_chunks(
            knowledge_pool,
            query,
            strategic=strategic,
            memory_snippets=memory_snippets_list,
        )
        draft_context = validate_context_quality(
            composed_chunks,
            knowledge_pool,
            "",
            query,
            strategic=strategic,
        )
        composed_chunks = draft_context.get("chunks", composed_chunks)
        context_quality = draft_context

        if getattr(settings, "RAG_CONTEXT_REPAIR_ENABLED", True) and (
            not context_quality.get("passed")
            or context_quality.get("context_conflict_score", 0)
            > float(getattr(settings, "CONTEXT_REPAIR_CONFLICT_THRESHOLD", 0.30))
            or (
                strategic
                and float(context_quality.get("manifesto_dominance", 0))
                < float(getattr(settings, "CONTEXT_REPAIR_MANIFESTO_THRESHOLD", 0.50))
            )
        ):
            repaired = repair_context(
                composed_chunks, knowledge_pool, context_quality, query, strategic=strategic
            )
            composed_chunks = repaired.get("chunks", composed_chunks)
            context_quality = repaired
            knowledge_context = compress_context(repaired.get("context_text", ""), max_chars)
        else:
            knowledge_context = compress_context(context_quality.get("context_text", ""), max_chars)
    else:
        knowledge_context = ""

    doc_chunks: List[Dict[str, Any]] = []
    if include_user_docs and user is not None:
        doc_chunks, documents_searched = retrieve_user_document_chunks(
            user, agent_query, top_k=top_k, document_ids=document_ids,
            embedding_service=embedding_service, es_service=es_service, trace=trace,
        )

    all_chunks = composed_chunks + doc_chunks
    sources = extract_sources(all_chunks)

    graph_block = ""
    if graph_concepts:
        graph_block = "Related strategic concepts: " + ", ".join(graph_concepts[:8])

    parts = [p for p in [memory_context, knowledge_context, graph_block] if p]
    context = compress_context("\n\n".join(parts), max_chars)

    if trace:
        trace.retrieved_chunks = [chunk_debug_row(c) for c in all_chunks[:top_k]]
        trace.context_sent_to_gpt = context
        trace.pipeline_stages = timer.stages
        trace.latency_ms = timer.mark("retrieval_done")

    return {
        "chunks": all_chunks,
        "context": context,
        "sources": sources,
        "context_used": bool(context),
        "documents_searched": documents_searched,
        "graph_concepts": graph_concepts,
        "expanded_query": agent_query,
        "memory_context_used": bool(memory_context),
        "context_composition": composition_meta,
        "context_quality": context_quality,
        "strategic_query": strategic,
        "knowledge_pool_size": len(knowledge_pool),
        "knowledge_pool": knowledge_pool,
    }


def format_user_document_context(chunks: List[Dict[str, Any]]) -> str:
    if not chunks:
        return ""
    lines = []
    for hit in chunks:
        text = (hit.get("text") or hit.get("_source", {}).get("text", "")).strip()
        title = hit.get("_source_title") or hit.get("metadata", {}).get("document_title", "Unknown")
        if text:
            lines.append(f"📖 From '{title}':\n\"{text}\"")
    if not lines:
        return ""
    return (
        "\n💡 DAVID'S WISDOM (You MUST reference these in your response):\n\n"
        + "\n\n".join(lines)
        + "\n\n⚠️ Base your response on the teachings above.\n"
    )


def build_rag_prompt(
    user_query: str,
    context: str,
    agent_id: str = "default",
    system_persona: Optional[str] = None,
    extra_system: Optional[str] = None,
) -> List[Dict[str, str]]:
    template = system_persona or get_agent_system_prompt(agent_id)
    system_content = render_prompt(template, context=context or "No knowledge retrieved.")
    if extra_system:
        system_content += "\n\n" + extra_system
    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_query},
    ]


def generate_rag_response(
    user_query: str,
    user=None,
    session=None,
    agent_id: str = "default",
    include_user_docs: bool = False,
    document_ids: Optional[List[int]] = None,
    top_k: int = None,
    max_chars: int = 6000,
    temperature: float = None,
    max_tokens: int = 1200,
    use_cache: bool = True,
    conversation_messages: Optional[List[Dict[str, str]]] = None,
    session_summary: Optional[str] = None,
    include_debug: bool = False,
    include_evaluation: bool = False,
    embedding_service=None,
    es_service=None,
    openai_client=None,
    session_id: Optional[int] = None,
) -> Dict[str, Any]:
    timer = RAGTimer()
    trace = RetrievalTrace()
    agent = get_agent(agent_id)
    temperature = temperature if temperature is not None else agent.get("temperature", 0.7)
    sid = session_id or (session.pk if session else None)

    planner = run_planner_entry(user_query, agent_id)
    agent_id = planner.get("primary_agent", agent_id)

    memory_snippets = memory_snippets_for_retrieval(
        sid,
        query=user_query,
        agent_id=agent_id,
        embedding_service=embedding_service,
    )
    if memory_snippets and session_summary:
        session_summary = session_summary + "\n" + "\n".join(memory_snippets)
    elif memory_snippets:
        session_summary = "\n".join(memory_snippets)

    def _do_retrieve():
        return retrieve_context(
            user_query,
            user=user,
            session=session,
            include_knowledge=True,
            include_user_docs=include_user_docs,
            document_ids=document_ids,
            top_k=top_k,
            max_chars=max_chars,
            conversation_messages=conversation_messages,
            session_summary=session_summary,
            agent_id=agent_id,
            embedding_service=embedding_service,
            es_service=es_service,
            trace=trace,
        )

    if not es_available(es_service):
        retrieval = safe_retrieve(_do_retrieve)
    else:
        try:
            retrieval = _do_retrieve()
        except Exception:
            retrieval = safe_retrieve(_do_retrieve)

    reasoning = run_reasoning_pipeline(
        user_query,
        retrieval.get("context", ""),
        agent_id=agent_id,
        memory_snippets=memory_snippets,
        graph_concepts=retrieval.get("graph_concepts", []),
    )
    context = retrieval["context"]
    sources = retrieval["sources"]
    chunks = retrieval["chunks"]

    from .strategic_insight import detect_strategic_tensions, format_proactive_prompt
    from .strategic_style_memory import format_style_prompt, get_strategic_style
    from .brand_brain import format_brand_brain_prompt, get_brand_brain, evolve_brand_brain
    from .brand_language_anchor import extract_brand_language_anchors, format_language_anchor_prompt
    from .feedback_learning import feedback_learning_prompt
    from .longitudinal_memory import (
        check_longitudinal_conflict,
        longitudinal_prompt_suffix,
        record_strategic_position,
    )

    brand_brain = get_brand_brain(sid)
    longitudinal = check_longitudinal_conflict(user_query, session_id=sid, memory_snippets=memory_snippets)

    strategic_insights = detect_strategic_tensions(
        memory_snippets, retrieval.get("graph_concepts", []), user_query, sources
    )
    extra_system = format_proactive_prompt(strategic_insights) or ""
    style = get_strategic_style(sid)
    style_prompt = format_style_prompt(style)
    if style_prompt:
        extra_system = (extra_system + style_prompt).strip()

    extra_system = (extra_system + format_brand_brain_prompt(brand_brain)).strip()
    fb_prompt = feedback_learning_prompt(sid)
    if fb_prompt:
        extra_system = (extra_system + fb_prompt).strip()
    long_suffix = longitudinal_prompt_suffix(longitudinal)
    if long_suffix:
        extra_system = (extra_system + long_suffix).strip()

    language_anchors = extract_brand_language_anchors(chunks, context)
    anchor_prompt = format_language_anchor_prompt(language_anchors)
    if anchor_prompt:
        extra_system = (extra_system + anchor_prompt).strip()

    from .failure_memory import inject_known_failure_warnings, record_failure_event
    from .philosophy_graph import philosophy_prompt_suffix, preserve_graph_consistency
    from .style_stabilization import get_style_vector, score_style_deviation, style_stabilization_prompt

    failure_warn = inject_known_failure_warnings(session_id=sid)
    if failure_warn:
        extra_system = (extra_system + failure_warn).strip()

    graph_check = preserve_graph_consistency(context[:500], context)
    phil_suffix = philosophy_prompt_suffix(graph_check)
    if phil_suffix:
        extra_system = (extra_system + phil_suffix).strip()

    style_dev = score_style_deviation("", get_style_vector(sid))
    style_suffix = style_stabilization_prompt(style_dev)
    if style_suffix:
        extra_system = (extra_system + style_suffix).strip()

    from .retrieval_confidence import assess_retrieval_confidence, confidence_label

    from .retrieval_critique import critique_retrieval_quality

    retrieval_critique = critique_retrieval_quality(user_query, chunks)
    context_quality = retrieval.get("context_quality") or {}
    if context_quality.get("full_verify_required"):
        retrieval_critique.setdefault("flags", []).append("context_conflict")
        retrieval_critique["full_verify_required"] = True
    if context_quality.get("strategic_density", 1) < float(
        getattr(settings, "CONTEXT_MIN_STRATEGIC_DENSITY", 0.60)
    ):
        retrieval_critique.setdefault("flags", []).append("low_strategic_density")
    if retrieval_critique.get("prompt_suffix"):
        extra_system = (extra_system + "\n\n" + retrieval_critique["prompt_suffix"]).strip()
    if context_quality.get("context_conflicts"):
        extra_system = (
            extra_system
            + "\n\nCONTEXT NOTE: Retrieved sources contain mixed strategic signals. "
            "Resolve toward manifesto-grounded trust and consistency; reject contradictory hype framing."
        ).strip()

    conf_mode, conf_avg, conf_prompt = assess_retrieval_confidence(chunks)
    if context_quality.get("context_conflict_score", 0) > 0:
        conf_avg = max(0.0, conf_avg - 0.20)
    if conf_prompt:
        extra_system = (extra_system + "\n\n" + conf_prompt).strip()

    retrieval_confidence = {
        "mode": conf_mode,
        "avg_hybrid_score": conf_avg,
        "label": confidence_label(conf_mode),
    }
    gpt_key = None

    if use_cache:
        gpt_key = rag_cache.gpt_response_cache_key(user_query, _context_hash(context))
        cached_answer = rag_cache.cache_get(gpt_key)
        if cached_answer is not None:
            trace.cache_hit_gpt = True
            trace.latency_ms = timer.total_ms
            result = {
                "answer": cached_answer,
                "sources": sources,
                "context_used": retrieval["context_used"],
                "chunks_retrieved": len(chunks),
                "cached": True,
                "agent_id": agent_id,
            }
            if include_debug or getattr(settings, "DEBUG_RAG", False):
                result["debug"] = trace.to_debug_dict()
            log_rag_query(user_query, user, trace, cached_answer, agent_id, session_id)
            return result

    from .content_safety import sanitize_context_for_content_filter

    safe_context = sanitize_context_for_content_filter(context)
    messages = build_rag_prompt(user_query, safe_context, agent_id=agent_id, extra_system=extra_system)
    client = openai_client or _default_openai_client()
    model = _default_chat_model()

    force_full_verify = bool(
        retrieval_critique.get("full_verify_required")
        or context_quality.get("full_verify_required")
    )
    strategic_query = bool(retrieval.get("strategic_query"))
    from .evidence_weighting import weighted_source_confidence
    from .uncertainty_generation import uncertainty_generation_config

    pre_confidence = min(
        1.0,
        max(
            0.25,
            conf_avg
            + float(context_quality.get("strategic_density") or 0) * 0.15
            - float(context_quality.get("context_conflict_score") or 0) * 0.25,
            weighted_source_confidence(sources, chunks) * 0.2,
        ),
    )
    uncertainty = uncertainty_generation_config(pre_confidence)
    extra_system = (extra_system + uncertainty["mode_prompt"]).strip()
    gen_temperature = uncertainty.get("temperature_adjustment", temperature)

    pipeline_result = run_quality_pipeline(
        client,
        model,
        messages,
        user_query,
        safe_context,
        gen_temperature,
        max_tokens,
        retrieval_confidence=conf_mode,
        force_full_verify=force_full_verify,
        context_quality=context_quality,
        retrieval_critique=retrieval_critique,
        confidence_score=pre_confidence,
        strategic_query=strategic_query,
        composed_chunks=chunks,
        language_anchors=language_anchors,
    )
    # verify against full context; generate with sanitized context for Azure safety
    answer = pipeline_result["answer"]

    from .cross_session_contradiction import detect_cross_session_contradiction

    cross_sess = detect_cross_session_contradiction(answer, sid, memory_snippets)
    longitudinal_post = check_longitudinal_conflict(user_query, answer, sid, memory_snippets)
    graph_answer_check = preserve_graph_consistency(answer, context)

    from .memory_conflict import detect_memory_conflicts

    post_conflicts = detect_memory_conflicts(answer, memory_snippets, user_query)
    for mc in post_conflicts:
        if not any(s.get("type") == mc.get("conflict_type") for s in strategic_insights):
            strategic_insights.append(
                {"type": mc.get("conflict_type", "memory_conflict"), "priority": "high", "message": mc["message"]}
            )

    trace.token_usage = pipeline_result.get("token_usage", {})
    retrieval_ms = timer.stages.get("retrieval_done", 0)
    latency_breakdown = {
        "embedding_ms": int(trace.pipeline_stages.get("embedding_ms", 0)),
        "retrieval_ms": retrieval_ms,
        "rerank_ms": int(trace.pipeline_stages.get("rerank_ms", retrieval_ms)),
        "generation_ms": int(pipeline_result.get("generation_ms", 0)),
        "verification_ms": int(pipeline_result.get("verification_ms", 0)),
        "total_ms": timer.total_ms,
    }
    trace.pipeline_stages = {**trace.pipeline_stages, **latency_breakdown, "total": timer.total_ms}
    trace.latency_ms = timer.total_ms

    if use_cache and gpt_key:
        rag_cache.cache_set(gpt_key, answer, rag_cache.ttl_gpt())

    from .reasoning_drift import score_reasoning_drift
    from .retrieval_metrics import (
        score_manifesto_dominance,
        score_split_retrieval_metrics,
        score_top1_hit,
    )

    drift = pipeline_result.get("reasoning_drift") or score_reasoning_drift(answer, context)
    split_metrics = score_split_retrieval_metrics(
        {"query": user_query},
        chunks,
        context_composition=context_quality,
    )
    from .strategic_consistency import compute_strategic_consistency
    from .reasoning_path import build_reasoning_path

    consistency = compute_strategic_consistency(answer, context, memory_snippets, style, session_id=sid)
    if sid:
        evolve_brand_brain(sid, answer, consistency=consistency, user=user)
        record_strategic_position(sid, user_query, answer[:600], user=user)
    reasoning_path = build_reasoning_path(
        answer,
        context,
        sources,
        verification=pipeline_result.get("verification", {}),
        drift=drift,
        graph_concepts=retrieval.get("graph_concepts", []),
        memory_snippets=memory_snippets,
        chunks=chunks,
    )
    retrieval_scores = {
        **score_top1_hit({"query": user_query, "expected_categories": []}, chunks),
        **score_manifesto_dominance({"query": user_query}, chunks),
        **split_metrics,
        **drift,
        **consistency,
    }

    result: Dict[str, Any] = {
        "answer": answer,
        "sources": sources,
        "context_used": retrieval["context_used"],
        "chunks_retrieved": len(chunks),
        "chunks": chunks,
        "retrieval_scores": retrieval_scores,
        "cached": False,
        "agent_id": agent_id,
        "pipeline": pipeline_result.get("pipeline"),
        "graph_concepts": retrieval.get("graph_concepts", []),
        "planner": planner.get("plan"),
        "selected_agents": planner.get("selected_agents", []),
    }

    from .system_health import get_system_health

    result["system_health"] = get_system_health()
    result["strategic_insights"] = strategic_insights
    result["retrieval_confidence"] = retrieval_confidence
    result["retrieval_critique"] = retrieval_critique
    result["context_quality"] = context_quality
    result["context_composition"] = retrieval.get("context_composition", {})
    result["reasoning_drift"] = drift
    result["reasoning_path"] = reasoning_path
    result["strategic_consistency"] = consistency
    result["critique_flags"] = pipeline_result.get("critique_flags", [])
    result["adaptive_repair"] = pipeline_result.get("repair", {})
    result["overclaim_suppressed"] = pipeline_result.get("overclaim_suppressed", False)
    result["repair_metrics"] = pipeline_result.get("repair_metrics", {})
    result["generation_mode"] = uncertainty.get("generation_mode")
    result["cross_session_contradiction"] = cross_sess
    result["longitudinal_memory"] = longitudinal_post
    result["brand_brain"] = get_brand_brain(sid)
    result["philosophy_graph"] = graph_answer_check
    result["reliability"] = pipeline_result.get("repair_metrics", {})
    result["verification"] = pipeline_result.get("verification", {})

    result["latency_breakdown"] = latency_breakdown

    evaluation = evaluate_rag_response(
        answer,
        context,
        sources,
        chunks,
        user_query,
        memory_snippets=memory_snippets,
        graph_concepts=retrieval.get("graph_concepts", []),
    )

    if pipeline_result.get("critique_flags"):
        record_failure_event(
            pipeline_result.get("critique_flags", []),
            query=user_query,
            severity=float(evaluation.get("hallucination_risk", 0.5)),
            session_id=sid,
        )

    from .enterprise_confidence import compute_enterprise_confidence

    enterprise_conf = compute_enterprise_confidence(
        conf_mode,
        conf_avg,
        sources,
        evaluation=evaluation,
        verification=pipeline_result.get("verification", {}),
        memory_conflicts=post_conflicts,
        context_quality=context_quality,
        reasoning_drift=drift,
    )
    if consistency.get("consistency_score"):
        enterprise_conf["confidence_score"] = round(
            min(
                1.0,
                enterprise_conf["confidence_score"] * 0.85
                + consistency["consistency_score"] * 0.15,
            ),
            3,
        )
    result["confidence"] = enterprise_conf
    retrieval_confidence["confidence_score"] = enterprise_conf["confidence_score"]
    retrieval_confidence["confidence_label"] = enterprise_conf["confidence_label"]

    if include_evaluation or getattr(settings, "RAG_EVALUATION_ENABLED", False):
        result["evaluation"] = evaluation
    else:
        result["evaluation"] = evaluation  # always attach for transparency in enterprise mode

    if getattr(settings, "RAG_DEBUG_PANEL", True) or include_debug or getattr(settings, "DEBUG_RAG", False):
        result["retrieval_debug"] = build_retrieval_debug(
            planner, chunks, sources, memory_snippets, retrieval.get("graph_concepts", []), trace, agent_id
        )

    if include_debug or getattr(settings, "DEBUG_RAG", False):
        result["debug"] = trace.to_debug_dict()
        result["debug"]["reasoning"] = reasoning

    result["thinking_messages"] = thinking_messages_for_ui(reasoning)
    result["reasoning_chain"] = reasoning.get("reasoning_chain", [])
    result["_context"] = context

    from .strategic_style_memory import (
        evolve_strategic_memory_profile,
        update_strategic_style_from_interaction,
    )

    update_strategic_style_from_interaction(sid, answer, memory_snippets, user)
    if sid:
        evolve_strategic_memory_profile(sid, answer, memory_snippets, consistency, user)

    learn_from_rag_interaction(
        sid, user_query, answer, sources, user, agent_id=agent_id, embedding_service=embedding_service
    )
    log_ai_usage(
        user,
        agent_id,
        "rag_query",
        trace.token_usage,
        latency_ms=trace.latency_ms,
        session_id=sid,
        cache_hit=trace.cache_hit_gpt or trace.cache_hit_retrieval,
        degraded=bool(retrieval.get("degraded")),
    )

    log_rag_query(user_query, user, trace, answer, agent_id, sid)

    from .reasoning_trace import build_reasoning_trace
    from .request_trace import log_ai_request_trace

    reasoning_trace = build_reasoning_trace(
        planner=planner,
        chunks=chunks,
        sources=sources,
        memory_snippets=memory_snippets,
        verification=pipeline_result.get("verification", {}),
        rejected_chunks=trace.rejected_chunks,
        pipeline=pipeline_result.get("pipeline", ""),
    )
    reasoning_trace["reasoning_path"] = reasoning_path[:6]
    reasoning_trace["critique_flags"] = pipeline_result.get("critique_flags", [])
    reasoning_trace["context_repairs"] = context_quality.get("repairs_applied", [])
    trace.reasoning_trace = reasoning_trace
    result["reasoning_trace"] = reasoning_trace

    log_ai_request_trace(
        user,
        user_query,
        agent_id,
        latency_breakdown,
        retrieval_confidence=conf_mode,
        hallucination_risk=evaluation.get("hallucination_risk"),
        pipeline=pipeline_result.get("pipeline", ""),
        session_id=sid,
        stages=trace.pipeline_stages,
        confidence_score=enterprise_conf.get("confidence_score"),
        reasoning_trace=reasoning_trace,
    )
    return result


def stream_rag_response(
    user_query: str,
    user=None,
    session=None,
    agent_id: str = "default",
    **kwargs,
) -> Generator[Dict[str, Any], None, None]:
    """SSE-friendly event generator: planner → sources → tokens → done."""
    from .system_health import get_system_health
    from .strategic_insight import detect_strategic_tensions, format_proactive_prompt

    planner = run_planner_entry(user_query, agent_id)
    agent_id = planner.get("primary_agent", agent_id)
    sid = session.pk if session else None

    memory_snippets = memory_snippets_for_retrieval(
        sid, query=user_query, agent_id=agent_id
    )

    yield {
        "type": "planner",
        "plan": planner.get("plan"),
        "selected_agents": planner.get("selected_agents", []),
        "agent_id": agent_id,
    }

    health = get_system_health()
    yield {"type": "system_health", "system_health": health}

    max_chars = kwargs.get("max_chars") or int(getattr(settings, "MAX_CONTEXT_CHARS", 6000))
    retrieval = retrieve_context(
        user_query,
        user=user,
        session=session,
        agent_id=agent_id,
        top_k=kwargs.get("top_k"),
        max_chars=max_chars,
        include_user_docs=kwargs.get("include_user_docs", False),
        document_ids=kwargs.get("document_ids"),
        conversation_messages=kwargs.get("conversation_messages"),
        embedding_service=kwargs.get("embedding_service"),
        es_service=kwargs.get("es_service"),
    )
    insights = detect_strategic_tensions(
        memory_snippets, retrieval.get("graph_concepts", []), user_query, retrieval["sources"]
    )

    yield {
        "type": "sources",
        "sources": retrieval["sources"],
        "graph_concepts": retrieval.get("graph_concepts", []),
        "strategic_insights": insights,
        "system_health": health,
    }

    from .retrieval_confidence import assess_retrieval_confidence
    from .rag_quality_pipeline import run_quality_pipeline, stream_verified_answer

    conf_mode, conf_avg, conf_prompt = assess_retrieval_confidence(retrieval.get("chunks", []))
    extra = format_proactive_prompt(insights) if insights else ""
    if conf_prompt:
        extra = (extra + "\n\n" + conf_prompt).strip()
    messages = build_rag_prompt(user_query, retrieval["context"], agent_id=agent_id, extra_system=extra)
    client = _default_openai_client()
    model = _default_chat_model()
    agent = get_agent(agent_id)

    stream_verified = getattr(settings, "RAG_STREAM_VERIFIED", True)
    if stream_verified:
        yield {"type": "status", "content": "Verifying answer against knowledge…"}
        pipeline_result = run_quality_pipeline(
            client,
            model,
            messages,
            user_query,
            retrieval["context"],
            agent.get("temperature", 0.7),
            kwargs.get("max_tokens", 1200),
            retrieval_confidence=conf_mode,
            composed_chunks=retrieval.get("chunks", []),
        )
        verified = pipeline_result.get("answer", "")
        for token in stream_verified_answer(verified):
            yield {"type": "token", "content": token}
        from .reasoning_path import build_reasoning_path

        reasoning_path = build_reasoning_path(
            verified,
            retrieval["context"],
            retrieval["sources"],
            verification=pipeline_result.get("verification", {}),
            chunks=retrieval.get("chunks", []),
        )
        yield {
            "type": "done",
            "strategic_insights": insights,
            "verification": pipeline_result.get("verification", {}),
            "pipeline": pipeline_result.get("pipeline"),
            "answer": verified,
            "reasoning_path": reasoning_path,
            "critique_flags": pipeline_result.get("critique_flags", []),
            "strategic_consistency": pipeline_result.get("strategic_consistency", {}),
            "retrieval_confidence": conf_mode,
            "repair_metrics": pipeline_result.get("repair_metrics", {}),
            "sources": retrieval["sources"][:12],
        }
    else:
        for token in stream_draft_tokens(
            client, model, messages, agent.get("temperature", 0.7), kwargs.get("max_tokens", 1200)
        ):
            yield {"type": "token", "content": token}
        yield {"type": "done", "strategic_insights": insights}


def build_combined_context_for_draft(
    question_text: str,
    draft: str,
    user,
    session=None,
    conversation_messages: Optional[List[Dict]] = None,
    top_k: int = 8,
    embedding_service=None,
    es_service=None,
) -> Dict[str, Any]:
    search_query = build_conversational_query(
        f"{question_text} {draft}".strip(), conversation_messages
    )
    embedding_service = embedding_service or _default_embedding_service()
    es_service = es_service or _default_es_service()
    persona = getattr(session, "persona", None) if session else None

    doc_chunks, documents_searched = retrieve_user_document_chunks(
        user, search_query, top_k=12,
        embedding_service=embedding_service, es_service=es_service,
    )
    doc_context = format_user_document_context(doc_chunks)
    knowledge = retrieve_context(
        question_text,
        user=user,
        session=session,
        include_knowledge=True,
        include_user_docs=False,
        conversation_messages=conversation_messages,
        top_k=top_k,
        max_chars=4000,
        embedding_service=embedding_service,
        es_service=es_service,
    )
    parts = []
    if doc_context:
        parts.append(doc_context)
    if knowledge["context"]:
        parts.append("\n--- David's method & training ---\n" + knowledge["context"])
    combined = "\n".join(parts)

    return {
        "context": combined,
        "sources": extract_sources(doc_chunks) + knowledge["sources"],
        "context_used": bool(combined),
        "documents_searched": documents_searched,
        "chunks": doc_chunks + knowledge["chunks"],
        "graph_concepts": knowledge.get("graph_concepts") or get_related_concepts(search_query),
    }
