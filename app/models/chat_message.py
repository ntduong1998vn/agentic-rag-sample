from sqlalchemy import Column, String, DateTime, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base


class ChatMessage(Base):
    """
    Stores chat messages in a format compatible with LangChain PostgresChatMessageHistory.
    
    The message column stores JSONB with the following structure:
    {
        "type": "human" | "ai" | "system" | "tool",
        "content": "message content",
        "additional_kwargs": {},
        "response_metadata": {}
    }
    
    Note: session_id links to conversations.session_id for application-level queries,
    while LangChain uses session_id directly for its memory operations.
    """
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # LangChain required: session identifier for message grouping
    session_id = Column(String(255), nullable=False, index=True)
    
    # LangChain required: message content in JSONB format
    message = Column(JSONB, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationship to conversation (via session_id foreign key)
    conversation = relationship(
        "Conversation",
        back_populates="messages",
        primaryjoin="ChatMessage.session_id == Conversation.session_id",
        foreign_keys="[ChatMessage.session_id]",
    )
