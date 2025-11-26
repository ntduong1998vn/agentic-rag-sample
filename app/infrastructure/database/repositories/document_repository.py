"""
Document repository implementation.

This module implements the repository pattern for document data access.
"""

from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.domain.knowledge_base.entities import Document, DocumentStatus
from app.domain.knowledge_base.ports import DocumentRepositoryPort
from app.infrastructure.database.models import DocumentModel


class SQLAlchemyDocumentRepository(DocumentRepositoryPort):
    """SQLAlchemy implementation of document repository."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, document: Document) -> Document:
        """Create a new document."""
        model = self._to_model(document)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return self._to_entity(model)
    
    async def create_many(self, documents: List[Document]) -> List[Document]:
        """Create multiple documents in batch."""
        models = [self._to_model(doc) for doc in documents]
        self.session.add_all(models)
        await self.session.commit()
        
        # Refresh all models
        for model in models:
            await self.session.refresh(model)
        
        return [self._to_entity(model) for model in models]
    
    async def get_by_id(self, document_id: uuid.UUID) -> Optional[Document]:
        """Get document by ID."""
        stmt = select(DocumentModel).where(DocumentModel.id == document_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None
    
    async def get_by_checksum(self, knowledge_base_id: uuid.UUID, checksum: str) -> Optional[Document]:
        """Get document by checksum to detect duplicates."""
        stmt = select(DocumentModel).where(
            DocumentModel.knowledge_base_id == knowledge_base_id,
            DocumentModel.checksum == checksum
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None
    
    async def list_by_knowledge_base(
        self,
        knowledge_base_id: uuid.UUID,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Document]:
        """List documents in a knowledge base, optionally filtered by status."""
        stmt = select(DocumentModel).where(DocumentModel.knowledge_base_id == knowledge_base_id)
        
        if status:
            stmt = stmt.where(DocumentModel.status == status)
        
        stmt = stmt.offset(skip).limit(limit).order_by(DocumentModel.created_at.desc())
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]
    
    async def update(self, document: Document) -> Document:
        """Update document."""
        stmt = select(DocumentModel).where(DocumentModel.id == document.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            raise ValueError(f"Document with id {document.id} not found")
        
        # Update fields
        model.status = document.status.value
        model.error_message = document.error_message
        model.chunks_count = document.chunks_count
        model.started_at = document.started_at
        model.completed_at = document.completed_at
        
        await self.session.commit()
        await self.session.refresh(model)
        return self._to_entity(model)
    
    async def count_by_status(self, knowledge_base_id: uuid.UUID, status: str) -> int:
        """Count documents by status."""
        stmt = select(func.count()).select_from(DocumentModel).where(
            DocumentModel.knowledge_base_id == knowledge_base_id,
            DocumentModel.status == status
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()
    
    @staticmethod
    def _to_entity(model: DocumentModel) -> Document:
        """Convert ORM model to domain entity."""
        return Document(
            id=model.id,
            knowledge_base_id=model.knowledge_base_id,
            file_path=model.file_path,
            file_name=model.file_name,
            file_size=model.file_size,
            file_type=model.file_type,
            checksum=model.checksum,
            status=DocumentStatus(model.status),
            error_message=model.error_message,
            chunks_count=model.chunks_count,
            started_at=model.started_at,
            completed_at=model.completed_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
    
    @staticmethod
    def _to_model(document: Document) -> DocumentModel:
        """Convert domain entity to ORM model."""
        return DocumentModel(
            id=document.id,
            knowledge_base_id=document.knowledge_base_id,
            file_path=document.file_path,
            file_name=document.file_name,
            file_size=document.file_size,
            file_type=document.file_type,
            checksum=document.checksum,
            status=document.status.value,
            error_message=document.error_message,
            chunks_count=document.chunks_count,
            started_at=document.started_at,
            completed_at=document.completed_at,
        )
