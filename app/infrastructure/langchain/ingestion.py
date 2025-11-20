"""
Ingestion service for documents and code.
"""

import mimetypes
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
import logging

# LangChain imports
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Local imports
from app.rag.embeddings import get_embedding_service
from app.infrastructure.langchain.vectorstore import get_vector_store_service
from app.connectors.gitlab_connector import get_gitlab_connector, GitLabConnector
from app.rag.ast_splitter import create_ast_splitter, ASTCodeSplitter
from app.config import get_logger, settings

# Configure logging
logger = get_logger(__name__)


class DocumentIngestionService:
    """
    Service for ingesting documents into the RAG system using LangChain
    """

    def __init__(self, data_path: str = "data"):
        """
        Initialize the ingestion service

        Args:
            data_path: Path to the data directory containing documents
        """
        self.data_path = Path(data_path)

        # Create data directory if it doesn't exist
        if not self.data_path.exists():
            logger.info(f"Creating data directory: {self.data_path}")
            self.data_path.mkdir(parents=True, exist_ok=True)

        self.embedding_service = get_embedding_service()
        self.vector_store_service = get_vector_store_service()

        # Initialize LangChain text splitter for document chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )

        logger.info(f"Initialized DocumentIngestionService with data path: {self.data_path}")

    def _extract_file_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from a file"""
        try:
            stat = file_path.stat()
            return {
                "file_name": file_path.name,
                "file_path": str(file_path),
                "file_size": stat.st_size,
                "file_type": file_path.suffix.lower(),
                "created_at": datetime.fromtimestamp(stat.st_ctime),
                "modified_at": datetime.fromtimestamp(stat.st_mtime),
                "mime_type": mimetypes.guess_type(str(file_path))[0] or "unknown"
            }
        except Exception as e:
            logger.error(f"Failed to extract metadata for {file_path}: {str(e)}")
            return {
                "file_name": file_path.name,
                "file_path": str(file_path),
                "file_type": file_path.suffix.lower(),
                "error": str(e)
            }

    def _load_file_content(self, file_path: Path) -> Optional[str]:
        """Load content from a file based on its extension"""
        try:
            file_ext = file_path.suffix.lower()
            
            # Handle different file types
            if file_ext in ['.pdf', '.docx', '.doc']:
                # Placeholder for PDF/Docx reading
                pass
            elif file_ext in ['.csv']:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            elif file_ext in ['.md', '.txt', '.py', '.js', '.ts', '.jsx', '.tsx', '.php', '.java', '.cpp', '.c', '.h']:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
                    
        except UnicodeDecodeError:
            logger.warning(f"Could not decode file as UTF-8: {file_path}")
            return None
        except Exception as e:
            logger.error(f"Failed to load file content: {str(e)}")
            return None

    def _process_single_file(self, file_path: Path) -> Tuple[List[Document], Dict[str, Any]]:
        """Process a single file and return documents with metadata"""
        try:
            logger.info(f"Processing file: {file_path}")

            # Extract file metadata
            file_metadata = self._extract_file_metadata(file_path)

            # Load file content
            content = self._load_file_content(file_path)
            if not content:
                logger.warning(f"No content extracted from {file_path}")
                return [], {**file_metadata, "status": "no_content"}

            # Create document with metadata
            doc = Document(
                page_content=content,
                metadata={
                    **file_metadata,
                    "id": f"{file_path.stem}_{hash(content) % 10000}"
                }
            )

            # Split document into chunks using LangChain text splitter
            try:
                chunks = self.text_splitter.split_documents([doc])
                logger.info(f"Text splitting created {len(chunks)} chunks from 1 document")
            except Exception as e:
                error_msg = f"Text splitting failed for {file_path}: {str(e)}"
                logger.error(error_msg)
                # If splitting fails, use the original document as a single chunk
                chunks = [doc]

            logger.info(f"Processed {file_path}: 1 document -> {len(chunks)} chunks")

            return chunks, {**file_metadata, "status": "success", "chunk_count": len(chunks)}

        except Exception as e:
            logger.error(f"Failed to process {file_path}: {str(e)}")
            file_metadata = self._extract_file_metadata(file_path)
            return [], {**file_metadata, "status": "error", "error_message": str(e)}

    async def ingest_directory(self, recursive: bool = True) -> Dict[str, Any]:
        """Ingest all documents from the data directory"""
        start_time = datetime.now()
        logger.info(f"Starting ingestion from {self.data_path}")

        if not self.data_path.exists():
            logger.error(f"Data directory does not exist: {self.data_path}")
            return {
                "success": False,
                "message": f"Data directory does not exist: {self.data_path}",
                "stats": {}
            }

        if recursive:
            files = list(self.data_path.rglob("*"))
        else:
            files = list(self.data_path.glob("*"))

        files = [f for f in files if f.is_file()]

        if not files:
            logger.warning(f"No files found in {self.data_path}")
            return {
                "success": True,
                "message": "No files to process",
                "stats": {"total_files": 0}
            }

        logger.info(f"Found {len(files)} files to process")

        all_documents = []
        processing_results = []

        for file_path in files:
            documents, metadata = self._process_single_file(file_path)
            all_documents.extend(documents)
            processing_results.append(metadata)

        stats = {
            "total_files": len(files),
            "processed_files": len([r for r in processing_results if r.get("status") == "success"]),
            "failed_files": len([r for r in processing_results if r.get("status") == "error"]),
            "total_chunks": len(all_documents),
            "start_time": start_time,
            "end_time": datetime.now()
        }

        if all_documents:
            try:
                logger.info(f"Adding {len(all_documents)} chunks to vector store")
                await self.vector_store_service.add_documents(all_documents)
                logger.info("Successfully added documents to vector store")
            except Exception as e:
                logger.error(f"Failed to add documents to vector store: {str(e)}")
                stats["vector_store_error"] = str(e)

        duration = stats["end_time"] - stats["start_time"]
        logger.info(f"Ingestion completed in {duration}: {stats}")

        return {
            "success": True,
            "message": f"Processed {stats['processed_files']}/{stats['total_files']} files successfully",
            "stats": stats,
            "processing_results": processing_results
        }

    def get_supported_file_types(self) -> List[str]:
        return ['.pdf', '.docx', '.doc', '.csv', '.md', '.txt', '.py', '.js', '.ts', '.jsx', '.tsx', '.php', '.java', '.cpp', '.c', '.h']


class CodeIngestionService:
    """
    Service for ingesting code from GitLab repositories into the RAG system.
    """

    def __init__(self,
                 gitlab_connector: Optional[GitLabConnector] = None,
                 ast_splitter: Optional[ASTCodeSplitter] = None):
        self.gitlab_connector = gitlab_connector or get_gitlab_connector()
        self.ast_splitter = ast_splitter or create_ast_splitter()
        logger.info("Initialized CodeIngestionService")

    async def ingest_repository(self, ref: str = 'main') -> Dict[str, Any]:
        """Ingest an entire GitLab repository."""
        start_time = datetime.now()
        logger.info(f"Starting repository ingestion (ref: {ref})")

        try:
            logger.info("Fetching files from GitLab...")
            documents = self.gitlab_connector.fetch_repository_documents(ref=ref)

            if not documents:
                return {
                    'success': False,
                    'message': 'No code files found in repository',
                    'stats': {'total_files': 0}
                }

            logger.info("Splitting documents into code chunks...")
            chunks = self.ast_splitter.split_documents(documents)

            stats = {
                'total_files': len(documents),
                'processed_chunks': len(chunks),
                'start_time': start_time,
                'end_time': datetime.now(),
            }

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
                'stats': {'total_files': 0}
            }

    async def ingest_files(self, file_paths: List[str], ref: str = 'main') -> Dict[str, Any]:
        """Ingest specific files from the repository."""
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
                doc = Document(page_content=content, metadata=metadata)
                documents.append(doc)

            except Exception as e:
                logger.error(f"Failed to process {file_path}: {str(e)}")
                failed_files.append(file_path)

        if not documents:
            return {
                'success': False,
                'message': f"Failed to fetch any of the {len(file_paths)} files",
                'stats': {'total_files': len(file_paths)}
            }

        chunks = self.ast_splitter.split_documents(documents)

        stats = {
            'total_files': len(file_paths),
            'processed_files': len(documents),
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
        try:
            return self.gitlab_connector.get_project_info()
        except Exception as e:
            logger.error(f"Failed to get repository info: {str(e)}")
            return {'error': str(e)}

    def list_code_files(self, ref: str = 'main') -> List[Dict[str, Any]]:
        try:
            code_files = self.gitlab_connector.fetch_all_code_files(ref=ref)
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
        try:
            if not self.gitlab_connector.test_connection():
                return False, "Failed to connect to GitLab"
            
            info = self.get_repository_info()
            if 'error' in info:
                return False, info['error']

            return True, f"Connected to repository: {info.get('name', 'Unknown')}"
        except Exception as e:
            return False, str(e)


# Global instances
_ingestion_service: Optional[DocumentIngestionService] = None
_code_ingestion_service: Optional[CodeIngestionService] = None


def get_ingestion_service() -> DocumentIngestionService:
    global _ingestion_service
    if _ingestion_service is None:
        _ingestion_service = DocumentIngestionService()
    return _ingestion_service


def get_code_ingestion_service() -> CodeIngestionService:
    global _code_ingestion_service
    if _code_ingestion_service is None:
        _code_ingestion_service = CodeIngestionService()
    return _code_ingestion_service
