#!/usr/bin/env python
"""
Pilot readiness smoke test — health, observability, chunk audit (no full golden).

Usage:
  python scripts/pilot_smoke_test.py
  BASE_URL=http://127.0.0.1:8000 TOKEN=eyJ... python scripts/pilot_smoke_test.py
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request

BASE = os.environ.get("BASE_URL", "http://127.0.0.1:8000").rstrip("/")
TOKEN = os.environ.get("TOKEN", "")


def get(path: str, auth: bool = False) -> tuple:
    headers = {}
    if auth and TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    req = urllib.request.Request(f"{BASE}{path}", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, json.loads(r.read().decode())
    except Exception as e:
        return 0, {"error": str(e)}


def main() -> int:
    checks = []
    code, body = get("/api/health/")
    checks.append(("health", code == 200 and body.get("checks", {}).get("database") == "ok"))

    if TOKEN:
        code, body = get("/api/sessions/product-observability/", auth=True)
        checks.append(("observability", code == 200 and "golden_passed" in body))
        code, body = get("/api/sessions/rag-system-health/", auth=True)
        checks.append(("rag_health", code == 200))
    else:
        print("Skip auth endpoints (set TOKEN=JWT for full pilot check)")

    print("Pilot smoke test")
    failed = 0
    for name, ok in checks:
        status = "OK" if ok else "FAIL"
        print(f"  [{status}] {name}")
        if not ok:
            failed += 1
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
