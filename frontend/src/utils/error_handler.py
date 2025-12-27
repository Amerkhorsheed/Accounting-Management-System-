"""
Frontend Error Handler - Centralized Error Handling Utilities

This module provides centralized error handling for the PySide6 frontend application.
It includes:
- ErrorHandler class with methods for displaying error dialogs and parsing API errors
- @handle_ui_error decorator for wrapping UI event handlers
- @handle_api_error decorator for wrapping API calls
- Comprehensive logging configuration with file rotation

Requirements: 6.3, 6.4, 3.1, 3.3, 7.1, 7.2, 7.3
"""
import logging
import logging.handlers
import os
import sys
import traceback
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Tuple, Optional, Any, Callable, Dict, List
import requests

from PySide6.QtWidgets import QMessageBox, QWidget

from .exceptions import (
    FrontendException,
    ConnectionException,
    TimeoutException,
    ValidationError,
)


# =============================================================================
# Logging Configuration
# Requirements: 7.1, 7.2, 7.3 - Comprehensive error logging with context
# =============================================================================

def _get_logs_directory() -> Path:
    """
    Get the logs directory path, creating it if necessary.
    
    Returns:
        Path to the logs directory
    """
    # Try to use a logs directory relative to the frontend folder
    # Navigate up from utils to src to frontend
    current_dir = Path(__file__).resolve().parent
    frontend_dir = current_dir.parent.parent  # frontend/src/utils -> frontend
    logs_dir = frontend_dir / 'logs'
    
    # Create logs directory if it doesn't exist
    try:
        logs_dir.mkdir(parents=True, exist_ok=True)
    except (PermissionError, OSError):
        # Fallback to user's home directory
        logs_dir = Path.home() / '.accounting_app' / 'logs'
        logs_dir.mkdir(parents=True, exist_ok=True)
    
    return logs_dir


