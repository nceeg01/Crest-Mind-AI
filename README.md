# CrestMind AI

Synthetic, resume-aligned portfolio demonstration of property-document intelligence. It includes a responsive React evidence workspace and a FastAPI ingestion/retrieval service with durable SQLite persistence for local/container use.

No client documents or production metrics are included. The public browser demo uses deterministic synthetic retrieval. Llama 3.3, Vertex AI OCR, Supabase, and pgvector describe prior project context or future adapters; this MVP does not claim those providers are live.

## Run
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn api.main:app --reload
cd web && npm install && npm run dev
```

## Verify
```bash
pytest -q
cd web && npm test && npm run build
```

Tests cover cited answers, property isolation, bounded retrieval, and idempotent ingestion. Uploads are limited to 5 MB. Text PDFs use PyMuPDF; scanned PDFs invoke Tesseract OCR and fail clearly when it is unavailable. DOCX citations use paragraph locators rather than invented pages.

## Team context
CrestMind began as UNT Capstone Group 13 work for Woodcrest Capital in Spring 2026. Original repository roles: Satish Wagle (AI), Sushil Dahal (backend/database), Smarika Koirala (frontend), Saurav Pandey (OCR/ingestion), and Yubraj Chaulagain (GCP/deployment).

The public browser demo does not persist server uploads. Local/container mode persists to SQLite. Retrieval scores are term-overlap metadata, not calibrated answer probabilities.
