"""
Document processor for loading, chunking, and preparing documents for embedding.
"""

from pathlib import Path
from typing import List

from langchain_core.documents import Document as LangchainDocument
from langchain_text_splitters import RecursiveCharacterTextSplitter
from unstructured.partition.auto import partition

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class DocumentProcessor:
    """Process documents: load content, chunk text, prepare for embedding."""

    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None,
    ):
        """
        Initialize document processor.

        Args:
            chunk_size: Maximum size of each chunk (defaults from settings)
            chunk_overlap: Overlap between chunks (defaults from settings)
        """
        self.chunk_size = chunk_size or settings.semantic_max_tokens_per_chunk
        self.chunk_overlap = chunk_overlap or settings.semantic_token_overlap

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
        )
        logger.debug(
            f"Initialized DocumentProcessor with chunk_size={self.chunk_size}, overlap={self.chunk_overlap}"
        )

    def load_document(self, file_path: str) -> str:
        """
        Load document content from file using unstructured.

        Args:
            file_path: Path to the document file

        Returns:
            Extracted text content
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        logger.info(f"Loading document: {path.name}")

        # Use unstructured to partition the document
        elements = partition(filename=str(path))

        # Combine all elements into text
        text_parts = []
        for element in elements:
            text = str(element)
            if text.strip():
                text_parts.append(text)

        content = "\n\n".join(text_parts)
        logger.debug(f"Loaded {len(content)} characters from {path.name}")
        return content

    def chunk_text(self, text: str, metadata: dict = None) -> List[LangchainDocument]:
        """
        Split text into chunks.

        Args:
            text: Text content to chunk
            metadata: Optional metadata to attach to each chunk

        Returns:
            List of Langchain Document objects
        """
        if not text.strip():
            logger.warning("Empty text provided for chunking")
            return []

        metadata = metadata or {}

        chunks = self.text_splitter.split_text(text)
        documents = [
            LangchainDocument(
                page_content=chunk, metadata={**metadata, "chunk_index": i}
            )
            for i, chunk in enumerate(chunks)
        ]

        logger.debug(f"Created {len(documents)} chunks from text")
        return documents

    def process_file(self, file_path: str, file_name: str) -> List[LangchainDocument]:
        """
        Full processing pipeline: load file and chunk into documents.

        Args:
            file_path: Path to the document file
            file_name: Name of the file for metadata

        Returns:
            List of Langchain Document objects ready for embedding
        """
        logger.info(f"Processing file: {file_name}")

        # Load content
        content = self.load_document(file_path)

        # Create chunks with file metadata
        metadata = {
            "source": file_path,
            "file_name": file_name,
        }
        chunks = self.chunk_text(content, metadata)

        logger.info(f"Processed {file_name}: {len(chunks)} chunks created")
        return chunks
