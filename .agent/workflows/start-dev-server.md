---
description: start development server
---

# Start Development Server

This workflow starts the FastAPI development server with hot-reload enabled.

## Steps

1. Ensure you're in the project root directory `/Users/duongnt/Projects/agentic-rag-sample`

2. Make sure all required environment variables are set in `.env` file:
   - Database credentials (POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD)
   - Qdrant connection settings
   - API keys (VOYAGE_API_KEY, GOOGLE_API_KEY, GITLAB_TOKEN if needed)

3. Ensure Docker services are running (Qdrant and PostgreSQL):
   ```bash
   docker-compose up -d
   ```

// turbo
4. Start the development server:
   ```bash
   uv run python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. Access the application:
   - API Documentation: http://localhost:8000/docs
   - API Info: http://localhost:8000/info
   - Health Check: http://localhost:8000/health

## Notes

- The server will auto-reload when you make changes to Python files
- Logs are stored in the `logs/` directory
- Default port is 8000, can be changed in the command
