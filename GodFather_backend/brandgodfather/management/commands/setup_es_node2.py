from __future__ import annotations

from django.core.management.base import BaseCommand
from elastic_transport import ConnectionError as ESConnectionError
from elasticsearch import ApiError
from elasticsearch_dsl import connections

from brandgodfather.documents import BRANDGODFATHER_NODE_2_ALIAS


RAGV2_INDICES = {
    "brandgodfather_sessions": {
        "mappings": {
            "properties": {
                "session_id": {"type": "keyword"},
                "user_id": {"type": "keyword"},
                "question_id": {"type": "integer"},
                "raw_answer": {"type": "text"},
                "answer_embedding": {"type": "dense_vector", "dims": 768, "index": True, "similarity": "cosine"},
                "prosody_flags": {"type": "object"},
                "emotional_weight": {"type": "float"},
                "resistance_level": {"type": "keyword"},
                "brand_seed": {"type": "keyword"},
                "phase": {"type": "keyword"},
                "gate_status": {"type": "keyword"},
                "document_type": {"type": "keyword"},
                "timestamp": {"type": "date"},
            }
        }
    },
    "brandgodfather_episodic": {
        "mappings": {
            "properties": {
                "session_id": {"type": "keyword"},
                "memory_type": {"type": "keyword"},
                "brand_seed": {"type": "keyword"},
                "thread_index": {"type": "object"},
                "shadow_profile": {"type": "object"},
                "pressure_state": {"type": "object"},
                "resistance_count": {"type": "object"},
                "three_word_foundation": {"type": "object"},
                "emotional_register": {"type": "keyword"},
                "question_reference": {"type": "integer"},
                "timestamp": {"type": "date"},
            }
        }
    },
    "brandgodfather_chunks_v2": {
        "mappings": {
            "properties": {
                "chunk_id": {"type": "keyword"},
                "source_file": {"type": "keyword"},
                "content": {"type": "text"},
                "chunk_type": {"type": "keyword"},
                "phase": {"type": "keyword"},
                "question_id": {"type": "integer"},
                "brand_type": {"type": "keyword"},
                "emotional_register": {"type": "keyword"},
                "pressure_level": {"type": "integer"},
                "chunk_embedding": {"type": "dense_vector", "dims": 768, "index": True, "similarity": "cosine"},
            }
        }
    },
}


class Command(BaseCommand):
    help = "Create RAGv2 Node-2 Elasticsearch indices if missing (no overwrite)."

    def handle(self, *args, **options):
        es = connections.get_connection(alias=BRANDGODFATHER_NODE_2_ALIAS)
        self.stdout.write(self.style.MIGRATE_HEADING("Setting up RAGv2 indices on ES Node 2"))

        for index_name, body in RAGV2_INDICES.items():
            try:
                if es.indices.exists(index=index_name):
                    self.stdout.write(self.style.WARNING(f"Skip existing index: {index_name}"))
                    continue
                es.indices.create(index=index_name, body=body)
                self.stdout.write(self.style.SUCCESS(f"Created index: {index_name}"))
            except (ApiError, ESConnectionError) as exc:
                self.stderr.write(self.style.ERROR(f"Failed index {index_name}: {exc}"))
                return

        self.stdout.write(self.style.SUCCESS("RAGv2 Node-2 index setup complete."))
