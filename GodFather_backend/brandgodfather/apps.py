from django.apps import AppConfig


class BrandGodFatherConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "brandgodfather"
    verbose_name = "BrandGodFather Brand Coaching"

    def ready(self):
        """
        Load all three ML models once at server startup and wire them into
        the ProsodyClassifier singleton.  Skipped in Celery worker processes
        where DJANGO_SETTINGS_MODULE is set but model loading is unnecessary.
        """
        import os

        # Don't load heavy models during management commands that don't need them
        # (migrate, collectstatic, etc.).  The environment variable check is an
        # escape hatch; omit it to always preload.
        if os.environ.get("SKIP_PROSODY_PRELOAD", "").lower() in ("1", "true", "yes"):
            return

        try:
            self._load_prosody_models()
        except Exception as exc:  # noqa: BLE001
            import logging
            logging.getLogger(__name__).warning(
                "ProsodyClassifier failed to preload models: %s", exc
            )

        if os.environ.get("SKIP_RAG_PRELOAD", "").lower() not in ("1", "true", "yes"):
            try:
                self._load_rag_models()
            except Exception as exc:  # noqa: BLE001
                import logging
                logging.getLogger(__name__).warning(
                    "HybridRAG cross-encoder preload failed: %s", exc
                )

    # ------------------------------------------------------------------

    def _load_prosody_models(self):
        import logging
        log = logging.getLogger(__name__)

        # 1. spaCy
        try:
            import spacy
            nlp = spacy.load("en_core_web_sm")
            log.info("spaCy en_core_web_sm loaded.")
        except Exception as exc:
            log.warning("spaCy load failed: %s", exc)
            nlp = None

        # 2. Sentence-Transformers
        try:
            from sentence_transformers import SentenceTransformer
            sentence_model = SentenceTransformer("all-MiniLM-L6-v2")
            log.info("SentenceTransformer all-MiniLM-L6-v2 loaded.")
        except Exception as exc:
            log.warning("SentenceTransformer load failed: %s", exc)
            sentence_model = None

        # 3. HuggingFace emotion pipeline
        try:
            from transformers import pipeline
            emotion_pipeline = pipeline(
                "text-classification",
                model="j-hartmann/emotion-english-distilroberta-base",
                top_k=None,
            )
            log.info("Emotion pipeline j-hartmann loaded.")
        except Exception as exc:
            log.warning("Emotion pipeline load failed: %s", exc)
            emotion_pipeline = None

        if nlp is None or sentence_model is None or emotion_pipeline is None:
            log.warning(
                "One or more ProsodyClassifier models unavailable — "
                "classifier will not be registered."
            )
            return

        from brandgodfather.services.prosody_classifier import ProsodyClassifier, set_classifier
        classifier = ProsodyClassifier(
            spacy_model=nlp,
            sentence_model=sentence_model,
            emotion_pipeline=emotion_pipeline,
        )
        set_classifier(classifier)
        log.info("ProsodyClassifier singleton registered.")

    def _load_rag_models(self):
        import logging

        log = logging.getLogger(__name__)

        try:
            from sentence_transformers import CrossEncoder

            model_name = "cross-encoder/ms-marco-MiniLM-L-6-v2"
            cross_encoder = CrossEncoder(model_name)
            from brandgodfather.services.rag_retrieval import set_cross_encoder

            set_cross_encoder(cross_encoder)
            log.info("HybridRAG CrossEncoder loaded: %s", model_name)
        except Exception as exc:
            log.warning("CrossEncoder load failed: %s", exc)
