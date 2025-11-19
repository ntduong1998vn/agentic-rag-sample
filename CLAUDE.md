# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a fully implemented **agentic-rag** system with conversational AI capabilities - a retrieval-augmented generation system with agentic capabilities for in-house chatbot applications. The system features complete RAG functionality with Japanese semantic chunking, Voyage AI embeddings, **Qdrant vector storage**, and Google Gemini 2.5 Flash-Lite integration for intelligent conversational responses.

## Major Updates: v1.2.0+ Features

### New: GitLab Code Integration
As of version 1.2.0, the system includes **GitLab repository integration** with AST-based code chunking for Python, JavaScript, TypeScript, and PHP. This allows you to:
- Ingest entire GitLab repositories into the vector store
- Extract structured code chunks at file, class, and function levels
- Search code semantically with rich metadata
- Query code alongside documents for comprehensive answers

### New: PostgreSQL Database Integration
The system now includes **comprehensive ingestion tracking** with PostgreSQL:
- Track ingestion jobs and file processing status
- Monitor processing statistics and error rates
- Database-backed persistence for operational metrics
- Alembic migrations for schema management

### New: Qdrant Migration (from ChromaDB)
The system has migrated from ChromaDB to **Qdrant vector database**:
- Better performance and scalability
- Repository-specific collections instead of global defaults
- Enhanced configuration management
- Improved collection operations

## Development Environment

- **Python**: 3.12.0 (specified in `.python-version`)
- **Package Manager**: uv (modern Python package manager, version 0.9.2)
- **Web Framework**: FastAPI
- **Platform**: Windows-based development

## Common Development Commands

### Environment Setup
```bash
uv sync                    # Install dependencies and create virtual environment
uv venv                    # Create new virtual environment
```

### Running Applications
```bash
# Start all services (Qdrant + PostgreSQL + pgAdmin)
docker-compose up -d                                 # Start all services in background
docker-compose down                                  # Stop all services
docker-compose logs -f                               # View service logs

# Start the RAG API server
uv run python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000  # Start with auto-reload
uv run python -m uvicorn app.main:app --host 0.0.0.0 --port 8080           # Custom port without reload
# Note: The original `uv run python main.py` commands are not applicable due to project restructure
```

### Dependency Management
```bash
uv add <package>          # Add new dependencies to pyproject.toml
uv pip install <package>  # Install packages in current environment
uv lock                   # Update lock file with latest versions
```

### GitLab Connector Dependencies

The GitLab integration requires these additional packages (installed via `uv sync`):
- `python-gitlab` - GitLab API client
- `tree-sitter` - Generic AST parsing library
- `tree-sitter-python` - Python AST grammar
- `tree-sitter-javascript` - JavaScript AST grammar
- `tree-sitter-typescript` - TypeScript AST grammar
- `tree-sitter-php` - PHP AST grammar

## Current Project Structure

