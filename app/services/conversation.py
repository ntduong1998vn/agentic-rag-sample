"""
Conversation service for CRUD operations and chat.
"""

import uuid
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.models.chat_message import ChatMessage
from app.schemas.conversation import ConversationCreate, ConversationUpdate


class ConversationService:
    """Service for conversation operations."""

    def __init__(self, db: Session):
        self.db = db

    def create_conversation(
        self, chatbot_id: UUID, conversation_in: ConversationCreate
    ) -> Conversation:
        """Create a new conversation."""
        conversation = Conversation(
            chatbot_id=chatbot_id,
            user_id=conversation_in.user_id,
            title=conversation_in.title or "New Conversation",
            session_id=str(uuid.uuid4()),
            thread_id=str(uuid.uuid4()),
            status="active",
        )
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def get_conversation(self, conversation_id: UUID) -> Optional[Conversation]:
        """Get a conversation by ID."""
        return (
            self.db.query(Conversation)
            .filter(Conversation.id == conversation_id)
            .first()
        )

    def get_conversations(
        self,
        chatbot_id: UUID,
        user_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Conversation]:
        """Get all conversations for a chatbot with optional user filter."""
        query = self.db.query(Conversation).filter(
            Conversation.chatbot_id == chatbot_id
        )
        if user_id:
            query = query.filter(Conversation.user_id == user_id)
        return (
            query.order_by(Conversation.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update_conversation(
        self, conversation_id: UUID, conversation_in: ConversationUpdate
    ) -> Optional[Conversation]:
        """Update an existing conversation."""
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return None

        update_data = conversation_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(conversation, field, value)

        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def delete_conversation(self, conversation_id: UUID) -> Optional[Conversation]:
        """Delete a conversation."""
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return None

        self.db.delete(conversation)
        self.db.commit()
        return conversation

    def get_messages(
        self, session_id: str, skip: int = 0, limit: int = 100
    ) -> List[ChatMessage]:
        """Get all messages for a conversation session."""
        return (
            self.db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def add_message(
        self, session_id: str, role: str, content: str, metadata: dict = None
    ) -> ChatMessage:
        """Add a message to a conversation."""
        message_data = {
            "type": role,
            "content": content,
            "additional_kwargs": metadata or {},
        }
        message = ChatMessage(
            session_id=session_id,
            message=message_data,
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message
