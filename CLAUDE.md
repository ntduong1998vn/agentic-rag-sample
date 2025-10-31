# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a fully implemented **agentic-rag** system - a retrieval-augmented generation system with agentic capabilities for in-house chatbot applications. The system features complete RAG functionality with Japanese semantic chunking, Voyage AI embeddings, and FAISS vector storage.

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
uv run python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000  # Start the RAG API server with auto-reload
uv run python -m uvicorn app.main:app --host 0.0.0.0 --port 8080           # Custom port without reload
# Note: The original `uv run python main.py` commands are not applicable due to project restructure
```

### Dependency Management
```bash
uv add <package>          # Add new dependencies to pyproject.toml
uv pip install <package>  # Install packages in current environment
uv lock                   # Update lock file with latest versions
```

## Current Project Structure

```
agentic-rag/
├── app/                     # FastAPI application modules
│   ├── __init__.py         # Package initialization
│   ├── main.py             # FastAPI application entry point
│   ├── dto/                # Data transfer objects
│   │   └── __init__.py
│   ├── rag/                # RAG system modules (to be implemented)
│   │   └── __init__.py
│   ├── routers/            # API route definitions
│   │   └── __init__.py
│   └── services/           # Business logic services
│       └── __init__.py
├── data/                   # Document storage directory
├── vector_store/           # FAISS index storage (created automatically)
├── .env                    # Environment variables (API keys)
├── .gitignore              # Git ignore rules
├── CLAUDE.md               # Project documentation
├── pyproject.toml          # Project configuration and dependencies
├── README.md               # Project readme
├── uv.lock                 # Locked dependency versions
└── .python-version         # Python version specification
```

## Project Architecture

This project is designed to implement a complete **agentic RAG system** with the following planned components:

### Core RAG Components (To Be Implemented)
- **Document Processing** (`app/rag/ingestion.py`): Multi-format file ingestion with Japanese semantic chunking
- **Embedding Generation** (`app/rag/embeddings.py`): Voyage AI 3.5 embedding configuration
- **Vector Database** (`app/rag/vector_store.py`): FAISS index with multiple index types (flat, IVF, HNSW)
- **Retrieval Mechanisms** (`app/rag/query_engine.py`): Semantic search with configurable similarity thresholds

### Agent Framework (To Be Implemented)
- **LLM Integration**: OpenAI integration with fallback to basic retrieval
- **Query Engine**: Configurable RAG pipeline with context generation
- **Memory Management**: Persistent vector storage with metadata

### API Layer (Basic Implementation)
- **FastAPI Application** (`app/main.py`): Basic FastAPI setup with health endpoints
  - `GET /` - Welcome message
  - `GET /health` - Health check endpoint
  - **Planned endpoints**: `/query`, `/similarity`, `/ingest`, `/upload`, `/status`, `/rebuild`

### Data Processing (To Be Implemented)
- **Ingestion Pipelines**: Automated processing of Excel, PDF, Word, text files
- **Japanese Optimization**: Semantic chunking with Japanese sentence separators (。！？)
- **Knowledge Base Management**: CRUD operations with metadata tracking
- **Vector Operations**: Efficient similarity search with configurable parameters

## Development Notes

- **Current Status**: Basic FastAPI application with health endpoints. RAG functionality needs to be implemented.
- **API Documentation**: Auto-generated at `/docs` endpoint when server is running
- **Project Status**: Infrastructure is ready for RAG system implementation
- **Environment Setup**: Will require `VOYAGE_API_KEY` in `.env` file for RAG functionality
- **Optional**: `OPENAI_API_KEY` for enhanced LLM responses (fallback to basic retrieval)
- **Data Source**: Place documents in `/data` folder - will support Excel, PDF, Word, text files
- **Vector Storage**: Will create automatic FAISS index in `/vector_store` directory

## Key Dependencies

- **llama-index**: Core RAG framework
- **llama-index-embeddings-voyageai**: Voyage AI 3.5 embeddings
- **llama-index-vector-stores-faiss**: FAISS vector storage
- **faiss-cpu**: Vector similarity search
- **fastapi**: Web API framework
- **python-dotenv**: Environment variable management
- **openpyxl**: Excel file support

## Technology Choices

- **uv**: Modern Python package management with fast dependency resolution
- **FastAPI**: High-performance async web API development with auto-documentation
- **llama-index**: Production-ready RAG framework with extensive integrations
- **Voyage AI 3.5**: State-of-the-art embeddings optimized for semantic search
- **FAISS**: Efficient vector similarity search from Facebook AI
- **Python 3.12**: Latest Python version with modern language features

## Quick Start Guide

1. **Install dependencies**:
   ```bash
   uv sync
   ```

2. **Configure API keys**:
   ```bash
   # Edit .env file
   VOYAGE_API_KEY=your_voyage_api_key_here
   OPENAI_API_KEY=your_openai_api_key_here  # Optional
   ```

3. **Add documents**:
   ```bash
   # Place files in data/ directory
   # Supports: .xlsx, .pdf, .docx, .txt, .md, .csv, and image files
   ```

4. **Start the server**:
   ```bash
   uv run python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Access the API**:
   - API Interface: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health
   - Welcome: http://localhost:8000/

## API Usage Examples

```bash
# Query documents with RAG
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "日本語の質問", "top_k": 5}'

# Pure similarity search
curl -X POST "http://localhost:8000/similarity" \
  -H "Content-Type: application/json" \
  -d '{"query": "検索キーワード", "top_k": 3}'

# Ingest documents from data folder
curl -X POST "http://localhost:8000/ingest"

# Upload a document
curl -X POST "http://localhost:8000/upload" \
  -F "file=@document.pdf"
```

## Development and Testing

Currently the application has basic FastAPI functionality:
```bash
# Test the basic API endpoints
curl http://localhost:8000/
curl http://localhost:8000/health

# Future testing (when RAG modules are implemented):
# uv run python app/rag/ingestion.py
# uv run python app/rag/embeddings.py
# uv run python app/rag/vector_store.py
# uv run python app/rag/query_engine.py
```