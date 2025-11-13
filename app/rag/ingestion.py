import mimetypes
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import logging
from datetime import datetime

# LangChain imports
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Local imports
from app.rag.embeddings import get_embedding_service
from app.rag.vector_store import get_vector_store_service
from app.config.logging_config import get_logger

# Configure logging
logger = get_logger(__name__)


class DocumentIngestionService:
    """
    Service for ingesting documents into the RAG system using LangChain
    """

    def __init__(self, data_path: str = "data"):
        """
        Initialize the ingestion service

        Args:
            data_path: Path to the data directory containing documents
        """
        self.data_path = Path(data_path)

        # Create data directory if it doesn't exist
        if not self.data_path.exists():
            logger.info(f"Creating data directory: {self.data_path}")
            self.data_path.mkdir(parents=True, exist_ok=True)

        self.embedding_service = get_embedding_service()
        self.vector_store_service = get_vector_store_service()

        # Initialize LangChain text splitter for document chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )

        logger.info(f"Initialized DocumentIngestionService with data path: {self.data_path}")

    def _extract_file_metadata(self, file_path: Path) -> Dict[str, Any]:
        """
        Extract metadata from a file

        Args:
            file_path: Path to the file

        Returns:
            Dictionary with file metadata
        """
        try:
            stat = file_path.stat()
            return {
                "file_name": file_path.name,
                "file_path": str(file_path),
                "file_size": stat.st_size,
                "file_type": file_path.suffix.lower(),
                "created_at": datetime.fromtimestamp(stat.st_ctime),
                "modified_at": datetime.fromtimestamp(stat.st_mtime),
                "mime_type": mimetypes.guess_type(str(file_path))[0] or "unknown"
            }
        except Exception as e:
            logger.error(f"Failed to extract metadata for {file_path}: {str(e)}")
            return {
                "file_name": file_path.name,
                "file_path": str(file_path),
                "file_type": file_path.suffix.lower(),
                "error": str(e)
            }

    def _load_file_content(self, file_path: Path) -> Optional[str]:
        """
        Load content from a file based on its extension

        Args:
            file_path: Path to the file

        Returns:
            File content as string or None if failed
        """
        try:
            file_ext = file_path.suffix.lower()
            
            # Handle different file types
            if file_ext in ['.pdf']:
                # For PDF files, you would need a PDF reader
                # For now, treat as text file
                pass
            elif file_ext in ['.docx', '.doc']:
                # For Word documents, you would need python-docx
                # For now, treat as text file
                pass
            elif file_ext in ['.csv']:
                # Handle CSV files
                import csv
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    return content
            elif file_ext in ['.md', '.txt', '.py', '.js', '.ts', '.jsx', '.tsx', '.php', '.java', '.cpp', '.c', '.h']:
                # Text-based files
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                # Default: try to read as text
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
                    
        except UnicodeDecodeError:
            logger.warning(f"Could not decode file as UTF-8: {file_path}")
            return None
        except Exception as e:
            logger.error(f"Failed to load file content: {str(e)}")
            return None

    def _process_single_file(self, file_path: Path) -> Tuple[List[Document], Dict[str, Any]]:
        """
        Process a single file and return documents with metadata

        Args:
            file_path: Path to the file

        Returns:
            Tuple of (documents, metadata)
        """
        try:
            logger.info(f"Processing file: {file_path}")

            # Extract file metadata
            file_metadata = self._extract_file_metadata(file_path)

            # Load file content
            content = self._load_file_content(file_path)
            if not content:
                logger.warning(f"No content extracted from {file_path}")
                return [], {**file_metadata, "status": "no_content"}

            # Create document with metadata
            doc = Document(
                page_content=content,
                metadata={
                    **file_metadata,
                    "id": f"{file_path.stem}_{hash(content) % 10000}"
                }
            )

            # Split document into chunks using LangChain text splitter
            try:
                chunks = self.text_splitter.split_documents([doc])
                logger.info(f"Text splitting created {len(chunks)} chunks from 1 document")
            except Exception as e:
                error_msg = f"Text splitting failed for {file_path}: {str(e)}"
                logger.error(error_msg)
                # If splitting fails, use the original document as a single chunk
                chunks = [doc]

            logger.info(f"Processed {file_path}: 1 document -> {len(chunks)} chunks")

            return chunks, {**file_metadata, "status": "success", "chunk_count": len(chunks)}

        except Exception as e:
            logger.error(f"Failed to process {file_path}: {str(e)}")
            file_metadata = self._extract_file_metadata(file_path)
            return [], {**file_metadata, "status": "error", "error_message": str(e)}

    async def ingest_directory(self, recursive: bool = True) -> Dict[str, Any]:
        """
        Ingest all documents from the data directory

        Args:
            recursive: Whether to search subdirectories recursively

        Returns:
            Dictionary with ingestion results
        """
        start_time = datetime.now()
        logger.info(f"Starting ingestion from {self.data_path}")

        # Check if data directory exists
        if not self.data_path.exists():
            logger.error(f"Data directory does not exist: {self.data_path}")
            return {
                "success": False,
                "message": f"Data directory does not exist: {self.data_path}",
                "stats": {}
            }

        # Find all files to process
        if recursive:
            files = list(self.data_path.rglob("*"))
        else:
            files = list(self.data_path.glob("*"))

        # Filter to files only (not directories)
        files = [f for f in files if f.is_file()]

        if not files:
            logger.warning(f"No files found in {self.data_path}")
            return {
                "success": True,
                "message": "No files to process",
                "stats": {
                    "total_files": 0,
                    "processed_files": 0,
                    "failed_files": 0,
                    "skipped_files": 0
                }
            }

        logger.info(f"Found {len(files)} files to process")

        # Process all files
        all_documents = []
        processing_results = []

        for file_path in files:
            documents, metadata = self._process_single_file(file_path)
            all_documents.extend(documents)
            processing_results.append(metadata)

        # Calculate statistics
        stats = {
            "total_files": len(files),
            "processed_files": len([r for r in processing_results if r.get("status") == "success"]),
            "failed_files": len([r for r in processing_results if r.get("status") == "error"]),
            "skipped_files": len([r for r in processing_results if r.get("status") in ["no_content", "skipped"]]),
            "total_chunks": len(all_documents),
            "start_time": start_time,
            "end_time": datetime.now()
        }

        # Add documents to vector store if any were processed
        if all_documents:
            try:
                logger.info(f"Adding {len(all_documents)} chunks to vector store")
                await self.vector_store_service.add_documents(all_documents)
                logger.info("Successfully added documents to vector store")
            except Exception as e:
                logger.error(f"Failed to add documents to vector store: {str(e)}")
                stats["vector_store_error"] = str(e)

        duration = stats["end_time"] - stats["start_time"]
        logger.info(f"Ingestion completed in {duration}: {stats}")

        return {
            "success": True,
            "message": f"Processed {stats['processed_files']}/{stats['total_files']} files successfully",
            "stats": stats,
            "processing_results": processing_results
        }

    def get_supported_file_types(self) -> List[str]:
        """
        Get list of supported file extensions

        Returns:
            List of supported file extensions
        """
        return ['.pdf', '.docx', '.doc', '.csv', '.md', '.txt', '.py', '.js', '.ts', '.jsx', '.tsx', '.php', '.java', '.cpp', '.c', '.h']


# Global ingestion service instance
_ingestion_service: Optional[DocumentIngestionService] = None


def get_ingestion_service() -> DocumentIngestionService:
    """
    Get the global ingestion service instance

    Returns:
        DocumentIngestionService instance
    """
    global _ingestion_service
    if _ingestion_service is None:
        _ingestion_service = DocumentIngestionService()
    return _ingestion_service