# BrandGodfather — RAGv2 Backend Architecture
## Agent Prompt Specification (Django + Celery + Elasticsearch + Azure AI)
### Version: RAGv2 | Coach Identity: BrandGodfather | Orchestration: Pure Python

---

> **RAGv2 Scope:** This entire document describes the creation of a second, isolated RAG pipeline
> called **RAGv2**. It runs on **Elasticsearch Node 2** (separate from your existing Node 1).
> All new indices, embeddings, session memory, and chunk storage created in this session
> belong exclusively to RAGv2. Node 1 and its existing embeddings are never modified.

> **No LangGraph. No LangChain.** The orchestration engine is pure Python —
> a sequential pipeline function with a built-in rejection loop using a `while` construct.
> The LLM is called directly via the API credentials stored in `.env`.

---

## Orchestration Design — Pure Python Pipeline

```
The enforcement loop in plain Python:

def run_coaching_pipeline(session_state: dict) -> dict:

    # Gate 1 — deterministic, instant
    vendor_result = VendorLanguageFilter.check(session_state["raw_answer"])
    if vendor_result["fail"]:
        return build_reject_response(vendor_result)

    # Gate 2 — ML classifiers
    prosody_result = ProsodyClassifier.analyze(
        session_state["raw_answer"],
        session_state["current_question"]
    )

    # Load memory from ES Node 2
    memory = load_episodic_memory(session_state["session_id"])

    # Update shadow profile (rule-based, no LLM)
    shadow = update_shadow_profile(memory["shadow_profile"], prosody_result)

    # Check for contradictions against past answers in ES Node 2
    contradiction = check_contradictions(
        session_state["session_id"],
        session_state["raw_answer"]
    )

    # RAGv2 retrieval from ES Node 2
    chunks = retrieve_rag_chunks(
        question_id=session_state["current_question"],
        pressure_level=memory["pressure_level"],
        query=session_state["raw_answer"],
        brand_seed=memory["brand_seed"]
    )

    # Enforcement loop — max 5 rejection cycles
    rejection_count = 0
    gate_status = "REJECT"

    while gate_status == "REJECT" and rejection_count < 5:

        # Assemble prompt with current pressure level
        system_prompt, user_prompt = assemble_prompt(
            session_state, memory, prosody_result,
            chunks, shadow, rejection_count
        )

        # Gate 3 — LLM call (credentials from .env)
        llm_result = call_llm(system_prompt, user_prompt)

        gate_status = llm_result["gate_status"]

        if gate_status == "REJECT":
            rejection_count += 1
            memory["pressure_level"] = min(memory["pressure_level"] + 1, 5)
            # Re-assemble prompt with higher pressure next iteration
            # RAG chunks already loaded — no re-retrieval in loop

    # Write to ES Node 2 and Django DB
    write_memory(session_state, memory, llm_result, prosody_result)

    return llm_result
```

The loop is the entire "graph." No framework needed.

---

## RAGv2 Full Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Django REST API                          │
│         /api/session/  /api/answer/  /api/brandbook/        │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                  Celery Task Queue (RAGv2)                  │
│         process_answer.delay(session_id, answer)            │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│         Pure Python Orchestration Engine (RAGv2)           │
│         apps/coaching/pipeline/orchestrator.py              │
│                                                             │
│  Step 1: VendorLanguageFilter.check()   ← Gate 1           │
│  Step 2: ProsodyClassifier.analyze()    ← Gate 2           │
│  Step 3: load_episodic_memory()         ← ES Node 2        │
│  Step 4: update_shadow_profile()        ← rule-based       │
│  Step 5: check_contradictions()         ← ES Node 2        │
│  Step 6: retrieve_rag_chunks()          ← ES Node 2        │
│  Step 7: while loop begins              ← enforcement      │
│    Step 7a: assemble_prompt()                               │
│    Step 7b: call_llm()                  ← .env credentials │
│    Step 7c: gate_enforcer()                                 │
│    Step 7d: escalate pressure if REJECT                     │
│  Step 8: write_memory()                 → ES Node 2        │
└─────────────────────────────────────────────────────────────┘
```

---

## Elasticsearch Node Strategy

```
Node 1 (EXISTING — DO NOT MODIFY):
  - Index: your existing brandgodfather_docs
  - Contains: chunked PDFs from earlier pipeline (RAGv1)
  - Embeddings: already stored
  - READ-ONLY access from RAGv2 for archetype context retrieval only

Node 2 (NEW — RAGv2 — build everything here):
  - Index: brandgodfather_sessions        (per-answer memory)
  - Index: brandgodfather_episodic        (shadow profile + thread index)
  - Index: brandgodfather_chunks_v2       (new PDF chunks + embeddings)
  - All embeddings: sentence-transformers or LLM API embeddings from .env
```

---

## File Structure (RAGv2)

```
apps/coaching/
├── models.py                              ← STEP 1
├── views.py                               ← STEP 7
├── serializers.py                         ← STEP 7
├── urls.py                                ← STEP 7
├── classifiers.py                         ← STEP 4
├── pipeline/
│   ├── __init__.py
│   ├── orchestrator.py                    ← STEP 5  (main pipeline)
│   ├── memory.py                          ← STEP 5  (ES read/write)
│   ├── retriever.py                       ← STEP 5  (RAGv2 retrieval)
│   ├── llm_client.py                      ← STEP 5  (LLM API caller)
│   └── prompts.py                         ← STEP 6  (prompt assembly)
├── tasks/
│   ├── __init__.py
│   ├── ingestion.py                       ← STEP 3
│   ├── coaching.py                        ← STEP 7
│   └── brandbook.py                       ← STEP 8
└── management/
    └── commands/
        ├── setup_es_node2.py              ← STEP 2
        └── ingest_brandgodfather_pdfs.py  ← STEP 3
```

---

---

# STEP 1 — Django Models & Session State

> **Agent Prompt 1 — run this first, nothing depends on it yet**

```
Build Django models for the BrandGodfather coaching system (RAGv2).

All models go in: apps/coaching/models.py
Use Django 4.2+. Do not modify any existing models outside this file.

─────────────────────────────────────────────
MODEL 1: CoachingSession
─────────────────────────────────────────────
Fields:
  session_id            UUIDField, primary_key=True, default=uuid.uuid4
  user_id               ForeignKey to settings.AUTH_USER_MODEL
  current_question      IntegerField, default=1
  status                CharField, choices:
                          COLLECTING  (context data form phase)
                          DISCOVERY   (Q1–Q30 active)
                          OUTPUT      (BrandBook generating)
                          COMPLETE    (session finished)
                        default=COLLECTING
  brand_seed            CharField, max_length=200, blank=True
  three_word_foundation JSONField, default=dict
  thread_index          JSONField, default=dict
  shadow_profile        JSONField, default=dict
  resistance_count      JSONField, default=dict
  pressure_level        JSONField, default=dict
  brand_book            JSONField, null=True, blank=True
  created_at            DateTimeField, auto_now_add=True
  updated_at            DateTimeField, auto_now=True

─────────────────────────────────────────────
MODEL 2: ContextData
─────────────────────────────────────────────
One-to-one with CoachingSession.
Stores the pre-Q1 "Safe Zone" form data (collected before DISCOVERY state).

Fields:
  session               OneToOneField to CoachingSession
  business_name         CharField, max_length=200
  website               URLField, blank=True
  location              CharField, max_length=200, blank=True
  acquisition_method    TextField  (how they get customers now)
  business_type         CharField, max_length=200
  market                CharField, max_length=200

─────────────────────────────────────────────
MODEL 3: QuestionAnswer
─────────────────────────────────────────────
Fields:
  session               ForeignKey to CoachingSession, related_name='answers'
  question_id           IntegerField  (1–30)
  question_phase        CharField, max_length=50
  raw_answer            TextField
  prosody_flags         JSONField, default=dict
  emotional_weight      FloatField, null=True
  resistance_level      CharField, choices: low / medium / high
  gate_status           CharField, choices: PASS / REJECT / PENDING
  rejection_count       IntegerField, default=0
  extracted_phrases     JSONField, default=dict
  embedding_id          CharField, max_length=200, blank=True
                        (stores the ES document ID in brandgodfather_sessions)
  ai_reply              TextField, blank=True
  created_at            DateTimeField, auto_now_add=True

  Meta: ordering = ['question_id', 'created_at']

