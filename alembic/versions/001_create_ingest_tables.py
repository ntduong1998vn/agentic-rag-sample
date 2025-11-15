"""Create ingest_jobs and ingest_files tables

Revision ID: 001
Revises:
Create Date: 2025-11-15 01:57:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create ingest_jobs table
    op.create_table('ingest_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column('process_id', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('ingestion_type', sa.String(50), nullable=False, index=True),
        sa.Column('source_identifier', sa.String(500), nullable=False, index=True),
        sa.Column('source_metadata', postgresql.JSON, nullable=True),
        sa.Column('status', sa.String(20), nullable=False, default='pending', index=True),
        sa.Column('sub_status', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False, index=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), onupdate=sa.text('NOW()'), nullable=False),
        sa.Column('total_files', sa.Integer, default=0, nullable=False),
        sa.Column('files_processed', sa.Integer, default=0, nullable=False),
        sa.Column('files_succeeded', sa.Integer, default=0, nullable=False),
        sa.Column('files_failed', sa.Integer, default=0, nullable=False),
        sa.Column('files_skipped', sa.Integer, default=0, nullable=False),
        sa.Column('chunks_created', sa.Integer, default=0, nullable=False),
        sa.Column('documents_added', sa.Integer, default=0, nullable=False),
        sa.Column('error_messages', postgresql.JSON, nullable=True),
        sa.Column('error_summary', sa.Text, nullable=True),
        sa.Column('retry_count', sa.Integer, default=0, nullable=False),
        sa.Column('max_retries', sa.Integer, default=3, nullable=False),
        sa.Column('ingestion_config', postgresql.JSON, nullable=True),
        sa.Column('processing_settings', postgresql.JSON, nullable=True),
        sa.Column('user_agent', sa.String(255), nullable=True),
        sa.Column('client_info', postgresql.JSON, nullable=True),
        sa.Column('environment_info', postgresql.JSON, nullable=True),

        # Constraints
        sa.CheckConstraint("status IN ('pending', 'in_progress', 'completed', 'failed', 'cancelled')", name='valid_status'),
        sa.CheckConstraint("total_files >= 0 AND files_processed >= 0 AND files_succeeded >= 0 AND files_failed >= 0 AND files_skipped >= 0 AND files_processed = files_succeeded + files_failed + files_skipped", name='valid_file_counts'),
        sa.CheckConstraint("(started_at IS NULL AND completed_at IS NULL) OR (started_at IS NOT NULL AND completed_at IS NULL) OR (started_at IS NOT NULL AND completed_at IS NOT NULL AND completed_at >= started_at)", name='valid_timing'),
        sa.CheckConstraint("retry_count >= 0 AND retry_count <= max_retries", name='valid_retry_count'),
    )

    # Create indexes for ingest_jobs
    op.create_index('idx_ingest_jobs_status_created', 'ingest_jobs', ['status', 'created_at'])
    op.create_index('idx_ingest_jobs_source_status', 'ingest_jobs', ['source_identifier', 'status'])
    op.create_index('idx_ingest_jobs_type_status', 'ingest_jobs', ['ingestion_type', 'status'])
    op.create_index('idx_ingest_jobs_active', 'ingest_jobs', ['status'], postgresql_where="status IN ('pending', 'in_progress')")
    op.create_index('idx_ingest_jobs_recent', 'ingest_jobs', ['created_at'])
    op.create_index('idx_ingest_jobs_completed_range', 'ingest_jobs', ['completed_at'], postgresql_where="completed_at IS NOT NULL")

    # Create ingest_files table
    op.create_table('ingest_files',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('ingest_jobs.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('file_path', sa.String(1000), nullable=False, index=True),
        sa.Column('source_path', sa.String(1000), nullable=True),
        sa.Column('file_status', sa.String(20), nullable=False, default='pending', index=True),
        sa.Column('file_size', sa.BigInteger, nullable=True),
        sa.Column('checksum', sa.String(128), nullable=True, index=True),
        sa.Column('file_type', sa.String(100), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('chunks_created', sa.Integer, default=0, nullable=False),
        sa.Column('documents_added', sa.Integer, default=0, nullable=False),
        sa.Column('file_metadata', postgresql.JSON, nullable=True),

        # Constraints
        sa.CheckConstraint("file_status IN ('pending', 'processing', 'completed', 'failed', 'retry', 'skipped')", name='valid_file_status'),
        sa.CheckConstraint("file_size IS NULL OR file_size >= 0", name='valid_file_size'),
        sa.CheckConstraint("chunks_created >= 0 AND documents_added >= 0", name='valid_processing_results'),
        sa.CheckConstraint("(started_at IS NULL AND completed_at IS NULL) OR (started_at IS NOT NULL AND completed_at IS NULL) OR (started_at IS NOT NULL AND completed_at IS NOT NULL AND completed_at >= started_at)", name='valid_file_timing'),
    )

    # Create indexes for ingest_files
    op.create_index('idx_ingest_files_job_status', 'ingest_files', ['job_id', 'file_status'])
    op.create_index('idx_ingest_files_status_started', 'ingest_files', ['file_status', 'started_at'])
    op.create_index('idx_ingest_files_completed_range', 'ingest_files', ['completed_at'], postgresql_where="completed_at IS NOT NULL")
    op.create_index('idx_ingest_files_path', 'ingest_files', ['file_path'])
    op.create_index('idx_ingest_files_checksum', 'ingest_files', ['checksum'])

    # Create views for common queries
    # View for active ingestion jobs
    op.execute("""
    CREATE OR REPLACE VIEW active_ingest_jobs AS
    SELECT
        id,
        process_id,
        ingestion_type,
        source_identifier,
        status,
        sub_status,
        created_at,
        started_at,
        EXTRACT(EPOCH FROM (NOW() - COALESCE(started_at, created_at))) as elapsed_seconds,
        total_files,
        files_processed,
        files_succeeded,
        files_failed,
        chunks_created,
        error_summary
    FROM ingest_jobs
    WHERE status IN ('pending', 'in_progress')
    ORDER BY created_at;
    """)

    # View for ingestion job summaries
    op.execute("""
    CREATE OR REPLACE VIEW ingest_job_summaries AS
    SELECT
        ingestion_type,
        status,
        COUNT(*) as job_count,
        AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) as avg_duration_seconds,
        AVG(total_files) as avg_total_files,
        AVG(files_processed) as avg_files_processed,
        AVG(chunks_created) as avg_chunks_created,
        MAX(created_at) as last_created_at,
        MAX(completed_at) as last_completed_at
    FROM ingest_jobs
    GROUP BY ingestion_type, status
    ORDER BY ingestion_type, status;
    """)

    # View for file status overviews
    op.execute("""
    CREATE OR REPLACE VIEW ingest_file_status_overview AS
    SELECT
        ij.ingestion_type,
        ij.source_identifier,
        ifi.file_status,
        COUNT(*) as file_count,
        AVG(ifi.file_size) as avg_file_size,
        SUM(ifi.chunks_created) as total_chunks_created,
        MIN(ifi.started_at) as earliest_start,
        MAX(ifi.completed_at) as latest_completion
    FROM ingest_files ifi
    JOIN ingest_jobs ij ON ifi.job_id = ij.id
    GROUP BY ij.ingestion_type, ij.source_identifier, ifi.file_status
    ORDER BY ij.ingestion_type, ij.source_identifier, ifi.file_status;
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop views
    op.execute("DROP VIEW IF EXISTS ingest_file_status_overview;")
    op.execute("DROP VIEW IF EXISTS ingest_job_summaries;")
    op.execute("DROP VIEW IF EXISTS active_ingest_jobs;")

    # Drop indexes for ingest_files
    op.drop_index('idx_ingest_files_checksum')
    op.drop_index('idx_ingest_files_path')
    op.drop_index('idx_ingest_files_completed_range')
    op.drop_index('idx_ingest_files_status_started')
    op.drop_index('idx_ingest_files_job_status')

    # Drop ingest_files table
    op.drop_table('ingest_files')

    # Drop indexes for ingest_jobs
    op.drop_index('idx_ingest_jobs_completed_range')
    op.drop_index('idx_ingest_jobs_recent')
    op.drop_index('idx_ingest_jobs_active')
    op.drop_index('idx_ingest_jobs_type_status')
    op.drop_index('idx_ingest_jobs_source_status')
    op.drop_index('idx_ingest_jobs_status_created')

    # Drop ingest_jobs table
    op.drop_table('ingest_jobs')