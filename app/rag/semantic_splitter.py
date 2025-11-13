import os
import re
from typing import Iterable, List, Union, Optional

# LangChain imports
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Local imports
from app.rag.embeddings import get_embedding_service
from app.config.logging_config import get_logger

# Configure logging
logger = get_logger(__name__)


# --- Minimal, fast JP sentence splitter ---
# Splits on 。？！ plus common JP quotes; keeps punctuation attached.
_JA_SPLIT_RE = re.compile(r'(?<=[。！？!?\n])(?=[^\n])')

def ja_sentence_splitter(text: str) -> List[str]:
    """
    Japanese sentence splitter optimized for semantic chunking

    Args:
        text: Text to split into sentences

    Returns:
        List of Japanese sentences
    """
    # Normalize Windows newlines; keep headings/blank lines intact
    text = text.replace("\r\n", "\n")
    # First split on headings / hard breaks to avoid mega-sentences
    blocks = re.split(r"\n{2,}", text)
    sentences: List[str] = []
    for b in blocks:
        # If block contains no JP punctuation, keep as one unit (tables, code, etc.)
        if not re.search(r"[。！？!?]", b):
            sentences.append(b.strip())
        else:
            sentences.extend([s.strip() for s in _JA_SPLIT_RE.split(b) if s.strip()])
    return [s for s in sentences if s]


class SemanticJapaneseSplitter:
    """
    Semantic text splitter optimized for Japanese text using Voyage AI embeddings
    """

    def __init__(self,
                 breakpoint_percentile_threshold: int = 90,
                 buffer_size: int = 1,
                 max_tokens_per_chunk: int = 800,
                 token_overlap: int = 50):
        """
        Initialize semantic Japanese splitter

        Args:
            breakpoint_percentile_threshold: Lower threshold creates more, smaller chunks
            buffer_size: Sentences to consider when computing similarity windows
            max_tokens_per_chunk: Hard cap to prevent oversize nodes
            token_overlap: Token overlap for the post-split hard cap
        """
        self.breakpoint_percentile_threshold = breakpoint_percentile_threshold
        self.buffer_size = buffer_size
        self.max_tokens_per_chunk = max_tokens_per_chunk
        self.token_overlap = token_overlap

        # Get embedding service from existing service
        self.embedding_service = get_embedding_service()

        # Validate Voyage API key
        if not os.environ.get("VOYAGE_API_KEY"):
            raise RuntimeError("VOYAGE_API_KEY is not set in environment variables")

        # Initialize semantic splitter with custom JP-aware sentence splitter
        try:
            embed_model = self.embedding_service.get_embedding_model()
            
            # Use LangChain's RecursiveCharacterTextSplitter instead
            self.semantic_splitter = RecursiveCharacterTextSplitter(
                chunk_size=max_tokens_per_chunk,
                chunk_overlap=token_overlap,
                length_function=len,
            )
            logger.info(f"Initialized SemanticJapaneseSplitter with threshold={breakpoint_percentile_threshold}, buffer_size={buffer_size}")
        except Exception as e:
            logger.error(f"Failed to initialize semantic splitter: {str(e)}")
            raise RuntimeError(f"Failed to initialize semantic splitter: {str(e)}")

    def split_documents(self, docs: Iterable[Union[str, Document]]) -> List[Document]:
        """
        Split documents using semantic chunking with Voyage AI embeddings

        Args:
            docs: Iterable of raw strings or LangChain Document objects

        Returns:
            List of Document objects ready for indexing

        Raises:
            RuntimeError: If semantic splitting fails due to API issues
        """
        try:
            logger.info(f"Starting semantic splitting for {len(list(docs))} documents")

            # Accept strings or Documents
            langchain_docs: List[Document] = []
            for d in docs:
                if isinstance(d, Document):
                    langchain_docs.append(d)
                else:
                    langchain_docs.append(Document(page_content=str(d)))

            # Use LangChain's text splitter
            chunks = self.semantic_splitter.split_documents(langchain_docs)
            logger.info(f"Semantic splitting created {len(chunks)} chunks")

            return chunks

        except Exception as e:
            error_msg = f"Semantic splitting failed: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def split_text(self, text: str) -> List[str]:
        """
        Split a single text using semantic chunking

        Args:
            text: Text to split

        Returns:
            List of text chunks

        Raises:
            RuntimeError: If semantic splitting fails due to API issues
        """
        try:
            doc = Document(page_content=text)
            chunks = self.split_documents([doc])
            return [chunk.page_content for chunk in chunks]
        except Exception as e:
            error_msg = f"Text semantic splitting failed: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e


def create_semantic_splitter(
    breakpoint_percentile_threshold: Optional[int] = None,
    buffer_size: Optional[int] = None,
    max_tokens_per_chunk: Optional[int] = None,
    token_overlap: Optional[int] = None
) -> SemanticJapaneseSplitter:
    """
    Factory function to create semantic splitter with environment variable defaults

    Args:
        breakpoint_percentile_threshold: Override for environment variable
        buffer_size: Override for environment variable
        max_tokens_per_chunk: Override for environment variable
        token_overlap: Override for environment variable

    Returns:
        Configured SemanticJapaneseSplitter instance
    """
    # Get values from environment variables or use defaults
    threshold = breakpoint_percentile_threshold or int(os.environ.get("SEMANTIC_BREAKPOINT_PERCENTILE_THRESHOLD", "90"))
    buffer = buffer_size or int(os.environ.get("SEMANTIC_BUFFER_SIZE", "1"))
    max_tokens = max_tokens_per_chunk or int(os.environ.get("SEMANTIC_MAX_TOKENS_PER_CHUNK", "800"))
    overlap = token_overlap or int(os.environ.get("SEMANTIC_TOKEN_OVERLAP", "50"))

    logger.info(f"Creating semantic splitter with config: threshold={threshold}, buffer={buffer}, max_tokens={max_tokens}, overlap={overlap}")

    return SemanticJapaneseSplitter(
        breakpoint_percentile_threshold=threshold,
        buffer_size=buffer,
        max_tokens_per_chunk=max_tokens,
        token_overlap=overlap
    )


# Example usage (for testing):
# if __name__ == "__main__":
#     splitter = create_semantic_splitter()
#     test_text = "これはテストです。次の文です！表もあります。\n\n第1章 概要\n日本語の文章を安全に分割します。"
#     chunks = splitter.split_text(test_text)
#     for i, chunk in enumerate(chunks):
#         print(f"Chunk {i+1} ({len(chunk)} chars): {chunk[:80].replace('\n', ' ')}")