─────────────────────────────────────────────
MODEL 4: ShadowProfile
─────────────────────────────────────────────
One-to-one with CoachingSession. Updated after every question by RAGv2.
Never exposed directly to the user via API.

Fields:
  session               OneToOneField to CoachingSession
  self_image            TextField, blank=True
  actual_signal         TextField, blank=True
  gap_score             FloatField, default=0.0   (0.0–1.0)
  fear_pattern          TextField, blank=True
  avoidance_topic       TextField, blank=True
  readiness_estimate    FloatField, default=5.0   (1.0–10.0)
  contradiction_log     JSONField, default=list
  last_updated          DateTimeField, auto_now=True
```

---

---

# STEP 2 — Elasticsearch Node 2 Index Setup (RAGv2)

> **Agent Prompt 2 — run after Step 1**
> This creates the three RAGv2 indices on ES Node 2. Node 1 is untouched.

```
Create Elasticsearch index setup for BrandGodfather RAGv2 (Node 2).

Package: elasticsearch-py
Read all Node 2 credentials exclusively from .env — never hardcode.

Required .env keys for Node 2:
  ES_NODE2_HOST=
  ES_NODE2_PORT=
  ES_NODE2_API_KEY=

Create Django management command:
  python manage.py setup_es_node2

File: apps/coaching/management/commands/setup_es_node2.py

The command must create exactly these three indices with the mappings below.
If an index already exists, skip it and log a message. Do not overwrite.

─────────────────────────────────────────────
INDEX 1: brandgodfather_sessions
─────────────────────────────────────────────
Purpose: Stores one document per question answer per session.
Used by: contradiction check, memory writer, BrandBook generator.

{
  "mappings": {
    "properties": {
      "session_id":        { "type": "keyword" },
      "user_id":           { "type": "keyword" },
      "question_id":       { "type": "integer" },
      "raw_answer":        { "type": "text" },
      "answer_embedding":  {
        "type": "dense_vector",
        "dims": 768,
        "index": true,
        "similarity": "cosine"
      },
      "prosody_flags":     { "type": "object" },
      "emotional_weight":  { "type": "float" },
      "resistance_level":  { "type": "keyword" },
      "brand_seed":        { "type": "keyword" },
      "phase":             { "type": "keyword" },
      "gate_status":       { "type": "keyword" },
      "document_type":     { "type": "keyword" },
      "timestamp":         { "type": "date" }
    }
  }
}

─────────────────────────────────────────────
INDEX 2: brandgodfather_episodic
─────────────────────────────────────────────
Purpose: Stores the evolving session state — shadow profile, thread index,
         pressure state. One document per session, updated after each question.
Used by: memory reader, memory writer in the pipeline.

{
  "mappings": {
    "properties": {
      "session_id":            { "type": "keyword" },
      "memory_type":           { "type": "keyword" },
      "brand_seed":            { "type": "keyword" },
      "thread_index":          { "type": "object" },
      "shadow_profile":        { "type": "object" },
      "pressure_state":        { "type": "object" },
      "resistance_count":      { "type": "object" },
      "three_word_foundation": { "type": "object" },
      "emotional_register":    { "type": "keyword" },
      "question_reference":    { "type": "integer" },
      "timestamp":             { "type": "date" }
    }
  }
}

─────────────────────────────────────────────
INDEX 3: brandgodfather_chunks_v2
─────────────────────────────────────────────
Purpose: Stores chunked + classified PDF content for RAGv2 retrieval.
Used by: retrieve_rag_chunks() in the pipeline.
Populated by: the PDF ingestion pipeline (Step 3).

# ─────────────────────────────────────────────────────────────────
# INSERT YOUR RAGv2 PDF/DOC FILES HERE
# Place all BrandGodfather source documents (PDFs, DOCs) that should
# be chunked and embedded into RAGv2 in a local directory, e.g.:
#   /path/to/your/ragv2_documents/
# Pass that path to the ingest command in Step 3.
# These chunks will be stored in brandgodfather_chunks_v2 with
# metadata (chunk_type, phase, question_id, emotional_register).
# ─────────────────────────────────────────────────────────────────

{
  "mappings": {
    "properties": {
      "chunk_id":            { "type": "keyword" },
      "source_file":         { "type": "keyword" },
      "content":             { "type": "text" },
      "chunk_type":          { "type": "keyword" },
      "phase":               { "type": "keyword" },
      "question_id":         { "type": "integer" },
      "brand_type":          { "type": "keyword" },
      "emotional_register":  { "type": "keyword" },
      "pressure_level":      { "type": "integer" },
      "chunk_embedding": {
        "type": "dense_vector",
        "dims": 768,
        "index": true,
        "similarity": "cosine"
      }
    }
  }
}

chunk_type must be exactly one of:
  archetype_definition    (what a Brand Type IS)
  rejection_example       (what a BAD answer looks like + why)
  gold_standard_example   (what a GREAT answer looks like)
  challenge_language      (exact phrases BrandGodfather uses)
  brandbook_fragment      (completed BrandBook section examples)
```

---

---

# STEP 3 — PDF Chunking & RAGv2 Ingestion Pipeline

> **Agent Prompt 3 — run after Step 2**
> Reads source documents, chunks them, classifies them, embeds them,
> and stores them in brandgodfather_chunks_v2 on ES Node 2.

```
Build the PDF chunking and embedding pipeline for BrandGodfather RAGv2.

Files to create:
  apps/coaching/tasks/ingestion.py
  apps/coaching/management/commands/ingest_brandgodfather_pdfs.py

─────────────────────────────────────────────
DOCUMENT INPUT — INSERT FILE PATHS HERE
─────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────
# RAGv2 SOURCE DOCUMENTS
# Replace the placeholder paths below with your actual PDF/DOC paths.
# These are the BrandGodfather IP documents to be chunked for RAGv2.
# Add as many files as needed.
#
# Example:
#   RAGv2_SOURCE_FILES = [
#       "/path/to/BrandGodfather_Methodology.pdf",
#       "/path/to/BrandArchetypes_Reference.pdf",
#       "/path/to/BrandBookExamples_Library.pdf",
#       "/path/to/ChallengeLanguage_Guide.pdf",
#   ]
#
# Or pass a directory to the management command:
#   python manage.py ingest_brandgodfather_pdfs --dir /path/to/ragv2_docs/
# ─────────────────────────────────────────────────────────────────

─────────────────────────────────────────────
EMBEDDING MODEL
─────────────────────────────────────────────
Check .env at runtime to decide which embedding model to use:
  - If LLM_EMBEDDING_ENDPOINT is set: use the API embedding endpoint
    from .env (same provider as the main LLM).
  - Fallback: sentence-transformers model all-mpnet-base-v2 (768 dims).

Required .env keys (embedding):
  LLM_EMBEDDING_ENDPOINT=    (optional — falls back to local if absent)
  LLM_EMBEDDING_KEY=         (optional)
  LLM_EMBEDDING_DEPLOYMENT=  (optional)

─────────────────────────────────────────────
CHUNKING RULES — SEMANTIC, NOT TOKEN-WINDOW
─────────────────────────────────────────────
1. Use pdfplumber to extract raw text per page.
2. Split by double newline (\n\n) first — paragraph-level units.
3. Merge any chunk under 80 words with the next chunk.
4. Cap chunk size at 400 words. Split larger at sentence boundaries.

