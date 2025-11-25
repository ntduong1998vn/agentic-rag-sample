"""
Tests for the Google Gemini embedding service.

This test suite verifies:
- Embedding service initialization with Google Gemini
- Single text embedding generation
- Batch embedding generation
- Vector dimension is 1536
- Integration with langchain GoogleGenerativeAIEmbeddings
"""
import pytest
from app.infrastructure.embeddings import EmbeddingService, get_embedding_service


class TestEmbeddingService:
    """Test Google Gemini embedding service"""

    def test_embedding_service_initialization(self):
        """Test that embedding service initializes correctly"""
        service = EmbeddingService()
        
        assert service is not None
        assert service.model == "models/embedding-001"
        assert service.dimension == 1536
        assert service.embeddings is not None

    def test_get_embedding_dimension(self):
        """Test that embedding dimension is 1536"""
        service = EmbeddingService()
        dimension = service.get_embedding_dimension()
        
        assert dimension == 1536

    @pytest.mark.asyncio
    async def test_get_single_embedding(self):
        """Test generating embedding for a single text"""
        service = EmbeddingService()
        text = "This is a test sentence for embedding generation."
        
        embedding = await service.get_embedding(text)
        
        assert embedding is not None
        assert isinstance(embedding, list)
        assert len(embedding) == 1536
        assert all(isinstance(x, float) for x in embedding)

    @pytest.mark.asyncio
    async def test_get_batch_embeddings(self):
        """Test generating embeddings for multiple texts"""
        service = EmbeddingService()
        texts = [
            "First test sentence.",
            "Second test sentence.",
            "Third test sentence."
        ]
        
        embeddings = await service.get_embeddings(texts)
        
        assert embeddings is not None
        assert isinstance(embeddings, list)
        assert len(embeddings) == 3
        
        for embedding in embeddings:
            assert isinstance(embedding, list)
            assert len(embedding) == 1536
            assert all(isinstance(x, float) for x in embedding)

    @pytest.mark.asyncio
    async def test_different_texts_produce_different_embeddings(self):
        """Test that different texts produce different embeddings"""
        service = EmbeddingService()
        text1 = "The cat sat on the mat."
        text2 = "The dog ran in the park."
        
        embedding1 = await service.get_embedding(text1)
        embedding2 = await service.get_embedding(text2)
        
        assert embedding1 != embedding2

    def test_get_embedding_service_singleton(self):
        """Test that get_embedding_service returns the same instance"""
        service1 = get_embedding_service()
        service2 = get_embedding_service()
        
        assert service1 is service2
