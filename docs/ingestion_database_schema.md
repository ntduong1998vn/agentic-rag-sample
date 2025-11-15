# Ingestion Database Schema

This document describes the PostgreSQL database schema for tracking data ingestion processes in the Agentic RAG system.

## Overview

The schema consists of two main tables:
- `ingest_jobs`: Tracks ingestion jobs (processes that can handle multiple files)
- `ingest_files`: Tracks individual files within each ingestion job

The schema is designed to support scalable ingestion tracking across multiple data sources including APIs, databases, file systems, and cloud storage.

## Tables

### ingest_jobs

The main table for tracking ingestion jobs. Each job represents a single ingestion operation that can process multiple files from various sources.

#### Columns

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key, auto-generated |
| `process_id` | VARCHAR(255) | Unique business process identifier |
| `ingestion_type` | VARCHAR(50) | Type of ingestion (api, database, filesystem, cloud, etc.) |
| `source_identifier` | VARCHAR(500) | Identifier for the data source |
| `source_metadata` | JSONB | Flexible metadata for source configuration |
| `status` | VARCHAR(20) | Job status: pending, in_progress, completed, failed, cancelled |
| `sub_status` | VARCHAR(50) | Detailed sub-status for progress tracking |
| `created_at` | TIMESTAMP | Job creation timestamp |
| `started_at` | TIMESTAMP | Job start timestamp |
| `completed_at` | TIMESTAMP | Job completion timestamp |
| `updated_at` | TIMESTAMP | Last update timestamp |
| `total_files` | INTEGER | Total number of files to process |
| `files_processed` | INTEGER | Number of files processed |
| `files_succeeded` | INTEGER | Number of files successfully processed |
| `files_failed` | INTEGER | Number of files that failed processing |
| `files_skipped` | INTEGER | Number of files skipped |
| `chunks_created` | INTEGER | Total chunks created from all files |
| `documents_added` | INTEGER | Total documents added to vector store |
| `error_messages` | JSONB | Array of detailed error messages |
| `error_summary` | TEXT | Summary of errors |
| `retry_count` | INTEGER | Number of retry attempts |
| `max_retries` | INTEGER | Maximum allowed retries |
| `ingestion_config` | JSONB | Configuration used for this job |
| `processing_settings` | JSONB | Processing settings (chunk sizes, etc.) |
| `user_agent` | VARCHAR(255) | User agent string |
| `client_info` | JSONB | Client information |
| `environment_info` | JSONB | Environment information |

#### Constraints

- `valid_status`: Status must be one of the allowed values
- `valid_file_counts`: File counts must be non-negative and consistent
- `valid_timing`: Timestamps must be logically consistent
- `valid_retry_count`: Retry count must be within bounds

#### Indexes

- `idx_ingest_jobs_status_created`: For querying by status and creation time
- `idx_ingest_jobs_source_status`: For filtering by source and status
- `idx_ingest_jobs_type_status`: For filtering by type and status
- `idx_ingest_jobs_active`: For finding active jobs (pending/in_progress)
- `idx_ingest_jobs_recent`: For recent jobs
- `idx_ingest_jobs_completed_range`: For completed jobs within time ranges

### ingest_files

Tracks individual files processed within ingestion jobs.

#### Columns

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key, auto-generated |
| `job_id` | UUID | Foreign key to ingest_jobs |
| `file_path` | VARCHAR(1000) | Path of the file being processed |
| `source_path` | VARCHAR(1000) | Original path in source system |
| `file_status` | VARCHAR(20) | File status: pending, processing, completed, failed, retry, skipped |
| `file_size` | BIGINT | File size in bytes |
| `checksum` | VARCHAR(128) | File checksum/hash |
| `file_type` | VARCHAR(100) | MIME type or file extension |
| `started_at` | TIMESTAMP | File processing start time |
| `completed_at` | TIMESTAMP | File processing completion time |
| `chunks_created` | INTEGER | Number of chunks created from this file |
| `documents_added` | INTEGER | Number of documents added from this file |
| `file_metadata` | JSONB | Additional file-specific metadata |

