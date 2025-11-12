"""
ChromaDB configuration module for RAG system.

This module provides configuration and initialization for ChromaDB client.
"""

import os
import chromadb
from chromadb.config import Settings
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def get_chroma_client(
    host: Optional[str] = None,
    port: Optional[int] = None,
    auth_token: Optional[str] = None
) -> chromadb.Client:
    """
    Initialize and return a ChromaDB client.

    Args:
        host: Chroma server host (default: from CHROMA_HOST env var)
        port: Chroma server port (default: from CHROMA_PORT env var)
        auth_token: Authentication token (default: from CHROMA_AUTH_TOKEN env var)

    Returns:
        chromadb.Client: Initialized ChromaDB client
    """
    # Get configuration from environment variables or parameters
    host = host or os.getenv("CHROMA_HOST", "localhost")
    port = port or int(os.getenv("CHROMA_PORT", "8001"))
    auth_token = auth_token or os.getenv("CHROMA_AUTH_TOKEN", "rag_token_123")
    collection_name = os.getenv("CHROMA_COLLECTION_NAME", "rag_documents")

    # Create settings for HTTP client
    settings = Settings(
        chroma_server_host=host,
        chroma_server_http_port=port,
        chroma_client_auth_provider="chromadb.auth.token_authn.TokenAuthClientProvider",
        chroma_client_auth_credentials=auth_token,
        anonymized_telemetry=False
    )

    # Create HTTP client
    client = chromadb.HttpClient(settings=settings)

    logger.info(f"Chroma client initialized - Host: {host}:{port}, Collection: {collection_name}")

    return client


def get_or_create_collection(
    client: Optional[chromadb.Client] = None,
    collection_name: Optional[str] = None
) -> chromadb.Collection:
    """
    Get or create a ChromaDB collection.

    Args:
        client: ChromaDB client instance (will be created if None)
        collection_name: Name of the collection (default: from CHROMA_COLLECTION_NAME env var)

    Returns:
        chromadb.Collection: The collection instance
    """
    if client is None:
        client = get_chroma_client()

    collection_name = collection_name or os.getenv("CHROMA_COLLECTION_NAME", "rag_documents")

    try:
        # Try to get existing collection
        collection = client.get_collection(name=collection_name)
        logger.info(f"Using existing collection: {collection_name}")
    except Exception:
        # Create new collection if it doesn't exist
        collection = client.create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}  # Use cosine similarity
        )
        logger.info(f"Created new collection: {collection_name}")

    return collection


def reset_collection(
    client: Optional[chromadb.Client] = None,
    collection_name: Optional[str] = None
) -> chromadb.Collection:
    """
    Delete and recreate a collection.

    Args:
        client: ChromaDB client instance (will be created if None)
        collection_name: Name of the collection (default: from CHROMA_COLLECTION_NAME env var)

    Returns:
        chromadb.Collection: New collection instance
    """
    if client is None:
        client = get_chroma_client()

    collection_name = collection_name or os.getenv("CHROMA_COLLECTION_NAME", "rag_documents")

    try:
        # Delete existing collection
        client.delete_collection(name=collection_name)
        logger.info(f"Deleted collection: {collection_name}")
    except Exception as e:
        logger.warning(f"Could not delete collection (might not exist): {e}")

    # Create new collection
    collection = client.create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )
    logger.info(f"Created new collection: {collection_name}")

    return collection


def get_collection_stats(client: Optional[chromadb.Client] = None) -> dict:
    """
    Get statistics for the ChromaDB collection.

    Args:
        client: ChromaDB client instance (will be created if None)

    Returns:
        dict: Collection statistics
    """
    if client is None:
        client = get_chroma_client()

    collection_name = os.getenv("CHROMA_COLLECTION_NAME", "rag_documents")

    try:
        collection = client.get_collection(name=collection_name)
        count = collection.count()
        return {
            "collection_name": collection_name,
            "document_count": count,
            "status": "active"
        }
    except Exception as e:
        logger.error(f"Error getting collection stats: {e}")
        return {
            "collection_name": collection_name,
            "document_count": 0,
            "status": "not_found"
        }
