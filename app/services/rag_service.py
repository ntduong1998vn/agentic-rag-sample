import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

# Local imports
from app.rag.embeddings import get_embedding_service, EmbeddingService
from app.rag.vector_store import get_vector_store_service, VectorStoreService
from app.rag.ingestion import get_ingestion_service, DocumentIngestionService
from app.services.ingestion_service import get_ingestion_business_service, IngestionBusinessService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
        self.ingestion_business_service = get_ingestion_business_service()
        logger.info("Initialized RAGService")

    async def initialize(self) -> bool:
        """
        Initialize all RAG components

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            logger.info("Initializing RAG service components")

            # Test embedding service
            embedding_test = self.embedding_service.test_connection()
            if not embedding_test:
                logger.error("Embedding service test failed")
                return False

            # Initialize vector store (this will load or create index)
            vector_store = self.vector_store_service.get_vector_store()

            # Get initial statistics
            stats = self.vector_store_service.get_stats()
            logger.info(f"RAG service initialized. Vector store stats: {stats}")

            return True

        except Exception as e:
            logger.error(f"Failed to initialize RAG service: {str(e)}")
            return False

    async def ingest_documents(self, recursive: bool = True) -> Dict[str, Any]:
        """
        Ingest documents from the data directory

        Args:
            recursive: Whether to search subdirectories recursively

        Returns:
            Dictionary with ingestion results
        """
        try:
            logger.info("Starting document ingestion through RAG service")

            result = await self.ingestion_business_service.ingest_data_directory(recursive=recursive)

            return result.dict()

        except Exception as e:
            logger.error(f"RAG service ingestion failed: {str(e)}")
            return {
                "success": False,
                "message": f"RAG ingestion failed: {str(e)}",
                "error": str(e)
            }

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
                    "text": result.node.text,
                    "score": result.score,
                    "metadata": result.node.metadata or {}
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
            logger.info("Retrieving document list through RAG service")

            result = await self.ingestion_business_service.get_processed_documents()

            return result.dict()

        except Exception as e:
            logger.error(f"Failed to get document list: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to get document list: {str(e)}",
                "total_documents": 0,
                "documents": []
            }

    def get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status

        Returns:
            Dictionary with system status
        """
        try:
            logger.info("Getting RAG system status")

            # Get ingestion business service status
            ingestion_status = self.ingestion_business_service.get_system_status()

            # Get vector store statistics
            vector_stats = self.vector_store_service.get_stats()

            # Get supported file types
            supported_types = self.ingestion_service.get_supported_file_types()

            return {
                "success": True,
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "components": {
                    "embedding_service": {
                        "status": "healthy" if self.embedding_service.test_connection() else "unhealthy",
                        "model": self.embedding_service.model_name,
                        "dimension": self.embedding_service.get_embedding_dimension()
                    },
                    "vector_store": {
                        "status": "healthy",
                        "stats": vector_stats
                    },
                    "ingestion_service": {
                        "status": "healthy",
                        "supported_file_types": supported_types
                    }
                },
                "overall_status": ingestion_status.get("status", "unknown")
            }

        except Exception as e:
            logger.error(f"Failed to get system status: {str(e)}")
            return {
                "success": False,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def clear_all_documents(self) -> Dict[str, Any]:
        """
        Clear all documents from the vector store

        Returns:
            Dictionary with operation results
        """
        try:
            logger.info("Clearing all documents through RAG service")

            result = self.ingestion_business_service.clear_vector_store()

            return result

        except Exception as e:
            logger.error(f"Failed to clear documents: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to clear documents: {str(e)}"
            }

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a comprehensive health check

        Returns:
            Dictionary with health check results
        """
        try:
            logger.info("Performing RAG service health check")

            health_status = {
                "success": True,
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "checks": {}
            }

            # Check embedding service
            embedding_healthy = self.embedding_service.test_connection()
            health_status["checks"]["embedding_service"] = {
                "status": "healthy" if embedding_healthy else "unhealthy",
                "details": "Voyage AI connection test" + (" passed" if embedding_healthy else " failed")
            }

            # Check vector store
            try:
                vector_stats = self.vector_store_service.get_stats()
                health_status["checks"]["vector_store"] = {
                    "status": "healthy",
                    "details": f"Vector store accessible with {vector_stats['total_documents']} documents"
                }
            except Exception as e:
                health_status["checks"]["vector_store"] = {
                    "status": "unhealthy",
                    "details": f"Vector store error: {str(e)}"
                }

            # Check data directory
            try:
                data_path = self.ingestion_service.data_path
                if data_path.exists():
                    health_status["checks"]["data_directory"] = {
                        "status": "healthy",
                        "details": f"Data directory accessible: {data_path}"
                    }
                else:
                    health_status["checks"]["data_directory"] = {
                        "status": "warning",
                        "details": f"Data directory does not exist: {data_path}"
                    }
            except Exception as e:
                health_status["checks"]["data_directory"] = {
                    "status": "unhealthy",
                    "details": f"Data directory error: {str(e)}"
                }

            # Overall status
            all_healthy = all(
                check["status"] == "healthy"
                for check in health_status["checks"].values()
            )
            health_status["status"] = "healthy" if all_healthy else "degraded"

            return health_status

        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                "success": False,
                "status": "error",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
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


async def initialize_rag_service() -> bool:
    """
    Initialize the global RAG service

    Returns:
        True if initialization successful, False otherwise
    """
    try:
        service = get_rag_service()
        return await service.initialize()
    except Exception as e:
        logger.error(f"Failed to initialize global RAG service: {str(e)}")
        return False