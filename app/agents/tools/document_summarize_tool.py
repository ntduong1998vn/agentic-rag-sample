"""Tool for summarizing document content from the knowledge base."""

from uuid import UUID
from typing import Optional

from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.chains import load_summarize_chain
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.services.document import DocumentService
from app.rag.vectorstores.s3_store import get_vector_store
from app.core.config import settings
from app.core.logging import get_logger
from app.agents.prompts import DOCUMENT_REDUCE_PROMPT

logger = get_logger(__name__)


def get_summarize_llm() -> ChatGoogleGenerativeAI:
    """Get a configured LLM for summarization."""
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-lite",
        google_api_key=settings.google_api_key,
        temperature=0.3,
    )


def create_document_summarize_tool(
    collection_name: str,
    chatbot_id: UUID,
    conversation_id: Optional[UUID] = None,
):
    """
    Create a document summarization tool.

    This tool allows summarizing the entire content of a specific document
    by loading all chunks from the vector store and using load_summarize_chain.

    Args:
        collection_name: The vector store collection name.
        chatbot_id: The chatbot ID to find documents for.
        conversation_id: Optional conversation ID for conversation-specific documents.

    Returns:
        A LangChain tool for summarizing a specific document.
    """

    @tool
    def summarize_document(document_name: str) -> str:
        """
        Summarize the entire content of a specific document.
        Use this tool when the user asks for a summary of a particular file or document.

        Args:
            document_name: The name or partial name of the document to summarize.

        Returns:
            A summary of the document content, or a message if the document is not found.
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

                # Load all chunks for the document from vector store
                vector_store = get_vector_store(collection_name)

                # Use a high k value to get all chunks for the document
                docs = vector_store.similarity_search(
                    query=" ",
                    k=100,
                    filter={"document_id": {"$eq": str(document_id)}},
                )

                if not docs:
                    return f"Không tìm thấy nội dung nào cho tài liệu '{found_document_name}'."

                # Sort by chunk_index for proper order
                docs.sort(key=lambda x: x.metadata.get("chunk_index", 0))

                logger.info(
                    f"Loaded {len(docs)} chunks for document '{found_document_name}' (ID: {document_id})"
                )

                # Merge chunks based on file extension
                file_name = found_document_name.lower()

                if file_name.endswith((".xlsx", ".xls")):
                    # Merge chunks by page_name for Excel files
                    logger.info("Merging chunks by page_name for Excel file")
                    merged_chunks = {}

                    for doc in docs:
                        page_name = doc.metadata.get("page_name", "unknown")
                        if page_name in merged_chunks:
                            # Append content to existing page
                            merged_chunks[page_name]["content"] += (
                                "\n\n" + doc.page_content
                            )
                        else:
                            # Create new entry for this page
                            merged_chunks[page_name] = {
                                "content": doc.page_content,
                                "metadata": doc.metadata.copy(),
                            }

                    # Convert merged chunks back to Document objects

                    docs = [
                        Document(
                            page_content=chunk_data["content"],
                            metadata=chunk_data["metadata"],
                        )
                        for page_name, chunk_data in merged_chunks.items()
                    ]
                    logger.info(f"Merged into {len(docs)} chunks by page_name")

                elif file_name.endswith(".pdf"):
                    # Merge chunks by page_number for PDF files
                    logger.info("Merging chunks by page_number for PDF file")
                    merged_chunks = {}

                    for doc in docs:
                        page_number = doc.metadata.get("page_number", 0)
                        if page_number in merged_chunks:
                            # Append content to existing page
                            merged_chunks[page_number]["content"] += (
                                "\n\n" + doc.page_content
                            )
                        else:
                            # Create new entry for this page
                            merged_chunks[page_number] = {
                                "content": doc.page_content,
                                "metadata": doc.metadata.copy(),
                            }

                    # Convert merged chunks back to Document objects, sorted by page number

                    docs = [
                        Document(
                            page_content=chunk_data["content"],
                            metadata=chunk_data["metadata"],
                        )
                        for page_number, chunk_data in sorted(merged_chunks.items())
                    ]
                    logger.info(f"Merged into {len(docs)} chunks by page_number")

                # Use load_summarize_chain with map_reduce for handling many chunks
                llm = get_summarize_llm()

                # Create custom combine prompt for detailed summaries
                combine_prompt = PromptTemplate(
                    template=DOCUMENT_REDUCE_PROMPT, input_variables=["text"]
                )

                chain = load_summarize_chain(
                    llm, chain_type="map_reduce", combine_prompt=combine_prompt
                )

                # Run the summarization chain
                summary_result = chain.invoke(docs)

                # Extract the output text from the result
                if isinstance(summary_result, dict):
                    summary_text = summary_result.get(
                        "output_text", str(summary_result)
                    )
                else:
                    summary_text = str(summary_result)

                return f"Tóm tắt tài liệu '{found_document_name}':\n\n{summary_text}"

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Error summarizing document: {e}")
            return f"Đã xảy ra lỗi khi tóm tắt tài liệu: {str(e)}"

    return summarize_document
