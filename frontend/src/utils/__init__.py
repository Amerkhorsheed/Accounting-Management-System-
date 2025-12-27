"""
Frontend Utilities Package
"""
from .exceptions import (
    FrontendException,
    ConnectionException,
    TimeoutException,
    ValidationError,
)
from .error_handler import (
    ErrorHandler,
    handle_ui_error,
    handle_api_error,
    log_error_with_context,
    get_frontend_logger,
)

__all__ = [
    # Exceptions
    'FrontendException',
    'ConnectionException',
    'TimeoutException',
    'ValidationError',
    # Error Handler
    'ErrorHandler',
    'handle_ui_error',
    'handle_api_error',
    'log_error_with_context',
    'get_frontend_logger',
]
