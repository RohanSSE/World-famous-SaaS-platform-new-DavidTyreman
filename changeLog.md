# changeLog

## Summary
This report documents the Train BGF admin enhancements that were implemented across frontend and backend, including:
- Train BGF route/page creation
- Restored `/admin/dev` route
- Fine-tuning UI with 4 phase sections
- BGF engine toggle (engine1 / engine2)
- Section save + section-specific train actions
- DB-backed version history
- Load Default support
- Dedicated backend module folder `AdminAITuning`
- Distinguished Swagger schema for all new Admin AI Tuning APIs

## What Was Implemented
### 1) Admin Route and Navigation
- Added Train BGF admin route: `/admin/train-bgf`
- Added navbar item `Train BGF`
- Restored route alias `/admin/dev`

### 2) Train BGF UI
On `/admin/train-bgf`, the page now includes:
- Main title: `Fine Tune the Brand Godfather AI engine`
- Engine toggle:
  - `Use BGF engine1` -> `rag_v1`
  - `Use BGF engine2` -> `rag_v2`
- 4 phase sections with fields:
  - Input Prompt
  - Goal of Prompt
  - Evaluation Criteria of Prompt
- Per section actions:
  - `Save`
  - `Train AI`
- Bottom panel:
  - Past fine-tuning versions from DB
  - Load any version into form
  - View full stored snapshot JSON
- `Load Default` button:
  - Loads default DB template into active config

### 3) Backend Architecture (Separate Folder)
A dedicated backend folder was added:
- `GodFather_backend/AdminAITuning/`

Files in this folder:
- `models.py`
  - `AITuningVersion` model for versioning and audit trail
- `service.py`
  - State retrieval
  - Save section tuning
  - Train section tuning
  - Load default template
- `views.py`
  - Admin-protected APIs for state/load/save/train
  - Swagger decorators and schemas
- `urls.py`
  - Endpoint routing

### 4) Data Model and Migration
- Added migration: `user_sessions/migrations/0023_aituningversion.py`
- New DB model:
  - `AITuningVersion`
  - Stores: action (`save/train/load_default`), section key, pipeline, full config snapshot, user, timestamp, and version number

### 5) API Integration
Mounted under existing sessions API namespace:
- Base: `/api/sessions/admin/ai-tuning/`

## Distinguished Swagger Schema
A dedicated Swagger tag was added:
- Tag: `Admin AI Tuning`

Each endpoint includes:
- `operation_id`
- Clear description
- Request body schema (where applicable)
- Response schema
- Path/query parameter schema

## Endpoint Names and Paths
### URL name: `admin-ai-tuning-state`
- Method: `GET`
- Path: `/api/sessions/admin/ai-tuning/`
- Purpose: Return current Train BGF config, parsed section data, default template info, and version history.

### URL name: `admin-ai-tuning-load-default`
- Method: `POST`
- Path: `/api/sessions/admin/ai-tuning/load-default/`
- Purpose: Load DB default tuning template into active config and record a version entry.

### URL name: `admin-ai-tuning-save-section`
- Method: `POST`
- Path: `/api/sessions/admin/ai-tuning/sections/<section_key>/save/`
- Purpose: Save a single section tuning payload and create version history.
- `section_key` allowed values:
  - `phase_1_master_prompt`
  - `phase_2_master_prompt`
  - `phase_3_master_prompt`
  - `phase_4_master_prompt`

### URL name: `admin-ai-tuning-train-section`
- Method: `POST`
- Path: `/api/sessions/admin/ai-tuning/sections/<section_key>/train/`
- Purpose: Section-specific train action (save + training trigger) and version logging.
- `section_key` allowed values:
  - `phase_1_master_prompt`
  - `phase_2_master_prompt`
  - `phase_3_master_prompt`
  - `phase_4_master_prompt`

## Frontend Files Updated
- `GodFather_frontend/src/admin/pages/train-bgf.jsx`
- `GodFather_frontend/src/admin/lib/adminApi.js`
- `GodFather_frontend/src/admin/layouts/nav-config-dashboard.jsx`
- `GodFather_frontend/src/admin/admin-routes.jsx`
- `GodFather_frontend/src/App.jsx`

## Backend Files Updated
- `GodFather_backend/AdminAITuning/__init__.py`
- `GodFather_backend/AdminAITuning/models.py`
- `GodFather_backend/AdminAITuning/service.py`
- `GodFather_backend/AdminAITuning/views.py`
- `GodFather_backend/AdminAITuning/urls.py`
- `GodFather_backend/user_sessions/urls.py`
- `GodFather_backend/user_sessions/migrations/0023_aituningversion.py`

## Operational Notes
- Run migration before using versioning APIs:
  - `python manage.py migrate`
- Swagger UI paths remain:
  - `/swagger/`
  - `/redoc/`
- All new Admin AI Tuning APIs are admin-protected.

## Validation Status
- Frontend changed files: no editor errors
- Backend changed files: no editor errors
- Endpoint docs added via `drf_yasg` decorators in `AdminAITuning/views.py`
