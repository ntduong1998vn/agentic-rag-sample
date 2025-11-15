"""
Centralized application settings using pydantic-settings.

This module provides a unified configuration system that loads settings
from environment variables and .env files using pydantic-settings.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """
    Main application settings.

    Loads configuration from environment variables and .env file.
    Environment variables are case-insensitive by default.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra='ignore',
    )

    # API Keys (flat structure for easier env var mapping)
    voyage_api_key: str = Field("", description="Voyage AI API key")
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
        """Construct database URL from individual PostgreSQL settings."""
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