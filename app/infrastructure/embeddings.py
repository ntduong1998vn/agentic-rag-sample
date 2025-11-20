"""
Embeddings service for generating text embeddings using Voyage AI.
"""
from typing import List, Optional
import voyageai
from app.config import settings, get_logger

logger = get_logger(__name__)


class EmbeddingService:
    """Service for generating embeddings using Voyage AI"""

    def __init__(self):
        """Initialize the embedding service"""
        self.client = voyageai.Client(api_key=settings.voyage_api_key)
        self.model = "voyage-3"
        self.dimension = 1024
        logger.info(f"Initialized EmbeddingService with model: {self.model}")

    async def get_embedding(self, text: str) -> List[float]:
        """
        Get embedding for a single text

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        result = self.client.embed([text], model=self.model)
        return result.embeddings[0]

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Get embeddings for multiple texts

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        result = self.client.embed(texts, model=self.model)
        return result.embeddings

    def get_embedding_dimension(self) -> int:
        """Get the dimension of the embedding vectors"""
        return self.dimension


# Global embedding service instance
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get the global embedding service instance"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
