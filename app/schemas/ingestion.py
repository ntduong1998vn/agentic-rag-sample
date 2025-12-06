"""
Pydantic schemas for ingestion API.
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class IngestionRequest(BaseModel):
    """Request schema for document ingestion."""
    folder_path: str = Field(default="./data", description="Path to folder containing documents to ingest")


class IngestionResponse(BaseModel):
    """Response schema for document ingestion."""
    status: str = Field(..., description="Ingestion status: success, partial, or failed")
    documents_registered: int = Field(..., description="Number of new documents registered")
    documents_processed: int = Field(..., description="Number of documents successfully processed")
    errors: List[str] = Field(default_factory=list, description="List of error messages if any")
