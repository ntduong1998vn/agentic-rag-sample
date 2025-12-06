"""
Document service for CRUD operations on documents.
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.document import Document
from app.services.document_scanner import FileInfo
from app.core.logging import get_logger

logger = get_logger(__name__)


class DocumentStatus:
    """Document processing status constants."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETE = "complete"
    FAILED = "failed"


class DocumentService:
    """Service for document operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, document_id: UUID) -> Optional[Document]:
        """Get document by ID."""
        return self.db.query(Document).filter(Document.id == document_id).first()

    def get_by_knowledge_base(self, knowledge_base_id: UUID) -> List[Document]:
        """Get all documents for a knowledge base."""
        return self.db.query(Document).filter(
            Document.knowledge_base_id == knowledge_base_id
        ).all()

    def get_pending_documents(self, knowledge_base_id: UUID) -> List[Document]:
        """Get documents that are not complete (pending or failed)."""
        return self.db.query(Document).filter(
            Document.knowledge_base_id == knowledge_base_id,
            Document.status != DocumentStatus.COMPLETE
        ).all()

    def get_existing_file_paths(self, knowledge_base_id: UUID) -> set:
        """Get set of file paths already registered for a knowledge base."""
        documents = self.db.query(Document.file_path).filter(
            Document.knowledge_base_id == knowledge_base_id
        ).all()
        return {doc.file_path for doc in documents}

    def register_documents(self, knowledge_base_id: UUID, files: List[FileInfo]) -> int:
        """
        Register new documents in the database.
        
        Args:
            knowledge_base_id: ID of the knowledge base
            files: List of file information from scanner
            
        Returns:
            Number of new documents registered
        """
        existing_paths = self.get_existing_file_paths(knowledge_base_id)
        new_count = 0

        for file_info in files:
            if file_info.path in existing_paths:
                logger.debug(f"Skipping already registered file: {file_info.name}")
                continue

            document = Document(
                knowledge_base_id=knowledge_base_id,
                file_path=file_info.path,
                file_name=file_info.name,
                file_size=file_info.size,
                file_type=file_info.file_type,
                status=DocumentStatus.PENDING,
                chunks_count=0,
            )
            self.db.add(document)
            new_count += 1
            logger.info(f"Registered new document: {file_info.name}")

        if new_count > 0:
            self.db.commit()
            logger.info(f"Registered {new_count} new documents")

        return new_count

    def update_status(
        self,
        document_id: UUID,
        status: str,
        error_message: Optional[str] = None,
        chunks_count: int = 0
    ) -> None:
        """Update document processing status."""
        document = self.get_by_id(document_id)
        if not document:
            logger.error(f"Document not found: {document_id}")
            return

        document.status = status
        document.error_message = error_message
        document.chunks_count = chunks_count

        now = datetime.now(timezone.utc)
        if status == DocumentStatus.PROCESSING:
            document.started_at = now
        elif status in (DocumentStatus.COMPLETE, DocumentStatus.FAILED):
            document.completed_at = now

        self.db.commit()
        logger.info(f"Updated document {document_id} status to {status}")
