import hashlib,os,sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];DB_PATH=Path(os.getenv("CRESTMIND_DB_PATH",ROOT/"data"/"crestmind.db"))
SCHEMA="""CREATE TABLE IF NOT EXISTS properties(id TEXT PRIMARY KEY,name TEXT,address TEXT);CREATE TABLE IF NOT EXISTS documents(id TEXT PRIMARY KEY,property_id TEXT,name TEXT,kind TEXT,content_hash TEXT UNIQUE);CREATE TABLE IF NOT EXISTS chunks(id TEXT PRIMARY KEY,document_id TEXT,locator TEXT,content TEXT);"""
def connect():
 DB_PATH.parent.mkdir(parents=True,exist_ok=True);db=sqlite3.connect(DB_PATH);db.row_factory=sqlite3.Row;return db
def initialize():
 with connect() as db:db.executescript(SCHEMA)
def ingest(property_id,name,kind,text):
 digest=hashlib.sha256(text.encode()).hexdigest();doc_id=digest[:16];parts=[x.strip()for x in text.split("\n\n")if x.strip()]
 with connect() as db:
  old=db.execute("SELECT id FROM documents WHERE content_hash=?",(digest,)).fetchone()
  if old:return old["id"],db.execute("SELECT count(*) FROM chunks WHERE document_id=?",(old["id"],)).fetchone()[0],False
  db.execute("INSERT INTO documents VALUES(?,?,?,?,?)",(doc_id,property_id,name,kind,digest))
  db.executemany("INSERT INTO chunks VALUES(?,?,?,?)",[(f"{doc_id}-{i}",doc_id,f"Section {i}",p)for i,p in enumerate(parts,1)])
 return doc_id,len(parts),True
def seed():
 props=[("maple-ridge","Maple Ridge Apartments","123 Maple St, Austin, TX"),("riverside","Riverside Commons","456 River Rd, Denver, CO"),("oakview","Oakview Plaza","789 Oak Ave, Seattle, WA")]
 with connect()as db:db.executemany("INSERT OR IGNORE INTO properties VALUES(?,?,?)",props)
 for p in(ROOT/"data"/"synthetic").glob("*.txt"):
  prop,kind,name=p.stem.split("__",2);ingest(prop,name.replace("_"," ")+".txt",kind,p.read_text())
