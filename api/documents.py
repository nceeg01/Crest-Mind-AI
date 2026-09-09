from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile

import fitz
from docx import Document


def extract(filename: str, payload: bytes) -> list[tuple[str, str]]:
    suffix = Path(filename).suffix.lower()
    if suffix == ".txt":
        return [("Section 1", payload.decode("utf-8"))]
    with NamedTemporaryFile(suffix=suffix) as temp:
        temp.write(payload)
        temp.flush()
        if suffix == ".docx":
            paragraphs = [p.text.strip() for p in Document(temp.name).paragraphs if p.text.strip()]
            return [(f"Paragraph {i}", text) for i, text in enumerate(paragraphs, 1)]
        if suffix == ".pdf":
            pdf = fitz.open(temp.name)
            pages: list[tuple[str, str]] = []
            for index, page in enumerate(pdf, 1):
                text = page.get_text().strip()
                if not text:
                    try:
                        text = page.get_text(textpage=page.get_textpage_ocr()).strip()
                    except Exception as exc:
                        raise ValueError("This scanned PDF needs Tesseract OCR on the server.") from exc
                pages.append((f"Page {index}", text))
            return pages
    raise ValueError("Only PDF, DOCX, and TXT files are supported.")
