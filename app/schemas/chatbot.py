"""
Pydantic schemas for chatbot API.
"""

from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ChatbotBase(BaseModel):
    """Base chatbot schema."""

    name: str
    model_name: str
    llm_config: Dict[str, Any] = {}


class ChatbotCreate(ChatbotBase):
    """Schema for creating a chatbot."""

    pass


class ChatbotUpdate(BaseModel):
    """Schema for updating a chatbot."""

    name: Optional[str] = None
    model_name: Optional[str] = None
    llm_config: Optional[Dict[str, Any]] = None


class Chatbot(ChatbotBase):
    """Schema for chatbot response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime
