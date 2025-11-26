"""
SQLAlchemy ORM models for ingestion tracking.

This module defines the database models (infrastructure layer) that map to database tables.
These models are separate from domain entities and handle persistence concerns.
"""

from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, ForeignKey, CheckConstraint, Index, UUID, BigInteger
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.infrastructure.database.database import Base


class IngestJobModel(Base):
    """
    ORM model for tracking ingestion jobs.
    
    Maps to the ingest_jobs table and provides persistence for IngestJob domain entities.
    """
    __tablename__ = "ingest_jobs"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Unique process identifier
    process_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # Ingestion type - extensible for multiple data sources
    ingestion_type = Column(String(50), nullable=False, index=True)
    
    # Source identifier - flexible field for different source types
    source_identifier = Column(String(500), nullable=False, index=True)
    
    # Flexible source metadata stored as JSON
    source_metadata = Column(JSON, nullable=True)
    
    # Job status
    status = Column(String(20), nullable=False, default='pending', index=True)
    
    # Sub-status for more detailed progress tracking
    sub_status = Column(String(50), nullable=True)
    
    # Timing information
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(),
                       onupdate=func.now(), nullable=False)
    
    # File processing statistics
    total_files = Column(Integer, default=0, nullable=False)
    files_processed = Column(Integer, default=0, nullable=False)
    files_succeeded = Column(Integer, default=0, nullable=False)
    files_failed = Column(Integer, default=0, nullable=False)
    files_skipped = Column(Integer, default=0, nullable=False)
    
    # Processing results
    chunks_created = Column(Integer, default=0, nullable=False)
    documents_added = Column(Integer, default=0, nullable=False)
    
    # Error handling
    error_messages = Column(JSON, nullable=True)
    error_summary = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    
    # Configuration and settings used for this job
    ingestion_config = Column(JSON, nullable=True)
    processing_settings = Column(JSON, nullable=True)
    
    # Audit information
    user_agent = Column(String(255), nullable=True)
    client_info = Column(JSON, nullable=True)
    environment_info = Column(JSON, nullable=True)
    
    # Relationship to files
    files = relationship("IngestFileModel", back_populates="job", cascade="all, delete-orphan")
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_ingest_jobs_status_created', 'status', 'created_at'),
        Index('idx_ingest_jobs_source_status', 'source_identifier', 'status'),
        Index('idx_ingest_jobs_type_status', 'ingestion_type', 'status'),
        Index('idx_ingest_jobs_active', 'status', postgresql_where="status IN ('pending', 'in_progress')"),
        Index('idx_ingest_jobs_recent', 'created_at'),
        Index('idx_ingest_jobs_completed_range', 'completed_at', postgresql_where="completed_at IS NOT NULL"),
    )


class IngestFileModel(Base):
    """
    ORM model for tracking individual files within an ingestion job.
    
    Maps to the ingest_files table and provides persistence for IngestFile domain entities.
    """
    __tablename__ = "ingest_files"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key to job
    job_id = Column(UUID(as_uuid=True), ForeignKey('ingest_jobs.id', ondelete='CASCADE'),
                   nullable=False, index=True)
    
    # File information
    file_path = Column(String(1000), nullable=False, index=True)
    source_path = Column(String(1000), nullable=True)
    
    # File status
    file_status = Column(String(20), nullable=False, default='pending', index=True)
    
    # File metadata
    file_size = Column(BigInteger, nullable=True)
    checksum = Column(String(128), nullable=True, index=True)
    file_type = Column(String(100), nullable=True)
    
    # Processing timing
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Processing results
    chunks_created = Column(Integer, default=0, nullable=False)
    documents_added = Column(Integer, default=0, nullable=False)
    
    # Additional metadata
    file_metadata = Column(JSON, nullable=True)
    
    # Relationship to job
    job = relationship("IngestJobModel", back_populates="files")
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_ingest_files_job_status', 'job_id', 'file_status'),
        Index('idx_ingest_files_status_started', 'file_status', 'started_at'),
        Index('idx_ingest_files_completed_range', 'completed_at', postgresql_where="completed_at IS NOT NULL"),
        Index('idx_ingest_files_path', 'file_path'),
        Index('idx_ingest_files_checksum', 'checksum'),
    )


class ChatbotModel(Base):
    """
    ORM model for Chatbot configuration.
    """
    __tablename__ = "chatbots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    model_name = Column(String(255), nullable=False)
    llm_config = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationship to knowledge base
    knowledge_base = relationship("KnowledgeBaseModel", back_populates="chatbot", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_chatbots_name', 'name'),
    )


class KnowledgeBaseModel(Base):
    """
    ORM model for chatbot knowledge base.
    
    Maps to the knowledge_bases table and represents a chatbot's document collection.
    """
    __tablename__ = "knowledge_bases"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key to chatbot (one-to-one)
    chatbot_id = Column(UUID(as_uuid=True), ForeignKey('chatbots.id', ondelete='CASCADE'),
                       nullable=False, unique=True, index=True)
    
    # Qdrant collection information
    collection_name = Column(String(255), nullable=False, unique=True, index=True)
    vector_dimension = Column(Integer, nullable=False, default=1536)
    
    # Statistics
    total_documents = Column(Integer, default=0, nullable=False)
    total_chunks = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(),
                       onupdate=func.now(), nullable=False)
    
    # Relationships
    chatbot = relationship("ChatbotModel", back_populates="knowledge_base")
    documents = relationship("DocumentModel", back_populates="knowledge_base", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_kb_chatbot_id', 'chatbot_id'),
        Index('idx_kb_collection_name', 'collection_name'),
    )


class DocumentModel(Base):
    """
    ORM model for tracking documents in a knowledge base.
    
    Maps to the documents table and tracks document processing status.
    """
    __tablename__ = "documents"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key to knowledge base
    knowledge_base_id = Column(UUID(as_uuid=True), ForeignKey('knowledge_bases.id', ondelete='CASCADE'),
                              nullable=False, index=True)
    
    # File information
    file_path = Column(String(1000), nullable=False)
    file_name = Column(String(500), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    file_type = Column(String(100), nullable=False)
    checksum = Column(String(128), nullable=False, index=True)
    
    # Processing status
    status = Column(String(20), nullable=False, default='pending', index=True)
    error_message = Column(Text, nullable=True)
    chunks_count = Column(Integer, default=0, nullable=False)
    
    # Processing timing
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(),
                       onupdate=func.now(), nullable=False)
    
    # Relationships
    knowledge_base = relationship("KnowledgeBaseModel", back_populates="documents")
    
    # Indexes and constraints
    __table_args__ = (
        # Unique constraint: one document per file path per knowledge base
        Index('idx_documents_kb_path', 'knowledge_base_id', 'file_path', unique=True),
        
        # Indexes for common queries
        Index('idx_documents_kb_id', 'knowledge_base_id'),
        Index('idx_documents_status', 'status'),
        Index('idx_documents_kb_status', 'knowledge_base_id', 'status'),
        Index('idx_documents_checksum', 'checksum'),
    )
