# Migration Guide: FAISS to ChromaDB

This document provides a comprehensive guide for migrating from FAISS to ChromaDB vector storage.

## Overview

**Migration Date**: 2025-11-12
**Previous Vector Store**: FAISS (Facebook AI Similarity Search)
**New Vector Store**: ChromaDB with Docker containerization
**Reason for Migration**: Better scalability, easier management, and Docker-based deployment

## What Changed

### 1. Vector Store Implementation

**File**: `app/rag/vector_store.py`

**Before**:
- Used FAISS (Facebook AI Similarity Search)
- Manual index management with save/load operations
- Multiple index types (flat, IVF, HNSW)
- Metadata stored separately in pickle files
- File-based persistence

**After**:
- Uses ChromaDB vector database
- Automatic persistence handled by Chroma
- Single collection-based storage
- Metadata integrated into Chroma documents
- HTTP API access to Chroma service

### 2. Dependencies

**File**: `pyproject.toml`

**Removed**:
```toml
"llama-index-vector-stores-faiss>=0.5.1"
"faiss-cpu>=1.12.0"
```

**Added**:
```toml
"chromadb>=0.5.0"
"langchain-chroma>=0.1.0"
```

### 3. Configuration

**New File**: `app/config/chroma_config.py`

**Environment Variables Added** (`.env`):
```bash
CHROMA_HOST=localhost
CHROMA_PORT=8001
CHROMA_COLLECTION_NAME=rag_documents
CHROMA_AUTH_TOKEN=rag_token_123
```

### 4. Docker Infrastructure

**New File**: `docker-compose.yml`

- ChromaDB service with HTTP API
- Persistent Docker volume: `chroma_data`
- Port mapping: 8001 (default)
- Health checks included

## Migration Impact

### Breaking Changes

1. **Storage Location**: Vector data now stored in Docker volume instead of `vector_store/` directory
2. **API Interface**: Chroma uses HTTP API instead of direct file access
3. **Similarity Scores**: Chroma returns distances (0-1 range), converted to similarities in code

### Non-Breaking Changes

1. **Service Interface**: `VectorStoreService` maintains same public methods
2. **API Endpoints**: All REST endpoints remain unchanged
3. **Document Format**: LlamaIndex `Document` objects still used

## Data Migration

### Option 1: Start Fresh (Recommended)

Since FAISS data was cleared during migration (as per requirements), simply:

1. Start ChromaDB: `docker-compose up -d`
2. Ingest documents: `POST /ingest`
3. Verify: `GET /ingest/stats`

### Option 2: Manual Data Migration (If Needed)

If you have FAISS data to migrate:

1. Export documents from FAISS (if possible)
2. Reformat to Chroma schema
3. Use Chroma's `add()` API to import
4. Verify integrity with search queries

## Verification Steps

After migration, verify:

1. **ChromaDB Service**:
   ```bash
   curl http://localhost:8001/api/v1/heartbeat
   # Should return: {"nanosecond heartbeat": 1234567890}
   ```

2. **Document Ingestion**:
   ```bash
   curl -X POST "http://localhost:8000/ingest" \
     -H "Content-Type: application/json" \
     -d '{"recursive": true}'
   ```

3. **Vector Store Stats**:
   ```bash
   curl http://localhost:8000/ingest/stats
   ```

4. **Search Functionality**:
   ```bash
   curl -X POST "http://localhost:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{"query": "test search", "top_k": 3}'
   ```

5. **Chroma Collection**:
   ```bash
   curl -X POST "http://localhost:8001/api/v1/collections/rag_documents/count"
   # Should return document count
   ```

## Testing

### Unit Tests

Test individual components:

```bash
# Test embeddings
uv run python -c "from app.rag.embeddings import get_embedding_service; print('Embeddings OK')"

# Test vector store
uv run python -c "from app.rag.vector_store import get_vector_store_service; print('Vector store OK')"

# Test Chroma client connection
uv run python -c "from app.config.chroma_config import get_chroma_client; client = get_chroma_client(); print(f'Chroma client OK: {client.heartbeat()}')"
```

