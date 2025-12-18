import json
import warnings
from langchain_core.tools import tool

from app.core.logging import get_logger
from app.rag.vectorstores.s3_store import get_vector_store, get_adjacent_chunks

logger = get_logger(__name__)

# DEPRECATION WARNING
warnings.warn(
    "rag_tool.py is deprecated and will be removed in a future version. "
    "Please use unified_search_tool.create_unified_search_tool() instead. "
    "See app/agents/tools/README.md for migration guide.",
    DeprecationWarning,
    stacklevel=2,
)


def create_knowledge_base_tool(collection_name: str):
    """Create a knowledge base search tool bound to a specific collection."""

    @tool
    def search_knowledge_base(query: str) -> str:
        """
        Search the chatbot's knowledge base for relevant information.
        Use this tool to find information that can help answer the user's question.

        Args:
            query: The search query to find relevant documents.

        Returns:
            Relevant document content from the knowledge base.
        """
        try:
            vector_store = get_vector_store(collection_name)

            # Use as_retriever with similarity_score_threshold to automatically filter by score
            retriever = vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={
                    "k": 6,
                    # "score_threshold": 0.7,
                },
            )

            docs = retriever.invoke(query)

            if not docs:
                return "No relevant documents found in the knowledge base with high accuracy (score > 0.7)."

            logger.info(
                f"Retrieved {len(docs)} documents with score > 0.7 for query='{query}'"
            )

            # Parent Document Retriever: collect unique (document_id, chunk_index) pairs
            seen_chunks = set()  # (document_id, chunk_index)
            all_chunks = []

            for doc in docs:
                document_id = doc.metadata.get("document_id")
                chunk_index = doc.metadata.get("chunk_index")

                if document_id and chunk_index is not None:
                    # Get adjacent chunks for this document
                    adjacent_chunks = get_adjacent_chunks(
                        index_name=collection_name,
                        document_id=document_id,
                        center_chunk_index=chunk_index,
                    )

                    for adj_chunk in adjacent_chunks:
                        adj_doc_id = adj_chunk.metadata.get("document_id")
                        adj_chunk_idx = adj_chunk.metadata.get("chunk_index")
                        key = (adj_doc_id, adj_chunk_idx)

                        if key not in seen_chunks:
                            seen_chunks.add(key)
                            all_chunks.append(adj_chunk)
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
            logger.info(
                f"Found {len(all_chunks)} chunks in knowledge base query='{query}'"
            )

            # Format results
            results = []
            for i, doc in enumerate(all_chunks, 1):
                source = doc.metadata.get("source", "Unknown")
                chunk_idx = doc.metadata.get("chunk_index", "?")
                results.append(
                    f"[Document {i}] (Source: {source}, Chunk: {chunk_idx})\n{doc.page_content}"
                )

            return "\n\n---\n\n".join(results)
        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}")
            return f"Error searching knowledge base: {str(e)}"

    return search_knowledge_base
