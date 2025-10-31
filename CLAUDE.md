# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a fully implemented **agentic-rag** system - a retrieval-augmented generation system with agentic capabilities for in-house chatbot applications. The system features complete RAG functionality with Japanese semantic chunking, Voyage AI embeddings, and FAISS vector storage.

## Development Environment

- **Python**: 3.14.0 (specified in `.python-version`)
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
uv run python main.py      # Start the RAG API server (default: http://localhost:8000)
uv run python main.py --dev # Development mode with auto-reload
uv run python main.py --port 8080 # Custom port
uv run python main.py --data-dir ./my-data # Custom data directory
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
├── src/                     # Core RAG system modules
│   ├── __init__.py         # Package initialization
│   ├── ingestion.py        # Document ingestion and Japanese semantic chunking
│   ├── embeddings.py       # Voyage AI 3.5 embedding configuration
│   ├── vector_store.py     # FAISS vector store management
│   ├── query_engine.py     # RAG query engine with LLM integration
│   └── api.py              # FastAPI endpoints and web interface
├── data/                   # Document storage directory
├── vector_store/           # FAISS index storage (created automatically)
├── main.py                 # FastAPI server entry point
├── .env                    # Environment variables (API keys)
├── pyproject.toml          # Project configuration and dependencies
└── uv.lock                 # Locked dependency versions
```

## Implemented Architecture

This project implements a complete **agentic RAG system** with the following components:

### Core RAG Components
- **Document Processing** (`src/ingestion.py`): Multi-format file ingestion with Japanese semantic chunking
- **Embedding Generation** (`src/embeddings.py`): Voyage AI 3.5 embeddings with API key management
- **Vector Database** (`src/vector_store.py`): FAISS index with multiple index types (flat, IVF, HNSW)
- **Retrieval Mechanisms** (`src/query_engine.py`): Semantic search with configurable similarity thresholds

### Agent Framework
- **LLM Integration**: OpenAI integration with fallback to basic retrieval
- **Query Engine**: Configurable RAG pipeline with context generation
- **Memory Management**: Persistent vector storage with metadata

### API Layer
- **FastAPI Endpoints** (`src/api.py`): Complete RESTful API with documentation
  - `POST /query` - RAG queries with LLM responses
  - `POST /similarity` - Pure similarity search
  - `POST /ingest` - Background document ingestion
  - `POST /upload` - Single document upload
  - `GET /status` - System status and statistics
  - `POST /rebuild` - System rebuild functionality

### Data Processing
- **Ingestion Pipelines**: Automated processing of Excel, PDF, Word, text files
- **Japanese Optimization**: Semantic chunking with Japanese sentence separators (。！？)
- **Knowledge Base Management**: CRUD operations with metadata tracking
- **Vector Operations**: Efficient similarity search with configurable parameters

## Development Notes

- **Current Status**: Fully implemented RAG system with production-ready API
- **API Documentation**: Auto-generated at `/docs` endpoint when server is running
- **Testing**: Individual modules have test functions when run directly
- **Environment Setup**: Requires `VOYAGE_API_KEY` in `.env` file (template provided)
- **Optional**: `OPENAI_API_KEY` for enhanced LLM responses (fallback to basic retrieval)
- **Data Source**: Place documents in `/data` folder - supports Excel, PDF, Word, text files
- **Vector Storage**: Automatic FAISS index creation in `/vector_store` directory

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
- **Python 3.14**: Latest Python version with modern language features

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
   uv run python main.py
   ```

5. **Access the API**:
   - API Interface: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health
   - System Status: http://localhost:8000/status

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

Individual modules can be tested directly:
```bash
# Test document ingestion
uv run python src/ingestion.py

# Test embeddings configuration
uv run python src/embeddings.py

# Test vector store
uv run python src/vector_store.py

# Test query engine
uv run python src/query_engine.py
```