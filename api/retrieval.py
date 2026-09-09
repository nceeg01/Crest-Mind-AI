import re
from collections import Counter
from .storage import connect
STOP={"a","an","and","are","for","in","is","of","on","the","to","what","with"}
def terms(text):return[w for w in re.findall(r"[a-z0-9]+",text.lower())if len(w)>1 and w not in STOP]
def search(query,property_id,top_k):
 wanted=Counter(terms(query))
 with connect()as db:rows=db.execute("SELECT c.*,d.name document_name FROM chunks c JOIN documents d ON d.id=c.document_id WHERE d.property_id=?",(property_id,)).fetchall()
 scored=[]
 for row in rows:
  have=Counter(terms(row["content"]));overlap=sum(min(n,have[w])for w,n in wanted.items());coverage=overlap/max(1,sum(wanted.values()))
  if coverage:scored.append({**dict(row),"relevance":round(coverage,3)})
 return sorted(scored,key=lambda x:(-x["relevance"],x["id"]))[:top_k]
def answer(query,sources):
 if not sources:return"I couldn’t find evidence for that question."
 wanted=set(terms(query));out=[]
 for source in sources[:3]:
  parts=re.split(r"(?<=[.!?])\s+",source["content"]);best=max(parts,key=lambda s:len(wanted.intersection(terms(s))),default="")
  if best and best not in out:out.append(best)
 return" ".join(f"{text} [{i}]"for i,text in enumerate(out,1))
