"""
Knowledge base service for managing knowledge bases.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.knowledge_base import KnowledgeBase
from app.core.logging import get_logger

logger = get_logger(__name__)

# Gemini embedding dimension (models/embedding-001)
GEMINI_EMBEDDING_DIMENSION = 768


class KnowledgeBaseService:
    """Service for knowledge base operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_chatbot_id(self, chatbot_id: UUID) -> Optional[KnowledgeBase]:
        """Get knowledge base by chatbot ID."""
        return self.db.query(KnowledgeBase).filter(
            KnowledgeBase.chatbot_id == chatbot_id
        ).first()

    def get_or_create_for_chatbot(self, chatbot_id: UUID) -> KnowledgeBase:
        """Get existing or create new knowledge base for a chatbot."""
        existing = self.get_by_chatbot_id(chatbot_id)
        if existing:
            logger.info(f"Found existing knowledge base for chatbot {chatbot_id}")
            return existing

        # Create new knowledge base
        collection_name = f"chatbot_{str(chatbot_id).replace('-', '_')}_kb"
        knowledge_base = KnowledgeBase(
            chatbot_id=chatbot_id,
            collection_name=collection_name,
            vector_dimension=GEMINI_EMBEDDING_DIMENSION,
            total_documents=0,
            total_chunks=0,
        )
        self.db.add(knowledge_base)
        self.db.commit()
        self.db.refresh(knowledge_base)
        logger.info(f"Created new knowledge base '{collection_name}' for chatbot {chatbot_id}")
        return knowledge_base

    def update_stats(self, knowledge_base_id: UUID, total_documents: int, total_chunks: int) -> None:
        """Update knowledge base statistics."""
        knowledge_base = self.db.query(KnowledgeBase).filter(
            KnowledgeBase.id == knowledge_base_id
        ).first()
        if knowledge_base:
            knowledge_base.total_documents = total_documents
            knowledge_base.total_chunks = total_chunks
            self.db.commit()
