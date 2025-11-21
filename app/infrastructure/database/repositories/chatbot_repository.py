from typing import List, Optional
import uuid
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.chatbot.entities import Chatbot
from app.domain.chatbot.ports import ChatbotRepository
from app.infrastructure.database.models import ChatbotModel

class SQLAlchemyChatbotRepository(ChatbotRepository):
    """
    SQLAlchemy implementation of ChatbotRepository.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_entity(self, model: ChatbotModel) -> Chatbot:
        return Chatbot(
            id=model.id,
            name=model.name,
            model_name=model.model_name,
            llm_config=model.llm_config,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    def _to_model(self, entity: Chatbot) -> ChatbotModel:
        return ChatbotModel(
            id=entity.id,
            name=entity.name,
            model_name=entity.model_name,
            llm_config=entity.llm_config,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )

    async def create(self, chatbot: Chatbot) -> Chatbot:
        model = self._to_model(chatbot)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_entity(model)

    async def get_by_id(self, chatbot_id: uuid.UUID) -> Optional[Chatbot]:
        result = await self.session.execute(
            select(ChatbotModel).where(ChatbotModel.id == chatbot_id)
        )
        model = result.scalar_one_or_none()
        if model:
            return self._to_entity(model)
        return None

    async def list(self, skip: int = 0, limit: int = 100) -> List[Chatbot]:
        result = await self.session.execute(
            select(ChatbotModel).offset(skip).limit(limit)
        )
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]

    async def update(self, chatbot: Chatbot) -> Chatbot:
        # In SQLAlchemy, if the object is attached to the session, changes are tracked.
        # However, since we are passing a domain entity, we need to fetch the model and update it.
        # Or merge the detached model.
        # Let's fetch and update for clarity and safety.
        
        result = await self.session.execute(
            select(ChatbotModel).where(ChatbotModel.id == chatbot.id)
        )
        model = result.scalar_one_or_none()
        if not model:
             # Should not happen if logic is correct, but handle gracefully or raise error
             # For now, let's try to merge if not found (upsert behavior) or raise.
             # Given the interface implies update of existing, we expect it to exist.
             raise ValueError(f"Chatbot with id {chatbot.id} not found")

        model.name = chatbot.name
        model.model_name = chatbot.model_name
        model.llm_config = chatbot.llm_config
        # updated_at is handled by DB onupdate, but we can also set it explicitly if we want to sync with entity
        model.updated_at = chatbot.updated_at
        
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_entity(model)

    async def delete(self, chatbot_id: uuid.UUID) -> bool:
        result = await self.session.execute(
            delete(ChatbotModel).where(ChatbotModel.id == chatbot_id)
        )
        return result.rowcount > 0
