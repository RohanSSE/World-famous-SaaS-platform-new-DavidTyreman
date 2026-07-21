#!/usr/bin/env python
"""Standalone Azure OpenAI reasoning benchmark.

Runs fixed generative Q&A simulations against the deployment configured in
GodFather_backend/.env and writes a plain-text benchmark report.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from dotenv import load_dotenv
from openai import AzureOpenAI


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "azure_reasoning_benchmark_results.txt"


@dataclass(frozen=True)
class BenchmarkCase:
    case_id: str
    title: str
    category: str
    prompt: str
    scorer: Callable[[str], tuple[float, str]]


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def _has_all(text: str, terms: list[str]) -> bool:
    lowered = _normalize(text)
    return all(term.lower() in lowered for term in terms)


def _extract_numbers(text: str) -> list[float]:
    numbers = []
    for match in re.findall(r"-?\d+(?:\.\d+)?", text.replace(",", "")):
        try:
            numbers.append(float(match))
        except ValueError:
            pass
    return numbers


def score_store_split(answer: str) -> tuple[float, str]:
    lowered = _normalize(answer)
    checks = {
        "south_15": bool(re.search(r"\bsouth\D{0,12}15\b|\b15\D{0,12}south\b", lowered)),
        "north_30": bool(re.search(r"\bnorth\D{0,12}30\b|\b30\D{0,12}north\b", lowered)),
        "east_27": bool(re.search(r"\beast\D{0,12}27\b|\b27\D{0,12}east\b", lowered)),
        "total_72": "72" in lowered,
    }
    return sum(checks.values()) / len(checks), ", ".join(k for k, v in checks.items() if v) or "no expected allocation found"


def score_meeting_slot(answer: str) -> tuple[float, str]:
    lowered = _normalize(answer)
    checks = {
        "recommends_tuesday": "tuesday" in lowered or "tue" in lowered,
        "mentions_10_00": bool(re.search(r"\b10(?::00)?\b", lowered)),
        "rejects_monday": "monday" in lowered and any(word in lowered for word in ["not", "conflict", "avoid", "unavailable"]),
        "handles_timezone": any(term in lowered for term in ["london", "uk", "new york", "ny", "time zone", "timezone"]),
    }
    return sum(checks.values()) / len(checks), ", ".join(k for k, v in checks.items() if v) or "no expected scheduling logic found"


def score_policy_exception(answer: str) -> tuple[float, str]:
    lowered = _normalize(answer)
    checks = {
        "store_credit": "store credit" in lowered or "credit" in lowered,
        "opened_item": "opened" in lowered,
        "non_defective": any(term in lowered for term in ["non-defective", "not defective", "non defective"]),
        "within_30_days": any(term in lowered for term in ["within 30 days", "30 days", "17 days"]),
    }
    return sum(checks.values()) / len(checks), ", ".join(k for k, v in checks.items() if v) or "no expected policy decision found"


def score_causal_plan(answer: str) -> tuple[float, str]:
    lowered = _normalize(answer)
    checks = {
        "isolates_variable": any(term in lowered for term in ["one variable", "isolate", "control", "hold", "one change at a time"]),
        "covers_all_changes": all(term in lowered for term in ["pricing", "homepage", "onboarding"]),
        "success_metric": any(term in lowered for term in ["conversion", "reply rate", "meeting", "booked", "metric"]),
        "measures_impact": any(term in lowered for term in ["measure", "impact", "observed", "improvement"]),
    }
    return sum(checks.values()) / len(checks), ", ".join(k for k, v in checks.items() if v) or "no expected experiment design found"


def score_weighted_choice(answer: str) -> tuple[float, str]:
    lowered = _normalize(answer)
    checks = {
        "chooses_beta": "beta" in lowered,
        "weighted_score_78_9": bool(re.search(r"\b78\.9\b|\b79(?:\.0)?\b", lowered)),
        "compares_alpha": "alpha" in lowered and bool(re.search(r"\b76(?:\.0)?\b", lowered)),
        "mentions_weights": any(term in lowered for term in ["weight", "weighted", "0.5", "50%"]),
    }
    return sum(checks.values()) / len(checks), ", ".join(k for k, v in checks.items() if v) or "no expected weighted decision found"


def score_contradiction(answer: str) -> tuple[float, str]:
    lowered = _normalize(answer)
    checks = {
        "flags_contradiction": any(term in lowered for term in ["contradiction", "inconsistent", "conflict", "discrepancy"]),
        "needs_source_of_truth": any(term in lowered for term in ["product team", "stakeholder", "source of truth", "confirm", "consult"]),
        "asks_clarifying_question": "?" in answer or "clarify" in lowered or "confirm" in lowered,
        "avoids_fabrication": any(term in lowered for term in ["cannot determine", "need", "confirm", "until"]),
    }
    return sum(checks.values()) / len(checks), ", ".join(k for k, v in checks.items() if v) or "no expected contradiction handling found"


CASES = [
    BenchmarkCase(
        case_id="R01",
        title="Constrained Inventory Split",
        category="math_reasoning",
        prompt=(
            "A warehouse has 72 display units for three stores. North must receive twice as many units as South. "
            "East must receive 12 more units than South. How many units should each store receive? "
            "Return the answer with a brief rationale."
        ),
        scorer=score_store_split,
    ),
    BenchmarkCase(
        case_id="R02",
        title="Cross-Time-Zone Meeting Choice",
        category="constraint_reasoning",
        prompt=(
            "Schedule a 45-minute call for Priya in London and Marcus in New York. Priya is available Monday "
            "15:00-17:00 London time and Tuesday 14:00-16:00 London time. Marcus is available Monday "
            "09:00-09:30 New York time and Tuesday 10:00-12:00 New York time. London is 5 hours ahead of "
            "New York. What is the earliest valid slot? Explain briefly."
        ),
        scorer=score_meeting_slot,
    ),
    BenchmarkCase(
        case_id="R03",
        title="Refund Policy Exception",
        category="rule_application",
        prompt=(
            "Policy: unopened items can be refunded within 14 days. Defective opened items can be refunded "
            "within 30 days. Non-defective opened items can receive store credit within 30 days. A customer "
            "returns an opened, non-defective item after 17 days and says they changed their mind. What outcome "
            "should support offer?"
        ),
        scorer=score_policy_exception,
    ),
    BenchmarkCase(
        case_id="R04",
        title="Causal Experiment Design",
        category="business_reasoning",
        prompt=(
            "A SaaS team changed pricing, homepage copy, and onboarding emails in the same week. Signups rose "
            "18%, but paid conversion fell 6%. Propose the simplest test plan to identify which change caused "
            "the paid-conversion drop."
        ),
        scorer=score_causal_plan,
    ),
    BenchmarkCase(
        case_id="R05",
        title="Weighted Vendor Decision",
        category="quantitative_decision",
        prompt=(
            "Choose between vendor Alpha and vendor Beta. Score weights: reliability 50%, cost 30%, support 20%. "
            "Alpha scores reliability 90, cost 60, support 65. Beta scores reliability 78, cost 85, support 72. "
            "Which vendor has the higher weighted score? Show the scores briefly."
        ),
        scorer=score_weighted_choice,
    ),
    BenchmarkCase(
        case_id="R06",
        title="Contradictory Requirements",
        category="critical_reasoning",
        prompt=(
            "A product brief says the free plan allows unlimited projects. Later it says the free plan has a hard "
            "limit of 300 projects. The launch FAQ must be accurate. What should the assistant do before drafting "
            "the FAQ answer?"
        ),
        scorer=score_contradiction,
    ),
]


def build_client() -> tuple[AzureOpenAI, str]:
    env_path = ROOT / ".env"
    load_dotenv(env_path)

    endpoint = (os.getenv("AZURE_OPENAI_ENDPOINT") or "").strip()
    api_key = (os.getenv("AZURE_OPENAI_API_KEY") or "").strip()
    deployment = (os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME") or "gpt-4o").strip()
    api_version = (os.getenv("AZURE_OPENAI_API_VERSION") or "2024-02-01").strip()

    if not endpoint or not api_key:
        raise RuntimeError(f"Missing AZURE_OPENAI_ENDPOINT or AZURE_OPENAI_API_KEY in {env_path}")

    return (
        AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
        ),
        deployment,
    )


def run_case(client: AzureOpenAI, deployment: str, case: BenchmarkCase, temperature: float) -> dict:
    started = time.perf_counter()
    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are being benchmarked on reasoning quality. Answer the user's Q&A task directly. "
                    "Give a concise final answer and a brief rationale, but do not include hidden chain-of-thought."
                ),
            },
            {"role": "user", "content": case.prompt},
        ],
        temperature=temperature,
        max_tokens=350,
    )
    elapsed_ms = (time.perf_counter() - started) * 1000
    answer = (response.choices[0].message.content or "").strip()
    score, evidence = case.scorer(answer)
    usage = response.usage
    return {
        "case_id": case.case_id,
        "title": case.title,
        "category": case.category,
        "prompt": case.prompt,
        "answer": answer,
        "score": round(score, 3),
        "evidence": evidence,
        "latency_ms": round(elapsed_ms, 1),
        "prompt_tokens": getattr(usage, "prompt_tokens", None) if usage else None,
        "completion_tokens": getattr(usage, "completion_tokens", None) if usage else None,
        "total_tokens": getattr(usage, "total_tokens", None) if usage else None,
    }


def format_report(results: list[dict], deployment: str, temperature: float) -> str:
    scores = [row["score"] for row in results]
    latencies = [row["latency_ms"] for row in results]
    token_totals = [row["total_tokens"] for row in results if row["total_tokens"] is not None]
    passed = sum(1 for score in scores if score >= 0.75)
    overall = statistics.mean(scores) if scores else 0.0

    lines = [
        "Azure OpenAI Reasoning Benchmark Results",
        "=" * 42,
        f"Generated UTC: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}",
        f"Deployment: {deployment}",
        f"Temperature: {temperature}",
        f"Cases run: {len(results)}",
        f"Pass threshold: 0.75 per case",
        "API key: not printed",
        "",
        "Summary",
        "-" * 42,
        f"Overall reasoning score: {overall:.3f} / 1.000",
        f"Passed cases: {passed}/{len(results)}",
        f"Average latency: {statistics.mean(latencies):.1f} ms" if latencies else "Average latency: n/a",
        f"Median latency: {statistics.median(latencies):.1f} ms" if latencies else "Median latency: n/a",
        f"Total tokens: {sum(token_totals)}" if token_totals else "Total tokens: n/a",
        "",
        "Case Results",
        "-" * 42,
    ]

    for row in results:
        status = "PASS" if row["score"] >= 0.75 else "REVIEW"
        lines.extend(
            [
                f"[{row['case_id']}] {row['title']} ({row['category']}) - {status}",
                f"Score: {row['score']:.3f}",
                f"Latency: {row['latency_ms']:.1f} ms",
                f"Tokens: prompt={row['prompt_tokens']} completion={row['completion_tokens']} total={row['total_tokens']}",
                f"Scoring evidence: {row['evidence']}",
                "Prompt:",
                row["prompt"],
                "Model answer:",
                row["answer"],
                "",
            ]
        )

    lines.extend(
        [
            "Notes",
            "-" * 42,
            "Scores are deterministic rubric checks over generated answers, not a second LLM judge.",
            "This benchmark is intentionally compact; rerun with the same temperature for comparable trend checks.",
            "No secrets from .env are written to this report.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark Azure OpenAI reasoning with fixed Q&A simulations.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Path to the .txt report to write.")
    parser.add_argument("--temperature", type=float, default=0.0, help="Sampling temperature for comparable runs.")
    args = parser.parse_args()

    client, deployment = build_client()
    results = [run_case(client, deployment, case, args.temperature) for case in CASES]
    report = format_report(results, deployment, args.temperature)

    output_path = args.output
    if not output_path.is_absolute():
        output_path = ROOT / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")

    print(f"Wrote benchmark results to {output_path}")
    print(f"Overall score: {statistics.mean(row['score'] for row in results):.3f}")


if __name__ == "__main__":
    main()