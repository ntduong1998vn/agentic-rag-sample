"""
V2 Streaming chat API endpoint.

Uses Server-Sent Events (SSE) to stream responses from the Supervisor Agent.
Supports token streaming, tool call events, and interrupt (clarification) events.
"""

from uuid import UUID
import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.conversation import ChatRequest
from app.services.conversation import ConversationService
from app.models.knowledge_base import KnowledgeBase
from app.agents.router_agent import create_router_agent, stream_router_agent
from app.db.checkpointer import get_checkpointer
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.post("/conversations/{conversation_id}/chat/stream")
async def chat_stream(
    conversation_id: UUID,
    chat_request: ChatRequest,
    db: Session = Depends(get_db),
):
    """
    V2 Streaming Chat endpoint using Server-Sent Events (SSE).

    The Router Agent analyzes user questions and routes them to the
    appropriate specialized agent. Responses are streamed token-by-token
    for better UX.

    Event types:
    - token: A token from the LLM response
    - tool_start: A tool call has started (e.g., calling rag_agent)
    - tool_end: A tool call has completed
    - interrupt: A clarification question for the user (graph paused)
    - done: Stream completed successfully
    - error: An error occurred
    """
    # Validate conversation exists
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

    async def event_generator():
        """Generate SSE events from Router Agent streaming."""
        full_response = ""
        
        try:
            async with get_checkpointer() as checkpointer:
                agent = create_router_agent(
                    chatbot_id=conversation.chatbot_id,
                    collection_name=knowledge_base.collection_name,
                    conversation_id=conversation_id,
                    gitlab_collection_name=None,
                    checkpointer=checkpointer,
                )
                
                async for event in stream_router_agent(
                    agent=agent,
                    question=chat_request.message,
                    thread_id=conversation.thread_id,
                ):
                    # Accumulate response for saving
                    if event["type"] == "token":
                        full_response += event["content"]
                    elif event["type"] == "interrupt":
                        # Clarification question — save as AI message
                        full_response += event["content"]

                    # Yield SSE formatted event
                    yield f"data: {json.dumps(event)}\n\n"
            
            # Save AI response after streaming completes
            if full_response:
                conversation_service.add_message(
                    session_id=conversation.session_id,
                    role="ai",
                    content=full_response,
                )
                
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )
