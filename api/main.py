from __future__ import annotations

import os
import secrets
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .documents import extract
from .models import AskRequest, AskResponse, DocumentSummary, Property, Source
from .retrieval import answer_from_sources, search
from .storage import connect, ingest_text, initialize, seed

MAX_UPLOAD_BYTES = 5 * 1024 * 1024


def authorize(x_api_key: str | None = Header(default=None)) -> None:
    expected = os.getenv("API_KEY")
    if expected and (not x_api_key or not secrets.compare_digest(expected, x_api_key)):
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize()
    seed()
    yield


app = FastAPI(title="CrestMind AI", version="2.0.0", lifespan=lifespan)
origins = [origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=False, allow_methods=["GET", "POST"], allow_headers=["Content-Type", "X-Api-Key"])


@app.get("/health")
def health():
    return {"status": "ok", "mode": "synthetic-demo"}


@app.get("/ready")
def ready():
    try:
        with connect() as db:
            db.execute("SELECT 1")
        return {"status": "ready"}
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Storage is unavailable.") from exc


@app.get("/properties", response_model=list[Property])
def properties(_: None = Depends(authorize)):
    with connect() as db:
        return [dict(row) for row in db.execute("SELECT * FROM properties ORDER BY name")]


@app.get("/documents", response_model=list[DocumentSummary])
def documents(property_id: str, _: None = Depends(authorize)):
    with connect() as db:
        rows = db.execute("SELECT id, property_id, name, kind, status FROM documents WHERE property_id = ? ORDER BY name", (property_id,)).fetchall()
    return [{**dict(row), "locator_label": "Sections"} for row in rows]


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest, _: None = Depends(authorize)):
    rows = search(request.query, request.property_id, request.top_k)
    sources = [Source(id=row["id"], document_id=row["document_id"], document_name=row["document_name"], locator=row["locator"], excerpt=row["content"], relevance=row["relevance"]) for row in rows]
    return AskResponse(answer=answer_from_sources(request.query, rows), found_in_documents=bool(rows), sources=sources)


@app.post("/documents")
async def upload(property_id: str, file: UploadFile = File(...), _: None = Depends(authorize)):
    payload = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(payload) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds the 5 MB demo limit.")
    try:
        sections = extract(file.filename or "upload", payload)
        text = "\n\n".join(content for _, content in sections)
        if not text.strip():
            raise ValueError("No usable text was found.")
        document_id, chunks, created = ingest_text(property_id, file.filename or "upload", "uploaded", text)
        return {"id": document_id, "chunks": chunks, "created": created}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
