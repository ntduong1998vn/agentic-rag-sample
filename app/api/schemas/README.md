# API Schemas

This folder contains Pydantic schema definitions for API request and response models, organized by domain.

## Structure

```
schemas/
├── chatbot.py           # Chatbot-related schemas
└── knowledge_base.py    # Knowledge base and document schemas
```

## Schema Files

### `chatbot.py`
Contains schemas for chatbot management:
- **ChatbotCreate** - Request schema for creating a new chatbot
- **ChatbotUpdate** - Request schema for updating an existing chatbot
- **ChatbotResponse** - Response schema for chatbot data

### `knowledge_base.py`
Contains schemas for knowledge base operations:
- **IngestRequest** - Request schema for document ingestion
- **IngestResponse** - Response schema for ingestion results
- **DocumentResponse** - Response schema for document information
- **KnowledgeBaseStats** - Response schema for knowledge base statistics

## Design Principles

✅ **Domain Organization** - Schemas grouped by business domain/resource  
✅ **Clear Naming** - Descriptive names indicating purpose (Create/Update/Response)  
✅ **Separation of Concerns** - API schemas separate from route logic  
✅ **Reusability** - Schemas can be imported and reused across routes  
✅ **Documentation** - Each schema includes docstrings and field descriptions

## Usage

Import schemas in route files:

```python
from app.api.schemas.chatbot import ChatbotCreate, ChatbotResponse
from app.api.schemas.knowledge_base import IngestRequest, IngestResponse

@router.post("/", response_model=ChatbotResponse)
async def create_chatbot(request: ChatbotCreate):
    # ...
```

## Adding New Schemas

When adding new API endpoints:

1. Create a new schema file in this folder if it's a new domain (e.g., `user.py`)
2. Add schemas to an existing file if they belong to an existing domain
3. Follow the naming convention: `{Resource}{Action}` (e.g., `UserCreate`, `UserUpdate`)
4. Include docstrings and field descriptions for API documentation
