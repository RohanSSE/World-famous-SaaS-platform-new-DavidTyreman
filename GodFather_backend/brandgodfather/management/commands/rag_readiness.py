import json

import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from elasticsearch import Elasticsearch

from brandgodfather.services.ragv2 import discovery_metadata as dm


class Command(BaseCommand):
    help = "Print one-line readiness for phase-questions JSON, Elasticsearch, and discovery metadata generation"

    def handle(self, *args, **options):
        phase_url = getattr(settings, "PHASE_QUESTIONS_API_URL", "http://localhost:4001/phase-questions/")

        phase_ok = False
        phase_count = 0
        phase_note = ""
        try:
            phase_resp = requests.get(phase_url, timeout=8)
            phase_resp.raise_for_status()
            payload = phase_resp.json()
            if isinstance(payload, list):
                phase_count = len(payload)
            elif isinstance(payload, dict):
                phase_count = len(payload.get("results") or payload.get("data") or payload.get("questions") or [])
            else:
                phase_count = 0
            phase_ok = True
        except Exception as exc:
            phase_note = str(exc).split("\n", 1)[0]

        es_ok = False
        es_status = "unknown"
        try:
            hosts = getattr(settings, "ELASTICSEARCH_DSL", {}).get("default", {}).get("hosts", "http://localhost:9200")
            es = Elasticsearch(hosts)
            es_ok = bool(es.ping())
            if es_ok:
                es_status = es.cluster.health().body.get("status", "unknown")
        except Exception as exc:
            es_status = f"error:{str(exc).splitlines()[0]}"

        metadata_ok = False
        metadata_segment = ""
        metadata_fetch_ok = False
        metadata_error = ""
        try:
            original_llm_json = dm._llm_json
            dm._llm_json = lambda system_prompt, user_prompt, default: {}
            try:
                data = dm.build_discovery_metadata(
                    session_id="readiness-check",
                    q_id="Q1",
                    raw_answer="Readiness probe answer.",
                )
            finally:
                dm._llm_json = original_llm_json

            metadata_ok = isinstance(data, dict) and "phase_1_segment" in data
            metadata_segment = str(data.get("phase_1_segment", ""))
            metadata_fetch_ok = bool(((data.get("live_questions") or {}).get("fetch_ok")))
        except Exception as exc:
            metadata_error = str(exc).split("\n", 1)[0]

        readiness = {
            "phase_questions_json": {
                "ok": phase_ok,
                "url": phase_url,
                "count": phase_count,
                "note": phase_note,
            },
            "elasticsearch": {
                "ok": es_ok,
                "status": es_status,
            },
            "discovery_metadata": {
                "ok": metadata_ok,
                "segment": metadata_segment,
                "live_fetch_ok": metadata_fetch_ok,
                "error": metadata_error,
            },
        }

        one_line = (
            "RAG_READINESS "
            f"phase_json={'ok' if phase_ok else 'fail'}(count={phase_count}) "
            f"es={'ok' if es_ok else 'fail'}(status={es_status}) "
            f"metadata={'ok' if metadata_ok else 'fail'}(segment={metadata_segment or '-'},live_fetch_ok={metadata_fetch_ok})"
        )

        self.stdout.write(one_line)
        self.stdout.write(json.dumps(readiness, ensure_ascii=True))