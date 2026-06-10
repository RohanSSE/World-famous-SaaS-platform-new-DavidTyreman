# Deployment Guide

This document describes how to deploy the GodFather Backend to a production-like environment so other developers or DevOps can run it reliably.

---

## 1. Requirements

- **Application:** Django (Gunicorn) or ASGI server (e.g. Daphne/Uvicorn) if WebSockets are needed.
- **Database:** PostgreSQL (recommended); SQLite only for dev.
- **Broker/backend:** Redis (Celery).
- **Search:** Elasticsearch 8.x.
- **Optional:** SMTP server for password reset and notifications.

---

## 2. Environment Variables

Set these in the host or in a `.env` file (with `django-environ` / `python-dotenv`). Do **not** commit secrets.

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key | Long random string |
| `DEBUG` | Debug mode | `False` in production |
| `ALLOWED_HOSTS` / `DJANGO_ALLOWED_HOSTS` | Comma-separated hosts | `yourdomain.com,api.yourdomain.com` |
| `DATABASE_URL` | PostgreSQL URL | `postgresql://user:pass@host:5432/dbname` |
| `OPENAI_API_KEY` | OpenAI API key | `sk-...` |
| `ELASTICSEARCH_HOSTS` | Elasticsearch URLs | `http://es:9200` |
| `REDIS_URL` / `CELERY_BROKER_URL` | Redis URL | `redis://redis:6379/0` |
| `EMAIL_HOST_USER` | SMTP user | Your SMTP user |
| `EMAIL_HOST_PASSWORD` | SMTP password | Your SMTP password |
| `FRONTEND_BASE_URL` | Frontend base URL | `https://app.yourdomain.com` |
| `TESSERACT_CMD` | Tesseract binary path | `/usr/bin/tesseract` |

In `project/settings.py`, use `env()` for these (e.g. `SECRET_KEY = env('SECRET_KEY')`) and keep defaults only for non-sensitive, dev-only values.

---

## 3. Database (PostgreSQL)

1. Create database and user.
2. Set `DATABASE_URL` or configure `DATABASES` in settings.
3. Run migrations:

   ```bash
   python manage.py migrate
   ```

4. (Optional) Create superuser: `python manage.py createsuperuser`.
5. (Optional) Run custom commands: e.g. `python manage.py create_permissions`.

---

## 4. Static and Media Files

- **Static:** Collect for production:

  ```bash
  python manage.py collectstatic --noinput
  ```

  Serve the collected directory via Nginx (or your reverse proxy); do not rely on Django to serve static in production.

- **Media:** Set `MEDIA_ROOT` to a persistent volume; serve via Nginx (e.g. `location /media/`) or CDN. Ensure the app has write permission.

---

## 5. Running the Application

**Option A — WSGI (no WebSockets)**

```bash
gunicorn project.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

**Option B — ASGI (HTTP + WebSockets)**

```bash
daphne -b 0.0.0.0 -p 8000 project.asgi:application
# or
uvicorn project.asgi:application --host 0.0.0.0 --port 8000
```

Use a process manager (systemd, Supervisor, or Docker) so the app restarts on failure.

### Supervisor example

A ready-to-edit Supervisor config is available at `deploy/supervisor/godfather.conf.example`.

This repo uses these default supervised ports:

- Backend API: `0.0.0.0:8001`
- Frontend static preview: `0.0.0.0:3003`

On the server, replace `/srv/godfather` in the example with the absolute repo path, ensure `/var/log/godfather` exists, then load it with Supervisor.

---

## 6. Celery Worker

Run one or more workers:

```bash
celery -A project worker -Q project.default --loglevel=info
```

- For production, use a proper pool (e.g. `prefork`) and tune concurrency.
- Run beat only if you add periodic tasks: `celery -A project beat --loglevel=info`.

Use the same `REDIS_URL` / `CELERY_BROKER_URL` and ensure Redis is available.

---

## 7. Redis

- Use a dedicated Redis instance for Celery (broker + result backend).
- For Django Channels (WebSockets), configure a Redis channel layer in production:

  ```python
  CHANNEL_LAYERS = {
      "default": {
          "BACKEND": "channels_redis.core.RedisChannelLayer",
          "CONFIG": {"hosts": [os.environ.get("REDIS_URL", "redis://localhost:6379/0")]},
      }
  }
  ```

  Install: `channels-redis`.

---

## 8. Elasticsearch

- Run Elasticsearch 8.x (single node or cluster).
- Set `ELASTICSEARCH_HOSTS` to the production URL(s).
- No need to pre-create indexes; the app creates them when documents are processed.

---

## 9. Reverse Proxy (Nginx Example)

- Terminate SSL at Nginx.
- Proxy `/` to Gunicorn/Daphne (e.g. `http://127.0.0.1:8000`).
- Serve `/static/` and `/media/` from disk.
- Set `Host` and `X-Forwarded-Proto` so Django sees the correct host and scheme.

Example (minimal):

```nginx
server {
    listen 443 ssl;
    server_name api.yourdomain.com;
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /path/to/static/;
    }
    location /media/ {
        alias /path/to/media/;
    }
}
```

---

## 10. Security Checklist

- Set `DEBUG = False`.
- Use a strong, unique `SECRET_KEY`.
- Restrict `ALLOWED_HOSTS`.
- Restrict CORS (e.g. `CORS_ALLOWED_ORIGINS`) to your frontend origin(s).
- Use HTTPS only; set `SECURE_PROXY_SSL_HEADER` if behind a proxy.
- Store DB, Redis, and API keys in env or a secret manager; never in code.
- Keep dependencies updated: `pip install -r requirements.txt --upgrade` and review CVEs.

---

## 11. Monitoring and Logging

- Point Django `LOGGING` to files or a logging service.
- Consider error tracking (e.g. Sentry) for uncaught exceptions.
- Health checks: a simple view that returns 200 and checks DB/Redis (optional) helps load balancers and orchestrators.

---

## 12. Summary of Services

| Service | Purpose |
|---------|---------|
| Django (Gunicorn/Daphne) | HTTP (and WebSocket if ASGI) |
| Celery worker | Document processing, async tasks |
| Redis | Celery broker/backend; Channels layer (if used) |
| PostgreSQL | Main database |
| Elasticsearch | Document search |
| Nginx (or similar) | Reverse proxy, static/media, SSL |

Use the same codebase and env configuration across environments; only the values of the environment variables should differ between staging and production.
