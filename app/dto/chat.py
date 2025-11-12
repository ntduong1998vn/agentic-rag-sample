from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    query: str
    top_k: Optional[int] = 5
    similarity_threshold: Optional[float] = 0.7
    stream: Optional[bool] = True  # Default to streaming


class SourceDocument(BaseModel):
    """Source document information for chat responses"""
    file_name: str
    file_path: str
    chunk_text: str
    similarity_score: float
    metadata: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    success: bool
    answer: str
    sources: List[SourceDocument] = []
    query: str
    response_time: Optional[float] = None
    error_message: Optional[str] = None