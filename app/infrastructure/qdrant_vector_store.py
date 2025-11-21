"""
Qdrant implementation of the VectorStorePort.

This module provides a concrete implementation of vector storage using Qdrant.
"""

import logging
from typing import List, Dict, Any, Optional

from qdrant_client import QdrantClient
from qdrant_client.http import models

from app.domain.knowledge_base.ports import VectorStorePort
from app.config import get_qdrant_client, settings

logger = logging.getLogger(__name__)


class QdrantVectorStore(VectorStorePort):
    """Qdrant implementation of the vector store interface."""
    
    def __init__(self, client: Optional[QdrantClient] = None):
        """
        Initialize Qdrant vector store.
        
        Args:
            client: Optional Qdrant client instance. If not provided, uses default from config.
        """
        self.client = client or get_qdrant_client()
        logger.info("Initialized QdrantVectorStore")
    
    async def store_vectors(
        self,
        collection_name: str,
        vectors: List[Dict[str, Any]]
    ) -> None:
        """
        Store vectors in Qdrant collection.
        
        Args:
            collection_name: Name of the Qdrant collection
            vectors: List of vector data with keys:
                - id: Unique identifier (str)
                - vector: Embedding vector (List[float])
                - payload: Metadata dictionary
        """
        try:
            # Convert to Qdrant PointStruct format
            points = [
                models.PointStruct(
                    id=vec["id"],
                    vector=vec["vector"],
                    payload=vec.get("payload", {})
                )
                for vec in vectors
            ]
            
            # Upsert points to Qdrant
            self.client.upsert(
                collection_name=collection_name,
                points=points
            )
            
            logger.info(f"Stored {len(vectors)} vectors in collection '{collection_name}'")
            
        except Exception as e:
            logger.error(f"Error storing vectors in Qdrant: {e}")
            raise
    
    async def delete_vectors(
        self,
        collection_name: str,
        filter_criteria: Dict[str, Any]
    ) -> None:
        """
        Delete vectors from Qdrant collection based on filter.
        
        Args:
            collection_name: Name of the Qdrant collection
            filter_criteria: Dictionary with filter conditions (e.g., {"document_id": "..."})
        """
        try:
            # Build Qdrant filter from criteria
            must_conditions = []
            for key, value in filter_criteria.items():
                must_conditions.append(
                    models.FieldCondition(
                        key=key,
                        match=models.MatchValue(value=str(value))
                    )
                )
            
            # Delete points matching the filter
            self.client.delete(
                collection_name=collection_name,
                points_selector=models.Filter(must=must_conditions)
            )
            
            logger.info(f"Deleted vectors from collection '{collection_name}' with filter: {filter_criteria}")
            
        except Exception as e:
            logger.error(f"Error deleting vectors from Qdrant: {e}")
            raise
    
    async def search_vectors(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 10,
        filter_criteria: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors in Qdrant.
        
        Args:
            collection_name: Name of the Qdrant collection
            query_vector: Query embedding vector
            limit: Maximum number of results
            filter_criteria: Optional filter conditions
            
        Returns:
            List of search results with score and payload
        """
        try:
            # Build filter if provided
            query_filter = None
            if filter_criteria:
                must_conditions = []
                for key, value in filter_criteria.items():
                    must_conditions.append(
                        models.FieldCondition(
                            key=key,
                            match=models.MatchValue(value=str(value))
                        )
                    )
                query_filter = models.Filter(must=must_conditions)
            
            # Perform search
            search_results = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                query_filter=query_filter
            )
            
            # Convert results to standard format
            results = []
            for hit in search_results:
                results.append({
                    "id": hit.id,
                    "score": hit.score,
                    "payload": hit.payload
                })
            
            logger.info(f"Found {len(results)} similar vectors in collection '{collection_name}'")
            return results
            
        except Exception as e:
            logger.error(f"Error searching vectors in Qdrant: {e}")
            raise
    
    async def create_collection(
        self,
        collection_name: str,
        vector_dimension: int,
        **kwargs
    ) -> None:
        """
        Create a Qdrant collection if it doesn't exist.
        
        Args:
            collection_name: Name of the collection
            vector_dimension: Dimension of the vectors
            **kwargs: Additional Qdrant-specific parameters
        """
        try:
            # Check if collection exists
            collections = self.client.get_collections().collections
            exists = any(col.name == collection_name for col in collections)
            
            if not exists:
                # Create collection with vector configuration
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=models.VectorParams(
                        size=vector_dimension,
                        distance=models.Distance.COSINE
                    )
                )
                logger.info(f"Created Qdrant collection '{collection_name}' with dimension {vector_dimension}")
            else:
                logger.info(f"Qdrant collection '{collection_name}' already exists")
                
        except Exception as e:
            logger.error(f"Error creating Qdrant collection: {e}")
            raise
    
    async def delete_collection(self, collection_name: str) -> None:
        """
        Delete a Qdrant collection.
        
        Args:
            collection_name: Name of the collection to delete
        """
        try:
            self.client.delete_collection(collection_name=collection_name)
            logger.info(f"Deleted Qdrant collection '{collection_name}'")
            
        except Exception as e:
            logger.error(f"Error deleting Qdrant collection: {e}")
            raise
    
    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """
        Get statistics about a Qdrant collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Dictionary with collection statistics
        """
        try:
            collection_info = self.client.get_collection(collection_name=collection_name)
            
            return {
                "collection_name": collection_name,
                "vectors_count": collection_info.vectors_count,
                "points_count": collection_info.points_count,
                "status": collection_info.status.value,
                "optimizer_status": collection_info.optimizer_status.value,
                "vector_dimension": collection_info.config.params.vectors.size
            }
            
        except Exception as e:
            logger.error(f"Error getting Qdrant collection stats: {e}")
            return {
                "collection_name": collection_name,
                "error": str(e)
            }
