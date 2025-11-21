"""
Knowledge base repository implementation.

This module implements the repository pattern for knowledge base data access.
"""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.domain.knowledge_base.entities import KnowledgeBase
from app.domain.knowledge_base.ports import KnowledgeBaseRepositoryPort
from app.infrastructure.database.models import KnowledgeBaseModel


class SQLAlchemyKnowledgeBaseRepository(KnowledgeBaseRepositoryPort):
    """SQLAlchemy implementation of knowledge base repository."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, knowledge_base: KnowledgeBase) -> KnowledgeBase:
        """Create a new knowledge base."""
        model = KnowledgeBaseModel(
            id=knowledge_base.id,
            chatbot_id=knowledge_base.chatbot_id,
            collection_name=knowledge_base.collection_name,
            vector_dimension=knowledge_base.vector_dimension,
            total_documents=knowledge_base.total_documents,
            total_chunks=knowledge_base.total_chunks,
        )
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return self._to_entity(model)
    
    async def get_by_id(self, knowledge_base_id: uuid.UUID) -> Optional[KnowledgeBase]:
        """Get knowledge base by ID."""
        stmt = select(KnowledgeBaseModel).where(KnowledgeBaseModel.id == knowledge_base_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None
    
    async def get_by_chatbot_id(self, chatbot_id: uuid.UUID) -> Optional[KnowledgeBase]:
        """Get knowledge base by chatbot ID."""
        stmt = select(KnowledgeBaseModel).where(KnowledgeBaseModel.chatbot_id == chatbot_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None
    
    async def update(self, knowledge_base: KnowledgeBase) -> KnowledgeBase:
        """Update knowledge base."""
        stmt = select(KnowledgeBaseModel).where(KnowledgeBaseModel.id == knowledge_base.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            raise ValueError(f"Knowledge base with id {knowledge_base.id} not found")
        
        model.collection_name = knowledge_base.collection_name
        model.vector_dimension = knowledge_base.vector_dimension
        model.total_documents = knowledge_base.total_documents
        model.total_chunks = knowledge_base.total_chunks
        
        await self.session.commit()
        await self.session.refresh(model)
        return self._to_entity(model)
    
    async def delete(self, knowledge_base_id: uuid.UUID) -> bool:
        """Delete knowledge base."""
        stmt = select(KnowledgeBaseModel).where(KnowledgeBaseModel.id == knowledge_base_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            return False
        
        await self.session.delete(model)
        await self.session.commit()
        return True
    
    @staticmethod
    def _to_entity(model: KnowledgeBaseModel) -> KnowledgeBase:
        """Convert ORM model to domain entity."""
        return KnowledgeBase(
            id=model.id,
            chatbot_id=model.chatbot_id,
            collection_name=model.collection_name,
            vector_dimension=model.vector_dimension,
            total_documents=model.total_documents,
            total_chunks=model.total_chunks,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