```
agentic-rag/
├── app/                     # FastAPI application modules
│   ├── __init__.py         # Package initialization
│   ├── main.py             # FastAPI application entry point
│   │
│   ├── config/             # Configuration modules
│   │   ├── __init__.py
│   │   ├── logging_config.py      # Application logging configuration
│   │   ├── qdrant_config.py       # Qdrant vector database configuration
│   │   └── settings.py            # Centralized configuration (NEW)
│   │
│   ├── connectors/         # External service connectors
│   │   ├── __init__.py
│   │   └── gitlab_connector.py    # GitLab API integration
│   │
│   ├── dto/                # Data transfer objects (Pydantic models)
│   │   ├── __init__.py
│   │   ├── chat.py                # Chat API models
│   │   ├── ingestion.py           # Document ingestion models
│   │   └── code_ingestion.py      # GitLab code models
│   │
│   ├── models/             # SQLAlchemy database models (NEW)
│   │   ├── __init__.py
│   │   ├── database.py            # Database connection and session management
│   │   └── ingestion.py           # Ingestion tracking models
│   │
│   ├── rag/                # RAG system modules (document processing)
│   │   ├── __init__.py
│   │   ├── ast_splitter.py        # AST-based code parsing for 4 languages
│   │   ├── code_ingestion.py      # GitLab code orchestration
│   │   ├── embeddings.py          # Voyage AI embedding generation
│   │   ├── ingestion.py           # Document ingestion pipeline
│   │   ├── semantic_splitter.py   # Japanese semantic chunking
│   │   └── vector_store.py        # Qdrant vector storage and retrieval
│   │
│   ├── routers/            # API route definitions
│   │   ├── __init__.py
│   │   ├── chat.py                # Chat endpoints
│   │   ├── code_ingestion.py      # GitLab code endpoints
│   │   └── ingestion.py           # Document management endpoints
│   │
│   ├── services/           # Business logic services
│   │   ├── __init__.py
│   │   ├── chatbot_service.py     # Chat and LLM integration
│   │   ├── gitlab_service.py      # GitLab business logic
│   │   └── rag_service.py         # Core RAG operations
│   │
│   └── utils/              # Utility modules
│       ├── __init__.py
│       └── session_manager.py     # Conversation session management
│
├── alembic/               # Database migrations (NEW)
│   ├── versions/          # Migration files
│   └── alembic.ini        # Migration configuration
│
├── data/                  # Document storage directory
├── docs/                  # Documentation files (NEW)
├── logs/                  # Application logs (NEW)
├── qdrant_data/          # Qdrant data volume (created by Docker)
├── tests/                 # Comprehensive test suite (NEW)
│   ├── __init__.py
│   ├── conftest.py        # Test configuration
│   ├── integration/       # Integration tests
│   └── unit/              # Unit tests
│
├── .env                   # Environment variables (API keys)
├── .env.example           # Environment variables template
├── .gitignore             # Git ignore rules
├── .python-version        # Python version specification
├── CLAUDE.md              # Project documentation (this file)
├── README.md              # Project readme
├── alembic.ini            # Database migration configuration (NEW)
├── docker-compose.yml     # Multi-service Docker configuration (Qdrant + PostgreSQL + pgAdmin)
├── pyproject.toml         # Project configuration and dependencies
└── uv.lock                # Locked dependency versions
```

### Core Components

**Document Processing** (`app/rag/`):
- `ingestion.py` - Multi-format document ingestion with statistics tracking
- `semantic_splitter.py` - Japanese-aware semantic text chunking (currently using basic splitting)
- `embeddings.py` - Voyage AI 3.5 embedding generation with LangChain integration
- `vector_store.py` - Qdrant vector storage with repository-specific collections
- `ast_splitter.py` - AST-based code parsing for Python/JS/TS/PHP with rich metadata
- `code_ingestion.py` - GitLab code orchestration with hierarchical chunking

**Database Layer** (`app/models/` - NEW):
- `database.py` - PostgreSQL connection and session management with SQLAlchemy
- `ingestion.py` - Ingestion tracking models (IngestJob, IngestFile) with comprehensive metrics

**External Integrations** (`app/connectors/`):
- `gitlab_connector.py` - GitLab API client with rate limiting and .gitignore filtering

**Service Layer** (`app/services/`):
- `rag_service.py` - Core RAG operations with database integration
- `chatbot_service.py` - Google Gemini 2.5 Flash-Lite integration with streaming
- `gitlab_service.py` - GitLab business logic with repository-specific collections

**API Layer** (`app/routers/`):
- `ingestion.py` - Document management endpoints with statistics
- `chat.py` - Chat endpoints with streaming support
- `code_ingestion.py` - GitLab code management endpoints with search filtering

**Configuration** (`app/config/`):
- `settings.py` - Centralized Pydantic settings with environment validation
- `qdrant_config.py` - Qdrant-specific configuration and collection management
- `logging_config.py` - Structured logging with rotation and multiple outputs

**Data Models** (`app/dto/`):
- `ingestion.py` - Document ingestion API models with validation
- `chat.py` - Chat API models with streaming support
- `code_ingestion.py` - GitLab API models with comprehensive metadata

## Project Architecture

This project implements a complete **agentic RAG system with conversational AI** featuring the following components:

### Core RAG Components (✅ Fully Implemented)
- **Document Processing** (`app/rag/ingestion.py`): Multi-format file ingestion with comprehensive statistics
- **Embedding Generation** (`app/rag/embeddings.py`): Voyage AI 3.5 embedding with LangChain integration
- **Vector Database** (`app/rag/vector_store.py`): Qdrant vector database with repository-specific collections
- **Semantic Splitter** (`app/rag/semantic_splitter.py`): Japanese-aware text chunking (Note: Currently using basic splitting, semantic features disabled)
- **Database Integration** (`app/models/`): PostgreSQL ingestion tracking with SQLAlchemy ORM

