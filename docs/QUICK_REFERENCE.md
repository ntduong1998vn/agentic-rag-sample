# Quick Reference Guide

## 🚀 Common Commands

### Development Server
```bash
# Start server
uv run python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Access API docs
open http://localhost:8000/docs
```

### Docker Services
```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f

# Check service status
docker-compose ps
```

### Database Migrations
```bash
# Create migration
uv run alembic revision --autogenerate -m "your message"

# Apply migrations
uv run alembic upgrade head

# Rollback last migration
uv run alembic downgrade -1

# Check current version
uv run alembic current
```

### Testing
```bash
# Run all tests
uv run pytest

# With coverage
uv run pytest --cov=app --cov-report=html

# Specific test file
uv run pytest tests/test_chatbot_api.py
```

## 📚 Workflows

Use these slash commands to access pre-configured workflows:

- `/start-dev-server` - Start development server
- `/setup-project` - Setup from scratch
- `/run-tests` - Run tests
- `/run-database-migration` - Database migrations
- `/manage-docker-services` - Docker management
- `/ingest-documents` - Document ingestion
- `/chat-with-documents` - Chat with docs
- `/manage-chatbots` - Chatbot CRUD
- `/add-new-feature` - Add new feature

## 🎯 API Quick Reference

### Base URL
```
http://localhost:8000
```

### Chat Endpoints

**POST /chat**
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Your question here",
    "collection_name": "your_collection"
  }'
```

**POST /chat/stream**
```bash
curl -X POST "http://localhost:8000/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Your question here",
    "collection_name": "your_collection"
  }'
```

### Chatbot Endpoints

**List Chatbots**
```bash
curl -X GET "http://localhost:8000/chatbots"
```

**Create Chatbot**
```bash
curl -X POST "http://localhost:8000/chatbots" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Bot",
    "description": "Bot description",
    "system_prompt": "You are a helpful assistant.",
    "model": "gemini-2.0-flash-exp",
    "temperature": 0.7,
    "qdrant_collection": "collection_name"
  }'
```

**Get Chatbot**
```bash
curl -X GET "http://localhost:8000/chatbots/1"
```

**Update Chatbot**
```bash
curl -X PUT "http://localhost:8000/chatbots/1" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Name",
    "temperature": 0.8
  }'
```

**Delete Chatbot**
```bash
curl -X DELETE "http://localhost:8000/chatbots/1"
```

### File Endpoints

**Upload Document**
```bash
curl -X POST "http://localhost:8000/files/upload" \
  -F "file=@/path/to/document.pdf" \
  -F "collection_name=my_collection"
```

**Ingest GitLab Code**
```bash
curl -X POST "http://localhost:8000/files/ingest-gitlab-code" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "12345",
    "collection_name": "code_collection",
    "branch": "main",
    "file_extensions": [".py", ".js"]
  }'
```

**List Collections**
```bash
curl -X GET "http://localhost:8000/files/collections"
```

**Get Collection Stats**
```bash
curl -X GET "http://localhost:8000/files/collections/my_collection/stats"
```

## 🏗️ Project Structure

```
app/
├── api/                    # HTTP endpoints
│   ├── routes_chat.py
│   ├── routes_chatbot.py
│   └── routes_files.py
├── application/            # Use cases
│   ├── chatbot/
│   └── rag/
├── domain/                 # Business entities
│   ├── chat/
│   ├── chatbot/
│   └── files/
├── infrastructure/         # Technical implementations
│   ├── database/
│   ├── embeddings.py
│   └── ast_splitter.py
└── connectors/            # External systems
    └── gitlab/
```

## 🔧 Configuration

### Environment Variables

```bash
# Database
POSTGRES_DB=agentic_rag
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
DATABASE_HOST=localhost
DATABASE_PORT=5432

# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333

# AI Services
VOYAGE_API_KEY=your_voyage_key
GOOGLE_API_KEY=your_gemini_key

# GitLab (Optional)
GITLAB_TOKEN=your_token
GITLAB_PROJECT_ID=your_project_id

# Logging
LOG_LEVEL=INFO
LOG_FILE_PATH=logs/app.log
```

### Model Options

**Gemini Models:**
- `gemini-2.0-flash-exp` - Fast, general-purpose (recommended)
- `gemini-1.5-pro` - More capable, slower
- `gemini-1.5-flash` - Balanced

**Parameters:**
- `temperature`: 0.0-1.0 (lower = more consistent)
- `max_tokens`: 512-4096 (response length)
- `top_k`: 3-10 (documents to retrieve)
- `threshold`: 0.5-0.9 (similarity cutoff)

## 🐳 Docker Services

| Service | Port | URL |
|---------|------|-----|
| PostgreSQL | 5432 | - |
| pgAdmin | 5050 | http://localhost:5050 |
| Qdrant | 6333 | http://localhost:6333 |
| Qdrant Dashboard | 6333 | http://localhost:6333/dashboard |
| API | 8000 | http://localhost:8000 |
| API Docs | 8000 | http://localhost:8000/docs |

## 🎨 Supported File Types

**Documents:**
- PDF (.pdf)
- Word (.docx, .doc)
- Excel (.xlsx, .xls)
- Text (.txt, .md)
- HTML (.html, .htm)
- EPUB (.epub)

**Code:**
- Python (.py)
- JavaScript (.js)
- TypeScript (.ts, .tsx)
- PHP (.php)

**Images:**
- JPEG, PNG, GIF, BMP, TIFF

## 💡 Tips & Tricks

### Database
- Use pgAdmin at http://localhost:5050 to inspect database
- Always backup before running migrations
- Use `alembic current` to check migration status

### Testing
- Run tests before committing
- Use `pytest -k "test_name"` to run specific tests
- Check coverage with `--cov-report=html`

### Development
- Use `/docs` for interactive API testing
- Monitor logs in `logs/` directory
- Use streaming endpoints for better UX
- Configure chatbots for different use cases

### Performance
- Adjust `top_k` based on document size
- Use lower `threshold` for broader results
- Consider batch operations for bulk ingestion
- Monitor Qdrant dashboard for vector stats

## 🐛 Troubleshooting

### Server won't start
```bash
# Check if ports are available
lsof -i :8000

# Restart Docker services
docker-compose restart
```

### Database connection error
```bash
# Check PostgreSQL status
docker-compose logs postgres

# Verify environment variables
cat .env
```

### Migration issues
```bash
# Check current migration
uv run alembic current

# View migration history
uv run alembic history

# Rollback and retry
uv run alembic downgrade -1
uv run alembic upgrade head
```

### Qdrant connection error
```bash
# Check Qdrant status
docker-compose logs qdrant

# Restart Qdrant
docker-compose restart qdrant
```

## 📖 Further Reading

- [Architecture Documentation](ARCHITECTURE.md)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [LangChain Documentation](https://python.langchain.com/)
