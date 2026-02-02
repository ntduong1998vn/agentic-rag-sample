# Agent Developer Guide

This guide provides essential information for AI coding agents working in this repository.

## Project Overview

**Agentic RAG Sample** - A Retrieval-Augmented Generation system with agentic capabilities built using Clean Architecture principles, FastAPI, LangChain, and Google Gemini.

## Build, Lint & Test Commands

### Package Management
This project uses **uv** as the package manager (not pip or poetry).

```bash
# Install dependencies
uv sync

# Add a new dependency
uv add package-name

# Add a dev dependency
uv add --dev package-name
```

### Development Server
```bash
# Start FastAPI development server with hot reload
uv run python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Access API docs at http://localhost:8000/docs
```

### Testing
```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_file.py

# Run specific test function
uv run pytest tests/test_file.py::test_function_name

# Run with coverage report
uv run pytest --cov=app --cov-report=html

# Run tests with output
uv run pytest -v -s

# Run async tests (requires pytest-asyncio)
uv run pytest -v tests/
```

### Database Migrations
```bash
# Create a new migration (autogenerate from models)
uv run alembic revision --autogenerate -m "description of changes"

# Apply migrations
uv run alembic upgrade head

# Rollback one migration
uv run alembic downgrade -1

# Show current revision
uv run alembic current

# Show migration history
uv run alembic history
```

### Docker Services
```bash
# Start all services (PostgreSQL, Qdrant, pgAdmin)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Restart services
docker-compose restart
```

## Project Structure (Clean Architecture)

```
app/
├── api/              # HTTP layer (FastAPI routes, request/response models)
│   ├── deps.py       # Dependency injection (database sessions, etc.)
│   ├── v1/           # API version 1
│   └── v2/           # API version 2
├── agents/           # LangGraph agents and workflows
├── core/             # Core application code
│   ├── config.py     # Centralized configuration (Pydantic Settings)
│   ├── exceptions.py # Custom exception classes
│   └── logging.py    # Centralized logging setup
├── db/               # Database layer
│   ├── base.py       # SQLAlchemy Base
│   ├── session.py    # Database session management
│   └── checkpointer.py # LangGraph checkpoint management
├── models/           # SQLAlchemy ORM models (database entities)
├── schemas/          # Pydantic schemas (API validation)
├── services/         # Business logic and use cases
├── rag/              # RAG components
│   ├── embeddings/   # Embedding implementations (Gemini, OpenAI)
│   ├── llms/         # LLM implementations
│   ├── vectorstores/ # Vector store implementations (Qdrant, S3)
│   └── retrievers/   # Retrieval logic
└── main.py           # FastAPI application entry point
```

## Code Style Guidelines

### Import Organization
Follow this order for imports:
1. Standard library imports
2. Third-party library imports (FastAPI, SQLAlchemy, etc.)
3. Local application imports (app.*)

```python
# Standard library
from typing import List, Optional
from uuid import UUID

# Third-party
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

# Local
from app.api.deps import get_db
from app.schemas.chatbot import Chatbot, ChatbotCreate
from app.services.chatbot import ChatbotService
```

### Type Hints
**REQUIRED** - Always use type hints for function parameters and return values:

```python
def get_chatbot(self, chatbot_id: UUID) -> Optional[Chatbot]:
    """Get a chatbot by ID."""
    return self.db.query(Chatbot).filter(Chatbot.id == chatbot_id).first()

async def process_document(file_path: str, collection_name: str) -> dict:
    """Process and ingest document."""
    # implementation
```

### Docstrings
Use triple-quoted docstrings for modules, classes, and functions:

```python
"""
Module-level docstring.
"""

class ChatbotService:
    """Service for chatbot operations."""
    
    def create_chatbot(self, chatbot_in: ChatbotCreate) -> Chatbot:
        """Create a new chatbot."""
```

### Naming Conventions
- **Classes**: PascalCase (e.g., `ChatbotService`, `ChatbotCreate`)
- **Functions/Methods**: snake_case (e.g., `get_chatbot`, `create_chatbot`)
- **Variables**: snake_case (e.g., `chatbot_id`, `db_session`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `MAX_TOKENS`, `DEFAULT_MODEL`)
- **Private methods**: Prefix with underscore (e.g., `_internal_method`)

### Database Models (SQLAlchemy)
- Use `UUID` as primary key with `uuid.uuid4` default
- Include `created_at` and `updated_at` timestamps
- Use `__tablename__` explicitly

```python
import uuid
from sqlalchemy import Column, String, JSON, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.base import Base

class Chatbot(Base):
    __tablename__ = "chatbots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
```

### Pydantic Schemas
- Use `BaseModel` for API schemas
- Inherit from base schemas for DRY principle
- Use `ConfigDict(from_attributes=True)` for ORM compatibility

