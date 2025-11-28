from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel


class ChatbotBase(BaseModel):
    name: str
    model_name: str
    llm_config: Dict[str, Any]


class ChatbotCreate(ChatbotBase):
    pass


class ChatbotUpdate(BaseModel):
    name: Optional[str] = None
    model_name: Optional[str] = None
    llm_config: Optional[Dict[str, Any]] = None


class Chatbot(ChatbotBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
