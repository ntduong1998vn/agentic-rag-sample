"""
Pure Python domain entities for file ingestion tracking.

This module defines the domain entities without any infrastructure dependencies.
These are pure Python dataclasses that contain business logic and validation.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from enum import Enum


class JobStatus(str, Enum):
    """Status of an ingestion job"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class FileStatus(str, Enum):
    """Status of an individual file"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"
    SKIPPED = "skipped"


@dataclass
class IngestFile:
    """
    Domain entity for tracking individual files within an ingestion job.
    
    Each file record represents a single file being processed as part of an ingestion job,
    with detailed status, metadata, and timing information.
    """
    # Identifiers
    id: UUID = field(default_factory=uuid4)
    job_id: UUID = field(default=None)
    
    # File information
    file_path: str = ""
    source_path: Optional[str] = None
    
    # File status
    file_status: FileStatus = FileStatus.PENDING
    
    # File metadata
    file_size: Optional[int] = None
    checksum: Optional[str] = None
    file_type: Optional[str] = None
    
    # Processing timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Processing results
    chunks_created: int = 0
    documents_added: int = 0
    
    # Additional metadata
    file_metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Validate entity after initialization"""
        if self.file_size is not None and self.file_size < 0:
            raise ValueError("File size cannot be negative")
        
        if self.chunks_created < 0:
            raise ValueError("Chunks created cannot be negative")
        
        if self.documents_added < 0:
            raise ValueError("Documents added cannot be negative")
        
        if self.completed_at and self.started_at and self.completed_at < self.started_at:
            raise ValueError("Completed time cannot be before started time")
    
    def start_processing(self) -> None:
        """Mark file as started processing"""
        self.file_status = FileStatus.PROCESSING
        self.started_at = datetime.now()
    
    def mark_completed(self, chunks: int, documents: int) -> None:
        """Mark file as successfully completed"""
        self.file_status = FileStatus.COMPLETED
        self.completed_at = datetime.now()
        self.chunks_created = chunks
        self.documents_added = documents
    
    def mark_failed(self) -> None:
        """Mark file as failed"""
        self.file_status = FileStatus.FAILED
        self.completed_at = datetime.now()
    
    def mark_skipped(self) -> None:
        """Mark file as skipped"""
        self.file_status = FileStatus.SKIPPED
        self.completed_at = datetime.now()


@dataclass
class IngestJob:
    """
    Domain entity for tracking ingestion jobs.
    
    Each ingestion job represents a single ingestion operation that can process
    multiple files from various data sources (APIs, databases, file systems, cloud storage).
    """
    # Identifiers
    id: UUID = field(default_factory=uuid4)
    process_id: str = ""
    
    # Ingestion type and source
    ingestion_type: str = ""
    source_identifier: str = ""
    source_metadata: Optional[Dict[str, Any]] = None
    
    # Job status
    status: JobStatus = JobStatus.PENDING
    sub_status: Optional[str] = None
    
    # Timing information
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    updated_at: datetime = field(default_factory=datetime.now)
    
    # File processing statistics
    total_files: int = 0
    files_processed: int = 0
    files_succeeded: int = 0
    files_failed: int = 0
    files_skipped: int = 0
    
    # Processing results
    chunks_created: int = 0
    documents_added: int = 0
    
    # Error handling
    error_messages: Optional[List[Dict[str, Any]]] = None
    error_summary: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    
    # Configuration and settings
    ingestion_config: Optional[Dict[str, Any]] = None
    processing_settings: Optional[Dict[str, Any]] = None
    
    # Audit information
    user_agent: Optional[str] = None
    client_info: Optional[Dict[str, Any]] = None
    environment_info: Optional[Dict[str, Any]] = None
    
    # Related files
    files: List[IngestFile] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate entity after initialization"""
        if self.total_files < 0:
            raise ValueError("Total files cannot be negative")
        
        if self.files_processed < 0 or self.files_succeeded < 0 or self.files_failed < 0 or self.files_skipped < 0:
            raise ValueError("File counts cannot be negative")
        
        if self.files_processed != self.files_succeeded + self.files_failed + self.files_skipped:
            raise ValueError("files_processed must equal files_succeeded + files_failed + files_skipped")
        
        if self.retry_count < 0 or self.retry_count > self.max_retries:
            raise ValueError(f"Retry count must be between 0 and {self.max_retries}")
        
        if self.completed_at and self.started_at and self.completed_at < self.started_at:
            raise ValueError("Completed time cannot be before started time")
    
    def start(self) -> None:
        """Mark job as started"""
        self.status = JobStatus.IN_PROGRESS
        self.started_at = datetime.now()
        self.updated_at = datetime.now()
    
    def complete(self) -> None:
        """Mark job as completed"""
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.now()
        self.updated_at = datetime.now()
    
    def fail(self, error_message: Optional[str] = None) -> None:
        """Mark job as failed"""
        self.status = JobStatus.FAILED
        self.completed_at = datetime.now()
        self.updated_at = datetime.now()
        
        if error_message:
            self.error_summary = error_message
            if self.error_messages is None:
                self.error_messages = []
            self.error_messages.append({
                "timestamp": datetime.now().isoformat(),
                "message": error_message
            })
    
    def cancel(self) -> None:
        """Cancel the job"""
        self.status = JobStatus.CANCELLED
        self.completed_at = datetime.now()
        self.updated_at = datetime.now()
    
    def increment_retry(self) -> bool:
        """
        Increment retry count. Returns True if retry is allowed, False otherwise.
        """
        if self.retry_count >= self.max_retries:
            return False
        
        self.retry_count += 1
        self.updated_at = datetime.now()
        return True
    
    def update_file_stats(self, succeeded: int = 0, failed: int = 0, skipped: int = 0) -> None:
        """Update file processing statistics"""
        self.files_succeeded += succeeded
        self.files_failed += failed
        self.files_skipped += skipped
        self.files_processed = self.files_succeeded + self.files_failed + self.files_skipped
        self.updated_at = datetime.now()
    
    def add_file(self, file: IngestFile) -> None:
        """Add a file to this job"""
        file.job_id = self.id
        self.files.append(file)
        self.total_files = len(self.files)
        self.updated_at = datetime.now()
    
    def can_retry(self) -> bool:
        """Check if job can be retried"""
        return self.retry_count < self.max_retries
    
    def is_active(self) -> bool:
        """Check if job is currently active"""
        return self.status in [JobStatus.PENDING, JobStatus.IN_PROGRESS]
    
    def is_finished(self) -> bool:
        """Check if job is finished (completed, failed, or cancelled)"""
        return self.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]
