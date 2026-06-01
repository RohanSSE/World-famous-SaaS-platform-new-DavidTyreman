from django.core.management.base import BaseCommand
from elastic_transport import ConnectionError as ESConnectionError
from elasticsearch import ApiError
from elasticsearch_dsl import connections

from synapse.documents import (
    SYNAPSE_NODE_2_ALIAS,
    SynapseBrandChunkDocument,
    SynapseEpisodicDocument,
    SynapseSessionDocument,
)


class Command(BaseCommand):
    help = "Create Synapse Elasticsearch indices on Node 2"

    def handle(self, *args, **options):
        es = connections.get_connection(alias=SYNAPSE_NODE_2_ALIAS)

        docs = [
            SynapseBrandChunkDocument,
            SynapseSessionDocument,
            SynapseEpisodicDocument,
        ]

        self.stdout.write(self.style.MIGRATE_HEADING("Creating Synapse indices on ES Node 2"))

        created = []
        for doc_cls in docs:
            index_name = doc_cls.Index.name
            try:
                doc_cls.init(using=SYNAPSE_NODE_2_ALIAS)
            except (ApiError, ESConnectionError) as exc:
                self.stderr.write(
                    self.style.ERROR(
                        f"Failed to initialize index {index_name} on Node 2: {exc}"
                    )
                )
                return
            created.append(index_name)
            self.stdout.write(self.style.SUCCESS(f"Initialized index: {index_name}"))

        self.stdout.write(self.style.MIGRATE_LABEL("\nSynapse index summary"))
        for name in created:
            try:
                present = bool(es.indices.exists(index=name))
            except (ApiError, ESConnectionError):
                present = False
            status = "present" if present else "missing"
            style = self.style.SUCCESS if present else self.style.WARNING
            self.stdout.write(style(f"- {name}: {status}"))

        self.stdout.write(self.style.SUCCESS("Completed create_synapse_indices."))
