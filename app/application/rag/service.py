"""
RAG service for document retrieval.
"""
from typing import List, Dict, Any, Optional
from app.infrastructure.langchain.vectorstore import get_vector_store_service
from app.config import get_logger

logger = get_logger(__name__)


class RAGService:
    """Service for RAG document retrieval"""

    def __init__(self):
        """Initialize the RAG service"""
        self.vector_store = get_vector_store_service()
        logger.info("Initialized RAGService")

    async def query_documents(
        self,
        query: str,
        top_k: int = 5,
        similarity_threshold: float = 0.7
    ) -> Dict[str, Any]:
        """
        Query documents from the vector store

        Args:
            query: Query text
            top_k: Number of results to return
            similarity_threshold: Minimum similarity score

        Returns:
            Dictionary with success status and results
        """
        try:
            search_results = await self.vector_store.search(
                query=query,
                top_k=top_k,
                similarity_threshold=similarity_threshold
            )

            results = []
            for result in search_results:
                results.append({
                    "text": result.document.page_content,
                    "score": result.score,
                    "metadata": result.document.metadata
                })

            return {
                "success": True,
                "results": results
            }

        except Exception as e:
            logger.error(f"Failed to query documents: {str(e)}")
            return {
                "success": False,
                "message": str(e),
                "results": []
            }


# Global RAG service instance
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """Get the global RAG service instance"""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
