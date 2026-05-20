# Sessions API — Frontend reference

**Base URL:** `/api/sessions/`  
**Auth:** All endpoints below require an **authenticated user** (e.g. Bearer token / session auth). Session must belong to the user (or agency view).

`{session_id}` and `{id}` below are the same: the session primary key integer.

---

## 1. Contextual assistant suggestion (avatar popup) — NEW

**POST** `/api/sessions/{session_id}/assistant-suggestion/`

Returns one short message + optional CTA for the avatar bubble. Messages refer to the **overall screen** (what this page is for, progress here, what they can do on this screen) — not "click here" or "click there" for specific buttons.

**Staying in sync with the UI:**  
The **message** describes the current screen and context (e.g. "You're on the foundation questions — halfway through already.", "This is your manifesto screen; everything here is yours to review."). The **cta** tells you which overall screen/section is relevant so you can show or emphasize that part of the UI:

| `cta` value        | Screen/section to align with |
|--------------------|-------------------------------|
| `"review_journey"` | Journey / progress / review screen or section |
| `"quick_tips"`     | Quick tips screen or panel |
| `null`             | No specific screen; general encouragement for current view |

So the avatar speaks about the screen as a whole; use `cta` to keep the suggestion in sync with which screen or section the user is on or might go to.

**Request body (JSON):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `route` | string | **Yes** | e.g. `/foundation-questions`, `/ChatKickoffPage`, `/brand-summary`, `/user-dashboard`, `/manifesto`, `/manifestoFirstPage`, `/chat-unlock` |
| `time_on_page_seconds` | number | No | Seconds on current page (default 0) |
| `current_step_index` | number \| null | No | Current step/question index (0-based) |
| `total_steps` | number \| null | No | Total steps on this page |
| `answers_count` | number | No | How many answers/steps are done |
| `last_action` | string | No | One of: `"answered"`, `"focused"`, `"scrolled"`, `"idle"` (default `"idle"`) |

**Response (200):**

```json
{
  "message": "You're on the foundation questions — halfway through already.",
  "cta": null
}
```

- `message`: string — one short, encouraging sentence (1–2 sentences) about the **overall screen** (progress, what this page is for). No "click here" wording.
- `cta`: `null` | `"review_journey"` | `"quick_tips"` — which screen/section is relevant; use the table above to show or emphasize that part of the UI.

**Errors:** `403` Access denied, `400` missing `route`, `500` AI error (you can show a fallback message).

---

## 2. AI answer suggestions (typing hints)

**POST** `/api/sessions/{session_id}/ai-answer-suggestions/`

Returns 2–4 short completion suggestions based on the question and what the user has typed.

**Request body (JSON):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `question_id` | number | **Yes** | Question ID |
| `hints` | string | No | User’s partial answer / what they typed so far (can be empty) |

**Response (200):**

```json
{
  "suggestions": [
    "Our mission is to help small businesses grow through simple, effective tools.",
    "We exist to empower small businesses with the resources they need to succeed."
  ]
}
```

- `suggestions`: array of strings (2–4 items). Empty array on parse/error.

**Errors:** `403` Access denied, `404` Question not found, `500` AI error.

---

## 3. AI draft improvement + follow-up question

**POST** `/api/sessions/sessions/{session_id}/ai-suggestion/draft/`

Note: URL has **two** “sessions” — `/api/sessions/sessions/{session_id}/ai-suggestion/draft/`

Improves the user’s draft answer and returns an optional follow-up question.

**Request body (JSON):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `question_id` | number | **Yes** | Question ID |
| `draft` | string | **Yes** | User’s current draft text |
| `refined` | boolean | No | `true` if this draft was already improved once; `false` or omit for raw input |

**Response (200):** Backend returns a rich format (improved answer + follow-up content). Shape is backend-defined; frontend already uses this.

**Errors:** `403` Access denied, `400` missing `question_id` or `draft`, `404` Question not found, `500` AI error.

---

## 4. Batch save answers — NEW (optional)

**POST** `/api/sessions/{session_id}/answers/batch/`

Create or update multiple answers in one request (upsert per question).

**Request body (JSON):**

```json
{
  "answers": [
    { "question_id": 1, "answer_text": "First answer here." },
    { "question_id": 2, "answer_text": "Second answer." }
  ]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `answers` | array | **Yes** | List of objects with `question_id` (number) and `answer_text` (string) |

**Response (200):**

```json
{
  "saved": 2,
  "answer_ids": [101, 102]
}
```

- Invalid or out-of-stage items are skipped; only successfully saved answers are counted and listed.

**Errors:** `403` No permission or session locked, `400` if `answers` is not a list.

---

## 5. Save single answer (existing)

**POST** `/api/sessions/{session_id}/answers/create/`

Create or update one answer. Contract unchanged.

**Request body (JSON):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `question` | number | **Yes** | Question ID (sent as `question` in JSON) |
| `answer_text` | string | **Yes** | Answer text |

**Response (200/201):** Full answer object (id, session, question, answer_text, etc.).

**Errors:** `403` No permission or session locked, `400` validation or stage error.

---

## Quick reference

| Purpose | Method | Path |
|--------|--------|------|
| Avatar contextual message | POST | `/api/sessions/{id}/assistant-suggestion/` |
| Typing hints (2–4 suggestions) | POST | `/api/sessions/{id}/ai-answer-suggestions/` |
| Draft improve + follow-up | POST | `/api/sessions/sessions/{id}/ai-suggestion/draft/` |
| Batch save answers | POST | `/api/sessions/{id}/answers/batch/` |
| Save one answer | POST | `/api/sessions/{id}/answers/create/` |

All require **authenticated user** and **session access** (user owns session or is agency viewing it).
