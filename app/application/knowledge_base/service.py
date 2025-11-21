"""
Knowledge base application service.

This module implements the use cases for knowledge base management and document ingestion.
"""

import logging
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.domain.knowledge_base.entities import KnowledgeBase, Document, DocumentChunk, DocumentStatus
from app.domain.knowledge_base.ports import (
    KnowledgeBaseRepositoryPort, 
    DocumentRepositoryPort, 
    DocumentChunkRepositoryPort,
    VectorStorePort
)
from app.domain.chatbot.ports import ChatbotRepository
from app.infrastructure.document_scanner import DocumentScanner
from app.infrastructure.document_processor import DocumentProcessor

logger = logging.getLogger(__name__)


class KnowledgeBaseService:
    """Service for knowledge base operations."""
    
    def __init__(
        self,
        kb_repository: KnowledgeBaseRepositoryPort,
        doc_repository: DocumentRepositoryPort,
        chunk_repository: DocumentChunkRepositoryPort,
        chatbot_repository: ChatbotRepository,
        vector_store: VectorStorePort,
        document_scanner: DocumentScanner,
        document_processor: DocumentProcessor
    ):
        self.kb_repository = kb_repository
        self.doc_repository = doc_repository
        self.chunk_repository = chunk_repository
        self.chatbot_repository = chatbot_repository
        self.vector_store = vector_store
        self.document_scanner = document_scanner
        self.document_processor = document_processor
    
    async def get_knowledge_base(self, chatbot_id: uuid.UUID) -> Optional[KnowledgeBase]:
        """Get knowledge base for a chatbot."""
        return await self.kb_repository.get_by_chatbot_id(chatbot_id)
    
    async def get_or_create_knowledge_base(self, chatbot_id: uuid.UUID) -> KnowledgeBase:
        """Get existing knowledge base or create a new one."""
        kb = await self.kb_repository.get_by_chatbot_id(chatbot_id)
        if kb:
            return kb
            
        # Verify chatbot exists
        chatbot = await self.chatbot_repository.get_by_id(chatbot_id)
        if not chatbot:
            raise ValueError(f"Chatbot with id {chatbot_id} not found")
            
        # Create new knowledge base
        collection_name = f"kb_{str(chatbot_id).replace('-', '_')}"
        vector_dimension = 1024  # Voyage-3 dimension
        
        # Ensure vector store collection exists
        await self.vector_store.create_collection(
            collection_name=collection_name,
            vector_dimension=vector_dimension
        )
        
        kb = KnowledgeBase(
            chatbot_id=chatbot_id,
            collection_name=collection_name,
            vector_dimension=vector_dimension
        )
        
        return await self.kb_repository.create(kb)
    
    async def ingest_documents(self, chatbot_id: uuid.UUID, folder_path: str = "data") -> Dict[str, Any]:
        """
        Ingest documents from a folder into the chatbot's knowledge base.
        
        Args:
            chatbot_id: ID of the chatbot
            folder_path: Path to the folder to scan (default: "data")
            
        Returns:
            Ingestion statistics
        """
        # 1. Get/Create Knowledge Base
        kb = await self.get_or_create_knowledge_base(chatbot_id)
        
        # 2. Scan documents
        logger.info(f"Scanning folder {folder_path} for chatbot {chatbot_id}")
        file_infos = self.document_scanner.scan_directory(folder_path)
        
        if not file_infos:
            return {
                "status": "completed",
                "message": "No files found to ingest",
                "files_found": 0,
                "files_ingested": 0
            }
            
        # 3. Register documents in database
        documents_to_process = []
        
        for file_info in file_infos:
            # Check for existing document
            existing_doc = await self.doc_repository.get_by_checksum(kb.id, file_info.checksum)
            
            if existing_doc:
                if existing_doc.status == DocumentStatus.COMPLETED:
                    logger.info(f"Skipping existing document: {file_info.file_name}")
                    continue
                elif existing_doc.status == DocumentStatus.FAILED:
                    # Retry failed document
                    logger.info(f"Retrying failed document: {file_info.file_name}")
                    existing_doc.status = DocumentStatus.PENDING
                    existing_doc.error_message = None
                    await self.doc_repository.update(existing_doc)
                    documents_to_process.append(existing_doc)
                else:
                    # Pending or processing, add to list
                    documents_to_process.append(existing_doc)
            else:
                # Create new document
                new_doc = Document(
                    knowledge_base_id=kb.id,
                    file_path=file_info.file_path,
                    file_name=file_info.file_name,
                    file_size=file_info.file_size,
                    file_type=file_info.file_type,
                    checksum=file_info.checksum
                )
                created_doc = await self.doc_repository.create(new_doc)
                documents_to_process.append(created_doc)
        
        logger.info(f"Found {len(documents_to_process)} documents to process")
        
        # 4. Process documents
        processed_count = 0
        failed_count = 0
        total_chunks_added = 0
        
        for doc in documents_to_process:
            try:
                # Update status to processing
                doc.start_processing()
                await self.doc_repository.update(doc)
                
                # Process document
                chunks = await self.document_processor.process_document(doc, kb)
                
                # Save chunks to DB
                if chunks:
                    await self.chunk_repository.create_many(chunks)
                
                # Update status to completed
                doc.mark_completed(len(chunks))
                await self.doc_repository.update(doc)
                
                processed_count += 1
                total_chunks_added += len(chunks)
                
            except Exception as e:
                logger.error(f"Failed to process document {doc.file_name}: {e}")
                doc.mark_failed(str(e))
                await self.doc_repository.update(doc)
                failed_count += 1
        
        # 5. Update Knowledge Base stats
        kb.increment_document_count(total_chunks_added)
        await self.kb_repository.update(kb)
        
        return {
            "status": "completed",
            "knowledge_base_id": kb.id,
            "collection_name": kb.collection_name,
            "files_found": len(file_infos),
            "files_processed": processed_count,
            "files_failed": failed_count,
            "total_chunks": total_chunks_added
        }
    
    async def list_documents(
        self, 
        chatbot_id: uuid.UUID, 
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Document]:
        """List documents in chatbot's knowledge base."""
        kb = await self.kb_repository.get_by_chatbot_id(chatbot_id)
        if not kb:
            return []
            
        return await self.doc_repository.list_by_knowledge_base(
            knowledge_base_id=kb.id,
            status=status,
            skip=skip,
            limit=limit
        )
    
    async def get_stats(self, chatbot_id: uuid.UUID) -> Dict[str, Any]:
        """Get knowledge base statistics."""
        kb = await self.kb_repository.get_by_chatbot_id(chatbot_id)
        if not kb:
            return {"status": "not_found"}
            
        # Get vector store stats
        vector_stats = self.vector_store.get_collection_stats(kb.collection_name)
        
        # Get DB stats
        pending_count = await self.doc_repository.count_by_status(kb.id, DocumentStatus.PENDING)
        processing_count = await self.doc_repository.count_by_status(kb.id, DocumentStatus.PROCESSING)
        completed_count = await self.doc_repository.count_by_status(kb.id, DocumentStatus.COMPLETED)
        failed_count = await self.doc_repository.count_by_status(kb.id, DocumentStatus.FAILED)
        
        return {
            "knowledge_base": {
                "id": kb.id,
                "collection_name": kb.collection_name,
                "total_documents": kb.total_documents,
                "total_chunks": kb.total_chunks,
                "updated_at": kb.updated_at
            },
            "documents": {
                "pending": pending_count,
                "processing": processing_count,
                "completed": completed_count,
                "failed": failed_count
            },
            "vector_store": vector_stats
        }
