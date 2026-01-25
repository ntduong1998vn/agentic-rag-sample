"""
Centralized application configuration.
"""

from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Main application settings.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
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

    # Vector Store (Qdrant - Legacy)
    qdrant_host: str = Field("localhost", description="Qdrant server host")
    qdrant_port: int = Field(6333, description="Qdrant server port")
    qdrant_api_key: Optional[str] = Field(None, description="Qdrant API key")

    # AWS S3 Vectors Configuration
    s3_vectors_bucket_name: str = Field("", description="S3 Vector Bucket name")
    s3_vectors_region: str = Field("us-east-1", description="AWS region for S3 Vectors")
    aws_access_key_id: Optional[str] = Field(None, description="AWS Access Key ID")
    aws_secret_access_key: Optional[str] = Field(
        None, description="AWS Secret Access Key"
    )

    # Logging
    log_level: str = Field("DEBUG", description="Logging level")
    log_file_path: str = Field("logs/app.log", description="Log file path")
    log_console: bool = Field(True, description="Enable console logging")

    # Semantic Chunking
    semantic_breakpoint_percentile_threshold: int = Field(
        90, description="Breakpoint percentile threshold"
    )
    semantic_buffer_size: int = Field(1, description="Buffer size")
    semantic_max_tokens_per_chunk: int = Field(
        800, description="Maximum tokens per chunk"
    )
    semantic_token_overlap: int = Field(50, description="Token overlap")

    # GitLab
    gitlab_url: str = Field("https://gitlab.com", description="GitLab instance URL")
    gitlab_token: str = Field("", description="GitLab access token")
    gitlab_project_id: str = Field("", description="GitLab project ID")

    # LangSmith Configuration
    langsmith_tracing: bool = Field(False, description="Enable LangSmith tracing")
    langsmith_endpoint: str = Field(
        "https://api.smith.langchain.com", description="LangSmith API endpoint"
    )
    langsmith_api_key: str = Field("", description="LangSmith API key")
    langsmith_project: str = Field("default", description="LangSmith project name")


# Global settings instance
settings = Settings()
