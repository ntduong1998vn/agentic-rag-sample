"""
Centralized logging configuration for the Agentic RAG application

This module provides unified logging configuration with both console and file output,
including log rotation and structured formatting for easy debugging.
"""

import os
import sys
import logging
import logging.handlers
from pathlib import Path
from typing import Optional
from datetime import datetime


# Global configuration
_logging_initialized = False


def setup_logging(
    log_level: str = "DEBUG",
    log_file_path: str = "logs/app.log",
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 14,  # 14 days retention
    enable_console: bool = True
) -> None:
    """
    Setup centralized logging configuration

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file_path: Path to the log file
        max_bytes: Maximum bytes before rotation (default: 10MB)
        backup_count: Number of backup files to keep (default: 14)
        enable_console: Whether to enable console output
    """
    global _logging_initialized

    if _logging_initialized:
        return

    # Convert string log level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.DEBUG)

    # Create logs directory if it doesn't exist
    log_path = Path(log_file_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Clear any existing handlers
    root_logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)-20s | %(funcName)-15s:%(lineno)-4d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File handler with rotation (both daily and size-based)
    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename=log_file_path,
        when='midnight',  # Daily rotation
        interval=1,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(formatter)

    # Add size-based rotation as secondary handler
    size_handler = logging.handlers.RotatingFileHandler(
        filename=log_file_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    size_handler.setLevel(numeric_level)
    size_handler.setFormatter(formatter)

    root_logger.addHandler(file_handler)
    root_logger.addHandler(size_handler)

    # Console handler (optional)
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_formatter = logging.Formatter(
            fmt='%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

    # Log initialization
    init_logger = logging.getLogger(__name__)
    init_logger.info(f"Logging initialized - Level: {log_level}, File: {log_file_path}")
    init_logger.info(f"Log rotation: Daily at midnight + {max_bytes//(1024*1024)}MB max, {backup_count} days retention")

    _logging_initialized = True


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the centralized configuration

    Args:
        name: Module name (typically __name__)

    Returns:
        Configured logger instance
    """
    # Ensure logging is initialized
    if not _logging_initialized:
        # Get configuration from environment variables
        log_level = os.getenv("LOG_LEVEL", "DEBUG")
        log_file_path = os.getenv("LOG_FILE_PATH", "logs/app.log")
        enable_console = os.getenv("LOG_CONSOLE", "true").lower() == "true"

        setup_logging(
            log_level=log_level,
            log_file_path=log_file_path,
            enable_console=enable_console
        )

    return logging.getLogger(name)


def log_function_call(logger: logging.Logger, func_name: str, args: tuple = (), kwargs: dict = None):
    """
    Log function call details for debugging

    Args:
        logger: Logger instance
        func_name: Function name
        args: Function arguments
        kwargs: Function keyword arguments
    """
    if logger.isEnabledFor(logging.DEBUG):
        kwargs = kwargs or {}
        args_str = ", ".join([str(arg) for arg in args])
        kwargs_str = ", ".join([f"{k}={v}" for k, v in kwargs.items()])

        params = []
        if args_str:
            params.append(args_str)
        if kwargs_str:
            params.append(kwargs_str)

        params_str = ", ".join(params)
        logger.debug(f"Calling {func_name}({params_str})")


def log_performance(logger: logging.Logger, operation: str, duration: float, details: str = ""):
    """
    Log performance timing information

    Args:
        logger: Logger instance
        operation: Operation description
        duration: Duration in seconds
        details: Additional details
    """
    details_str = f" - {details}" if details else ""
    logger.debug(f"PERFORMANCE: {operation} took {duration:.3f}s{details_str}")


def log_api_request(logger: logging.Logger, method: str, path: str, status_code: int = None, duration: float = None):
    """
    Log API request information

    Args:
        logger: Logger instance
        method: HTTP method
        path: API path
        status_code: HTTP status code (optional)
        duration: Request duration in seconds (optional)
    """
    status_str = f" - {status_code}" if status_code else ""
    duration_str = f" - {duration:.3f}s" if duration else ""
    logger.info(f"API {method} {path}{status_str}{duration_str}")


def log_error_with_context(logger: logging.Logger, error: Exception, context: str = ""):
    """
    Log error with additional context information

    Args:
        logger: Logger instance
        error: Exception instance
        context: Additional context information
    """
    context_str = f" - Context: {context}" if context else ""
    logger.error(f"Error occurred{context_str}: {type(error).__name__}: {str(error)}", exc_info=True)


# Convenience function for quick logging setup
def initialize_logging():
    """
    Initialize logging with default settings from environment variables
    """
    log_level = os.getenv("LOG_LEVEL", "DEBUG")
    log_file_path = os.getenv("LOG_FILE_PATH", "logs/app.log")
    enable_console = os.getenv("LOG_CONSOLE", "true").lower() == "true"

    setup_logging(
        log_level=log_level,
        log_file_path=log_file_path,
        enable_console=enable_console
    )