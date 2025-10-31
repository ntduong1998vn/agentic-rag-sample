import mimetypes
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import logging
from datetime import datetime

# LlamaIndex imports
from llama_index.core import Document
from llama_index.core.readers import SimpleDirectoryReader
from llama_index.readers.file import (
    PDFReader,
    DocxReader,
    CSVReader,
    EpubReader,
    MarkdownReader,
    ImageReader,
)
from llama_index.core.text_splitter import TokenTextSplitter

# Local imports
from app.rag.embeddings import get_embedding_service
from app.rag.vector_store import get_vector_store_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JapaneseSentenceSplitter(TokenTextSplitter):
    """
    Custom text splitter optimized for Japanese text with semantic awareness
    """

    def __init__(self,
                 chunk_size: int = 512,
                 chunk_overlap: int = 50,
                 separators: Optional[List[str]] = None):
        """
        Initialize Japanese sentence splitter

        Args:
            chunk_size: Maximum size of each chunk in tokens
            chunk_overlap: Number of tokens to overlap between chunks
            separators: List of sentence separators
        """
        super().__init__(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

        # Japanese sentence separators and semantic break points
        if separators is None:
            self.separators = [
                "。",  # Japanese period
                "！",  # Japanese exclamation mark
                "？",  # Japanese question mark
                "．",  # Fullwidth period
                "\n\n",  # Paragraph break
                "\n",    # Line break
                "、",    # Japanese comma
                "，",    # Fullwidth comma
                "：",    # Japanese colon
                "；",    # Japanese semicolon
            ]
        else:
            self.separators = separators

    def split_text(self, text: str) -> List[str]:
        """
        Split text into chunks using Japanese semantic rules

        Args:
            text: Text to split

        Returns:
            List of text chunks
        """
        if not text.strip():
            return []

        # Preprocess text
        text = text.strip()
        chunks = []

        # Find all natural break points
        break_positions = [0]  # Start of text

        for separator in self.separators:
            pos = 0
            while True:
                pos = text.find(separator, pos)
                if pos == -1:
                    break
                break_positions.append(pos + len(separator))
                pos += len(separator)

        # Add end of text
        break_positions.append(len(text))

        # Remove duplicates and sort
        break_positions = sorted(list(set(break_positions)))

        # Create segments based on break positions
        segments = []
        for i in range(len(break_positions) - 1):
            start = break_positions[i]
            end = break_positions[i + 1]
            segment = text[start:end].strip()
            if segment:
                segments.append(segment)

        # Combine segments into chunks respecting chunk_size
        current_chunk = ""
        for segment in segments:
            # If adding this segment exceeds chunk_size, start new chunk
            if len(current_chunk) + len(segment) > self.chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = segment
            else:
                current_chunk += segment

        # Add final chunk if not empty
        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        # Ensure chunks are not too small (merge very small chunks)
        final_chunks = []
        temp_chunk = ""

        for chunk in chunks:
            if len(chunk) < self.chunk_size // 4 and temp_chunk:  # Very small chunk
                temp_chunk += chunk
            else:
                if temp_chunk:
                    final_chunks.append(temp_chunk)
                temp_chunk = chunk

        if temp_chunk:
            final_chunks.append(temp_chunk)

        return final_chunks


class DocumentIngestionService:
    """
    Service for ingesting documents into the RAG system
    """

    def __init__(self, data_path: str = "data"):
        """
        Initialize the ingestion service

        Args:
            data_path: Path to the data directory containing documents
        """
        self.data_path = Path(data_path)
        self.embedding_service = get_embedding_service()
        self.vector_store_service = get_vector_store_service()

        # Initialize file readers
        self.readers = {
            ".pdf": PDFReader(),
            ".docx": DocxReader(),
            ".doc": DocxReader(),
            ".csv": CSVReader(),
            ".epub": EpubReader(),
            ".md": MarkdownReader(),
            ".txt": SimpleDirectoryReader(input_files=[""]),
            # Image files
            ".jpg": ImageReader(),
            ".jpeg": ImageReader(),
            ".png": ImageReader(),
            ".gif": ImageReader(),
            ".bmp": ImageReader(),
            ".tiff": ImageReader(),
        }

        # Japanese sentence splitter
        self.text_splitter = JapaneseSentenceSplitter(
            chunk_size=512,
            chunk_overlap=50
        )

        logger.info(f"Initialized DocumentIngestionService with data path: {self.data_path}")

    def _get_file_reader(self, file_path: Path):
        """
        Get the appropriate reader for a file type

        Args:
            file_path: Path to the file

        Returns:
            File reader instance
        """
        file_extension = file_path.suffix.lower()

        if file_extension in self.readers:
            return self.readers[file_extension]
        else:
            # Default to text reader for unsupported files
            logger.warning(f"No specific reader for {file_extension}, using default text reader")
            return SimpleDirectoryReader(input_files=[str(file_path)])

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

            # Get appropriate reader
            reader = self._get_file_reader(file_path)

            # Load documents
            if isinstance(reader, SimpleDirectoryReader):
                # For SimpleDirectoryReader, we need to specify the file
                temp_reader = SimpleDirectoryReader(input_files=[str(file_path)])
                documents = temp_reader.load_data()
            else:
                # For specialized readers
                documents = reader.load_data(file_path)

            if not documents:
                logger.warning(f"No content extracted from {file_path}")
                return [], {**file_metadata, "status": "no_content"}

            # Add file metadata to all documents
            for doc in documents:
                doc.metadata = {**doc.metadata, **file_metadata}

            # Split documents into chunks using Japanese semantic splitter
            chunked_documents = []
            for doc in documents:
                chunks = self.text_splitter.split_text(doc.text)
                for i, chunk in enumerate(chunks):
                    chunk_doc = Document(
                        text=chunk,
                        doc_id=f"{file_path.stem}_chunk_{i}",
                        metadata={
                            **doc.metadata,
                            "chunk_index": i,
                            "total_chunks": len(chunks),
                            "chunk_text": chunk
                        }
                    )
                    chunked_documents.append(chunk_doc)

            logger.info(f"Processed {file_path}: {len(documents)} documents -> {len(chunked_documents)} chunks")

            return chunked_documents, {**file_metadata, "status": "success", "chunk_count": len(chunked_documents)}

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
                self.vector_store_service.save_index()
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
        return list(self.readers.keys())


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