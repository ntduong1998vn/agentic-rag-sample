from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# RAG service imports
from app.routers.ingestion import router as ingestion_router
from app.routers.chat import router as chat_router
from app.routers.code_ingestion import router as code_router
from app.config.logging_config import initialize_logging, get_logger

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
    * **Voyage AI 3.5 Embeddings**: State-of-the-art text embeddings
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
    * **Ingestion**: Process documents from `/data` directory
    * **Document Management**: List and manage processed documents
    * **Health Checks**: System monitoring and status reporting
    * **GitLab Code**: `/code` - Ingest and search GitLab repositories
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
app.include_router(ingestion_router)
app.include_router(chat_router)
app.include_router(code_router)

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
            "ingestion": "/ingest",
            "code": "/code"
        }
    }

# Enhanced health check endpoint
@app.get("/health")
async def health_check():
    """
    Basic health check endpoint
    """
    return {
        "status": "healthy",
        "service": "Agentic RAG API",
        "version": "1.2.0"
    }

# API information endpoint
@app.get("/info")
async def api_info():
    """
    Get detailed API information
    """
    return {
        "name": "Agentic RAG API",
        "version": "1.2.0",
        "description": "Retrieval-augmented generation system with agentic capabilities",
        "features": [
            "Japanese semantic document chunking",
            "Voyage AI 3.5 embeddings",
            "Qdrant vector storage",
            "Multi-format document processing",
            "Conversational AI with Google Gemini 2.5 Flash-Lite",
            "Stateless chat processing",
            "Streaming response support",
            "RESTful API design",
            "GitLab Integration",
            "AST-based Code Chunking (Python, JavaScript, TypeScript, PHP)"
        ],
        "supported_file_types": [
            ".pdf", ".docx", ".doc", ".csv", ".txt", ".md",
            ".html", ".htm", ".jpg", ".jpeg", ".png", ".gif",
            ".bmp", ".tiff", ".epub"
        ],
        "supported_code_languages": [
            "Python (.py)",
            "JavaScript (.js)",
            "TypeScript (.ts, .tsx)",
            "PHP (.php)"
        ],
        "endpoints": {
            "chat": "/chat",
            "ingestion": "/ingest",
            "documents": "/ingest/documents",
            "stats": "/ingest/stats",
            "code": "/code",
            "code_ingestion": "/code/ingest",
            "code_search": "/code/search",
            "code_stats": "/code/stats",
            "code_files": "/code/files"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