─────────────────────────────────────────────
CHUNK CLASSIFICATION (keyword matching)
─────────────────────────────────────────────
Classify each chunk into chunk_type — first match wins:

  rejection_example:      contains any of:
                          ["reject", "block", "fail", "invalid",
                           "not acceptable", "must not", "does not pass"]

  gold_standard_example:  contains any of:
                          ["example", "such as", "e.g.", "approved",
                           "this passes", "good answer", "ideal response"]

  challenge_language:     contains any of:
                          ["must", "require", "enforce", "push", "challenge",
                           "force the user", "do not accept", "redirect"]

  archetype_definition:   contains any of:
                          ["brand type", "archetype", "is defined as",
                           "brand category", "brand identity"]

  brandbook_fragment:     contains any of:
                          ["brand book", "brandbook", "final output",
                           "brand promise", "origin spark", "line in the sand"]

  Default if no match:    challenge_language

─────────────────────────────────────────────
METADATA EXTRACTION PER CHUNK
─────────────────────────────────────────────
  phase:              detect from nearest section header above chunk.
                      Map "Phase I" → "I", "Phase II" → "II" etc.
                      If no header found: leave blank.

  question_id:        detect Q1–Q30 reference in or near chunk.
                      Store as integer. First found wins.
                      If none: store 0.

  emotional_register: "confrontational" if chunk contains challenge/
                        push/confront/force language.
                      "supportive" if positive/affirming language.
                      "neutral" otherwise.

  brand_type:         if chunk references a named brand archetype
                      (Challenger, Sage, Rebel, Guide etc.): store name.
                      Otherwise: "general".

─────────────────────────────────────────────
CELERY TASK
─────────────────────────────────────────────
@shared_task
def ingest_pdf_to_ragv2(file_path: str, brand_type: str = "general"):
    """
    Celery task for single PDF ingestion into RAGv2.
    Target index: brandgodfather_chunks_v2 on ES Node 2.
    Steps: extract → chunk → classify → embed → store.
    Does NOT modify ES Node 1 or any existing RAGv1 indices.
    """

─────────────────────────────────────────────
MANAGEMENT COMMAND
─────────────────────────────────────────────
python manage.py ingest_brandgodfather_pdfs --dir /path/to/ragv2_docs/

Options:
  --dir         Directory of PDF files to ingest
  --file        Single file path
  --brand_type  Optional brand type tag (default: "general")
  --dry_run     Classify and print chunk summary — do not write to ES

Dispatches one ingest_pdf_to_ragv2 Celery task per file.
Print summary: files found, chunks expected, tasks queued.
```

---

---

# STEP 4 — Prosody Classifier & Vendor Language Filter

> **Agent Prompt 4 — run after Step 1. Independent of Steps 2 and 3.**
> Pure rule-based + ML. No LLM, no ES calls.
> These are Gate 1 and Gate 2 of the three-gate enforcement system.

```
Build ProsodyClassifier and VendorLanguageFilter for BrandGodfather RAGv2.

File: apps/coaching/classifiers.py

─────────────────────────────────────────────────────────────────
INSTALL REQUIREMENTS (add to requirements.txt):
─────────────────────────────────────────────────────────────────
spacy>=3.7.0
sentence-transformers>=2.7.0
transformers>=4.40.0
torch>=2.0.0

After install run:
  python -m spacy download en_core_web_sm

─────────────────────────────────────────────────────────────────
CLASS 1: ProsodyClassifier
─────────────────────────────────────────────────────────────────
Load all models once at __init__ — not per call:
  - spacy: en_core_web_sm
  - sentence-transformers: all-MiniLM-L6-v2
  - transformers pipeline: j-hartmann/emotion-english-distilroberta-base

Method: analyze(answer: str, question_id: int) -> dict

Detect and return all flags:

1. HEDGING
   Phrases: ["kind of", "maybe", "I guess", "sort of", "basically",
              "I think", "perhaps", "might be", "could be", "somewhat",
              "in a way", "more or less", "you could say"]
   Return: {"hedging": bool, "hedge_words_found": list}

2. DEFLECTION
   Phrases: ["we offer", "our service", "I provide", "what we do is",
              "we specialize", "our team", "competitive", "quality service",
              "best in class", "one stop shop", "full service",
              "industry leading", "passionate about", "results-driven"]
   Return: {"deflection": bool, "deflection_phrases": list}

3. AVOIDANCE LENGTH
   For Q4–Q30 only: flag if word count < 15.
   Return: {"avoidance_length": bool, "word_count": int}

4. PASSIVE VOICE
   Use spacy. Detect tokens with dep_ == "nsubjpass".
   Return: {"passive_voice": bool, "passive_count": int}

5. QUESTION ECHO
   Cosine similarity (sentence-transformers) between answer and
   question prompt text. If similarity > 0.65: flag as echo.
   Use QUESTION_PROMPTS dict from apps/coaching/pipeline/prompts.py
   Return: {"question_echo": bool, "similarity_score": float}

6. MONEY MOTIVATION (Q1 ONLY)
   Phrases: ["profit", "income", "making a living", "revenue", "money",
              "financial", "earn", "salary", "cash flow", "pay the bills"]
   Return: {"money_motivation": bool}

7. EMOTIONAL WEIGHT
   Use j-hartmann/emotion-english-distilroberta-base pipeline.
   Return: {"dominant_emotion": str, "emotional_weight": float}

RESISTANCE LEVEL LOGIC:
  high:   3+ flags triggered
          OR money_motivation True (Q1)
          OR deflection True
  medium: 1–2 flags triggered
  low:    0 flags triggered

FINAL RETURN SCHEMA:
{
  "flags": { ...all above... },
  "resistance_level": "low" | "medium" | "high",
  "should_challenge": bool,
  "challenge_reason": "human-readable string"
}

should_challenge = True if resistance_level is medium or high.

─────────────────────────────────────────────────────────────────
CLASS 2: VendorLanguageFilter
─────────────────────────────────────────────────────────────────
Gate 1 — hard deterministic block. Runs before any ML or LLM.
If this fires: answer is rejected immediately, pipeline stops here.

Method: check(text: str) -> dict

HARD_FAIL_PATTERNS = [
  "we offer", "quality service", "competitive pricing",
  "best in class", "one stop shop", "full service",
  "industry leading", "passionate about", "results-driven",
  "innovative solutions", "seamless experience", "synergy",
  "leverage", "holistic approach", "customer-centric"
]

Case-insensitive. Return:
{
  "fail": bool,
  "matched_patterns": list
}
```

---

---

# STEP 5 — Pure Python Orchestration Pipeline (RAGv2)

> **Agent Prompt 5 — run after Steps 1–4 are complete**
> This is the full pipeline. No LangGraph. No LangChain.
> Five files under apps/coaching/pipeline/.

---

## STEP 5A — LLM Client

```
Build the LLM API client for BrandGodfather RAGv2.

File: apps/coaching/pipeline/llm_client.py

Read ALL credentials from Django settings, which reads from .env.
Never hardcode endpoints or keys.

Required .env keys:
  LLM_API_ENDPOINT=       (the full chat completions endpoint URL)
  LLM_API_KEY=            (API key for the LLM provider)
  LLM_MODEL_NAME=         (model identifier string)
  LLM_MAX_TOKENS=1000     (optional, default 1000)

─────────────────────────────────────────────
FUNCTION: call_llm(system_prompt: str, user_prompt: str) -> dict
─────────────────────────────────────────────
1. Read endpoint, key, model from Django settings.
2. POST to LLM_API_ENDPOINT with:
   {
     "model": LLM_MODEL_NAME,
     "messages": [
       {"role": "system", "content": system_prompt},
       {"role": "user",   "content": user_prompt}
     ],
     "max_tokens": LLM_MAX_TOKENS,
     "temperature": 0.4
   }
   Headers: {"Authorization": "Bearer {LLM_API_KEY}",
             "Content-Type": "application/json"}
3. Extract content string from response.
   Handle both OpenAI-style (choices[0].message.content)
   and raw content array formats.
