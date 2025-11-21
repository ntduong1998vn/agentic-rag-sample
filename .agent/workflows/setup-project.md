---
description: setup project from scratch
---

# Setup Project From Scratch

This workflow sets up the entire project from a fresh clone.

## Prerequisites

- Python 3.12 or higher
- Docker and Docker Compose installed
- uv package manager installed (`pip install uv`)

## Steps

1. Clone the repository (if not already done):
   ```bash
   git clone <repository-url>
   cd agentic-rag-sample
   ```

2. Copy the environment file and configure it:
   ```bash
   cp .env.example .env
   ```

3. Edit `.env` file and set all required values:
   - POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
   - QDRANT_HOST, QDRANT_PORT
   - VOYAGE_API_KEY
   - GOOGLE_API_KEY
   - GITLAB_TOKEN (optional, for GitLab integration)
   - GITLAB_PROJECT_ID (optional)

// turbo
4. Install Python dependencies using uv:
   ```bash
   uv sync
   ```

// turbo
5. Start Docker services:
   ```bash
   docker-compose up -d
   ```

6. Wait for services to be ready (check with `docker-compose ps`)

// turbo
7. Initialize the database with Alembic migrations:
   ```bash
   uv run alembic upgrade head
   ```

// turbo
8. Verify the setup by starting the server:
   ```bash
   uv run python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

9. Visit http://localhost:8000/docs to confirm the API is running

## Troubleshooting

- If Docker containers fail to start, check if ports 5432, 6333, 6334, 5050 are available
- If database connection fails, verify PostgreSQL is running: `docker-compose logs postgres`
- If Qdrant connection fails, verify Qdrant is running: `docker-compose logs qdrant`
