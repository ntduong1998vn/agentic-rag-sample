# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Agentic RAG — a Retrieval-Augmented Generation system with multi-agent orchestration built on Clean Architecture principles. Features Japanese document processing, semantic chunking, vector search, and conversational AI powered by Google Gemini.

**Python 3.12 | FastAPI | LangChain/LangGraph | Google Gemini | Qdrant | PostgreSQL**

## Common Commands

### Package Manager: uv (not pip/poetry)
```bash
uv sync                              # Install all dependencies
uv add package-name                  # Add dependency
uv add --dev package-name            # Add dev dependency
```

### Development Server
```bash
docker-compose up -d                 # Start PostgreSQL, Qdrant, pgAdmin
uv run alembic upgrade head          # Apply database migrations
uv run python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
uv run streamlit run streamlit_app.py  # Streamlit UI on port 8501
```

### Testing
```bash
uv run pytest                                     # All tests
uv run pytest tests/test_file.py                  # Single file
uv run pytest tests/test_file.py::test_fn         # Single test
uv run pytest --cov=app --cov-report=html         # With coverage
uv run pytest -v -s                               # Verbose with stdout
```

### Database Migrations (Alembic)
```bash
uv run alembic revision --autogenerate -m "desc"  # Create migration
uv run alembic upgrade head                       # Apply
uv run alembic downgrade -1                       # Rollback one
```

## Architecture

### Clean Architecture Layers
```
API (app/api/) → Services (app/services/) → Models (app/models/) → DB (app/db/)
```
- **app/api/**: FastAPI routes, Pydantic request/response schemas. v1 = legacy endpoints, v2 = router agent
- **app/services/**: Business logic. Services receive DB sessions via FastAPI dependency injection (`app/api/deps.py`)
- **app/models/**: SQLAlchemy ORM models with UUID primary keys and timestamps
- **app/schemas/**: Pydantic v2 validation schemas with `ConfigDict(from_attributes=True)` for ORM compat
- **app/core/config.py**: Centralized Pydantic Settings — access via `from app.core.config import settings`
- **app/core/logging.py**: Centralized logging — use `from app.core.logging import get_logger`

### Multi-Agent System (LangGraph)

**Router/Supervisor** (`app/agents/router_agent.py`) orchestrates four specialized agents:

| Agent | Directory | Purpose |
|-------|-----------|---------|
| `gitlab_agent` | `app/agents/workflows/gitlab_agent/` | Code analysis from GitLab repos |
| `rag_agent` | `app/agents/workflows/rag_agent/` | Document retrieval & Q&A |
| `ba_agent` | `app/agents/workflows/ba_agent/` | Business analysis, impact/gap analysis |
| `qc_agent` | `app/agents/workflows/qc_agent/` | Manual test case generation |

Key patterns:
- **Supervisor dispatches** via LangChain `create_agent` with sub-agents as tools
- **Only the supervisor uses a checkpointer** (LangGraph checkpoint in PostgreSQL) for conversation memory; sub-agents are stateless
- **Skills pattern**: Progressive prompt disclosure — agent-specific instructions in `skills/Skill.md` files loaded on demand via `load_skill` tool, reducing upfront token usage
- **Middleware**: `SummarizationMiddleware`, `TodoListMiddleware`, `FilesystemFileSearchMiddleware` added per-agent as needed
- **Pre-created agents**: Agents are cached to avoid recreation on each request

### RAG Pipeline (`app/rag/`)

```
Document Ingestion (Unstructured) → Token-based Semantic Chunking → Gemini Embeddings (768d)
→ Qdrant Vector Store → Enhanced Retriever → Gemini LLM Generation (streaming)
```

- **Embeddings**: `app/rag/embeddings/` (Gemini, OpenAI)
- **LLMs**: `app/rag/llms/` (Gemini, OpenAI)
- **Vector stores**: `app/rag/vectorstores/` (Qdrant, S3)
- **Retrievers**: `app/rag/retrievers/`
- **Pipelines**: `app/rag/pipelines/` (document processing)

### Unit Test Request Workflow
When a user requests test cases, the supervisor evaluates spec completeness (5 criteria). If < 3 criteria met, routes to BA Agent first to enrich the spec, then to QC Agent. If >= 3, routes directly to QC Agent.

## Code Conventions

- **Type hints required** on all function parameters and return values
- **Import order**: stdlib → third-party → local (`app.*`)
- **Naming**: PascalCase classes, snake_case functions/variables, UPPER_SNAKE_CASE constants
- **DB models**: UUID primary keys, `created_at`/`updated_at` timestamps, explicit `__tablename__`
- **Config access**: Always `from app.core.config import settings` (never hardcode)
- **Logging**: Always `from app.core.logging import get_logger`
- **Exceptions**: Use custom exceptions from `app.core.exceptions` in services; convert to `HTTPException` in API layer

## Creating a New Agent

1. Create `app/agents/workflows/my_agent/` with `__init__.py`, `agent.py`, `prompts.py`, and optional `skills/`
2. Implement `create_my_agent()` and `run_my_agent()` in `agent.py`
3. Register as a tool in `router_agent.py` and update `SUPERVISOR_SYSTEM_PROMPT`
4. Add middleware as needed (TodoList, Summarization, FilesystemFileSearch)

## Environment

Required env vars (see `.env.example`): `GOOGLE_API_KEY`, `POSTGRES_*`, `QDRANT_HOST/PORT`. Optional: `GITLAB_TOKEN`, `LANGSMITH_*` for tracing.

Docker services: PostgreSQL 15 (5432), Qdrant (6333/6334), pgAdmin (5050).
