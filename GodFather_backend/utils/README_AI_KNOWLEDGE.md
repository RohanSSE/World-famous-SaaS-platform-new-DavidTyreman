# AI Knowledge Base (Training + After-Manifesto)

This folder holds the **knowledge sources** and **scripts** used to train and improve AI responses (David's voice, manifesto principles, post-manifesto scenarios).

## Knowledge files

- **`training-AI-tool.txt`** – Training playbook: 10 principles, avatar behaviour, tone phases, guardrails, intake/coaching/output phases.
- **`after-manifesto-ai-tool.txt`** – Post-manifesto: content prompts, scenario coaching (crisis, launch, customer service, social, blog, culture, ad copy).

These are chunked, embedded, and stored in Elasticsearch for **RAG (retrieval-augmented generation)** so the AI uses this context when answering.

## Flow

1. **Build index (one-time or after editing the .txt files)**  
   From project root:
   ```bash
   python manage.py build_ai_knowledge
   ```
   - Reads both `.txt` files from `utils/`
   - Chunks with overlap (see `utils/ai_knowledge_config.py`)
   - Generates embeddings via **Azure OpenAI** (see Environment below)
   - Creates/overwrites Elasticsearch index `ai_knowledge`

2. **Retrieval at runtime**  
   - **AI suggestion (improve answer)** – Retrieves knowledge by question + draft and appends to “KB context” so David’s method and tone guide the reply.
   - **Manifesto generation** – Retrieves by “brand manifesto principles tone voice” and injects into the system prompt.
   - **Session summary** – Retrieves by “brand summary synthesis…” and injects into the system prompt.

3. **Config**  
   - Chunk size / overlap / index name: `utils/ai_knowledge_config.py`
   - Top-k and search type: `utils/retrieve_ai_knowledge.py` (defaults) and call sites in `user_sessions/views.py`

## Environment (Azure OpenAI only)

All AI features (chat and embeddings) use **Azure OpenAI** only.

- **Required:** `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`
- **Chat:** `AZURE_OPENAI_DEPLOYMENT_NAME` (e.g. `gpt-4o`)
- **Embeddings:** `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` (e.g. `text-embedding-ada-002`)
- Optional: `AZURE_OPENAI_API_VERSION` (default `2024-02-01`)

If the embedding deployment does not exist in your Azure resource, `build_ai_knowledge` will fail with `DeploymentNotFound`; create that deployment in the Azure portal.

## Where code lives

- **Misc / data under `utils/`**  
  - `training-AI-tool.txt`, `after-manifesto-ai-tool.txt`  
  - `ai_knowledge_config.py`, `chunk_knowledge.py`, `build_ai_knowledge_index.py`, `retrieve_ai_knowledge.py`  
  - This README

- **App code**  
  - `user_sessions/views.py` – uses `retrieve_ai_knowledge` and `format_knowledge_context` in manifesto, summary, and AI suggestion.  
  - `user_sessions/management/commands/build_ai_knowledge.py` – management command.  
  - `document/utils/embedding_service.py` – Azure OpenAI embeddings only.  
  - `document/utils/elasticsearch_service.py` – shared for document and AI knowledge indexes.

## Optimizing retrieval

- **Chunk size / overlap** – Tune in `ai_knowledge_config.py` (e.g. `AI_KNOWLEDGE_CHUNK_SIZE`, `AI_KNOWLEDGE_CHUNK_OVERLAP`).
- **Top-k** – Increase in `retrieve_ai_knowledge()` calls or in `ai_knowledge_config.AI_KNOWLEDGE_TOP_K`.
- **Search type** – `hybrid` (default) uses both vector and keyword; use `vector` or `keyword` if needed.
- **Context length** – `format_knowledge_context(..., max_chars=...)` in views to avoid overflowing the model context.
