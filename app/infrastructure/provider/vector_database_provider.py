"""
Vector database provider for dependency injection.

This module provides a centralized way to manage vector database instances
and enables easy switching between different implementations.
"""

import logging
from typing import Optional

from app.domain.knowledge_base.ports import VectorStorePort
from app.infrastructure.qdrant_vector_store import QdrantVectorStore

logger = logging.getLogger(__name__)


class VectorDatabaseProvider:
    """
    Provider for vector database instances.
    
    This class manages the creation and lifecycle of vector database instances,
    supporting dependency injection and enabling easy switching between implementations.
    """
    
    _instance: Optional['VectorDatabaseProvider'] = None
    _vector_store: Optional[VectorStorePort] = None
    
    def __new__(cls):
        """Singleton pattern to ensure only one provider instance exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the provider."""
        if self._vector_store is None:
            self._initialize_default()
    
    def _initialize_default(self):
        """Initialize with default vector database (Qdrant)."""
        logger.info("Initializing VectorDatabaseProvider with QdrantVectorStore")
        self._vector_store = QdrantVectorStore()
    
    def get_vector_store(self) -> VectorStorePort:
        """
        Get the vector database instance.
        
        Returns:
            VectorStorePort: The configured vector database instance
        """
        if self._vector_store is None:
            self._initialize_default()
        return self._vector_store
    
    def set_vector_store(self, vector_store: VectorStorePort):
        """
        Set a custom vector database implementation.
        
        This allows for runtime configuration or testing with different implementations.
        
        Args:
            vector_store: Custom vector store implementation
        """
        logger.info(f"Setting custom vector store: {type(vector_store).__name__}")
        self._vector_store = vector_store
    
    @classmethod
    def reset(cls):
        """Reset the provider (useful for testing)."""
        if cls._instance is not None:
            cls._instance._vector_store = None


# Global provider instance
_provider = VectorDatabaseProvider()


def get_vector_database() -> VectorStorePort:
    """
    Dependency injection function for vector database.
    
    This function can be used with FastAPI's Depends() to inject
    the vector database into routes and services.
    
    Returns:
        VectorStorePort: The configured vector database instance
    """
    return _provider.get_vector_store()


def configure_vector_database(vector_store: VectorStorePort):
    """
    Configure the vector database implementation to use.
    
    This should be called during application startup to set the desired
    vector database implementation.
    
    Args:
        vector_store: Vector store implementation to use
    """
    _provider.set_vector_store(vector_store)
