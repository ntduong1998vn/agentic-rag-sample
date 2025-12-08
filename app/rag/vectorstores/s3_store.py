"""Amazon S3 Vectors store implementation using langchain-aws."""

from typing import List, Optional
from uuid import UUID

from langchain_core.documents import Document as LangchainDocument
from langchain_aws.vectorstores import AmazonS3Vectors
from langchain_aws.embeddings import BedrockEmbeddings

from app.core.config import settings
from app.core.logging import get_logger
from app.rag.embeddings.gemini import get_gemini_embeddings

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
    logger.debug(f"Index name: {index_name} -> normalized: {normalized_name}")

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
        non_filterable_metadata_keys=["_page_content", "source"],
        page_content_metadata_key="_page_content",
    )


def ensure_index_exists(index_name: str, vector_size: int = None) -> None:
    """
    Ensure an index exists in S3 Vectors.

    Note: With create_index_if_not_exist=True in get_vector_store,
    the index is created automatically when first adding documents.

    Args:
        index_name: Name of the index
        vector_size: Vector dimension (not used - determined automatically)
    """
    # S3 Vectors creates the index automatically when adding documents
    # if create_index_if_not_exist=True
    logger.debug(f"Index will be auto-created if not exists: {index_name}")


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

    logger.info(f"Adding {len(documents)} documents to index: {index_name}")
    vector_store = get_vector_store(index_name)
    ids = vector_store.add_documents(documents)

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

        # Search for vectors with this document_id to get their IDs
        # Use a generic query and filter by document_id
        results = vector_store.similarity_search(
            query="",  # Empty query to match all
            k=1000,  # Get as many as possible
            filter={"document_id": {"$eq": str(document_id)}},
        )

        if results:
            # Get the IDs from the results
            ids_to_delete = [doc.id for doc in results if doc.id]
            if ids_to_delete:
                vector_store.delete(ids=ids_to_delete)
                logger.info(
                    f"Deleted {len(ids_to_delete)} vectors for document {document_id} from index {index_name}"
                )
            else:
                logger.warning(
                    f"Found documents but no IDs to delete for document {document_id}"
                )
        else:
            logger.debug(
                f"No vectors found for document {document_id} in index {index_name}"
            )

    except Exception as e:
        logger.error(f"Error deleting vectors for document {document_id}: {e}")
        # Don't raise - this is a cleanup operation that shouldn't block re-processing
