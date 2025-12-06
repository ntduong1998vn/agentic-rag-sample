import uuid
from sqlalchemy import Column, String, Integer, BigInteger, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base


class ConversationDocument(Base):
    """
    Represents a document uploaded within a specific conversation.
    
    These documents are stored in a separate vector collection per conversation
    to provide conversation-specific context for the chatbot.
    """
    __tablename__ = "conversation_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # File information
    file_name = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    file_type = Column(String(100), nullable=False)
    
    # Processing status: pending, processing, complete, failed
    status = Column(String(20), nullable=False, default="pending", index=True)
    chunks_count = Column(Integer, nullable=False, default=0)
    error_message = Column(Text, nullable=True)
    
    # Vector collection name for this conversation's documents
    collection_name = Column(String(255), nullable=True, index=True)
    
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    conversation = relationship("Conversation", back_populates="documents")