```python
from pydantic import BaseModel, ConfigDict
from uuid import UUID

class ChatbotBase(BaseModel):
    """Base chatbot schema."""
    name: str
    model_name: str

class ChatbotCreate(ChatbotBase):
    """Schema for creating a chatbot."""
    pass

class Chatbot(ChatbotBase):
    """Schema for chatbot response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    created_at: datetime
```

### Error Handling
Use custom exceptions from `app.core.exceptions`:

```python
from app.core.exceptions import NotFoundError, ValidationError

# In services
if not chatbot:
    raise NotFoundError("Chatbot not found", details={"id": chatbot_id})

# In API endpoints (convert to HTTPException)
from fastapi import HTTPException

if not chatbot:
    raise HTTPException(status_code=404, detail="Chatbot not found")
```

### Configuration
Always use centralized configuration from `app.core.config.settings`:

```python
from app.core.config import settings

# Access configuration
api_key = settings.google_api_key
db_url = settings.database_url
qdrant_host = settings.qdrant_host
```

### Dependency Injection
Use FastAPI's dependency injection system:

```python
from fastapi import Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db

@router.post("/")
def create_chatbot(
    chatbot_in: ChatbotCreate,
    db: Session = Depends(get_db),
) -> Chatbot:
    service = ChatbotService(db)
    return service.create_chatbot(chatbot_in)
```

### Database Sessions
Always use the dependency injection pattern for database sessions:

```python
# In endpoints
def endpoint(db: Session = Depends(get_db)):
    # Use db here
    pass

# The session is automatically closed after the request
```

## Testing Guidelines

- Place tests in `tests/` directory
- Use pytest fixtures for setup/teardown
- Use `pytest-asyncio` for async tests
- Mock external dependencies (APIs, databases)

## Environment Variables

Required environment variables (see `.env.example`):
- `GOOGLE_API_KEY` - Google Gemini API key
- `POSTGRES_*` - PostgreSQL connection details
- `QDRANT_HOST`, `QDRANT_PORT` - Qdrant vector database
- `GITLAB_TOKEN`, `GITLAB_PROJECT_ID` - GitLab integration (optional)

## Key Technologies

- **Python**: 3.12+
- **Framework**: FastAPI
- **ORM**: SQLAlchemy 2.0
- **Migrations**: Alembic
- **Validation**: Pydantic v2
- **Vector DB**: Qdrant
- **LLM Framework**: LangChain, LangGraph
- **LLM Provider**: Google Gemini
- **Package Manager**: uv

## Important Notes

1. **Clean Architecture**: Follow the layered architecture. API → Services → Models/DB
2. **Type Safety**: Always use type hints
3. **Database**: PostgreSQL with UUID primary keys and timestamps
4. **Async**: This codebase uses both sync and async code. Check existing patterns
5. **Logging**: Use `from app.core.logging import get_logger` for logging
6. **Never commit**: `.env` files, `__pycache__`, `.venv/`, `logs/`
7. When you need to search docs, use `context7` tools.

## Multi-Agent System

This project implements a **multi-agent architecture** with a supervisor/router pattern for coordinating specialized agents.

### Available Agents

#### 1. Router/Supervisor Agent (`app/agents/router_agent.py`)
**Role:** Orchestrates and routes user requests to specialized agents

**Capabilities:**
- Evaluates user requests and determines which agent(s) to invoke
- Maintains conversation context via checkpointer
- Synthesizes responses from multiple agents when needed
- **Special workflow for unit test requests** - evaluates spec completeness

**Tools:**
- `gitlab_agent` - Code-related queries
- `rag_agent` - Document retrieval
- `ba_agent` - Business analysis
- `qc_agent` - Manual test case generation
- `load_supervisor_skill` - Evaluation criteria for test requests

#### 2. GitLab Agent (`app/agents/workflows/gitlab_agent/`)
**Role:** Answer code-related questions from GitLab repositories

**Use Cases:**
- Source code analysis
- Architecture documentation
- Implementation details
- Code search and debugging

#### 3. RAG Agent (`app/agents/workflows/rag_agent/`)
**Role:** Document retrieval and Q&A

**Use Cases:**
- General document search
- Knowledge base queries
- Policy/guide lookup
- PDF/Word/Excel document Q&A

#### 4. BA Agent (`app/agents/workflows/ba_agent/`)
**Role:** Business analysis and requirements gathering

**Capabilities:**
- Analyzes raw specifications
- Performs Impact Analysis (screens, APIs, DB affected)
- Performs Gap Analysis (missing logic, inconsistencies)
- Creates comprehensive BA reports

**Tools:**
- `search_knowledge_base` - Find related system documentation
- `write_todos` - Track analysis tasks (TodoListMiddleware)

