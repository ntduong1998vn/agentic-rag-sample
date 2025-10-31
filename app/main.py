import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# RAG service imports
from app.routers.ingestion import router as ingestion_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
    * **FAISS Vector Storage**: Efficient similarity search
    * **Multi-format Support**: PDF, Word, Excel, text, images, and more
    * **RESTful API**: Clean API design with comprehensive documentation

    ## Endpoints

    * **Ingestion**: Process documents from `/data` directory
    * **Document Management**: List and manage processed documents
    * **Health Checks**: System monitoring and status reporting
    """,
    version="1.0.0",
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

# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint with API information
    """
    return {
        "message": "Agentic RAG API is running",
        "version": "1.0.0",
        "description": "Retrieval-augmented generation system with agentic capabilities",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "ingestion": "/ingest"
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
        "version": "1.0.0"
    }

# API information endpoint
@app.get("/info")
async def api_info():
    """
    Get detailed API information
    """
    return {
        "name": "Agentic RAG API",
        "version": "1.0.0",
        "description": "Retrieval-augmented generation system with agentic capabilities",
        "features": [
            "Japanese semantic document chunking",
            "Voyage AI 3.5 embeddings",
            "FAISS vector storage",
            "Multi-format document processing",
            "RESTful API design"
        ],
        "supported_file_types": [
            ".pdf", ".docx", ".doc", ".csv", ".txt", ".md",
            ".html", ".htm", ".jpg", ".jpeg", ".png", ".gif",
            ".bmp", ".tiff", ".epub"
        ],
        "endpoints": {
            "ingestion": "/ingest",
            "documents": "/ingest/documents",
            "stats": "/ingest/stats"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