4. Strip any markdown fences (```json ... ```) from the response string.
5. Parse as JSON. Required schema:
   {
     "gate_status":    "PASS" or "REJECT",
     "ai_reply":       "string shown to user",
     "extracted_data": {
       "brand_seed":      "string or null",
       "tension":         "string or null",
       "key_phrase":      "string",
       "thread_addition": "string or null"
     },
     "pressure_used":  int,
     "challenge_type": "string"
   }
6. If JSON parse fails: return safe default:
   {
     "gate_status": "REJECT",
     "ai_reply": "Let us go deeper on that. Can you tell me more
                  about what that means to you?",
     "extracted_data": {"brand_seed": null, "tension": null,
                        "key_phrase": "", "thread_addition": null},
     "pressure_used": 1,
     "challenge_type": "parse_fallback"
   }
   Log the raw response and parse error.

─────────────────────────────────────────────
FUNCTION: call_llm_for_brandbook(system_prompt: str,
                                  user_prompt: str) -> dict
─────────────────────────────────────────────
Same as call_llm but:
  - temperature: 0.6  (more generative for BrandBook prose)
  - max_tokens: 3000
  - Returns raw parsed JSON dict (nine BrandBook sections)
  - On parse failure: return {"error": True, "raw": raw_string}

─────────────────────────────────────────────
Add to Django settings.py:
─────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────
# BrandGodfather RAGv2 — LLM API Settings
# All values read from .env — never hardcode
# ─────────────────────────────────────────────────────────────
LLM_API_ENDPOINT         = os.environ.get("LLM_API_ENDPOINT", "")
LLM_API_KEY              = os.environ.get("LLM_API_KEY", "")
LLM_MODEL_NAME           = os.environ.get("LLM_MODEL_NAME", "")
LLM_MAX_TOKENS           = int(os.environ.get("LLM_MAX_TOKENS", 1000))

LLM_EMBEDDING_ENDPOINT   = os.environ.get("LLM_EMBEDDING_ENDPOINT", "")
LLM_EMBEDDING_KEY        = os.environ.get("LLM_EMBEDDING_KEY", "")
LLM_EMBEDDING_DEPLOYMENT = os.environ.get("LLM_EMBEDDING_DEPLOYMENT", "")

ES_NODE2_HOST            = os.environ.get("ES_NODE2_HOST", "")
ES_NODE2_PORT            = os.environ.get("ES_NODE2_PORT", "9200")
ES_NODE2_API_KEY         = os.environ.get("ES_NODE2_API_KEY", "")
```

---

## STEP 5B — Memory Module

```
Build the memory read/write module for BrandGodfather RAGv2.

File: apps/coaching/pipeline/memory.py

Uses: brandgodfather_episodic + brandgodfather_sessions on ES Node 2.
ES client reads credentials from Django settings (ES_NODE2_* keys).

─────────────────────────────────────────────
FUNCTION: load_episodic_memory(session_id: str) -> dict
─────────────────────────────────────────────
1. Query brandgodfather_episodic on ES Node 2:
   filter: session_id == session_id
   sort: timestamp desc
   size: 1
2. If found: return the document as dict.
3. If not found (first question ever): return defaults:
   {
     "brand_seed":           "",
     "thread_index":         {},
     "shadow_profile": {
       "self_image":         "",
       "actual_signal":      "",
       "gap_score":          0.0,
       "fear_pattern":       "",
       "avoidance_topic":    "",
       "readiness_estimate": 5.0,
       "contradictions":     []
     },
     "pressure_level":       1,
     "resistance_count":     {},
     "three_word_foundation": {}
   }

─────────────────────────────────────────────
FUNCTION: write_memory(session_state: dict, memory: dict,
                        llm_result: dict, prosody_result: dict) -> str
─────────────────────────────────────────────
Write 1: brandgodfather_sessions (ES Node 2) — one doc per answer:
  {
    "session_id":       session_state["session_id"],
    "user_id":          session_state["user_id"],
    "question_id":      session_state["current_question"],
    "raw_answer":       session_state["raw_answer"],
    "answer_embedding": embed_text(session_state["raw_answer"]),
    "prosody_flags":    prosody_result["flags"],
    "emotional_weight": prosody_result["flags"]["emotional_weight"]
                            ["emotional_weight"],
    "resistance_level": prosody_result["resistance_level"],
    "brand_seed":       memory["brand_seed"],
    "phase":            session_state["current_phase"],
    "gate_status":      llm_result["gate_status"],
    "document_type":    "answer",
    "timestamp":        datetime.utcnow().isoformat()
  }
  Store returned ES doc ID as es_doc_id.

Write 2: brandgodfather_episodic (ES Node 2) — upsert by session_id:
  {
    "session_id":           session_state["session_id"],
    "memory_type":          "session_state",
    "brand_seed":           memory["brand_seed"],
    "thread_index":         memory["thread_index"],
    "shadow_profile":       memory["shadow_profile"],
    "pressure_state":       {"current": memory["pressure_level"],
                             "by_question": memory["resistance_count"]},
    "resistance_count":     memory["resistance_count"],
    "question_reference":   session_state["current_question"],
    "timestamp":            datetime.utcnow().isoformat()
  }
  Use update_by_query with upsert=True on session_id.

Write 3: Django DB — create/update QuestionAnswer record:
  session_id, question_id, raw_answer, prosody_flags,
  emotional_weight, resistance_level, gate_status,
  rejection_count, extracted_phrases (from llm_result["extracted_data"]),
  ai_reply, embedding_id (es_doc_id from Write 1)

Write 4: Django DB — update CoachingSession:
  brand_seed, thread_index, shadow_profile,
  resistance_count, pressure_level

Return: es_doc_id string

─────────────────────────────────────────────
FUNCTION: embed_text(text: str) -> list[float]
─────────────────────────────────────────────
If LLM_EMBEDDING_ENDPOINT is set in settings: call the embedding API.
Else: use sentence-transformers all-mpnet-base-v2 locally.
Return list of 768 floats.
Cache the local model at module level — load once, reuse.
```

---

## STEP 5C — RAGv2 Retriever

```
Build the RAGv2 retrieval module for BrandGodfather.

File: apps/coaching/pipeline/retriever.py

─────────────────────────────────────────────
FUNCTION: retrieve_rag_chunks(question_id: int, pressure_level: int,
                               query: str, brand_seed: str) -> dict
─────────────────────────────────────────────
1. Build ES filter:
   {"question_id": question_id,
    "pressure_level": {"lte": pressure_level + 1}}
   (allow chunks one pressure level above current — for forward priming)

2. DENSE SEARCH on brandgodfather_chunks_v2 (ES Node 2):
   Embed: query + " " + brand_seed using embed_text()
   knn search with filter above.
   Retrieve top 6 chunks.

3. SPARSE SEARCH on brandgodfather_chunks_v2 (ES Node 2):
   BM25 text match on query + " " + brand_seed with same filter.
   Retrieve top 4 chunks.

4. Merge and deduplicate by chunk_id. Keep top 5 by combined score.

5. ARCHETYPE CONTEXT from ES Node 1 (existing RAGv1 index):
   Simple text match on brand_seed.
   Retrieve 1 chunk for archetype flavour.
   Mark this chunk as source="ragv1" — used for context only,
   never as a direct rejection or gold example.

6. From merged results extract:
   gold_standard_example:  first chunk where chunk_type == "gold_standard_example"
   rejection_example:      first chunk where chunk_type == "rejection_example"
   challenge_language:     first chunk where chunk_type == "challenge_language"
                           AND pressure_level <= current pressure_level

7. Return:
   {
     "all_chunks":            list of top 5 dicts,
     "gold_standard_example": str (content) or "",
     "rejection_example":     str (content) or "",
     "challenge_language":    str (content) or "",
     "archetype_context":     str (content from Node 1) or ""
   }
```

---

## STEP 5D — Shadow Profile Updater

```
Build the shadow profile update logic for BrandGodfather RAGv2.

File: apps/coaching/pipeline/shadow.py

