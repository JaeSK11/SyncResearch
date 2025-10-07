from fastapi import APIRouter, HTTPException
from api.models.requests import QueryRequest, CompareRequest
from api.models.responses import QueryResponse
from api.dependencies import get_rag_pipeline
import time

router = APIRouter()

@router.post("/", response_model=QueryResponse)
async def query_papers(request: QueryRequest):
    """Query the research papers"""
    start = time.time()
   
    try:
        rag = get_rag_pipeline()
        answer, sources = rag.query(
            request.question,
            n_chunks=request.n_results,
            paper_filter=request.paper_filter
        )
        
        # Format sources correctly for frontend
        formatted_sources = []
        if sources and 'metadatas' in sources and sources['metadatas']:
            for metadata in sources['metadatas'][0]:
                formatted_sources.append({
                    'paper_id': metadata.get('paper_id', 'unknown'),
                    'section': metadata.get('section', 'general'),
                    'chunk_id': str(metadata.get('chunk_id', ''))  
                })
        
        return QueryResponse(
            answer=answer,
            sources=formatted_sources,
            confidence=0.85,
            processing_time=time.time() - start
        )
    except Exception as e:
        import traceback
        print(f"Error: {traceback.format_exc()}")
        raise HTTPException(500, str(e))

@router.post("/compare")
async def compare_papers(request: CompareRequest):
    """Compare two research papers"""
    # Multi-agent comparison implementation
    return {"comparison": "Not yet implemented"}