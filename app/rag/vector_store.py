"""
Vector store module for managing ChromaDB storage.

This module provides a service layer for document storage and retrieval using ChromaDB.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
from chromadb import Collection
from langchain_chroma import Chroma
from llama_index.core.schema import Document, NodeWithScore
from app.rag.embeddings import get_embedding_service
from app.config.logging_config import get_logger
from app.config.chroma_config import get_or_create_collection

# Configure logging
logger = get_logger(__name__)


class VectorStoreService:
    """Service for managing ChromaDB vector storage"""

    def __init__(self, collection_name: Optional[str] = None):
        """
        Initialize the vector store service

        Args:
            collection_name: Name of the Chroma collection (uses env var if None)
        """
        self.embedding_service = get_embedding_service()
        self.collection_name = collection_name
        self._chroma_client = None
        self._collection = None
        self._vector_store = None

        logger.info("Initialized VectorStoreService with ChromaDB")

    def _get_chroma_collection(self) -> Collection:
        """
        Get or create the ChromaDB collection

        Returns:
            Collection: ChromaDB collection instance
        """
        if self._collection is None:
            self._collection = get_or_create_collection(collection_name=self.collection_name)
        return self._collection

    def _get_vector_store(self) -> Chroma:
        """
        Get the LangChain Chroma vector store instance

        Returns:
            Chroma: LangChain Chroma vector store
        """
        if self._vector_store is None:
            collection = self._get_chroma_collection()

            # Create LangChain Chroma wrapper
            self._vector_store = Chroma(
                client=collection._client,
                collection_name=collection.name,
                embedding_function=None,  # We'll compute embeddings manually
            )

        return self._vector_store

    async def add_documents(self, documents: List[Document]) -> None:
        """
        Add documents to the vector store

        Args:
            documents: List of Document objects to add
        """
        if not documents:
            logger.warning("No documents to add")
            return

        logger.info(f"Adding {len(documents)} documents to Chroma collection")

        try:
            collection = self._get_chroma_collection()

            # Generate embeddings for all documents
            texts = [doc.text for doc in documents]
            embeddings = await self.embedding_service.get_embeddings(texts)

            # Prepare documents for Chroma
            ids = []
            metadatas = []

            for idx, doc in enumerate(documents):
                # Create unique ID for each document
                doc_id = doc.doc_id or f"doc_{idx}_{hash(doc.text) % 10000}"
                ids.append(doc_id)

                # Prepare metadata
                metadata = doc.metadata or {}
                metadata.update({
                    "text_preview": doc.text[:200]  # Store text preview
                })
                metadatas.append(metadata)

            # Add to Chroma collection
            collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas
            )

            logger.info(f"Successfully added {len(documents)} documents to Chroma collection")

        except Exception as e:
            logger.error(f"Failed to add documents to Chroma: {str(e)}")
            raise

    async def search(
        self,
        query: str,
        top_k: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[NodeWithScore]:
        """
        Search for similar documents in Chroma collection

        Args:
            query: Query text
            top_k: Number of results to return
            similarity_threshold: Minimum similarity score (0-1)

        Returns:
            List of NodeWithScore objects
        """
        if not query.strip():
            return []

        try:
            collection = self._get_chroma_collection()

            # Generate query embedding
            query_embedding = await self.embedding_service.get_embedding(query)

            # Search in Chroma collection
            # Chroma returns distances, we need to convert to similarities
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=min(top_k, 100),  # Get more results to filter by threshold
                include=["documents", "metadatas", "distances"]
            )

            # Convert to NodeWithScore objects
            search_results = []

            if results and results["ids"] and results["ids"][0]:
                ids = results["ids"][0]
                documents = results["documents"][0]
                metadatas = results["metadatas"][0]
                distances = results["distances"][0]

                for idx, doc_id in enumerate(ids):
                    # Convert distance to similarity (Chroma uses cosine distance)
                    # For cosine distance: similarity = 1 - distance
                    similarity = 1.0 - distances[idx]

                    if similarity >= similarity_threshold:
                        # Extract metadata
                        metadata = metadatas[idx] if idx < len(metadatas) else {}

                        # Remove text_preview from metadata for the document
                        doc_metadata = {k: v for k, v in metadata.items() if k != "text_preview"}

                        # Create Document object
                        doc = Document(
                            text=documents[idx],
                            doc_id=doc_id,
                            metadata=doc_metadata
                        )

                        # Create NodeWithScore
                        node_with_score = NodeWithScore(
                            node=doc,
                            score=float(similarity)
                        )
                        search_results.append(node_with_score)

            logger.info(f"Found {len(search_results)} results for query (threshold: {similarity_threshold})")
            return search_results

        except Exception as e:
            logger.error(f"Failed to search Chroma collection: {str(e)}")
            raise

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the Chroma collection

        Returns:
            Dictionary with collection statistics
        """
        try:
            collection = self._get_chroma_collection()
            count = collection.count()

            return {
                'collection_name': collection.name,
                'document_count': count,
                'status': 'active',
                'dimension': self.embedding_service.get_embedding_dimension()
            }

        except Exception as e:
            logger.error(f"Failed to get Chroma stats: {str(e)}")
            return {
                'collection_name': self.collection_name or 'rag_documents',
                'document_count': 0,
                'status': 'error',
                'error': str(e)
            }

    def clear_index(self) -> None:
        """
        Clear all documents from the Chroma collection
        """
        try:
            from app.config.chroma_config import reset_collection

            self._collection = reset_collection(collection_name=self.collection_name)
            self._vector_store = None  # Reset cached vector store

            logger.info(f"Cleared Chroma collection: {self._collection.name}")

        except Exception as e:
            logger.error(f"Failed to clear Chroma collection: {str(e)}")
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
