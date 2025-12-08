import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base


class Conversation(Base):
    """
    Represents a chat conversation between a user and a chatbot.
    
    Links to:
    - ChatMessage via session_id (for LangChain ChatMessageHistory)
    - LangGraph checkpoints via thread_id (for LangGraph PostgresSaver)
    """
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chatbot_id = Column(UUID(as_uuid=True), ForeignKey("chatbots.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    title = Column(String(500), nullable=True)
    
    # LangChain ChatMessageHistory session identifier
    session_id = Column(String(255), nullable=False, unique=True, index=True)
    
    # LangGraph checkpoint thread identifier
    thread_id = Column(String(255), nullable=False, unique=True, index=True)
    
    status = Column(String(20), nullable=False, default="active", index=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    chatbot = relationship("Chatbot", backref="conversations")
    documents = relationship("ConversationDocument", back_populates="conversation", cascade="all, delete-orphan")
    messages = relationship(
        "ChatMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        primaryjoin="Conversation.session_id == ChatMessage.session_id",
        foreign_keys="[ChatMessage.session_id]",
    )
