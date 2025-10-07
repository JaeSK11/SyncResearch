from pydantic import BaseModel
from typing import List

class Source(BaseModel):
    paper_id: str
    section: str
    chunk_id: str = ""

class QueryResponse(BaseModel):
    answer: str
    sources: List[Source]
    confidence: float
    processing_time: float

class PaperInfo(BaseModel):
    paper_id: str
    title: str
    num_chunks: int
    processed_at: str