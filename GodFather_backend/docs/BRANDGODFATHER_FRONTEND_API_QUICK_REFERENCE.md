# BrandGodFather Frontend API Quick Reference

Base URL prefix:

- `/api`

Authentication:

- JWT Bearer token required for all `/api/brandgodfather/*` endpoints.
- Header:

```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

---

## Auth Contracts (Needed By Frontend)

### 1) Login

- Method: `POST`
- Path: `/api/auth/login/`

Request:

```json
{
  "email": "user@example.com",
  "password": "your-password"
}
```

Success `200`:

```json
{
  "refresh": "<jwt-refresh>",
  "access": "<jwt-access>",
  "user": {
    "id": 12,
    "email": "user@example.com"
  }
}
```

Failure `401`:

```json
{
  "detail": "Invalid email or password"
}
```

### 2) Refresh Access Token

- Method: `POST`
- Path: `/api/auth/token/refresh/`

Request:

```json
{
  "refresh": "<jwt-refresh>"
}
```

Success `200`:

```json
{
  "access": "<new-jwt-access>"
}
```

---

## BrandGodFather Contracts

Namespace:

- `/api/brandgodfather`

### 1) Start Session

- Method: `POST`
- Path: `/api/brandgodfather/session/start/`

Request:

```json
{
  "user_id": "12",
  "context_data": {
    "source": "web"
  }
}
```

Success `201`:

```json
{
  "session_id": "cb9135a9-f50f-4e21-a482-31eb6a198dbf",
  "first_question": {
    "q_id": "Q1",
    "phase": "I",
    "prompt": "What belief would you defend even if no one paid you for it?"
  },
  "welcome_sequence": [
    "Welcome to BrandGodFather.",
    "We will go one layer deeper on every answer.",
    "Start with complete honesty, not polished positioning."
  ]
}
```

Failure `400`:

```json
{
  "detail": "user_id is required."
}
```

### 2) Get Session Detail

- Method: `GET`
- Path: `/api/brandgodfather/session/{session_id}/`

Success `200`:

```json
{
  "session_id": "cb9135a9-f50f-4e21-a482-31eb6a198dbf",
  "user_id": "12",
  "current_phase": "I",
  "current_q_id": "Q2",
  "brand_seed": "...",
  "tension": "...",
  "thread_index": {},
  "shadow_profile": {
    "self_image": "unknown",
    "actual_signal": "unknown",
    "gap_score": 0.0,
    "fear_pattern": "unknown",
    "readiness_estimate": 1.0
  },
  "all_answers": [],
  "context_data": {
    "source": "web"
  },
  "created_at": "2026-06-01T11:20:15.183214+00:00",
  "updated_at": "2026-06-01T11:20:15.183214+00:00",
  "current_question": {
    "q_id": "Q2",
    "phase": "I",
    "prompt": "...",
    "enforcement_rule": "..."
  },
  "depth_history": [0.62, 0.71]
}
```

Failure `404`:

```json
{
  "detail": "Session not found."
}
```

### 3) Submit Answer (Sync)

- Method: `POST`
- Path: `/api/brandgodfather/answer/`

Request:

```json
{
  "session_id": "cb9135a9-f50f-4e21-a482-31eb6a198dbf",
  "q_id": "Q14",
  "answer": "I am avoiding being specific because I fear rejection.",
  "async": false
}
```

Success `200`:

```json
{
  "status": "PASS",
  "reply": "Good. That is specific. Keep going deeper.",
  "next_q_id": "Q15",
  "depth_score": 0.78,
  "session_updated": true
}
```

Possible reject `200`:

```json
{
  "status": "REJECT",
  "reply": "This is still generic. Name the exact fear and cost.",
  "next_q_id": null,
  "depth_score": 0.44,
  "session_updated": false
}
```

Validation failure `400`:

```json
{
  "detail": "session_id, q_id, and answer are required."
}
```

### 4) Submit Answer (Async)

- Method: `POST`
- Path: `/api/brandgodfather/answer/`

Request:

```json
{
  "session_id": "cb9135a9-f50f-4e21-a482-31eb6a198dbf",
  "q_id": "Q14",
  "answer": "...",
  "async": true
}
```

Accepted `202`:

```json
{
  "task_id": "4ce3f6a3-5d2e-46d0-86c0-18c3206d9b76",
  "status": "PENDING"
}
```

### 5) Poll Async Answer Status

- Method: `GET`
- Path: `/api/brandgodfather/answer/status/{task_id}/`

Running `200`:

```json
{
  "task_id": "4ce3f6a3-5d2e-46d0-86c0-18c3206d9b76",
  "status": "STARTED"
}
```

Success `200`:

```json
{
  "task_id": "4ce3f6a3-5d2e-46d0-86c0-18c3206d9b76",
  "status": "SUCCESS",
  "result": {
    "status": "PASS",
    "reply": "...",
    "next_q_id": "Q15",
    "depth_score": 0.78,
    "session_updated": true
  }
}
```

Failure `500`:

```json
{
  "task_id": "4ce3f6a3-5d2e-46d0-86c0-18c3206d9b76",
  "status": "FAILURE",
  "error": "<error text>"
}
```

### 6) Output Dashboard: Social

- Method: `GET`
- Path: `/api/brandgodfather/output/{session_id}/social/`

Success `200`:

```json
{
  "session_id": "cb9135a9-f50f-4e21-a482-31eb6a198dbf",
  "content_type": "social",
  "content": [
    {
      "angle": "...",
      "hook_line": "...",
      "platform_suggestion": "LinkedIn",
      "brand_seed_connection": "..."
    }
  ],
  "week_number": 23,
  "brand_filter_result": [
    {
      "brand_seed_present": true,
      "foundation_energy_present": true,
      "generic_filter_pass": true,
      "line_in_sand_consistent": true,
      "failures": [],
      "passed": true
    }
  ],
  "created_at": "2026-06-01T11:20:15.183214+00:00"
}
```

### 7) Output Dashboard: Campaign

- Method: `GET`
- Path: `/api/brandgodfather/output/{session_id}/campaign/`

Success `200`:

```json
{
  "session_id": "cb9135a9-f50f-4e21-a482-31eb6a198dbf",
  "content_type": "campaign",
  "content": {
    "campaign_name": "...",
    "core_message": "...",
    "call_to_action": "...",
    "what_it_protects": "..."
  },
  "week_number": 23,
  "brand_filter_result": {
    "brand_seed_present": true,
    "foundation_energy_present": true,
    "generic_filter_pass": true,
    "line_in_sand_consistent": true,
    "failures": [],
    "passed": true
  },
  "created_at": "2026-06-01T11:20:15.183214+00:00"
}
```

### 8) Output Dashboard: Outreach

- Method: `GET`
- Path: `/api/brandgodfather/output/{session_id}/outreach/`

Success `200`:

```json
{
  "session_id": "cb9135a9-f50f-4e21-a482-31eb6a198dbf",
  "content_type": "outreach",
  "content": [
    {
      "outreach_type": "Email",
      "subject_line": "...",
      "opening": "...",
      "trust_signal": "...",
      "cta": "..."
    }
  ],
  "week_number": 23,
  "brand_filter_result": [
    {
      "brand_seed_present": true,
      "foundation_energy_present": true,
      "generic_filter_pass": true,
      "line_in_sand_consistent": true,
      "failures": [],
      "passed": true
    }
  ],
  "created_at": "2026-06-01T11:20:15.183214+00:00"
}
```

Not found `404` (all output endpoints):

```json
{
  "detail": "Output not found for this session."
}
```

---

## Frontend Usage Pattern

1. Login and cache `access` + `refresh` tokens.
2. Start session once.
3. Submit answers question-by-question.
4. If using async, poll task status until `SUCCESS`.
5. Read session detail for current question and depth history.
6. After Q30 completion, fetch social/campaign/outreach output cards.

---

## Contract Notes

- `status` values in answer flow: `PASS` or `REJECT`.
- Async task status values: `PENDING`, `STARTED`, `RETRY`, `SUCCESS`, `FAILURE`.
- `brand_filter_result` shape depends on content type:
  - Social and outreach: usually an array of filter results.
  - Campaign: usually a single filter result object.
