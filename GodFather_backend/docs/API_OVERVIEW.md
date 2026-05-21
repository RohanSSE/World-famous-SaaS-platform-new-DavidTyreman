# API Overview

This document summarizes the REST and WebSocket APIs so developers can integrate with the GodFather Backend. For request/response schemas, use **Swagger** (`/swagger/`) or **ReDoc** (`/redoc/`).

---

## Base URL and Auth

- **Base URL (local):** `http://127.0.0.1:8000`
- **Authentication:** JWT. Send header: `Authorization: Bearer <access_token>`
- **Login:** `POST /api/auth/login/` returns `access` and `refresh`; use `access` for API calls. Use `POST /api/auth/token/refresh/` with `refresh` to get a new `access`.

---

## 1. Authentication — `/api/auth/`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register/` | Register (email + password) |
| POST | `/api/auth/login/` | Login; returns JWT access + refresh |
| GET  | `/api/auth/me/` | Current user profile |
| PUT  | `/api/auth/me/` | Update profile |
| POST | `/api/auth/change-password/` | Change password |
| POST | `/api/auth/password/reset/` | Request password reset email |
| POST | `/api/auth/password/reset/confirm/` | Confirm reset with token |
| POST | `/api/auth/token/refresh/` | Refresh access token |
| POST | `/api/auth/token/verify/` | Verify token |
| GET  | `/api/auth/roles/` | List roles |
| POST | `/api/auth/roles/` | Create role |
| GET  | `/api/auth/roles/<id>/` | Role detail |
| GET  | `/api/auth/permissions/` | List permissions |
| POST | `/api/auth/permissions/` | Create permission |
| GET  | `/api/auth/permissions/<id>/` | Permission detail |
| GET  | `/api/auth/users/` | List users (admin) |
| GET  | `/api/auth/users/<id>/` | User detail (admin) |
| GET  | `/api/auth/agencies/` | List agencies |
| POST | `/api/auth/agencies/` | Create agency |
| GET  | `/api/auth/agencies/<id>/` | Agency detail |

---

## 2. Sessions (Questionnaire) — `/api/sessions/`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET  | `/api/sessions/` | List sessions (filtered by user/agency) |
| POST | `/api/sessions/create/` | Create session |
| GET  | `/api/sessions/<id>/` | Session detail |
| PATCH | `/api/sessions/<id>/` | Update session |
| DELETE | `/api/sessions/<id>/` | Delete session |
| POST | `/api/sessions/<id>/start/` | Start session |
| POST | `/api/sessions/<id>/complete/` | Mark completed |
| POST | `/api/sessions/<id>/assign-agency/` | Assign agency |
| POST | `/api/sessions/<id>/lock/` | Brand Lock — lock session |
| POST | `/api/sessions/<id>/unlock/` | Unlock session |
| GET  | `/api/sessions/<id>/answers/` | List answers for session |
| POST | `/api/sessions/<id>/answers/create/` | Create or update answer |
| DELETE | `/api/sessions/<id>/answers/<answer_id>/` | Delete answer |
| GET  | `/api/sessions/<id>/comments/` | List review comments |
| POST | `/api/sessions/<id>/comments/add/` | Add review comment |
| GET  | `/api/sessions/<id>/conversations/` | List AI conversations |
| PATCH | `/api/sessions/<id>/conversations/<conversation_id>/edit/` | Edit conversation |
| POST | `/api/sessions/<id>/answers/<answer_id>/ai-suggestion/` | AI suggestion for answer |
| POST | `/api/sessions/<id>/ai-answer-suggestions/` | AI answer suggestions (e.g. from 2–3 words) |
| POST | `/api/sessions/sessions/<id>/answer-ai-suggestion-from-documents/` | AI suggestion using document context |
| POST | `/api/sessions/<id>/generate-manifesto/` | Generate brand manifesto |
| GET  | `/api/sessions/<id>/manifesto/` | Get manifesto (e.g. JSON) |
| GET  | `/api/sessions/<id>/manifesto/download/` | Download manifesto PDF |
| POST | `/api/sessions/<id>/generate-summary/` | Generate session summary |
| POST | `/api/sessions/<id>/generate-foundation-summary/` | Generate foundation summary (long-running) |
| GET  | `/api/sessions/<id>/foundation-summary/` | Get foundation summary |
| PATCH | `/api/sessions/<id>/update-foundation-summary/` | Update foundation summary |
| POST | `/api/sessions/<id>/generate-social-content/` | Generate social content |
| GET  | `/api/sessions/questions/` | List questions (stages) |
| GET  | `/api/sessions/dashboard/task/` | Client task dashboard |
| GET  | `/api/sessions/dashboard/review/` | Agency review dashboard |

---

## 3. Documents — `/api/document/`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET  | `/api/document/documents/` | List documents |
| POST | `/api/document/documents/` | Upload PDF (multipart: `file`, `title`) |
| GET  | `/api/document/documents/<id>/` | Document detail (includes `is_indexed`) |
| PUT  | `/api/document/documents/<id>/` | Update document |
| DELETE | `/api/document/documents/<id>/` | Delete document and index |
| POST | `/api/document/documents/<id>/search/` | Search within document (body: `query`, `search_type`, `top_k`) |

**Search body (typical):**

- `query`: search text  
- `search_type`: `"vector"` \| `"keyword"` \| `"hybrid"`  
- `top_k`: number of results (optional)

---

## 4. WebSocket

| URL | Purpose |
|-----|---------|
| `ws://127.0.0.1:8000/ws/sessions/<session_pk>/generate-foundation-summary/` | Long-running foundation summary generation; client can send JWT in query or subprotocol for auth. |

Connection and message format are implemented in `user_sessions.consumers.FoundationSummaryConsumer` and `user_sessions.routing.websocket_urlpatterns`.

---

## 5. Admin & API Docs

| URL | Description |
|-----|-------------|
| `/admin/` | Django admin (staff/superuser) |
| `/swagger/` | Swagger UI (OpenAPI) |
| `/redoc/` | ReDoc (OpenAPI) |

---

## 6. Typical Flows

**User and session**

1. `POST /api/auth/register/` or `POST /api/auth/login/` → get tokens.  
2. `POST /api/sessions/create/` → create session.  
3. `POST /api/sessions/<id>/start/` → start.  
4. `GET /api/sessions/questions/` → get questions.  
5. `POST /api/sessions/<id>/answers/create/` for each answer.  
6. `POST /api/sessions/<id>/answers/<answer_id>/ai-suggestion/` for AI help.  
7. `POST /api/sessions/<id>/complete/` then `POST /api/sessions/<id>/lock/` for Brand Lock.  
8. `POST /api/sessions/<id>/generate-manifesto/` → `GET /api/sessions/<id>/manifesto/` or `.../manifesto/download/`.

**Document and search**

1. `POST /api/document/documents/` with PDF → wait until `is_indexed` is true (or poll `GET /api/document/documents/<id>/`).  
2. `POST /api/document/documents/<id>/search/` with `query`, `search_type`, `top_k`.  
3. Use document context in session AI endpoints (e.g. document-based suggestion) as required by the frontend.

All endpoints that modify data require authentication unless otherwise documented (e.g. password reset). Use Swagger/ReDoc for exact request/response shapes and error codes.