─────────────────────────────────────────────
FUNCTION: update_shadow_profile(shadow: dict,
                                 prosody_result: dict,
                                 raw_answer: str,
                                 question_id: int) -> dict
─────────────────────────────────────────────
All rule-based. No LLM call.

1. self_image:
   If raw_answer contains first-person strong claims
   ("I am", "I have", "I always", "my brand is"):
   extract the clause. Update shadow["self_image"].

2. actual_signal:
   If resistance_level == "high" or deflection flag True:
     shadow["actual_signal"] = "vendor-level thinking detected"
   If resistance_level == "low":
     shadow["actual_signal"] = "brand-level clarity emerging"

3. gap_score (rolling average):
   gap_raw = 1.0 if "vendor" in shadow["actual_signal"] else 0.0
   shadow["gap_score"] = (shadow["gap_score"] * 0.7) + (gap_raw * 0.3)
   Round to 2 decimal places.

4. fear_pattern:
   If prosody_result["flags"]["avoidance_length"]["avoidance_length"]:
     shadow["fear_pattern"] = f"avoidance of depth on Q{question_id}"

5. readiness_estimate (rolling average):
   ew = prosody_result["flags"]["emotional_weight"]["emotional_weight"]
   new_est = (shadow["readiness_estimate"] * 0.8) + (ew * 10 * 0.2)
   shadow["readiness_estimate"] = round(max(1.0, min(10.0, new_est)), 1)

6. Return updated shadow dict.

─────────────────────────────────────────────
FUNCTION: check_contradictions(session_id: str,
                                raw_answer: str,
                                current_question: int) -> dict
─────────────────────────────────────────────
1. Embed raw_answer using embed_text().
2. Query brandgodfather_sessions (ES Node 2) for session_id,
   all documents where document_type="answer".
3. For each previous answer:
   Compute cosine similarity with current embedding.
   If similarity > 0.85:
     Call call_llm() with a short focused prompt:
       "Do these two statements contradict each other?
        Statement A (Q{prev_q}): {prev_answer}
        Statement B (Q{current_question}): {raw_answer}
        Reply with JSON only: {"contradicts": true/false, "reason": "..."}"
     If contradicts == true:
       Append to contradictions list:
       {"q_current": current_question,
        "q_previous": prev_q,
        "reason": reason_string}
4. Return:
   {
     "found": bool,
     "contradictions": list,
     "challenge_addition": "Contradicts Q{n} — {reason}" or ""
   }
```

---

## STEP 5E — Main Orchestrator

```
Build the main pure Python pipeline orchestrator for BrandGodfather RAGv2.

File: apps/coaching/pipeline/orchestrator.py

This is the single entry point called by the Celery task.
It replaces LangGraph entirely. No external orchestration framework used.

─────────────────────────────────────────────
IMPORTS
─────────────────────────────────────────────
from ..classifiers import VendorLanguageFilter, ProsodyClassifier
from .memory import load_episodic_memory, write_memory
from .retriever import retrieve_rag_chunks
from .shadow import update_shadow_profile, check_contradictions
from .llm_client import call_llm
from .prompts import assemble_prompt, get_phase_for_question, \
                     get_question_prompt, get_enforcement_rule

# Instantiate classifiers once at module level — reused across requests
_vendor_filter  = VendorLanguageFilter()
_prosody_clf    = ProsodyClassifier()

─────────────────────────────────────────────
FUNCTION: run_coaching_pipeline(session_id: str,
                                 user_id: str,
                                 current_question: int,
                                 raw_answer: str) -> dict
─────────────────────────────────────────────

session_state = {
    "session_id":      session_id,
    "user_id":         user_id,
    "current_question": current_question,
    "current_phase":   get_phase_for_question(current_question),
    "raw_answer":      raw_answer,
    "question_prompt": get_question_prompt(current_question),
    "enforcement_rule": get_enforcement_rule(current_question)
}

# ── GATE 1: Vendor Language Filter (deterministic) ───────────────
vendor_result = _vendor_filter.check(raw_answer)
if vendor_result["fail"]:
    return {
        "gate_status":  "REJECT",
        "ai_reply":     _build_vendor_challenge(vendor_result),
        "extracted_data": {"brand_seed": None, "tension": None,
                           "key_phrase": "", "thread_addition": None},
        "pressure_used": 1,
        "challenge_type": "vendor_language_hard_block",
        "advance_question": False
    }

# ── GATE 2: Prosody Classifier (ML) ─────────────────────────────
prosody_result = _prosody_clf.analyze(raw_answer, current_question)

# ── Load session memory from ES Node 2 ──────────────────────────
memory = load_episodic_memory(session_id)

# ── Update shadow profile (rule-based, no LLM) ──────────────────
memory["shadow_profile"] = update_shadow_profile(
    memory["shadow_profile"], prosody_result, raw_answer, current_question
)

# ── Contradiction check against past answers ────────────────────
contradiction = check_contradictions(session_id, raw_answer, current_question)
if contradiction["found"]:
    prosody_result["should_challenge"] = True
    prosody_result["challenge_reason"] += " | " + contradiction["challenge_addition"]
    memory["shadow_profile"]["contradictions"].extend(
        contradiction["contradictions"]
    )

# ── RAGv2 retrieval from ES Node 2 ───────────────────────────────
chunks = retrieve_rag_chunks(
    question_id=current_question,
    pressure_level=memory["pressure_level"],
    query=raw_answer,
    brand_seed=memory["brand_seed"]
)

# ── ENFORCEMENT LOOP (Gate 3 — LLM) ─────────────────────────────
# Pure Python while loop replaces LangGraph conditional edges.
# Max 5 rejections per question — hard cap to prevent infinite loop.
# On each rejection: pressure escalates, prompt reassembled.
# RAG chunks are NOT re-fetched inside the loop (already loaded).

MAX_REJECTIONS = 5
rejection_count = 0
gate_status = "REJECT"
llm_result = {}

while gate_status == "REJECT" and rejection_count < MAX_REJECTIONS:

    system_prompt, user_prompt = assemble_prompt(
        session_state=session_state,
        memory=memory,
        prosody_result=prosody_result,
        chunks=chunks,
        rejection_count=rejection_count
    )

    llm_result = call_llm(system_prompt, user_prompt)
    gate_status = llm_result["gate_status"]

    if gate_status == "REJECT":
        rejection_count += 1
        memory["pressure_level"] = min(memory["pressure_level"] + 1, 5)
        # Update resistance count for this question
        q_key = str(current_question)
        memory["resistance_count"][q_key] = \
            memory["resistance_count"].get(q_key, 0) + 1

# ── Post-loop: forced pass after hitting cap ─────────────────────
# Log forced passes for quality review — do not surface to user.
if gate_status == "REJECT" and rejection_count >= MAX_REJECTIONS:
    gate_status = "PASS"
    llm_result["gate_status"] = "PASS"
    llm_result["challenge_type"] = "forced_pass_cap_reached"

# ── Update memory state on PASS ──────────────────────────────────
if gate_status == "PASS":
    extracted = llm_result.get("extracted_data", {})
    if extracted.get("brand_seed"):
        memory["brand_seed"] = extracted["brand_seed"]
    if extracted.get("thread_addition"):
        memory["thread_index"][str(current_question)] = \
            extracted["thread_addition"]

# ── Write to ES Node 2 + Django DB ───────────────────────────────
write_memory(session_state, memory, llm_result, prosody_result)

# ── Return final result to Celery task ───────────────────────────
return {
    "gate_status":       gate_status,
    "ai_reply":          llm_result["ai_reply"],
    "extracted_data":    llm_result.get("extracted_data", {}),
    "pressure_used":     llm_result.get("pressure_used", 1),
    "challenge_type":    llm_result.get("challenge_type", ""),
    "rejection_count":   rejection_count,
    "advance_question":  gate_status == "PASS",
    "brand_seed":        memory["brand_seed"]
}

