import logging

from celery import shared_task

from synapse.services.pdf_ingestion import PDFIngestionService
from synapse.services.orchestrator import QuestionOrchestrator

logger = logging.getLogger(__name__)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_backoff_max=120, retry_jitter=True, max_retries=5)
def ingest_pdf_task(self, pdf_path, metadata=None):
    """Ingest a Synapse coaching PDF into synapse_brand_chunks on Node 2."""
    metadata = metadata or {}
    logger.info("Synapse PDF ingest started task=%s path=%s", self.request.id, pdf_path)

    service = PDFIngestionService()
    chunks = service.chunk_document(pdf_path, metadata=metadata)
    logger.info("Synapse chunking complete path=%s chunks=%s", pdf_path, len(chunks))

    if not chunks:
        logger.warning("Synapse ingest skipped path=%s reason=no_chunks", pdf_path)
        return {"pdf_path": pdf_path, "chunks": 0, "embedded": 0, "indexed": 0, "failed": 0}

    chunks = service.embed_chunks(chunks)
    logger.info("Synapse embedding complete path=%s embeddings=%s", pdf_path, len(chunks))

    result = service.ingest_to_es(chunks)
    logger.info(
        "Synapse ingest done path=%s success=%s failed=%s",
        pdf_path,
        result.get("success", 0),
        result.get("failed", 0),
    )
    return {
        "pdf_path": pdf_path,
        "chunks": len(chunks),
        "embedded": len(chunks),
        "indexed": result.get("success", 0),
        "failed": result.get("failed", 0),
    }


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_backoff_max=120, retry_jitter=True, max_retries=3)
def process_answer_async(self, session_id, q_id, user_answer):
    """Run full Synapse answer orchestration asynchronously."""
    logger.info(
        "Synapse process_answer_async started task=%s session_id=%s q_id=%s",
        self.request.id,
        session_id,
        q_id,
    )
    orchestrator = QuestionOrchestrator()
    result = orchestrator.process_answer(session_id=session_id, q_id=q_id, user_answer=user_answer)
    payload = result.model_dump() if hasattr(result, "model_dump") else dict(result)
    logger.info(
        "Synapse process_answer_async done task=%s session_id=%s q_id=%s status=%s",
        self.request.id,
        session_id,
        q_id,
        payload.get("status"),
    )
    return payload


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_backoff_max=60, retry_jitter=True, max_retries=3)
def brand_type_determination_task(self, session_id):
    """Async hook after Q14 PASS for brand-type determination pipeline."""
    logger.info(
        "Synapse brand_type_determination_task started task=%s session_id=%s",
        self.request.id,
        session_id,
    )
    # Placeholder for dedicated classifier pipeline integration.
    return {"session_id": session_id, "status": "queued_brand_type_determination"}


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_backoff_max=60, retry_jitter=True, max_retries=3)
def manifesto_generation_task(self, session_id):
    """Async hook after Q30 PASS for manifesto generation pipeline."""
    logger.info(
        "Synapse manifesto_generation_task started task=%s session_id=%s",
        self.request.id,
        session_id,
    )
    # Placeholder for manifesto generation integration.
    return {"session_id": session_id, "status": "queued_manifesto_generation"}
