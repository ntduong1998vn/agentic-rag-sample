"""
GitLab code ingestion API router.

This module provides API endpoints for:
- Ingesting GitLab repositories
- Searching code
- Managing ingested code
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks, Depends
from pydantic import BaseModel, Field

# Local imports
from app.services.gitlab_service import get_gitlab_rag_service, GitLabRAGService
from app.dto.code_ingestion import (
    GitLabIngestionRequest,
    GitLabIngestionResponse,
    RepositoryStatsResponse,
    CodeQueryRequest,
    CodeSearchResponse,
    FileListResponse,
    ClearCodeRequest,
    ClearCodeResponse,
    HealthCheckResponse,
    RepositoryInfo,
    FileInfo,
    IngestionStatus,
)
from app.config.logging_config import get_logger

# Configure logging
logger = get_logger(__name__)

# Create FastAPI router
router = APIRouter(prefix="/code", tags=["GitLab Code"])


# Pydantic models for API requests and query parameters
class IngestionQueryParams(BaseModel):
    """Query parameters for ingestion endpoint"""
    ref: str = Field(
        default="main",
        description="Branch name, commit SHA, or tag to ingest from"
    )


class SearchQueryParams(BaseModel):
    """Query parameters for search endpoint"""
    query: str = Field(..., description="Search query")
    top_k: int = Field(default=10, ge=1, le=100, description="Number of results")
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    language: Optional[str] = Field(default=None, description="Filter by language")
    file_path: Optional[str] = Field(default=None, description="Filter by file path")
    chunk_type: Optional[str] = Field(default=None, description="Filter by chunk type")


def get_service() -> GitLabRAGService:
    """Dependency injection for GitLab RAG service"""
    return get_gitlab_rag_service()


@router.post(
    "/ingest",
    response_model=GitLabIngestionResponse,
    summary="Ingest GitLab repository",
    description="""
    Ingest an entire GitLab repository into the RAG system.

    This endpoint will:
    - Fetch all code files from the GitLab repository
    - Parse files using tree-sitter AST parser
    - Extract structured chunks (file, class, function levels)
    - Generate embeddings using Voyage AI
    - Store in ChromaDB vector storage

    Supported languages: Python, JavaScript, TypeScript, PHP

    Note: This is a synchronous operation that may take time for large repositories.
    Use the status endpoint to check progress for future async implementation.
    """
)
async def ingest_repository(
    ref: str = Query(default="main", description="Branch name, commit SHA, or tag"),
    service: GitLabRAGService = Depends(get_service)
):
    """Ingest GitLab repository"""
    try:
        logger.info(f"Received ingestion request for ref: {ref}")

        # Validate setup first
        is_valid, message = service.validate_setup()
        if not is_valid:
            raise HTTPException(status_code=400, detail=message)

        # Start ingestion
        result = await service.ingest_repository(ref=ref)

        if result["success"]:
            return GitLabIngestionResponse(
                success=result["success"],
                message=result["message"],
                status=IngestionStatus(**result["stats"]),
                repository_info=RepositoryInfo(**result.get("repository_info", {})),
                files=[]  # Would populate with detailed file info in complete implementation
            )
        else:
            raise HTTPException(status_code=500, detail=result["message"])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ingestion endpoint error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during ingestion: {str(e)}"
        )


@router.get(
    "/stats",
    response_model=RepositoryStatsResponse,
    summary="Get repository statistics",
    description="""
    Get detailed statistics about ingested GitLab repository.

    Returns information about:
    - Total number of ingested chunks
    - File and line counts
    - Language distribution
    - Chunk type breakdown
    - Repository information
    - Last ingestion time
    """
)
def get_repository_stats(
    service: GitLabRAGService = Depends(get_service)
):
    """Get repository statistics"""
    try:
        logger.info("Received request for repository statistics")

        # Get repository stats
        stats = service.get_repository_stats()

        if "error" in stats:
            raise HTTPException(status_code=500, detail=stats["error"])

        # Build response
        return RepositoryStatsResponse(
            success=True,
            message="Repository statistics retrieved successfully",
            stats=stats  # Would use actual model in complete implementation
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Repository stats endpoint error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.post(
    "/search",
    response_model=CodeSearchResponse,
    summary="Search code",
    description="""
    Search for relevant code snippets in the ingested repository.

    Performs semantic search using:
    - Voyage AI embeddings
    - ChromaDB vector similarity search
    - Metadata filtering

    Supports filtering by:
    - Programming language (python, javascript, typescript, php)
    - File path pattern (e.g., "src/auth/*.py")
    - Chunk type (file, class, function, method)

    Returns code snippets with rich metadata:
    - Code text and similarity score
    - File path and line numbers
    - Function/class signatures
    - Docstrings and documentation
    - Parent class hierarchy
    """
)
async def search_code(
    request: CodeQueryRequest,
    service: GitLabRAGService = Depends(get_service)
):
    """Search code in repository"""
    try:
        logger.info(f"Received code search request: '{request.query}'")

        if not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")

        # Perform search
        result = await service.search_code(
            query=request.query,
            top_k=request.top_k,
            similarity_threshold=request.similarity_threshold,
            language=request.language,
            file_path=request.file_path,
            chunk_type=request.chunk_type
        )

        if result["success"]:
            # Map results to response model
            search_results = [
                CodeSearchResult(**r) for r in result["results"]
            ]

            return CodeSearchResponse(
                success=result["success"],
                message=result["message"],
                results=search_results,
                total_results=result["total_results"],
                query=result["query"],
                top_k=result["top_k"],
                similarity_threshold=result["similarity_threshold"],
                filters=result["filters"]
            )
        else:
            raise HTTPException(status_code=500, detail=result["message"])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Code search endpoint error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during search: {str(e)}"
        )


@router.get(
    "/files",
    response_model=FileListResponse,
    summary="List ingested files",
    description="""
    List all code files that have been ingested into the RAG system.

    Returns metadata about each file:
    - File path and name
    - Programming language
    - File size
    - Number of chunks created
    - Last commit information

    Supports filtering by language and pagination.
    """
)
def list_files(
    language: Optional[str] = Query(default=None, description="Filter by language"),
    page: int = Query(default=1, ge=1, description="Page number"),
    limit: int = Query(default=50, ge=1, le=500, description="Items per page"),
    service: GitLabRAGService = Depends(get_service)
):
    """List ingested files"""
    try:
        logger.info("Received request for ingested files list")

        result = service.list_ingested_files()

        if result["success"]:
            # Apply language filter
            files = result["files"]
            if language:
                files = [f for f in files if f.get("language") == language]

            # Apply pagination
            start = (page - 1) * limit
            end = start + limit
            paginated_files = files[start:end]

            # Convert to FileInfo models
            file_infos = [FileInfo(**f) for f in paginated_files]

            return FileListResponse(
                success=result["success"],
                message=result["message"],
                files=file_infos,
                total_files=len(files)
            )
        else:
            raise HTTPException(status_code=500, detail=result["message"])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File list endpoint error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.delete(
    "/clear",
    response_model=ClearCodeResponse,
    summary="Clear all code chunks",
    description="""
    Remove all code chunks from the vector store.

    This will permanently delete all ingested code documents and chunks.
    Use with caution - code will need to be re-ingested afterward.

    Warning: This clears everything in the vector store, not just code.
    """
)
def clear_code_documents(
    confirm: bool = Query(default=False, description="Must be True to confirm deletion"),
    service: GitLabRAGService = Depends(get_service)
):
    """Clear all code documents"""
    try:
        logger.info("Received request to clear code documents")

        if not confirm:
            raise HTTPException(
                status_code=400,
                detail="Confirmation required. Set confirm=true to proceed."
            )

        result = service.clear_all_code()

        if result["success"]:
            return ClearCodeResponse(**result)
        else:
            raise HTTPException(status_code=500, detail=result["message"])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Clear code endpoint error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="GitLab health check",
    description="""
    Check GitLab connectivity and configuration status.

    Returns:
    - Whether GitLab is configured
    - Whether connection is successful
    - Whether repository access is available
    - Repository information if accessible

    Use this endpoint to verify setup before ingestion.
    """
)
def health_check(
    service: GitLabRAGService = Depends(get_service)
):
    """Check GitLab health"""
    try:
        logger.info("Received GitLab health check request")

        # Validate setup
        is_valid, message = service.validate_setup()

        if is_valid:
            # Test connection
            is_connected = service.code_ingestion_service.validate_configuration()

            # Get repository info
            repo_info = None
            try:
                repo_info = RepositoryInfo(**service.gitlab_connector.get_project_info())
            except:
                pass

            return HealthCheckResponse(
                is_configured=True,
                is_connected=is_connected[0],
                repository_access=is_connected[0],
                message=message,
                repository_info=repo_info
            )
        else:
            return HealthCheckResponse(
                is_configured=False,
                is_connected=False,
                repository_access=False,
                message=message,
                repository_info=None
            )

    except Exception as e:
        logger.error(f"Health check endpoint error: {str(e)}", exc_info=True)
        return HealthCheckResponse(
            is_configured=False,
            is_connected=False,
            repository_access=False,
            message=f"Health check failed: {str(e)}",
            repository_info=None
        )


# Additional utility endpoints

@router.get(
    "/status",
    summary="Get ingestion status (Async)",
    description="""
    Get the status of a running ingestion job.

    For future implementation of async ingestion.
    Currently returns placeholder response.
    """
)
def get_ingestion_status(job_id: str):
    """Get ingestion job status (placeholder)"""
    return {
        "job_id": job_id,
        "status": "completed",
        "message": "Ingestion completed successfully",
        "progress": 100,
        "stats": {
            "total_files": 0,
            "processed_files": 0,
            "processed_chunks": 0
        }
    }


"""
Example API Usage:

1. Health Check (verify setup):
```bash
curl http://localhost:8000/code/health
```

2. Ingest Repository:
```bash
curl -X POST "http://localhost:8000/code/ingest?ref=main"
```

3. Search Code:
```bash
curl -X POST http://localhost:8000/code/search \
  -H "Content-Type: application/json" \
  -d '{"query": "how to authenticate", "top_k": 5, "language": "python"}'
```

4. Get Statistics:
```bash
curl http://localhost:8000/code/stats
```

5. List Files:
```bash
curl "http://localhost:8000/code/files?language=python&page=1&limit=50"
```

6. Clear All Code:
```bash
curl -X DELETE "http://localhost:8000/code/clear?confirm=true"
```
"""
