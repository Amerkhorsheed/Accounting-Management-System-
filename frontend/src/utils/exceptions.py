"""
Frontend Exceptions - Custom Exception Classes for the PySide6 Frontend

This module defines exception types for handling errors in the frontend application.
These exceptions provide typed error handling for network connectivity issues,
request timeouts, and client-side validation errors.

Requirements: 8.3, 8.4
"""


class FrontendException(Exception):
    """
    Base exception for frontend errors.
    
    All frontend-specific exceptions should inherit from this class
    to enable consistent error handling across the application.
    
    Attributes:
        message: Human-readable error message (in Arabic for user display)
        code: Machine-readable error code for programmatic handling
    """
    
    def __init__(self, message: str, code: str = None):
        self.message = message
        self.code = code or 'FRONTEND_ERROR'
        super().__init__(self.message)
    
    def __str__(self) -> str:
        return self.message
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(message='{self.message}', code='{self.code}')"


class ConnectionException(FrontendException):
    """
    Exception for network connectivity issues.
    
    Raised when the frontend cannot establish a connection to the backend server.
    This includes DNS resolution failures, connection refused errors, and
    network unreachable conditions.
    
    Requirement: 8.3 - THE Frontend SHALL define ConnectionException for network connectivity issues
    """
    
    def __init__(self, message: str = "فشل الاتصال بالخادم"):
        super().__init__(message, 'CONNECTION_ERROR')


class TimeoutException(FrontendException):
    """
    Exception for request timeout errors.
    
    Raised when a request to the backend server exceeds the configured timeout.
    This allows the UI to display appropriate retry options to the user.
    
    Requirement: 8.4 - THE Frontend SHALL define TimeoutException for request timeout errors
    """
    
    def __init__(self, message: str = "انتهت مهلة الاتصال بالخادم"):
        super().__init__(message, 'TIMEOUT_ERROR')


class ValidationError(FrontendException):
    """
    Exception for client-side validation errors.
    
    Raised when user input fails client-side validation before being sent
    to the backend. This enables immediate feedback to users without
    requiring a server round-trip.
    
    Attributes:
        field: The name of the field that failed validation
        message: Description of the validation failure
        code: Error code (always 'VALIDATION_ERROR')
    """
    
    def __init__(self, field: str, message: str):
        self.field = field
        super().__init__(message, 'VALIDATION_ERROR')
    
    def __repr__(self) -> str:
        return f"ValidationError(field='{self.field}', message='{self.message}')"
