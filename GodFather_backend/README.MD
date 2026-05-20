# GodFather Backend

Installation and Setup Instructions

**Full documentation for developers (tech stack, architecture, API, deployment) is in the [docs/](./docs/) folder.**

"""
SETUP GUIDE:

1. Install System Dependencies (Ubuntu/Debian):
   sudo apt-get update
   sudo apt-get install -y tesseract-ocr poppler-utils

2. Install Python Dependencies:
   pip install -r requirements.txt

3. Start Elasticsearch and Redis:
   # Option A: Using Docker
   docker-compose up -d
   
   # Option B: Manual installation
   # Follow official guides for Elasticsearch and Redis

4. Run Migrations:
   python manage.py makemigrations documents
   python manage.py migrate

5. Create Media Directory:
   mkdir -p media/documents

6. Start Celery Worker:
   celery -A project worker --pool=solo --loglevel=info

7. Start Django Development Server:
   python manage.py runserver

USAGE:

1. Upload a PDF:
   POST /api/documents/
   Content-Type: multipart/form-data
   Body: {
     "file": <pdf_file>,
     "title": "My Document"
   }

2. Check document status:
   GET /api/documents/{id}/

3. Search within document:
   POST /api/documents/{id}/search/
   Body: {
     "query": "branding strategy",
     "search_type": "hybrid",
     "top_k": 5
   }

4. Get AI suggestion with document context:
   POST /api/answers/{session_id}/ai-suggestion/
   Body: {
     "question_text": "What is brand positioning?",
     "answer_text": "Brand positioning is...",
     "use_documents": true,
     "document_ids": [1, 2]  // optional
   }

5. Delete document:
   DELETE /api/documents/{id}/

TROUBLESHOOTING:

- If Tesseract fails: Check installation and PATH
- If Celery doesn't process: Ensure Redis is running
- If Elasticsearch connection fails: Check if it's running on port 9200
- Large PDFs may take time: Check Celery logs for progress





celery -A project worker -Q project.default --pool=solo -c 1 --loglevel=info

