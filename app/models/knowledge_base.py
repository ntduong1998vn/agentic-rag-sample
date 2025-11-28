import uuid
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base

class KnowledgeBase(Base):
    __tablename__ = "knowledge_bases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chatbot_id = Column(UUID(as_uuid=True), ForeignKey("chatbots.id", ondelete="CASCADE"), nullable=False, index=True)
    collection_name = Column(String(255), nullable=False, index=True, unique=True)
    vector_dimension = Column(Integer, nullable=False)
    total_documents = Column(Integer, nullable=False, default=0)
    total_chunks = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint('total_chunks >= 0', name='valid_chunks_count'),
        CheckConstraint('total_documents >= 0', name='valid_documents_count'),
        CheckConstraint('vector_dimension > 0', name='valid_vector_dimension'),
    )

    # Relationships
    documents = relationship("Document", back_populates="knowledge_base", cascade="all, delete-orphan")
    chatbot = relationship("Chatbot", backref="knowledge_bases")