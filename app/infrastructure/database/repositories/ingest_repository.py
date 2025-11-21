"""
Repository pattern for ingestion entities.

This module provides repositories that handle the mapping between domain entities
and ORM models, abstracting database operations from the domain layer.
"""

from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from datetime import datetime

from app.domain.files.entities import IngestJob, IngestFile, JobStatus, FileStatus
from app.infrastructure.database.models import IngestJobModel, IngestFileModel


class IngestFileRepository:
    """
    Repository for IngestFile entities.
    
    Handles CRUD operations and mapping between IngestFile domain entities
    and IngestFileModel ORM models.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    @staticmethod
    def to_entity(model: IngestFileModel) -> IngestFile:
        """Convert ORM model to domain entity"""
        return IngestFile(
            id=model.id,
            job_id=model.job_id,
            file_path=model.file_path,
            source_path=model.source_path,
            file_status=FileStatus(model.file_status),
            file_size=model.file_size,
            checksum=model.checksum,
            file_type=model.file_type,
            started_at=model.started_at,
            completed_at=model.completed_at,
            chunks_created=model.chunks_created,
            documents_added=model.documents_added,
            file_metadata=model.file_metadata,
        )
    
    @staticmethod
    def to_model(entity: IngestFile) -> IngestFileModel:
        """Convert domain entity to ORM model"""
        return IngestFileModel(
            id=entity.id,
            job_id=entity.job_id,
            file_path=entity.file_path,
            source_path=entity.source_path,
            file_status=entity.file_status.value,
            file_size=entity.file_size,
            checksum=entity.checksum,
            file_type=entity.file_type,
            started_at=entity.started_at,
            completed_at=entity.completed_at,
            chunks_created=entity.chunks_created,
            documents_added=entity.documents_added,
            file_metadata=entity.file_metadata,
        )
    
    def create(self, entity: IngestFile) -> IngestFile:
        """Create a new file record"""
        model = self.to_model(entity)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self.to_entity(model)
    
    def get_by_id(self, file_id: UUID) -> Optional[IngestFile]:
        """Get file by ID"""
        model = self.db.query(IngestFileModel).filter(IngestFileModel.id == file_id).first()
        return self.to_entity(model) if model else None
    
    def get_by_job_id(self, job_id: UUID) -> List[IngestFile]:
        """Get all files for a job"""
        models = self.db.query(IngestFileModel).filter(IngestFileModel.job_id == job_id).all()
        return [self.to_entity(model) for model in models]
    
    def update(self, entity: IngestFile) -> IngestFile:
        """Update existing file record"""
        model = self.db.query(IngestFileModel).filter(IngestFileModel.id == entity.id).first()
        if not model:
            raise ValueError(f"IngestFile with id {entity.id} not found")
        
        # Update fields
        model.file_path = entity.file_path
        model.source_path = entity.source_path
        model.file_status = entity.file_status.value
        model.file_size = entity.file_size
        model.checksum = entity.checksum
        model.file_type = entity.file_type
        model.started_at = entity.started_at
        model.completed_at = entity.completed_at
        model.chunks_created = entity.chunks_created
        model.documents_added = entity.documents_added
        model.file_metadata = entity.file_metadata
        
        self.db.commit()
        self.db.refresh(model)
        return self.to_entity(model)
    
    def delete(self, file_id: UUID) -> bool:
        """Delete file record"""
        model = self.db.query(IngestFileModel).filter(IngestFileModel.id == file_id).first()
        if model:
            self.db.delete(model)
            self.db.commit()
            return True
        return False


class IngestJobRepository:
    """
    Repository for IngestJob entities.
    
    Handles CRUD operations and mapping between IngestJob domain entities
    and IngestJobModel ORM models.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.file_repo = IngestFileRepository(db)
    
    @staticmethod
    def to_entity(model: IngestJobModel, include_files: bool = True) -> IngestJob:
        """Convert ORM model to domain entity"""
        files = []
        if include_files and model.files:
            files = [IngestFileRepository.to_entity(f) for f in model.files]
        
        return IngestJob(
            id=model.id,
            process_id=model.process_id,
            ingestion_type=model.ingestion_type,
            source_identifier=model.source_identifier,
            source_metadata=model.source_metadata,
            status=JobStatus(model.status),
            sub_status=model.sub_status,
            created_at=model.created_at,
            started_at=model.started_at,
            completed_at=model.completed_at,
            updated_at=model.updated_at,
            total_files=model.total_files,
            files_processed=model.files_processed,
            files_succeeded=model.files_succeeded,
            files_failed=model.files_failed,
            files_skipped=model.files_skipped,
            chunks_created=model.chunks_created,
            documents_added=model.documents_added,
            error_messages=model.error_messages,
            error_summary=model.error_summary,
            retry_count=model.retry_count,
            max_retries=model.max_retries,
            ingestion_config=model.ingestion_config,
            processing_settings=model.processing_settings,
            user_agent=model.user_agent,
            client_info=model.client_info,
            environment_info=model.environment_info,
            files=files,
        )
    
    @staticmethod
    def to_model(entity: IngestJob, include_files: bool = False) -> IngestJobModel:
        """Convert domain entity to ORM model"""
        model = IngestJobModel(
            id=entity.id,
            process_id=entity.process_id,
            ingestion_type=entity.ingestion_type,
            source_identifier=entity.source_identifier,
            source_metadata=entity.source_metadata,
            status=entity.status.value,
            sub_status=entity.sub_status,
            created_at=entity.created_at,
            started_at=entity.started_at,
            completed_at=entity.completed_at,
            updated_at=entity.updated_at,
            total_files=entity.total_files,
            files_processed=entity.files_processed,
            files_succeeded=entity.files_succeeded,
            files_failed=entity.files_failed,
            files_skipped=entity.files_skipped,
            chunks_created=entity.chunks_created,
            documents_added=entity.documents_added,
            error_messages=entity.error_messages,
            error_summary=entity.error_summary,
            retry_count=entity.retry_count,
            max_retries=entity.max_retries,
            ingestion_config=entity.ingestion_config,
            processing_settings=entity.processing_settings,
            user_agent=entity.user_agent,
            client_info=entity.client_info,
            environment_info=entity.environment_info,
        )
        
        if include_files and entity.files:
            model.files = [IngestFileRepository.to_model(f) for f in entity.files]
        
        return model
    
    def create(self, entity: IngestJob) -> IngestJob:
        """Create a new job"""
        model = self.to_model(entity, include_files=True)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self.to_entity(model)
    
    def get_by_id(self, job_id: UUID) -> Optional[IngestJob]:
        """Get job by ID"""
        model = self.db.query(IngestJobModel).filter(IngestJobModel.id == job_id).first()
        return self.to_entity(model) if model else None
    
    def get_by_process_id(self, process_id: str) -> Optional[IngestJob]:
        """Get job by process ID"""
        model = self.db.query(IngestJobModel).filter(IngestJobModel.process_id == process_id).first()
        return self.to_entity(model) if model else None
    
    def get_all(self, limit: int = 100, offset: int = 0) -> List[IngestJob]:
        """Get all jobs with pagination"""
        models = self.db.query(IngestJobModel).offset(offset).limit(limit).all()
        return [self.to_entity(model) for model in models]
    
    def get_by_status(self, status: JobStatus, limit: int = 100) -> List[IngestJob]:
        """Get jobs by status"""
        models = self.db.query(IngestJobModel).filter(
            IngestJobModel.status == status.value
        ).limit(limit).all()
        return [self.to_entity(model) for model in models]
    
    def get_active_jobs(self) -> List[IngestJob]:
        """Get all active jobs (pending or in-progress)"""
        models = self.db.query(IngestJobModel).filter(
            IngestJobModel.status.in_(['pending', 'in_progress'])
        ).all()
        return [self.to_entity(model) for model in models]
    
    def update(self, entity: IngestJob) -> IngestJob:
        """Update existing job"""
        model = self.db.query(IngestJobModel).filter(IngestJobModel.id == entity.id).first()
        if not model:
            raise ValueError(f"IngestJob with id {entity.id} not found")
        
        # Update fields
        model.process_id = entity.process_id
        model.ingestion_type = entity.ingestion_type
        model.source_identifier = entity.source_identifier
        model.source_metadata = entity.source_metadata
        model.status = entity.status.value
        model.sub_status = entity.sub_status
        model.started_at = entity.started_at
        model.completed_at = entity.completed_at
        model.updated_at = datetime.now()
        model.total_files = entity.total_files
        model.files_processed = entity.files_processed
        model.files_succeeded = entity.files_succeeded
        model.files_failed = entity.files_failed
        model.files_skipped = entity.files_skipped
        model.chunks_created = entity.chunks_created
        model.documents_added = entity.documents_added
        model.error_messages = entity.error_messages
        model.error_summary = entity.error_summary
        model.retry_count = entity.retry_count
        model.max_retries = entity.max_retries
        model.ingestion_config = entity.ingestion_config
        model.processing_settings = entity.processing_settings
        model.user_agent = entity.user_agent
        model.client_info = entity.client_info
        model.environment_info = entity.environment_info
        
        self.db.commit()
        self.db.refresh(model)
        return self.to_entity(model)
    
    def delete(self, job_id: UUID) -> bool:
        """Delete job (cascades to files)"""
        model = self.db.query(IngestJobModel).filter(IngestJobModel.id == job_id).first()
        if model:
            self.db.delete(model)
            self.db.commit()
            return True
        return False
