# BrandGodFather Manual RAG Runbook

This runbook is for developers who want to manually run, validate, and clean re-ingest the BrandGodFather RAG corpus.

## 1. Preconditions

1. Elasticsearch Node 2 is running and reachable from Django (`ES_NODE_2`).
2. Redis is running for Celery broker.
3. Python venv is active or commands use the venv Python directly.
4. Azure OpenAI embedding env vars are set (`AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, embedding deployment settings).

## 2. Create Fresh BrandGodFather Indices

Run from `GodFather_backend`:

```powershell
$env:SKIP_PROSODY_PRELOAD="1"
$env:SKIP_RAG_PRELOAD="1"
.\venv\Scripts\python.exe manage.py create_brandgodfather_indices
```

Expected indices:

- `brandgodfather_brand_chunks`
- `brandgodfather_sessions`
- `brandgodfather_episodic`

## 3. Start/Verify Celery Worker

Start worker (same shell location: `GodFather_backend`):

```powershell
.\venv\Scripts\python.exe -m celery -A project worker -l info -Q project.default -n celery@rohana --pool=solo
```

From another shell, verify registered worker tasks:

```powershell
.\venv\Scripts\python.exe manage.py shell -c "from celery import current_app; print(current_app.control.inspect().registered())"
```

`brandgodfather.tasks.ingest_pdf_task` should be present.

## 4. Dispatch PDF Ingestion

```powershell
$env:SKIP_PROSODY_PRELOAD="1"
$env:SKIP_RAG_PRELOAD="1"
.\venv\Scripts\python.exe manage.py ingest_brandgodfather_pdfs --dir "RAG-docsv2"
```

## 5. Verify Indexed Document Count

```powershell
.\venv\Scripts\python.exe manage.py shell -c "from elasticsearch_dsl import connections; from brandgodfather.documents import BRANDGODFATHER_NODE_2_ALIAS; es=connections.get_connection(alias=BRANDGODFATHER_NODE_2_ALIAS); print(es.count(index='brandgodfather_brand_chunks'))"
```

If count is `0`, inspect worker logs and queue state.

## 6. Verify Retrieval End-to-End (Service Level)

Use query parameters aligned with current corpus metadata (currently most chunks are `question_id=general`, `phase=general`):

```powershell
.\venv\Scripts\python.exe manage.py shell -c "from brandgodfather.services.rag_retrieval import HybridRAGService; s=HybridRAGService(); ctx=s.get_question_context(q_id='general', phase='', user_answer='I reject generic positioning and vendor language.', pressure_level=3, session={'brand_type':'rebel'}); print(ctx.model_dump())"
```

Expected: non-empty `question_chunks` and/or `challenge_chunks`.

## 7. Diagnose Metadata Shape (Optional but Recommended)

```powershell
.\venv\Scripts\python.exe manage.py shell -c "from elasticsearch_dsl import connections; from brandgodfather.documents import BRANDGODFATHER_NODE_2_ALIAS; es=connections.get_connection(alias=BRANDGODFATHER_NODE_2_ALIAS); body={'size':0,'aggs':{'qids':{'terms':{'field':'question_id','size':10}},'phases':{'terms':{'field':'phase','size':10}},'types':{'terms':{'field':'chunk_type','size':10}}}}; r=es.search(index='brandgodfather_brand_chunks',body=body); print(r['aggregations'])"
```

## 8. Remove "Synapse" from Indexed Content Cleanly

### Current source hit inventory

At the time of this runbook update:

- `BrandGodFather_Logic_Schema_v1.2.pdf`: contains `Synapse` mentions
- `Vessel & Craft FINAL Brand Book.pdf`: contains `0` Synapse mentions

### Clean procedure

1. Edit/replace `RAG-docsv2/BrandGodFather_Logic_Schema_v1.2.pdf` to remove legacy "Synapse" wording.
2. Recreate or clear target index data.
3. Re-ingest PDFs.
4. Validate no residual mentions:

```powershell
.\venv\Scripts\python.exe manage.py shell -c "from elasticsearch_dsl import connections; from brandgodfather.documents import BRANDGODFATHER_NODE_2_ALIAS; es=connections.get_connection(alias=BRANDGODFATHER_NODE_2_ALIAS); r=es.search(index='brandgodfather_brand_chunks', body={'size':5,'query':{'multi_match':{'query':'Synapse','fields':['text']}}}); print(r['hits']['total']); [print(h['_source'].get('chunk_id')) for h in r['hits']['hits']]"
```

## 9. Do We Need to Retrain Embeddings?

No model retraining is required for this rename.

- Re-ingestion re-generates vectors for documents into the current index.
- Retraining is only needed if you intentionally change to a custom embedding model strategy.
