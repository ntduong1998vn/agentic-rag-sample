"""
Conversation and chat API endpoints.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.conversation import (
    Conversation,
    ConversationCreate,
    ConversationUpdate,
    ChatRequest,
    ChatResponse,
    ChatMessage as ChatMessageSchema,
    SourceDocument,
)
from app.services.conversation import ConversationService
from app.services.chatbot import ChatbotService
from app.models.knowledge_base import KnowledgeBase
from app.agents.rag_agent import create_rag_agent, run_agent
from app.db.checkpointer import get_checkpointer

router = APIRouter()


# ============================================================================
# Conversation CRUD Endpoints
# ============================================================================


@router.post("/{chatbot_id}/conversations", response_model=Conversation)
def create_conversation(
    chatbot_id: UUID,
    conversation_in: ConversationCreate,
    db: Session = Depends(get_db),
) -> Conversation:
    """Create a new conversation for a chatbot."""
    # Verify chatbot exists
    chatbot_service = ChatbotService(db)
    chatbot = chatbot_service.get_chatbot(chatbot_id)
    if not chatbot:
        raise HTTPException(status_code=404, detail="Chatbot not found")

    conversation_service = ConversationService(db)
    return conversation_service.create_conversation(chatbot_id, conversation_in)


@router.get("/{chatbot_id}/conversations", response_model=List[Conversation])
def list_conversations(
    chatbot_id: UUID,
    user_id: Optional[UUID] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> List[Conversation]:
    """List all conversations for a chatbot."""
    conversation_service = ConversationService(db)
    return conversation_service.get_conversations(
        chatbot_id=chatbot_id,
        user_id=user_id,
        skip=skip,
        limit=limit,
    )


@router.get("/conversations/{conversation_id}", response_model=Conversation)
def get_conversation(
    conversation_id: UUID,
    db: Session = Depends(get_db),
) -> Conversation:
    """Get a specific conversation."""
    conversation_service = ConversationService(db)
    conversation = conversation_service.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.put("/conversations/{conversation_id}", response_model=Conversation)
def update_conversation(
    conversation_id: UUID,
    conversation_in: ConversationUpdate,
    db: Session = Depends(get_db),
) -> Conversation:
    """Update a conversation."""
    conversation_service = ConversationService(db)
    conversation = conversation_service.update_conversation(
        conversation_id, conversation_in
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.delete("/conversations/{conversation_id}", response_model=Conversation)
def delete_conversation(
    conversation_id: UUID,
    db: Session = Depends(get_db),
) -> Conversation:
    """Delete a conversation."""
    conversation_service = ConversationService(db)
    conversation = conversation_service.delete_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


# ============================================================================
# Chat Endpoints
# ============================================================================


@router.post("/conversations/{conversation_id}/chat", response_model=ChatResponse)
async def chat(
    conversation_id: UUID,
    chat_request: ChatRequest,
    db: Session = Depends(get_db),
) -> ChatResponse:
    """Send a message and get a response from the chatbot."""
    conversation_service = ConversationService(db)
    conversation = conversation_service.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Get chatbot's knowledge base
    knowledge_base = (
        db.query(KnowledgeBase)
        .filter(KnowledgeBase.chatbot_id == conversation.chatbot_id)
        .first()
    )

    if not knowledge_base:
        raise HTTPException(
            status_code=400,
            detail="Chatbot has no knowledge base configured",
        )

    # Save user message (for explicit message history API)
    conversation_service.add_message(
        session_id=conversation.session_id,
        role="human",
        content=chat_request.message,
    )

    # Create and run agent with PostgresSaver checkpointer
    # History is automatically loaded/saved by LangGraph via thread_id
    async with get_checkpointer() as checkpointer:
        agent = create_rag_agent(
            collection_name=knowledge_base.collection_name,
            chatbot_id=conversation.chatbot_id,
            conversation_id=conversation_id,
            checkpointer=checkpointer,
        )
        response_text, sources = await run_agent(
            agent=agent,
            message=chat_request.message,
            thread_id=conversation.thread_id,
        )

    # Save AI response (for explicit message history API)
    conversation_service.add_message(
        session_id=conversation.session_id,
        role="ai",
        content=response_text,
    )

    return ChatResponse(
        response=response_text,
        conversation_id=conversation_id,
        sources=[
            SourceDocument(content=s.get("content", ""), metadata=s.get("metadata", {}))
            for s in sources
        ],
    )


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=List[ChatMessageSchema],
)
def get_messages(
    conversation_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> List[ChatMessageSchema]:
    """Get message history for a conversation."""
    conversation_service = ConversationService(db)
    conversation = conversation_service.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return conversation_service.get_messages(
        session_id=conversation.session_id,
        skip=skip,
        limit=limit,
    )
