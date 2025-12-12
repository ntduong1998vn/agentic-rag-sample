"""
V2 Conversation and chat API endpoints.

Uses the new LangGraph RAG Agent with:
- Simple questions: embedded ReAct agent with tools
- Complex questions: multi-step planning workflow
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.conversation import (
    ChatRequest,
    ChatResponse,
    SourceDocument,
)
from app.services.conversation import ConversationService
from app.models.knowledge_base import KnowledgeBase
from app.agents.workflows.rag_agent import create_rag_agent, run_rag_agent
from app.db.checkpointer import get_checkpointer

router = APIRouter()

# ============================================================================
# V2 Chat Endpoint (New LangGraph RAG Agent)
# ============================================================================


@router.post("/conversations/{conversation_id}/chat", response_model=ChatResponse)
async def chat(
    conversation_id: UUID,
    chat_request: ChatRequest,
    db: Session = Depends(get_db),
) -> ChatResponse:
    """
    V2 Chat endpoint using the new LangGraph RAG Agent.

    This endpoint uses the refactored rag_agent with:
    - Simple questions: embedded ReAct agent with tools (search, check, summarize)
    - Complex questions: multi-step planning workflow with refinement

    The agent automatically classifies questions and routes them to the
    appropriate handler.
    """
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

    # Save user message
    conversation_service.add_message(
        session_id=conversation.session_id,
        role="human",
        content=chat_request.message,
    )

    # Create and run new LangGraph rag_agent with checkpointer
    async with get_checkpointer() as checkpointer:
        agent = create_rag_agent(
            chatbot_id=conversation.chatbot_id,
            collection_name=knowledge_base.collection_name,
            conversation_id=conversation_id,
            checkpointer=checkpointer,
        )
        response_text, sources = await run_rag_agent(
            agent=agent,
            question=chat_request.message,
            thread_id=conversation.thread_id,
        )

    # Save AI response
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