#### Constraints

- `valid_file_status`: Status must be one of the allowed values
- `valid_file_size`: File size must be non-negative if provided
- `valid_processing_results`: Processing counts must be non-negative
- `valid_file_timing`: Timestamps must be logically consistent

#### Indexes

- `idx_ingest_files_job_status`: For querying files by job and status
- `idx_ingest_files_status_started`: For files by status and start time
- `idx_ingest_files_completed_range`: For completed files within time ranges
- `idx_ingest_files_path`: For file path lookups
- `idx_ingest_files_checksum`: For checksum lookups

## Views

### active_ingest_jobs

Shows currently active ingestion jobs (pending or in_progress).

```sql
SELECT
    id, process_id, ingestion_type, source_identifier, status, sub_status,
    created_at, started_at, elapsed_seconds, total_files, files_processed,
    files_succeeded, files_failed, chunks_created, error_summary
FROM ingest_jobs
WHERE status IN ('pending', 'in_progress')
ORDER BY created_at;
```

### ingest_job_summaries

Provides summary statistics grouped by ingestion type and status.

```sql
SELECT
    ingestion_type, status, job_count, avg_duration_seconds,
    avg_total_files, avg_files_processed, avg_chunks_created,
    last_created_at, last_completed_at
FROM ingest_jobs
GROUP BY ingestion_type, status;
```

### ingest_file_status_overview

Overview of file processing status across different sources and types.

```sql
SELECT
    ingestion_type, source_identifier, file_status, file_count,
    avg_file_size, total_chunks_created, earliest_start, latest_completion
FROM ingest_files
JOIN ingest_jobs ON ingest_files.job_id = ingest_jobs.id
GROUP BY ingestion_type, source_identifier, file_status;
```

## Usage Examples

### Creating a new ingestion job

```python
from app.models.ingestion import IngestJob
from app.models.database import SessionLocal

db = SessionLocal()
job = IngestJob(
    process_id="api-ingest-001",
    ingestion_type="api",
    source_identifier="https://api.example.com/data",
    source_metadata={"endpoint": "/v1/data", "auth_token": "token"},
    total_files=100
)
db.add(job)
db.commit()
```

### Tracking file processing

```python
from app.models.ingestion import IngestFile

file_record = IngestFile(
    job_id=job.id,
    file_path="/data/file1.json",
    source_path="https://api.example.com/data/file1.json",
    file_size=1024,
    checksum="abc123..."
)
db.add(file_record)
db.commit()
```

### Querying active jobs

```sql
SELECT * FROM active_ingest_jobs;
```

### Getting job statistics

```sql
SELECT * FROM ingest_job_summaries
WHERE ingestion_type = 'api';
```

## Migration

The schema is managed using Alembic. To apply migrations:

```bash
alembic upgrade head
```

To create new migrations after schema changes:

```bash
alembic revision --autogenerate -m "Description of changes"
```

## Design Principles

1. **Scalability**: UUID primary keys and proper indexing for large datasets
2. **Flexibility**: JSONB columns for extensible metadata
3. **Data Integrity**: Comprehensive constraints and foreign key relationships
4. **Auditability**: Complete timestamp tracking and status history
5. **Performance**: Optimized indexes for common query patterns
6. **Multi-source Support**: Generic design accommodating various data sources

## Supported Data Sources

The schema is designed to handle multiple ingestion types:

- **API**: REST API endpoints with authentication
- **Database**: SQL/NoSQL database exports
- **Filesystem**: Local or network file systems
- **Cloud Storage**: S3, GCS, Azure Blob Storage, etc.
- **GitLab**: Repository and file ingestion (existing support)

Each source type can store specific configuration in the `source_metadata` JSONB field.