─────────────────────────────────────────────
HELPER: _build_vendor_challenge(vendor_result: dict) -> str
─────────────────────────────────────────────
Returns a BrandGodfather-voice rejection message for vendor language.
Do not reveal the matched patterns to the user.
Example: "That language belongs to a brochure, not a brand.
          Strip away what you offer and tell me what you believe."
Vary the message — do not use the same string every time.
Define 5 variants and rotate by hash of vendor_result["matched_patterns"].
```

---

---

# STEP 6 — Prompt Assembly & Question Map

> **Agent Prompt 6 — run after Step 5**

```
Build the prompt assembly system for BrandGodfather RAGv2.

File: apps/coaching/pipeline/prompts.py

─────────────────────────────────────────────
SECTION A: QUESTION PROMPTS MAP (Q1–Q30)
─────────────────────────────────────────────
QUESTION_PROMPTS = {
    1:  "What motivated you to start this business journey in the "
        "first place? If you had to name the spirit behind it in "
        "one word or short phrase, what is it?",
    2:  "What do you believe your business truly does — not the "
        "service, but the idea behind it?",
    3:  "Right now, do you see yourself as a Vendor, a Specialist, "
        "or a Brand — and what language do your customers use about you?",
    4:  "What frustrates you most about the market you operate in?",
    5:  "Where do you feel most misunderstood by the people you "
        "most want to serve?",
    6:  "What felt broken or wrong in your industry before you entered it?",
    7:  "What do you believe that most of your competitors would "
        "actively disagree with?",
    8:  "If your products and services disappeared tomorrow, "
        "what IDEA would remain?",
    9:  "Complete this: 'The world would be better if...'",
    10: "What is the real transformation you create — not the "
        "deliverable, but the change in the person?",
    11: "What is your line in the sand — what will your brand "
        "never do, stand for, or be associated with?",
    12: "Name three non-negotiable values that govern every "
        "decision your brand makes.",
    13: "When your brand enters a room, what happens to the energy?",
    14: "Describe your brand's personality in three words — "
        "and none of them can be 'friendly' or 'professional'.",
    15: "Who do you most want to serve — and who are you "
        "willing to exclude to serve them better?",
    16: "What is the unspoken fear your ideal client carries "
        "but is afraid to say out loud?",
    17: "How should your ideal client feel after working with you?",
    18: "What is your meaningful difference — and why specifically "
        "cannot a competitor replicate it?",
    19: "What competitive axis do you refuse to compete on — "
        "price, speed, volume, or something else?",
    20: "Who is your brand NOT for — and how is that exclusion "
        "actually a relief to them?",
    21: "What can someone always expect from you, "
        "every single time, without exception?",
    22: "What is the one thing someone would say about your brand "
        "when recommending you without hesitation?",
    23: "Five years from now, what do you want people to say "
        "about what your brand stood for?",
    24: "What work do you want more of — and what work "
        "will you no longer accept?",
    25: "What have you been avoiding that is holding your brand back?",
    26: "Where are you playing small — and what risk or "
        "judgment are you afraid of?",
    27: "Are you willing to polarize the market to become "
        "the Go-To Brand for the right people?",
    28: "What is the one thing you will STOP doing "
        "immediately to honour this brand?",
    29: "On a scale of 1–10, how ready are you to lead "
        "with this brand — and what would move it one point higher?",
    30: "Do you grant BrandGodfather the authority to challenge "
        "you from this point forward without apology?"
}

─────────────────────────────────────────────
SECTION B: ENFORCEMENT RULES MAP (Q1–Q30)
─────────────────────────────────────────────
ENFORCEMENT_RULES = {
    1:  "Reject money as the final motivation. Translate to underlying emotion. "
        "Extract and store the Brand Seed: one emotionally strong word or phrase.",
    2:  "Block all service lists. Require language about belief, "
        "meaning, or change — not what they do.",
    3:  "Require evidence of current perceived position. "
        "If unsupported, reframe as aspiration not fact.",
    4:  "Convert complaints into strategic insights. "
        "Store the core tension for the BrandBook.",
    5:  "Force specific articulation of how they are misinterpreted. "
        "Reject vague 'they don't see value' answers.",
    6:  "Require a specific practice or norm they are rejecting. "
        "Block generic 'the industry is bad' answers.",
    7:  "The belief must be disagreeable to a competitor. "
        "If universally agreeable, challenge and deepen it.",
    8:  "Zero-Product Test: remove all operational language. "
        "Validate the idea survives if all products are deleted.",
    9:  "Personal Grounding: response must be tied to a personal "
        "belief or lived experience. Block abstract moral statements.",
    10: "Identity Shift: must describe a change in confidence, clarity, "
        "or behaviour. Reject deliverables as final answers.",
    11: "Mandatory Opposition: require a specific refusal. "
        "If user says nothing, explain that neutrality prevents leadership.",
    12: "Behavioural Test: values must be observable. "
        "Ask how each value specifically shows up in their actions.",
    13: "Energy Impact: must describe the emotional shift when the "
        "brand enters. Reject adjectives that don't imply energy change.",
    14: "Sharpness Filter: require distinctiveness. "
        "Block bland descriptors like friendly or professional.",
    15: "Exclusion Test: reject 'everyone.' Force a specific trade-off.",
    16: "Psychological Depth: must be a fear the client is afraid "
        "to admit out loud. Reject surface-level fears.",
    17: "Felt State: must describe a specific felt state. "
        "Store as Brand Promise input.",
    18: "Competitor Gap: require explanation of why competitors "
        "cannot replicate this. Block unsupported claims.",
    19: "Axis of Rejection: must identify a specific competitive "
        "axis being rejected (price, speed, scale).",
    20: "Relief over Rejection: frame exclusion as a relief "
        "to the excluded client, not a hostile act.",
    21: "Consistent Standard: must describe a repeatable experience. "
        "Reject hype or aspirations.",
    22: "Brag-Worthy: identify the specific thing that makes "
        "someone recommend without hesitation.",
    23: "External Narrative: must describe what others say, "
        "not internal revenue goals.",
    24: "Boundary Definition: must define specific work to accept "
        "and reject. Block 'less stress' as an answer.",
    25: "Business Context: keep grounded in brand — "
        "do not allow therapy-style exploration.",
    26: "Risk Articulation: normalise discomfort and require "
        "the user to state the risk or judgment they fear.",
    27: "Explicit Trade-off: state the cost of being a Go-To Brand. "
        "Use no softening language.",
    28: "Concrete Action: identify a specific behaviour the "
        "founder must STOP doing immediately.",
    29: "Intensity Adjustment: use the 1–10 score to adjust "
        "challenge intensity. Ask what moves it +1.",
    30: "Hard Stop: confirm explicit consent to move into "
        "challenge-led mode before proceeding."
}

─────────────────────────────────────────────
SECTION C: PRESSURE LEVEL INSTRUCTIONS
─────────────────────────────────────────────
PRESSURE_INSTRUCTIONS = {
    1: "Reflect their words back warmly. Ask what they mean by the "
       "key phrase. Be precise but not confrontational.",
    2: "Offer an alternative interpretation. Suggest their answer "
       "might be pointing to something deeper. Invite them further.",
    3: "Name the avoidance directly. Tell them what their answer "
       "reveals. Use their Brand Seed to contrast what they said.",
    4: "State plainly what this answer would mean for their brand. "
       "Connect it to being invisible or interchangeable. No softening.",
    5: "Connect this moment to the cost of staying a vendor. "
       "Ask if they are willing to keep playing small. "
       "Reference an earlier answer from the thread index."
}

─────────────────────────────────────────────
SECTION D: PHASE MAP
─────────────────────────────────────────────
PHASE_MAP = {
    **{q: "I: Origin"       for q in range(1,  6)},
    **{q: "II: Edge"        for q in range(6,  8)},
    **{q: "III: Idea"       for q in range(8, 12)},
    **{q: "IV: Foundation"  for q in range(12, 15)},
    **{q: "V: Truth"        for q in range(15, 18)},
    **{q: "VI: Difference"  for q in range(18, 21)},
    **{q: "VII: Promise"    for q in range(21, 23)},
    **{q: "VIII: Vision"    for q in range(23, 25)},
    **{q: "IX: Readiness"   for q in range(25, 31)},
}

