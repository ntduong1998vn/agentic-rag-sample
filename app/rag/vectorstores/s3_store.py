"""Amazon S3 Vectors store implementation using langchain-aws."""

import json
from typing import List
from uuid import UUID

from langchain_core.documents import Document as LangchainDocument
from langchain_aws.vectorstores import AmazonS3Vectors
from langchain_aws.embeddings import BedrockEmbeddings

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def normalize_index_name(index_name: str) -> str:
    """
    Normalize index name to comply with S3 Vectors requirements.

    S3 Vectors index names must:
    - Only contain lowercase letters (a-z), numbers (0-9), and hyphens (-)
    - Start with a letter
    - Be 3-63 characters long

    Args:
        index_name: Original index name

    Returns:
        Normalized index name
    """
    import re

    # Convert to lowercase
    normalized = index_name.lower()

    # Replace underscores and spaces with hyphens
    normalized = normalized.replace("_", "-").replace(" ", "-")

    # Remove all characters except lowercase letters, numbers, and hyphens
    normalized = re.sub(r"[^a-z0-9-]", "", normalized)

    # Remove consecutive hyphens
    normalized = re.sub(r"-+", "-", normalized)

    # Remove leading/trailing hyphens
    normalized = normalized.strip("-")

    # Ensure it starts with a letter
    if not normalized or not normalized[0].isalpha():
        normalized = "idx-" + normalized

    # Ensure minimum length of 3
    if len(normalized) < 3:
        normalized = "idx-" + normalized

    # Truncate to 63 characters if needed
    if len(normalized) > 63:
        normalized = normalized[:63].rstrip("-")

    return normalized


def get_vector_store(index_name: str) -> AmazonS3Vectors:
    """
    Get an AmazonS3Vectors instance for an index.

    Args:
        index_name: Name of the vector index (equivalent to collection_name in Qdrant)

    Returns:
        AmazonS3Vectors instance
    """
    # Normalize index name to comply with S3 Vectors requirements
    normalized_name = normalize_index_name(index_name)

    embeddings = BedrockEmbeddings(
        model_id="amazon.titan-embed-text-v1",
        region_name=settings.s3_vectors_region,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
    )

    # S3 Vectors has a 2048 bytes limit for filterable metadata
    # Mark large fields as non-filterable, keep only document_id filterable
    return AmazonS3Vectors(
        vector_bucket_name=settings.s3_vectors_bucket_name,
        index_name=normalized_name,
        embedding=embeddings,
        region_name=settings.s3_vectors_region,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        create_index_if_not_exist=True,
        distance_metric="cosine",
        non_filterable_metadata_keys=[
            "_page_content",
            "filetype",
        ],
        page_content_metadata_key="_page_content",
    )


def add_documents_to_index(
    index_name: str,
    documents: List[LangchainDocument],
    document_id: UUID,
) -> int:
    """
    Add documents to an S3 Vectors index.

    Args:
        index_name: Name of the S3 Vectors index
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

    vector_store = get_vector_store(index_name)
    ids = vector_store.add_documents(documents, batch_size=100, use_async_db=True)

    logger.info(
        f"Successfully added {len(documents)} chunks to index {index_name}, IDs: {ids[:3]}..."
    )
    return len(documents)


def delete_document_vectors(index_name: str, document_id: UUID) -> None:
    """
    Delete all vectors associated with a document.

    Note: S3 Vectors only supports deletion by vector IDs, not by metadata filter.
    This function searches for vectors with the document_id and then deletes them.

    Args:
        index_name: Name of the S3 Vectors index
        document_id: ID of the document whose vectors should be deleted
    """
    try:
        vector_store = get_vector_store(index_name)
        total_deleted = 0

        while True:
            # Search for vectors with this document_id to get their IDs
            # Use a dummy query (actual text doesn't matter since we filter by document_id)
            # Note: S3 Vectors QueryVectors limit topK to 100
            results = vector_store.similarity_search(
                query="all",  # Dummy query to satisfy embedding model requirements
                k=100,  # Max allowed by S3 Vectors QueryVectors
                filter={"document_id": {"$eq": str(document_id)}},
            )

            if not results:
                break

            # Get the IDs from the results
            ids_to_delete = [doc.id for doc in results if doc.id]

            if not ids_to_delete:
                logger.warning(
                    f"Found documents but no IDs to delete for document {document_id}"
                )
                break

            vector_store.delete(ids=ids_to_delete)
            count = len(ids_to_delete)
            total_deleted += count
            logger.debug(f"Deleted batch of {count} vectors for document {document_id}")

            # If we got fewer than k results, we've likely found everything
            if len(results) < 100:
                break

        if total_deleted > 0:
            logger.info(
                f"Deleted total {total_deleted} vectors for document {document_id} from index {index_name}"
            )
        else:
            logger.debug(
                f"No vectors found for document {document_id} in index {index_name}"
            )

    except Exception as e:
        logger.error(f"Error deleting vectors for document {document_id}: {e}")
        # Don't raise - this is a cleanup operation that shouldn't block re-processing


def get_adjacent_chunks(
    index_name: str,
    document_id: str,
    center_chunk_index: int,
    adjacent_count: int = 3,
) -> List[LangchainDocument]:
    """
    Get adjacent chunks around a center chunk for Parent Document Retriever pattern.

    Given a center chunk, retrieves chunks within the range:
    [center - adjacent_count, center + adjacent_count]
    e.g., center=3, adjacent_count=5 -> chunks 0-8 (capped at 0)

    Args:
        index_name: Name of the S3 Vectors index
        document_id: ID of the document to get chunks from
        center_chunk_index: The chunk_index of the center chunk
        adjacent_count: Number of chunks to get on each side (default: 5)

    Returns:
        List of LangchainDocument objects sorted by chunk_index
    """
    try:
        vector_store = get_vector_store(index_name)

        # Calculate the range of chunk indices to fetch
        start_index = max(0, center_chunk_index - adjacent_count)
        end_index = center_chunk_index + adjacent_count

        # Use $gte and $lte operators to filter chunk_index range directly
        results = vector_store.similarity_search(
            query="all",  # Dummy query
            k=100,  # Max chunks to retrieve
            filter={
                "$and": [
                    {"document_id": {"$eq": document_id}},
                    {"chunk_index": {"$gte": start_index}},
                    {"chunk_index": {"$lte": end_index}},
                ]
            },
        )

        # Sort by chunk_index to maintain order
        results.sort(key=lambda x: x.metadata.get("chunk_index", 0))

        return results

    except Exception as e:
        logger.error(f"Error getting adjacent chunks: {e}")
        return []
