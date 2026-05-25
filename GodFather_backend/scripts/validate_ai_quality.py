#!/usr/bin/env python
"""
AI Quality Validation — retrieval, latency, strategic queries, evaluation baseline.

Usage:
  python scripts/validate_ai_quality.py
  python scripts/validate_ai_quality.py --skip-eval   # skip slow GPT eval cases
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import django

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
os.environ.setdefault("DJANGO_SKIP_KNOWLEDGE_AUTO", "1")
django.setup()

from django.conf import settings  # noqa: E402

from user_sessions.services.reasoning_orchestrator import run_planner_entry  # noqa: E402
from user_sessions.services.rag_service import (  # noqa: E402
    extract_sources,
    get_cached_embedding,
    retrieve_knowledge_chunks,
)
from user_sessions.services.system_health import get_system_health  # noqa: E402
from user_sessions.services.strategic_insight import detect_strategic_tensions  # noqa: E402
from utils.knowledge_graph import get_related_concepts  # noqa: E402

STRATEGIC_QUERIES = [
    "How should a premium brand build trust?",
    "Our messaging feels generic. How do we differentiate?",
    "What weakens brand authority?",
    "Help position us against cheaper competitors.",
]

RETRIEVAL_QUERIES = [
    "How can a brand create emotional connection?",
    "How to differentiate from competitors?",
    "What creates brand trust?",
    "How should manifesto positioning work?",
]

BASELINE_TARGETS = {
    "groundedness": 0.85,
    "citation_accuracy": 0.90,
    "hallucination_risk": 0.15,
    "retrieval_precision": 0.80,
}


def _dupes(chunks):
    texts = [(c.get("text") or "")[:80] for c in chunks]
    return len(texts) - len(set(texts))


def analyze_retrieval(query: str) -> dict:
    t0 = time.perf_counter()
    emb_t0 = time.perf_counter()
    emb = get_cached_embedding(query)
    emb_ms = (time.perf_counter() - emb_t0) * 1000

    ret_t0 = time.perf_counter()
    chunks = retrieve_knowledge_chunks(query, search_type="hybrid", use_rerank=True)
    ret_ms = (time.perf_counter() - ret_t0) * 1000

    concepts = get_related_concepts(query)
    sources = extract_sources(chunks)
    dup_count = _dupes(chunks)

    top3 = []
    for i, c in enumerate(chunks[:3], 1):
        meta = c.get("metadata") or {}
        top3.append(
            {
                "rank": i,
                "hybrid": c.get("hybrid_score"),
                "vector": c.get("vector_score"),
                "keyword": c.get("keyword_score"),
                "graph": c.get("graph_score"),
                "ce": c.get("cross_encoder_score"),
                "category": meta.get("category") or c.get("category"),
                "title": (meta.get("title") or "")[:50],
                "reasons": c.get("retrieval_reasons") or [],
            }
        )

    manifesto_first = sum(
        1 for c in chunks[:3]
        if (c.get("metadata") or {}).get("category") == "manifesto"
        or "manifesto" in str((c.get("metadata") or {}).get("file", "")).lower()
    )

    return {
        "query": query,
        "latency_ms": {"embedding": round(emb_ms, 1), "retrieval_total": round(ret_ms, 1)},
        "hits": len(chunks),
        "duplicates": dup_count,
        "graph_concepts": concepts[:6],
        "manifesto_in_top3": manifesto_first,
        "top3": top3,
        "sources": sources[:3],
        "total_ms": round((time.perf_counter() - t0) * 1000, 1),
    }


def analyze_strategic(query: str) -> dict:
    planner = run_planner_entry(query, "strategist")
    retrieval = analyze_retrieval(query)
    insights = detect_strategic_tensions([], retrieval["graph_concepts"], query, retrieval["sources"])
    return {
        "query": query,
        "planner": {
            "intent": planner.get("intent"),
            "primary_agent": planner.get("primary_agent"),
            "selected_agents": planner.get("selected_agents"),
        },
        "retrieval": retrieval,
        "strategic_insights": insights,
    }


def verify_sse_order() -> dict:
    """Simulate stream event order without HTTP."""
    from user_sessions.services.rag_service import stream_rag_response

    events = []
    try:
        for ev in stream_rag_response("What creates brand trust?"):
            events.append(ev.get("type"))
            if ev.get("type") == "sources":
                got_sources = True
            if ev.get("type") == "token":
                break
    except Exception as e:
        return {"ok": False, "error": str(e), "events": events}

    expected_prefix = ["planner", "system_health", "sources"]
    ok = events[:3] == expected_prefix
    return {"ok": ok, "events": events, "expected_prefix": expected_prefix}


def run_evaluation_baseline() -> dict:
    from scripts.run_rag_evaluation import load_cases, score_case
    from user_sessions.services.rag_service import generate_rag_response

    cases = load_cases()
    rows = []
    for case in cases[:6]:
        try:
            result = generate_rag_response(
                case["query"],
                agent_id="strategist",
                include_evaluation=True,
                use_cache=False,
            )
            rows.append(score_case(case, result))
        except Exception as e:
            rows.append({"id": case["id"], "pass": False, "error": str(e)})

    if not rows:
        return {"cases": 0}

    n = len(rows)
    avg = lambda k: sum(r.get(k, 0) for r in rows if "error" not in r) / max(n, 1)
    baseline = {
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "cases_run": n,
        "passed": sum(1 for r in rows if r.get("pass")),
        "metrics": {
            "groundedness": round(avg("groundedness"), 3),
            "citation_accuracy": round(avg("citation_score"), 3),
            "hallucination_risk": round(avg("hallucination_risk"), 3),
            "retrieval_precision": round(avg("retrieval_relevance"), 3),
        },
        "targets": BASELINE_TARGETS,
        "rows": rows,
    }
    out = ROOT / "evaluation" / "baseline_metrics.json"
    out.write_text(json.dumps(baseline, indent=2), encoding="utf-8")
    return baseline


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-eval", action="store_true")
    args = parser.parse_args()

    print("=" * 60)
    print("AI QUALITY VALIDATION")
    print("=" * 60)

    health = get_system_health()
    print("\n[System Health]", json.dumps({k: bool(v) if not isinstance(v, (str, int, float)) else v for k, v in health.items()}, indent=2))

    print("\n--- STEP 1: Retrieval quality ---")
    retrieval_report = []
    for q in RETRIEVAL_QUERIES:
        r = analyze_retrieval(q)
        retrieval_report.append(r)
        print(f"\n  Q: {q[:55]}...")
        print(f"  hits={r['hits']} dupes={r['duplicates']} manifesto_top3={r['manifesto_in_top3']}")
        print(f"  latency embed={r['latency_ms']['embedding']}ms retrieval={r['latency_ms']['retrieval_total']}ms")
        for t in r["top3"]:
            print(f"    [{t['rank']}] hybrid={t['hybrid']} cat={t['category']} | {t['title']}")

    print("\n--- STEP 2: Strategic queries + planner ---")
    strategic_report = []
    for q in STRATEGIC_QUERIES:
        s = analyze_strategic(q)
        strategic_report.append(s)
        p = s["planner"]
        print(f"\n  Q: {q[:55]}...")
        print(f"  agents={p['selected_agents']} primary={p['primary_agent']} intent={p.get('intent')}")
        if s["strategic_insights"]:
            print(f"  insight: {s['strategic_insights'][0]['message'][:80]}...")

    print("\n--- STEP 3: SSE event order ---")
    sse = verify_sse_order()
    print(f"  OK={sse['ok']} events={sse.get('events', [])}")

    print("\n--- STEP 4: Latency targets ---")
    embeds = [r["latency_ms"]["embedding"] for r in retrieval_report]
    rets = [r["latency_ms"]["retrieval_total"] for r in retrieval_report]
    print(f"  embedding avg={sum(embeds)/len(embeds):.0f}ms (target <300)")
    print(f"  retrieval avg={sum(rets)/len(rets):.0f}ms (target <400+700 rerank)")

    if not args.skip_eval:
        print("\n--- STEP 6: Evaluation baseline ---")
        baseline = run_evaluation_baseline()
        print(f"  metrics={baseline.get('metrics')}")
        print(f"  saved: evaluation/baseline_metrics.json")
    else:
        baseline = None

    report = {
        "health": health,
        "settings": {
            "MAX_CONTEXT_CHARS": getattr(settings, "MAX_CONTEXT_CHARS", 6000),
            "MAX_RERANK_BEFORE": getattr(settings, "MAX_RERANK_CHUNKS_BEFORE", 12),
            "MAX_RERANK_AFTER": getattr(settings, "MAX_RERANK_CHUNKS_AFTER", 6),
            "cross_encoder": getattr(settings, "RAG_CROSS_ENCODER_ENABLED", False),
        },
        "retrieval": retrieval_report,
        "strategic": strategic_report,
        "sse": sse,
        "baseline": baseline,
    }
    out = ROOT / "evaluation" / "validation_report.json"
    out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(f"\nFull report: {out}")
    print("=" * 60)


if __name__ == "__main__":
    main()
