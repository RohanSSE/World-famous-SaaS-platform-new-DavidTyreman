import logging
import os
from datetime import datetime, timezone

from celery import shared_task
from django.dispatch import Signal
from elasticsearch_dsl import connections
import requests

from brandgodfather.documents import BRANDGODFATHER_NODE_2_ALIAS
from brandgodfather.services.pdf_ingestion import PDFIngestionService
from brandgodfather.services.BrandBook_generator import BrandBook
from brandgodfather.services.orchestrator import QuestionOrchestrator
from brandgodfather.services.output_mode import OutputModeEngine
from brandgodfather.services.ragv2.orchestrator import run_coaching_pipeline

logger = logging.getLogger(__name__)

brandbook_generated = Signal()

OUTPUT_INDEX = "brandgodfather_output_content"


def _notify_brandbook_webhook(session_id, task_id, payload):
    url = os.getenv("BRANDGODFATHER_FRONTEND_WEBHOOK_URL", "").strip()
    if not url:
        return False

    resp = requests.post(
        url,
        json={
            "event": "brandbook_generated",
            "session_id": session_id,
            "task_id": task_id,
            "payload": payload,
        },
        timeout=10,
    )
    resp.raise_for_status()
    return True


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_backoff_max=120, retry_jitter=True, max_retries=5)
def ingest_pdf_task(self, pdf_path, metadata=None):
    """Ingest a BrandGodFather coaching PDF into brandgodfather_brand_chunks on Node 2."""
    metadata = metadata or {}
    logger.info("BrandGodFather PDF ingest started task=%s path=%s", self.request.id, pdf_path)

    service = PDFIngestionService()
    chunks = service.chunk_document(pdf_path, metadata=metadata)
    logger.info("BrandGodFather chunking complete path=%s chunks=%s", pdf_path, len(chunks))

    if not chunks:
        logger.warning("BrandGodFather ingest skipped path=%s reason=no_chunks", pdf_path)
        return {"pdf_path": pdf_path, "chunks": 0, "embedded": 0, "indexed": 0, "failed": 0}

    chunks = service.embed_chunks(chunks)
    logger.info("BrandGodFather embedding complete path=%s embeddings=%s", pdf_path, len(chunks))

    result = service.ingest_to_es(chunks)
    logger.info(
        "BrandGodFather ingest done path=%s success=%s failed=%s",
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
    """Run full BrandGodFather answer orchestration asynchronously."""
    logger.info(
        "BrandGodFather process_answer_async started task=%s session_id=%s q_id=%s",
        self.request.id,
        session_id,
        q_id,
    )
    orchestrator = QuestionOrchestrator()
    result = orchestrator.process_answer(session_id=session_id, q_id=q_id, user_answer=user_answer)
    payload = result.model_dump() if hasattr(result, "model_dump") else dict(result)
    logger.info(
        "BrandGodFather process_answer_async done task=%s session_id=%s q_id=%s status=%s",
        self.request.id,
        session_id,
        q_id,
        payload.get("status"),
    )
    return payload


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_backoff_max=120, retry_jitter=True, max_retries=3)
def process_answer_async_ragv2(self, session_state):
    """Run RAGv2 standalone coaching pipeline asynchronously."""
    logger.info(
        "BrandGodFather process_answer_async_ragv2 started task=%s session_id=%s question=%s",
        self.request.id,
        session_state.get("session_id"),
        session_state.get("current_question"),
    )
    result = run_coaching_pipeline(session_state=session_state)
    logger.info(
        "BrandGodFather process_answer_async_ragv2 done task=%s session_id=%s status=%s",
        self.request.id,
        session_state.get("session_id"),
        result.get("gate_status"),
    )
    return result


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_backoff_max=60, retry_jitter=True, max_retries=3)
def brand_type_determination_task(self, session_id):
    """Async hook after Q14 PASS for brand-type determination pipeline."""
    logger.info(
        "BrandGodFather brand_type_determination_task started task=%s session_id=%s",
        self.request.id,
        session_id,
    )
    # Placeholder for dedicated classifier pipeline integration.
    return {"session_id": session_id, "status": "queued_brand_type_determination"}


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_backoff_max=60, retry_jitter=True, max_retries=3)
def manifesto_generation_task(self, session_id):
    """Async hook after Q30 PASS for manifesto generation pipeline."""
    logger.info(
        "BrandGodFather manifesto_generation_task started task=%s session_id=%s",
        self.request.id,
        session_id,
    )
    # Placeholder for manifesto generation integration.
    return {"session_id": session_id, "status": "queued_manifesto_generation"}


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_backoff_max=120, retry_jitter=True, max_retries=3)
def generate_BrandBook_task(self, session_id):
    """Generate the BrandGodFather BrandBook after Q30 PASS and notify listeners."""
    logger.info(
        "BrandGodFather generate_BrandBook_task started task=%s session_id=%s",
        self.request.id,
        session_id,
    )
    generator = BrandBook()
    result = generator.generate(session_id=session_id)
    payload = result.model_dump() if hasattr(result, "model_dump") else dict(result)

    brandbook_generated.send(
        sender=generate_BrandBook_task,
        session_id=session_id,
        task_id=self.request.id,
        payload=payload,
    )

    try:
        delivered = _notify_brandbook_webhook(
            session_id=session_id,
            task_id=self.request.id,
            payload=payload,
        )
        logger.info(
            "BrandGodFather generate_BrandBook_task webhook session_id=%s delivered=%s",
            session_id,
            delivered,
        )
    except Exception as exc:
        logger.warning(
            "BrandGodFather generate_BrandBook_task webhook failed session_id=%s error=%s",
            session_id,
            exc,
        )

    logger.info(
        "BrandGodFather generate_BrandBook_task done task=%s session_id=%s final_score=%s",
        self.request.id,
        session_id,
        payload.get("final_score"),
    )
    return payload


