from typing import List, Dict, Any, Optional
from datetime import datetime

# Local imports
from app.rag.embeddings import get_embedding_service, EmbeddingService
from app.rag.vector_store import get_vector_store_service, VectorStoreService
from app.rag.ingestion import get_ingestion_service, DocumentIngestionService
from app.dto.ingestion import DocumentInfo, IngestionStatus, IngestionResponse, DocumentListResponse
from app.config.logging_config import get_logger

# Configure logging
logger = get_logger(__name__)


class RAGService:
    """
    Main RAG service that provides a unified interface for all RAG operations
    """

    def __init__(self):
        """
        Initialize the RAG service
        """
        self.embedding_service = get_embedding_service()
        self.vector_store_service = get_vector_store_service()
        self.ingestion_service = get_ingestion_service()
        logger.info("Initialized RAGService")

    
    async def ingest_documents(self, recursive: bool = True) -> Dict[str, Any]:
        """
        Ingest documents from the data directory

        Args:
            recursive: Whether to search subdirectories recursively

        Returns:
            Dictionary with ingestion results
        """
        try:
            logger.info("Starting business layer ingestion process")

            # Call the core ingestion service
            ingestion_result = await self.ingestion_service.ingest_directory(recursive=recursive)

            if not ingestion_result["success"]:
                response = IngestionResponse(
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
                return response.dict()

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

            response = IngestionResponse(
                success=True,
                message=ingestion_result["message"],
                status=status,
                documents=documents
            )
            return response.dict()

        except Exception as e:
            logger.error(f"Business layer ingestion failed: {str(e)}")
            response = IngestionResponse(
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
            return response.dict()

    async def query_documents(self,
                             query: str,
                             top_k: int = 5,
                             similarity_threshold: float = 0.7) -> Dict[str, Any]:
        """
        Query documents for relevant content

        Args:
            query: Query text
            top_k: Number of results to return
            similarity_threshold: Minimum similarity score

        Returns:
            Dictionary with query results
        """
        try:
            logger.info(f"Querying documents with: {query}")

            if not query.strip():
                return {
                    "success": False,
                    "message": "Query cannot be empty",
                    "results": []
                }

            # Search for similar documents
            results = await self.vector_store_service.search(
                query=query,
                top_k=top_k,
                similarity_threshold=similarity_threshold
            )

            # Convert results to a more API-friendly format
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "text": result.document.page_content,
                    "score": result.score,
                    "metadata": result.document.metadata or {}
                })

            return {
                "success": True,
                "query": query,
                "results": formatted_results,
                "total_results": len(formatted_results),
                "top_k": top_k,
                "similarity_threshold": similarity_threshold
            }

        except Exception as e:
            logger.error(f"RAG query failed: {str(e)}")
            return {
                "success": False,
                "message": f"Query failed: {str(e)}",
                "results": []
            }

    async def get_document_list(self) -> Dict[str, Any]:
        """
        Get list of processed documents

        Returns:
            Dictionary with document list
        """
        try:
            logger.info("Retrieving processed documents list")

            # Get vector store statistics
            vector_stats = self.vector_store_service.get_stats()

            # For now, we'll extract document info from the vector store metadata
            # In a more complete implementation, you might have a separate document registry
            documents = []
            total_documents = vector_stats.get("document_count", 0)

            if total_documents > 0:
                # Get detailed information from vector store
                # Note: This is a simplified implementation
                # In production, you'd want to maintain a separate document registry

                # Since we don't have direct access to document metadata through the current interface,
                # we'll create a placeholder response with the available stats
                message = f"Found {total_documents} document chunks in the vector store"
            else:
                message = "No documents found in the vector store"

            response = DocumentListResponse(
                success=True,
                message=message,
                total_documents=total_documents,
                documents=documents  # Would populate with actual document info in complete implementation
            )
            return response.dict()

        except Exception as e:
            logger.error(f"Failed to retrieve processed documents: {str(e)}")
            response = DocumentListResponse(
                success=False,
                message=f"Failed to retrieve documents: {str(e)}",
                total_documents=0,
                documents=[]
            )
            return response.dict()

    

    def clear_all_documents(self) -> Dict[str, Any]:
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

    

# Global RAG service instance
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """
    Get the global RAG service instance

    Returns:
        RAGService instance
    """
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
