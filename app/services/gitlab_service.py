"""
GitLab RAG Service - Business logic layer for code operations using LangChain.

Provides a unified interface for GitLab code ingestion, search, and retrieval.
Integrates with vector store for storage and retrieval.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import os

# Local imports
from app.connectors.gitlab_connector import get_gitlab_connector
from app.rag.code_ingestion import get_code_ingestion_service
from app.rag.embeddings import get_embedding_service, EmbeddingService
from app.rag.vector_store import get_vector_store_service, VectorStoreService
from app.config.logging_config import get_logger

# Configure logging
logger = get_logger(__name__)


class GitLabRAGService:
    """
    Service for GitLab code operations - ingestion, search, and management.
    Integrates with vector store for retrieval-augmented generation.
    """

    def __init__(self,
                 gitlab_connector=None,
                 code_ingestion_service=None,
                 embedding_service: Optional[EmbeddingService] = None,
                 vector_store_service: Optional[VectorStoreService] = None):
        """
        Initialize the GitLab RAG service.

        Args:
            gitlab_connector: GitLab connector instance
            code_ingestion_service: Code ingestion service instance
            embedding_service: Embedding service instance
            vector_store_service: Vector store service instance
        """
        self.gitlab_connector = gitlab_connector or get_gitlab_connector()
        self.code_ingestion_service = code_ingestion_service or get_code_ingestion_service()
        self.embedding_service = embedding_service or get_embedding_service()
        self.vector_store_service = vector_store_service or get_vector_store_service()

        logger.info("Initialized GitLabRAGService")

    async def ingest_repository(self, ref: str = 'main') -> Dict[str, Any]:
        """
        Ingest entire GitLab repository into vector store.

        Args:
            ref: Branch name, commit SHA, or tag

        Returns:
            Dictionary with ingestion results
        """
        start_time = datetime.now()
        logger.info(f"Starting repository ingestion (ref: {ref})")

        try:
            # Validate configuration
            is_valid, message = self.code_ingestion_service.validate_configuration()
            if not is_valid:
                return {
                    'success': False,
                    'message': message,
                    'stats': {
                        'total_files': 0,
                        'processed_chunks': 0,
                        'start_time': start_time,
                        'end_time': datetime.now(),
                        'duration_seconds': 0,
                    }
                }

            # Check for existing ingestion
            existing_count = self.get_repository_stats().get('total_chunks', 0)
            if existing_count > 0:
                logger.warning(f"Repository already has {existing_count} chunks. Use update or clear first.")
                return {
                    'success': False,
                    'message': f"Repository already has {existing_count} chunks. Use update or clear first.",
                    'stats': {
                        'total_files': 0,
                        'processed_chunks': existing_count,
                        'start_time': start_time,
                        'end_time': datetime.now(),
                        'duration_seconds': 0,
                    }
                }

            # Perform ingestion
            result = await self.code_ingestion_service.ingest_repository(ref=ref)

            if not result['success']:
                return result

            # Get chunks and add to vector store
            chunks = result['chunks']
            if chunks:
                logger.info(f"Adding {len(chunks)} chunks to vector store...")
                await self.vector_store_service.add_documents(chunks)
                logger.info("Successfully added chunks to vector store")

            # Calculate final statistics
            stats = result['stats']
            stats['repository'] = self.gitlab_connector.get_project_info()
            stats['duration_seconds'] = (stats['end_time'] - stats['start_time']).total_seconds()

            logger.info(f"Repository ingestion completed: {stats['processed_chunks']} chunks "
                       f"from {stats['total_files']} files ({stats['duration_seconds']:.1f}s)")

            return {
                'success': True,
                'message': result['message'],
                'stats': stats,
                'repository_info': self.gitlab_connector.get_project_info(),
            }

        except Exception as e:
            logger.error(f"Repository ingestion failed: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': f"Ingestion failed: {str(e)}",
                'stats': {
                    'total_files': 0,
                    'processed_chunks': 0,
                    'start_time': start_time,
                    'end_time': datetime.now(),
                    'duration_seconds': (datetime.now() - start_time).total_seconds(),
                }
            }

    async def search_code(self,
                         query: str,
                         top_k: int = 10,
                         similarity_threshold: float = 0.7,
                         language: Optional[str] = None,
                         file_path: Optional[str] = None,
                         chunk_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Search for relevant code chunks in the vector store.

        Args:
            query: Search query
            top_k: Number of results to return
            similarity_threshold: Minimum similarity score
            language: Filter by programming language
            file_path: Filter by file path pattern
            chunk_type: Filter by chunk type (file/class/function)

        Returns:
            Dictionary with search results
        """
        try:
            logger.info(f"Searching code with query: '{query}' (top_k={top_k})")

            if not query.strip():
                return {
                    'success': False,
                    'message': 'Query cannot be empty',
                    'results': [],
                    'total_results': 0,
                }

            # Search in vector store
            results = await self.vector_store_service.search(
                query=query,
                top_k=top_k,
                similarity_threshold=similarity_threshold
            )

            if not results:
                return {
                    'success': True,
                    'message': 'No results found',
                    'results': [],
                    'total_results': 0,
                    'query': query,
                    'filters': {
                        'language': language,
                        'file_path': file_path,
                        'chunk_type': chunk_type,
                    }
                }

            # Format results and apply filters
            formatted_results = []
            for result in results:
                doc = result.document
                metadata = doc.metadata or {}

                # Apply filters
                if language and metadata.get('language') != language:
                    continue
                if chunk_type and metadata.get('chunk_type') != chunk_type:
                    continue
                if file_path and file_path not in metadata.get('file_path', ''):
                    continue

                formatted_results.append({
                    'text': doc.page_content,
                    'score': result.score,
                    'metadata': metadata,
                    'chunk_type': metadata.get('chunk_type'),
                    'language': metadata.get('language'),
                    'file_path': metadata.get('file_path'),
                    'chunk_name': metadata.get('chunk_name'),
                    'signature': metadata.get('chunk_signature'),
                    'start_line': metadata.get('start_line'),
                    'end_line': metadata.get('end_line'),
                })

            logger.info(f"Found {len(formatted_results)} results after filtering")

            return {
                'success': True,
                'message': f"Found {len(formatted_results)} results",
                'results': formatted_results,
                'total_results': len(formatted_results),
                'query': query,
                'top_k': top_k,
                'similarity_threshold': similarity_threshold,
                'filters': {
                    'language': language,
                    'file_path': file_path,
                    'chunk_type': chunk_type,
                }
            }

        except Exception as e:
            logger.error(f"Code search failed: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': f"Search failed: {str(e)}",
                'results': [],
                'total_results': 0,
                'query': query,
            }

    def get_repository_stats(self) -> Dict[str, Any]:
        """
        Get statistics about ingested code in the vector store.

        Returns:
            Dictionary with repository statistics
        """
        try:
            logger.info("Retrieving repository statistics")

            # Get vector store stats
            vector_stats = self.vector_store_service.get_stats()

            # If no documents, return empty stats
            if vector_stats['document_count'] == 0:
                return {
                    'total_chunks': 0,
                    'total_files': 0,
                    'languages': {},
                    'chunk_types': {},
                    'total_lines': 0,
                    'repository_info': None,
                }

            # For now, return basic stats. In a complete implementation,
            # we would maintain a document registry with more detailed stats
            return {
                'total_chunks': vector_stats['document_count'],
                'total_files': 0,  # Would be tracked in registry
                'languages': {},   # Would be tracked in registry
                'chunk_types': {}, # Would be tracked in registry
                'total_lines': 0,  # Would be tracked in registry
                'repository_info': None,  # Would be stored during ingestion
            }

        except Exception as e:
            logger.error(f"Failed to get repository stats: {str(e)}")
            return {
                'error': str(e),
                'total_chunks': 0,
                'total_files': 0,
                'languages': {},
                'chunk_types': {},
                'total_lines': 0,
                'repository_info': None,
            }

    def list_ingested_files(self) -> Dict[str, Any]:
        """
        List all ingested files.

        Returns:
            Dictionary with file list
        """
        try:
            # For now, return empty list. In complete implementation,
            # would query vector store for unique file paths
            return {
                'success': True,
                'files': [],
                'total_files': 0,
            }

        except Exception as e:
            logger.error(f"Failed to list ingested files: {str(e)}")
            return {
                'success': False,
                'message': f"Failed to list files: {str(e)}",
                'files': [],
                'total_files': 0,
            }

    def clear_all_code(self) -> Dict[str, Any]:
        """
        Clear all code chunks from the vector store.

        Returns:
            Dictionary with operation results
        """
        try:
            logger.info("Clearing all code chunks from vector store")

            # Get current stats
            stats_before = self.get_repository_stats()

            # Clear the vector store (this clears everything, not just code)
            self.vector_store_service.clear_index()

            logger.info("Vector store cleared")

            return {
                'success': True,
                'message': f"Successfully cleared {stats_before['total_chunks']} code chunks",
                'cleared_chunks': stats_before['total_chunks'],
            }

        except Exception as e:
            logger.error(f"Failed to clear code chunks: {str(e)}")
            return {
                'success': False,
                'message': f"Failed to clear code chunks: {str(e)}",
                'cleared_chunks': 0,
            }

    def validate_setup(self) -> Tuple[bool, str]:
        """
        Validate that all components are properly configured.

        Returns:
            Tuple of (is_valid, message)
        """
        try:
            # Validate GitLab configuration
            if not os.environ.get('GITLAB_TOKEN'):
                return False, "GITLAB_TOKEN environment variable not set"

            if not os.environ.get('GITLAB_PROJECT_ID'):
                return False, "GITLAB_PROJECT_ID environment variable not set"

            # Test GitLab connectivity
            is_valid, message = self.code_ingestion_service.validate_configuration()
            if not is_valid:
                return False, message

            # Validate embedding service
            if not os.environ.get('VOYAGE_API_KEY'):
                return False, "VOYAGE_API_KEY environment variable not set"

            # Validate vector store
            if not os.environ.get('CHROMA_HOST'):
                logger.warning("CHROMA_HOST not set, using default: localhost")

            return True, "All components configured correctly"

        except Exception as e:
            return False, f"Validation failed: {str(e)}"

# Global service instance
_service_instance: Optional[GitLabRAGService] = None


def get_gitlab_rag_service() -> GitLabRAGService:
    """
    Get the global GitLab RAG service instance.

    Returns:
        GitLabRAGService instance
    """
    global _service_instance
    if _service_instance is None:
        _service_instance = GitLabRAGService()
    return _service_instance
