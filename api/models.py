from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    query: str = Field(min_length=2, max_length=500)
    property_id: str
    top_k: int = Field(default=4, ge=1, le=8)


class Source(BaseModel):
    id: str
    document_id: str
    document_name: str
    locator: str
    excerpt: str
    relevance: float


class AskResponse(BaseModel):
    answer: str
    found_in_documents: bool
    sources: list[Source]
    retrieval_method: str = "term-overlap demo retrieval"


class Property(BaseModel):
    id: str
    name: str
    address: str


class DocumentSummary(BaseModel):
    id: str
    property_id: str
    name: str
    kind: str
    status: str
    locator_label: str
