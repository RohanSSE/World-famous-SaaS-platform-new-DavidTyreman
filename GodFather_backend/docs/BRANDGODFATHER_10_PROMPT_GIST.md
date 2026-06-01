# BrandGodFather Build Gist (10-Prompt Summary)

## What's been developed so far ?

This build sequence delivered the BrandGodFather backend pipeline end-to-end, from answer intake to post-manifesto recurring dashboard outputs.

Core delivered layers:

1. Coaching intelligence and enforcement
- Prosody/Gate enforcement (vendor/cliche resistance, pressure hints)
- Contradiction detection across prior answers
- Shadow profile updates (self-image vs actual signal)

2. Retrieval and prompting
- Hybrid RAG retrieval over BrandGodFather chunk index
- Prompt assembly for strict coaching behavior and structured outputs
- Runtime fallback for Elasticsearch clusters that do not support native retriever syntax

3. Sessioned orchestration flow
- Question orchestration for pass/reject path
- Session lifecycle and Q1-Q30 routing
- Async answer processing and task status polling

4. Post-Q30 assets
- BrandBook generation + generic filter + output mode update
- Manifesto hook (task slot present)

5. Output Mode dashboard engine
- Weekly Social Point of View generation
- Monthly Campaign generation
- Weekly Growth Outreach generation
- Mandatory brand filter + regeneration loop (max 2 retries)

6. Operational and naming migration
- Synapse renamed to BrandGodFather in app surface
- New BrandGodFather output index and scheduled Celery beat jobs

---

## Main Components

Service modules in brandgodfather/services:

- prosody_classifier.py
- contradiction_engine.py
- shadow_profile.py
- rag_retrieval.py
- prompt_assembler.py
- orchestrator.py
- question_router.py
- session_manager.py
- BrandBook_generator.py
- output_mode.py

Task entrypoints in brandgodfather/tasks.py:

- process_answer_async
- generate_BrandBook_task
- weekly_social_task
- monthly_campaign_task
- weekly_outreach_task

Documents/index mappings in brandgodfather/documents.py:

- brandgodfather_brand_chunks
- brandgodfather_sessions
- brandgodfather_episodic
- brandgodfather_output_content

---

## API Endpoints For Developers

Base namespace:

- /api/brandgodfather/

### 1. Start Session

- Method: POST
- Path: /api/brandgodfather/session/start/
- Purpose: Start a Q1-Q30 coaching session.
- Body:

```json
{
  "user_id": "<user-id>",
  "context_data": {}
}
```

- Returns: session_id + first question payload.

### 2. Session Detail

- Method: GET
- Path: /api/brandgodfather/session/{session_id}/
- Purpose: Read current question, session state, depth history.

### 3. Submit Answer (Sync or Async)

- Method: POST
- Path: /api/brandgodfather/answer/
- Purpose: Process one answer step.
- Body:

```json
{
  "session_id": "<session-id>",
  "q_id": "Q14",
  "answer": "<free text>",
  "async": true
}
```

- If async=true: returns task_id.
- If async=false: returns immediate pass/reject payload.

### 4. Poll Async Answer Task

- Method: GET
- Path: /api/brandgodfather/answer/status/{task_id}/
- Purpose: Retrieve async answer processing result.

### 5. Output Mode (Dashboard Content)

All output endpoints are GET and return latest generated content record for the session.

- /api/brandgodfather/output/{session_id}/social/
- /api/brandgodfather/output/{session_id}/campaign/
- /api/brandgodfather/output/{session_id}/outreach/

Output payload shape includes:

- session_id
- content_type
- content
- week_number
- brand_filter_result
- created_at

---

## Output Mode Rules Implemented

Implemented in brandgodfather/services/output_mode.py.

### Weekly Social

- Generates 5 ideas
- Format per idea:
  - angle
  - hook_line
  - platform_suggestion
  - brand_seed_connection

### Monthly Campaign

- Generates 1 campaign
- Format:
  - campaign_name
  - core_message
  - call_to_action
  - what_it_protects

### Weekly Outreach

- Generates outreach templates grounded in WOM trigger + ideal client fear (Q16)
- Format per template:
  - outreach_type
  - subject_line
  - opening
  - trust_signal
  - cta

### Mandatory Brand Filter

Every generated piece is checked for:

- brand_seed_present
- foundation_energy_present
- generic_filter_pass
- line_in_sand_consistent

If any check fails:

- regenerate content
- max 2 regeneration attempts

---

## Background Scheduling

Configured in project/settings.py (CELERY_BEAT_SCHEDULE):

- brandgodfather-weekly-social: Monday
- brandgodfather-monthly-campaign: day 1 of month
- brandgodfather-weekly-outreach: Wednesday

All scheduled jobs:

1. Query completed sessions (Q30 PASS)
2. Generate content via OutputModeEngine
3. Store in brandgodfather_output_content

Stored document shape:

```json
{
  "session_id": "...",
  "content_type": "social|campaign|outreach",
  "content": {},
  "week_number": 23,
  "brand_filter_result": {},
  "created_at": "2026-06-01T...Z"
}
```

---

## Manual Ops Commands

Run from GodFather_backend.

### Create/refresh indices

```powershell
$env:SKIP_PROSODY_PRELOAD="1"
$env:SKIP_RAG_PRELOAD="1"
.\venv\Scripts\python.exe manage.py create_brandgodfather_indices
```

### Ingest RAG PDFs

```powershell
$env:SKIP_PROSODY_PRELOAD="1"
$env:SKIP_RAG_PRELOAD="1"
.\venv\Scripts\python.exe manage.py ingest_brandgodfather_pdfs --dir "RAG-docsv2"
```

### Start worker

```powershell
.\venv\Scripts\python.exe -m celery -A project worker -l info -Q project.default -n celery@rohana --pool=solo
```

### Run checks

```powershell
.\venv\Scripts\python.exe manage.py check
```

---

## Known Notes For Devs

1. RAG retrieval compatibility
- Some ES clusters reject native retriever syntax.
- Service now falls back to classic dense+sparse fusion automatically.

2. Source corpus language
- If indexed text still includes legacy "Synapse" wording, update source PDFs and re-ingest.

3. Embeddings retraining
- Not required for naming migration.
- Re-ingestion is sufficient to regenerate vectors in target indices.

---

## Fast Integration Order (Frontend/Backend Dev)

1. Start a session
2. Loop answer submit + task polling until Q30 PASS
3. Read session detail for state/depth
4. Read output endpoints for dashboard cards:
- social
- campaign
- outreach
5. Let Celery beat refresh outputs on schedule
