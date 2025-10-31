from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime


class DocumentInfo(BaseModel):
    """Document metadata information"""
    file_name: str
    file_path: str
    file_size: int
    file_type: str
    page_count: Optional[int] = None
    chunk_count: int
    processed_at: datetime
    status: str
    error_message: Optional[str] = None


class IngestionStatus(BaseModel):
    """Status of the ingestion process"""
    total_files: int
    processed_files: int
    failed_files: int
    skipped_files: int
    start_time: datetime
    end_time: Optional[datetime] = None
    is_complete: bool
    errors: List[str] = []


class IngestionResponse(BaseModel):
    """Response model for ingestion API"""
    success: bool
    message: str
    status: IngestionStatus
    documents: List[DocumentInfo] = []


class DocumentListResponse(BaseModel):
    """Response model for document list API"""
    success: bool
    message: str
    total_documents: int
    documents: List[DocumentInfo] = []