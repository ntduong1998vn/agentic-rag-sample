import os
from typing import List, Optional
from langchain_core.embeddings import Embeddings
from dotenv import load_dotenv
from app.config.logging_config import get_logger

# Configure logging
logger = get_logger(__name__)

# Load environment variables
load_dotenv()


class VoyageEmbeddings(Embeddings):
    """Custom LangChain embedding wrapper for Voyage AI"""
    
    def __init__(self, model_name: str = "voyage-3.5", api_key: Optional[str] = None):
        self.model_name = model_name
        self.api_key = api_key or os.getenv("VOYAGE_API_KEY")
        
        if not self.api_key:
            raise ValueError("VOYAGE_API_KEY environment variable is required")
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents"""
        try:
            import voyageai
            logger.info(f"Generating embeddings for {len(texts)} documents")
            
            # Use the correct voyageai API
            client = voyageai
            result = client.embed(
                texts=texts,
                model=self.model_name,
                api_key=self.api_key
            )
            logger.info(f"Successfully generated {len(result.embeddings)} embeddings")
            
            # Convert to List[List[float]] and ensure all values are floats
            return [[float(x) for x in embedding] for embedding in result.embeddings]
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {str(e)}")
            raise
    
    def embed_query(self, text: str) -> List[float]:
        """Embed a single query text"""
        try:
            import voyageai
            logger.info(f"Generating embedding for query text (length: {len(text)})")
            
            # Use the correct voyageai API
            client = voyageai
            result = client.embed(
                texts=[text],
                model=self.model_name,
                api_key=self.api_key
            )
            embedding = result.embeddings[0]
            logger.info(f"Successfully generated embedding with dimension: {len(embedding)}")
            
            # Convert to List[float] and ensure all values are floats
            return [float(x) for x in embedding]
        except Exception as e:
            logger.error(f"Failed to generate embedding: {str(e)}")
            raise


class EmbeddingService:
    """Service for managing Voyage AI embeddings using LangChain"""

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

        self._embedding_model: Optional[Embeddings] = None

    def get_embedding_model(self) -> Embeddings:
        """
        Get or create the embedding model instance

        Returns:
            Configured Voyage AI embedding model
        """
        if self._embedding_model is None:
            logger.info(f"Initializing Voyage AI embedding model: {self.model_name}")
            try:
                self._embedding_model = VoyageEmbeddings(
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

            # Use LangChain's embedding model
            embeddings = model.embed_documents(texts)
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

            embedding = model.embed_query(text)
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