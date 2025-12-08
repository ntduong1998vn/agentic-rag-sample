"""Tool for searching content within a specific document."""

from uuid import UUID
from typing import Optional

from langchain_core.tools import tool
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.document import Document
from app.models.conversation_document import ConversationDocument
from app.models.knowledge_base import KnowledgeBase
from app.rag.vectorstores.qdrant_store import get_vector_store
from app.core.logging import get_logger
from qdrant_client.http import models as qdrant_models

logger = get_logger(__name__)


def create_document_search_tool(
    collection_name: str,
    chatbot_id: UUID,
    conversation_id: Optional[UUID] = None,
):
    """
    Create a document-specific search tool.

    This tool allows searching for content within a specific document by filtering
    on the document_id metadata in Qdrant.

    Args:
        collection_name: The Qdrant collection name.
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
                document_id = None
                found_document_name = None

                # Search in documents table (via knowledge_base)
                knowledge_bases = (
                    db.query(KnowledgeBase)
                    .filter(KnowledgeBase.chatbot_id == chatbot_id)
                    .all()
                )

                for kb in knowledge_bases:
                    documents = (
                        db.query(Document)
                        .filter(
                            Document.knowledge_base_id == kb.id,
                            Document.file_name.ilike(f"%{document_name}%"),
                            Document.status
                            == "complete",  # Only search in completed documents
                        )
                        .all()
                    )

                    if documents:
                        # Use the first match
                        document_id = documents[0].id
                        found_document_name = documents[0].file_name
                        break

                # If not found in knowledge base, search in conversation documents
                if not document_id and conversation_id:
                    conv_documents = (
                        db.query(ConversationDocument)
                        .filter(
                            ConversationDocument.conversation_id == conversation_id,
                            ConversationDocument.file_name.ilike(f"%{document_name}%"),
                            ConversationDocument.status == "complete",
                        )
                        .all()
                    )

                    if conv_documents:
                        document_id = conv_documents[0].id
                        found_document_name = conv_documents[0].file_name
                        # Note: conversation documents may use different collection
                        # We'll use the one passed in for now

                if not document_id:
                    return f"Không tìm thấy tài liệu '{document_name}' hoặc tài liệu chưa được xử lý hoàn tất."

                # Search in Qdrant with document_id filter
                vector_store = get_vector_store(collection_name)

                # Create filter for the specific document
                search_kwargs = {
                    "k": 4,
                    "filter": qdrant_models.Filter(
                        must=[
                            qdrant_models.FieldCondition(
                                key="metadata.document_id",
                                match=qdrant_models.MatchValue(value=str(document_id)),
                            )
                        ]
                    ),
                }

                # Perform similarity search with filter
                docs = vector_store.similarity_search(query, **search_kwargs)

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
