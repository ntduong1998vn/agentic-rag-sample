"""
Document processor service.

This module handles loading, chunking, embedding, and storing documents.
"""

import logging
from typing import List, Dict, Any, Optional
import uuid
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.domain.knowledge_base.entities import Document, DocumentChunk, KnowledgeBase
from app.domain.knowledge_base.ports import VectorStorePort
from app.infrastructure.embeddings import get_embedding_service
from app.config import settings

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Service for processing documents."""
    
    def __init__(self, vector_store: VectorStorePort):
        """
        Initialize document processor.
        
        Args:
            vector_store: Vector store implementation for storing embeddings
        """
        self.vector_store = vector_store
        self.embedding_service = get_embedding_service()
        
        # Configure text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.semantic_max_tokens_per_chunk,
            chunk_overlap=settings.semantic_token_overlap,
            length_function=len,
            is_separator_regex=False,
        )
    
    async def process_document(self, document: Document, knowledge_base: KnowledgeBase) -> List[DocumentChunk]:
        """
        Process a document: load, chunk, embed, and store.
        
        Args:
            document: Document entity to process
            knowledge_base: Knowledge base the document belongs to
            
        Returns:
            List of created DocumentChunk entities
        """
        try:
            # 1. Load content
            content = self._load_content(document.file_path)
            if not content:
                logger.warning(f"No content extracted from {document.file_path}")
                return []
            
            # 2. Create chunks
            text_chunks = self.text_splitter.split_text(content)
            logger.info(f"Created {len(text_chunks)} chunks for {document.file_name}")
            
            if not text_chunks:
                return []
            
            # 3. Generate embeddings
            embeddings = await self.embedding_service.get_embeddings(text_chunks)
            
            # 4. Prepare vectors and DocumentChunk entities
            vectors = []
            document_chunks = []
            
            for i, (text, embedding) in enumerate(zip(text_chunks, embeddings)):
                chunk_id = uuid.uuid4()
                vector_id = str(chunk_id)
                
                # Prepare vector data for storage
                vector_data = {
                    "id": vector_id,
                    "vector": embedding,
                    "payload": {
                        "document_id": str(document.id),
                        "knowledge_base_id": str(knowledge_base.id),
                        "file_name": document.file_name,
                        "file_path": document.file_path,
                        "chunk_index": i,
                        "content": text,
                        "metadata": {
                            "file_type": document.file_type,
                            "file_size": document.file_size
                        }
                    }
                }
                vectors.append(vector_data)
                
                # Create DocumentChunk entity
                chunk = DocumentChunk(
                    id=chunk_id,
                    document_id=document.id,
                    chunk_index=i,
                    content=text,
                    chunk_size=len(text),
                    vector_id=vector_id
                )
                document_chunks.append(chunk)
            
            # 5. Store in vector database
            await self.vector_store.store_vectors(
                collection_name=knowledge_base.collection_name,
                vectors=vectors
            )
            
            return document_chunks
            
        except Exception as e:
            logger.error(f"Error processing document {document.id}: {e}")
            raise
            
    def _load_content(self, file_path: str) -> str:
        """
        Load text content from file.
        
        Currently supports text-based files. 
        TODO: Add support for PDF, DOCX, etc. using LangChain loaders.
        """
        path = Path(file_path)
        
        # Simple text loading for now
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            raise
            
    async def delete_document_vectors(self, document: Document, knowledge_base: KnowledgeBase) -> None:
        """Delete vectors for a document from vector store."""
        try:
            await self.vector_store.delete_vectors(
                collection_name=knowledge_base.collection_name,
                filter_criteria={"document_id": str(document.id)}
            )
        except Exception as e:
            logger.error(f"Error deleting vectors for document {document.id}: {e}")
            # Don't raise here, just log error
