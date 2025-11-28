from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.chatbot import Chatbot
from app.repositories.chatbot import ChatbotRepository
from app.schemas.chatbot import ChatbotCreate, ChatbotUpdate


class ChatbotService:
    def __init__(self, db: Session):
        self.repository = ChatbotRepository(db)

    def get_chatbot(self, chatbot_id: UUID) -> Optional[Chatbot]:
        return self.repository.get(chatbot_id)

    def get_chatbots(self, skip: int = 0, limit: int = 100) -> List[Chatbot]:
        return self.repository.get_multi(skip=skip, limit=limit)

    def create_chatbot(self, chatbot_in: ChatbotCreate) -> Chatbot:
        return self.repository.create(chatbot_in)

    def update_chatbot(self, chatbot_id: UUID, chatbot_in: ChatbotUpdate) -> Optional[Chatbot]:
        chatbot = self.repository.get(chatbot_id)
        if not chatbot:
            return None
        return self.repository.update(chatbot, chatbot_in)

    def delete_chatbot(self, chatbot_id: UUID) -> Optional[Chatbot]:
        return self.repository.delete(chatbot_id)
