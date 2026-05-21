# Technology Stack

This document lists all major technologies, frameworks, and libraries used in the GodFather Backend.

---

## Core Framework

| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.x | Runtime |
| **Django** | 4.2.27 | Web framework, ORM, admin, middleware |
| **Django REST Framework** | 3.16.1 | REST API, serializers, permissions, pagination |

---

## Database & ORM

| Technology | Purpose |
|------------|---------|
| **SQLite** | Default database for development |
| **PostgreSQL** | Recommended for production (`psycopg2-binary` 2.9.11) |
| **Django ORM** | All database access; no raw SQL in app code |

---

## Authentication & Authorization

| Technology | Version | Purpose |
|------------|---------|---------|
| **djangorestframework-simplejwt** | 5.5.1 | JWT access + refresh tokens |
| **PyJWT** | 2.10.1 | JWT encoding/decoding |
| **Custom User model** | — | Email-based login (no username) |
| **Role-Based Access Control (RBAC)** | — | Roles (admin, agency, client) and permission codenames |
| **Custom permissions** | — | Granular per-resource checks in `accounts.permissions` |

---

## Search & AI

| Technology | Version | Purpose |
|------------|---------|---------|
| **Elasticsearch** | 8.19.1 | Document indexing, vector + keyword search |
| **elasticsearch-dsl** | 8.15.4 | Elasticsearch query building |
| **elastic-transport** | 8.17.1 | Elasticsearch HTTP transport |
| **OpenAI** | 2.3.0 | GPT-4o (chat), text-embedding-ada-002 (embeddings) |
| **Vector embeddings** | — | Semantic search over document chunks |

---

## Task Queue & Messaging

| Technology | Version | Purpose |
|------------|---------|---------|
| **Celery** | 5.5.3 | Async tasks (e.g. document processing) |
| **Redis** | 5.2.1 | Celery broker and result backend |
| **kombu** | 5.5.4 | Message serialization for Celery |
| **amqp** | 5.3.1 | AMQP support (optional) |

---

## Document Processing

| Technology | Version | Purpose |
|------------|---------|---------|
| **PyPDF2** | 3.0.1 | PDF text extraction |
| **pdf2image** | 1.17.0 | PDF → images for OCR |
| **pytesseract** | 0.3.13 | OCR on image-based PDFs |
| **Pillow** | 11.3.0 | Image handling |
| **reportlab** | 4.4.5 | PDF generation (e.g. manifestos) |
| **WeasyPrint** | 66.0 | HTML → PDF (if used) |

---

## Real-Time (WebSockets)

| Technology | Purpose |
|------------|---------|
| **Django Channels** | ASGI, WebSocket routing |
| **channels** (from `requirements.txt` / `INSTALLED_APPS`) | In-memory channel layer (dev); Redis recommended for production |
| **ASGI** | HTTP + WebSocket in one process |

---

## API Documentation

| Technology | Version | Purpose |
|------------|---------|---------|
| **drf-yasg** | 1.21.11 | OpenAPI/Swagger schema and UI |
| **Swagger UI** | — | `/swagger/` |
| **ReDoc** | — | `/redoc/` |

---

## HTTP & Deployment

| Technology | Version | Purpose |
|------------|---------|---------|
| **gunicorn** | 23.0.0 | WSGI HTTP server for production |
| **django-cors-headers** | 4.9.0 | CORS for frontend |

---

## Configuration & Environment

| Technology | Version | Purpose |
|------------|---------|---------|
| **django-environ** | 0.12.0 | Environment variables and `.env` |
| **python-dotenv** | 1.1.1 | Dotenv loading |

---

## Other Notable Dependencies

| Package | Purpose |
|---------|---------|
| **pydantic** | Data validation (e.g. OpenAI client) |
| **httpx / httpcore** | HTTP client (e.g. OpenAI) |
| **urllib3** | HTTP utilities |
| **pytz / tzdata** | Timezone handling |
| **certifi** | SSL certificates |

---

## External Services (Runtime)

- **Elasticsearch** — typically `http://localhost:9200`
- **Redis** — typically `redis://localhost:6379/0`
- **OpenAI API** — requires `OPENAI_API_KEY`
- **SMTP** — e.g. Gmail for password reset (configurable in settings)

---

## Version Summary

- **Django:** 4.2.27  
- **Python:** 3.x (check `python --version` and project docs)  
- **Database:** SQLite (dev) / PostgreSQL (prod)  
- **Broker/backend:** Redis for Celery  
- **Search:** Elasticsearch 8.x  
- **AI:** OpenAI API (GPT-4o, text-embedding-ada-002)  

For the full list with pinned versions, see the project root **`requirements.txt`**.
