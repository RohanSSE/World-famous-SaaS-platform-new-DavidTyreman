import logging



from celery import shared_task



logger = logging.getLogger(__name__)





@shared_task

def rebuild_ai_knowledge_index_task(force=False):

    """

    Celery: rebuild Rag_doc → embeddings → Elasticsearch ai_knowledge index.

    Skips work when fingerprint unchanged unless force=True.

    """

    from utils.ai_knowledge_auto import run_build_with_state



    logger.info("AI knowledge auto-index task started (force=%s)", force)

    success, message = run_build_with_state(force=force)

    if not success:

        logger.error("AI knowledge index build failed: %s", message)

    else:

        logger.info("AI knowledge index build OK: %s", message)

    return {"success": success, "message": message}





@shared_task(bind=True)

def generate_manifesto_task(self, session_id: int, user_id: int):

    """Async manifesto generation (Phase 6)."""

    from user_sessions.services.ai_generation_service import run_manifesto_generation



    logger.info("Manifesto task %s session=%s", self.request.id, session_id)

    return run_manifesto_generation(session_id, user_id)





@shared_task(bind=True)

def generate_session_summary_task(self, session_id: int, user_id: int):

    """Async full brand summary."""

    from user_sessions.services.ai_generation_service import run_session_summary_generation



    logger.info("Summary task %s session=%s", self.request.id, session_id)

    return run_session_summary_generation(session_id, user_id)





@shared_task(bind=True)

def generate_foundation_summary_task(self, session_id: int, user_id: int):

    """Async foundation summary."""

    from user_sessions.services.ai_generation_service import run_foundation_summary_generation



    logger.info("Foundation summary task %s session=%s", self.request.id, session_id)

    return run_foundation_summary_generation(session_id, user_id)


@shared_task
def run_rag_evaluation_nightly_task():
    """Nightly RAG regression evaluation (Phase 15)."""
    import os
    import subprocess
    import sys

    env = {**os.environ, "EVAL_RUN_TYPE": "nightly", "DJANGO_SKIP_KNOWLEDGE_AUTO": "1"}
    script = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts", "run_rag_evaluation.py")
    result = subprocess.run(
        [sys.executable, script],
        cwd=os.path.dirname(os.path.dirname(__file__)),
        env=env,
        capture_output=True,
        text=True,
        timeout=3600,
    )
    logger.info("RAG evaluation nightly exit=%s", result.returncode)
    if result.stdout:
        logger.info(result.stdout[-2000:])
    if result.returncode != 0 and result.stderr:
        logger.error(result.stderr[-2000:])
    return {"returncode": result.returncode}


@shared_task
def analyze_failures_nightly_task():
    """Nightly failure cluster mining for sprint planning."""
    import os
    import subprocess
    import sys

    env = {**os.environ, "DJANGO_SKIP_KNOWLEDGE_AUTO": "1"}
    script = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts", "analyze_failures.py")
    out = os.path.join(os.path.dirname(os.path.dirname(__file__)), "evaluation", "failure_clusters_auto.md")
    result = subprocess.run(
        [sys.executable, script, "--write", out],
        cwd=os.path.dirname(os.path.dirname(__file__)),
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    logger.info("Failure analysis nightly exit=%s", result.returncode)
    return {"returncode": result.returncode, "output": (result.stdout or "")[-1500:]}


@shared_task
def decay_brand_memory_importance_task():
    """Nightly: decay importance_score on stale brand memories (Phase 14)."""
    from utils.pgvector_retrieval import apply_importance_decay

    updated = apply_importance_decay(days_half_life=30)
    logger.info("Brand memory importance decay: %s rows updated", updated)
    return {"updated": updated}


@shared_task
def compress_brand_memories_task(session_id: int):
    """Compress many session memories into one strategic summary (Phase 14)."""
    from utils.pgvector_retrieval import compress_session_memories

    summary = compress_session_memories(session_id)
    logger.info("Memory compression session=%s: %s", session_id, bool(summary))
    return {"session_id": session_id, "compressed": bool(summary)}
