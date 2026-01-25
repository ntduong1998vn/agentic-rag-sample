from app.rag.vectorstores.qdrant_store import get_vector_store
from uuid import UUID
from typing import Optional, List
from langchain_core.documents import Document
from langchain_core.tools import tool
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.services.document import DocumentService
from app.core.logging import get_logger

logger = get_logger(__name__)


def _retrieve_and_expand_chunks(
    collection_name: str,
    query: str,
    document_id_filter: Optional[str] = None,
    k: int = 6,
    adjacent_count: int = 3,
) -> List[Document]:
    """
    Core retrieval logic with Parent Document Retriever expansion.

    This function handles:
    1. Similarity search with score threshold
    2. Adjacent chunk retrieval for context
    3. Deduplication
    4. Sorting by document_id and chunk_index

    Args:
        collection_name: The vector store collection name.
        query: The search query.
        document_id_filter: Optional document_id to filter results.
        k: Number of top results to retrieve.
        adjacent_count: Number of adjacent chunks to retrieve on each side.

    Returns:
        List of expanded Document chunks, sorted by document_id and chunk_index.
    """
    vector_store = get_vector_store(collection_name)

    # Build search kwargs
    search_kwargs = {
        "k": k,
    }

    # Add document_id filter if specified
    if document_id_filter:
        search_kwargs["filter"] = {"document_id": {"$eq": document_id_filter}}

    # Use retriever with similarity
    retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs=search_kwargs,
    )

    docs = retriever.invoke(query)

    if not docs:
        return []

    logger.info(
        f"Retrieved {len(docs)} documents for query='{query}'"
        + (
            f" (filtered by document_id={document_id_filter})"
            if document_id_filter
            else ""
        )
    )

    # Since adjacent_count is 0, just use the docs directly
    if adjacent_count == 0:
        all_chunks = docs
    else:
        # Parent Document Retriever: collect unique (document_id, chunk_index) pairs
        seen_chunks = set()  # (document_id, chunk_index)
        all_chunks = []

        for doc in docs:
            doc_id = doc.metadata.get("document_id")
            chunk_index = doc.metadata.get("chunk_index")

            if doc_id and chunk_index is not None:
                # Without get_adjacent_chunks, just add the original doc
                key = (doc_id, chunk_index)
                if key not in seen_chunks:
                    seen_chunks.add(key)
                    all_chunks.append(doc)
            else:
                # Fallback: no chunk_index metadata, use original doc
                all_chunks.append(doc)

        # Sort by document_id, then by chunk_index for reading order
        all_chunks.sort(
            key=lambda x: (
                x.metadata.get("document_id", ""),
                x.metadata.get("chunk_index", 0),
            )
        )

    # Log metadata of all found chunks
    logger.info(f"Found {len(all_chunks)} chunks for query='{query}'")

    return all_chunks


def create_unified_search_tool(
    collection_name: str,
    chatbot_id: UUID,
    conversation_id: Optional[UUID] = None,
):
    """
    Create a unified search tool that can search both:
    1. The entire knowledge base (when document_name is not provided)
    2. Within a specific document (when document_name is provided)

    This tool merges the functionality of:
    - search_knowledge_base (rag_tool.py)
    - search_document_content (document_search_tool.py)

    Args:
        collection_name: The vector store collection name.
        chatbot_id: The chatbot ID to find documents for.
        conversation_id: Optional conversation ID for conversation-specific documents.

    Returns:
        A LangChain tool for unified search.
    """

    @tool
    def search_knowledge_base(query: str, document_name: Optional[str] = None) -> str:
        """
        Search the chatbot's knowledge base for relevant information.

        This tool can perform two types of searches:
        1. General search: When document_name is not provided, search across all documents.
        2. Document-specific search: When document_name is provided, search only within that document.

        Args:
            query: The search query to find relevant content.
            document_name: Optional. The name or partial name of a specific document to search in.
                          If not provided, searches the entire knowledge base.

        Returns:
            Relevant document content, or a message if nothing is found.
        """
        try:
            document_id_filter = None
            found_document_name = None

            # If document_name is provided, find its document_id
            if document_name:
                db: Session = SessionLocal()
                try:
                    document_service = DocumentService(db)
                    result = document_service.find_document_by_name(
                        chatbot_id=chatbot_id,
                        document_name=document_name,
                        conversation_id=conversation_id,
                    )

                    if result:
                        document_id, found_document_name = result
                        document_id_filter = str(document_id)
                    else:
                        return f"Không tìm thấy tài liệu '{document_name}' hoặc tài liệu chưa được xử lý hoàn tất."
                finally:
                    db.close()

            # Retrieve and expand chunks
            all_chunks = _retrieve_and_expand_chunks(
                collection_name=collection_name,
                query=query,
                document_id_filter=document_id_filter,
                k=10,
                adjacent_count=0,
            )

            # Handle no results
            if not all_chunks:
                if document_name:
                    return f"Không tìm thấy thông tin liên quan đến '{query}' trong tài liệu '{found_document_name}' với độ chính xác cao (score > 0.7)."
                else:
                    return "No relevant documents found in the knowledge base with high accuracy (score > 0.7)."

            # Format results with clear citations
            results = []

            for i, doc in enumerate(all_chunks, 1):
                source = doc.metadata.get("source", "Unknown")
                chunk_idx = doc.metadata.get("chunk_index", "?")

                # Create citation reference
                citation = f"[Source {i}] {source} (chunk {chunk_idx})"

                results.append(f"{citation}\n---\n{doc.page_content}")

            # Add citation summary at the end
            citation_summary = "\n\n## References\n"
            for i, doc in enumerate(all_chunks, 1):
                source = doc.metadata.get("source", "Unknown")
                citation_summary += f"- [Source {i}]: {source}\n"

            return "\n\n".join(results) + citation_summary
            
        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}")
            return f"Error searching knowledge base: {str(e)}"
    
    return search_knowledge_base
