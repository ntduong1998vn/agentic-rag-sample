"""
Repository ports (interfaces) for knowledge base domain.

These define the contracts for persistence and data access.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import uuid

from app.domain.knowledge_base.entities import KnowledgeBase, Document


class KnowledgeBaseRepositoryPort(ABC):
    """Abstract repository interface for knowledge base operations."""
    
    @abstractmethod
    async def create(self, knowledge_base: KnowledgeBase) -> KnowledgeBase:
        """Create a new knowledge base."""
        pass
    
    @abstractmethod
    async def get_by_id(self, knowledge_base_id: uuid.UUID) -> Optional[KnowledgeBase]:
        """Get knowledge base by ID."""
        pass
    
    @abstractmethod
    async def get_by_chatbot_id(self, chatbot_id: uuid.UUID) -> Optional[KnowledgeBase]:
        """Get knowledge base by chatbot ID."""
        pass
    
    @abstractmethod
    async def update(self, knowledge_base: KnowledgeBase) -> KnowledgeBase:
        """Update knowledge base."""
        pass
    
    @abstractmethod
    async def delete(self, knowledge_base_id: uuid.UUID) -> bool:
        """Delete knowledge base."""
        pass


class DocumentRepositoryPort(ABC):
    """Abstract repository interface for document operations."""
    
    @abstractmethod
    async def create(self, document: Document) -> Document:
        """Create a new document."""
        pass
    
    @abstractmethod
    async def create_many(self, documents: List[Document]) -> List[Document]:
        """Create multiple documents in batch."""
        pass
    
    @abstractmethod
    async def get_by_id(self, document_id: uuid.UUID) -> Optional[Document]:
        """Get document by ID."""
        pass
    
    @abstractmethod
    async def get_by_checksum(self, knowledge_base_id: uuid.UUID, checksum: str) -> Optional[Document]:
        """Get document by checksum to detect duplicates."""
        pass
    
    @abstractmethod
    async def list_by_knowledge_base(
        self, 
        knowledge_base_id: uuid.UUID,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Document]:
        """List documents in a knowledge base, optionally filtered by status."""
        pass
    
    @abstractmethod
    async def update(self, document: Document) -> Document:
        """Update document."""
        pass
    
    @abstractmethod
    async def count_by_status(self, knowledge_base_id: uuid.UUID, status: str) -> int:
        """Count documents by status."""
        pass


class VectorStorePort(ABC):
    """
    Abstract interface for vector database operations.
    
    This port allows switching between different vector databases
    (Qdrant, Pinecone, Weaviate, etc.) without changing business logic.
    """
    
    @abstractmethod
    async def store_vectors(
        self,
        collection_name: str,
        vectors: List[Dict[str, Any]]
    ) -> None:
        """
        Store vectors in the vector database.
        
        Args:
            collection_name: Name of the collection/index
            vectors: List of vector data containing:
                - id: Unique identifier for the vector
                - vector: The embedding vector (List[float])
                - payload: Metadata associated with the vector
        """
        pass
    
    @abstractmethod
    async def delete_vectors(
        self,
        collection_name: str,
        filter_criteria: Dict[str, Any]
    ) -> None:
        """
        Delete vectors from the collection based on filter criteria.
        
        Args:
            collection_name: Name of the collection/index
            filter_criteria: Filter conditions (e.g., {"document_id": "..."})
        """
        pass
    
    @abstractmethod
    async def search_vectors(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 10,
        filter_criteria: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors.
        
        Args:
            collection_name: Name of the collection/index
            query_vector: The query embedding vector
            limit: Maximum number of results to return
            filter_criteria: Optional filter conditions
            
        Returns:
            List of search results containing vector data and scores
        """
        pass
    
    @abstractmethod
    async def create_collection(
        self,
        collection_name: str,
        vector_dimension: int,
        **kwargs
    ) -> None:
        """
        Create a new collection/index if it doesn't exist.
        
        Args:
            collection_name: Name of the collection/index
            vector_dimension: Dimension of the vectors
            **kwargs: Additional provider-specific parameters
        """
        pass
    
    @abstractmethod
    async def delete_collection(self, collection_name: str) -> None:
        """
        Delete a collection/index.
        
        Args:
            collection_name: Name of the collection/index
        """
        pass
    
    @abstractmethod
    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """
        Get statistics about a collection.
        
        Args:
            collection_name: Name of the collection/index
            
        Returns:
            Dictionary containing collection statistics
        """
        pass