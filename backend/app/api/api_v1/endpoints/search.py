from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from backend.app.services.rag_service import query_rag

router = APIRouter()

class SearchRequest(BaseModel):
    query: str
    top_k: int = 5

class Source(BaseModel):
    source: str
    page: Any
    type: Optional[str] = None
    # Add other meta fields if needed

class SearchResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    # debug info
    # context: str 

@router.post("/", response_model=SearchResponse)
def search_legislation(request: SearchRequest):
    try:
        result = query_rag(request.query, request.top_k)
        
        # Check for error key in result
        if isinstance(result, dict) and "error" in result:
             # Try to identify 429
             error_msg = str(result["error"])
             status_code = 429 if "429" in error_msg or "Quota" in error_msg else 500
             raise HTTPException(status_code=status_code, detail=error_msg)
             
        return SearchResponse(
            answer=result["answer"],
            sources=result["sources"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
