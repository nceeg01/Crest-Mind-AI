import os
os.environ["CRESTMIND_DB_PATH"]="/tmp/crestmind-test.db"
from fastapi.testclient import TestClient
from api.main import app
def test_answer_and_isolation():
 with TestClient(app)as c:
  good=c.post("/ask",json={"query":"maximum building height","property_id":"maple-ridge"}).json()
  none=c.post("/ask",json={"query":"maximum building height","property_id":"riverside"}).json()
 assert good["found_in_documents"]and"60 feet"in good["answer"]and good["sources"]
 assert not none["found_in_documents"]
def test_bounds():
 with TestClient(app)as c:assert c.post("/ask",json={"query":"height","property_id":"maple-ridge","top_k":99}).status_code==422
def test_idempotent_upload():
 with TestClient(app)as c:
  one=c.post("/documents?property_id=maple-ridge",files={"file":("note.txt",b"Roof access requires notice.","text/plain")}).json()
  two=c.post("/documents?property_id=maple-ridge",files={"file":("note.txt",b"Roof access requires notice.","text/plain")}).json()
 assert one["created"]and not two["created"]
