from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks, Depends
from pydantic import BaseModel, Field

# Local imports
from app.infrastructure.langchain.ingestion import get_ingestion_service, get_code_ingestion_service
from app.infrastructure.langchain.vectorstore import get_vector_store_service
from app.config import get_logger

# Configure logging
logger = get_logger(__name__)

# Create FastAPI router
router = APIRouter(prefix="/files", tags=["files"])

# Pydantic models for API requests
class IngestionRequest(BaseModel):
    """Request model for document ingestion"""
    recursive: Optional[bool] = Field(
        default=True,
        description="Whether to search subdirectories recursively"
    )

class IngestionResponse(BaseModel):
    success: bool
    message: str
    stats: dict
    processing_results: Optional[List[dict]] = None

@router.post("/ingest", response_model=IngestionResponse, summary="Ingest documents from data folder")
async def ingest_documents(
    request: IngestionRequest,
    background_tasks: BackgroundTasks
):
    """
    Process all files in the /data directory and add them to the RAG system.
    """
    try:
        logger.info(f"Received ingestion request with recursive={request.recursive}")

        # Get ingestion service
        ingestion_service = get_ingestion_service()

        # Start ingestion
        result = await ingestion_service.ingest_directory(recursive=request.recursive)

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

@router.delete("/clear", summary="Clear all documents from vector store")
async def clear_documents():
    """
    Remove all documents from the vector store.
    """
    try:
        logger.info("Received request to clear all documents")

        # Get vector store service
        vector_store = get_vector_store_service()

        # Clear documents
        vector_store.clear_index()

        return {"success": True, "message": "All documents cleared"}

    except Exception as e:
        logger.error(f"Clear documents endpoint error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while clearing documents: {str(e)}"
        )

@router.get("/stats", summary="Get detailed vector store statistics")
async def get_vector_store_stats():
    """
    Get detailed statistics about the vector store.
    """
    try:
        logger.info("Received request for vector store statistics")

        # Get vector store service
        vector_store = get_vector_store_service()
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

# Code Ingestion Endpoints

@router.post("/code/ingest", summary="Ingest GitLab repository")
async def ingest_repository(
    ref: str = Query(default="main", description="Branch name, commit SHA, or tag")
):
    """Ingest GitLab repository"""
    try:
        logger.info(f"Received ingestion request for ref: {ref}")
        
        service = get_code_ingestion_service()
        
        # Validate setup first
        is_valid, message = service.validate_configuration()
        if not is_valid:
            raise HTTPException(status_code=400, detail=message)

        # Start ingestion
        result = await service.ingest_repository(ref=ref)

        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["message"])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ingestion endpoint error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during ingestion: {str(e)}"
        )
