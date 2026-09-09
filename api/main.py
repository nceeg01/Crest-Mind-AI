import os,secrets
from contextlib import asynccontextmanager
from fastapi import Depends,FastAPI,File,Header,HTTPException,UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel,Field
from .retrieval import answer,search
from .storage import connect,ingest,initialize,seed
class Ask(BaseModel):query:str=Field(min_length=2,max_length=500);property_id:str;top_k:int=Field(4,ge=1,le=8)
def auth(x_api_key:str|None=Header(None)):
 expected=os.getenv("API_KEY")
 if expected and(not x_api_key or not secrets.compare_digest(expected,x_api_key)):raise HTTPException(401,"Invalid or missing API key.")
@asynccontextmanager
async def life(_):initialize();seed();yield
app=FastAPI(title="CrestMind AI",lifespan=life)
app.add_middleware(CORSMiddleware,allow_origins=os.getenv("ALLOWED_ORIGINS","http://localhost:5173").split(","),allow_credentials=False,allow_methods=["GET","POST"],allow_headers=["Content-Type","X-Api-Key"])
@app.get("/health")
def health():return{"status":"ok","mode":"synthetic-demo"}
@app.get("/properties")
def properties(_=Depends(auth)):
 with connect()as db:return[dict(x)for x in db.execute("SELECT * FROM properties ORDER BY name")]
@app.get("/documents")
def documents(property_id:str,_=Depends(auth)):
 with connect()as db:return[dict(x)for x in db.execute("SELECT id,property_id,name,kind FROM documents WHERE property_id=?",(property_id,))]
@app.post("/ask")
def ask(request:Ask,_=Depends(auth)):
 rows=search(request.query,request.property_id,request.top_k)
 return{"answer":answer(request.query,rows),"found_in_documents":bool(rows),"retrieval_method":"term-overlap demo retrieval","sources":[{"id":x["id"],"document_id":x["document_id"],"document_name":x["document_name"],"locator":x["locator"],"excerpt":x["content"],"relevance":x["relevance"]}for x in rows]}
@app.post("/documents")
async def upload(property_id:str,file:UploadFile=File(...),_=Depends(auth)):
 payload=await file.read(5*1024*1024+1)
 if len(payload)>5*1024*1024:raise HTTPException(413,"File exceeds the 5 MB demo limit.")
 if not(file.filename or"").lower().endswith(".txt"):raise HTTPException(422,"Public API fixture accepts TXT; PDF/DOCX OCR adapter requires the container build.")
 try:text=payload.decode()
 except UnicodeDecodeError:raise HTTPException(422,"File is not valid UTF-8.")
 doc,chunks,created=ingest(property_id,file.filename or"upload.txt","uploaded",text)
 return{"id":doc,"chunks":chunks,"created":created}
