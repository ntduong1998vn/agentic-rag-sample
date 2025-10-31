import os
from typing import List, Optional
from llama_index.core.embeddings import BaseEmbedding
from llama_index.embeddings.voyageai import VoyageEmbedding
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class EmbeddingService:
    """Service for managing Voyage AI embeddings"""

    def __init__(self, model_name: str = "voyage-3.5", api_key: Optional[str] = None):
        """
        Initialize the embedding service

        Args:
            model_name: Voyage AI model name (default: voyage-3.5)
            api_key: Voyage AI API key (from env if not provided)
        """
        self.model_name = model_name
        self.api_key = api_key or os.getenv("VOYAGE_API_KEY")

        if not self.api_key:
            raise ValueError("VOYAGE_API_KEY environment variable is required")

        self._embedding_model: Optional[BaseEmbedding] = None

    def get_embedding_model(self) -> BaseEmbedding:
        """
        Get or create the embedding model instance

        Returns:
            Configured Voyage AI embedding model
        """
        if self._embedding_model is None:
            logger.info(f"Initializing Voyage AI embedding model: {self.model_name}")
            try:
                self._embedding_model = VoyageEmbedding(
                    model_name=self.model_name,
                    api_key=self.api_key
                )
                logger.info("Voyage AI embedding model initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Voyage AI embedding model: {str(e)}")
                raise

        return self._embedding_model

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        try:
            model = self.get_embedding_model()
            logger.info(f"Generating embeddings for {len(texts)} texts")

            embeddings = await model.aget_text_embedding_batch(texts)
            logger.info(f"Successfully generated {len(embeddings)} embeddings")

            return embeddings
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {str(e)}")
            raise

    async def get_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text

        Args:
            text: Text string to embed

        Returns:
            Embedding vector
        """
        if not text.strip():
            raise ValueError("Text cannot be empty")

        try:
            model = self.get_embedding_model()
            logger.info(f"Generating embedding for text (length: {len(text)})")

            embedding = await model.aget_text_embedding(text)
            logger.info(f"Successfully generated embedding with dimension: {len(embedding)}")

            return embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {str(e)}")
            raise

    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of the embedding vectors

        Returns:
            Embedding dimension size
        """
        # Voyage 3.5 produces 1024-dimensional embeddings
        return 1024

    def test_connection(self) -> bool:
        """
        Test the connection to Voyage AI API

        Returns:
            True if connection is successful, False otherwise
        """
        try:
            model = self.get_embedding_model()
            test_text = "テスト接続"  # "Test connection" in Japanese

            # Test synchronous embedding
            embedding = model.get_text_embedding(test_text)

            if embedding and len(embedding) > 0:
                logger.info("Voyage AI API connection test successful")
                return True
            else:
                logger.error("Voyage AI API connection test failed: Empty embedding")
                return False

        except Exception as e:
            logger.error(f"Voyage AI API connection test failed: {str(e)}")
            return False


# Global embedding service instance
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """
    Get the global embedding service instance

    Returns:
        EmbeddingService instance
    """
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service


def initialize_embeddings() -> bool:
    """
    Initialize the embedding service and test connection

    Returns:
        True if initialization successful, False otherwise
    """
    try:
        service = get_embedding_service()
        return service.test_connection()
    except Exception as e:
        logger.error(f"Failed to initialize embedding service: {str(e)}")
        return False