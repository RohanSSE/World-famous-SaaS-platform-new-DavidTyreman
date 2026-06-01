# RAG Knowledge Library (`Rag_doc/`)

Drop training and reference documents here. They are chunked, embedded, and indexed into Elasticsearch (`ai_knowledge`) for RAG at runtime.

Legacy flat PDFs placed in `Rag_docs/` are also indexed. Their category is inferred from the filename, so new brand books and briefs dropped there become available to RAG after the index rebuilds.

## Folder layout

| Folder | Use for |
|--------|---------|
| `branding/` | Brand identity, voice, David's method, coaching playbooks |
| `manifesto/` | Manifesto structure, post-manifesto scenarios, output templates |
| `psychology/` | Emotional drivers, customer psychology, behaviour |
| `strategy/` | Brand strategy, planning, long-term direction |
| `positioning/` | Differentiation, market position, competitive framing |
| `sales/` | Sales narrative, objections, conversion language |
| `marketing/` | Campaigns, content, channels, messaging execution |

## Supported file types

- `.txt`, `.md`, `.markdown` — plain text
- `.pdf` — text extraction + OCR fallback (same pipeline as user uploads)

## Auto indexing (default)

The backend **automatically** rebuilds the `ai_knowledge` Elasticsearch index when:

1. **Django starts** — queues a Celery task if Rag_doc changed or index is missing  
2. **Every 6 hours** — Celery Beat schedule (`ai-knowledge-index-refresh`)  
3. **Before AI retrieval** — checks fingerprint when RAG runs  
4. **After you add/edit files** — next check detects new fingerprint and rebuilds  

**Requirements:** Redis, Celery worker, Elasticsearch, Azure embeddings.

```bash
# Terminal 1 — API
python manage.py runserver

# Terminal 2 — worker (required for auto-index)
celery -A project worker -l info

# Terminal 3 — optional periodic checks
celery -A project beat -l info
```

### Manual commands

```bash
# Queue rebuild if stale (same as auto)
python manage.py build_ai_knowledge

# Force full rebuild now (sync, no Celery)
python manage.py build_ai_knowledge --force --sync

# Show fingerprint / status only
python manage.py build_ai_knowledge --status
```

Disable auto-index: set `AI_KNOWLEDGE_AUTO_INDEX = False` in `project/settings.py`.

## Notes

- Files in subfolders are included (recursive).
- Category name is stored in chunk metadata as `source` / `category` for retrieval debugging.
- Legacy files under `utils/training-AI-tool.txt` are still ingested if `INCLUDE_LEGACY_UTILS_TXT` is enabled in `utils/ai_knowledge_config.py`.
