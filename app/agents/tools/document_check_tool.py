"""Tool for checking document existence in the knowledge base."""

from uuid import UUID
from typing import Optional

from langchain_core.tools import tool
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.document import Document
from app.models.conversation_document import ConversationDocument
from app.models.knowledge_base import KnowledgeBase
from app.models.conversation import Conversation
from app.core.logging import get_logger

logger = get_logger(__name__)


def create_document_check_tool(chatbot_id: UUID, conversation_id: Optional[UUID] = None):
    """
    Create a document check tool bound to a specific chatbot and conversation.
    
    Args:
        chatbot_id: The chatbot ID to check documents for.
        conversation_id: Optional conversation ID to also check conversation-specific documents.
    
    Returns:
        A LangChain tool for checking document existence.
    """

    @tool
    def check_document_exists(document_name: str) -> str:
        """
        Check if a document with the given name exists in the chatbot's knowledge base.
        Use this tool when the user asks about a specific document or wants to know
        if a particular document is available.

        Args:
            document_name: The name or partial name of the document to check.

        Returns:
            A message indicating whether the document exists or not.
        """
        try:
            db: Session = SessionLocal()
            try:
                found_documents = []
                
                # Search in documents table (via knowledge_base)
                knowledge_bases = db.query(KnowledgeBase).filter(
                    KnowledgeBase.chatbot_id == chatbot_id
                ).all()
                
                for kb in knowledge_bases:
                    documents = db.query(Document).filter(
                        Document.knowledge_base_id == kb.id,
                        Document.file_name.ilike(f"%{document_name}%")
                    ).all()
                    
                    for doc in documents:
                        found_documents.append({
                            "name": doc.file_name,
                            "type": "knowledge_base",
                            "status": doc.status,
                        })
                
                # Search in conversation_documents table if conversation_id is provided
                if conversation_id:
                    conv_documents = db.query(ConversationDocument).filter(
                        ConversationDocument.conversation_id == conversation_id,
                        ConversationDocument.file_name.ilike(f"%{document_name}%")
                    ).all()
                    
                    for doc in conv_documents:
                        found_documents.append({
                            "name": doc.file_name,
                            "type": "conversation",
                            "status": doc.status,
                        })
                else:
                    # If no conversation_id, check all conversations for this chatbot
                    conversations = db.query(Conversation).filter(
                        Conversation.chatbot_id == chatbot_id
                    ).all()
                    
                    for conv in conversations:
                        conv_documents = db.query(ConversationDocument).filter(
                            ConversationDocument.conversation_id == conv.id,
                            ConversationDocument.file_name.ilike(f"%{document_name}%")
                        ).all()
                        
                        for doc in conv_documents:
                            found_documents.append({
                                "name": doc.file_name,
                                "type": "conversation",
                                "status": doc.status,
                            })
                
                if found_documents:
                    # Format the response
                    result_lines = [f"Có, tôi tìm thấy {len(found_documents)} tài liệu phù hợp:"]
                    for doc in found_documents:
                        source_type = "Knowledge Base" if doc["type"] == "knowledge_base" else "Cuộc hội thoại"
                        result_lines.append(f"- {doc['name']} (Nguồn: {source_type}, Trạng thái: {doc['status']})")
                    
                    return "\n".join(result_lines)
                else:
                    return f"Không, tôi không tìm thấy tài liệu nào có tên '{document_name}' trong hệ thống của chatbot này."
                    
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error checking document existence: {e}")
            return f"Đã xảy ra lỗi khi kiểm tra tài liệu: {str(e)}"

    return check_document_exists
