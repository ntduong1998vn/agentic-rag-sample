"""RAG tool for searching context via retrieval."""

from langchain_core.tools import tool

from app.core.logging import get_logger
from app.rag.vectorstores.s3_store import get_vector_store

logger = get_logger(__name__)


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
            docs = vector_store.similarity_search(query, k=4)

            if not docs:
                return "No relevant documents found in the knowledge base."

            results = []
            for i, doc in enumerate(docs, 1):
                source = doc.metadata.get("source", "Unknown")
                results.append(f"[Document {i}] (Source: {source})\n{doc.page_content}")

            return "\n\n---\n\n".join(results)
        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}")
            return f"Error searching knowledge base: {str(e)}"

    return search_knowledge_base
