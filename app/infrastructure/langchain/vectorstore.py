"""
Vector store module for managing Qdrant storage.

This module provides a service layer for document storage and retrieval using Qdrant.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import PointStruct, SearchRequest
from langchain_core.documents import Document
from app.infrastructure.embeddings import get_embedding_service
from app.config import get_logger, get_or_create_collection, get_collection_stats, reset_collection, get_qdrant_client
from app.config import settings

# Configure logging
logger = get_logger(__name__)


class SearchResult:
    """Represents a search result with document and score"""
    
    def __init__(self, document: Document, score: float):
        self.document = document
        self.score = score
    
    @property
    def node(self):
        """Compatibility property for llama-index style access"""
        return self.document


class VectorStoreService:
    """Service for managing Qdrant vector storage"""

    def __init__(self, collection_name: Optional[str] = None):
        """
        Initialize the vector store service

        Args:
            collection_name: Name of the Qdrant collection (uses env var if None)
        """
        self.embedding_service = get_embedding_service()
        self.collection_name = collection_name
        self._qdrant_client = None
        self._collection = None

        logger.info("Initialized VectorStoreService with Qdrant")

    def _get_qdrant_client(self) -> QdrantClient:
        """
        Get or create the Qdrant client

        Returns:
            QdrantClient: Qdrant client instance
        """
        if self._qdrant_client is None:
            self._qdrant_client = get_qdrant_client()
        return self._qdrant_client

    def _get_collection(self) -> models.CollectionInfo:
        """
        Get or create the Qdrant collection

        Returns:
            models.CollectionInfo: Collection info
        """
        if self._collection is None:
            vector_size = self.embedding_service.get_embedding_dimension()
            self._collection = get_or_create_collection(
                collection_name=self.collection_name,
                vector_size=vector_size
            )
        return self._collection

    async def add_documents(self, documents: List[Document]) -> None:
        """
        Add documents to the vector store

        Args:
            documents: List of Document objects to add
        """
        if not documents:
            logger.warning("No documents to add")
            return

        logger.info(f"Adding {len(documents)} documents to Qdrant collection")

        try:
            client = self._get_qdrant_client()
            collection_info = self._get_collection()
            collection_name = self.collection_name

            # Generate embeddings for all documents
            texts = [doc.page_content for doc in documents]
            embeddings = await self.embedding_service.get_embeddings(texts)

            # Prepare points for Qdrant
            points = []

            for idx, doc in enumerate(documents):
                # Create unique ID for each document
                doc_id = doc.metadata.get('id', f"doc_{idx}_{hash(doc.page_content) % 10000}")
                
                # Prepare metadata - exclude text_preview, chunk_name, and error
                metadata = doc.metadata or {}
                metadata = {
                    k: v for k, v in metadata.items() 
                    if k not in ["text_preview", "chunk_name", "error"]
                }

                # Convert embedding to list if it's a numpy array
                embedding_vector = embeddings[idx]
                if hasattr(embedding_vector, 'tolist'):
                    embedding_vector = embedding_vector.tolist()
                elif isinstance(embedding_vector, list):
                    embedding_vector = embedding_vector
                else:
                    # Convert to list if it's a numpy array
                    embedding_vector = list(embedding_vector)

                # Create point
                point = PointStruct(
                    id=doc_id,
                    vector=embedding_vector,
                    payload={
                        **metadata,
                        "document": doc.page_content,
                        "chunk_text": doc.page_content
                    }
                )
                points.append(point)

            # Upload points to Qdrant
            client.upsert(
                collection_name=collection_name,
                points=points
            )

            logger.info(f"Successfully added {len(documents)} documents to Qdrant collection")

        except Exception as e:
            logger.error(f"Failed to add documents to Qdrant: {str(e)}")
            raise

    async def search(
        self,
        query: str,
        top_k: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[SearchResult]:
        """
        Search for similar documents in Qdrant collection

        Args:
            query: Query text
            top_k: Number of results to return
            similarity_threshold: Minimum similarity score (0-1)

        Returns:
            List of SearchResult objects
        """
        if not query.strip():
            return []

        try:
            client = self._get_qdrant_client()
            collection_name = self.collection_name

            # Generate query embedding
            query_embedding = await self.embedding_service.get_embedding(query)

            # Convert query embedding to list if needed
            if hasattr(query_embedding, 'tolist'):
                query_vector = query_embedding.tolist()
            elif isinstance(query_embedding, list):
                query_vector = query_embedding
            else:
                query_vector = list(query_embedding)

            # Search in Qdrant collection
            search_results = client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=min(top_k, 100),  # Get more results to filter by threshold
                with_payload=True,
                with_vectors=False
            )

            # Convert to SearchResult objects
            formatted_results = []

            for result in search_results:
                # Check if similarity meets threshold
                similarity = result.score

                if similarity >= similarity_threshold:
                    # Extract metadata and document content
                    payload = result.payload or {}
                    
                    # Remove text_preview and document from metadata for the document
                    doc_metadata = {
                        k: v for k, v in payload.items() 
                        if k not in ["text_preview", "document"]
                    }

                    # Create Document object
                    doc = Document(
                        page_content=payload.get("chunk_text", payload.get("document", "")),
                        metadata=doc_metadata
                    )

                    # Create SearchResult
                    search_result = SearchResult(
                        document=doc,
                        score=float(similarity)
                    )
                    formatted_results.append(search_result)

            logger.info(f"Found {len(formatted_results)} results for query (threshold: {similarity_threshold})")
            return formatted_results

        except Exception as e:
            logger.error(f"Failed to search Qdrant collection: {str(e)}")
            raise

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the Qdrant collection

        Returns:
            Dictionary with collection statistics
        """
        try:
            stats = get_collection_stats(collection_name=self.collection_name)
            stats.update({
                'dimension': self.embedding_service.get_embedding_dimension()
            })
            
            return stats

        except Exception as e:
            logger.error(f"Failed to get Qdrant stats: {str(e)}")
            return {
                'collection_name': self.collection_name or 'rag_documents',
                'document_count': 0,
                'status': 'error',
                'error': str(e)
            }

    def clear_index(self) -> None:
        """
        Clear all documents from the Qdrant collection
        """
        try:
            vector_size = self.embedding_service.get_embedding_dimension()
            self._collection = reset_collection(
                collection_name=self.collection_name,
                vector_size=vector_size
            )

            logger.info(f"Cleared Qdrant collection")

        except Exception as e:
            logger.error(f"Failed to clear Qdrant collection: {str(e)}")
            raise


# Global vector store service instance
_vector_store_service: Optional[VectorStoreService] = None


def get_vector_store_service() -> VectorStoreService:
    """
    Get the global vector store service instance

    Returns:
        VectorStoreService instance
    """
    global _vector_store_service
    if _vector_store_service is None:
        _vector_store_service = VectorStoreService()
    return _vector_store_service
