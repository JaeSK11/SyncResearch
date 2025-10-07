from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import shutil
from api.models.responses import PaperInfo
from api.dependencies import get_pipeline
import sys
from pathlib import Path
# Add parent directory to path so we can import our modules
sys.path.append(str(Path(__file__).parent.parent))

from functools import lru_cache
from rag_pipeline.basic_rag import BasicRAG
from storage.minio_client import MinIOStorage
router = APIRouter()

@router.post("/upload")
async def upload_paper(file: UploadFile = File(...)):
    """Upload and process a new research paper"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(400, "Only PDF files accepted")
    
    # Save uploaded file
    temp_path = Path(f"/tmp/{file.filename}")
    with temp_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Process through pipeline
    pipeline = get_pipeline()
    result = pipeline.process_paper(str(temp_path))
    
    return {"message": "Paper processed", "paper_id": result['paper_id']}

@router.get("/", response_model=List[PaperInfo])
async def list_papers():
    """List all papers in the system"""
    pipeline = get_pipeline()
    papers = pipeline.list_papers()
    return papers

@router.delete("/{paper_id}")
async def delete_paper(paper_id: str):
    """Remove a paper from the system"""
    # Implementation
    return {"message": f"Paper {paper_id} deleted"}