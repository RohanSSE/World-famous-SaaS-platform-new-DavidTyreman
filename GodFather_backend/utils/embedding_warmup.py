"""Warm Azure embedding + cross-encoder on startup to cut first-token latency."""
from __future__ import annotations

import logging
import threading

logger = logging.getLogger(__name__)
_warmed = False


def warmup_ai_models(async_mode: bool = True) -> None:
    global _warmed
    if _warmed:
        return

    def _run():
        global _warmed
        try:
            from django.conf import settings

            if not getattr(settings, "RAG_EMBEDDING_WARMUP", True):
                return
            from document.utils.embedding_service import EmbeddingService

            svc = EmbeddingService()
            svc.generate_embedding("warmup brand strategy retrieval")
            logger.info("Embedding warmup complete")

            if getattr(settings, "RAG_CROSS_ENCODER_ENABLED", False):
                from utils.rerank_knowledge import _get_cross_encoder

                _get_cross_encoder()
                logger.info("Cross-encoder warmup complete")
            _warmed = True
        except Exception as e:
            logger.warning("AI model warmup skipped: %s", e)

    if async_mode:
        threading.Thread(target=_run, daemon=True, name="ai-warmup").start()
    else:
        _run()