### Chatbot System (✅ Fully Implemented)
- **Chatbot Service** (`app/services/chatbot_service.py`): LLM integration with Google Gemini 2.5 Flash-Lite
- **LangChain Integration**: Modern LLM framework for prompt engineering and response generation
- **Streaming Support**: Real-time response streaming for enhanced user experience
- **Stateless Processing**: Each query processed independently without session memory

### API Layer (✅ Fully Implemented)
- **FastAPI Application** (`app/main.py`): Complete FastAPI setup with comprehensive endpoints
  - `GET /` - Welcome message with API information
  - `GET /health` - Health check endpoint
  - `GET /info` - Detailed API information with features and supported file types
  - **Chat Endpoints** (`/chat`):
    - `POST /chat` - Main chat endpoint with streaming support and stateless processing
  - **Document Ingestion Endpoints** (`/ingest`):
    - `POST /ingest` - Process documents from data directory with statistics
    - `GET /ingest/documents` - List processed documents with metadata
    - `GET /ingest/stats` - Get detailed ingestion statistics
    - `DELETE /ingest/clear` - Clear all documents from vector store
  - **GitLab Code Endpoints** (`/code`):
    - `POST /code/ingest` - Ingest GitLab repository with AST parsing
    - `POST /code/search` - Search code semantically with filtering
    - `GET /code/stats` - Get repository statistics
    - `GET /code/files` - List ingested code files with pagination
    - `DELETE /code/clear` - Clear all code chunks
    - `GET /code/health` - Check GitLab connectivity

### Data Processing (✅ Fully Implemented)
- **Ingestion Pipelines**: Automated processing of Excel, PDF, Word, text files
- **Japanese Optimization**: Semantic chunking with Japanese sentence separators (。！？)
- **Knowledge Base Management**: CRUD operations with metadata tracking
- **Vector Operations**: Efficient similarity search with configurable parameters

## Development Notes

- **Current Status**: Fully implemented RAG + Chatbot system with conversational AI capabilities (v1.2.0+)
- **API Documentation**: Auto-generated at `/docs` endpoint when server is running
- **Project Status**: Production-ready with comprehensive features
- **Environment Setup**: Requires both `VOYAGE_API_KEY` and `GOOGLE_API_KEY` in `.env` file
- **Data Source**: Place documents in `/data` folder - supports Excel, PDF, Word, text files
- **Vector Storage**: Qdrant with Docker for managed vector storage and retrieval
- **Stateless Processing**: Each query processed independently without session memory
- **Docker Integration**: Multi-service setup (Qdrant + PostgreSQL + pgAdmin) with persistent volumes
- **Database Integration**: PostgreSQL with comprehensive ingestion tracking and Alembic migrations
- **Test Suite**: Comprehensive unit and integration tests (60+ tests)
- **Configuration**: Centralized Pydantic settings with environment validation

## Recent Major Changes

### Migration from ChromaDB to Qdrant (✅ Complete)
- **Performance**: Significantly improved vector operations and scalability
- **Collection Management**: Repository-specific collections prevent cross-contamination
- **Configuration**: Centralized settings with better error handling
- **Error Recovery**: Improved collection management and validation

### PostgreSQL Database Integration (✅ Complete)
- **Ingestion Tracking**: Comprehensive job and file-level tracking
- **Statistics**: Detailed metrics on processing times, success rates, errors
- **Schema Management**: Alembic migrations for reliable database updates
- **Operational Metrics**: Database-backed persistence for monitoring

### Enhanced GitLab Integration (✅ Complete)
- **Repository-Specific Collections**: Each repository gets its own Qdrant collection
- **AST-Based Parsing**: Sophisticated multi-language code analysis
- **Rich Metadata**: Function signatures, docstrings, line numbers, inheritance
- **Rate Limiting**: Respects GitLab API limits with proper backoff
- **Error Handling**: Graceful failure for individual files

## New: GitLab Integration (v1.2.0)

The system now includes **GitLab connector** with AST-based code chunking. This enables:

### GitLab Code Ingestion Pipeline
1. **GitLab Connector** (`app/connectors/gitlab_connector.py`)
   - Authenticates with GitLab using Personal Access Token
   - Recursively traverses repository tree
   - Filters by file extensions (.py, .js, .ts, .php)
   - Respects .gitignore patterns
   - Fetches file contents with metadata

