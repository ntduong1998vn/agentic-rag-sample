"""
V2 Conversation and chat API endpoints.

Uses the Router Agent (Supervisor) to route questions to:
- GitLab Agent: for code-related questions
- RAG Agent: for document-related questions
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
from app.agents.router_agent import create_router_agent, run_router_agent
from app.db.checkpointer import get_checkpointer

router = APIRouter()

# ============================================================================
# V2 Chat Endpoint (Router Agent - Supervisor)
# ============================================================================


@router.post("/conversations/{conversation_id}/chat", response_model=ChatResponse)
async def chat(
    conversation_id: UUID,
    chat_request: ChatRequest,
    db: Session = Depends(get_db),
) -> ChatResponse:
    """
    V2 Chat endpoint using the Router Agent (Supervisor).

    The Router Agent analyzes user questions and routes them to the
    appropriate specialized agent:
    - GitLab Agent: for code, repository, and technical documentation questions
    - RAG Agent: for general documents and knowledge base questions

    The selected agent handles the question and returns the response.
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

    # Create and run Router Agent (Supervisor) with checkpointer
    async with get_checkpointer() as checkpointer:
        agent = create_router_agent(
            chatbot_id=conversation.chatbot_id,
            collection_name=knowledge_base.collection_name,
            conversation_id=conversation_id,
            gitlab_collection_name=None,  # Uses same collection as RAG for now
            checkpointer=checkpointer,
        )
        response_text, selected_agent, sources = await run_router_agent(
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
