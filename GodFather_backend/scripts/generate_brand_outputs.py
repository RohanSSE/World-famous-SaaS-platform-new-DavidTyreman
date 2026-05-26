#!/usr/bin/env python
"""
Generate structured brand book outputs from retrieved knowledge.
Usage: python scripts/generate_brand_outputs.py --query "Summarize our brand DNA"
"""
import argparse
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", default="Generate a complete brand book summary from our knowledge base.")
    parser.add_argument("--out", default=str(ROOT / "evaluation" / "brand_outputs.json"))
    args = parser.parse_args()

    from user_sessions.services.rag_service import generate_rag_response
    from user_sessions.services.brand_language_anchor import extract_brand_language_anchors
    from user_sessions.services.brand_output_schemas import (
        empty_brand_output,
        narrative_to_structured_sections,
    )

    result = generate_rag_response(
        user_query=args.query,
        agent_id="branding",
        include_user_docs=False,
        include_evaluation=True,
    )
    answer = result.get("answer", "")
    chunks = result.get("chunks", [])
    context = result.get("_context") or ""
    anchors = extract_brand_language_anchors(chunks, context)
    structured = narrative_to_structured_sections(answer, anchors)
    ev = result.get("evaluation") or {}

    payload = {
        "query": args.query,
        "structured": structured,
        "schema_version": "brand_output_v1",
        "narrative": answer,
        "language_anchors": anchors,
        "sources": (result.get("sources") or [])[:10],
        "metrics": {
            "consistency_score": (result.get("strategic_consistency") or {}).get("consistency_score"),
            "hallucination_risk": ev.get("hallucination_risk"),
            "unsupported_claim_rate": ev.get("unsupported_claim_rate"),
            "high_inference_rate": ev.get("high_inference_rate"),
            "grounded_answer_ratio": ev.get("grounded_answer_ratio"),
            "claim_grounded_ratio": ev.get("claim_grounded_ratio"),
        },
    }

    out_path = Path(args.out)
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {out_path}")
    for key in empty_brand_output().keys():
        print(f"  - {key}")


if __name__ == "__main__":
    main()
