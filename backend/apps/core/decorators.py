"""
Core Decorators - Error Handling Decorators for ViewSets and Services

This module provides decorators for consistent error handling across the application.
Implements Requirements 6.1, 6.2, 7.1, 7.2, 7.3.
"""
import logging
import traceback
from functools import wraps
from typing import Callable, Any

from django.db import IntegrityError, DatabaseError
from rest_framework.response import Response
from rest_framework import status

from .exceptions import (
    BusinessException,
    ValidationException,
    DatabaseException,
)

# Configure logger for error handling
logger = logging.getLogger('apps.core.decorators')


def _get_request_context(request) -> dict:
    """
    Extract context information from a request for logging.
    
    Args:
        request: The HTTP request object
        
    Returns:
        Dictionary with request context information
    """
    context = {
        'method': getattr(request, 'method', 'UNKNOWN'),
        'path': getattr(request, 'path', 'UNKNOWN'),
    }
    
    # Add user information if available
    if hasattr(request, 'user') and request.user:
        if hasattr(request.user, 'is_authenticated') and request.user.is_authenticated:
            context['user_id'] = getattr(request.user, 'id', None)
            context['username'] = getattr(request.user, 'username', None)
        else:
            context['user'] = 'anonymous'
    
    # Add request data (sanitized - avoid logging sensitive data)
    if hasattr(request, 'data') and request.data:
        # Only log keys, not values to avoid sensitive data exposure
        context['request_data_keys'] = list(request.data.keys()) if isinstance(request.data, dict) else 'non-dict'
    
    # Add query params
    if hasattr(request, 'query_params') and request.query_params:
        context['query_params'] = dict(request.query_params)
    
    return context


def _log_error(func_name: str, exception: Exception, context: dict = None) -> None:
    """
    Log an error with full context information.
    
    Implements Requirements 7.1, 7.2, 7.3:
    - Includes timestamp (handled by logging formatter)
    - Includes error type and message
    - Includes full stack trace
    - Includes relevant context (user, request data)
    
    Args:
        func_name: Name of the function where error occurred
        exception: The exception that was raised
        context: Additional context information
    """
    error_info = {
        'function': func_name,
        'error_type': type(exception).__name__,
        'error_message': str(exception),
        'context': context or {},
    }
    
    logger.error(
        f"Error in {func_name}: [{type(exception).__name__}] {str(exception)}",
        extra=error_info,
        exc_info=True  # This includes the full traceback
    )


def handle_view_error(func: Callable) -> Callable:
    """
    Decorator for ViewSet actions.
    
    Catches exceptions and returns proper JSON responses with error details.
    Implements Requirements 6.1, 7.1, 7.2, 7.3.
    
    Usage:
        class MyViewSet(viewsets.ModelViewSet):
            @handle_view_error
            @action(detail=False, methods=['get'])
            def my_action(self, request):
                # ... action code
    
    Args:
        func: The ViewSet action method to wrap
        
    Returns:
        Wrapped function with error handling
    """
    @wraps(func)
    def wrapper(self, request, *args, **kwargs):
        try:
            return func(self, request, *args, **kwargs)
        
        except BusinessException:
            # Let custom_exception_handler handle BusinessException subclasses
            # This ensures consistent error response format
            raise
        
        except IntegrityError as e:
            # Database integrity errors (unique constraints, foreign keys, etc.)
            context = _get_request_context(request)
            _log_error(func.__name__, e, context)
            
            # Parse the error to provide user-friendly message
            error_detail = str(e)
            user_message = 'خطأ في قاعدة البيانات'
            
            if 'UNIQUE constraint' in error_detail or 'unique' in error_detail.lower():
                user_message = 'القيمة المدخلة موجودة مسبقاً. يرجى استخدام قيمة مختلفة.'
            elif 'FOREIGN KEY' in error_detail or 'foreign key' in error_detail.lower():
                user_message = 'لا يمكن إتمام العملية لأن العنصر مرتبط بسجلات أخرى.'
            elif 'NOT NULL' in error_detail or 'not null' in error_detail.lower():
                user_message = 'يرجى ملء جميع الحقول المطلوبة.'
            
            return Response(
                {
                    'detail': user_message,
                    'code': 'DATABASE_INTEGRITY_ERROR',
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        except DatabaseError as e:
            # General database errors
            context = _get_request_context(request)
            _log_error(func.__name__, e, context)
            
            return Response(
                {
                    'detail': 'حدث خطأ في قاعدة البيانات. يرجى المحاولة مرة أخرى أو التواصل مع الدعم الفني.',
                    'code': 'DATABASE_ERROR',
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        except Exception as e:
            # Catch all other unexpected exceptions
            context = _get_request_context(request)
            _log_error(func.__name__, e, context)
            
            return Response(
                {
                    'detail': 'حدث خطأ غير متوقع. يرجى المحاولة مرة أخرى أو التواصل مع الدعم الفني.',
                    'code': 'INTERNAL_ERROR',
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    return wrapper


def handle_service_error(func: Callable) -> Callable:
    """
    Decorator for service methods.
    
    Catches exceptions and raises appropriate BusinessException subclasses.
    Implements Requirements 6.2, 7.1, 7.2, 7.3.
    
    Usage:
        class MyService:
            @staticmethod
            @handle_service_error
            def my_method(param1, param2):
                # ... service code
    
    Args:
        func: The service method to wrap
        
    Returns:
        Wrapped function with error handling
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        
        except BusinessException:
            # Re-raise BusinessException subclasses as-is
            # They already have proper error messages and codes
            raise
        
        except IntegrityError as e:
            # Database integrity errors - convert to ValidationException
            _log_error(func.__name__, e)
            
            # Extract useful information from the integrity error
            error_detail = str(e)
            if 'UNIQUE constraint' in error_detail or 'unique' in error_detail.lower():
                raise ValidationException(
                    'القيمة المدخلة موجودة مسبقاً. يرجى استخدام قيمة مختلفة.'
                )
            elif 'FOREIGN KEY' in error_detail or 'foreign key' in error_detail.lower():
                raise ValidationException(
                    'لا يمكن إتمام العملية لأن العنصر مرتبط بسجلات أخرى أو المرجع غير صالح.'
                )
            elif 'NOT NULL' in error_detail or 'not null' in error_detail.lower():
                raise ValidationException(
                    'يرجى ملء جميع الحقول المطلوبة.'
                )
            else:
                raise ValidationException(
                    'حدث خطأ في قاعدة البيانات. يرجى التحقق من البيانات المدخلة.'
                )
        
        except DatabaseError as e:
            # General database errors - convert to DatabaseException
            _log_error(func.__name__, e)
            raise DatabaseException(
                operation=func.__name__,
                detail=str(e)
            )
        
        except Exception as e:
            # Catch all other unexpected exceptions
            _log_error(func.__name__, e)
            raise BusinessException(
                message='حدث خطأ غير متوقع أثناء تنفيذ العملية. يرجى المحاولة مرة أخرى.',
                code='OPERATION_FAILED'
            )
    
    return wrapper