def _iter_completed_q30_sessions(es):
    body = {
        "size": 500,
        "query": {"match_all": {}},
        "sort": [{"updated_at": {"order": "desc", "unmapped_type": "date"}}],
    }
    resp = es.search(index="brandgodfather_sessions", body=body)
    hits = resp.get("hits", {}).get("hits", [])
    for hit in hits:
        source = hit.get("_source", {})
        if OutputModeEngine.eligible_completed_session(source):
            yield source


def _store_output(es, session_id, content_type, content, brand_filter_result):
    now = datetime.now(timezone.utc).isoformat()
    week_number = int(datetime.now(timezone.utc).isocalendar().week)
    doc = {
        "session_id": session_id,
        "content_type": content_type,
        "content": content,
        "week_number": week_number,
        "brand_filter_result": brand_filter_result,
        "created_at": now,
    }
    doc_id = f"{session_id}:{content_type}:{now}"
    es.update(
        index=OUTPUT_INDEX,
        id=doc_id,
        body={"doc": doc, "doc_as_upsert": True},
        refresh=True,
    )


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_backoff_max=180, retry_jitter=True, max_retries=2)
def weekly_social_task(self):
    logger.info("BrandGodFather weekly_social_task started task=%s", self.request.id)
    es = connections.get_connection(alias=BRANDGODFATHER_NODE_2_ALIAS)
    engine = OutputModeEngine()
    generated = 0

    for session in _iter_completed_q30_sessions(es):
        session_id = str(session.get("session_id", "") or "")
        if not session_id:
            continue
        items = engine.generate_weekly_social(session_id=session_id)
        payload = [item.model_dump() for item in items]
        filter_payload = [item.get("brand_filter_result", {}) for item in payload]
        _store_output(es, session_id, "social", payload, filter_payload)
        generated += 1

    logger.info("BrandGodFather weekly_social_task done task=%s sessions=%s", self.request.id, generated)
    return {"sessions_generated": generated, "content_type": "social"}


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_backoff_max=180, retry_jitter=True, max_retries=2)
def monthly_campaign_task(self):
    logger.info("BrandGodFather monthly_campaign_task started task=%s", self.request.id)
    es = connections.get_connection(alias=BRANDGODFATHER_NODE_2_ALIAS)
    engine = OutputModeEngine()
    generated = 0

    for session in _iter_completed_q30_sessions(es):
        session_id = str(session.get("session_id", "") or "")
        if not session_id:
            continue
        idea = engine.generate_monthly_campaign(session_id=session_id)
        payload = idea.model_dump()
        _store_output(es, session_id, "campaign", payload, payload.get("brand_filter_result", {}))
        generated += 1

    logger.info("BrandGodFather monthly_campaign_task done task=%s sessions=%s", self.request.id, generated)
    return {"sessions_generated": generated, "content_type": "campaign"}


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_backoff_max=180, retry_jitter=True, max_retries=2)
def weekly_outreach_task(self):
    logger.info("BrandGodFather weekly_outreach_task started task=%s", self.request.id)
    es = connections.get_connection(alias=BRANDGODFATHER_NODE_2_ALIAS)
    engine = OutputModeEngine()
    generated = 0

    for session in _iter_completed_q30_sessions(es):
        session_id = str(session.get("session_id", "") or "")
        if not session_id:
            continue
        items = engine.generate_weekly_outreach(session_id=session_id)
        payload = [item.model_dump() for item in items]
        filter_payload = [item.get("brand_filter_result", {}) for item in payload]
        _store_output(es, session_id, "outreach", payload, filter_payload)
        generated += 1

    logger.info("BrandGodFather weekly_outreach_task done task=%s sessions=%s", self.request.id, generated)
    return {"sessions_generated": generated, "content_type": "outreach"}
