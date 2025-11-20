"""
GitLab connector for fetching repository files and metadata using LangChain.

This module provides a connector to interact with GitLab repositories,
fetch file contents, and convert them to LangChain Documents.
"""

import os
from typing import List, Dict, Any, Optional
from pathlib import Path
import fnmatch
import time
from urllib.parse import urlparse

# GitLab API imports
import gitlab
from gitlab.v4.objects import Project

# LangChain imports
from langchain_core.documents import Document

# Local imports
from app.config import get_logger, settings

# Configure logging
logger = get_logger(__name__)


class GitLabConnector:
    """
    Connector for GitLab repositories. Handles authentication, file fetching,
    and conversion to LangChain Documents.
    """

    # Supported code file extensions for 4 languages
    CODE_EXTENSIONS = {
        '.py',     # Python
        '.js',     # JavaScript
        '.ts',     # TypeScript
        '.tsx',    # TypeScript React
        '.jsx',    # JavaScript React
        '.php',    # PHP
    }

    # Patterns to ignore (similar to .gitignore)
    IGNORE_PATTERNS = [
        'node_modules/**',
        'vendor/**',
        'dist/**',
        'build/**',
        '*.min.js',
        '*.bundle.js',
        '.git/**',
        '__pycache__/**',
        '*.pyc',
        '.env*',
        '*.log',
    ]

    def __init__(self, gitlab_url: Optional[str] = None,
                 gitlab_token: Optional[str] = None,
                 project_id: Optional[str] = None):
        """
        Initialize GitLab connector.

        Args:
            gitlab_url: GitLab instance URL (defaults to settings)
            gitlab_token: GitLab personal access token (defaults to settings)
            project_id: GitLab project ID (defaults to settings)
        """
        # Use centralized settings, fallback to parameters
        self.gitlab_url = gitlab_url or settings.gitlab_url
        self.gitlab_token = gitlab_token or settings.gitlab_token
        self.project_id = project_id or settings.gitlab_project_id

        if not self.gitlab_token:
            raise ValueError("GitLab token not provided. Set gitlab_token in settings or pass as parameter.")

        if not self.project_id:
            raise ValueError("GitLab project ID not provided. Set gitlab_project_id in settings or pass as parameter.")

        # Initialize GitLab client
        try:
            self.gl = gitlab.Gitlab(self.gitlab_url, private_token=self.gitlab_token)
            self.gl.auth()
            logger.info(f"Successfully authenticated to GitLab: {self.gitlab_url}")
        except Exception as e:
            logger.error(f"Failed to authenticate to GitLab: {str(e)}")
            raise

        # Get project
        try:
            self.project = self.gl.projects.get(self.project_id)
            logger.info(f"Connected to project: {self.project.name} (ID: {self.project_id})")
        except Exception as e:
            logger.error(f"Failed to get project {self.project_id}: {str(e)}")
            raise

    def should_ignore_path(self, file_path: str) -> bool:
        """
        Check if a file path should be ignored based on ignore patterns.

        Args:
            file_path: File path to check

        Returns:
            True if file should be ignored
        """
        for pattern in self.IGNORE_PATTERNS:
            if fnmatch.fnmatch(file_path, pattern):
                return True
        return False

    def is_code_file(self, file_path: str) -> bool:
        """
        Check if a file is a supported code file.

        Args:
            file_path: File path to check

        Returns:
            True if file is a code file
        """
        file_ext = Path(file_path).suffix.lower()
        return file_ext in self.CODE_EXTENSIONS

    def fetch_repository_tree(self, ref: str = 'main', recursive: bool = True) -> List[Dict[str, Any]]:
        """
        Fetch repository tree structure.

        Args:
            ref: Branch name, commit SHA, or tag
            recursive: Whether to fetch recursively

        Returns:
            List of tree items
        """
        try:
            logger.info(f"Fetching repository tree for ref: {ref}")

            # List repository tree
            items = self.project.repository_tree(path='', ref=ref, recursive=recursive, all=True)

            logger.info(f"Fetched {len(items)} items from repository tree")
            return items

        except Exception as e:
            logger.error(f"Failed to fetch repository tree: {str(e)}")
            raise

    def fetch_file_content(self, file_path: str, ref: str = 'main') -> Optional[str]:
        """
        Fetch content of a single file.

        Args:
            file_path: Path to the file in repository
            ref: Branch name, commit SHA, or tag

        Returns:
            File content as string or None if failed
        """
        try:
            # Get file from repository
            file = self.project.files.get(file_path=file_path, ref=ref)

            # Decode content
            import base64
            content = base64.b64decode(file.content).decode('utf-8')

            logger.debug(f"Fetched file: {file_path} ({len(content)} bytes)")
            return content

        except UnicodeDecodeError:
            logger.warning(f"Failed to decode file as UTF-8, skipping: {file_path}")
            return None
        except Exception as e:
            logger.error(f"Failed to fetch file {file_path}: {str(e)}")
            return None

    def fetch_file_metadata(self, file_path: str, ref: str = 'main') -> Dict[str, Any]:
        """
        Fetch metadata for a file.

        Args:
            file_path: Path to the file in repository
            ref: Branch name, commit SHA, or tag

        Returns:
            Dictionary with file metadata
        """
        try:
            # Get file info
            file = self.project.files.get(file_path=file_path, ref=ref)

            # Get last commit for this file
            commits = self.project.commits.list(path=file_path, ref_name=ref, per_page=1)
            last_commit = commits[0] if commits else None

            metadata = {
                'file_path': file_path,
                'file_name': Path(file_path).name,
                'file_size': file.size,
                'blob_id': file.blob_id,
                'commit_id': file.commit_id,
                'ref': ref,
                'last_commit': {
                    'id': last_commit.id if last_commit else None,
                    'author_name': last_commit.author_name if last_commit else None,
                    'author_email': last_commit.author_email if last_commit else None,
                    'authored_date': last_commit.authored_date if last_commit else None,
                    'message': last_commit.message if last_commit else None,
                } if last_commit else None,
            }

            return metadata

        except Exception as e:
            logger.error(f"Failed to fetch metadata for {file_path}: {str(e)}")
            return {'file_path': file_path, 'error': str(e)}

    def fetch_all_code_files(self, ref: str = 'main', progress_callback=None) -> List[Dict[str, Any]]:
        """
        Fetch all code files from the repository.

        Args:
            ref: Branch name, commit SHA, or tag
            progress_callback: Optional callback function for progress updates

        Returns:
            List of dictionaries with file info and content
        """
        logger.info(f"Fetching all code files from repository (ref: {ref})")

        # Get repository tree
        tree_items = self.fetch_repository_tree(ref=ref)

        code_files = []
        total_files = len(tree_items)
        processed = 0

        for item in tree_items:
            if item['type'] == 'blob':  # It's a file
                file_path = item['path']

                # Skip if should be ignored
                if self.should_ignore_path(file_path):
                    logger.debug(f"Ignoring file: {file_path}")
                    continue

                # Skip if not a code file
                if not self.is_code_file(file_path):
                    logger.debug(f"Skipping non-code file: {file_path}")
                    continue

                try:
                    # Fetch file content
                    content = self.fetch_file_content(file_path, ref=ref)
                    if content is None:
                        continue

                    # Fetch metadata
                    metadata = self.fetch_file_metadata(file_path, ref=ref)

                    # Add repository context
                    metadata.update({
                        'repository_name': self.project.name,
                        'repository_id': self.project.id,
                        'repository_url': self.project.web_url,
                        'default_branch': self.project.default_branch,
                        'visibility': self.project.visibility,
                    })

                    code_files.append({
                        'path': file_path,
                        'content': content,
                        'metadata': metadata,
                    })

                    logger.debug(f"Successfully fetched: {file_path}")

                except Exception as e:
                    logger.error(f"Error processing {file_path}: {str(e)}")
                    continue

            processed += 1
            if progress_callback and processed % 10 == 0:
                progress_callback(processed, total_files)

            # Rate limiting: sleep briefly every 20 files
            if processed % 20 == 0:
                time.sleep(0.1)

        logger.info(f"Fetched {len(code_files)} code files from repository")
        return code_files

    def to_documents(self, code_files: List[Dict[str, Any]]) -> List[Document]:
        """
        Convert code files to LangChain Documents.

        Args:
            code_files: List of code file dictionaries

        Returns:
            List of LangChain Document objects
        """
        documents = []

        for file_info in code_files:
            try:
                doc = Document(
                    page_content=file_info['content'],
                    metadata=file_info['metadata']
                )
                documents.append(doc)

                logger.debug(f"Created document for: {file_info['path']}")

            except Exception as e:
                logger.error(f"Failed to create document for {file_info['path']}: {str(e)}")
                continue

        logger.info(f"Converted {len(documents)} code files to LangChain Documents")
        return documents

    def fetch_repository_documents(self, ref: str = 'main',
                                   progress_callback=None) -> List[Document]:
        """
        Fetch all code files and convert to LangChain Documents.

        Args:
            ref: Branch name, commit SHA, or tag
            progress_callback: Optional callback for progress updates

        Returns:
            List of LangChain Document objects
        """
        logger.info("Starting repository fetch and document conversion")

        # Fetch all code files
        code_files = self.fetch_all_code_files(ref=ref, progress_callback=progress_callback)

        # Convert to documents
        documents = self.to_documents(code_files)

        logger.info(f"Completed: {len(documents)} documents created")
        return documents

    def get_project_info(self) -> Dict[str, Any]:
        """
        Get information about the connected project.

        Returns:
            Dictionary with project info
        """
        return {
            'id': self.project.id,
            'name': self.project.name,
            'description': self.project.description,
            'web_url': self.project.web_url,
            'default_branch': self.project.default_branch,
            'visibility': self.project.visibility,
            'path_with_namespace': self.project.path_with_namespace,
        }

    def test_connection(self) -> bool:
        """
        Test connection to GitLab and project access.

        Returns:
            True if connection successful
        """
        try:
            # Test authentication
            user = self.gl.user
            if user and hasattr(user, 'username'):
                logger.info(f"Connected as user: {user.username}")
            else:
                logger.info(f"Connected to GitLab")

            # Test project access
            project_info = self.get_project_info()
            logger.info(f"Project access confirmed: {project_info['name']}")

            return True
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False


# Global connector instance
_connector_instance: Optional[GitLabConnector] = None


def get_gitlab_connector() -> GitLabConnector:
    """
    Get the global GitLab connector instance.

    Returns:
        GitLabConnector instance
    """
    global _connector_instance
    if _connector_instance is None:
        _connector_instance = GitLabConnector()
    return _connector_instance


def validate_gitlab_config() -> bool:
    """
    Validate GitLab configuration using centralized settings.

    Returns:
        True if configuration is valid
    """
    required_configs = [settings.gitlab_token, settings.gitlab_project_id]
    if not all(required_configs):
        missing_configs = []
        if not settings.gitlab_token:
            missing_configs.append("gitlab_token")
        if not settings.gitlab_project_id:
            missing_configs.append("gitlab_project_id")
        logger.warning(f"Missing GitLab configuration: {', '.join(missing_configs)}")
        return False

    return True
