"""
Gemini embedding model wrapper using langchain-google-genai.
"""

from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.core.config import settings
from app.core.logging import get_logger
from google.genai.local_tokenizer import LocalTokenizer

logger = get_logger(__name__)

# Gemini embedding model configuration
GEMINI_EMBEDDING_MODEL = "gemini-embedding-001"
GEMINI_EMBEDDING_DIMENSION = 3072


def get_gemini_embeddings() -> GoogleGenerativeAIEmbeddings:
    """
    Get configured Gemini embeddings instance.

    Returns:
        GoogleGenerativeAIEmbeddings instance configured with API key
    """
    if not settings.google_api_key:
        raise ValueError("GOOGLE_API_KEY is not configured")

    embeddings = GoogleGenerativeAIEmbeddings(
        model=GEMINI_EMBEDDING_MODEL,
        google_api_key=settings.google_api_key,
    )
    return embeddings


def count_tokens(text: str) -> int:
    tokenizer = LocalTokenizer(model_name="gemini-2.5-flash-lite")
    return tokenizer.count_tokens(text).total_tokens


def get_embedding_dimension() -> int:
    """Get the embedding dimension for Gemini model."""
    return GEMINI_EMBEDDING_DIMENSION