def get_phase_for_question(q: int) -> str:
    return PHASE_MAP.get(q, "Unknown")

def get_question_prompt(q: int) -> str:
    return QUESTION_PROMPTS.get(q, "")

def get_enforcement_rule(q: int) -> str:
    return ENFORCEMENT_RULES.get(q, "")

─────────────────────────────────────────────
SECTION E: PROMPT ASSEMBLER
─────────────────────────────────────────────
def assemble_prompt(session_state: dict, memory: dict,
                    prosody_result: dict, chunks: dict,
                    rejection_count: int) -> tuple[str, str]:
    """
    Returns (system_prompt, user_prompt).
    Called by the orchestrator on every loop iteration.
    Pressure level is read from memory["pressure_level"] —
    already escalated by the loop before this is called on retry.
    """

    thread_lines = "\n".join(
        f"  Q{k}: {v}" for k, v in memory["thread_index"].items()
    ) or "  (none yet)"

    shadow = memory["shadow_profile"]
    pressure = memory["pressure_level"]

    system_prompt = f"""
You are BrandGodfather, a Benevolent Authority and brand leadership coach.
Your purpose is to extract emotional truth and block vendor thinking.

YOUR LAWS:
1. You NEVER apologize for challenging the user.
2. You NEVER accept safe, polite, or logical answers when emotional
   truth is required.
3. You ALWAYS refer back to the user's Brand Seed: "{memory['brand_seed']}"
4. You DO NOT defer your authority to the user.
5. You sound like a wise, direct mentor — never a chatbot.
6. You NEVER use these words in your reply:
   "we offer", "quality service", "competitive pricing",
   "passionate", "innovative", "seamless", "leverage", "synergy".

CURRENT SESSION CONTEXT:
  Brand Seed:      {memory['brand_seed'] or '(not yet extracted)'}
  Phase:           {session_state['current_phase']}
  Question:        Q{session_state['current_question']} of 30
  Pressure Level:  {pressure}/5
  Rejection count: {rejection_count} this question

SHADOW PROFILE (internal — NEVER reveal this to the user):
  Self-image:          {shadow.get('self_image', 'unknown')}
  Actual signal:       {shadow.get('actual_signal', 'unknown')}
  Gap score:           {shadow.get('gap_score', 0.0):.2f}
  Fear pattern:        {shadow.get('fear_pattern', 'none detected')}
  Readiness estimate:  {shadow.get('readiness_estimate', 5.0):.1f}/10

THREAD INDEX — weave these into your challenges where relevant:
{thread_lines}

PRESSURE INSTRUCTION FOR LEVEL {pressure}:
{PRESSURE_INSTRUCTIONS[min(pressure, 5)]}

RESPONSE FORMAT — return ONLY valid JSON, zero markdown, zero preamble:
{{
  "gate_status":    "PASS" or "REJECT",
  "ai_reply":       "Your response. Use their exact words. Reference Brand Seed on REJECT.",
  "extracted_data": {{
    "brand_seed":      "extracted word/phrase or null (Q1 only)",
    "tension":         "extracted tension or null (Q4 only)",
    "key_phrase":      "most emotionally loaded phrase in their answer",
    "thread_addition": "phrase to store in thread index or null"
  }},
  "pressure_used":  {pressure},
  "challenge_type": "brief description of challenge applied"
}}

PASS criteria:
  Emotional specificity, personal belief, or lived experience.
  No vendor language. No hedging on core meaning.
  Directly addresses the enforcement rule.

REJECT criteria:
  Feature-based, vague, vendor phrases, money as final motivation (Q1),
  or fewer than 2 meaningful sentences.
""".strip()

    user_prompt = f"""
Question asked: {session_state['question_prompt']}

User's answer: {session_state['raw_answer']}

Enforcement rule: {session_state['enforcement_rule']}

Prosody flags: {prosody_result.get('challenge_reason', 'none')}

From BrandGodfather knowledge base:
  Rejected answer example:   {chunks.get('rejection_example', 'none retrieved')}
  Passing answer example:    {chunks.get('gold_standard_example', 'none retrieved')}
  Challenge language to use: {chunks.get('challenge_language', 'none retrieved')}
""".strip()

    return system_prompt, user_prompt
```

---

---

# STEP 7 — Celery Task & Django API (RAGv2)

> **Agent Prompt 7 — run after Steps 1–6 are complete**

```
Build the Celery task and Django REST API views for BrandGodfather RAGv2.

─────────────────────────────────────────────────────────────────
FILE 1: apps/coaching/tasks/coaching.py
─────────────────────────────────────────────────────────────────
from celery import shared_task
from ..pipeline.orchestrator import run_coaching_pipeline
from ..pipeline.prompts import (
    get_phase_for_question,
    get_question_prompt,
    QUESTION_PROMPTS
)

@shared_task(bind=True, max_retries=3, default_retry_delay=2)
def process_answer_task(self, session_id: str, raw_answer: str):
    """
    RAGv2 main Celery task.
    Calls run_coaching_pipeline() — the pure Python orchestrator.
    Updates Django DB and ES Node 2 internally via write_memory().
    Returns AI reply and gate status to the API view.
    """
    try:
        from ..models import CoachingSession

        session = CoachingSession.objects.get(session_id=session_id)
        q = session.current_question

        result = run_coaching_pipeline(
            session_id=str(session_id),
            user_id=str(session.user_id),
            current_question=q,
            raw_answer=raw_answer
        )

        # Advance question on PASS
        if result["advance_question"]:
            session.current_question += 1
            if session.current_question > 30:
                session.status = "OUTPUT"
            session.brand_seed = result.get("brand_seed", session.brand_seed)
            session.save()

        next_q = session.current_question
        return {
            "gate_status":          result["gate_status"],
            "ai_reply":             result["ai_reply"],
            "current_question":     next_q,
            "next_question_prompt": QUESTION_PROMPTS.get(next_q),
            "brand_seed":           result.get("brand_seed", session.brand_seed),
            "session_complete":     next_q > 30
        }

    except Exception as exc:
        raise self.retry(exc=exc)

─────────────────────────────────────────────────────────────────
FILE 2: apps/coaching/views.py
─────────────────────────────────────────────────────────────────
Build these four REST endpoints using Django REST Framework.
All endpoints require authentication (IsAuthenticated).

──────────────────────────────────────
ENDPOINT 1: POST /api/coaching/session/start/
──────────────────────────────────────
Body:
{
  "business_name":       "string",
  "website":             "string (optional)",
  "location":            "string (optional)",
  "acquisition_method":  "string",
  "business_type":       "string",
  "market":              "string"
}

Logic:
  1. Create CoachingSession (status → DISCOVERY).
  2. Create ContextData record.
  3. Return:
{
  "session_id":              "uuid",
  "first_question":          1,
  "first_question_prompt":   "What motivated you...",
  "welcome_message":         "Welcome, {user.first_name}. I am here to
                              guide you from being a vendor to
                              becoming a brand.",
  "struggle_disclaimer":     "If this feels harder than expected,
                              that is a good sign.",
  "clarity_rule":            "Clarity comes after exploration,
                              not before."
}

──────────────────────────────────────
ENDPOINT 2: POST /api/coaching/session/{session_id}/answer/
──────────────────────────────────────
Body: { "answer": "string" }

Logic:
  1. Validate session exists and status == DISCOVERY.
  2. Validate answer is not empty.
  3. Call process_answer_task.delay(session_id, answer).
  4. Poll AsyncResult — max 30s timeout.
  5. Return:
{
  "ai_reply":             "string",
  "gate_status":          "PASS" or "REJECT",
  "current_question":     int,
  "next_question_prompt": "string or null",
  "depth_score":          float,
  "session_complete":     bool
}
  depth_score = emotional_weight from the latest QuestionAnswer record.

