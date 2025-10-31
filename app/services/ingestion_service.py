import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

# Local imports
from app.rag.ingestion import get_ingestion_service, DocumentIngestionService
from app.rag.vector_store import get_vector_store_service, VectorStoreService
from app.dto.ingestion import DocumentInfo, IngestionStatus, IngestionResponse, DocumentListResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IngestionBusinessService:
    """
    Business logic service for document ingestion operations
    """

    def __init__(self):
        """
        Initialize the ingestion business service
        """
        self.ingestion_service = get_ingestion_service()
        self.vector_store_service = get_vector_store_service()
        logger.info("Initialized IngestionBusinessService")

    async def ingest_data_directory(self, recursive: bool = True) -> IngestionResponse:
        """
        Ingest all documents from the data directory

        Args:
            recursive: Whether to search subdirectories recursively

        Returns:
            IngestionResponse with processing results
        """
        try:
            logger.info("Starting business layer ingestion process")

            # Call the core ingestion service
            ingestion_result = await self.ingestion_service.ingest_directory(recursive=recursive)

            if not ingestion_result["success"]:
                return IngestionResponse(
                    success=False,
                    message=ingestion_result["message"],
                    status=IngestionStatus(
                        total_files=0,
                        processed_files=0,
                        failed_files=0,
                        skipped_files=0,
                        start_time=datetime.now(),
                        is_complete=True,
                        errors=[ingestion_result["message"]]
                    )
                )

            # Extract statistics
            stats = ingestion_result["stats"]
            processing_results = ingestion_result.get("processing_results", [])

            # Create ingestion status
            status = IngestionStatus(
                total_files=stats["total_files"],
                processed_files=stats["processed_files"],
                failed_files=stats["failed_files"],
                skipped_files=stats["skipped_files"],
                start_time=stats["start_time"],
                end_time=stats.get("end_time"),
                is_complete=True,
                errors=[r.get("error_message") for r in processing_results if r.get("error_message")]
            )

            # Create document info objects
            documents = []
            for result in processing_results:
                if result.get("status") == "success":
                    doc_info = DocumentInfo(
                        file_name=result.get("file_name", "unknown"),
                        file_path=result.get("file_path", "unknown"),
                        file_size=result.get("file_size", 0),
                        file_type=result.get("file_type", "unknown"),
                        page_count=result.get("page_count"),  # May not be available for all formats
                        chunk_count=result.get("chunk_count", 0),
                        processed_at=result.get("modified_at", datetime.now()),
                        status=result.get("status", "unknown"),
                        error_message=result.get("error_message")
                    )
                    documents.append(doc_info)

            return IngestionResponse(
                success=True,
                message=ingestion_result["message"],
                status=status,
                documents=documents
            )

        except Exception as e:
            logger.error(f"Business layer ingestion failed: {str(e)}")
            return IngestionResponse(
                success=False,
                message=f"Ingestion failed: {str(e)}",
                status=IngestionStatus(
                    total_files=0,
                    processed_files=0,
                    failed_files=1,
                    skipped_files=0,
                    start_time=datetime.now(),
                    is_complete=True,
                    errors=[str(e)]
                )
            )

    async def get_processed_documents(self) -> DocumentListResponse:
        """
        Get list of all processed documents

        Returns:
            DocumentListResponse with document information
        """
        try:
            logger.info("Retrieving processed documents list")

            # Get vector store statistics
            vector_stats = self.vector_store_service.get_stats()

            # For now, we'll extract document info from the vector store metadata
            # In a more complete implementation, you might have a separate document registry
            documents = []
            total_documents = vector_stats["total_documents"]

            if total_documents > 0:
                # Get detailed information from vector store
                # Note: This is a simplified implementation
                # In production, you'd want to maintain a separate document registry

                # Since we don't have direct access to document metadata through the current interface,
                # we'll create a placeholder response with the available stats
                message = f"Found {total_documents} document chunks in the vector store"
            else:
                message = "No documents found in the vector store"

            return DocumentListResponse(
                success=True,
                message=message,
                total_documents=total_documents,
                documents=documents  # Would populate with actual document info in complete implementation
            )

        except Exception as e:
            logger.error(f"Failed to retrieve processed documents: {str(e)}")
            return DocumentListResponse(
                success=False,
                message=f"Failed to retrieve documents: {str(e)}",
                total_documents=0,
                documents=[]
            )

    def get_system_status(self) -> Dict[str, Any]:
        """
        Get the status of the ingestion system

        Returns:
            Dictionary with system status information
        """
        try:
            logger.info("Retrieving system status")

            # Get vector store statistics
            vector_stats = self.vector_store_service.get_stats()

            # Get supported file types
            supported_types = self.ingestion_service.get_supported_file_types()

            return {
                "success": True,
                "status": "healthy",
                "vector_store": vector_stats,
                "supported_file_types": supported_types,
                "ingestion_service": "available",
                "embedding_service": "available"
            }

        except Exception as e:
            logger.error(f"Failed to get system status: {str(e)}")
            return {
                "success": False,
                "status": "error",
                "error": str(e)
            }

    def clear_vector_store(self) -> Dict[str, Any]:
        """
        Clear all documents from the vector store

        Returns:
            Dictionary with operation results
        """
        try:
            logger.info("Clearing vector store")

            self.vector_store_service.clear_index()

            return {
                "success": True,
                "message": "Vector store cleared successfully"
            }

        except Exception as e:
            logger.error(f"Failed to clear vector store: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to clear vector store: {str(e)}"
            }


# Global business service instance
_ingestion_business_service: Optional[IngestionBusinessService] = None


def get_ingestion_business_service() -> IngestionBusinessService:
    """
    Get the global ingestion business service instance

    Returns:
        IngestionBusinessService instance
    """
    global _ingestion_business_service
    if _ingestion_business_service is None:
        _ingestion_business_service = IngestionBusinessService()
    return _ingestion_business_service