2. **AST Code Splitter** (`app/rag/ast_splitter.py`)
   - Multi-language tree-sitter parsers (Python, JS, TS, PHP)
   - Extracts hierarchical chunks (file → class → function)
   - Rich metadata extraction:
     - Function/class signatures
     - Type hints and return types
     - Docstrings (Python docstrings, JSDoc, PHPDoc)
     - Decorators and visibility modifiers
     - Line numbers and navigation info
     - Parent class relationships

3. **Code Ingestion Service** (`app/rag/code_ingestion.py`)
   - Orchestrates GitLab fetching
   - Processes chunks through AST splitter
   - Prepares documents for vector storage
   - Tracks ingestion statistics

4. **GitLab Service Layer** (`app/services/gitlab_service.py`)
   - Business logic for code operations
   - Search with filtering (language, path, chunk type)
   - Repository statistics
   - Duplicate detection

### Key Features
- **Hierarchical Chunking**: Repository → File → Class → Function
- **Rich Navigation**: Line numbers, signatures, docstrings
- **Multi-language**: Python, JavaScript, TypeScript, PHP
- **Metadata Filtering**: Search by language, file type, path
- **Rate Limiting**: Respects GitLab API limits
- **Error Handling**: Graceful failure for individual files

## API Endpoints

### GitLab Code Management (`/code`)
- `POST /code/ingest?ref=main` - Ingest repository
- `POST /code/search` - Search code with filters
- `GET /code/stats` - Get repository statistics
- `GET /code/files` - List ingested files
- `DELETE /code/clear?confirm=true` - Clear all code
- `GET /code/health` - Check GitLab connectivity

### Core RAG Endpoints
- `POST /chat` - Chat with RAG system
- `POST /ingest` - Process documents from data directory
- `GET /ingest/documents` - List processed documents
- `GET /ingest/stats` - Get ingestion statistics

### System Endpoints
- `GET /` - API information
- `GET /health` - Health check
- `GET /info` - Detailed API information
- `GET /docs` - Swagger UI documentation
- `GET /redoc` - ReDoc documentation

## Environment Configuration

### Core Configuration (Required)
```bash
# Voyage AI API Configuration
VOYAGE_API_KEY=your_voyage_api_key_here

# Google Gemini API Configuration
GOOGLE_API_KEY=your_google_api_key_here

# Qdrant Configuration (Vector Database)
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_API_KEY=your_qdrant_api_key_here  # Optional for local setup

# PostgreSQL Configuration (Database)
DATABASE_URL=postgresql://postgres:password@localhost:5432/rag_db
# Or individual components:
DB_HOST=localhost
DB_PORT=5432
DB_NAME=rag_db
DB_USER=postgres
DB_PASSWORD=password
```

### GitLab Configuration (Optional)
```bash
# GitLab Configuration
GITLAB_URL=https://gitlab.com  # or your self-hosted GitLab
GITLAB_TOKEN=your_gitlab_personal_access_token_here
GITLAB_PROJECT_ID=your_project_id_here

# Code Chunking Configuration
CODE_CHUNKING_MIN_TOKENS=100    # Minimum tokens per chunk
CODE_CHUNKING_MAX_TOKENS=2000   # Maximum tokens per chunk
```

### Semantic Chunking Configuration
```bash
# These control how documents are split into chunks
SEMANTIC_BREAKPOINT_PERCENTILE_THRESHOLD=90
SEMANTIC_BUFFER_SIZE=1
SEMANTIC_MAX_TOKENS_PER_CHUNK=800
SEMANTIC_TOKEN_OVERLAP=50
```

## Key Dependencies

### RAG Components
- **llama-index**: Core RAG framework
- **llama-index-embeddings-voyageai**: Voyage AI 3.5 embeddings
- **llama-index-readers-file**: Multi-format document readers
- **qdrant-client**: Qdrant vector database client
- **voyageai**: Voyage AI client

### Database Components (NEW)
- **sqlalchemy**: PostgreSQL ORM and database operations
- **alembic**: Database migration management
- **psycopg2-binary**: PostgreSQL database driver
- **asyncpg**: Async PostgreSQL support for FastAPI

### GitLab Integration (NEW)
- **python-gitlab**: GitLab API client
- **tree-sitter**: Generic AST parsing library
- **tree-sitter-python**: Python AST grammar
- **tree-sitter-javascript**: JavaScript AST grammar
- **tree-sitter-typescript**: TypeScript AST grammar
- **tree-sitter-php**: PHP AST grammar

