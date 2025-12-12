from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# New structure imports
from app.core.logging import initialize_logging, get_logger

# Initialize centralized logging
initialize_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    """
    # Startup
    logger.info("Starting Agentic RAG API...")
    logger.info("Agentic RAG API startup complete")

    yield

    # Shutdown
    logger.info("Shutting down Agentic RAG API...")


# Create FastAPI application with lifespan management
app = FastAPI(
    title="Agentic RAG API",
    description="""
    Retrieval-augmented generation system with agentic capabilities for in-house chatbot applications.

    ## Features

    * **Japanese Document Processing**: Semantic chunking optimized for Japanese text
    * **Google Gemini Embeddings**: State-of-the-art text embeddings (gemini-embedding-001)
    * **Qdrant Vector Storage**: Docker-containerized vector database with similarity search
    * **Multi-format Support**: PDF, Word, Excel, text, images, and more
    * **Conversational AI**: Chat with documents using Google Gemini 2.5 Flash-Lite
    * **Stateless Processing**: Each query processed independently without session memory
    * **Streaming Responses**: Real-time response streaming for better UX
    * **RESTful API**: Clean API design with comprehensive documentation
    * **GitLab Integration**: Ingest and search code from GitLab repositories
    * **AST-based Code Chunking**: Semantic analysis for Python, JavaScript, TypeScript, PHP

    ## Endpoints

    * **Chat**: `/chat` - Q&A with document retrieval and LLM generation
    * **Files**: `/files` - Document and code ingestion and management
    * **Chatbots**: `/chatbots` - Chatbot management and knowledge base ingestion
    * **Health Checks**: System monitoring and status reporting
    """,

    version="1.2.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
from app.api.v1.api import api_router as api_router_v1
from app.api.v2.api import api_router as api_router_v2

app.include_router(api_router_v1, prefix="/api/v1")
app.include_router(api_router_v2, prefix="/api/v2")



# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint with API information
    """
    return {
        "message": "Agentic RAG API is running",
        "version": "1.2.0",
        "description": "Retrieval-augmented generation system with agentic capabilities",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "chat": "/chat",
            "files": "/files",
            "chatbots": "/chatbots"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
