from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from langchain_core.messages import HumanMessage
from backend.app.agent.client import app as agent_app

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

@router.post("/", response_model=SearchResponse)
async def search_legislation(request: SearchRequest):
    try:
        # Agent Invocation
        inputs = {"messages": [HumanMessage(content=request.query)]}
        result = await agent_app.ainvoke(inputs)
        
        # Extract Answer
        last_message = result["messages"][-1]
        answer = last_message.content
        
        # Extract Sources (if any, chitchat will have empty list)
        sources = result.get("sources", [])
        
        return SearchResponse(
            answer=answer,
            sources=sources
        )
    except Exception as e:
        print(f"Agent Error: {e}")
        # Identify Quota issues
        if "429" in str(e) or "Quota" in str(e):
            raise HTTPException(status_code=429, detail="Google Gemini API kotası doldu.")
            
        raise HTTPException(status_code=500, detail=str(e))
