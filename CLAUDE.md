# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a fully implemented **agentic-rag** system with conversational AI capabilities - a retrieval-augmented generation system with agentic capabilities for in-house chatbot applications. The system features complete RAG functionality with Japanese semantic chunking, Voyage AI embeddings, **ChromaDB vector storage**, and Google Gemini 2.5 Flash-Lite integration for intelligent conversational responses.

## New: GitLab Code Integration

As of version 1.2.0, the system includes **GitLab repository integration** with AST-based code chunking for Python, JavaScript, TypeScript, and PHP. This allows you to:
- Ingest entire GitLab repositories into the vector store
- Extract structured code chunks at file, class, and function levels
- Search code semantically with rich metadata
- Query code alongside documents for comprehensive answers

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
# Start ChromaDB service (required for vector storage)
docker-compose up -d                                 # Start ChromaDB in background
docker-compose down                                  # Stop ChromaDB
docker-compose logs -f                               # View ChromaDB logs

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
│   ├── connectors/         # External service connectors
│   │   ├── __init__.py
│   │   └── gitlab_connector.py    # GitLab API integration
│   │
│   ├── config/             # Configuration modules
│   │   ├── __init__.py
│   │   ├── logging_config.py
│   │   └── chroma_config.py       # ChromaDB configuration
│   │
│   ├── dto/                # Data transfer objects (Pydantic models)
│   │   ├── __init__.py
│   │   ├── ingestion.py           # Document ingestion models
│   │   ├── chat.py                # Chat API models
│   │   └── code_ingestion.py      # GitLab code models (NEW)
│   │
│   ├── rag/                # RAG system modules (document processing)
│   │   ├── __init__.py
│   │   ├── embeddings.py          # Voyage AI embedding generation
│   │   ├── ingestion.py           # Document ingestion pipeline
│   │   ├── semantic_splitter.py   # Japanese semantic chunking
│   │   ├── vector_store.py        # ChromaDB vector storage
│   │   ├── ast_splitter.py        # AST-based code chunking (NEW)
│   │   └── code_ingestion.py      # GitLab code orchestration (NEW)
│   │
│   ├── routers/            # API route definitions
│   │   ├── __init__.py
│   │   ├── ingestion.py           # Document ingestion endpoints
│   │   ├── chat.py                # Chat endpoints
│   │   └── code_ingestion.py      # GitLab code endpoints (NEW)
│   │
│   ├── services/           # Business logic services
│   │   ├── __init__.py
│   │   ├── rag_service.py         # RAG operations service
│   │   ├── chatbot_service.py     # Chat and LLM integration
│   │   └── gitlab_service.py      # GitLab service layer (NEW)
│   │
│   └── utils/              # Utility modules
│       ├── __init__.py
│       └── session_manager.py     # Conversation session management
│
├── data/                   # Document storage directory
├── chroma_data/           # ChromaDB data volume (created by Docker)
├── .env                    # Environment variables (API keys)
├── .env.example           # Environment variables template
├── .gitignore             # Git ignore rules
├── docker-compose.yml     # ChromaDB Docker configuration
├── CLAUDE.md               # Project documentation
├── pyproject.toml          # Project configuration and dependencies
├── README.md               # Project readme
├── uv.lock                 # Locked dependency versions
└── .python-version         # Python version specification
```

### Core Components

**Document Processing** (`app/rag/`):
- `ingestion.py` - Multi-format document ingestion
- `semantic_splitter.py` - Japanese-aware semantic text chunking
- `embeddings.py` - Voyage AI 3.5 embedding generation
- `vector_store.py` - ChromaDB storage and retrieval
- `ast_splitter.py` - AST-based code parsing for Python/JS/TS/PHP (NEW)
- `code_ingestion.py` - GitLab code orchestration (NEW)

**External Integrations** (`app/connectors/`):
- `gitlab_connector.py` - GitLab API client for repository access (NEW)

**Service Layer** (`app/services/`):
- `rag_service.py` - Core RAG operations
- `chatbot_service.py` - LLM integration and chat management
- `gitlab_service.py` - GitLab business logic (NEW)

**API Layer** (`app/routers/`):
- `ingestion.py` - Document management endpoints
- `chat.py` - Chat and conversation endpoints
- `code_ingestion.py` - GitLab code management endpoints (NEW)

**Data Models** (`app/dto/`):
- `ingestion.py` - Document ingestion API models
- `chat.py` - Chat API models
- `code_ingestion.py` - GitLab API request/response models (NEW)
│   ├── config/             # Configuration modules
│   │   ├── __init__.py
│   │   ├── logging_config.py
│   │   └── chroma_config.py # ChromaDB configuration
│   ├── dto/                # Data transfer objects
│   │   ├── __init__.py
│   │   ├── ingestion.py    # Ingestion API models
│   │   └── chat.py         # Chat API models
│   ├── rag/                # RAG system modules (document processing only)
│   │   ├── __init__.py
│   │   ├── embeddings.py   # Voyage AI embedding generation
│   │   ├── ingestion.py    # Document ingestion and processing
│   │   ├── semantic_splitter.py  # Japanese semantic chunking
│   │   └── vector_store.py # ChromaDB vector storage and retrieval
│   ├── routers/            # API route definitions
│   │   ├── __init__.py
│   │   ├── ingestion.py    # Document ingestion endpoints
│   │   └── chat.py         # Chat and conversation endpoints
│   ├── services/           # Business logic services
│   │   ├── __init__.py
│   │   ├── rag_service.py  # RAG operations service
│   │   └── chatbot_service.py  # Chat and LLM integration service
│   └── utils/              # Utility modules
│       ├── __init__.py
│       └── session_manager.py  # Conversation session management
├── data/                   # Document storage directory
├── chroma_data/           # ChromaDB data volume (created by Docker)
├── .env                    # Environment variables (API keys)
├── .env.example           # Environment variables template
├── .gitignore             # Git ignore rules
├── docker-compose.yml     # ChromaDB Docker configuration
├── CLAUDE.md               # Project documentation
├── pyproject.toml          # Project configuration and dependencies
├── README.md               # Project readme
├── uv.lock                 # Locked dependency versions
└── .python-version         # Python version specification
```

