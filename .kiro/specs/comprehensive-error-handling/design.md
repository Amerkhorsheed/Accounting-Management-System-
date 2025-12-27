# Design Document: Comprehensive Error Handling

## Overview

This design document outlines the implementation of comprehensive error handling (try-catch) across the entire Accounting Management System. The goal is to ensure all operations are wrapped in proper error handling with meaningful error messages that explain the reason for failures.

The system already has a foundation for error handling:
- Custom exception classes in `backend/apps/core/exceptions.py`
- Custom exception handler registered in Django REST Framework
- Basic error handling in `frontend/src/services/api.py`

This design extends that foundation to provide:
1. Decorators for consistent error handling in ViewSets and services
2. Enhanced frontend error handling with user-friendly messages
3. Comprehensive logging with context
4. Additional exception types for specific error categories

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      FRONTEND (PySide6)                          │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                   UI Event Handlers                          ││
│  │  @handle_ui_error decorator catches exceptions               ││
│  │  Shows error dialogs with user-friendly messages             ││
│  └─────────────────────────────────────────────────────────────┘│
│                              │                                   │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                   API Service Layer                          ││
│  │  @handle_api_error decorator catches network errors          ││
│  │  Parses error responses and raises typed exceptions          ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼ HTTP/REST
┌─────────────────────────────────────────────────────────────────┐
│                      BACKEND (Django)                            │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                   ViewSet Layer                              ││
│  │  @handle_view_error decorator catches exceptions             ││
│  │  Returns JSON responses with error details                   ││
│  └─────────────────────────────────────────────────────────────┘│
│                              │                                   │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                   Service Layer                              ││
│  │  @handle_service_error decorator catches exceptions          ││
│  │  Converts to BusinessException with context                  ││
│  └─────────────────────────────────────────────────────────────┘│
│                              │                                   │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              Custom Exception Handler                        ││
│  │  Converts all exceptions to proper HTTP responses            ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. Backend Error Handling Decorators

**Location:** `backend/apps/core/decorators.py`

```python
def handle_view_error(func):
    """
    Decorator for ViewSet actions.
    Catches exceptions and returns proper JSON responses.
    """
    @wraps(func)
    def wrapper(self, request, *args, **kwargs):
        try:
            return func(self, request, *args, **kwargs)
        except BusinessException:
            raise  # Let custom_exception_handler handle it
        except Exception as e:
            logger.exception(f"Unexpected error in {func.__name__}")
            return Response(
                {'detail': str(e), 'code': 'INTERNAL_ERROR'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    return wrapper

def handle_service_error(func):
    """
    Decorator for service methods.
    Catches exceptions and raises appropriate BusinessExceptions.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except BusinessException:
            raise
        except IntegrityError as e:
            logger.exception(f"Database integrity error in {func.__name__}")
            raise ValidationException(f"Database constraint violation: {str(e)}")
        except Exception as e:
            logger.exception(f"Unexpected error in {func.__name__}")
            raise BusinessException(f"Operation failed: {str(e)}")
    return wrapper
```

### 2. Additional Backend Exception Types

**Location:** `backend/apps/core/exceptions.py` (extend existing)

```python
class DatabaseException(BusinessException):
    """Exception for database-related errors."""
    def __init__(self, operation: str, detail: str):
        message = f"Database error during {operation}: {detail}"
        self.operation = operation
        self.detail_msg = detail
        super().__init__(message, 'DATABASE_ERROR')

class NetworkException(BusinessException):
    """Exception for external service call failures."""
    def __init__(self, service: str, detail: str):
        message = f"External service '{service}' failed: {detail}"
        self.service = service
        self.detail_msg = detail
        super().__init__(message, 'NETWORK_ERROR')

class ConfigurationException(BusinessException):
    """Exception for configuration errors."""
    def __init__(self, setting: str, detail: str):
        message = f"Configuration error for '{setting}': {detail}"
        self.setting = setting
        self.detail_msg = detail
        super().__init__(message, 'CONFIG_ERROR')
```

### 3. Frontend Error Handling Utilities

**Location:** `frontend/src/utils/error_handler.py`

```python
class ErrorHandler:
    """Centralized error handling for the frontend."""
    
    @staticmethod
    def show_error_dialog(parent, title: str, message: str, details: str = None):
        """Show a user-friendly error dialog."""
        dialog = QMessageBox(parent)
        dialog.setIcon(QMessageBox.Critical)
        dialog.setWindowTitle(title)
        dialog.setText(message)
        if details:
            dialog.setDetailedText(details)
        dialog.exec()
    
    @staticmethod
    def parse_api_error(error: ApiException) -> tuple[str, str]:
        """Parse API error into user message and technical details."""
        # Returns (user_message, technical_details)
        pass

def handle_ui_error(func):
    """Decorator for UI event handlers."""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except ApiException as e:
            user_msg, details = ErrorHandler.parse_api_error(e)
            ErrorHandler.show_error_dialog(self, "خطأ", user_msg, details)
        except Exception as e:
            logger.exception(f"UI error in {func.__name__}")
            ErrorHandler.show_error_dialog(self, "خطأ غير متوقع", str(e))
    return wrapper

def handle_api_error(func):
    """Decorator for API service methods."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.Timeout:
            raise TimeoutException("انتهت مهلة الاتصال بالخادم")
        except requests.exceptions.ConnectionError:
            raise ConnectionException("فشل الاتصال بالخادم")
        except Exception as e:
            logger.exception(f"API error in {func.__name__}")
            raise
    return wrapper
```

