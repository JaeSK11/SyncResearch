from pydantic import BaseModel
from typing import Optional, List

class QueryRequest(BaseModel):
    question: str
    paper_filter: Optional[str] = None
    n_results: int = 5

class CompareRequest(BaseModel):
    paper_x: str
    paper_y: str
    comparison_type: str = "general"  # general, methodology, results