"""
Data Transfer Objects for GitLab code ingestion API.

This module defines Pydantic models for API request/response contracts
related to GitLab code ingestion and search operations.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class GitLabIngestionSettings(BaseModel):
    """Settings for GitLab repository ingestion"""
    ref: str = Field(
        default="main",
        description="Branch name, commit SHA, or tag to ingest from",
        example="main"
    )
    incremental: bool = Field(
        default=False,
        description="Whether to perform incremental update (not implemented yet)")
    file_filter: Optional[str] = Field(
        default=None,
        description="Optional glob pattern to filter files (e.g., '*.py')",
        example="*.py"
    )


class GitLabIngestionRequest(BaseModel):
    """Request model for GitLab repository ingestion"""
    settings: GitLabIngestionSettings = Field(
        default_factory=GitLabIngestionSettings,
        description="Ingestion settings"
    )


class FileInfo(BaseModel):
    """Information about an ingested file"""
    path: str = Field(
        description="File path in repository"
    )
    size: int = Field(
        description="File size in bytes"
    )
    language: str = Field(
        description="Programming language",
        example="python"
    )
    chunk_count: int = Field(
        description="Number of chunks created from this file"
    )
    last_commit: Optional[str] = Field(
        default=None,
        description="Last commit hash"
    )
    author: Optional[str] = Field(
        default=None,
        description="Last commit author"
    )


class ChunkInfo(BaseModel):
    """Information about a code chunk"""
    chunk_type: str = Field(
        description="Type of chunk (file, class, function, method)",
        example="function"
    )
    name: Optional[str] = Field(
        default=None,
        description="Chunk name (function/class name)",
        example="get_user_data"
    )
    signature: Optional[str] = Field(
        default=None,
        description="Function/method signature",
        example="def get_user_data(user_id: int) -> Dict"
    )
    language: str = Field(
        description="Programming language",
        example="python"
    )
    file_path: str = Field(
        description="Source file path",
        example="src/api/users.py"
    )
    start_line: int = Field(
        description="Start line number in source file"
    )
    end_line: int = Field(
        description="End line number in source file"
    )
    parent_class: Optional[str] = Field(
        default=None,
        description="Parent class name (for methods)",
        example="UserService"
    )
    docstring: Optional[str] = Field(
        default=None,
        description="Docstring or comment",
        max_length=500
    )


class IngestionStatus(BaseModel):
    """Status information about the ingestion process"""
    total_files: int = Field(
        description="Total number of files in repository"
    )
    processed_files: int = Field(
        description="Number of files successfully processed"
    )
    failed_files: int = Field(
        description="Number of files that failed processing"
    )
    processed_chunks: int = Field(
        description="Total number of chunks created"
    )
    start_time: datetime = Field(
        description="When ingestion started"
    )
    end_time: Optional[datetime] = Field(
        default=None,
        description="When ingestion completed"
    )
    duration_seconds: float = Field(
        description="Total duration in seconds"
    )
    status: str = Field(
        default="completed",
        description="Status of ingestion"
    )


class RepositoryInfo(BaseModel):
    """Information about the GitLab repository"""
    id: int = Field(
        description="GitLab project ID"
    )
    name: str = Field(
        description="Repository name"
    )
    description: Optional[str] = Field(
        default=None,
        description="Repository description"
    )
    web_url: str = Field(
        description="Repository URL"
    )
    default_branch: str = Field(
        description="Default branch name",
        example="main"
    )
    visibility: str = Field(
        description="Repository visibility (public/private)",
        example="private"
    )
    path_with_namespace: str = Field(
        description="Full repository path",
        example="username/project-name"
    )


class GitLabIngestionResponse(BaseModel):
    """Response model for GitLab ingestion API"""
    success: bool = Field(
        description="Whether ingestion was successful"
    )
    message: str = Field(
        description="Status message"
    )
    status: IngestionStatus = Field(
        description="Detailed ingestion status"
    )
    repository_info: Optional[RepositoryInfo] = Field(
        default=None,
        description="Information about the ingested repository"
    )
    files: List[FileInfo] = Field(
        default_factory=list,
        description="List of processed files"
    )


class CodeQueryRequest(BaseModel):
    """Request model for code search"""
    query: str = Field(
        description="Search query",
        example="How do I authenticate users?"
    )
    top_k: int = Field(
        default=10,
        description="Maximum number of results to return",
        ge=1,
        le=100
    )
    similarity_threshold: float = Field(
        default=0.7,
        description="Minimum similarity score (0.0 to 1.0)",
        ge=0.0,
        le=1.0
    )
    language: Optional[str] = Field(
        default=None,
        description="Filter by programming language",
        example="python"
    )
    file_path: Optional[str] = Field(
        default=None,
        description="Filter by file path pattern",
        example="src/auth/*.py"
    )
    chunk_type: Optional[str] = Field(
        default=None,
        description="Filter by chunk type (file/class/function/method)",
        example="function"
    )


class CodeSearchResult(BaseModel):
    """Result of a code search"""
    text: str = Field(
        description="Code chunk text"
    )
    score: float = Field(
        description="Similarity score (0.0 to 1.0)"
    )
    language: str = Field(
        description="Programming language"
    )
    file_path: str = Field(
        description="Source file path"
    )
    chunk_type: str = Field(
        description="Chunk type"
    )
    chunk_name: Optional[str] = Field(
        default=None,
        description="Chunk name"
    )
    signature: Optional[str] = Field(
        default=None,
        description="Function signature"
    )
    start_line: int = Field(
        description="Start line number"
    )
    end_line: int = Field(
        description="End line number"
    )
    parent_class: Optional[str] = Field(
        default=None,
        description="Parent class name"
    )


class CodeSearchResponse(BaseModel):
    """Response model for code search API"""
    success: bool = Field(
        description="Whether search was successful"
    )
    message: str = Field(
        description="Status message"
    )
    results: List[CodeSearchResult] = Field(
        description="Search results"
    )
    total_results: int = Field(
        description="Number of results returned"
    )
    query: str = Field(
        description="Original query"
    )
    top_k: int = Field(
        description="Requested number of results"
    )
    similarity_threshold: float = Field(
        description="Similarity threshold used"
    )
    filters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Filters applied"
    )


class LanguageStats(BaseModel):
    """Statistics for a programming language"""
    language: str = Field(
        description="Language name"
    )
    file_count: int = Field(
        description="Number of files"
    )
    chunk_count: int = Field(
        description="Number of chunks"
    )
    percentage: float = Field(
        description="Percentage of total chunks"
    )


class ChunkTypeStats(BaseModel):
    """Statistics for chunk types"""
    chunk_type: str = Field(
        description="Chunk type (file/class/function/method)"
    )
    count: int = Field(
        description="Number of chunks"
    )
    percentage: float = Field(
        description="Percentage of total chunks"
    )


class RepositoryStats(BaseModel):
    """Statistics about ingested repository"""
    total_chunks: int = Field(
        description="Total number of code chunks"
    )
    total_files: int = Field(
        description="Total number of source files"
    )
    total_lines: int = Field(
        description="Total lines of code (approximate)"
    )
    languages: List[LanguageStats] = Field(
        default_factory=list,
        description="Statistics by language"
    )
    chunk_types: List[ChunkTypeStats] = Field(
        default_factory=list,
        description="Statistics by chunk type"
    )
    repository_info: Optional[RepositoryInfo] = Field(
        default=None,
        description="Repository information"
    )
    last_ingestion: Optional[datetime] = Field(
        default=None,
        description="When repository was last ingested"
    )


class RepositoryStatsResponse(BaseModel):
    """Response model for repository statistics"""
    success: bool = Field(
        description="Whether stats retrieval was successful"
    )
    message: str = Field(
        description="Status message"
    )
    stats: RepositoryStats = Field(
        description="Repository statistics"
    )


class FileListResponse(BaseModel):
    """Response model for file list"""
    success: bool = Field(
        description="Whether file list retrieval was successful"
    )
    message: str = Field(
        description="Status message"
    )
    files: List[FileInfo] = Field(
        description="List of files"
    )
    total_files: int = Field(
        description="Total number of files"
    )


class ClearCodeRequest(BaseModel):
    """Request model for clearing code chunks"""
    confirm: bool = Field(
        default=False,
        description="Confirmation flag (must be True to clear)"
    )


class ClearCodeResponse(BaseModel):
    """Response model for clearing code chunks"""
    success: bool = Field(
        description="Whether clear operation was successful"
    )
    message: str = Field(
        description="Status message"
    )
    cleared_chunks: int = Field(
        description="Number of chunks cleared"
    )


class HealthCheckResponse(BaseModel):
    """Response model for GitLab health check"""
    is_configured: bool = Field(
        description="Whether GitLab is configured"
    )
    is_connected: bool = Field(
        description="Whether connected to GitLab"
    )
    repository_access: bool = Field(
        description="Whether repository access is available"
    )
    message: str = Field(
        description="Status message"
    )
    repository_info: Optional[RepositoryInfo] = Field(
        default=None,
        description="Repository information if accessible"
    )