### Chatbot Components
- **langchain**: Modern LLM framework
- **langchain-google-genai**: Google Gemini integration
- **google-generativeai**: Official Gemini SDK

### Core Infrastructure
- **fastapi**: Web API framework
- **python-dotenv**: Environment variable management
- **openpyxl**: Excel file support

## Technology Choices

- **uv**: Modern Python package management with fast dependency resolution
- **FastAPI**: High-performance async web API development with auto-documentation
- **Docker + Docker Compose**: Containerized Qdrant for easy deployment
- **LlamaIndex**: Production-ready RAG framework for document processing and retrieval
- **LangChain + Gemini 2.5 Flash-Lite**: State-of-the-art conversational AI with streaming support
- **Voyage AI 3.5**: Advanced embeddings optimized for multilingual semantic search
- **Qdrant**: High-performance vector database with built-in similarity search
- **Tree-sitter**: Fast and accurate AST parsing for code analysis
- **GitLab API**: Direct integration with GitLab repositories
- **Separation of Concerns**: Clean architecture separating RAG processing from chatbot logic

## Quick Start Guide

1. **Install dependencies**:
   ```bash
   uv sync
   ```

2. **Configure API keys and database settings**:
   ```bash
   # Edit .env file with your API keys
   VOYAGE_API_KEY=your_voyage_api_key_here
   GOOGLE_API_KEY=your_google_api_key_here  # Required for chat functionality

   # Database configuration
   DATABASE_URL=postgresql://postgres:password@localhost:5432/rag_db
   # Or use individual DB_* variables
   ```

3. **Start all services (Qdrant + PostgreSQL + pgAdmin)**:
   ```bash
   docker-compose up -d
   ```

4. **Run database migrations** (first time setup):
   ```bash
   # Apply database migrations
   uv run alembic upgrade head
   ```

