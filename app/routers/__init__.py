"""
Router modules for the RAG API.

This package contains all route definitions organized by functional area.
"""

from .system import router as system_router
from .query import router as query_router
from .ingestion import router as ingestion_router

__all__ = [
    "system_router",
    "query_router",
    "ingestion_router",
]