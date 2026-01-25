"""
Document processor for loading, chunking, and preparing documents for embedding.
"""

from app.rag.embeddings.gemini import count_tokens
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
            length_function=count_tokens,
        )
        logger.debug(
            f"Initialized DocumentProcessor with chunk_size={self.chunk_size}, overlap={self.chunk_overlap}"
        )

    def load_document(self, file_path: str) -> List[LangchainDocument]:
        """
        Load document content from file using unstructured.

        Args:
            file_path: Path to the document file

        Returns:
            List of Langchain Documents with metadata
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        logger.info(f"Loading document: {path.name}")

        elements = partition(filename=str(path), find_subtable=False)

        documents = []
        for element in elements:
            metadata = (
                element.metadata.to_dict()
                if hasattr(element.metadata, "to_dict")
                else {}
            )

            text = str(element)
            if text.strip():
                documents.append(
                    LangchainDocument(page_content=text, metadata=metadata)
                )

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

        # Load content as documents with metadata
        raw_documents = self.load_document(file_path)

        # Merge file metadata into each document's metadata
        file_metadata = {
            "source": file_path,
            "file_name": file_name,
        }

        allowed_keys = {
            "filetype",
            "source",
            "file_name",
            "chunk_index",
            "document_id",
            # "file_directory",
            # "filename",
            "page_name",
            "page_number",
            "last_modified",
        }

        for doc in raw_documents:
            doc.metadata = {k: v for k, v in doc.metadata.items() if k in allowed_keys}
            doc.metadata.update(file_metadata)

        chunks = self.text_splitter.split_documents(raw_documents)

        for i, chunk in enumerate(chunks):
            chunk.metadata["chunk_index"] = i

        logger.info(f"Processed {file_name}: {len(chunks)} chunks created")
        return chunks
