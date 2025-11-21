"""
Knowledge Base API routes.

This module defines the API endpoints for knowledge base management and document ingestion.
"""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.database import get_db
from app.infrastructure.database.repositories.chatbot_repository import SQLAlchemyChatbotRepository
from app.infrastructure.database.repositories.knowledge_base_repository import SQLAlchemyKnowledgeBaseRepository
from app.infrastructure.database.repositories.document_repository import SQLAlchemyDocumentRepository, SQLAlchemyDocumentChunkRepository
from app.infrastructure.document_scanner import DocumentScanner
from app.infrastructure.document_processor import DocumentProcessor
from app.infrastructure.provider.vector_database_provider import get_vector_database
from app.application.knowledge_base.service import KnowledgeBaseService
from app.domain.knowledge_base.entities import DocumentStatus
from app.domain.knowledge_base.ports import VectorStorePort
from app.api.schemas.knowledge_base import (
    IngestRequest,
    IngestResponse,
    DocumentResponse,
    KnowledgeBaseStats
)

router = APIRouter(prefix="/chatbots/{chatbot_id}/knowledge-base", tags=["knowledge-base"])


# --- Dependencies ---

async def get_knowledge_base_service(
    db: AsyncSession = Depends(get_db),
    vector_store: VectorStorePort = Depends(get_vector_database)
) -> KnowledgeBaseService:
    """Dependency to get KnowledgeBaseService instance."""
    kb_repo = SQLAlchemyKnowledgeBaseRepository(db)
    doc_repo = SQLAlchemyDocumentRepository(db)
    chunk_repo = SQLAlchemyDocumentChunkRepository(db)
    chatbot_repo = SQLAlchemyChatbotRepository(db)
    
    scanner = DocumentScanner()
    processor = DocumentProcessor(vector_store=vector_store)
    
    return KnowledgeBaseService(
        kb_repository=kb_repo,
        doc_repository=doc_repo,
        chunk_repository=chunk_repo,
        chatbot_repository=chatbot_repo,
        vector_store=vector_store,
        document_scanner=scanner,
        document_processor=processor
    )


# --- Routes ---

@router.post("/ingest", response_model=IngestResponse)
async def ingest_documents(
    chatbot_id: uuid.UUID,
    request: IngestRequest,
    service: KnowledgeBaseService = Depends(get_knowledge_base_service)
):
    """
    Ingest documents from a folder into the chatbot's knowledge base.
    
    Scans the folder, registers documents, chunks them, generates embeddings,
    and stores them in the chatbot's dedicated Qdrant collection.
    """
    try:
        result = await service.ingest_documents(chatbot_id, request.folder_path)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/documents", response_model=List[DocumentResponse])
async def list_documents(
    chatbot_id: uuid.UUID,
    status: Optional[DocumentStatus] = None,
    skip: int = 0,
    limit: int = 100,
    service: KnowledgeBaseService = Depends(get_knowledge_base_service)
):
    """List documents in the chatbot's knowledge base."""
    status_str = status.value if status else None
    return await service.list_documents(chatbot_id, status_str, skip, limit)


@router.get("/stats", response_model=KnowledgeBaseStats)
async def get_stats(
    chatbot_id: uuid.UUID,
    service: KnowledgeBaseService = Depends(get_knowledge_base_service)
):
    """Get statistics for the chatbot's knowledge base."""
    stats = await service.get_stats(chatbot_id)
    if stats.get("status") == "not_found":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge base not found")
    return stats
