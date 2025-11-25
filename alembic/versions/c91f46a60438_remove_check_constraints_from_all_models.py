"""remove check constraints from all models

Revision ID: c91f46a60438
Revises: 37d2b8fcfc4d
Create Date: 2025-11-25 08:16:30.489483

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c91f46a60438'
down_revision: Union[str, Sequence[str], None] = '37d2b8fcfc4d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Remove all check constraints."""
    # Drop constraints from ingest_jobs table
    op.drop_constraint('valid_status', 'ingest_jobs', type_='check')
    op.drop_constraint('valid_file_counts', 'ingest_jobs', type_='check')
    op.drop_constraint('valid_timing', 'ingest_jobs', type_='check')
    op.drop_constraint('valid_retry_count', 'ingest_jobs', type_='check')
    
    # Drop constraints from ingest_files table
    op.drop_constraint('valid_file_status', 'ingest_files', type_='check')
    op.drop_constraint('valid_file_size', 'ingest_files', type_='check')
    op.drop_constraint('valid_processing_results', 'ingest_files', type_='check')
    op.drop_constraint('valid_file_timing', 'ingest_files', type_='check')
    
    # Drop constraints from knowledge_bases table
    op.drop_constraint('valid_documents_count', 'knowledge_bases', type_='check')
    op.drop_constraint('valid_chunks_count', 'knowledge_bases', type_='check')
    op.drop_constraint('valid_vector_dimension', 'knowledge_bases', type_='check')
    
    # Drop constraints from documents table
    op.drop_constraint('valid_document_status', 'documents', type_='check')
    op.drop_constraint('valid_document_file_size', 'documents', type_='check')
    op.drop_constraint('valid_document_chunks_count', 'documents', type_='check')
    op.drop_constraint('valid_document_timing', 'documents', type_='check')
    
    # Drop constraints from document_chunks table
    op.drop_constraint('valid_chunk_index', 'document_chunks', type_='check')
    op.drop_constraint('valid_chunk_size', 'document_chunks', type_='check')


def downgrade() -> None:
    """Downgrade schema - Re-add all check constraints."""
    # Re-add constraints to ingest_jobs table
    op.create_check_constraint(
        'valid_status',
        'ingest_jobs',
        "status IN ('pending', 'in_progress', 'completed', 'failed', 'cancelled')"
    )
    op.create_check_constraint(
        'valid_file_counts',
        'ingest_jobs',
        "total_files >= 0 AND files_processed >= 0 AND files_succeeded >= 0 AND "
        "files_failed >= 0 AND files_skipped >= 0 AND "
        "files_processed = files_succeeded + files_failed + files_skipped"
    )
    op.create_check_constraint(
        'valid_timing',
        'ingest_jobs',
        "(started_at IS NULL AND completed_at IS NULL) OR "
        "(started_at IS NOT NULL AND completed_at IS NULL) OR "
        "(started_at IS NOT NULL AND completed_at IS NOT NULL AND completed_at >= started_at)"
    )
    op.create_check_constraint(
        'valid_retry_count',
        'ingest_jobs',
        "retry_count >= 0 AND retry_count <= max_retries"
    )
    
    # Re-add constraints to ingest_files table
    op.create_check_constraint(
        'valid_file_status',
        'ingest_files',
        "file_status IN ('pending', 'processing', 'completed', 'failed', 'retry', 'skipped')"
    )
    op.create_check_constraint(
        'valid_file_size',
        'ingest_files',
        "file_size IS NULL OR file_size >= 0"
    )
    op.create_check_constraint(
        'valid_processing_results',
        'ingest_files',
        "chunks_created >= 0 AND documents_added >= 0"
    )
    op.create_check_constraint(
        'valid_file_timing',
        'ingest_files',
        "(started_at IS NULL AND completed_at IS NULL) OR "
        "(started_at IS NOT NULL AND completed_at IS NULL) OR "
        "(started_at IS NOT NULL AND completed_at IS NOT NULL AND completed_at >= started_at)"
    )
    
    # Re-add constraints to knowledge_bases table
    op.create_check_constraint(
        'valid_documents_count',
        'knowledge_bases',
        "total_documents >= 0"
    )
    op.create_check_constraint(
        'valid_chunks_count',
        'knowledge_bases',
        "total_chunks >= 0"
    )
    op.create_check_constraint(
        'valid_vector_dimension',
        'knowledge_bases',
        "vector_dimension > 0"
    )
    
    # Re-add constraints to documents table
    op.create_check_constraint(
        'valid_document_status',
        'documents',
        "status IN ('pending', 'processing', 'completed', 'failed', 'skipped')"
    )
    op.create_check_constraint(
        'valid_document_file_size',
        'documents',
        "file_size >= 0"
    )
    op.create_check_constraint(
        'valid_document_chunks_count',
        'documents',
        "chunks_count >= 0"
    )
    op.create_check_constraint(
        'valid_document_timing',
        'documents',
        "(started_at IS NULL AND completed_at IS NULL) OR "
        "(started_at IS NOT NULL AND completed_at IS NULL) OR "
        "(started_at IS NOT NULL AND completed_at IS NOT NULL AND completed_at >= started_at)"
    )
    
    # Re-add constraints to document_chunks table
    op.create_check_constraint(
        'valid_chunk_index',
        'document_chunks',
        "chunk_index >= 0"
    )
    op.create_check_constraint(
        'valid_chunk_size',
        'document_chunks',
        "chunk_size > 0"
    )
