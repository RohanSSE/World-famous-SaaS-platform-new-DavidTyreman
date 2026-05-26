#!/usr/bin/env python
"""Audit knowledge chunk corpus — weak / duplicate / generic detection."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import django

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
os.environ.setdefault("DJANGO_SKIP_KNOWLEDGE_AUTO", "1")
django.setup()

from user_sessions.services.chunk_quality_audit import audit_chunks  # noqa: E402


def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    report = audit_chunks(limit=limit)
    out = ROOT / "evaluation" / "chunk_quality_report.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Scanned: {report['chunks_scanned']}")
    print(f"Weak: {report['weak_chunk_count']} | Generic: {report['generic_chunk_count']} | Dup snippets: {report['duplicate_snippet_count']}")
    print(report["recommendation"])
    print(f"Saved {out}")


if __name__ == "__main__":
    main()
