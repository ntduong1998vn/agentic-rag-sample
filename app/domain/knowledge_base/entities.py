"""
Knowledge base domain entities.

This module defines the core business entities for the knowledge base system.
These are pure Python dataclasses with no external dependencies.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum
import uuid


class DocumentStatus(str, Enum):
    """Document processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class KnowledgeBase:
    """
    Domain entity representing a chatbot's knowledge base.
    
    A knowledge base stores documents and their embeddings in a Qdrant collection.
    """
    chatbot_id: uuid.UUID
    collection_name: str
    vector_dimension: int = 1536
    total_documents: int = 0
    total_chunks: int = 0
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def increment_document_count(self, chunks: int = 0) -> None:
        """Increment document and chunk counts."""
        self.total_documents += 1
        self.total_chunks += chunks
    
    def update_stats(self, documents: int, chunks: int) -> None:
        """Update knowledge base statistics."""
        self.total_documents = documents
        self.total_chunks = chunks


@dataclass
class Document:
    """
    Domain entity representing a document in a knowledge base.
    
    Tracks the processing status and metadata of a document.
    """
    knowledge_base_id: uuid.UUID
    file_path: str
    file_name: str
    file_size: int
    file_type: str
    checksum: str
    status: DocumentStatus = DocumentStatus.PENDING
    error_message: Optional[str] = None
    chunks_count: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def start_processing(self) -> None:
        """Mark document as processing."""
        self.status = DocumentStatus.PROCESSING
        self.started_at = datetime.now()
    
    def mark_completed(self, chunks_count: int) -> None:
        """Mark document as completed."""
        self.status = DocumentStatus.COMPLETED
        self.chunks_count = chunks_count
        self.completed_at = datetime.now()
    
    def mark_failed(self, error_message: str) -> None:
        """Mark document as failed."""
        self.status = DocumentStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.now()
    
    def mark_skipped(self, reason: str) -> None:
        """Mark document as skipped."""
        self.status = DocumentStatus.SKIPPED
        self.error_message = reason


@dataclass
class FileInfo:
    """
    Value object representing file information from scanning.
    
    Used to pass file metadata before creating Document entities.
    """
    file_path: str
    file_name: str
    file_size: int
    file_type: str
    checksum: str
