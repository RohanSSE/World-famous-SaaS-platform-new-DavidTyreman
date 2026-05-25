import logging

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class SessionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'user_sessions'

    def ready(self):
        from utils.ai_knowledge_auto import should_run_startup_hook, enqueue_rebuild

        if not should_run_startup_hook():
            return
        try:
            if enqueue_rebuild(force=False):
                logger.info("AI knowledge auto-index queued on startup")
        except Exception as e:
            logger.warning("AI knowledge startup enqueue failed: %s", e)

        try:
            from utils.embedding_warmup import warmup_ai_models

            warmup_ai_models(async_mode=True)
        except Exception as e:
            logger.warning("Embedding warmup enqueue failed: %s", e)
