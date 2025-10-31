import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field

# Local imports
from app.services.rag_service import get_rag_service
from app.dto.ingestion import IngestionResponse, DocumentListResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI router
router = APIRouter(prefix="/ingest", tags=["ingestion"])

# Pydantic models for API requests
class IngestionRequest(BaseModel):
    """Request model for document ingestion"""
    recursive: Optional[bool] = Field(
        default=True,
        description="Whether to search subdirectories recursively"
    )


@router.post("", response_model=IngestionResponse, summary="Ingest documents from data folder")
async def ingest_documents(
    request: IngestionRequest,
    background_tasks: BackgroundTasks
):
    """
    Process all files in the /data directory and add them to the RAG system.

    This endpoint will:
    - Scan the /data directory for supported file types
    - Process documents with Japanese semantic chunking
    - Generate embeddings using Voyage AI 3.5
    - Store chunks in FAISS vector database

    Supported file types: .pdf, .docx, .csv, .txt, .md, .html, .jpg, .png, and more
    """
    try:
        logger.info(f"Received ingestion request with recursive={request.recursive}")

        # Get RAG service
        rag_service = get_rag_service()

        # Start ingestion (you could make this a background task for long operations)
        result = await rag_service.ingest_documents(recursive=request.recursive)

        # Convert to IngestionResponse format
        if result.get("success"):
            return IngestionResponse(**result)
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get("message", "Ingestion failed")
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ingestion endpoint error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during ingestion: {str(e)}"
        )


@router.get("/documents", response_model=DocumentListResponse, summary="List processed documents")
async def get_processed_documents():
    """
    Get a list of all documents that have been processed and added to the RAG system.

    Returns metadata about processed documents including:
    - File names and paths
    - Document sizes and types
    - Processing status
    - Chunk counts
    """
    try:
        logger.info("Received request for processed documents list")

        # Get RAG service
        rag_service = get_rag_service()

        # Get document list
        result = await rag_service.get_document_list()

        # Convert to DocumentListResponse format
        if result.get("success"):
            return DocumentListResponse(**result)
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get("message", "Failed to retrieve document list")
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document list endpoint error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while retrieving documents: {str(e)}"
        )






# Additional utility endpoints

@router.delete("/clear", summary="Clear all documents from vector store")
async def clear_documents():
    """
    Remove all documents from the FAISS vector store.

    This will permanently delete all indexed documents and chunks.
    Use with caution - documents will need to be re-ingested afterward.
    """
    try:
        logger.info("Received request to clear all documents")

        # Get RAG service
        rag_service = get_rag_service()

        # Clear documents
        result = rag_service.clear_all_documents()

        if result.get("success"):
            return result
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get("message", "Failed to clear documents")
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Clear documents endpoint error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while clearing documents: {str(e)}"
        )


@router.get("/stats", summary="Get detailed vector store statistics")
async def get_vector_store_stats():
    """
    Get detailed statistics about the FAISS vector store.

    Returns information about:
    - Index type and configuration
    - Number of documents and chunks
    - Index file status
    - Storage statistics
    """
    try:
        logger.info("Received request for vector store statistics")

        # Get RAG service
        rag_service = get_rag_service()

        # Get vector store statistics
        vector_store = rag_service.vector_store_service
        stats = vector_store.get_stats()

        return {
            "success": True,
            "message": "Vector store statistics retrieved successfully",
            "stats": stats
        }

    except Exception as e:
        logger.error(f"Vector store stats endpoint error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while getting statistics: {str(e)}"
        )