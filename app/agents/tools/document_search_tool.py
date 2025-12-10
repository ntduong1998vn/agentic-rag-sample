from uuid import UUID
from typing import Optional

from langchain_core.tools import tool
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.services.document import DocumentService
from app.rag.vectorstores.s3_store import get_vector_store

from app.core.logging import get_logger

logger = get_logger(__name__)


def create_document_search_tool(
    collection_name: str,
    chatbot_id: UUID,
    conversation_id: Optional[UUID] = None,
):
    """
    Create a document-specific search tool.

    This tool allows searching for content within a specific document by filtering
    on the document_id metadata in vector store.

    Args:
        collection_name: The vector store collection name.
        chatbot_id: The chatbot ID to find documents for.
        conversation_id: Optional conversation ID for conversation-specific documents.

    Returns:
        A LangChain tool for searching within a specific document.
    """

    @tool
    def search_document_content(document_name: str, query: str) -> str:
        """
        Search for specific content within a particular document.
        Use this tool when the user asks about the content of a specific file or document.

        Args:
            document_name: The name or partial name of the document to search in.
            query: The search query to find relevant content within the document.

        Returns:
            Relevant content from the specified document, or a message if the document is not found.
        """
        try:
            db: Session = SessionLocal()
            try:
                # Find the document by name
                document_service = DocumentService(db)
                result = document_service.find_document_by_name(
                    chatbot_id=chatbot_id,
                    document_name=document_name,
                    conversation_id=conversation_id,
                )

                if result:
                    document_id, found_document_name = result
                else:
                    document_id = None
                    found_document_name = None

                if not document_id:
                    return f"Không tìm thấy tài liệu '{document_name}' hoặc tài liệu chưa được xử lý hoàn tất."

                # Search in vector store with document_id filter
                vector_store = get_vector_store(collection_name)

                docs = vector_store.similarity_search(
                    query,
                    k=6,
                    filter={"document_id": {"$eq": str(document_id)}},
                )
                # # Get base retriever with document filter
                # base_retriever = vector_store.as_retriever(
                #     search_type="similarity",
                #     search_kwargs={
                #         "k": 6,
                #         "filter": {"document_id": {"$eq": str(document_id)}},
                #     },
                # )

                # # Use enhanced retrieval with Multi-Query + Compression
                # docs = retrieve_with_enhanced_retriever(
                #     base_retriever=base_retriever,
                #     query=query,
                #     use_multi_query=True,
                #     use_compression=False,
                # )

                if not docs:
                    return f"Không tìm thấy thông tin liên quan đến '{query}' trong tài liệu '{found_document_name}'."

                # Format results
                results = [
                    f"Kết quả tìm kiếm trong tài liệu '{found_document_name}':\n"
                ]
                for i, doc in enumerate(docs, 1):
                    results.append(f"[Đoạn {i}]\n{doc.page_content}")

                return "\n\n---\n\n".join(results)

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Error searching document content: {e}")
            return f"Đã xảy ra lỗi khi tìm kiếm trong tài liệu: {str(e)}"

    return search_document_content
