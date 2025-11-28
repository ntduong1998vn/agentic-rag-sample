from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.chatbot import Chatbot, ChatbotCreate, ChatbotUpdate
from app.services.chatbot import ChatbotService

router = APIRouter()


@router.post("/", response_model=Chatbot)
def create_chatbot(
    chatbot_in: ChatbotCreate,
    db: Session = Depends(get_db),
) -> Chatbot:
    service = ChatbotService(db)
    return service.create_chatbot(chatbot_in)


@router.get("/", response_model=List[Chatbot])
def read_chatbots(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> List[Chatbot]:
    service = ChatbotService(db)
    return service.get_chatbots(skip=skip, limit=limit)


@router.get("/{chatbot_id}", response_model=Chatbot)
def read_chatbot(
    chatbot_id: UUID,
    db: Session = Depends(get_db),
) -> Chatbot:
    service = ChatbotService(db)
    chatbot = service.get_chatbot(chatbot_id)
    if not chatbot:
        raise HTTPException(status_code=404, detail="Chatbot not found")
    return chatbot


@router.put("/{chatbot_id}", response_model=Chatbot)
def update_chatbot(
    chatbot_id: UUID,
    chatbot_in: ChatbotUpdate,
    db: Session = Depends(get_db),
) -> Chatbot:
    service = ChatbotService(db)
    chatbot = service.update_chatbot(chatbot_id, chatbot_in)
    if not chatbot:
        raise HTTPException(status_code=404, detail="Chatbot not found")
    return chatbot


@router.delete("/{chatbot_id}", response_model=Chatbot)
def delete_chatbot(
    chatbot_id: UUID,
    db: Session = Depends(get_db),
) -> Chatbot:
    service = ChatbotService(db)
    chatbot = service.delete_chatbot(chatbot_id)
    if not chatbot:
        raise HTTPException(status_code=404, detail="Chatbot not found")
    return chatbot
