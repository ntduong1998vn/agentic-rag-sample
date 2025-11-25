"""
Centralized application configuration.
"""

import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
import qdrant_client
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams
from qdrant_client.http.exceptions import UnexpectedResponse

# Configure logging
logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    """
    Main application settings.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra='ignore',
    )

    # API Keys
    google_api_key: str = Field("", description="Google Gemini API key")
    openai_api_key: str = Field("", description="OpenAI API key")

    # Database Configuration
    postgres_host: str = Field("localhost", description="PostgreSQL host")
    postgres_port: int = Field(5432, description="PostgreSQL port")
    postgres_db: str = Field("agentic_rag", description="PostgreSQL database name")
    postgres_user: str = Field("agentic_rag", description="PostgreSQL user")
    postgres_password: str = Field("agentic_rag_123", description="PostgreSQL password")
    
    @property
    def database_url(self) -> str:
        """Construct database URL."""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    # Vector Store
    qdrant_host: str = Field("localhost", description="Qdrant server host")
    qdrant_port: int = Field(6333, description="Qdrant server port")
    qdrant_api_key: Optional[str] = Field(None, description="Qdrant API key")

    # Logging
    log_level: str = Field("DEBUG", description="Logging level")
    log_file_path: str = Field("logs/app.log", description="Log file path")
    log_console: bool = Field(True, description="Enable console logging")

    # Semantic Chunking
    semantic_breakpoint_percentile_threshold: int = Field(90, description="Breakpoint percentile threshold")
    semantic_buffer_size: int = Field(1, description="Buffer size")
    semantic_max_tokens_per_chunk: int = Field(800, description="Maximum tokens per chunk")
    semantic_token_overlap: int = Field(50, description="Token overlap")

    # GitLab
    gitlab_url: str = Field("https://gitlab.com", description="GitLab instance URL")
    gitlab_token: str = Field("", description="GitLab access token")
    gitlab_project_id: str = Field("", description="GitLab project ID")


# Global settings instance
settings = Settings()


# Qdrant Helpers

def get_qdrant_client(
    host: Optional[str] = None,
    port: Optional[int] = None,
    api_key: Optional[str] = None
) -> qdrant_client.QdrantClient:
    """Initialize and return a Qdrant client."""
    host = host or settings.qdrant_host
    port = port or settings.qdrant_port
    api_key = api_key or settings.qdrant_api_key

    if api_key:
        return qdrant_client.QdrantClient(
            host=host, 
            port=port, 
            api_key=api_key, 
            timeout=30,
            prefer_grpc=False  # Use HTTP instead of gRPC to avoid SSL issues
        )
    else:
        return qdrant_client.QdrantClient(
            host=host, 
            port=port, 
            timeout=30,
            prefer_grpc=False  # Use HTTP instead of gRPC to avoid SSL issues
        )


def get_or_create_collection(
    collection_name: str,
    vector_size: int = 1536,
    client: Optional[qdrant_client.QdrantClient] = None
) -> models.CollectionInfo:
    """Get or create a Qdrant collection."""
    if client is None:
        client = get_qdrant_client()

    try:
        collection_info = client.get_collection(collection_name=collection_name)
        logger.info(f"Using existing collection: {collection_name}")
        return collection_info
    except UnexpectedResponse:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
        )
        logger.info(f"Created new collection: {collection_name}")
        return client.get_collection(collection_name=collection_name)
    except Exception as e:
        logger.error(f"Error handling collection: {e}")
        raise


def reset_collection(
    collection_name: str,
    vector_size: int = 1536,
    client: Optional[qdrant_client.QdrantClient] = None
) -> models.CollectionInfo:
    """Delete and recreate a collection."""
    if client is None:
        client = get_qdrant_client()

    try:
        client.delete_collection(collection_name=collection_name)
        logger.info(f"Deleted collection: {collection_name}")
    except UnexpectedResponse:
        logger.warning(f"Collection {collection_name} does not exist")
    except Exception as e:
        logger.warning(f"Could not delete collection: {e}")

    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
    )
    logger.info(f"Created new collection: {collection_name}")
    return client.get_collection(collection_name=collection_name)


def get_collection_stats(
    collection_name: str,
    client: Optional[qdrant_client.QdrantClient] = None
) -> Dict[str, Any]:
    """Get statistics for the Qdrant collection."""
    if client is None:
        client = get_qdrant_client()

    try:
        collection_info = client.get_collection(collection_name=collection_name)
        points_count = client.count(collection_name=collection_name).count
        
        return {
            "collection_name": collection_name,
            "document_count": points_count,
            "status": "active",
            "vectors_config": collection_info.config.params.vectors.to_dict() if collection_info.config.params.vectors else None
        }
    except Exception as e:
        logger.error(f"Error getting collection stats: {e}")
        return {
            "collection_name": collection_name,
            "document_count": 0,
            "status": "not_found"
        }

# Logging Configuration (Simplified version of logging_config.py)
_logging_initialized = False

def setup_logging(
    log_level: Optional[str] = None,
    log_file_path: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 14,
    enable_console: Optional[bool] = None
) -> None:
    """Setup centralized logging configuration."""
    global _logging_initialized
    if _logging_initialized:
        return

    log_level = log_level or settings.log_level
    log_file_path = log_file_path or settings.log_file_path
    enable_console = enable_console if enable_console is not None else settings.log_console

    numeric_level = getattr(logging, log_level.upper(), logging.DEBUG)
    
    # Create logs directory
    log_path = Path(log_file_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    root_logger.handlers.clear()

    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)-20s | %(funcName)-15s:%(lineno)-4d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File handler
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler(
        filename=log_file_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_formatter = logging.Formatter(
            fmt='%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

    _logging_initialized = True
    logging.getLogger(__name__).info(f"Logging initialized - Level: {log_level}")

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    if not _logging_initialized:
        setup_logging()
    return logging.getLogger(name)

def initialize_logging():
    setup_logging()
