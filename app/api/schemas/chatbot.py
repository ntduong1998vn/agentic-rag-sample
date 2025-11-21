"""
Chatbot API schemas.

This module defines Pydantic models for chatbot-related API requests and responses.
"""

import uuid
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class ChatbotCreate(BaseModel):
    """Schema for creating a new chatbot."""
    name: str = Field(..., min_length=1, max_length=255, description="Name of the chatbot")
    model_name: str = Field(..., min_length=1, max_length=255, description="LLM model to use")
    llm_config: Dict[str, Any] = Field(default_factory=dict, description="LLM configuration parameters")


class ChatbotUpdate(BaseModel):
    """Schema for updating an existing chatbot."""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="New name for the chatbot")
    model_name: Optional[str] = Field(None, min_length=1, max_length=255, description="New LLM model")
    llm_config: Optional[Dict[str, Any]] = Field(None, description="New LLM configuration")


class ChatbotResponse(BaseModel):
    """Schema for chatbot response."""
    id: uuid.UUID
    name: str
    model_name: str
    llm_config: Dict[str, Any]
    created_at: Any
    updated_at: Any

    class Config:
        from_attributes = True
