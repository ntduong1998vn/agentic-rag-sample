"""
Chatbot service for CRUD operations.
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.chatbot import Chatbot
from app.schemas.chatbot import ChatbotCreate, ChatbotUpdate


class ChatbotService:
    """Service for chatbot operations."""

    def __init__(self, db: Session):
        self.db = db

    def create_chatbot(self, chatbot_in: ChatbotCreate) -> Chatbot:
        """Create a new chatbot."""
        chatbot = Chatbot(
            name=chatbot_in.name,
            model_name=chatbot_in.model_name,
            llm_config=chatbot_in.llm_config,
        )
        self.db.add(chatbot)
        self.db.commit()
        self.db.refresh(chatbot)
        return chatbot

    def get_chatbot(self, chatbot_id: UUID) -> Optional[Chatbot]:
        """Get a chatbot by ID."""
        return self.db.query(Chatbot).filter(Chatbot.id == chatbot_id).first()

    def get_chatbots(self, skip: int = 0, limit: int = 100) -> List[Chatbot]:
        """Get all chatbots with pagination."""
        return self.db.query(Chatbot).offset(skip).limit(limit).all()

    def update_chatbot(self, chatbot_id: UUID, chatbot_in: ChatbotUpdate) -> Optional[Chatbot]:
        """Update an existing chatbot."""
        chatbot = self.get_chatbot(chatbot_id)
        if not chatbot:
            return None

        update_data = chatbot_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(chatbot, field, value)

        self.db.commit()
        self.db.refresh(chatbot)
        return chatbot

    def delete_chatbot(self, chatbot_id: UUID) -> Optional[Chatbot]:
        """Delete a chatbot."""
        chatbot = self.get_chatbot(chatbot_id)
        if not chatbot:
            return None

        self.db.delete(chatbot)
        self.db.commit()
        return chatbot