### Integration Tests

Test full RAG pipeline:

```bash
# 1. Ingest documents
# 2. Query documents
# 3. Verify results
# 4. Clear and repeat
```

## Troubleshooting

### Common Issues

1. **Chroma Connection Error**
   ```
   Error: Cannot connect to Chroma server
   Solution: Ensure docker-compose is running: docker-compose up -d
   ```

2. **Authentication Error**
   ```
   Error: Unauthorized access to Chroma
   Solution: Check CHROMA_AUTH_TOKEN matches in .env and docker-compose.yml
   ```

3. **Collection Not Found**
   ```
   Error: Collection rag_documents does not exist
   Solution: The collection is created automatically on first use
   ```

4. **Similarity Score Differences**
   ```
   Note: Chroma uses cosine distance (0-1), converted to similarity in code
   Similarity = 1 - distance
   ```

### Debug Commands

```bash
# Check Chroma health
curl http://localhost:8001/api/v1/heartbeat

# List collections
curl http://localhost:8001/api/v1/collections

# Get collection info
curl http://localhost:8001/api/v1/collections/rag_documents

# View Docker logs
docker-compose logs -f chroma

# Restart Chroma
docker-compose restart chroma
```

## Rollback Plan

If issues arise and rollback is needed:

1. **Stop Chroma**: `docker-compose down`
2. **Revert Code**: Git revert to commit before migration
3. **Restore FAISS**: Restore `vector_store/` directory from backup
4. **Reinstall Dependencies**: `uv sync`
5. **Verify**: Test search functionality

### Git Commands for Rollback

```bash
# Find migration commit
git log --oneline

# Revert to previous state
git revert <migration-commit-hash>

# Or checkout previous commit
git checkout <previous-commit-hash>
```

## Performance Considerations

### Chroma vs FAISS

- **Indexing Speed**: Chroma similar to FAISS Flat index
- **Query Speed**: Chroma optimized for production use
- **Scalability**: Chroma better for larger document sets
- **Memory Usage**: Chroma manages memory more efficiently
- **Persistence**: Chroma automatic vs FAISS manual saves

### Optimization Tips

1. **Collection Management**:
   - Use meaningful collection names
   - Clean old collections periodically

2. **Query Performance**:
   - Adjust `n_results` in queries
   - Use appropriate similarity thresholds

3. **Docker Resources**:
   - Allocate sufficient memory to Docker
   - Monitor disk usage for persistent volume

## Best Practices

### Development

1. **Always start ChromaDB first**: `docker-compose up -d`
2. **Use appropriate similarity thresholds**: 0.7-0.8 works well
3. **Monitor Chroma logs**: `docker-compose logs -f chroma`
4. **Test with small datasets first**: Then scale up

### Production

1. **Secure Chroma**: Change default auth token
2. **Backup volumes**: Regular backup of `chroma_data` volume
3. **Monitor performance**: Track query times and memory usage
4. **Scale resources**: Adjust Docker resources as needed

## Support and Resources

### Documentation

- ChromaDB: https://docs.trychroma.com
- LangChain Chroma: https://python.langchain.com/docs/integrations/vectorstores/chroma
- LlamaIndex: https://docs.llamaindex.ai

### Community

- ChromaDB Discord: https://discord.gg/MMeYNTmh3x
- GitHub Issues: For bug reports and feature requests

## Migration Summary

Successfully migrated from FAISS to ChromaDB with:
- ✅ Docker containerization
- ✅ Persistent storage
- ✅ Maintained API compatibility
- ✅ Improved scalability
- ✅ Easier management

**Migration Completed**: 2025-11-12
**Migrationed By**: Claude Code
**Review Status**: Pending review and testing
