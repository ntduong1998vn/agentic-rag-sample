"""
Centralized logging configuration.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


_logging_initialized = False


def setup_logging(
    log_level: Optional[str] = None,
    log_file_path: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 14,
    enable_console: Optional[bool] = None
) -> None:
    """Setup centralized logging configuration."""
    global _logging_initialized
    if _logging_initialized:
        return

    from .config import settings
    
    log_level = log_level or settings.log_level
    log_file_path = log_file_path or settings.log_file_path
    enable_console = enable_console if enable_console is not None else settings.log_console

    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create logs directory
    log_path = Path(log_file_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    root_logger.handlers.clear()

    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)-20s | %(funcName)-15s:%(lineno)-4d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File handler
    file_handler = RotatingFileHandler(
        filename=log_file_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_formatter = logging.Formatter(
            fmt='%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

    # logging.getLogger(__name__).info(f"Logging initialized - Level: {log_level}")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    if not _logging_initialized:
        setup_logging()
    return logging.getLogger(name)


def initialize_logging():
    """Initialize logging with default settings."""
    setup_logging()
