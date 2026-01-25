"""Qdrant vector store implementation using langchain-qdrant."""

from typing import List
from uuid import UUID

from langchain_core.documents import Document as LangchainDocument
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models

from app.core.config import settings
from app.core.logging import get_logger
from app.rag.embeddings.gemini import get_gemini_embeddings, get_embedding_dimension

logger = get_logger(__name__)


def get_qdrant_client() -> QdrantClient:
    """Get Qdrant client instance."""
    return QdrantClient(
        host=settings.qdrant_host,
        port=settings.qdrant_port,
        api_key=settings.qdrant_api_key,
    )


def ensure_collection_exists(collection_name: str, vector_size: int = None) -> None:
    """
    Ensure a collection exists in Qdrant, create if not.

    Args:
        collection_name: Name of the collection
        vector_size: Vector dimension (defaults to Gemini embedding dimension)
    """
    client = get_qdrant_client()
    vector_size = vector_size or get_embedding_dimension()

    collections = client.get_collections()
    existing_names = [c.name for c in collections.collections]

    if collection_name not in existing_names:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=qdrant_models.VectorParams(
                size=vector_size,
                distance=qdrant_models.Distance.COSINE,
            ),
        )
        logger.info(
            f"Created Qdrant collection: {collection_name} with vector size {vector_size}"
        )
    else:
        logger.debug(f"Collection already exists: {collection_name}")


def get_vector_store(collection_name: str) -> QdrantVectorStore:
    """
    Get a QdrantVectorStore instance for a collection.

    Args:
        collection_name: Name of the Qdrant collection

    Returns:
        QdrantVectorStore instance
    """
    embeddings = get_gemini_embeddings()
    client = get_qdrant_client()

    return QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        embedding=embeddings,
    )


def add_documents_to_collection(
    collection_name: str,
    documents: List[LangchainDocument],
    document_id: UUID,
) -> int:
    """
    Add documents to a Qdrant collection.

    Args:
        collection_name: Name of the Qdrant collection
        documents: List of Langchain Document objects (chunks)
        document_id: ID of the source document for metadata

    Returns:
        Number of documents added
    """
    if not documents:
        logger.warning("No documents to add")
        return 0

    # Add document_id to metadata for each chunk
    for doc in documents:
        doc.metadata["document_id"] = str(document_id)

    ensure_collection_exists(collection_name)
    vector_store = get_vector_store(collection_name)
    vector_store.add_documents(documents, batch_size=100)

    logger.info(f"Added {len(documents)} chunks to collection {collection_name}")
    return len(documents)


def delete_document_vectors(collection_name: str, document_id: UUID) -> None:
    """
    Delete all vectors associated with a document.

    Args:
        collection_name: Name of the Qdrant collection
        document_id: ID of the document whose vectors should be deleted
    """
    client = get_qdrant_client()

    # Check if collection exists first
    collections = client.get_collections()
    existing_names = [c.name for c in collections.collections]

    if collection_name not in existing_names:
        logger.debug(
            f"Collection {collection_name} not found, skipping vector deletion for {document_id}"
        )
        return

    client.delete(
        collection_name=collection_name,
        points_selector=qdrant_models.FilterSelector(
            filter=qdrant_models.Filter(
                must=[
                    qdrant_models.FieldCondition(
                        key="metadata.document_id",
                        match=qdrant_models.MatchValue(value=str(document_id)),
                    )
                ]
            )
        ),
    )
    logger.info(
        f"Deleted vectors for document {document_id} from collection {collection_name}"
    )
