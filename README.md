# Agentic RAG Sample

A powerful Retrieval-Augmented Generation (RAG) system with agentic capabilities, built following Clean Architecture principles.

## 🌟 Features

- 🇯🇵 **Japanese Document Processing** - Semantic chunking optimized for Japanese text
- 🚀 **Google Gemini Embeddings** - State-of-the-art text embeddings (gemini-embedding-001)
- 🗄️ **Qdrant Vector Storage** - Docker-containerized vector database
- 📄 **Multi-format Support** - PDF, Word, Excel, Markdown, images, and more
- 💬 **Conversational AI** - Chat with documents using Google Gemini
- 🎨 **Streamlit Chatbot UI** - Beautiful, modern web interface for chatting with your documents
- 🔄 **Streaming Responses** - Real-time response streaming
- 🦊 **GitLab Integration** - Ingest and search code from repositories
- 🌳 **AST-based Code Chunking** - Semantic analysis for Python, JS, TS, PHP
- 🎯 **Customizable Chatbots** - Configure multiple chatbots with different personalities


## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Docker and Docker Compose
- uv package manager (`pip install uv`)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd agentic-rag-sample

# Copy environment file
cp .env.example .env

# Edit .env and add your API keys
# - POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
# - GOOGLE_API_KEY

# Install dependencies
uv sync

# Start Docker services (PostgreSQL, Qdrant, pgAdmin)
docker-compose up -d

# Run database migrations
uv run alembic upgrade head

# Start the development server
uv run python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Visit http://localhost:8000/docs for the interactive API documentation.

## 📚 Documentation

- **[Architecture Guide](docs/ARCHITECTURE.md)** - Detailed architecture documentation
- **[Alembic Guide](docs/alembic-guide.md)** - Database migration guide
- **[Streamlit UI Guide](STREAMLIT_README.md)** - Chatbot web interface documentation
- **[API Documentation](http://localhost:8000/docs)** - Interactive API docs (when server is running)

## 🛠️ Available Workflows

This project includes pre-configured workflows for common tasks. Use slash commands to access them:

| Workflow | Command | Description |
|----------|---------|-------------|
| Start Dev Server | `/start-dev-server` | Start the FastAPI development server |
| Setup Project | `/setup-project` | Setup project from scratch |
| Run Tests | `/run-tests` | Run the test suite |
| Run Migrations | `/run-database-migration` | Create and run database migrations |
| Manage Docker | `/manage-docker-services` | Manage Docker services |
| Ingest Documents | `/ingest-documents` | Ingest documents into the system |
| Chat with Documents | `/chat-with-documents` | Query ingested documents |
| Manage Chatbots | `/manage-chatbots` | CRUD operations for chatbots |
| Add New Feature | `/add-new-feature` | Add a feature following clean architecture |

## 🏗️ Architecture

This project follows **Clean Architecture** with clear separation of concerns:

```
app/
├── api/              # HTTP endpoints and request/response models
├── application/      # Use cases and application services
├── domain/          # Business entities and repository interfaces
├── infrastructure/  # External integrations (DB, APIs, embeddings)
└── connectors/      # External system connectors (GitLab, etc.)
```

### Key Technologies

- **FastAPI** - Web framework
- **SQLAlchemy 2.0** - ORM for PostgreSQL
- **Alembic** - Database migrations
- **Qdrant** - Vector database
- **LangChain** - LLM application framework
- **Google Gemini** - Large language models and embeddings

## 🔧 Common Tasks

### Start Development Server

```bash
uv run python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Run Tests

```bash
# All tests
uv run pytest

# With coverage
uv run pytest --cov=app --cov-report=html
```

### Database Migrations

```bash
# Create migration
uv run alembic revision --autogenerate -m "description"

# Apply migration
uv run alembic upgrade head

# Rollback
uv run alembic downgrade -1
```

### Manage Docker Services

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 🎯 API Endpoints

### Chat
- `POST /chat` - Q&A with document retrieval
- `POST /chat/stream` - Streaming chat responses

### Chatbots
- `GET /chatbots` - List all chatbots
- `POST /chatbots` - Create a chatbot
- `GET /chatbots/{id}` - Get chatbot by ID
- `PUT /chatbots/{id}` - Update chatbot
- `DELETE /chatbots/{id}` - Delete chatbot

### Files
- `POST /files/upload` - Upload and ingest documents
- `POST /files/ingest-gitlab-code` - Ingest code from GitLab
- `GET /files/collections` - List collections
- `GET /files/collections/{name}/stats` - Get collection statistics

### System
- `GET /` - API information
- `GET /health` - Health check
- `GET /info` - Detailed API info

## 📝 Example Usage

### Upload a Document

```bash
curl -X POST "http://localhost:8000/files/upload" \
  -F "file=@document.pdf" \
  -F "collection_name=my_docs"
```

### Chat with Documents

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is this document about?",
    "collection_name": "my_docs"
  }'
```

### Create a Chatbot

```bash
curl -X POST "http://localhost:8000/chatbots" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Support Bot",
    "description": "Customer support assistant",
    "system_prompt": "You are a helpful customer support agent.",
    "model": "gemini-2.5-flash-preview-09-2025",
    "temperature": 0.7,
    "qdrant_collection": "my_docs"
  }'
```

## 🐳 Docker Services

- **PostgreSQL**: `localhost:5432` - Relational database
- **pgAdmin**: `localhost:5050` - Database admin UI
- **Qdrant**: `localhost:6333` - Vector database
- **Qdrant Dashboard**: `localhost:6333/dashboard` - Vector DB UI

## 🧪 Testing

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_chatbot_api.py

# Run with coverage
uv run pytest --cov=app --cov-report=html

# View coverage report
open htmlcov/index.html
```

## 📊 Project Structure

```
agentic-rag-sample/
├── .agent/
│   └── workflows/          # Pre-configured workflows
├── alembic/               # Database migrations
├── app/
│   ├── api/              # API routes and endpoints
│   ├── application/      # Business use cases
│   ├── connectors/       # External system connectors
│   ├── domain/          # Domain entities and ports
│   ├── infrastructure/  # Technical implementations
│   ├── config.py        # Application configuration
│   └── main.py          # FastAPI application
├── data/                # Local data storage
├── docs/                # Documentation
├── logs/                # Application logs
├── tests/               # Test suite
├── .env                 # Environment variables (create from .env.example)
├── docker-compose.yml   # Docker services configuration
└── pyproject.toml       # Project dependencies
```

## 🔐 Environment Variables

Required environment variables (see `.env.example`):

```bash
# Database
POSTGRES_DB=agentic_rag
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password

# Vector Database
QDRANT_HOST=localhost
QDRANT_PORT=6333

# AI Services
GOOGLE_API_KEY=your_gemini_key

# GitLab (Optional)
GITLAB_TOKEN=your_token
GITLAB_PROJECT_ID=your_project_id
```

## 🤝 Contributing

1. Follow Clean Architecture principles
2. Write tests for new features
3. Use type hints
4. Document your code
5. Run tests before committing
6. Follow the existing code style

## 📄 License

[Your License Here]

## 🙋 Support

For questions or issues, please open an issue on GitHub.

---

Made with ❤️ using FastAPI, LangChain, and Clean Architecture
