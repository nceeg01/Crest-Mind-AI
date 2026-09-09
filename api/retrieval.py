from __future__ import annotations

import re
from collections import Counter

from .storage import connect

STOP = {"a", "an", "and", "are", "for", "in", "is", "of", "on", "the", "to", "what", "with"}


def terms(text: str) -> list[str]:
    return [w for w in re.findall(r"[a-z0-9]+", text.lower()) if len(w) > 1 and w not in STOP]


def search(query: str, property_id: str, top_k: int) -> list[dict]:
    query_terms = Counter(terms(query))
    with connect() as db:
        rows = db.execute("""SELECT c.id, c.document_id, c.locator, c.content, d.name AS document_name
               FROM chunks c JOIN documents d ON d.id = c.document_id
               WHERE d.property_id = ?""", (property_id,)).fetchall()
    scored = []
    for row in rows:
        content_terms = Counter(terms(row["content"]))
        overlap = sum(min(count, content_terms[word]) for word, count in query_terms.items())
        coverage = overlap / max(1, sum(query_terms.values()))
        if coverage > 0:
            scored.append({**dict(row), "relevance": round(coverage, 3)})
    return sorted(scored, key=lambda item: (-item["relevance"], item["id"]))[:top_k]


def answer_from_sources(query: str, sources: list[dict]) -> str:
    if not sources:
        return "I couldn’t find evidence for that question. Try another phrase or upload a relevant document."
    sentences = []
    wanted = set(terms(query))
    for source in sources[:3]:
        candidates = re.split(r"(?<=[.!?])\s+", source["content"])
        best = max(candidates, key=lambda sentence: len(wanted.intersection(terms(sentence))), default="")
        if best and best not in sentences:
            sentences.append(best.strip())
    return " ".join(f"{sentence} [{index}]" for index, sentence in enumerate(sentences, 1))
