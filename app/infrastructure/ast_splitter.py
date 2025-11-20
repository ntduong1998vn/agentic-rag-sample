"""
AST-based code splitter for semantic code chunking.
"""
from typing import List, Optional
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.config import get_logger

logger = get_logger(__name__)


class ASTCodeSplitter:
    """AST-based code splitter for semantic code chunking"""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """Initialize the AST code splitter"""
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        # For now, use a simple text splitter as fallback
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )
        logger.info(f"Initialized ASTCodeSplitter")

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split documents into chunks

        Args:
            documents: List of documents to split

        Returns:
            List of document chunks
        """
        return self.text_splitter.split_documents(documents)


def create_ast_splitter(chunk_size: int = 1000, chunk_overlap: int = 200) -> ASTCodeSplitter:
    """Create an AST code splitter instance"""
    return ASTCodeSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
