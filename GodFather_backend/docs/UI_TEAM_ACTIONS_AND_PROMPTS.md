# UI team — Changes and prompts

This doc lists what the frontend needs to do to use the new/updated backend features, and gives copy-paste prompts for implementation.

**API details:** See `API_SESSIONS_FRONTEND.md` for request/response shapes and base URL.

---

## 1. Avatar contextual suggestion (NEW — UI changes needed)

### What backend provides
- **POST** `/api/sessions/{session_id}/assistant-suggestion/`
- Returns `{ message, cta }`: one short sentence about the **current screen** (no "click here") and an optional `cta` (`"review_journey"` | `"quick_tips"` | `null`) so the UI can align with the right screen/section.

### What the UI team needs to do

1. **Add or use an avatar/bubble component** that can show a short message (1–2 sentences) on relevant screens (e.g. foundation-questions, ChatKickoffPage, brand-summary, user-dashboard, manifesto, manifestoFirstPage, chat-unlock).

2. **Call the API when it makes sense**, e.g.:
   - When the user lands on a supported route, or after they’ve been on the page for a few seconds.
   - Optionally again after `last_action` changes (e.g. after they answer, scroll, or stay idle for a bit).
   - Send: current `route`, `time_on_page_seconds`, `current_step_index`, `total_steps`, `answers_count`, `last_action` (one of `"answered"` | `"focused"` | `"scrolled"` | `"idle"`).

3. **Display the `message`** in the avatar bubble. If the API fails, show a fallback like “Keep going — you’re doing great!”

4. **Use `cta` to stay in sync with screens** (no “click here” in the copy):
   - `cta === "review_journey"` → Emphasize or surface the **journey / progress / review** screen or section (e.g. make it more visible or suggest navigating there).
   - `cta === "quick_tips"` → Emphasize or surface the **quick tips** screen or panel.
   - `cta === null` → No extra UI; just show the message for the current view.

### Prompts for the UI team

**Prompt 1 — When to call the API**
> “On these routes — foundation-questions, ChatKickoffPage, brand-summary, user-dashboard, manifesto, manifestoFirstPage, chat-unlock — we need to call POST /api/sessions/{sessionId}/assistant-suggestion/ to get a short contextual message for the avatar. Call it when the user enters the page (or after a short delay, e.g. 2–3 seconds). Optionally call it again when the user answers a question, scrolls, or has been idle for a while. Send the current route, time on page in seconds, current step index, total steps, answers count, and last_action (‘answered’ | ‘focused’ | ‘scrolled’ | ‘idle’).”

**Prompt 2 — What to send in the request**
> “The request body must include: `route` (string, required — e.g. ‘/foundation-questions’ or ‘/user-dashboard’); optionally `time_on_page_seconds` (number), `current_step_index` (number or null), `total_steps` (number or null), `answers_count` (number), `last_action` (one of ‘answered’, ‘focused’, ‘scrolled’, ‘idle’). Use the same auth header as other session APIs.”

**Prompt 3 — How to show the response**
> “Show the response `message` in the avatar bubble. The message describes the overall screen (e.g. ‘You’re on the foundation questions — halfway through already.’), not a specific button. If the API returns a `cta`, use it only to decide which screen or section to emphasize: ‘review_journey’ = journey/progress/review area, ‘quick_tips’ = quick tips area; do not add ‘click here’ text. On API error, show a fallback message like ‘Keep going — you’re doing great!’.”

---

## 2. AI answer suggestions (typing hints) — Optional UI check

### What backend provides
- **POST** `/api/sessions/{session_id}/ai-answer-suggestions/`
- Body: `{ question_id, hints }`. Response: `{ suggestions: string[] }` (2–4 items).

### What the UI team needs to do
- If you already call this endpoint: **no change** required; backend now returns JSON with 2–4 suggestions. Keep sending `question_id` and `hints` (user’s partial text).
- If you don’t use it yet: add a way to request suggestions while the user types (e.g. debounced) and show the `suggestions` array as tappable/clickable chips or list items that insert that text into the answer field.

### Prompt for the UI team
> “For the answer input where we have a question_id, we can get 2–4 completion suggestions from POST /api/sessions/{sessionId}/ai-answer-suggestions/ with body { question_id, hints } (hints = what the user has typed so far). Show the returned ‘suggestions’ array as chips or list items; when the user picks one, insert that text (or append) into the answer field. Debounce the request while typing (e.g. 300–500 ms after last keystroke).”

---

## 3. AI draft improvement + follow-up — No UI change required

- **POST** `/api/sessions/sessions/{session_id}/ai-suggestion/draft/` (note the double `sessions` in the path).
- Body: `{ question_id, draft, refined }`. Backend behavior unchanged; frontend can keep current integration.

---

## 4. Batch save answers (NEW — Optional)

### What backend provides
- **POST** `/api/sessions/{session_id}/answers/batch/`
- Body: `{ answers: [ { question_id, answer_text }, ... ] }`. Response: `{ saved, answer_ids }`.

### What the UI team needs to do
- **Optional.** Use this only if you want to save multiple answers in one request (e.g. “Save all” on a page with several inputs). Same auth and session as single-answer create. No UI change required if you keep saving one answer at a time via `answers/create/`.

### Prompt for the UI team
> “If we add a ‘Save all’ or bulk-save flow, call POST /api/sessions/{sessionId}/answers/batch/ with body { answers: [ { question_id: 1, answer_text: "..." }, ... ] }. Response is { saved: number, answer_ids: number[] }. Use the same auth as single-answer save. Invalid or out-of-stage items are skipped; only successfully saved answers are in saved and answer_ids.”

---

## 5. Single answer save — No UI change required

- **POST** `/api/sessions/{session_id}/answers/create/` with `{ question, answer_text }`. Contract unchanged; keep using as today.

---

## Summary: where the UI must change

| Feature | UI change? | Action |
|--------|------------|--------|
| **Avatar contextual suggestion** | **Yes** | Add/use avatar bubble; call assistant-suggestion API; send route + progress; show message; use cta to align with journey/tips screen. |
| AI answer suggestions | Optional | Already integrated → no change. Not yet → add debounced call and show suggestions as chips/list. |
| Draft improve + follow-up | No | Keep current integration. |
| Batch save answers | Optional | Use only if you add bulk-save; same auth as single save. |
| Single answer save | No | No change. |

Use the **prompts** in sections 1 and 2 (and 4 if you add batch save) as implementation instructions for the UI team.
