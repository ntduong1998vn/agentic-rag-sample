"""
Qdrant configuration module for RAG system.

This module provides configuration and initialization for Qdrant client.
"""

from typing import Optional, Dict, Any
import qdrant_client
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from qdrant_client.http.exceptions import UnexpectedResponse
import logging

from .settings import settings

logger = logging.getLogger(__name__)


def get_qdrant_client(
    host: Optional[str] = None,
    port: Optional[int] = None,
    api_key: Optional[str] = None
) -> qdrant_client.QdrantClient:
    """
    Initialize and return a Qdrant client.

    Args:
        host: Qdrant server host (default: from QDRANT_HOST env var)
        port: Qdrant server port (default: from QDRANT_PORT env var)
        api_key: API key (default: from QDRANT_API_KEY env var)

    Returns:
        qdrant_client.QdrantClient: Initialized Qdrant client
    """
    # Get configuration from centralized settings or parameters
    host = host or settings.qdrant_host
    port = port or settings.qdrant_port
    api_key = api_key or settings.qdrant_api_key

    # Create Qdrant client
    if api_key:
        client = qdrant_client.QdrantClient(
            host=host,
            port=port,
            api_key=api_key,
            timeout=30
        )
    else:
        client = qdrant_client.QdrantClient(
            host=host,
            port=port,
            timeout=30
        )

    return client


def get_or_create_collection(
    collection_name: str,
    vector_size: int = 1536,
    client: Optional[qdrant_client.QdrantClient] = None
) -> models.CollectionInfo:
    """
    Get or create a Qdrant collection.

    Args:
        client: Qdrant client instance (will be created if None)
        collection_name: Name of the collection
        vector_size: Size of the embedding vectors (default: 1536)

    Returns:
        models.CollectionInfo: The collection info
    """
    if client is None:
        client = get_qdrant_client()

    try:
        # Try to get existing collection
        collection_info = client.get_collection(collection_name=collection_name)
        logger.info(f"Using existing collection: {collection_name}")
        return collection_info
    except UnexpectedResponse:
        # Create new collection if it doesn't exist
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
        )
        logger.info(f"Created new collection: {collection_name}")
        
        # Return collection info
        return client.get_collection(collection_name=collection_name)
    except Exception as e:
        logger.error(f"Error handling collection: {e}")
        raise


def reset_collection(
    collection_name: str,
    vector_size: int = 1536,
    client: Optional[qdrant_client.QdrantClient] = None
) -> models.CollectionInfo:
    """
    Delete and recreate a collection.

    Args:
        client: Qdrant client instance (will be created if None)
        collection_name: Name of the collection
        vector_size: Size of the embedding vectors

    Returns:
        models.CollectionInfo: New collection info
    """
    if client is None:
        client = get_qdrant_client()

    try:
        # Delete existing collection
        client.delete_collection(collection_name=collection_name)
        logger.info(f"Deleted collection: {collection_name}")
    except UnexpectedResponse:
        logger.warning(f"Collection {collection_name} does not exist")
    except Exception as e:
        logger.warning(f"Could not delete collection (might not exist): {e}")

    # Create new collection
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
    )
    logger.info(f"Created new collection: {collection_name}")

    # Return collection info
    return client.get_collection(collection_name=collection_name)


def get_collection_stats(
    collection_name: str,
    client: Optional[qdrant_client.QdrantClient] = None
) -> Dict[str, Any]:
    """
    Get statistics for the Qdrant collection.

    Args:
        client: Qdrant client instance (will be created if None)
        collection_name: Name of the collection

    Returns:
        dict: Collection statistics
    """
    if client is None:
        client = get_qdrant_client()

    try:
        collection_info = client.get_collection(collection_name=collection_name)
        points_count = client.count(collection_name=collection_name).count
        
        return {
            "collection_name": collection_name,
            "document_count": points_count,
            "status": "active",
            "vectors_config": collection_info.config.params.vectors.to_dict() if collection_info.config.params.vectors else None
        }
    except Exception as e:
        logger.error(f"Error getting collection stats: {e}")
        return {
            "collection_name": collection_name,
            "document_count": 0,
            "status": "not_found"
        }