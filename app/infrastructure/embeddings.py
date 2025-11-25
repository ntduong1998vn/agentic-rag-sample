"""
Embeddings service for generating text embeddings using Google Gemini.
"""
from typing import List, Optional
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from app.config import settings, get_logger

logger = get_logger(__name__)


class EmbeddingService:
    """Service for generating embeddings using Google Gemini"""

    def __init__(self):
        """Initialize the embedding service"""
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            google_api_key=settings.google_api_key,
            task_type="retrieval_document"
        )
        self.dimension = 1536

    def _pad_embedding(self, embedding: List[float]) -> List[float]:
        """Pad embedding vector to 1536 dimensions with zeros"""
        if len(embedding) >= self.dimension:
            return embedding[:self.dimension]
        return embedding + [0.0] * (self.dimension - len(embedding))

    async def get_embedding(self, text: str) -> List[float]:
        """
        Get embedding for a single text

        Args:
            text: Text to embed

        Returns:
            1536-dimensional embedding vector (768D embedding padded with zeros)
        """
        embedding = await self.embeddings.aembed_query(text)
        return self._pad_embedding(embedding)

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Get embeddings for multiple texts

        Args:
            texts: List of texts to embed

        Returns:
            List of 1536-dimensional embedding vectors (768D embeddings padded with zeros)
        """
        embeddings = await self.embeddings.aembed_documents(texts)
        return [self._pad_embedding(emb) for emb in embeddings]

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
