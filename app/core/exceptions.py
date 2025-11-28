"""
Custom exceptions for the application.
"""


class BaseAppException(Exception):
    """Base exception for all application exceptions."""
    
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ConfigurationError(BaseAppException):
    """Raised when there is a configuration error."""
    pass


class DatabaseError(BaseAppException):
    """Raised when there is a database-related error."""
    pass


class VectorStoreError(BaseAppException):
    """Raised when there is a vector store-related error."""
    pass


class APIError(BaseAppException):
    """Raised when there is an API-related error."""
    pass


class AuthenticationError(BaseAppException):
    """Raised when there is an authentication error."""
    pass


class AuthorizationError(BaseAppException):
    """Raised when there is an authorization error."""
    pass


class ValidationError(BaseAppException):
    """Raised when there is a validation error."""
    pass


class NotFoundError(BaseAppException):
    """Raised when a resource is not found."""
    pass


class FileProcessingError(BaseAppException):
    """Raised when there is an error processing a file."""
    pass
