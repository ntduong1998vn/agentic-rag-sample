from typing import List, Optional, Dict, Any
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.database import get_db
from app.infrastructure.database.chatbot_repository import SQLAlchemyChatbotRepository
from app.application.chatbot.service import ChatbotService

router = APIRouter(prefix="/chatbots", tags=["chatbots"])

# --- Schemas ---

class ChatbotCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    model_name: str = Field(..., min_length=1, max_length=255)
    llm_config: Dict[str, Any] = Field(default_factory=dict)

class ChatbotUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    model_name: Optional[str] = Field(None, min_length=1, max_length=255)
    llm_config: Optional[Dict[str, Any]] = None

class ChatbotResponse(BaseModel):
    id: uuid.UUID
    name: str
    model_name: str
    llm_config: Dict[str, Any]
    created_at: Any # Using Any to avoid datetime serialization issues if not handled elsewhere, but Pydantic handles datetime fine usually.
    updated_at: Any

    class Config:
        from_attributes = True

# --- Dependencies ---

async def get_chatbot_service(db: AsyncSession = Depends(get_db)) -> ChatbotService:
    repository = SQLAlchemyChatbotRepository(db)
    return ChatbotService(repository)

# --- Routes ---

@router.post("/", response_model=ChatbotResponse, status_code=status.HTTP_201_CREATED)
async def create_chatbot(
    chatbot: ChatbotCreate,
    service: ChatbotService = Depends(get_chatbot_service)
):
    return await service.create_chatbot(
        name=chatbot.name,
        model_name=chatbot.model_name,
        llm_config=chatbot.llm_config
    )

@router.get("/", response_model=List[ChatbotResponse])
async def list_chatbots(
    skip: int = 0,
    limit: int = 100,
    service: ChatbotService = Depends(get_chatbot_service)
):
    return await service.list_chatbots(skip=skip, limit=limit)

@router.get("/{chatbot_id}", response_model=ChatbotResponse)
async def get_chatbot(
    chatbot_id: uuid.UUID,
    service: ChatbotService = Depends(get_chatbot_service)
):
    chatbot = await service.get_chatbot(chatbot_id)
    if not chatbot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chatbot not found")
    return chatbot

@router.put("/{chatbot_id}", response_model=ChatbotResponse)
async def update_chatbot(
    chatbot_id: uuid.UUID,
    chatbot_update: ChatbotUpdate,
    service: ChatbotService = Depends(get_chatbot_service)
):
    updated_chatbot = await service.update_chatbot(
        chatbot_id=chatbot_id,
        name=chatbot_update.name,
        model_name=chatbot_update.model_name,
        llm_config=chatbot_update.llm_config
    )
    if not updated_chatbot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chatbot not found")
    return updated_chatbot

@router.delete("/{chatbot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chatbot(
    chatbot_id: uuid.UUID,
    service: ChatbotService = Depends(get_chatbot_service)
):
    success = await service.delete_chatbot(chatbot_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chatbot not found")
