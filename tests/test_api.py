import os

os.environ["CRESTMIND_DB_PATH"] = "/tmp/crestmind-test.db"

from fastapi.testclient import TestClient

from api.main import app


def test_grounded_answer_and_citations():
    with TestClient(app) as client:
        response = client.post("/ask", json={"query": "What is the maximum building height?", "property_id": "maple-ridge"})
    assert response.status_code == 200
    body = response.json()
    assert body["found_in_documents"] is True
    assert "60 feet" in body["answer"]
    assert body["sources"][0]["document_name"]


def test_property_isolation_and_unknown_answer():
    with TestClient(app) as client:
        response = client.post("/ask", json={"query": "What is the maximum building height?", "property_id": "riverside"})
    assert response.status_code == 200
    assert response.json()["found_in_documents"] is False


def test_top_k_is_bounded():
    with TestClient(app) as client:
        response = client.post("/ask", json={"query": "height", "property_id": "maple-ridge", "top_k": 99})
    assert response.status_code == 422


def test_duplicate_upload_is_idempotent():
    with TestClient(app) as client:
        first = client.post("/documents?property_id=maple-ridge", files={"file": ("note.txt", b"Roof access requires written notice.", "text/plain")})
        second = client.post("/documents?property_id=maple-ridge", files={"file": ("note.txt", b"Roof access requires written notice.", "text/plain")})
    assert first.status_code == 200
    assert first.json()["created"] is True
    assert second.json()["created"] is False
