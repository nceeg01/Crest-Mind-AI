from __future__ import annotations

import hashlib
import os
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = Path(os.getenv("CRESTMIND_DB_PATH", ROOT / "data" / "crestmind.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS properties (
  id TEXT PRIMARY KEY, name TEXT NOT NULL, address TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS documents (
  id TEXT PRIMARY KEY, property_id TEXT NOT NULL REFERENCES properties(id),
  name TEXT NOT NULL, kind TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'ingested',
  content_hash TEXT NOT NULL UNIQUE, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS chunks (
  id TEXT PRIMARY KEY, document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  locator TEXT NOT NULL, content TEXT NOT NULL
);
"""


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db


def initialize() -> None:
    with connect() as db:
        db.executescript(SCHEMA)


def seed() -> None:
    fixtures = ROOT / "data" / "synthetic"
    properties = [
        ("maple-ridge", "Maple Ridge Apartments", "123 Maple St, Austin, TX"),
        ("riverside", "Riverside Commons", "456 River Rd, Denver, CO"),
        ("oakview", "Oakview Plaza", "789 Oak Ave, Seattle, WA"),
    ]
    with connect() as db:
        db.executemany("INSERT OR IGNORE INTO properties VALUES (?, ?, ?)", properties)
    for path in sorted(fixtures.glob("*.txt")):
        property_id, kind, display_name = path.stem.split("__", 2)
        ingest_text(property_id, display_name.replace("_", " ") + ".txt", kind, path.read_text())


def ingest_text(property_id: str, name: str, kind: str, text: str) -> tuple[str, int, bool]:
    digest = hashlib.sha256(text.encode()).hexdigest()
    document_id = digest[:16]
    paragraphs = [part.strip() for part in text.split("\n\n") if part.strip()]
    with connect() as db:
        existing = db.execute("SELECT id FROM documents WHERE content_hash = ?", (digest,)).fetchone()
        if existing:
            count = db.execute("SELECT count(*) FROM chunks WHERE document_id = ?", (existing["id"],)).fetchone()[0]
            return existing["id"], count, False
        db.execute("INSERT INTO documents(id, property_id, name, kind, content_hash) VALUES (?, ?, ?, ?, ?)", (document_id, property_id, name, kind, digest))
        for index, paragraph in enumerate(paragraphs, 1):
            db.execute("INSERT INTO chunks VALUES (?, ?, ?, ?)", (f"{document_id}-{index}", document_id, f"Section {index}", paragraph))
    return document_id, len(paragraphs), True
