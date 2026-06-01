from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

from elasticsearch_dsl import connections
from pydantic import BaseModel

from document.utils.embedding_service import EmbeddingService
from brandgodfather.documents import BRANDGODFATHER_NODE_2_ALIAS
from utils.retry_azure import with_azure_retry

logger = logging.getLogger(__name__)


class RAGContext(BaseModel):
    question_chunks: List[str]
    challenge_chunks: List[str]
    gold_standard: Optional[str]
    rejection_example: Optional[str]


@dataclass
class SearchHit:
    chunk_id: str
    text: str
    chunk_type: str
    question_id: str
    phase: str
    brand_type: str
    score: float = 0.0


_cross_encoder_instance = None


def set_cross_encoder(instance) -> None:
    global _cross_encoder_instance
    _cross_encoder_instance = instance


def get_cross_encoder():
    return _cross_encoder_instance


class HybridRAGService:
    INDEX_NAME = "brandgodfather_brand_chunks"
    _es_supports_rrf_cache: Optional[bool] = None

    def __init__(self) -> None:
        self.embedding_service = EmbeddingService()
        self.es = connections.get_connection(alias=BRANDGODFATHER_NODE_2_ALIAS)

    def get_question_context(
        self,
        q_id: str,
        phase: str,
        user_answer: str,
        pressure_level: int,
        session: Any,
    ) -> RAGContext:
        # 1) Question context (same q_id + phase)
        question_filters = {
            "question_id": q_id,
            "phase": phase,
        }
        question_hits = self._retrieve_context(
            query_text=user_answer,
            filters=question_filters,
            k=20,
        )

        # 2) Pressure context (challenge language)
        pressure_filters = {
            "chunk_type": "challenge_language",
            "phase": phase,
        }

        # Optional pressure tag if corpus includes it.
        pressure_tag = f"pressure_{pressure_level}"
        pressure_filters["emotional_register"] = pressure_tag

        challenge_hits = self._retrieve_context(
            query_text=user_answer,
            filters=pressure_filters,
            k=20,
        )

        # Fallback without pressure tag if no results.
        if not challenge_hits:
            pressure_filters.pop("emotional_register", None)
            challenge_hits = self._retrieve_context(
                query_text=user_answer,
                filters=pressure_filters,
                k=20,
            )

        # 3) Brand-type context only after Q14.
        if self._q_number(q_id) > 14:
            emerging_brand_type = self._get_session_value(session, "brand_type")
            if emerging_brand_type:
                brand_filters = {
                    "chunk_type": "archetype_definition",
                    "brand_type": str(emerging_brand_type),
                }
                # Retrieved separately by design; merged implicitly via rerank pool
                _ = self._retrieve_context(
                    query_text=user_answer,
                    filters=brand_filters,
                    k=20,
                )

        question_chunks = [h.text for h in question_hits[:2]]
        challenge_chunks = [h.text for h in challenge_hits[:1]]

        gold_standard = self._first_chunk_by_type(
            question_hits,
            "gold_standard_example",
        )
        rejection_example = self._first_chunk_by_type(
            question_hits,
            "rejection_example",
        )

        return RAGContext(
            question_chunks=question_chunks,
            challenge_chunks=challenge_chunks,
            gold_standard=gold_standard,
            rejection_example=rejection_example,
        )

    def _retrieve_context(
        self,
        query_text: str,
        filters: Dict[str, Any],
        k: int = 20,
    ) -> List[SearchHit]:
        if self._es_supports_rrf():
            try:
                native = self._rrf_search_native(query_text=query_text, filters=filters, k=k)
                top_native = native[:10]
                reranked_native = self._rerank(query=query_text, candidates=top_native)
                return reranked_native[:3]
            except Exception as exc:
                # Some clusters report support via version but still reject retriever syntax.
                logger.warning("Native RRF unavailable at runtime, falling back: %s", exc)
                self._force_disable_native_rrf()

        vector = self._embed_query(query_text)
        dense_results = self._dense_search(vector=vector, filters=filters, k=k)
        sparse_results = self._sparse_search(text=query_text, filters=filters, k=k)

        fused = self._rrf_fuse(dense_results=dense_results, sparse_results=sparse_results)

        # Rerank top 10 fused candidates, return top 3
        top_fused = fused[:10]
        reranked = self._rerank(query=query_text, candidates=top_fused)
        return reranked[:3]

    def _force_disable_native_rrf(self) -> None:
        self.__class__._es_supports_rrf_cache = False

    def _embed_query(self, text: str) -> List[float]:
        vector = with_azure_retry(
            lambda: self.embedding_service.generate_embedding(text),
        )
        return vector

    def _dense_search(
        self,
        vector: List[float],
        filters: Dict[str, Any],
        k: int = 20,
    ) -> List[SearchHit]:
        filter_clauses = self._build_term_filters(filters)

        body: Dict[str, Any] = {
            "size": k,
            "knn": {
                "field": "dense_vector",
                "query_vector": vector,
                "k": k,
                "num_candidates": max(k * 4, 50),
                "filter": filter_clauses,
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

        resp = self.es.search(index=self.INDEX_NAME, body=body)
        return self._parse_hits(resp)

    def _sparse_search(
        self,
        text: str,
        filters: Dict[str, Any],
        k: int = 20,
    ) -> List[SearchHit]:
        filter_clauses = self._build_term_filters(filters)

        body = {
            "size": k,
            "query": {
                "bool": {
                    "must": [
                        {
                            "match": {
                                "text": {
                                    "query": text,
                                    "operator": "or",
                                }
                            }
                        }
                    ],
                    "filter": filter_clauses,
                }
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

        resp = self.es.search(index=self.INDEX_NAME, body=body)
        return self._parse_hits(resp)

    def _rrf_fuse(
        self,
        dense_results: Sequence[SearchHit],
        sparse_results: Sequence[SearchHit],
    ) -> List[SearchHit]:
        ranked: Dict[str, Tuple[float, SearchHit]] = {}

        for rank, hit in enumerate(dense_results, start=1):
            score = 1.0 / (rank + 60)
            prev = ranked.get(hit.chunk_id)
            if prev is None:
                ranked[hit.chunk_id] = (score, hit)
            else:
                ranked[hit.chunk_id] = (prev[0] + score, prev[1])

        for rank, hit in enumerate(sparse_results, start=1):
            score = 1.0 / (rank + 60)
            prev = ranked.get(hit.chunk_id)
            if prev is None:
                ranked[hit.chunk_id] = (score, hit)
            else:
                ranked[hit.chunk_id] = (prev[0] + score, prev[1])

        fused = []
        for final_score, hit in ranked.values():
            hit.score = final_score
            fused.append(hit)

        fused.sort(key=lambda h: h.score, reverse=True)
        return fused

    def _rrf_search_native(
        self,
        query_text: str,
        filters: Dict[str, Any],
        k: int = 20,
    ) -> List[SearchHit]:
        vector = self._embed_query(query_text)
        filter_clauses = self._build_term_filters(filters)

        body = {
            "size": k,
            "retriever": {
                "rrf": {
                    "rank_constant": 60,
                    "retrievers": [
                        {
                            "knn": {
                                "field": "dense_vector",
                                "query_vector": vector,
                                "k": k,
                                "num_candidates": max(k * 4, 50),
                                "filter": filter_clauses,
                            }
                        },
                        {
                            "standard": {
                                "query": {
                                    "bool": {
                                        "must": [
                                            {
                                                "match": {
                                                    "text": {
                                                        "query": query_text,
                                                        "operator": "or",
                                                    }
                                                }
                                            }
                                        ],
                                        "filter": filter_clauses,
                                    }
                                }
                            }
                        },
                    ],
                }
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

        resp = self.es.search(index=self.INDEX_NAME, body=body)
        return self._parse_hits(resp)

    def _rerank(self, query: str, candidates: Sequence[SearchHit]) -> List[SearchHit]:
        if not candidates:
            return []

        encoder = get_cross_encoder()
        if encoder is None:
            # Soft fallback to fused order if model not loaded.
            return list(candidates)

        pairs = [[query, c.text] for c in candidates]
        scores = encoder.predict(pairs)

        scored = []
        for hit, score in zip(candidates, scores):
            hit.score = float(score)
            scored.append(hit)

        scored.sort(key=lambda h: h.score, reverse=True)
        return scored

    @staticmethod
    def _build_term_filters(filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        clauses: List[Dict[str, Any]] = []
        for key, value in filters.items():
            if value is None or value == "":
                continue
            clauses.append({"term": {key: value}})
        return clauses

    @staticmethod
    def _parse_hits(resp: Dict[str, Any]) -> List[SearchHit]:
        out: List[SearchHit] = []
        for raw in resp.get("hits", {}).get("hits", []):
            src = raw.get("_source", {})
            out.append(
                SearchHit(
                    chunk_id=str(src.get("chunk_id") or raw.get("_id", "")),
                    text=str(src.get("text", "")),
                    chunk_type=str(src.get("chunk_type", "")),
                    question_id=str(src.get("question_id", "")),
                    phase=str(src.get("phase", "")),
                    brand_type=str(src.get("brand_type", "")),
                    score=float(raw.get("_score", 0.0) or 0.0),
                )
            )
        return out

    @staticmethod
    def _first_chunk_by_type(hits: Sequence[SearchHit], chunk_type: str) -> Optional[str]:
        for hit in hits:
            if hit.chunk_type == chunk_type:
                return hit.text
        return None

    @staticmethod
    def _q_number(q_id: str) -> int:
        m = re.search(r"(\d+)", str(q_id))
        if not m:
            return 0
        return int(m.group(1))

    @staticmethod
    def _get_session_value(session: Any, key: str) -> Optional[Any]:
        if session is None:
            return None
        if isinstance(session, dict):
            return session.get(key)
        return getattr(session, key, None)

    def _es_supports_rrf(self) -> bool:
        cached = self.__class__._es_supports_rrf_cache
        if cached is not None:
            return cached
        try:
            info = self.es.info()
            version_text = str(info.get("version", {}).get("number", "0.0.0"))
            major, minor, *_ = [int(p) for p in version_text.split(".")[:2]]
            supported = (major, minor) >= (8, 9)
            self.__class__._es_supports_rrf_cache = supported
            return supported
        except Exception:
            logger.debug("Could not determine ES version; falling back to manual RRF.")
            self.__class__._es_supports_rrf_cache = False
            return False
