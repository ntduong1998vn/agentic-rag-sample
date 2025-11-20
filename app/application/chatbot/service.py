from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime

from app.domain.chatbot.entities import Chatbot
from app.domain.chatbot.ports import ChatbotRepository

class ChatbotService:
    """
    Service for managing chatbots.
    """

    def __init__(self, repository: ChatbotRepository):
        self.repository = repository

    async def create_chatbot(self, name: str, model_name: str, llm_config: Dict[str, Any]) -> Chatbot:
        """
        Create a new chatbot.
        """
        chatbot = Chatbot(
            name=name,
            model_name=model_name,
            llm_config=llm_config
        )
        return await self.repository.create(chatbot)

    async def get_chatbot(self, chatbot_id: uuid.UUID) -> Optional[Chatbot]:
        """
        Get a chatbot by ID.
        """
        return await self.repository.get_by_id(chatbot_id)

    async def list_chatbots(self, skip: int = 0, limit: int = 100) -> List[Chatbot]:
        """
        List all chatbots.
        """
        return await self.repository.list(skip, limit)

    async def update_chatbot(self, chatbot_id: uuid.UUID, name: Optional[str] = None, 
                           model_name: Optional[str] = None, llm_config: Optional[Dict[str, Any]] = None) -> Optional[Chatbot]:
        """
        Update a chatbot.
        """
        chatbot = await self.repository.get_by_id(chatbot_id)
        if not chatbot:
            return None
        
        chatbot.update(name=name, model_name=model_name, llm_config=llm_config)
        return await self.repository.update(chatbot)

    async def delete_chatbot(self, chatbot_id: uuid.UUID) -> bool:
        """
        Delete a chatbot.
        """
        return await self.repository.delete(chatbot_id)
