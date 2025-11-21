"""
Knowledge Base API schemas.

This module defines Pydantic models for knowledge base and document-related API requests and responses.
"""

import uuid
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from app.domain.knowledge_base.entities import DocumentStatus


class IngestRequest(BaseModel):
    """Schema for document ingestion request."""
    folder_path: str = Field(
        default="data",
        description="Path to the folder to ingest documents from"
    )


class IngestResponse(BaseModel):
    """Schema for ingestion response."""
    status: str
    knowledge_base_id: uuid.UUID
    collection_name: str
    files_found: int
    files_processed: int
    files_failed: int
    total_chunks: int


class DocumentResponse(BaseModel):
    """Schema for document information response."""
    id: uuid.UUID
    file_name: str
    file_path: str
    file_size: int
    file_type: str
    status: DocumentStatus
    error_message: Optional[str] = None
    chunks_count: int
    created_at: Any
    updated_at: Any
    
    class Config:
        from_attributes = True


class KnowledgeBaseStats(BaseModel):
    """Schema for knowledge base statistics response."""
    knowledge_base: Dict[str, Any]
    documents: Dict[str, int]
    vector_store: Dict[str, Any]