### 4. Frontend Exception Types

**Location:** `frontend/src/utils/exceptions.py`

```python
class FrontendException(Exception):
    """Base exception for frontend errors."""
    def __init__(self, message: str, code: str = None):
        self.message = message
        self.code = code or 'FRONTEND_ERROR'
        super().__init__(self.message)

class ConnectionException(FrontendException):
    """Exception for network connectivity issues."""
    def __init__(self, message: str = "فشل الاتصال بالخادم"):
        super().__init__(message, 'CONNECTION_ERROR')

class TimeoutException(FrontendException):
    """Exception for request timeout errors."""
    def __init__(self, message: str = "انتهت مهلة الاتصال"):
        super().__init__(message, 'TIMEOUT_ERROR')

class ValidationError(FrontendException):
    """Exception for client-side validation errors."""
    def __init__(self, field: str, message: str):
        self.field = field
        super().__init__(message, 'VALIDATION_ERROR')
```

## Data Models

No new data models are required. Error handling uses the existing logging infrastructure.

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: ViewSet Error Response Format
*For any* exception raised in a ViewSet action decorated with @handle_view_error, the response SHALL be a valid JSON object containing at least 'detail' and 'code' fields.
**Validates: Requirements 1.1, 1.2**

### Property 2: Service Exception Propagation
*For any* exception raised in a service method decorated with @handle_service_error, the exception SHALL be converted to a BusinessException subclass with a descriptive message.
**Validates: Requirements 2.1, 2.2**

### Property 3: API Error Parsing
*For any* error response from the backend API, the frontend error handler SHALL extract and display the error message from the response body.
**Validates: Requirements 3.3**

### Property 4: UI Error Containment
*For any* exception raised in a UI event handler decorated with @handle_ui_error, the application SHALL NOT crash and SHALL display an error dialog.
**Validates: Requirements 4.1, 4.2**

### Property 5: Error Logging Completeness
*For any* error logged by the error handler, the log entry SHALL contain timestamp, error type, message, and stack trace.
**Validates: Requirements 7.1, 7.2**

### Property 6: Validation Error Field Specificity
*For any* validation error response, the response SHALL include the specific field name that failed validation.
**Validates: Requirements 5.1, 8.1**

## Error Handling

### Error Response Format

All backend errors follow this JSON structure:

```json
{
    "detail": "Human-readable error message",
    "code": "ERROR_CODE",
    "field": "field_name (optional)",
    "context": { ... } // Additional context (optional)
}
```

### HTTP Status Code Mapping

| Exception Type | HTTP Status | Code |
|---------------|-------------|------|
| ValidationException | 400 | VALIDATION_ERROR |
| BusinessException | 400 | BUSINESS_ERROR |
| InsufficientStockException | 400 | INSUFFICIENT_STOCK |
| InvalidOperationException | 400 | INVALID_OPERATION |
| DuplicateException | 400 | DUPLICATE_ERROR |
| NotFoundException | 404 | NOT_FOUND |
| PermissionDeniedException | 403 | PERMISSION_DENIED |
| DatabaseException | 500 | DATABASE_ERROR |
| NetworkException | 502 | NETWORK_ERROR |
| Unhandled Exception | 500 | INTERNAL_ERROR |

### Frontend Error Display

| Error Type | Display Method |
|-----------|----------------|
| Validation Error | Inline field error + toast |
| Business Error | Error dialog with details |
| Network Error | Toast with retry option |
| Timeout Error | Toast with retry option |
| Unknown Error | Error dialog with technical details |

## Testing Strategy

### Dual Testing Approach

1. **Unit Tests**: Verify specific error scenarios and edge cases
2. **Property-Based Tests**: Verify error handling properties across all inputs

### Property-Based Testing Framework

Use **Hypothesis** for Python property-based testing:

```python
from hypothesis import given, strategies as st
```

### Test Categories

1. **Decorator Tests**
   - Test @handle_view_error catches all exception types
   - Test @handle_service_error converts exceptions properly
   - Test @handle_ui_error shows dialogs without crashing

2. **Exception Handler Tests**
   - Test custom_exception_handler returns correct status codes
   - Test error response format is consistent

3. **Error Parsing Tests**
   - Test frontend parses all error response formats
   - Test error messages are user-friendly

### Test Configuration

Each property-based test should run a minimum of 100 iterations.

Property tests must be tagged with the format:
`**Feature: comprehensive-error-handling, Property {number}: {property_text}**`
