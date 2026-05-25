"""
RAG observability: debug payloads, latency, query logging (Phase 8).
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

from django.conf import settings

logger = logging.getLogger(__name__)


@dataclass
class RetrievalTrace:
    query: str = ""
    latency_ms: int = 0
    cache_hit_embedding: bool = False
    cache_hit_retrieval: bool = False
    cache_hit_gpt: bool = False
    vector_scores: List[float] = field(default_factory=list)
    keyword_scores: List[float] = field(default_factory=list)
    rerank_scores: List[float] = field(default_factory=list)
    retrieved_chunks: List[Dict[str, Any]] = field(default_factory=list)
    rejected_chunks: List[Dict[str, Any]] = field(default_factory=list)
    reasoning_trace: Dict[str, Any] = field(default_factory=dict)
    context_sent_to_gpt: str = ""
    token_usage: Dict[str, int] = field(default_factory=dict)
    pipeline_stages: Dict[str, int] = field(default_factory=dict)
    agent_id: str = "default"
    intent: str = ""

    def to_debug_dict(self) -> Dict[str, Any]:
        return {
            "retrieved_chunks": self.retrieved_chunks,
            "vector_scores": self.vector_scores,
            "keyword_scores": self.keyword_scores,
            "rerank_scores": self.rerank_scores,
            "latency_ms": self.latency_ms,
            "cache_hit": {
                "embedding": self.cache_hit_embedding,
                "retrieval": self.cache_hit_retrieval,
                "gpt": self.cache_hit_gpt,
            },
            "context_preview": (self.context_sent_to_gpt or "")[:800],
            "context_length": len(self.context_sent_to_gpt or ""),
            "token_usage": self.token_usage,
            "pipeline_stages_ms": self.pipeline_stages,
            "agent_id": self.agent_id,
            "intent": self.intent,
            "rejected_chunks": self.rejected_chunks[:8],
            "reasoning_trace": self.reasoning_trace,
        }


class RAGTimer:
    def __init__(self):
        self._start = time.perf_counter()
        self.stages: Dict[str, int] = {}

    def mark(self, stage: str) -> int:
        elapsed = int((time.perf_counter() - self._start) * 1000)
        self.stages[stage] = elapsed
        return elapsed

    @property
    def total_ms(self) -> int:
        return int((time.perf_counter() - self._start) * 1000)


def chunk_debug_row(chunk: Dict[str, Any]) -> Dict[str, Any]:
    meta = chunk.get("metadata") or {}
    return {
        "title": meta.get("title", ""),
        "category": meta.get("category") or meta.get("source", ""),
        "file": meta.get("file") or meta.get("path", ""),
        "score": round(float(chunk.get("score") or chunk.get("rrf_score") or 0), 4),
        "chunk_type": meta.get("chunk_type", ""),
        "preview": (chunk.get("text") or "")[:120],
    }


def should_include_debug(request=None) -> bool:
    if getattr(settings, "DEBUG_RAG", False):
        return True
    if request and getattr(request, "data", None):
        return bool(request.data.get("debug"))
    return False


def log_rag_query(
    query: str,
    user,
    trace: RetrievalTrace,
    answer: str = "",
    agent_id: str = "default",
    session_id: Optional[int] = None,
) -> None:
    """Persist RAGQueryLog when RAG_QUERY_LOGGING enabled."""
    if not getattr(settings, "RAG_QUERY_LOGGING", True):
        return
    try:
        from user_sessions.models import RAGQueryLog

        RAGQueryLog.objects.create(
            user=user if user and getattr(user, "is_authenticated", False) else None,
            session_id=session_id,
            query=query[:2000],
            agent_id=agent_id,
            top_chunks=[chunk_debug_row(c) for c in trace.retrieved_chunks[:12]],
            latency_ms=trace.latency_ms,
            token_usage=trace.token_usage,
            cache_hit=trace.cache_hit_embedding or trace.cache_hit_retrieval or trace.cache_hit_gpt,
            context_length=len(trace.context_sent_to_gpt or ""),
            answer_preview=(answer or "")[:500],
            debug_payload=trace.to_debug_dict() if getattr(settings, "DEBUG_RAG", False) else {},
        )
    except Exception as e:
        logger.warning("RAGQueryLog save failed: %s", e)
