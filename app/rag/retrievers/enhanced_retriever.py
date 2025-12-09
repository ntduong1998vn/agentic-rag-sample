"""Enhanced retriever with Multi-Query and Contextual Compression.

Uses langchain-classic's MultiQueryRetriever and ContextualCompressionRetriever
to improve retrieval quality.
"""

from typing import List

from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.retrievers.multi_query import MultiQueryRetriever
from langchain_classic.retrievers.contextual_compression import (
    ContextualCompressionRetriever,
)
from langchain_classic.retrievers.document_compressors import LLMChainExtractor

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def get_llm_for_retriever() -> ChatGoogleGenerativeAI:
    """Get a lightweight LLM for retriever operations."""
    return ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-lite",
        google_api_key=settings.google_api_key,
        temperature=0.3,
    )


def create_multi_query_retriever(
    base_retriever: BaseRetriever,
    llm: BaseChatModel = None,
) -> MultiQueryRetriever:
    """
    Create a MultiQueryRetriever that generates multiple query variants.

    Args:
        base_retriever: The base retriever (e.g., vector store retriever).
        llm: Optional LLM for query generation. Uses default if not provided.

    Returns:
        MultiQueryRetriever instance.
    """
    if llm is None:
        llm = get_llm_for_retriever()

    retriever = MultiQueryRetriever.from_llm(
        retriever=base_retriever,
        llm=llm,
    )

    return retriever


def create_compression_retriever(
    base_retriever: BaseRetriever,
    llm: BaseChatModel = None,
) -> ContextualCompressionRetriever:
    """
    Create a ContextualCompressionRetriever that extracts relevant content.

    Args:
        base_retriever: The base retriever to compress results from.
        llm: Optional LLM for compression. Uses default if not provided.

    Returns:
        ContextualCompressionRetriever instance.
    """
    if llm is None:
        llm = get_llm_for_retriever()

    compressor = LLMChainExtractor.from_llm(llm)

    retriever = ContextualCompressionRetriever(
        base_compressor=compressor,
        base_retriever=base_retriever,
    )

    return retriever


def create_enhanced_retriever(
    base_retriever: BaseRetriever,
    use_multi_query: bool = True,
    use_compression: bool = True,
    llm: BaseChatModel = None,
) -> BaseRetriever:
    """
    Create an enhanced retriever with Multi-Query and/or Contextual Compression.

    This combines:
    1. MultiQueryRetriever: Generates multiple query variants to increase recall
    2. ContextualCompressionRetriever: Extracts only relevant content from documents

    Args:
        base_retriever: The base vector store retriever.
        use_multi_query: Whether to use Multi-Query Retrieval.
        use_compression: Whether to use Contextual Compression.
        llm: Optional LLM for both operations.

    Returns:
        Enhanced retriever combining the selected strategies.
    """
    if llm is None:
        llm = get_llm_for_retriever()

    retriever = base_retriever

    # First, wrap with Multi-Query Retriever
    if use_multi_query:
        retriever = create_multi_query_retriever(retriever, llm)

    # Then, wrap with Contextual Compression
    if use_compression:
        retriever = create_compression_retriever(retriever, llm)

    return retriever


def retrieve_with_enhanced_retriever(
    base_retriever: BaseRetriever,
    query: str,
    use_multi_query: bool = True,
    use_compression: bool = True,
) -> List[Document]:
    """
    Retrieve documents using enhanced retrieval strategies.

    Args:
        base_retriever: The base vector store retriever.
        query: The search query.
        use_multi_query: Whether to use Multi-Query Retrieval.
        use_compression: Whether to use Contextual Compression.

    Returns:
        List of retrieved and processed documents.
    """
    enhanced_retriever = create_enhanced_retriever(
        base_retriever=base_retriever,
        use_multi_query=use_multi_query,
        use_compression=use_compression,
    )

    docs = enhanced_retriever.invoke(query)
    logger.info(
        f"Enhanced retrieval returned {len(docs)} documents for query: {query[:50]}..."
    )

    return docs