def _setup_frontend_logging() -> logging.Logger:
    """
    Configure comprehensive logging for the frontend application.
    
    Requirements:
    - 7.1: Include timestamp, error type, and message
    - 7.2: Include full stack trace
    - 7.3: Include relevant context (user, request data, etc.)
    
    Returns:
        Configured logger instance
    """
    logs_dir = _get_logs_directory()
    
    # Create formatters
    # Verbose formatter with full context for file logs
    verbose_formatter = logging.Formatter(
        fmt='[%(asctime)s] %(levelname)s [%(name)s:%(lineno)d] %(module)s.%(funcName)s\n'
            'Message: %(message)s\n'
            '%(context_info)s'
            '---',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Simple formatter for console
    simple_formatter = logging.Formatter(
        fmt='%(levelname)s [%(name)s] %(message)s'
    )
    
    # Error-specific formatter with extra detail
    error_formatter = logging.Formatter(
        fmt='[%(asctime)s] %(levelname)s\n'
            'Logger: %(name)s:%(lineno)d\n'
            'Function: %(module)s.%(funcName)s\n'
            'Message: %(message)s\n'
            '%(context_info)s'
            '================================================================================',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Get or create the frontend logger
    frontend_logger = logging.getLogger('frontend')
    
    # Only configure if not already configured
    if not frontend_logger.handlers:
        frontend_logger.setLevel(logging.DEBUG)
        
        # Console handler for development
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        console_handler.addFilter(_ContextFilter())
        frontend_logger.addHandler(console_handler)
        
        # Main log file with rotation (5MB max, keep 5 backups)
        try:
            main_file_handler = logging.handlers.RotatingFileHandler(
                filename=logs_dir / 'frontend.log',
                maxBytes=5 * 1024 * 1024,  # 5 MB
                backupCount=5,
                encoding='utf-8'
            )
            main_file_handler.setLevel(logging.DEBUG)
            main_file_handler.setFormatter(verbose_formatter)
            main_file_handler.addFilter(_ContextFilter())
            frontend_logger.addHandler(main_file_handler)
        except (PermissionError, OSError) as e:
            print(f"Warning: Could not create main log file: {e}")
        
        # Error-specific log file with rotation (5MB max, keep 10 backups)
        try:
            error_file_handler = logging.handlers.RotatingFileHandler(
                filename=logs_dir / 'frontend_errors.log',
                maxBytes=5 * 1024 * 1024,  # 5 MB
                backupCount=10,
                encoding='utf-8'
            )
            error_file_handler.setLevel(logging.ERROR)
            error_file_handler.setFormatter(error_formatter)
            error_file_handler.addFilter(_ContextFilter())
            frontend_logger.addHandler(error_file_handler)
        except (PermissionError, OSError) as e:
            print(f"Warning: Could not create error log file: {e}")
    
    return frontend_logger


class _ContextFilter(logging.Filter):
    """
    Logging filter that adds context information to log records.
    
    Requirement 7.3: Include relevant context (user, request data, etc.)
    """
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add context_info attribute to the log record."""
        # Build context info string from extra attributes
        context_parts = []
        
        # Check for common context attributes
        context_attrs = [
            ('function', 'Function'),
            ('class_name', 'Class'),
            ('view', 'View'),
            ('user', 'User'),
            ('operation', 'Operation'),
            ('error_type', 'Error Type'),
            ('error_code', 'Error Code'),
            ('http_status', 'HTTP Status'),
            ('endpoint', 'Endpoint'),
            ('request_data', 'Request Data'),
        ]
        
        for attr, label in context_attrs:
            value = getattr(record, attr, None)
            if value is not None:
                context_parts.append(f'{label}: {value}')
        
        # Add traceback if present
        if record.exc_info:
            context_parts.append('Traceback: (see below)')
        
        # Set context_info attribute
        if context_parts:
            record.context_info = 'Context:\n  ' + '\n  '.join(context_parts) + '\n'
        else:
            record.context_info = ''
        
        return True


# Initialize the frontend logger
logger = _setup_frontend_logging()

# Also configure the module-level logger to use the same configuration
module_logger = logging.getLogger(__name__)
if not module_logger.handlers:
    module_logger.parent = logger


class ErrorHandler:
    """
    Centralized error handling for the frontend application.
    
    Provides static methods for:
    - Displaying user-friendly error dialogs
    - Parsing API error responses into user messages and technical details
    - Showing field-specific errors inline in forms
    - Showing business errors in dialogs with details
    
    Requirement 6.4: THE Frontend SHALL provide a utility function for displaying 
    error dialogs with consistent formatting
    Requirements 5.1, 5.2, 5.3, 5.4: Error message clarity and actionability
    """
    
    @staticmethod
    def show_error_dialog(
        parent: Optional[QWidget],
        title: str,
        message: str,
        details: Optional[str] = None
    ) -> None:
        """
        Show a user-friendly error dialog.
        
        Args:
            parent: Parent widget for the dialog (can be None)
            title: Dialog window title
            message: Main error message to display
            details: Optional technical details (shown in expandable section)
        """
        dialog = QMessageBox(parent)
        dialog.setIcon(QMessageBox.Critical)
        dialog.setWindowTitle(title)
        dialog.setText(message)
        
        if details:
            dialog.setDetailedText(details)
        
        dialog.exec()
    
    @staticmethod
    def show_business_error_dialog(
        parent: Optional[QWidget],
        error: Exception
    ) -> None:
        """
        Show a business error dialog with detailed explanation.
        
        Requirement 5.2: WHEN a business rule violation occurs THEN the Error_Handler 
        SHALL explain the rule that was violated
        
        Args:
            parent: Parent widget for the dialog (can be None)
            error: The exception containing business error details
        """
        dialog = QMessageBox(parent)
        dialog.setIcon(QMessageBox.Warning)
        dialog.setWindowTitle("خطأ في العملية")  # "Operation Error"
        
        # Extract business rule violation message
        business_message = ErrorHandler.extract_business_rule_violation(error)
        
        if business_message:
            dialog.setText(business_message)
        else:
            # Fallback to generic message
            user_message, _ = ErrorHandler.parse_api_error(error)
            dialog.setText(user_message)
        
        # Add technical details for debugging
        technical_details = ErrorHandler._build_technical_details(error)
        if technical_details:
            dialog.setDetailedText(technical_details)
        
        dialog.exec()
    
    @staticmethod
    def show_validation_error_dialog(
        parent: Optional[QWidget],
        error: Exception,
        form_dialog: Optional[Any] = None
    ) -> None:
        """
        Show validation errors with field-specific details.
        
        If a form_dialog is provided, also sets inline field errors.
        
        Requirement 5.1: WHEN a validation error occurs THEN the Error_Handler 
        SHALL display which field has the error and why
        
        Args:
            parent: Parent widget for the dialog (can be None)
            error: The exception containing validation errors
            form_dialog: Optional FormDialog to set inline field errors
        """
        # Extract field errors from the exception
        field_errors = {}
        if hasattr(error, 'field_errors') and error.field_errors:
            field_errors = error.field_errors
        
        # If we have a form dialog, set inline errors
        if form_dialog and field_errors:
            ErrorHandler.set_form_field_errors(form_dialog, field_errors)
        
        # Show dialog with formatted errors
        dialog = QMessageBox(parent)
        dialog.setIcon(QMessageBox.Warning)
        dialog.setWindowTitle("خطأ في البيانات")  # "Data Error"
        
        if field_errors:
            formatted_errors = ErrorHandler.format_validation_errors(field_errors)
            dialog.setText("يرجى تصحيح الأخطاء التالية:\n\n" + formatted_errors)
        else:
            user_message, _ = ErrorHandler.parse_api_error(error)
            dialog.setText(user_message)
        
        dialog.exec()
    
    @staticmethod
    def set_form_field_errors(form_dialog: Any, field_errors: Dict[str, List[str]]) -> None:
        """
        Set inline field errors on a FormDialog.
        
        Requirement 5.1: Show field-specific errors inline
        
        Args:
            form_dialog: The FormDialog instance
            field_errors: Dictionary mapping field names to error messages
        """
        if not hasattr(form_dialog, 'field_widgets'):
            return
        
        for field_name, messages in field_errors.items():
            # Try to find the field widget
            if field_name in form_dialog.field_widgets:
                field_widget = form_dialog.field_widgets[field_name]
                # Join multiple messages
                error_message = ', '.join(messages)
                field_widget.set_error(error_message)
    
    @staticmethod
    def clear_form_field_errors(form_dialog: Any) -> None:
        """
        Clear all inline field errors on a FormDialog.
        
        Args:
            form_dialog: The FormDialog instance
        """
        if not hasattr(form_dialog, 'field_widgets'):
            return
        
        for field_widget in form_dialog.field_widgets.values():
            field_widget.clear_error()
    
    @staticmethod
    def _build_technical_details(error: Exception) -> str:
        """
        Build technical details string from an exception.
        
        Args:
            error: The exception to extract details from
            
        Returns:
            Formatted technical details string
        """
        details_parts = []
        
        if hasattr(error, 'status_code') and error.status_code:
            details_parts.append(f"HTTP Status: {error.status_code}")
        if hasattr(error, 'error_code') and error.error_code:
            details_parts.append(f"Error Code: {error.error_code}")
        if hasattr(error, 'code') and error.code:
            details_parts.append(f"Code: {error.code}")
        if hasattr(error, 'detail') and error.detail:
            details_parts.append(f"Detail: {error.detail}")
        if hasattr(error, 'field_errors') and error.field_errors:
            field_info = []
            for field, messages in error.field_errors.items():
                field_info.append(f"  {field}: {', '.join(messages)}")
            if field_info:
                details_parts.append("Field Errors:\n" + '\n'.join(field_info))
        
        # Add exception type and message
        details_parts.append(f"\nException Type: {type(error).__name__}")
        details_parts.append(f"Message: {str(error)}")
        
        return '\n'.join(details_parts)
    
    @staticmethod
    def show_warning_dialog(
        parent: Optional[QWidget],
        title: str,
        message: str,
        details: Optional[str] = None
    ) -> None:
        """
        Show a warning dialog.
        
        Args:
            parent: Parent widget for the dialog (can be None)
            title: Dialog window title
            message: Main warning message to display
            details: Optional technical details (shown in expandable section)
        """
        dialog = QMessageBox(parent)
        dialog.setIcon(QMessageBox.Warning)
        dialog.setWindowTitle(title)
        dialog.setText(message)
        
        if details:
            dialog.setDetailedText(details)
        
        dialog.exec()
    
    @staticmethod
    def show_retry_dialog(
        parent: Optional[QWidget],
        title: str,
        message: str
    ) -> bool:
        """
        Show an error dialog with retry option.
        
        Args:
            parent: Parent widget for the dialog (can be None)
            title: Dialog window title
            message: Error message to display
            
        Returns:
            True if user clicked Retry, False otherwise
        """
        dialog = QMessageBox(parent)
        dialog.setIcon(QMessageBox.Warning)
        dialog.setWindowTitle(title)
        dialog.setText(message)
        dialog.setStandardButtons(QMessageBox.Retry | QMessageBox.Cancel)
        dialog.setDefaultButton(QMessageBox.Retry)
        
        return dialog.exec() == QMessageBox.Retry

    @staticmethod
    def parse_api_error(error: Exception) -> Tuple[str, str]:
        """
        Parse API error into user message and technical details.
        
        Extracts error information from various exception types and formats
        them into user-friendly messages and technical details for debugging.
        
        Requirement 3.3: WHEN the server returns an error response THEN the Frontend 
        SHALL parse and display the error details from the response
        
        Args:
            error: The exception to parse
            
        Returns:
            Tuple of (user_message, technical_details)
        """
        user_message = "حدث خطأ غير متوقع"  # Default: "An unexpected error occurred"
        technical_details = str(error)
        
        # Handle our custom frontend exceptions
        if isinstance(error, ConnectionException):
            user_message = error.message
            technical_details = f"Error Code: {error.code}\n{str(error)}"
            
        elif isinstance(error, TimeoutException):
            user_message = error.message
            technical_details = f"Error Code: {error.code}\n{str(error)}"
            
        elif isinstance(error, ValidationError):
            user_message = f"خطأ في الحقل '{error.field}': {error.message}"
            technical_details = f"Field: {error.field}\nError: {error.message}"
            
        elif isinstance(error, FrontendException):
            user_message = error.message
            technical_details = f"Error Code: {error.code}\n{str(error)}"
            
        # Handle enhanced ApiException from the API service
        elif hasattr(error, 'status_code') and hasattr(error, 'field_errors'):
            # This is our enhanced ApiException
            user_message = error.message
            
            # Build technical details
            details_parts = []
            if hasattr(error, 'status_code') and error.status_code:
                details_parts.append(f"HTTP Status: {error.status_code}")
            if hasattr(error, 'error_code') and error.error_code:
                details_parts.append(f"Error Code: {error.error_code}")
            if hasattr(error, 'detail') and error.detail:
                details_parts.append(f"Detail: {error.detail}")
            if hasattr(error, 'field_errors') and error.field_errors:
                field_info = []
                for field, messages in error.field_errors.items():
                    field_info.append(f"  {field}: {', '.join(messages)}")
                if field_info:
                    details_parts.append("Field Errors:\n" + '\n'.join(field_info))
            
            technical_details = '\n'.join(details_parts) if details_parts else str(error)
            
        # Handle legacy ApiException (string-based)
        elif hasattr(error, '__class__') and error.__class__.__name__ == 'ApiException':
            error_str = str(error)
            user_message, technical_details = ErrorHandler._parse_api_exception_string(error_str)
            
        # Handle requests library exceptions
        elif isinstance(error, requests.exceptions.Timeout):
            user_message = "انتهت مهلة الاتصال بالخادم"
            technical_details = f"Request Timeout: {str(error)}"
            
        elif isinstance(error, requests.exceptions.ConnectionError):
            user_message = "فشل الاتصال بالخادم"
            technical_details = f"Connection Error: {str(error)}"
            
        elif isinstance(error, requests.exceptions.RequestException):
            user_message = "فشل في الاتصال بالخادم"
            technical_details = f"Request Error: {str(error)}"
            
        else:
            # Generic exception handling
            user_message = "حدث خطأ غير متوقع"
            technical_details = f"Exception Type: {type(error).__name__}\nMessage: {str(error)}"
        
        return user_message, technical_details
    
    @staticmethod
    def _parse_api_exception_string(error_str: str) -> Tuple[str, str]:
        """
        Parse an API exception string into user message and technical details.
        
        API exceptions typically have format: "STATUS_CODE: error_details"
        
        Args:
            error_str: The error string from ApiException
            
        Returns:
            Tuple of (user_message, technical_details)
        """
        technical_details = error_str
        
        # Try to extract status code and message
        if ':' in error_str:
            parts = error_str.split(':', 1)
            status_part = parts[0].strip()
            message_part = parts[1].strip() if len(parts) > 1 else ""
            
            # Map HTTP status codes to user-friendly messages
            status_messages = {
                '400': 'خطأ في البيانات المدخلة',  # Bad Request
                '401': 'يرجى تسجيل الدخول مرة أخرى',  # Unauthorized
                '403': 'ليس لديك صلاحية لهذه العملية',  # Forbidden
                '404': 'العنصر المطلوب غير موجود',  # Not Found
                '409': 'تعارض في البيانات',  # Conflict
                '422': 'خطأ في التحقق من البيانات',  # Unprocessable Entity
                '500': 'خطأ في الخادم',  # Internal Server Error
                '502': 'خطأ في الاتصال بالخادم',  # Bad Gateway
                '503': 'الخادم غير متاح حالياً',  # Service Unavailable
            }
            
            # Get base message from status code
            user_message = status_messages.get(status_part, 'حدث خطأ غير متوقع')
            
            # If there's additional detail, append it
            if message_part:
                # Parse field-specific errors from DRF format
                field_errors = ErrorHandler._extract_field_errors(message_part)
                if field_errors:
                    user_message = field_errors
                elif len(message_part) < 200:  # Only show short messages
                    user_message = f"{user_message}: {message_part}"
        else:
            user_message = error_str if len(error_str) < 100 else 'حدث خطأ غير متوقع'
        
        return user_message, technical_details
    
    @staticmethod
    def _extract_field_errors(error_detail: str) -> Optional[str]:
        """
        Extract field-specific errors from DRF error format.
        
        DRF errors often come in format: "field_name: error message; field2: error2"
        
        Requirement 5.1: WHEN a validation error occurs THEN the Error_Handler 
        SHALL display which field has the error and why
        
        Args:
            error_detail: The error detail string
            
        Returns:
            Formatted field errors or None if not field-specific
        """
        if ';' in error_detail or ':' in error_detail:
            # Split by semicolon for multiple field errors
            parts = error_detail.split(';')
            formatted_errors = []
            
            for part in parts:
                part = part.strip()
                if ':' in part:
                    field, message = part.split(':', 1)
                    field = field.strip()
                    message = message.strip()
                    
                    # Translate common field names to Arabic
                    field_translations = {
                        'name': 'الاسم',
                        'code': 'الكود',
                        'barcode': 'الباركود',
                        'price': 'السعر',
                        'cost_price': 'سعر التكلفة',
                        'sale_price': 'سعر البيع',
                        'quantity': 'الكمية',
                        'stock': 'المخزون',
                        'stock_quantity': 'كمية المخزون',
                        'min_stock': 'الحد الأدنى للمخزون',
                        'detail': 'التفاصيل',
                        'non_field_errors': 'خطأ عام',
                        'description': 'الوصف',
                        'category': 'الفئة',
                        'supplier': 'المورد',
                        'customer': 'العميل',
                        'phone': 'الهاتف',
                        'email': 'البريد الإلكتروني',
                        'address': 'العنوان',
                        'date': 'التاريخ',
                        'due_date': 'تاريخ الاستحقاق',
                        'amount': 'المبلغ',
                        'total': 'الإجمالي',
                        'discount': 'الخصم',
                        'tax': 'الضريبة',
                        'notes': 'الملاحظات',
                        'status': 'الحالة',
                        'items': 'العناصر',
                        'product': 'المنتج',
                        'unit': 'الوحدة',
                        'username': 'اسم المستخدم',
                        'password': 'كلمة المرور',
                    }
                    
                    translated_field = field_translations.get(field, field)
                    formatted_errors.append(f"{translated_field}: {message}")
            
            if formatted_errors:
                return '\n'.join(formatted_errors)
        
        return None
    
    @staticmethod
    def extract_business_rule_violation(error: Exception) -> Optional[str]:
        """
        Extract business rule violation details from an error.
        
        Requirement 5.2: WHEN a business rule violation occurs THEN the Error_Handler 
        SHALL explain the rule that was violated
        
        Args:
            error: The exception to analyze
            
        Returns:
            Business rule violation message or None
        """
        # Check for enhanced ApiException with error_code
        if hasattr(error, 'error_code') and error.error_code:
            error_code = error.error_code
            
            # Map error codes to business rule explanations
            business_rules = {
                'INSUFFICIENT_STOCK': 'لا يوجد مخزون كافٍ لإتمام هذه العملية',
                'INVALID_OPERATION': 'هذه العملية غير مسموح بها في الحالة الحالية',
                'DUPLICATE_ERROR': 'هذا العنصر موجود بالفعل',
                'BUSINESS_ERROR': 'مخالفة لقواعد العمل',
                'VALIDATION_ERROR': 'خطأ في التحقق من البيانات',
                'PERMISSION_DENIED': 'ليس لديك صلاحية لهذه العملية',
                'NOT_FOUND': 'العنصر المطلوب غير موجود',
                'DATABASE_ERROR': 'خطأ في قاعدة البيانات',
                'NETWORK_ERROR': 'خطأ في الاتصال بالخدمة الخارجية',
                'CONFIG_ERROR': 'خطأ في إعدادات النظام',
            }
            
            if error_code in business_rules:
                base_message = business_rules[error_code]
                # Add detail if available
                if hasattr(error, 'detail') and error.detail:
                    return f"{base_message}: {error.detail}"
                return base_message
        
        # Check for detail in the error message
        if hasattr(error, 'detail') and error.detail:
            return error.detail
        
        return None
    
    @staticmethod
    def format_validation_errors(field_errors: Dict[str, List[str]]) -> str:
        """
        Format field-specific validation errors for display.
        
        Requirement 5.1: WHEN a validation error occurs THEN the Error_Handler 
        SHALL display which field has the error and why
        
        Args:
            field_errors: Dictionary mapping field names to error messages
            
        Returns:
            Formatted error string for display
        """
        if not field_errors:
            return ""
        
        # Field name translations
        translations = {
            'name': 'الاسم',
            'code': 'الكود',
            'barcode': 'الباركود',
            'price': 'السعر',
            'cost_price': 'سعر التكلفة',
            'sale_price': 'سعر البيع',
            'quantity': 'الكمية',
            'stock': 'المخزون',
            'stock_quantity': 'كمية المخزون',
            'min_stock': 'الحد الأدنى للمخزون',
            'description': 'الوصف',
            'category': 'الفئة',
            'supplier': 'المورد',
            'customer': 'العميل',
            'phone': 'الهاتف',
            'email': 'البريد الإلكتروني',
            'address': 'العنوان',
            'date': 'التاريخ',
            'due_date': 'تاريخ الاستحقاق',
            'amount': 'المبلغ',
            'total': 'الإجمالي',
            'subtotal': 'المجموع الفرعي',
            'discount': 'الخصم',
            'tax': 'الضريبة',
            'notes': 'الملاحظات',
            'status': 'الحالة',
            'items': 'العناصر',
            'product': 'المنتج',
            'unit': 'الوحدة',
            'username': 'اسم المستخدم',
            'password': 'كلمة المرور',
            'general': 'خطأ عام',
            'non_field_errors': 'خطأ عام',
        }
        
        formatted_lines = []
        for field, messages in field_errors.items():
            translated_field = translations.get(field, field)
            error_text = ', '.join(messages)
            formatted_lines.append(f"• {translated_field}: {error_text}")
        
        return '\n'.join(formatted_lines)


def handle_ui_error(func: Callable) -> Callable:
    """
    Decorator for UI event handlers.
    
    Catches exceptions in UI event handlers and displays appropriate error dialogs
    without crashing the application. Shows different dialogs based on error type:
    - Validation errors: Shows field-specific errors
    - Business errors: Shows business rule violation details
    - Other errors: Shows generic error dialog
    
    Requirement 6.3: THE Frontend SHALL provide a decorator for wrapping API calls with try-catch
    Requirement 4.1: WHEN an exception occurs in any button click handler THEN the Frontend 
    SHALL catch the exception and show an error dialog
    Requirement 7.1, 7.2, 7.3: Comprehensive error logging with context
    Requirements 5.1, 5.2, 5.3, 5.4: Error message clarity and actionability
    
    Usage:
        @handle_ui_error
        def on_button_clicked(self):
            # This code is protected from crashes
            self.do_something_risky()
    
    Args:
        func: The UI event handler function to wrap
        
    Returns:
        Wrapped function with error handling
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as e:
            # Build comprehensive context for logging
            # Requirement 7.3: Include relevant context
            context = {
                'function': func.__name__,
                'class_name': self.__class__.__name__ if hasattr(self, '__class__') else 'Unknown',
                'error_type': type(e).__name__,
                'view': getattr(self, 'objectName', lambda: 'Unknown')() if hasattr(self, 'objectName') else 'Unknown',
            }
            
            # Add error-specific context
            if hasattr(e, 'code'):
                context['error_code'] = e.code
            if hasattr(e, 'status_code'):
                context['http_status'] = e.status_code
            if hasattr(e, 'error_code'):
                context['error_code'] = e.error_code
            
            # Truncate args for safety (avoid logging sensitive data)
            if args:
                context['args'] = str(args)[:200]
            
            # Log the error with full context
            # Requirement 7.1: Include timestamp, error type, and message
            # Requirement 7.2: Include full stack trace (exc_info=True)
            logger.error(
                f"UI error in {func.__name__}: [{type(e).__name__}] {str(e)}",
                extra=context,
                exc_info=True  # This includes the full traceback
            )
            
            # Determine parent widget for dialog
            parent = self if isinstance(self, QWidget) else None
            
            # Handle different error types appropriately
            # Requirement 5.1, 5.2, 5.3, 5.4: Show appropriate error dialogs
            error_code = getattr(e, 'error_code', None) or getattr(e, 'code', None)
            
            # Check for validation errors (field-specific)
            if hasattr(e, 'field_errors') and e.field_errors:
                ErrorHandler.show_validation_error_dialog(parent, e)
            
            # Check for business rule violations
            elif error_code in ['INSUFFICIENT_STOCK', 'INVALID_OPERATION', 'DUPLICATE_ERROR', 
                               'BUSINESS_ERROR', 'PERMISSION_DENIED', 'NOT_FOUND']:
                ErrorHandler.show_business_error_dialog(parent, e)
            
            # Check for network/connection errors
            elif isinstance(e, (ConnectionException, TimeoutException)):
                user_message = e.message
                ErrorHandler.show_retry_dialog(parent, "خطأ في الاتصال", user_message)
            
            # Default: show generic error dialog
            else:
                user_message, technical_details = ErrorHandler.parse_api_error(e)
                ErrorHandler.show_error_dialog(
                    parent,
                    "خطأ",  # "Error" in Arabic
                    user_message,
                    technical_details
                )
            
            # Return None to indicate the operation failed
            return None
    
    return wrapper


def handle_api_error(func: Callable) -> Callable:
    """
    Decorator for API service methods.
    
    Catches network-related exceptions and converts them to typed frontend exceptions.
    This allows the UI layer to handle specific error types appropriately.
    
    Requirement 3.1: WHEN an API call fails THEN the Frontend SHALL catch the exception 
    and display a user-friendly error message
    Requirement 3.2: WHEN a network timeout occurs THEN the Frontend SHALL display 
    a specific timeout message with retry option
    Requirement 7.1, 7.2, 7.3: Comprehensive error logging with context
    
    Usage:
        @handle_api_error
        def get_products(self):
            return self._request('GET', 'products/')
    
    Args:
        func: The API method to wrap
        
    Returns:
        Wrapped function with error handling
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.Timeout as e:
            # Build context for logging
            context = {
                'function': func.__name__,
                'error_type': 'Timeout',
                'operation': 'API Request',
            }
            
            # Try to extract endpoint from args/kwargs
            if args and hasattr(args[0], '__class__'):
                context['class_name'] = args[0].__class__.__name__
            
            # Requirement 7.1, 7.2: Log with timestamp and traceback
            logger.error(
                f"API timeout in {func.__name__}: Request timed out",
                extra=context,
                exc_info=True
            )
            raise TimeoutException("انتهت مهلة الاتصال بالخادم. يرجى المحاولة مرة أخرى.")
            
        except requests.exceptions.ConnectionError as e:
            # Build context for logging
            context = {
                'function': func.__name__,
                'error_type': 'ConnectionError',
                'operation': 'API Request',
            }
            
            if args and hasattr(args[0], '__class__'):
                context['class_name'] = args[0].__class__.__name__
            
            logger.error(
                f"API connection error in {func.__name__}: {str(e)}",
                extra=context,
                exc_info=True
            )
            raise ConnectionException("فشل الاتصال بالخادم. يرجى التحقق من اتصال الشبكة.")
            
        except requests.exceptions.RequestException as e:
            # Build context for logging
            context = {
                'function': func.__name__,
                'error_type': type(e).__name__,
                'operation': 'API Request',
            }
            
            if args and hasattr(args[0], '__class__'):
                context['class_name'] = args[0].__class__.__name__
            
            logger.error(
                f"API request error in {func.__name__}: {str(e)}",
                extra=context,
                exc_info=True
            )
            raise ConnectionException(f"فشل في الاتصال بالخادم: {str(e)}")
            
        except Exception as e:
            # Log unexpected errors with full context
            context = {
                'function': func.__name__,
                'error_type': type(e).__name__,
                'operation': 'API Request',
            }
            
            if args and hasattr(args[0], '__class__'):
                context['class_name'] = args[0].__class__.__name__
            
            # Add error-specific context
            if hasattr(e, 'code'):
                context['error_code'] = e.code
            if hasattr(e, 'status_code'):
                context['http_status'] = e.status_code
            
            logger.error(
                f"Unexpected API error in {func.__name__}: [{type(e).__name__}] {str(e)}",
                extra=context,
                exc_info=True
            )
            raise
    
    return wrapper


# Export all public components
__all__ = [
    'ErrorHandler',
    'handle_ui_error',
    'handle_api_error',
    'log_error_with_context',
    'get_frontend_logger',
    'logger',
]


def get_frontend_logger(name: str = None) -> logging.Logger:
    """
    Get a logger configured for the frontend application.
    
    This ensures all frontend loggers use the same configuration
    with proper file handlers and formatters.
    
    Args:
        name: Optional logger name (will be prefixed with 'frontend.')
        
    Returns:
        Configured logger instance
    """
    if name:
        return logging.getLogger(f'frontend.{name}')
    return logger


def log_error_with_context(
    error: Exception,
    operation: str,
    context: Dict[str, Any] = None,
    logger_instance: logging.Logger = None
) -> None:
    """
    Log an error with comprehensive context information.
    
    This is a utility function for logging errors with full context
    when not using the decorators.
    
    Requirements:
    - 7.1: Include timestamp, error type, and message
    - 7.2: Include full stack trace
    - 7.3: Include relevant context
    
    Args:
        error: The exception to log
        operation: Description of the operation that failed
        context: Additional context information
        logger_instance: Optional specific logger to use
    
    Example:
        try:
            result = some_operation()
        except Exception as e:
            log_error_with_context(
                e,
                operation="Loading inventory data",
                context={'product_id': 123, 'user': 'admin'}
            )
    """
    log = logger_instance or logger
    
    # Build the context dictionary
    log_context = {
        'operation': operation,
        'error_type': type(error).__name__,
    }
    
    # Add error-specific attributes
    if hasattr(error, 'code'):
        log_context['error_code'] = error.code
    if hasattr(error, 'status_code'):
        log_context['http_status'] = error.status_code
    if hasattr(error, 'field'):
        log_context['field'] = error.field
    
    # Merge with provided context
    if context:
        log_context.update(context)
    
    # Log with full traceback
    log.error(
        f"Error during {operation}: [{type(error).__name__}] {str(error)}",
        extra=log_context,
        exc_info=True
    )
