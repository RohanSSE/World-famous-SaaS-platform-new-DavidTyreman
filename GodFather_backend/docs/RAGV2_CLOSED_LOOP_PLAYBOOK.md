# RAGv2 Closed-Loop Playbook

Date: 2026-06-11
Status: Ready to use
Owner: Backend + AI Orchestration

## 1. Purpose

This document is the implementation playbook for RAGv2 as a phase-aware, closed-loop generative system.

RAGv2 must:
- combine phase prompt injection + retrieval context + episodic memory
- use the LLM configured from `.env`
- generate UI-facing content
- persist phase checkpoints and episodic memory metadata
- reuse persisted memory/checkpoints in the next generation cycle

## 2. Core Loop

For each user interaction:

1. Resolve active phase
2. Read memory and prior phase artifacts
3. Retrieve relevant RAG context
4. Build layered prompt
5. Generate structured output via configured LLM
6. Evaluate checkpoint readiness
7. Persist artifact + episodic memory delta
8. Return UI payload

This loop repeats and continuously improves context quality.

## 3. Phase Model

## 3.1 Phases

- phase_1: Discovery
- phase_2: Brand Book and Playbook
- phase_3: Brand Promotion
- phase_4: Strategic Guidance and Content Creation

## 3.2 Phase State Rules

- Phase should be pinned to session state once started.
- Do not re-resolve phase from keywords on every query if a pinned phase exists.
- Move to next phase only when checkpoint criteria are satisfied.

## 3.3 Checkpoint Status

- not_started
- in_progress
- completed

## 4. Prompt Layering Contract

Prompt assembly order (top to bottom):

1. System identity prompt (BrandGodfather role/rules)
2. Active phase master prompt
3. Operator injection (if enabled)
4. Episodic memory digest
5. Prior checkpoint/artifact digest
6. Retrieved chunk evidence digest
7. Current user instruction and output format contract

## 5. Retrieval Contract

RAGv2 retrieval should include:

- embeddings/chunks from `brandgodfather_chunks_v2`
- optionally phase artifacts as high-authority memory context
- score/rank metadata
- source identifiers for traceability

Retrieval output should be normalized before prompt assembly:

```json
{
  "sources": [],
  "chunks": [],
  "retrieval_confidence": {},
  "reasoning_path": {}
}
```

## 6. Generation Output Contract

Generator must return structured payload (not plain text only):

```json
{
  "ui_content": "string",
  "summary": "string",
  "checkpoint_delta": {
    "status": "in_progress",
    "completed": false,
    "missing_items": []
  },
  "episodic_memory_delta": [
    {
      "type": "strategic_truth",
      "value": "string",
      "confidence": 0.0,
      "source_ref": "string"
    }
  ],
  "sources": [],
  "retrieval_confidence": {},
  "reasoning_path": {}
}
```

## 7. Episodic Memory Schema

Store normalized entries, not raw transcript blobs.

Each entry:

```json
{
  "type": "strategic_truth|audience_signal|brand_constraint|tone_rule|contradiction|approved_copy|rejected_copy|open_question",
  "value": "string",
  "phase_key": "phase_1",
  "interaction_id": "string",
  "confidence": 0.0,
  "source_refs": [],
  "timestamp": "ISO8601"
}
```

## 8. Phase Artifact Schema

Per session + phase artifact should include:

```json
{
  "phase_key": "phase_2",
  "objective": "string",
  "status": "in_progress",
  "completed": false,
  "ui_content": "string",
  "summary": "string",
  "approved_output": {},
  "missing_items": [],
  "source_count": 0,
  "sources": [],
  "retrieval_confidence": {},
  "reasoning_path": {},
  "updated_at": "ISO8601"
}
```

## 9. Checkpoint Completion Rules

Define explicit completion checks per phase.

Examples:

- phase_1 complete when: audience + tension + category constraints all present with confidence threshold
- phase_2 complete when: brand DNA + promise + voice + positioning validated
- phase_3 complete when: promotion strategy has channel plan + differentiation + CTA logic
- phase_4 complete when: strategic recommendations + content outputs + rationale all grounded

## 10. API Contract (Recommended)

## 10.1 Request

```json
{
  "session_id": 123,
  "user_query": "string",
  "pipeline": "rag_v2",
  "phase_override": null,
  "prompt_injection": {
    "pre_retrieval_prompt": "string",
    "system_injection_prompt": "string"
  }
}
```

## 10.2 Response

```json
{
  "active_pipeline": "rag_v2",
  "rag_phase": "phase_2",
  "ui_content": "string",
  "phase_artifact": {},
  "phase_artifacts": {},
  "episodic_memory_updated": true,
  "sources": [],
  "retrieval_confidence": {},
  "reasoning_path": {},
  "latency_breakdown": {}
}
```

## 11. Persistence Sequence (Transaction Intent)

Within one request cycle:

1. Save generation output artifact
2. Save checkpoint status delta
3. Save episodic memory deltas
4. Save source/reasoning metadata

If any persistence step fails, return response with explicit persistence error state and avoid silent partial writes.

## 12. Observability and Quality Gates

Track:

- phase progression rate
- checkpoint completion rate
- contradiction incidence
- memory reuse hit-rate
- source grounding ratio
- generic output rate

Use these to tune prompts and retrieval profiles.

## 13. Implementation Delta Against Current Repo

Current strengths already present:

- phase prompt injection in RAGv2 pipeline
- phase artifact persistence
- episodic memory in brandgodfather RAGv2 orchestration
- `.env`-driven LLM client

Recommended next upgrades:

1. Pin phase in session to avoid heuristic phase flapping
2. Introduce structured `checkpoint_delta` in generation output
3. Introduce normalized episodic memory entry model
4. Centralize prompt builder and enforce layered prompt order
5. Add checkpoint evaluator (rule-based first)
6. Expose memory/checkpoint state clearly to UI

## 14. Execution Checklist

- [ ] Confirm env settings for LLM + ES Node2
- [ ] Ensure `brandgodfather_chunks_v2` contains embeddings
- [ ] Enable `rag_v2` in dev config
- [ ] Implement structured generation payload contract
- [ ] Implement checkpoint evaluator
- [ ] Persist episodic memory deltas
- [ ] Validate UI renders phase-aware output and checkpoint status
- [ ] Validate loop continuity across at least 10 sequential interactions

## 15. Instruction Template For Next Iterations

Use this format when giving implementation instructions:

1. Phase and objective:
2. Expected UI output shape:
3. Required memory fields to extract/store:
4. Checkpoint completion criteria:
5. Constraints (tone, evidence, safety):
6. Acceptance tests:

---

This playbook is intended to be used as the single source of truth for RAGv2 closed-loop implementation and handoff.
