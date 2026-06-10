from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from elasticsearch.helpers import scan
from elasticsearch_dsl import connections

from brandgodfather.documents import BRANDGODFATHER_NODE_2_ALIAS


INDICES = [
    "brandgodfather_sessions",
    "brandgodfather_episodic",
    "brandgodfather_chunks_v2",
    "brandgodfather_brand_chunks",
]


class Command(BaseCommand):
    help = "Backup RAGv2 indices/embeddings to RAGprocessdata folder as JSONL snapshots."

    def add_arguments(self, parser):
        parser.add_argument("--output-dir", default=str(Path(settings.BASE_DIR) / "RAGprocessdata"), help="Backup directory path")

    def handle(self, *args, **options):
        out_dir = Path(options["output_dir"]).expanduser().resolve()
        out_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        es = connections.get_connection(alias=BRANDGODFATHER_NODE_2_ALIAS)

        summary = []
        for index_name in INDICES:
            if not es.indices.exists(index=index_name):
                self.stdout.write(self.style.WARNING(f"Skip missing index: {index_name}"))
                continue

            path = out_dir / f"{index_name}_{timestamp}.jsonl"
            count = 0
            with path.open("w", encoding="utf-8") as fh:
                for hit in scan(es, index=index_name, query={"query": {"match_all": {}}}, size=1000):
                    row = {
                        "_id": hit.get("_id"),
                        "_index": hit.get("_index"),
                        "_source": hit.get("_source", {}),
                    }
                    fh.write(json.dumps(row, ensure_ascii=False) + "\n")
                    count += 1

            summary.append({"index": index_name, "count": count, "file": str(path)})
            self.stdout.write(self.style.SUCCESS(f"Backed up {index_name}: {count} docs"))

        manifest = out_dir / f"ragv2_backup_manifest_{timestamp}.json"
        manifest.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        self.stdout.write(self.style.SUCCESS(f"Backup manifest: {manifest}"))
