# Vector Database Provider

This module implements the **Provider Pattern** for vector database dependency injection.

## Overview

The `VectorDatabaseProvider` centralizes the management of vector database instances, making it easy to:
- Switch between different vector database implementations
- Configure the vector database at application startup
- Use dependency injection in FastAPI routes
- Test with mock implementations

## Usage

### Default Configuration (Qdrant)

By default, the provider uses `QdrantVectorStore`. No configuration needed:

```python
from app.infrastructure.provider.vector_database_provider import get_vector_database

# In your route or service
vector_db = get_vector_database()
```

### FastAPI Dependency Injection

Use with FastAPI's `Depends()`:

```python
from fastapi import Depends
from app.infrastructure.provider.vector_database_provider import get_vector_database
from app.domain.knowledge_base.ports import VectorStorePort

@app.post("/endpoint")
async def my_endpoint(vector_store: VectorStorePort = Depends(get_vector_database)):
    # Use vector_store
    pass
```

### Configure Different Implementation

To use a different vector database, configure at startup:

```python
from app.infrastructure.provider.vector_database_provider import configure_vector_database
from app.infrastructure.pinecone_vector_store import PineconeVectorStore

# In your FastAPI lifespan or startup event
def configure_app():
    pinecone_store = PineconeVectorStore(api_key="your-api-key")
    configure_vector_database(pinecone_store)
```

## Architecture

```
┌─────────────────────────────────────┐
│  FastAPI Routes / Services          │
│  (Depends on VectorStorePort)       │
└─────────────┬───────────────────────┘
              │ Dependency Injection
              ▼
┌─────────────────────────────────────┐
│  VectorDatabaseProvider              │
│  (Singleton, manages instance)       │
└─────────────┬───────────────────────┘
              │ Returns configured
              ▼
┌─────────────────────────────────────┐
│  VectorStorePort Interface           │
│  (Abstract interface)                │
└─────────────┬───────────────────────┘
              │ Implemented by
              ▼
┌─────────────────────────────────────┐
│  QdrantVectorStore / Others          │
│  (Concrete implementations)          │
└─────────────────────────────────────┘
```

## Files

- `vector_database_provider.py` - Provider class and dependency injection functions
- `example_configuration.py` - Examples of how to configure different implementations

## Benefits

✅ **Centralized Configuration** - One place to configure vector database  
✅ **Easy Switching** - Change implementation in one line  
✅ **Testability** - Easy to inject mock implementations for testing  
✅ **Type Safety** - All dependencies use `VectorStorePort` interface  
✅ **Singleton Pattern** - Ensures consistent instance across application