5. **Add documents to data/**:
   ```bash
   # Place files in data/ directory
   # Supports: .xlsx, .pdf, .docx, .txt, .md, .csv, and image files
   ```

6. **Start the server**:
   ```bash
   uv run python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

7. **Access the API**:
   - API Interface: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health
   - Welcome: http://localhost:8000/
   - API Info: http://localhost:8000/info

8. **Access pgAdmin** (database management):
   - URL: http://localhost:5050
   - Default credentials: admin@admin.com / admin

## Optional: GitLab Integration

To use the GitLab code ingestion feature:

7. **Configure GitLab credentials**:
   ```bash
   # Edit .env file
   GITLAB_URL=https://gitlab.com
   GITLAB_TOKEN=your_gitlab_personal_access_token
   GITLAB_PROJECT_ID=12345  # Your GitLab project ID
   ```

8. **Verify GitLab connectivity** (before ingestion):
   ```bash
   curl http://localhost:8000/code/health
   ```

9. **Ingest GitLab repository**:
   ```bash
   curl -X POST "http://localhost:8000/code/ingest?ref=main"
   ```

10. **Search code**:
    ```bash
    curl -X POST http://localhost:8000/code/search \
      -H "Content-Type: application/json" \
      -d '{"query": "authentication function", "language": "python", "top_k": 5}'
    ```

## API Usage Examples

### Chat Endpoints

```bash
# Chat with documents (regular response)
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "日本語で質問してください", "top_k": 5, "stream": false}'

# Chat with streaming response
curl -X POST "http://localhost:8000/chat?stream=true" \
  -H "Content-Type: application/json" \
  -d '{"query": "Tell me about the documents", "top_k": 5}'

# Simple chat with documents (stateless)
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "Can you explain that in more detail?", "top_k": 5}'
```

### Document Management Endpoints

```bash
# Ingest documents from data folder
curl -X POST "http://localhost:8000/ingest" \
  -H "Content-Type: application/json" \
  -d '{"recursive": true}'

# List processed documents
curl -X GET "http://localhost:8000/ingest/documents"

# Get ingestion statistics
curl -X GET "http://localhost:8000/ingest/stats"
```

### System Endpoints

```bash
# Health check
curl -X GET "http://localhost:8000/health"

# API information
curl -X GET "http://localhost:8000/info"

# Root endpoint
curl -X GET "http://localhost:8000/"
```

### GitLab Code Endpoints

```bash
# Check GitLab connectivity
curl http://localhost:8000/code/health

# Ingest entire repository from main branch
curl -X POST "http://localhost:8000/code/ingest?ref=main"

# Ingest from specific branch or tag
curl -X POST "http://localhost:8000/code/ingest?ref=develop"
curl -X POST "http://localhost:8000/code/ingest?ref=v1.0.0"

# Search code (general query)
curl -X POST http://localhost:8000/code/search \
  -H "Content-Type: application/json" \
  -d '{"query": "authentication function", "top_k": 10}'

# Search with language filter
curl -X POST http://localhost:8000/code/search \
  -H "Content-Type: application/json" \
  -d '{"query": "API endpoint", "language": "python", "top_k": 5}'

# Search with file path filter
curl -X POST http://localhost:8000/code/search \
  -H "Content-Type: application/json" \
  -d '{"query": "user management", "file_path": "src/auth/*.py", "top_k": 10}'

# Search specific chunk types
curl -X POST http://localhost:8000/code/search \
  -H "Content-Type: application/json" \
  -d '{"query": "handle database connection", "chunk_type": "function", "top_k": 5}'

# Get repository statistics
curl http://localhost:8000/code/stats

# List ingested files
curl http://localhost:8000/code/files

# List files filtered by language
curl "http://localhost:8000/code/files?language=python"

# Paginated file listing
curl "http://localhost:8000/code/files?page=1&limit=50"

# List files in specific directory
curl "http://localhost:8000/code/files?path=src/components/"

# Clear all code documents (confirmation required)
curl -X DELETE "http://localhost:8000/code/clear?confirm=true"
```

## Development and Testing

The application has full RAG + Chatbot functionality:

### Testing the API

```bash
# Test basic system endpoints
curl http://localhost:8000/
curl http://localhost:8000/health
curl http://localhost:8000/info

# Test chat functionality
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "Hello, can you help me?", "stream": false}'

# Test document ingestion
curl -X POST "http://localhost:8000/ingest" \
  -H "Content-Type: application/json" \
  -d '{"recursive": true}'
```

### Testing Individual Components

```bash
# Test RAG components (if needed for debugging)
# Note: These are typically called through the service layer
uv run python -c "from app.rag.embeddings import get_embedding_service; print('Embeddings OK')"
uv run python -c "from app.rag.vector_store import get_vector_store_service; print('Vector store OK')"
uv run python -c "from app.rag.ingestion import get_ingestion_service; print('Ingestion OK')"

# Test chatbot components
uv run python -c "from app.services.chatbot_service import get_chatbot_service; print('Chatbot service OK')"

# Test database connection
uv run python -c "from app.models.database import get_db; print('Database OK')"

# Run the test suite
uv run pytest                    # Run all tests
uv run pytest tests/unit/        # Run unit tests only
uv run pytest tests/integration/ # Run integration tests only
uv run pytest -v                 # Run with verbose output
```

### API Documentation

Visit http://localhost:8000/docs for interactive API documentation with:
- Automatic request/response examples
- Testable endpoints directly in browser
- Comprehensive parameter descriptions
- Response schema documentation

## Known Issues and Areas for Improvement

### Current Issues
1. **Semantic Splitter**: Currently using basic `RecursiveCharacterTextSplitter` instead of true semantic chunking with Voyage AI embeddings
2. **Collection Naming**: GitLab service collection naming could be more robust for edge cases
3. **Statistics Placeholders**: Some GitLab service methods return placeholder data instead of actual statistics

### Areas for Enhancement
1. **Security**: Add authentication, authorization, API rate limiting
2. **Monitoring**: Add metrics, health checks, performance monitoring
3. **Async Processing**: Implement background job processing for large ingestions
4. **Session Management**: Add conversation history and context persistence
5. **Real-time Updates**: Add webhook support for GitLab repository changes
6. **Caching**: Implement response caching for better performance
7. **Advanced Filtering**: Enhanced metadata filtering in search results

### Technology Debt
- Semantic splitter needs to be re-enabled with proper Voyage AI integration
- Some GitLab service methods need completion with actual implementation
- Collection management could be more robust for edge cases

## Architecture Strengths

1. **Modular Design**: Clean separation of concerns with service layers
2. **Extensibility**: Easy to add new languages, file types, and integrations
3. **Error Resilience**: Comprehensive error handling throughout the pipeline
4. **Performance**: Async operations and efficient vector storage
5. **Configuration**: Flexible, environment-driven configuration with validation
6. **Testing**: Comprehensive test suite with 60+ tests across all components
7. **Documentation**: Extensive API documentation and examples
8. **Database Integration**: Robust PostgreSQL integration with migration support