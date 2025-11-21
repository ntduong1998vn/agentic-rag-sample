---
description: ingest documents into the system
---

# Ingest Documents

This workflow describes how to ingest documents into the RAG system.

## Prerequisites

- Ensure the development server is running
- Ensure Qdrant and PostgreSQL are running
- Have your documents ready

## Ingest Local Files

1. Prepare your documents in supported formats:
   - PDF, DOCX, DOC, CSV, TXT, MD
   - HTML, HTM
   - Images: JPG, JPEG, PNG, GIF, BMP, TIFF
   - EPUB

2. Use the API to upload files:
   ```bash
   curl -X POST "http://localhost:8000/files/upload" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@/path/to/your/document.pdf" \
     -F "collection_name=your_collection_name"
   ```

3. Or use the interactive API docs at http://localhost:8000/docs:
   - Navigate to POST `/files/upload`
   - Click "Try it out"
   - Choose your file
   - Specify collection name
   - Execute

## Ingest Code from GitLab

1. Ensure GitLab credentials are set in `.env`:
   - GITLAB_TOKEN
   - GITLAB_PROJECT_ID

2. Use the code ingestion endpoint:
   ```bash
   curl -X POST "http://localhost:8000/files/ingest-gitlab-code" \
     -H "Content-Type: application/json" \
     -d '{
       "project_id": "your-project-id",
       "collection_name": "code_collection",
       "branch": "main",
       "file_extensions": [".py", ".js", ".ts"]
     }'
   ```

3. Supported code languages:
   - Python (.py)
   - JavaScript (.js)
   - TypeScript (.ts, .tsx)
   - PHP (.php)

## Check Ingestion Status

4. Get collection statistics:
   ```bash
   curl -X GET "http://localhost:8000/files/collections/<collection_name>/stats"
   ```

5. List all collections:
   ```bash
   curl -X GET "http://localhost:8000/files/collections"
   ```

## Delete Documents

6. Delete a specific collection:
   ```bash
   curl -X DELETE "http://localhost:8000/files/collections/<collection_name>"
   ```

## Tips

- Use descriptive collection names for organization
- For large documents, ingestion may take time
- Monitor logs for ingestion progress
- Documents are chunked semantically for better retrieval
- Code is parsed using AST for better semantic chunking
- Japanese text is supported with optimized chunking

## Troubleshooting

- If upload fails: check file size limits and format support
- If GitLab ingestion fails: verify token permissions and project access
- Check server logs for detailed error messages
