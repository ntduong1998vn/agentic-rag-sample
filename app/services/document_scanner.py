"""
Document scanner for discovering files in a folder.
"""

import os
from pathlib import Path
from typing import List, NamedTuple

from app.core.logging import get_logger

logger = get_logger(__name__)

# Supported file extensions
SUPPORTED_EXTENSIONS = {
    '.pdf': 'application/pdf',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.doc': 'application/msword',
    '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    '.xls': 'application/vnd.ms-excel',
    '.md': 'text/markdown',
    '.txt': 'text/plain',
    '.csv': 'text/csv',
}


class FileInfo(NamedTuple):
    """Information about a discovered file."""
    path: str
    name: str
    size: int
    file_type: str


class DocumentScanner:
    """Scanner for discovering documents in a folder."""

    def __init__(self, supported_extensions: dict = None):
        self.supported_extensions = supported_extensions or SUPPORTED_EXTENSIONS

    def scan_folder(self, folder_path: str) -> List[FileInfo]:
        """
        Scan a folder and return information about supported files.
        
        Args:
            folder_path: Path to the folder to scan
            
        Returns:
            List of FileInfo objects for supported files
        """
        folder = Path(folder_path)
        if not folder.exists():
            logger.warning(f"Folder does not exist: {folder_path}")
            return []

        if not folder.is_dir():
            logger.warning(f"Path is not a directory: {folder_path}")
            return []

        files = []
        for file_path in folder.rglob('*'):
            if file_path.is_file():
                ext = file_path.suffix.lower()
                if ext in self.supported_extensions:
                    try:
                        file_info = FileInfo(
                            path=str(file_path.absolute()),
                            name=file_path.name,
                            size=file_path.stat().st_size,
                            file_type=self.supported_extensions[ext],
                        )
                        files.append(file_info)
                        logger.debug(f"Found supported file: {file_path.name}")
                    except OSError as e:
                        logger.error(f"Error reading file {file_path}: {e}")

        logger.info(f"Scanned folder {folder_path}: found {len(files)} supported files")
        return files
