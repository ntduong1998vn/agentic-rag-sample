"""
Ingestion service orchestrating the full document ingestion pipeline.
"""

from typing import List
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.services.knowledge_base import KnowledgeBaseService
from app.services.document_scanner import DocumentScanner
from app.services.document import DocumentService, DocumentStatus
from app.rag.pipelines.document_processor import DocumentProcessor
from app.rag.vectorstores.s3_store import (
    ensure_index_exists,
    add_documents_to_index,
    delete_document_vectors,
)

logger = get_logger(__name__)


class IngestionResult:
    """Result of an ingestion operation."""

    def __init__(self):
        self.documents_registered: int = 0
        self.documents_processed: int = 0
        self.errors: List[str] = []

    @property
    def status(self) -> str:
        """Get overall status based on results."""
        if not self.errors:
            return "success"
        elif self.documents_processed > 0:
            return "partial"
        else:
            return "failed"


class IngestionService:
    """Service for orchestrating document ingestion."""

    def __init__(self, db: Session):
        self.db = db
        self.knowledge_base_service = KnowledgeBaseService(db)
        self.document_service = DocumentService(db)
        self.document_scanner = DocumentScanner()
        self.document_processor = DocumentProcessor()

    def ingest_for_chatbot(
        self, chatbot_id: UUID, folder_path: str = "./data"
    ) -> IngestionResult:
        """
        Ingest documents from a folder for a specific chatbot.

        This is a two-step process:
        1. Check/create knowledge base, scan folder, register documents in DB
        2. Process pending documents (chunk → embed → store in Qdrant)

        Args:
            chatbot_id: ID of the chatbot
            folder_path: Path to folder containing documents

        Returns:
            IngestionResult with statistics and any errors
        """
        result = IngestionResult()

        logger.info(
            f"Starting ingestion for chatbot {chatbot_id} from folder {folder_path}"
        )

        # Step 1: Get or create knowledge base
        try:
            knowledge_base = self.knowledge_base_service.get_or_create_for_chatbot(
                chatbot_id
            )
            logger.info(f"Using knowledge base: {knowledge_base.collection_name}")
        except Exception as e:
            error_msg = f"Failed to get/create knowledge base: {str(e)}"
            logger.error(error_msg)
            result.errors.append(error_msg)
            return result

        # Step 1b: Ensure S3 Vectors index exists
        try:
            ensure_index_exists(
                knowledge_base.collection_name, knowledge_base.vector_dimension
            )
        except Exception as e:
            error_msg = f"Failed to create S3 Vectors index: {str(e)}"
            logger.error(error_msg)
            result.errors.append(error_msg)
            return result

        # Step 1c: Scan folder and register documents
        try:
            files = self.document_scanner.scan_folder(folder_path)
            if not files:
                logger.warning(f"No supported files found in {folder_path}")
            else:
                result.documents_registered = self.document_service.register_documents(
                    knowledge_base.id, files
                )
                logger.info(f"Registered {result.documents_registered} new documents")
        except Exception as e:
            error_msg = f"Failed to scan/register documents: {str(e)}"
            logger.error(error_msg)
            result.errors.append(error_msg)
            # Continue to process any existing pending documents

        # Step 2: Process pending documents
        pending_documents = self.document_service.get_pending_documents(
            knowledge_base.id
        )
        logger.info(f"Found {len(pending_documents)} pending documents to process")

        for document in pending_documents:
            try:
                processed = self._process_document(
                    document, knowledge_base.collection_name
                )
                if processed:
                    result.documents_processed += 1
            except Exception as e:
                error_msg = f"Failed to process {document.file_name}: {str(e)}"
                logger.error(error_msg)
                result.errors.append(error_msg)

                # Update document status to failed
                self.document_service.update_status(
                    document.id, DocumentStatus.FAILED, error_message=str(e)
                )

        # Update knowledge base stats
        self._update_knowledge_base_stats(knowledge_base.id)

        logger.info(
            f"Ingestion complete: {result.documents_registered} registered, "
            f"{result.documents_processed} processed, {len(result.errors)} errors"
        )

        return result

    def _process_document(self, document, collection_name: str) -> bool:
        """
        Process a single document: chunk, embed, store.

        Args:
            document: Document model instance
            collection_name: Qdrant collection name

        Returns:
            True if processing was successful
        """
        logger.info(f"Processing document: {document.file_name}")

        # Update status to processing
        self.document_service.update_status(document.id, DocumentStatus.PROCESSING)

        try:
            # Delete any existing vectors for this document (in case of re-processing)
            delete_document_vectors(collection_name, document.id)

            # Process file into chunks
            chunks = self.document_processor.process_file(
                document.file_path, document.file_name
            )

            if not chunks:
                logger.warning(f"No chunks created from {document.file_name}")
                self.document_service.update_status(
                    document.id, DocumentStatus.COMPLETE, chunks_count=0
                )
                return True

            # Add chunks to S3 Vectors
            chunks_added = add_documents_to_index(collection_name, chunks, document.id)

            # Update document status to complete
            self.document_service.update_status(
                document.id, DocumentStatus.COMPLETE, chunks_count=chunks_added
            )

            logger.info(
                f"Successfully processed {document.file_name}: {chunks_added} chunks"
            )
            return True

        except Exception as e:
            logger.error(f"Error processing {document.file_name}: {e}")
            self.document_service.update_status(
                document.id, DocumentStatus.FAILED, error_message=str(e)
            )
            raise

    def _update_knowledge_base_stats(self, knowledge_base_id: UUID) -> None:
        """Update knowledge base statistics after ingestion."""
        documents = self.document_service.get_by_knowledge_base(knowledge_base_id)

        total_documents = len(
            [d for d in documents if d.status == DocumentStatus.COMPLETE]
        )
        total_chunks = sum(
            d.chunks_count for d in documents if d.status == DocumentStatus.COMPLETE
        )

        self.knowledge_base_service.update_stats(
            knowledge_base_id, total_documents, total_chunks
        )
        logger.debug(
            f"Updated knowledge base stats: {total_documents} docs, {total_chunks} chunks"
        )