#### 5. QC Agent (`app/agents/workflows/qc_agent/`) **[NEW]**
**Role:** Generate comprehensive manual unit test cases

**Capabilities:**
- Creates tabular test case documentation for QA testers
- Applies 10 testing Points of View (POVs) for thorough coverage
- Uses LangChain skills pattern with progressive prompt disclosure
- Searches reference files for templates and guidelines

**Tools:**
- `Glob` - Find reference files (*.md, templates) via FilesystemFileSearchMiddleware
- `Grep` - Search content within reference files via FilesystemFileSearchMiddleware
- `load_skill` - Load QC skill instructions
- `search_knowledge_base` - Find related features
- `write_todos` - Track test generation progress (TodoListMiddleware)

**Middleware:**
- `FilesystemFileSearchMiddleware` - Provides Glob and Grep tools for file search
- `TodoListMiddleware` - Task tracking
- `SummarizationMiddleware` - Context window management

**Skills Structure:**
```
app/agents/workflows/qc_agent/skills/
├── Skill.md                      # Instructions for writing test cases
└── references/
    ├── pov.md                    # 10 testing POVs (Functional, Security, etc.)
    └── unit_test_template.md    # Tabular test case template
```

**10 Testing POVs:**
1. Functional (positive/negative/boundary)
2. Data Validation (formats, types, constraints)
3. State & Flow (transitions, workflows)
4. Business Rules (calculations, conditions)
5. Security (authorization, authentication)
6. Error Handling (messages, recovery)
7. Integration (APIs, external systems)
8. Usability (UX, accessibility)
9. Performance (response times, scalability)
10. Regression Risk (criticality, prioritization)

### Unit Test Request Workflow

When a user requests to **write unit tests** or **create test cases**:

```
User: "Write unit tests for [feature]"
              │
              ▼
┌─────────────────────────────┐
│   Supervisor Agent          │
│   1. load_supervisor_skill()│
│   2. Evaluate completeness  │
└─────────────────────────────┘
              │
    Check 5 criteria:
    1. Feature name?
    2. Acceptance criteria?
    3. Input/output specs?
    4. Business rules?
    5. Edge cases?
              │
    ┌─────────┴──────────┐
    │ < 3 criteria ✓     │ ≥ 3 criteria ✓
    ▼                    ▼
┌──────────┐      ┌──────────┐
│ BA Agent │      │ QC Agent │
│ (enrich) │      │ (direct) │
└──────────┘      └──────────┘
    │                    │
    └────────┬───────────┘
             ▼
      ┌──────────┐
      │ QC Agent │
      │ (write   │
      │  tests)  │
      └──────────┘
             │
             ▼
    Test Cases Table
    (markdown format)
```

### Skills Pattern (LangChain)

This project uses LangChain's **skills pattern** for progressive prompt disclosure:

**Supervisor Skill** (`app/agents/skills/Skill.md`):
- Evaluation criteria for test request completeness
- Decision logic for routing to BA → QC or QC directly

**QC Skill** (`app/agents/workflows/qc_agent/skills/Skill.md`):
- Detailed instructions for writing test cases
- Workflow steps and best practices
- Tool usage guide (Glob, Grep)

**Benefits:**
- Specialized prompts loaded on-demand
- Reduces upfront token usage
- Easier to maintain and update agent knowledge
- Team can develop skills independently

### Creating a New Agent

Follow the existing patterns:

1. **Create agent directory:**
   ```
   app/agents/workflows/my_agent/
   ├── __init__.py
   ├── agent.py         # create_my_agent(), run_my_agent()
   ├── prompts.py       # MY_AGENT_SYSTEM_PROMPT
   └── skills/          # (optional) Skills and references
   ```

2. **Implement agent functions:**
   - `create_my_agent()` - Use `create_agent()` with tools and middleware
   - `run_my_agent()` - Async function to invoke agent

3. **Add to router:**
   - Create `create_my_agent_tool()` in `router_agent.py`
   - Add tool to supervisor's tools list
   - Update `SUPERVISOR_SYSTEM_PROMPT` with agent description

4. **Use middleware as needed:**
   - `TodoListMiddleware` - Task tracking
   - `SummarizationMiddleware` - Long conversation handling
   - Custom middleware - Implement `AgentMiddleware`

### Agent Development Best Practices

1. **Stateless sub-agents** - Only supervisor uses checkpointer for conversation memory
2. **Tool caching** - Pre-create agents for reuse (avoid creating on every call)
3. **Clear prompts** - Define agent role, capabilities, and decision logic
4. **Type hints** - Always use type hints for all parameters and returns
5. **Logging** - Use `get_logger(__name__)` for debugging
6. **Error handling** - Wrap agent calls in try/except, return error messages
7. **Skills pattern** - For complex agents, use skills for progressive disclosure
7. When you need to search docs, use `context7` tools.