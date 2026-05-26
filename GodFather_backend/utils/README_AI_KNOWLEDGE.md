# AI Knowledge Base (RAG)

Knowledge for David's voice, manifesto, and coaching is stored under **`Rag_doc/`**, chunked, embedded, and indexed into Elasticsearch (`ai_knowledge`).

## Rag_doc layout

```
Rag_doc/
├── branding/
├── manifesto/
├── psychology/
├── strategy/
├── positioning/
├── sales/
└── marketing/
```

Supported: `.txt`, `.md`, `.pdf` (PDF uses the same extract/OCR pipeline as user document uploads).

## Auto indexing

Enabled by default (`AI_KNOWLEDGE_AUTO_INDEX`, `AI_KNOWLEDGE_AUTO_INDEX_ON_STARTUP` in `project/settings.py`).

- Fingerprints all files under `Rag_doc/`; rebuilds only when content changes.
- State file: `data/ai_knowledge_index_state.json` (gitignored).
- Celery task: `user_sessions.tasks.rebuild_ai_knowledge_index_task`.

Run worker: `celery -A project worker -l info`  
Optional beat: `celery -A project beat -l info`

## Manual build

```bash
python manage.py build_ai_knowledge          # queue if stale
python manage.py build_ai_knowledge --sync --force   # immediate full rebuild
python manage.py build_ai_knowledge --status        # inspect only
```

## Flow

1. **Ingest** — `utils/rag_doc_loader.py` discovers files per category → `chunk_knowledge.py` chunks with overlap.
2. **Embed** — Azure OpenAI (`AZURE_OPENAI_EMBEDDING_DEPLOYMENT`).
3. **Index** — Elasticsearch index `ai_knowledge`.
4. **Retrieve** — `utils/retrieve_ai_knowledge.py` (hybrid search) used in AI suggestion, manifesto, summaries.

## Legacy files

`utils/training-AI-tool.txt` and `utils/after-manifesto-ai-tool.txt` are still loaded when `INCLUDE_LEGACY_UTILS_TXT = True` in `ai_knowledge_config.py`. Copies are also placed under `Rag_doc/branding/` and `Rag_doc/manifesto/` for the primary pipeline.

## Environment (Azure OpenAI)

- `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` (e.g. `text-embedding-3-small`, 1536 dims)
- Elasticsearch at `ELASTICSEARCH_HOSTS` (default `http://localhost:9200`)

## Config

- `utils/ai_knowledge_config.py` — paths, categories, chunk size, top-k
- `utils/retrieve_ai_knowledge.py` — runtime retrieval
