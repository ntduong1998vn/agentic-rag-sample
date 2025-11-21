"""
Document scanner service.

This module handles scanning directories for files and extracting metadata.
"""

import os
import hashlib
import mimetypes
from pathlib import Path
from typing import List, Dict, Any, Generator
import logging

from app.domain.knowledge_base.entities import FileInfo

logger = logging.getLogger(__name__)


class DocumentScanner:
    """Service for scanning documents in a directory."""
    
    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path)
    
    def scan_directory(self, directory_path: str, recursive: bool = True) -> List[FileInfo]:
        """
        Scan a directory for files.
        
        Args:
            directory_path: Path to scan (relative to base_path or absolute)
            recursive: Whether to scan subdirectories
            
        Returns:
            List of FileInfo objects
        """
        path = Path(directory_path)
        if not path.is_absolute():
            path = self.base_path / path
            
        if not path.exists():
            logger.warning(f"Directory not found: {path}")
            return []
            
        if not path.is_dir():
            logger.warning(f"Path is not a directory: {path}")
            return []
            
        files: List[FileInfo] = []
        
        try:
            if recursive:
                file_iter = path.rglob("*")
            else:
                file_iter = path.glob("*")
                
            for file_path in file_iter:
                if file_path.is_file() and not file_path.name.startswith('.'):
                    try:
                        file_info = self._process_file(file_path)
                        files.append(file_info)
                    except Exception as e:
                        logger.error(f"Error processing file {file_path}: {e}")
                        
        except Exception as e:
            logger.error(f"Error scanning directory {path}: {e}")
            
        return files
    
    def _process_file(self, file_path: Path) -> FileInfo:
        """Extract metadata from a file."""
        # Get basic stats
        stats = file_path.stat()
        file_size = stats.st_size
        
        # Determine mime type
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = "application/octet-stream"
            
        # Calculate checksum
        checksum = self._calculate_checksum(file_path)
        
        return FileInfo(
            file_path=str(file_path),
            file_name=file_path.name,
            file_size=file_size,
            file_type=mime_type,
            checksum=checksum
        )
    
    def _calculate_checksum(self, file_path: Path, chunk_size: int = 8192) -> str:
        """Calculate SHA-256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(chunk_size), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
