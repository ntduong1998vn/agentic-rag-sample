from abc import ABC, abstractmethod
from typing import List, Optional
import uuid
from app.domain.chatbot.entities import Chatbot

class ChatbotRepository(ABC):
    """
    Interface for Chatbot persistence.
    """

    @abstractmethod
    async def create(self, chatbot: Chatbot) -> Chatbot:
        """Save a new chatbot."""
        pass

    @abstractmethod
    async def get_by_id(self, chatbot_id: uuid.UUID) -> Optional[Chatbot]:
        """Retrieve a chatbot by its ID."""
        pass

    @abstractmethod
    async def list(self, skip: int = 0, limit: int = 100) -> List[Chatbot]:
        """List all chatbots with pagination."""
        pass

    @abstractmethod
    async def update(self, chatbot: Chatbot) -> Chatbot:
        """Update an existing chatbot."""
        pass

    @abstractmethod
    async def delete(self, chatbot_id: uuid.UUID) -> bool:
        """Delete a chatbot by its ID."""
        pass
