"""
Pydantic schemas for conversation and chat API.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ConversationCreate(BaseModel):
    """Schema for creating a conversation."""
    user_id: UUID
    title: Optional[str] = None


class ConversationUpdate(BaseModel):
    """Schema for updating a conversation."""
    title: Optional[str] = None
    status: Optional[str] = None


class Conversation(BaseModel):
    """Schema for conversation response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    chatbot_id: UUID
    user_id: UUID
    title: Optional[str]
    session_id: str
    thread_id: str
    status: str
    created_at: datetime
    updated_at: datetime


class ChatRequest(BaseModel):
    """Schema for chat request."""
    message: str


class SourceDocument(BaseModel):
    """Schema for RAG source document."""
    content: str
    metadata: Dict[str, Any] = {}


class ChatResponse(BaseModel):
    """Schema for chat response."""
    response: str
    conversation_id: UUID
    sources: List[SourceDocument] = []


class ChatMessage(BaseModel):
    """Schema for chat message history."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: str
    role: str
    message: Dict[str, Any]
    created_at: datetime
