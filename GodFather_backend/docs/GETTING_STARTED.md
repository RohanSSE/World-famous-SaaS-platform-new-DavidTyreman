# Getting Started

This guide helps a new developer set up the GodFather Backend locally and run it end-to-end.

---

## Prerequisites

- **Python** 3.10+ (recommended; check with `python --version`)
- **Redis** — for Celery broker and result backend
- **Elasticsearch** 8.x — for document search
- **Tesseract OCR** — for image-based PDF text extraction (optional but recommended for full document processing)
- **Poppler** — for `pdf2image` (PDF → images)

---

## 1. Clone and Enter Project

```bash
cd path/to/GodFather_backend
```

---

## 2. Virtual Environment (Recommended)

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4. System Dependencies (for PDF + OCR)

**Windows**

- Install [Tesseract](https://github.com/UB-Mannheim/tesseract/wiki) and add it to `PATH`, or set `TESSERACT_CMD` in `.env` to the executable path (e.g. `C:\...\tesseract.exe`).
- Poppler: use a Windows build or Chocolatey, and ensure `pdf2image` can find it.

**Ubuntu/Debian**

```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr poppler-utils
```

**macOS**

```bash
brew install tesseract poppler
```

---

## 5. Environment Variables

Create a `.env` file in the project root (optional; many defaults are in `project/settings.py`):

```env
# Optional overrides
SECRET_KEY=your-secret-key-here
DEBUG=True
OPENAI_API_KEY=sk-...
ELASTICSEARCH_HOSTS=http://localhost:9200
REDIS_URL=redis://localhost:6379/0
TESSERACT_CMD=/usr/bin/tesseract
# For password reset emails
FRONTEND_BASE_URL=http://localhost:3000
```

- **OPENAI_API_KEY** is required for AI suggestions and document embeddings.
- Other values default to localhost if not set.

---

## 6. Database

Default is SQLite (no extra setup):

```bash
python manage.py migrate
```

For PostgreSQL, configure `DATABASES` in `project/settings.py` (or via `django-environ` and `DATABASE_URL`), then run `migrate` again.

---

## 7. Create Media Directory

```bash
mkdir -p media
# or on Windows: mkdir media
```

Used for uploaded PDFs and generated files.

---

## 8. Start External Services

**Redis**

- Local: start Redis on `localhost:6379`, or set `CELERY_BROKER_URL` / `REDIS_URL` to your Redis URL.

**Elasticsearch**

- Start Elasticsearch (e.g. on `http://localhost:9200`), or set `ELASTICSEARCH_HOSTS` in settings/`.env`.

**Optional: Docker**

- If you use Docker for Redis and Elasticsearch, start those containers before running the app.

---

## 9. Run the Application

**Terminal 1 — Django**

```bash
python manage.py runserver
```

API: `http://127.0.0.1:8000/`  
Admin: `http://127.0.0.1:8000/admin/`  
Swagger: `http://127.0.0.1:8000/swagger/`  
ReDoc: `http://127.0.0.1:8000/redoc/`

**Terminal 2 — Celery worker**

```bash
celery -A project worker -Q project.default --pool=solo -c 1 --loglevel=info
```

- Required for document processing (indexing PDFs).
- On Windows, `--pool=solo` is typically needed.

**Optional — WebSockets (ASGI)**

For WebSocket endpoints (e.g. foundation summary):

```bash
uvicorn project.asgi:application --host 0.0.0.0 --port 8000
```

Or use Daphne/another ASGI server; ensure `project.asgi.application` is used so both HTTP and WebSocket are served.

---

## 10. Create a Superuser (Optional)

```bash
python manage.py createsuperuser
```

Use this account to log in to Django admin and (if your frontend supports it) to get JWT tokens for testing.

---

## 11. Create Permissions (Optional)

If the project uses custom permission codenames:

```bash
python manage.py create_permissions
```

---

## 12. Quick API Check

1. **Register:** `POST /api/auth/register/` with `email` and `password`.
2. **Login:** `POST /api/auth/login/` with same credentials → get `access` and `refresh` in response.
3. **Profile:** `GET /api/auth/me/` with header `Authorization: Bearer <access>`.
4. **Sessions:** `GET /api/sessions/` with same header.

Use Swagger at `/swagger/` to explore and call endpoints.

---

## Troubleshooting

| Issue | What to check |
|-------|----------------|
| Tesseract errors | Install Tesseract and set `TESSERACT_CMD` if needed; optional for text-only PDFs. |
| Celery not processing tasks | Redis running; worker started with `celery -A project worker ...`. |
| Elasticsearch connection errors | Elasticsearch running on port 9200 (or `ELASTICSEARCH_HOSTS`). |
| OpenAI errors | Valid `OPENAI_API_KEY` in environment or settings. |
| CORS errors from frontend | `CORS_ALLOW_ALL_ORIGINS` or `CORS_ALLOWED_ORIGINS` in `project/settings.py`. |
| Migrations | Run `python manage.py migrate` after pulling or changing models. |

---

## Next Steps

- **[API_OVERVIEW.md](./API_OVERVIEW.md)** — List of endpoints and how to use them.
- **[ARCHITECTURE.md](./ARCHITECTURE.md)** — How the project is structured.
- **[DEPLOYMENT.md](./DEPLOYMENT.md)** — Production deployment.
