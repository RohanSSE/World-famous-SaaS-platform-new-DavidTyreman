# Project Architecture

This document describes the high-level architecture of the GodFather Backend so other developers can understand how the system is structured and how data flows.

---

## 1. What the System Does

GodFather Backend is an **AI-assisted branding questionnaire platform**. It provides:

- **Multi-tenant agencies** — Organizations (agencies) with users (clients, agency staff, admins).
- **Branding sessions** — Clients run through a staged questionnaire; answers can be improved with AI suggestions.
- **Document context** — Users upload PDFs; text is extracted, chunked, embedded, and indexed in Elasticsearch so AI suggestions can use document-based context.
- **Brand Lock** — Sessions can be locked so answers cannot be edited without unlocking.
- **Manifesto generation** — From session answers, the system can generate a brand manifesto (e.g. JSON + PDF).
- **Real-time** — WebSockets (e.g. foundation summary generation) for long-running AI operations.

---

## 2. Top-Level Project Structure

```
GodFather_backend/
├── project/              # Django project config
│   ├── settings.py       # All app settings
│   ├── urls.py           # Root URL routing
│   ├── wsgi.py           # WSGI entry (e.g. Gunicorn)
│   ├── asgi.py           # ASGI entry (HTTP + WebSocket)
│   └── celery.py         # Celery app config
├── accounts/             # Users, roles, agencies, auth
├── document/             # PDF upload, processing, search
├── user_sessions/        # Questionnaire sessions, answers, AI, manifesto
├── manage.py
├── requirements.txt
└── docs/                 # This documentation
```

---

## 3. Application Breakdown

### 3.1 `accounts` — Authentication & Tenancy

- **Purpose:** User identity, login, roles, permissions, and multi-tenant agencies.
- **Key models:** `User` (email-based), `Role`, `Permission`, `Agency`, `Dashboard`.
- **Auth:** JWT (access + refresh) via `djangorestframework-simplejwt`.
- **URL prefix:** `/api/auth/` (see [API_OVERVIEW.md](./API_OVERVIEW.md)).

Responsibilities:

- Registration, login, password change, password reset.
- CRUD for roles, permissions, agencies.
- Current user profile (`/me/`).
- All permission checks ultimately depend on user role and optional permission codenames.

---

### 3.2 `document` — Documents & Search

- **Purpose:** Upload PDFs, extract text, chunk, embed, index in Elasticsearch, and run semantic/keyword search.
- **Key models:** `Document` (file, metadata, `is_indexed`).
- **URL prefix:** `/api/document/`.

Flow:

1. Client uploads PDF → `Document` created, `is_indexed=False`.
2. Celery task `process_document_task` runs: extract text (PyPDF2 + OCR fallback) → chunk (e.g. 500 chars, overlap) → generate embeddings (OpenAI) → create/index Elasticsearch index.
3. Document marked `is_indexed=True`.
4. Search API: vector, keyword, or hybrid search over that document’s index.

**Static RAG library (`Rag_doc/`):** Categorized knowledge under `branding/`, `manifesto`, `psychology/`, `strategy/`, `positioning/`, `sales/`, `marketing/` is indexed via `python manage.py build_ai_knowledge` into the shared `ai_knowledge` Elasticsearch index (see `utils/rag_doc_loader.py`).

Utilities under `document/utils/`:

- **PDFProcessor** — Extract text, chunking.
- **EmbeddingService** — OpenAI embeddings.
- **ElasticsearchService** — Index creation, indexing, search.

---

### 3.3 `user_sessions` — Questionnaire & AI

- **Purpose:** Branding questionnaire sessions, answers, AI suggestions, manifesto, and real-time updates.
- **Key models:** `Session`, `Question`, `Answer`, `Conversation`, `ReviewComment`, `AIOutput`, `FoundationSummary` (if present).
- **URL prefix:** `/api/sessions/`.
- **WebSocket:** e.g. `ws/sessions/<id>/generate-foundation-summary/` (see `user_sessions/routing.py` and `consumers.py`).

Session lifecycle:

- **Status:** `draft` → `in_progress` → `completed` → `locked`.
- **Brand Lock:** `is_locked` prevents editing answers; unlock may require password/flow defined in views.
- **Access:** Creator, assigned agency (for review), and admins; enforced in views and permission classes.

Question stages (e.g. Foundation, Identity, Strategy, Visual, Messaging) drive ordering and access. AI suggestion flow:

- Load question, current answer, conversation history, foundation answer (if any), and optional document context from Elasticsearch.
- Build prompt → call OpenAI GPT-4o → return improved answer + optional follow-up; store in `Conversation`.

Manifesto: generated from answers (e.g. JSON + PDF download). WebSocket consumer streams or notifies when long-running steps (e.g. foundation summary) complete.

---

## 4. Request Flow (HTTP)

```
Client
  → CORS / Security middleware
  → Django URL router (project/urls.py)
  → App URLs (accounts, document, user_sessions)
  → View/ViewSet
  → Permission checks (JWT + RBAC/custom)
  → Serializer (validation)
  → Model / Elasticsearch / OpenAI / Celery
  → JSON response
```

- **Auth:** `Authorization: Bearer <access_token>`.
- **Default:** All API views require authentication unless explicitly allowed (e.g. password reset, Swagger/ReDoc).

---

## 5. Authentication Flow

1. User registers or logs in via `/api/auth/` → receives **access** and **refresh** tokens.
2. Client stores tokens and sends `Authorization: Bearer <access_token>` on each request.
3. `JWTAuthentication` validates token and attaches `User` to `request`.
4. View/permission code checks `request.user`, role, and optional permission codenames (e.g. `has_perm` or custom logic in `accounts.permissions`).

---

## 6. Document Processing Flow (Async)

1. POST document → `Document` created → Celery task enqueued.
2. Worker: extract text → chunk → embeddings → create ES index → bulk index chunks.
3. Document updated to `is_indexed=True`.
4. Search endpoints use that index (vector, keyword, or hybrid).

---

## 7. Database Relationships (Simplified)

- **User** N→1 **Agency** (optional); User M→N **Role** (via role assignment).
- **Session** 1→1 **User** (created_by); Session N→1 **Agency** (optional assignment).
- **Session** 1→N **Answer**; each **Answer** 1→1 **Question**.
- **Session** 1→N **Conversation** (e.g. per question); 1→1 **AIOutput** (manifesto).
- **Document** N→1 **User** (uploaded_by).

All access control (who can see/edit sessions, documents, agencies) is enforced in views and permission classes using these relationships and roles.

---

## 8. Concurrency & Scaling

- **HTTP:** Stateless; scale by running more Django/Gunicorn workers.
- **Celery:** One or more workers; broker and result backend in Redis. Scale by adding workers or queues.
- **Elasticsearch:** Single node for dev; cluster for production.
- **Channels:** In-memory layer in dev; use Redis channel layer in production for multi-process WebSocket support.

---

## 9. Security Highlights

- JWT with refresh rotation; optional blacklist.
- RBAC + custom permission codenames.
- CORS configured (restrict origins in production).
- File upload: PDF only, size limits in settings.
- Session lock prevents editing without unlock.
- Passwords hashed by Django; password reset via email token.

---

## 10. Where to Look Next

- **Endpoints and usage:** [API_OVERVIEW.md](./API_OVERVIEW.md)
- **Tech versions and services:** [TECH_STACK.md](./TECH_STACK.md)
- **Setup and run:** [GETTING_STARTED.md](./GETTING_STARTED.md)
- **Production:** [DEPLOYMENT.md](./DEPLOYMENT.md)