## Project Architecture

This project implements a complete **agentic RAG system with conversational AI** featuring the following components:

### Core RAG Components (✅ Fully Implemented)
- **Document Processing** (`app/rag/ingestion.py`): Multi-format file ingestion with Japanese semantic chunking
- **Embedding Generation** (`app/rag/embeddings.py`): Voyage AI 3.5 embedding configuration
- **Vector Database** (`app/rag/vector_store.py`): FAISS index with multiple index types (flat, IVF, HNSW)
- **Semantic Splitter** (`app/rag/semantic_splitter.py`): Japanese-aware text chunking

### Chatbot System (✅ Fully Implemented)
- **Chatbot Service** (`app/services/chatbot_service.py`): LLM integration with Google Gemini 2.5 Flash-Lite
- **LangChain Integration**: Modern LLM framework for prompt engineering and response generation
- **Streaming Support**: Real-time response streaming for enhanced user experience
- **Stateless Processing**: Each query processed independently without session memory

### API Layer (✅ Fully Implemented)
- **FastAPI Application** (`app/main.py`): Complete FastAPI setup with comprehensive endpoints
  - `GET /` - Welcome message with API information
  - `GET /health` - Health check endpoint
  - `GET /info` - Detailed API information
  - **Chat Endpoints** (`/chat`):
    - `POST /chat` - Main chat endpoint with streaming support and stateless processing
  - **Ingestion Endpoints** (`/ingest`):
    - `POST /ingest` - Process documents from data directory
    - `GET /ingest/documents` - List processed documents
    - `GET /ingest/stats` - Get ingestion statistics

### Data Processing (✅ Fully Implemented)
- **Ingestion Pipelines**: Automated processing of Excel, PDF, Word, text files
- **Japanese Optimization**: Semantic chunking with Japanese sentence separators (。！？)
- **Knowledge Base Management**: CRUD operations with metadata tracking
- **Vector Operations**: Efficient similarity search with configurable parameters

## Development Notes

- **Current Status**: Fully implemented RAG + Chatbot system with conversational AI capabilities
- **API Documentation**: Auto-generated at `/docs` endpoint when server is running
- **Project Status**: Production-ready with comprehensive features
- **Environment Setup**: Requires both `VOYAGE_API_KEY` and `GOOGLE_API_KEY` in `.env` file
- **Data Source**: Place documents in `/data` folder - supports Excel, PDF, Word, text files
- **Vector Storage**: ChromaDB with Docker for managed vector storage and retrieval
- **Stateless Processing**: Each query processed independently without session memory
- **Docker Integration**: ChromaDB runs in container (port 8001) with persistent volume

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

# ChromaDB Configuration
CHROMA_HOST=localhost
CHROMA_PORT=8001
CHROMA_COLLECTION_NAME=rag_documents
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
- **chromadb**: ChromaDB vector database
- **langchain-chroma**: LangChain ChromaDB integration
- **voyageai**: Voyage AI client

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
- **Docker + Docker Compose**: Containerized ChromaDB for easy deployment
- **LlamaIndex**: Production-ready RAG framework for document processing and retrieval
- **LangChain + Gemini 2.5 Flash-Lite**: State-of-the-art conversational AI with streaming support
- **Voyage AI 3.5**: Advanced embeddings optimized for multilingual semantic search
- **ChromaDB**: Modern vector database with built-in similarity search
- **Tree-sitter**: Fast and accurate AST parsing for code analysis
- **GitLab API**: Direct integration with GitLab repositories
- **Separation of Concerns**: Clean architecture separating RAG processing from chatbot logic

## Quick Start Guide

1. **Install dependencies**:
   ```bash
   uv sync
   ```

2. **Configure API keys and Chroma settings**:
   ```bash
   # Edit .env file
   VOYAGE_API_KEY=your_voyage_api_key_here
   GOOGLE_API_KEY=your_google_api_key_here  # Required for chat functionality

   # Chroma configuration (optional - defaults to localhost:8001)
   CHROMA_HOST=localhost
   CHROMA_PORT=8001
   CHROMA_AUTH_TOKEN=rag_token_123
   CHROMA_COLLECTION_NAME=rag_documents
   ```

3. **Start ChromaDB service**:
   ```bash
   docker-compose up -d
   ```

4. **Add documents to data/**:
   ```bash
   # Place files in data/ directory
   # Supports: .xlsx, .pdf, .docx, .txt, .md, .csv, and image files
   ```

5. **Start the server**:
   ```bash
   uv run python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

6. **Access the API**:
   - API Interface: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health
   - Welcome: http://localhost:8000/
   - API Info: http://localhost:8000/info

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
```

### API Documentation

Visit http://localhost:8000/docs for interactive API documentation with:
- Automatic request/response examples
- Testable endpoints directly in browser
- Comprehensive parameter descriptions
- Response schema documentation