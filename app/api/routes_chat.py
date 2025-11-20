from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

# Local imports
from app.infrastructure.langchain.chat_service import get_chatbot_service
from app.domain.chat.models import ChatRequest, ChatResponse
from app.config import get_logger

# Configure logging
logger = get_logger(__name__)

# Create FastAPI router
router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse, summary="Chat with documents")
async def chat_with_documents(
    request: ChatRequest,
    stream: Optional[bool] = Query(False, description="Enable streaming response")
):
    """
    Chat with your documents using RAG + LLM.

    This endpoint combines document retrieval with AI-powered conversation:
    - Retrieves relevant document chunks using semantic search
    - Generates contextual responses using Google Gemini 2.5 Flash-Lite
    - Supports streaming responses for better user experience

    **Features:**
    - Japanese and English language support
    - Source document attribution
    - Configurable retrieval parameters
    - Stateless processing (each query is independent)

    **Usage:**
    - Send a question to get AI-powered answers based on your documents
    - Set stream=true for real-time response streaming
    - Adjust top_k and similarity_threshold for retrieval tuning
    """
    try:
        logger.info(f"Received chat request: {request.query[:100]}...")

        # Get chatbot service
        chatbot_service = get_chatbot_service()

        # Handle streaming vs non-streaming
        if request.stream or stream:
            return StreamingResponse(
                chatbot_service.chat_stream(request),
                media_type="text/plain",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"  # Disable nginx buffering
                }
            )
        else:
            # Non-streaming response
            response = await chatbot_service.chat(request)
            return response

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing your request: {str(e)}"
        )