──────────────────────────────────────
ENDPOINT 3: POST /api/coaching/session/{session_id}/brandbook/
──────────────────────────────────────
Logic:
  1. Validate session.current_question > 30.
  2. Validate session.status == OUTPUT or COMPLETE.
  3. Dispatch generate_brandbook_task.delay(session_id).
  4. Return:
{
  "task_id":  "celery task id string",
  "status":   "generating"
}

──────────────────────────────────────
ENDPOINT 4: GET /api/coaching/session/{session_id}/status/
──────────────────────────────────────
Return:
{
  "session_id":        "uuid",
  "status":            "COLLECTING|DISCOVERY|OUTPUT|COMPLETE",
  "current_question":  int,
  "brand_seed":        "string",
  "depth_score":       float,
  "answers_completed": int,
  "brandbook_ready":   bool
}
```

---

---

# STEP 8 — BrandBook Generator (RAGv2)

> **Agent Prompt 8 — run last, after all prior steps**

```
Build the BrandGodfather BrandBook Generator for RAGv2.

File: apps/coaching/tasks/brandbook.py

The BrandBook is the final output of the 30-question session —
previously called "manifesto" — renamed to BrandBook throughout.

─────────────────────────────────────────────────────────────────
GENERIC FILTER — deterministic, runs before LLM
─────────────────────────────────────────────────────────────────
BRANDBOOK_BANNED_PHRASES = [
    "we offer", "quality service", "competitive pricing",
    "best in class", "passionate", "innovative", "seamless",
    "leverage", "synergy", "holistic", "results-driven",
    "customer-centric", "thought leader", "game changer",
    "disruptive", "scalable solutions", "value-added"
]

─────────────────────────────────────────────────────────────────
@shared_task
def generate_brandbook_task(session_id: str):
─────────────────────────────────────────────────────────────────

STEP 1 — Load all 30 answers from brandgodfather_sessions (ES Node 2).
  Query: session_id + document_type="answer", sort by question_id asc.
  Build dict: {question_id: raw_answer} for Q1–Q30.

STEP 2 — Load session metadata from brandgodfather_episodic (ES Node 2).
  Load: brand_seed, three_word_foundation, shadow_profile, thread_index.

STEP 3 — Load from Django DB:
  CoachingSession.brand_seed
  CoachingSession.three_word_foundation
  All QuestionAnswer records for the session.

STEP 4 — Run Generic Filter on all 30 raw answers.
  Check each answer for BRANDBOOK_BANNED_PHRASES.
  Build report: {question_id: [matched phrases]}.

STEP 5 — Build synthesis prompt and call LLM.
  Use call_llm_for_brandbook() from apps/coaching/pipeline/llm_client.py

  SYSTEM PROMPT:
  You are BrandGodfather generating the final BrandBook for a founder.
  This BrandBook must sound like it was written by a brand philosopher —
  not a marketing copywriter.
  Use the founder's exact words wherever possible.
  Never use generic marketing language.
  Every section must feel specific to THIS founder.
  If you find yourself writing any of these words, stop and rewrite:
  {BRANDBOOK_BANNED_PHRASES as comma-separated string}

  Brand Seed: {brand_seed}
  3-Word Foundation: {three_word_foundation}
  Line in the Sand (Q11): {answers[11]}
  Brand Promise (Q17): {answers[17]}
  Word-of-Mouth Trigger (Q22): {answers[22]}
  Banned phrases found in session answers: {generic_filter_report}

  USER PROMPT:
  All 30 session answers:
  {formatted as "Q1: [answer]\nQ2: [answer]\n..." etc.}

  Generate the BrandBook with EXACTLY these nine sections.
  Return as JSON only — no markdown, no preamble:
  {
    "origin_spark":          "prose — from Q1 + Q2",
    "the_edge":              "prose — from Q6 + Q7",
    "the_big_idea":          "prose — from Q8 + Q9 + Q10",
    "line_in_the_sand":      "prose — from Q11",
    "three_word_foundation": "prose — from Q12 + Q13 + Q14",
    "who_this_is_for":       "prose — from Q15 + Q16 + Q19 + Q20",
    "brand_promise":         "prose — from Q17 + Q21 + Q22",
    "the_vision":            "prose — from Q23 + Q24",
    "authority_grant":       "prose — from Q30"
  }

STEP 6 — Run VendorLanguageFilter on each BrandBook section.
  Import VendorLanguageFilter from apps/coaching/classifiers.py
  For each of the nine sections:
    If fail is True:
      Call call_llm_for_brandbook() again for that section only.
      System: "Rewrite this BrandBook section without these phrases:
               {matched_patterns}. Use the founder's own words only."
      User: "Original section: {section_text}"
      Max 3 regeneration attempts per section.

STEP 7 — Store final BrandBook.
  Save to CoachingSession.brand_book (JSONField) in Django DB.
  Save to brandgodfather_sessions (ES Node 2):
  {
    "session_id":    session_id,
    "document_type": "brandbook",
    "content":       brandbook_json_as_string,
    "brand_seed":    brand_seed,
    "gate_status":   "PASS",
    "timestamp":     utcnow().isoformat()
  }
  Update CoachingSession.status = "COMPLETE".

STEP 8 — Return result dict:
  {
    "brand_book":              {nine section dict},
    "brand_seed":              str,
    "three_word_foundation":   dict,
    "generic_filter_flags":    {question_id: [phrases]},
    "sections_regenerated":    [section names regenerated],
    "regeneration_attempts":   {section_name: int},
    "all_sections_pass":       bool
  }
```

---

---

## RAGv2 Run Order Summary

```
Step 1  →  Django models (run first — everything depends on this)
Step 2  →  ES Node 2 index setup
           run: python manage.py setup_es_node2
Step 3  →  PDF ingestion pipeline
           # INSERT YOUR RAGv2 PDF PATHS BEFORE RUNNING
           run: python manage.py ingest_brandgodfather_pdfs --dir /your/path/
Step 4  →  Classifiers (Gate 1 + Gate 2 — pure Python, no LLM)
Step 5A →  LLM client + Django settings (.env wiring)
Step 5B →  Memory module (ES Node 2 read/write)
Step 5C →  RAGv2 retriever (ES Node 2 hybrid search)
Step 5D →  Shadow profile + contradiction check
Step 5E →  Main orchestrator (pure Python while loop — no LangGraph)
Step 6  →  Prompt assembly + Q1–Q30 maps (imported by orchestrator)
Step 7  →  Celery task + Django API views
Step 8  →  BrandBook generator (run last)
```

---

## Three-Gate Enforcement Summary

```
GATE 1 — VendorLanguageFilter     (deterministic, no LLM, no ML)
  Hard keyword match. Instant REJECT. Pipeline exits immediately.
  No ES reads, no classifier calls, no LLM spend.

GATE 2 — ProsodyClassifier        (ML classifiers, no LLM)
  Detects hedging, avoidance, passive voice, echo, length, emotion.
  Sets pressure_level and challenge_reason for the LLM prompt.
  Does not block on its own — feeds Gate 3.

GATE 3 — LLM Judge (BrandGodfather via .env API credentials)
  Evaluates meaning, emotional depth, and enforcement rule compliance.
  RAGv2 gold standard + rejection examples passed in prompt context.
  Returns structured JSON: gate_status PASS or REJECT.
  On REJECT: pure Python while loop escalates pressure and retries.
  Hard cap: 5 rejections per question, then forced PASS with flag.

ALL THREE MUST RETURN PASS TO ADVANCE TO THE NEXT QUESTION.
```

---

*Document prepared for RAGv2 implementation.*
*Orchestration: pure Python — no LangGraph, no LangChain.*
*LLM: credentials read exclusively from .env at runtime.*
*Final output: BrandBook (not manifesto).*
*Coach identity: BrandGodfather — Benevolent Authority.*
