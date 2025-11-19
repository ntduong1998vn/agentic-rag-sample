"""
Code ingestion service for GitLab repositories using LangChain.

This module orchestrates the ingestion pipeline:
1. Fetch code files from GitLab
2. Split into AST-based chunks
3. Prepare documents for vector storage
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import os

# Local imports
from app.connectors.gitlab_connector import get_gitlab_connector, GitLabConnector
from app.rag.ast_splitter import create_ast_splitter, ASTCodeSplitter
from langchain_core.documents import Document
from app.config.logging_config import get_logger
from app.config.settings import settings

# Configure logging
logger = get_logger(__name__)


class CodeIngestionService:
    """
    Service for ingesting code from GitLab repositories into the RAG system.
    Orchestrates GitLab fetching and AST-based chunking using LangChain.
    """

    def __init__(self,
                 gitlab_connector: Optional[GitLabConnector] = None,
                 ast_splitter: Optional[ASTCodeSplitter] = None):
        """
        Initialize the code ingestion service.

        Args:
            gitlab_connector: GitLab connector instance (uses global if None)
            ast_splitter: AST splitter instance (uses global if None)
        """
        self.gitlab_connector = gitlab_connector or get_gitlab_connector()
        self.ast_splitter = ast_splitter or create_ast_splitter()

        logger.info("Initialized CodeIngestionService")

    async def ingest_repository(self, ref: str = 'main') -> Dict[str, Any]:
        """
        Ingest an entire GitLab repository.

        Args:
            ref: Branch name, commit SHA, or tag

        Returns:
            Dictionary with ingestion results and statistics
        """
        start_time = datetime.now()
        logger.info(f"Starting repository ingestion (ref: {ref})")

        try:
            # Fetch repository documents
            logger.info("Fetching files from GitLab...")
            documents = self.gitlab_connector.fetch_repository_documents(ref=ref)

            if not documents:
                return {
                    'success': False,
                    'message': 'No code files found in repository',
                    'stats': {
                        'total_files': 0,
                        'processed_chunks': 0,
                        'start_time': start_time,
                        'end_time': datetime.now(),
                    }
                }

            # Split documents into code chunks
            logger.info("Splitting documents into code chunks...")
            chunks = self.ast_splitter.split_documents(documents)

            # Calculate statistics
            stats = {
                'total_files': len(documents),
                'processed_files': len(documents),  # All files processed successfully
                'failed_files': 0,  # No failures in this implementation
                'processed_chunks': len(chunks),
                'start_time': start_time,
                'end_time': datetime.now(),
                'duration_seconds': (datetime.now() - start_time).total_seconds(),
            }

            duration = stats['end_time'] - stats['start_time']
            logger.info(f"Ingestion completed in {duration}: {len(chunks)} chunks from "
                       f"{len(documents)} files")

            return {
                'success': True,
                'message': f"Successfully processed {len(documents)} files into {len(chunks)} chunks",
                'chunks': chunks,
                'stats': stats,
            }

        except Exception as e:
            logger.error(f"Repository ingestion failed: {str(e)}")
            return {
                'success': False,
                'message': f"Ingestion failed: {str(e)}",
                'stats': {
                    'total_files': 0,
                    'processed_files': 0,
                    'failed_files': 0,
                    'processed_chunks': 0,
                    'start_time': start_time,
                    'end_time': datetime.now(),
                    'duration_seconds': (datetime.now() - start_time).total_seconds(),
                }
            }

    async def ingest_files(self, file_paths: List[str], ref: str = 'main') -> Dict[str, Any]:
        """
        Ingest specific files from the repository.

        Args:
            file_paths: List of file paths to ingest
            ref: Branch name, commit SHA, or tag

    Returns:
            Dictionary with ingestion results
        """
        start_time = datetime.now()
        logger.info(f"Starting ingestion of {len(file_paths)} specific files")

        documents = []
        failed_files = []

        for file_path in file_paths:
            try:
                content = self.gitlab_connector.fetch_file_content(file_path, ref=ref)
                if content is None:
                    failed_files.append(file_path)
                    continue

                metadata = self.gitlab_connector.fetch_file_metadata(file_path, ref=ref)

                doc = Document(
                    page_content=content,
                    metadata=metadata,
                )
                documents.append(doc)

            except Exception as e:
                logger.error(f"Failed to process {file_path}: {str(e)}")
                failed_files.append(file_path)

        if not documents:
            return {
                'success': False,
                'message': f"Failed to fetch any of the {len(file_paths)} files",
                'stats': {
                    'total_files': len(file_paths),
                    'processed_files': 0,
                    'failed_files': len(failed_files),
                    'processed_chunks': 0,
                    'start_time': start_time,
                    'end_time': datetime.now(),
                }
            }

        # Split into chunks
        chunks = self.ast_splitter.split_documents(documents)

        stats = {
            'total_files': len(file_paths),
            'processed_files': len(documents),
            'failed_files': len(failed_files),
            'processed_chunks': len(chunks),
            'start_time': start_time,
            'end_time': datetime.now(),
        }

        return {
            'success': True,
            'message': f"Processed {len(documents)}/{len(file_paths)} files into {len(chunks)} chunks",
            'chunks': chunks,
            'failed_files': failed_files,
            'stats': stats,
        }

    def get_repository_info(self) -> Dict[str, Any]:
        """
        Get information about the connected repository.

        Returns:
            Dictionary with repository info
        """
        try:
            return self.gitlab_connector.get_project_info()
        except Exception as e:
            logger.error(f"Failed to get repository info: {str(e)}")
            return {'error': str(e)}

    def list_code_files(self, ref: str = 'main') -> List[Dict[str, Any]]:
        """
        List all code files in the repository.

        Args:
            ref: Branch name, commit SHA, or tag

        Returns:
            List of file information dictionaries
        """
        try:
            code_files = self.gitlab_connector.fetch_all_code_files(ref=ref)
            logger.info(f"Found {len(code_files)} code files")

            # Return simplified info
            return [
                {
                    'path': f['path'],
                    'size': f['metadata']['file_size'],
                    'language': self._detect_language(f['path']),
                }
                for f in code_files
            ]
        except Exception as e:
            logger.error(f"Failed to list code files: {str(e)}")
            return []

    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file path"""
        from pathlib import Path
        ext = Path(file_path).suffix.lower()
        mapping = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.jsx': 'javascript',
            '.php': 'php',
        }
        return mapping.get(ext, 'unknown')

    def validate_configuration(self) -> Tuple[bool, str]:
        """
        Validate GitLab configuration and connectivity.

        Returns:
            Tuple of (is_valid, message)
        """
        try:
            # Test connection
            if not self.gitlab_connector.test_connection():
                return False, "Failed to connect to GitLab"

            # Check if we can list repository tree (read access)
            info = self.get_repository_info()
            if 'error' in info:
                return False, info['error']

            return True, f"Connected to repository: {info.get('name', 'Unknown')}"

        except Exception as e:
            return False, str(e)


# Global service instance
_service_instance: Optional[CodeIngestionService] = None


def get_code_ingestion_service() -> CodeIngestionService:
    """
    Get the global code ingestion service instance.

    Returns:
        CodeIngestionService instance
    """
    global _service_instance
    if _service_instance is None:
        _service_instance = CodeIngestionService()
    return _service_instance


def validate_code_ingestion_setup() -> Tuple[bool, str]:
    """
    Validate that code ingestion is properly configured.

    Returns:
        Tuple of (is_valid, message)
    """
    try:
        # Check configuration using centralized settings
        if not settings.gitlab_token:
            return False, "GitLab token not configured in settings"

        if not settings.gitlab_project_id:
            return False, "GitLab project ID not configured in settings"

        # Test service
        service = get_code_ingestion_service()
        is_valid, message = service.validate_configuration()

        return is_valid, message

    except Exception as e:
        return False, f"Setup validation failed: {str(e)}"


def get_ast_splitter() -> ASTCodeSplitter:
    """
    Get or create the global AST splitter instance
    
    Returns:
        ASTCodeSplitter instance
    """
    return create_ast_splitter()
