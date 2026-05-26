"""
Build or refresh the AI knowledge Elasticsearch index.

Auto mode (default): only rebuilds when Rag_doc files changed or index missing.
Use --force to always rebuild. Use --sync to run in-process (no Celery).
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "Build/refresh AI knowledge index from Rag_doc/. "
        "Auto-skips if already up to date unless --force."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Rebuild even if fingerprint unchanged',
        )
        parser.add_argument(
            '--sync',
            action='store_true',
            help='Run in this process (do not enqueue Celery)',
        )
        parser.add_argument(
            '--status',
            action='store_true',
            help='Show index state only, do not build',
        )

    def handle(self, *args, **options):
        from utils.ai_knowledge_config import AI_KNOWLEDGE_INDEX_NAME
        from utils.ai_knowledge_auto import (
            compute_knowledge_fingerprint,
            elasticsearch_index_exists,
            ensure_index_current,
            load_index_state,
            needs_rebuild,
            run_build_with_state,
        )

        if options['status']:
            from utils.rag_doc_loader import discover_rag_doc_files
            from utils.chunk_knowledge import load_and_chunk_all

            state = load_index_state()
            should, reason = needs_rebuild(force=False)
            files = discover_rag_doc_files()
            chunks = load_and_chunk_all()

            self.stdout.write(self.style.MIGRATE_HEADING("AI Knowledge Index Status"))
            self.stdout.write(f"Rag_doc source files: {len(files)}")
            for path, cat in files:
                self.stdout.write(f"  - [{cat}] {path.name}")
            self.stdout.write(f"Chunks if indexed now: {len(chunks)}")
            self.stdout.write(f"ES index '{AI_KNOWLEDGE_INDEX_NAME}' exists: {elasticsearch_index_exists()}")
            self.stdout.write(f"Current fingerprint: {compute_knowledge_fingerprint()[:32]}...")
            self.stdout.write(f"Stored fingerprint: {(state.get('fingerprint') or 'none')[:32]}")
            self.stdout.write(f"Status: {state.get('status', 'unknown')}")
            self.stdout.write(f"Indexed chunks (last build): {state.get('chunk_count', 0)}")
            self.stdout.write(f"Last built: {state.get('last_built_at', 'never')}")
            self.stdout.write(f"Last message: {state.get('last_message', '-')}")
            if state.get('error'):
                self.stdout.write(self.style.ERROR(f"Last error: {state.get('error')}"))
            self.stdout.write(f"Needs rebuild: {should} ({reason})")

            try:
                from elasticsearch import Elasticsearch
                es = Elasticsearch(["http://localhost:9200"], request_timeout=5)
                if es.indices.exists(index=AI_KNOWLEDGE_INDEX_NAME):
                    count = es.count(index=AI_KNOWLEDGE_INDEX_NAME)["count"]
                    self.stdout.write(self.style.SUCCESS(f"ES document count in ai_knowledge: {count}"))
                else:
                    self.stdout.write(self.style.WARNING("ES: ai_knowledge index not found"))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"ES direct check: {e}"))
            return

        if options['sync'] or options['force']:
            success, message = run_build_with_state(force=options['force'])
        else:
            ok, message = ensure_index_current(async_build=True, force=False)
            if message.startswith('enqueued'):
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Rebuild queued via Celery ({message}). "
                        "Run: celery -A project worker -l info"
                    )
                )
                return
            success, message = ok, message

        if success:
            self.stdout.write(self.style.SUCCESS(message))
        else:
            self.stderr.write(self.style.ERROR(message))
