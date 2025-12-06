"""
Ingestion API endpoints.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.ingestion import IngestionRequest, IngestionResponse
from app.services.chatbot import ChatbotService
from app.services.ingestion import IngestionService
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.post("/{chatbot_id}/ingest", response_model=IngestionResponse)
def ingest_documents(
    chatbot_id: UUID,
    request: IngestionRequest = IngestionRequest(),
    db: Session = Depends(get_db),
) -> IngestionResponse:
    """
    Ingest documents from a folder into the chatbot's knowledge base.
    
    This endpoint performs two main steps:
    1. Check/create knowledge base for the chatbot, scan folder, and register documents in DB
    2. Process pending documents (chunk → embed → store vectors in Qdrant)
    
    Args:
        chatbot_id: ID of the chatbot to ingest documents for
        request: Optional request body with folder_path (defaults to "./data")
        
    Returns:
        IngestionResponse with status, counts, and any errors
    """
    logger.info(f"Ingestion request for chatbot {chatbot_id} from folder {request.folder_path}")
    
    # Verify chatbot exists
    chatbot_service = ChatbotService(db)
    chatbot = chatbot_service.get_chatbot(chatbot_id)
    if not chatbot:
        raise HTTPException(status_code=404, detail="Chatbot not found")
    
    # Run ingestion
    ingestion_service = IngestionService(db)
    result = ingestion_service.ingest_for_chatbot(chatbot_id, request.folder_path)
    
    return IngestionResponse(
        status=result.status,
        documents_registered=result.documents_registered,
        documents_processed=result.documents_processed,
        errors=result.errors,
    )
