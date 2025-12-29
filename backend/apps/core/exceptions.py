"""
Core Exceptions - Custom Exception Classes and Exception Handler
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    """
    Custom exception handler for Django REST Framework.
    
    Handles all custom business exceptions and returns proper HTTP status codes
    and error formats as specified in Requirements 8.1, 8.2, 8.3, 8.4.
    """
    # First, call the default exception handler to get the standard error response
    response = exception_handler(exc, context)
    
    # Handle custom business exceptions
    if isinstance(exc, ValidationException):
        # Requirement 8.1: Return 400 with field-specific error messages
        data = {
            'detail': exc.message,
            'code': exc.code,
        }
        if exc.field:
            data['field'] = exc.field
        return Response(data, status=status.HTTP_400_BAD_REQUEST)
    
    elif isinstance(exc, NotFoundException):
        # Requirement 8.2: Return 404 with descriptive message
        return Response(
            {
                'detail': exc.message,
                'code': exc.code,
                'model': exc.model_name,
                'identifier': exc.identifier,
            },
            status=status.HTTP_404_NOT_FOUND
        )
    
    elif isinstance(exc, InsufficientStockException):
        # Requirement 8.3: Return 400 with violation details
        return Response(
            {
                'detail': exc.message,
                'code': exc.code,
                'product_name': exc.product_name,
                'requested': exc.requested,
                'available': exc.available,
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    elif isinstance(exc, InvalidOperationException):
        # Requirement 8.3: Return 400 with violation details
        return Response(
            {
                'detail': exc.message,
                'code': exc.code,
                'operation': exc.operation,
                'reason': exc.reason,
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    elif isinstance(exc, DuplicateException):
        # Requirement 8.3: Return 400 with violation details
        return Response(
            {
                'detail': exc.message,
                'code': exc.code,
                'field': exc.field,
                'value': exc.value,
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    elif isinstance(exc, PermissionDeniedException):
        # Requirement 8.4: Return 403 for permission errors
        return Response(
            {
                'detail': exc.message,
                'code': exc.code,
                'action': exc.action,
            },
            status=status.HTTP_403_FORBIDDEN
        )
    
    elif isinstance(exc, DatabaseException):
        # Requirement 8.1: Return 500 for database-related errors
        return Response(
            {
                'detail': exc.message,
                'code': exc.code,
                'operation': exc.operation,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    elif isinstance(exc, NetworkException):
        # Requirement 8.2: Return 502 for external service failures
        return Response(
            {
                'detail': exc.message,
                'code': exc.code,
                'service': exc.service,
            },
            status=status.HTTP_502_BAD_GATEWAY
        )
    
    elif isinstance(exc, ConfigurationException):
        # Return 500 for configuration errors
        return Response(
            {
                'detail': exc.message,
                'code': exc.code,
                'setting': exc.setting,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    elif isinstance(exc, DeletionProtectedException):
        # Return 400 for deletion protection errors
        return Response(
            {
                'detail': exc.message,
                'code': exc.code,
                'model': exc.model,
                'identifier': exc.identifier,
                'reason': exc.reason,
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    elif isinstance(exc, BusinessException):
        # Generic business exception - return 400
        return Response(
            {
                'detail': exc.message,
                'code': exc.code,
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Return the default response for other exceptions
    return response


class BusinessException(Exception):
    """Base exception for business logic errors."""
    
    def __init__(self, message: str, code: str = None):
        self.message = message
        self.code = code or 'BUSINESS_ERROR'
        super().__init__(self.message)


class ValidationException(BusinessException):
    """
    Exception for validation errors.
    
    Requirement 5.1: WHEN a validation error occurs THEN the Error_Handler 
    SHALL display which field has the error and why
    """
    
    # Field name translations for user-friendly messages
    FIELD_TRANSLATIONS = {
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
        'minimum_stock': 'الحد الأدنى للمخزون',
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
        'warehouse': 'المستودع',
        'invoice': 'الفاتورة',
        'order': 'الطلب',
        'payment': 'الدفعة',
        'expense': 'المصروف',
    }
    
    def __init__(self, message: str, field: str = None):
        self.field = field
        # If field is provided, create a user-friendly message with translated field name
        if field:
            translated_field = self.FIELD_TRANSLATIONS.get(field, field)
            user_message = f"خطأ في حقل '{translated_field}': {message}"
        else:
            user_message = message
        super().__init__(user_message, 'VALIDATION_ERROR')


class InsufficientStockException(BusinessException):
    """
    Exception when stock is insufficient for an operation.
    
    Requirement 5.2: WHEN a business rule violation occurs THEN the Error_Handler 
    SHALL explain the rule that was violated
    """
    
    def __init__(self, product_name: str, requested: int, available: int):
        message = (
            f"الكمية المتاحة من '{product_name}' غير كافية لإتمام العملية. "
            f"الكمية المطلوبة: {requested}، الكمية المتاحة: {available}. "
            f"يرجى تقليل الكمية المطلوبة أو زيادة المخزون."
        )
        self.product_name = product_name
        self.requested = requested
        self.available = available
        super().__init__(message, 'INSUFFICIENT_STOCK')


class DuplicateException(BusinessException):
    """
    Exception for duplicate record errors.
    
    Requirement 5.1: WHEN a validation error occurs THEN the Error_Handler 
    SHALL display which field has the error and why
    """
    
    # Field name translations for user-friendly messages
    FIELD_TRANSLATIONS = {
        'name': 'الاسم',
        'code': 'الكود',
        'barcode': 'الباركود',
        'email': 'البريد الإلكتروني',
        'phone': 'الهاتف',
        'invoice_number': 'رقم الفاتورة',
        'order_number': 'رقم الطلب',
        'payment_number': 'رقم الدفعة',
        'expense_number': 'رقم المصروف',
    }
    
    def __init__(self, field: str, value: str):
        translated_field = self.FIELD_TRANSLATIONS.get(field, field)
        message = f"القيمة '{value}' موجودة مسبقاً في حقل '{translated_field}'. يرجى استخدام قيمة مختلفة."
        self.field = field
        self.value = value
        super().__init__(message, 'DUPLICATE_ERROR')


class NotFoundException(BusinessException):
    """
    Exception when a record is not found.
    
    Requirement 5.4: WHEN a not found error occurs THEN the Error_Handler 
    SHALL specify what resource was not found
    """
    
    # Model name translations for user-friendly messages
    MODEL_TRANSLATIONS = {
        'Product': 'المنتج',
        'Category': 'الفئة',
        'Customer': 'العميل',
        'Supplier': 'المورد',
        'Invoice': 'الفاتورة',
        'PurchaseOrder': 'أمر الشراء',
        'Expense': 'المصروف',
        'Payment': 'الدفعة',
        'Stock': 'المخزون',
        'Warehouse': 'المستودع',
        'Unit': 'الوحدة',
        'User': 'المستخدم',
    }
    
    def __init__(self, model_name: str, identifier: str):
        translated_model = self.MODEL_TRANSLATIONS.get(model_name, model_name)
        message = f"لم يتم العثور على {translated_model} بالمعرف: {identifier}. تأكد من صحة المعرف أو أن العنصر لم يتم حذفه."
        self.model_name = model_name
        self.identifier = identifier
        super().__init__(message, 'NOT_FOUND')


class PermissionDeniedException(BusinessException):
    """
    Exception for permission denied errors.
    
    Requirement 5.3: WHEN a permission error occurs THEN the Error_Handler 
    SHALL explain what permission is required
    """
    
    # Action translations for user-friendly messages
    ACTION_TRANSLATIONS = {
        'create': 'إنشاء',
        'read': 'عرض',
        'update': 'تعديل',
        'delete': 'حذف',
        'approve': 'اعتماد',
        'confirm': 'تأكيد',
        'cancel': 'إلغاء',
        'export': 'تصدير',
        'import': 'استيراد',
        'view_reports': 'عرض التقارير',
        'manage_users': 'إدارة المستخدمين',
        'manage_settings': 'إدارة الإعدادات',
    }
    
    def __init__(self, action: str):
        translated_action = self.ACTION_TRANSLATIONS.get(action, action)
        message = f"ليس لديك صلاحية لتنفيذ: {translated_action}. يرجى التواصل مع مدير النظام للحصول على الصلاحيات المطلوبة."
        self.action = action
        super().__init__(message, 'PERMISSION_DENIED')


class InvalidOperationException(BusinessException):
    """
    Exception for invalid business operations.
    
    Requirement 5.2: WHEN a business rule violation occurs THEN the Error_Handler 
    SHALL explain the rule that was violated
    """
    
    # Operation translations for user-friendly messages
    OPERATION_TRANSLATIONS = {
        'confirm_invoice': 'تأكيد الفاتورة',
        'cancel_invoice': 'إلغاء الفاتورة',
        'approve_order': 'اعتماد الطلب',
        'receive_goods': 'استلام البضاعة',
        'return_items': 'إرجاع الأصناف',
        'adjust_stock': 'تعديل المخزون',
        'delete_product': 'حذف المنتج',
        'delete_customer': 'حذف العميل',
        'delete_supplier': 'حذف المورد',
    }
    
    def __init__(self, operation: str, reason: str):
        translated_operation = self.OPERATION_TRANSLATIONS.get(operation, operation)
        message = f"لا يمكن تنفيذ عملية '{translated_operation}': {reason}"
        self.operation = operation
        self.reason = reason
        super().__init__(message, 'INVALID_OPERATION')


class DatabaseException(BusinessException):
    """
    Exception for database-related errors.
    
    Requirement 8.1: THE Backend SHALL define DatabaseException for database-related errors
    """
    
    def __init__(self, operation: str, detail: str):
        # Provide user-friendly message without exposing internal details
        message = f"حدث خطأ في قاعدة البيانات أثناء تنفيذ العملية. يرجى المحاولة مرة أخرى أو التواصل مع الدعم الفني."
        self.operation = operation
        self.detail_msg = detail  # Keep technical details for logging
        super().__init__(message, 'DATABASE_ERROR')


class NetworkException(BusinessException):
    """
    Exception for external service call failures.
    
    Requirement 8.2: THE Backend SHALL define NetworkException for external service call failures
    """
    
    def __init__(self, service: str, detail: str):
        message = f"فشل الاتصال بالخدمة الخارجية '{service}'. يرجى التحقق من اتصال الشبكة والمحاولة مرة أخرى."
        self.service = service
        self.detail_msg = detail  # Keep technical details for logging
        super().__init__(message, 'NETWORK_ERROR')


class ConfigurationException(BusinessException):
    """Exception for configuration errors."""
    
    def __init__(self, setting: str, detail: str):
        message = f"خطأ في إعدادات النظام. يرجى التواصل مع مدير النظام لمراجعة الإعدادات."
        self.setting = setting
        self.detail_msg = detail  # Keep technical details for logging
        super().__init__(message, 'CONFIG_ERROR')


class DeletionProtectedException(BusinessException):
    """
    Exception when deletion is prevented due to related records.
    
    Requirement 11.5: WHEN a category has expenses THEN THE Desktop_App 
    SHALL prevent deletion and show an error message
    """
    
    # Model name translations for user-friendly messages
    MODEL_TRANSLATIONS = {
        'Product': 'المنتج',
        'Category': 'الفئة',
        'ExpenseCategory': 'فئة المصروفات',
        'Customer': 'العميل',
        'Supplier': 'المورد',
        'Invoice': 'الفاتورة',
        'PurchaseOrder': 'أمر الشراء',
        'Expense': 'المصروف',
        'Payment': 'الدفعة',
        'Stock': 'المخزون',
        'Warehouse': 'المستودع',
        'Unit': 'الوحدة',
        'User': 'المستخدم',
    }
    
    def __init__(self, model: str, identifier: str, reason: str):
        translated_model = self.MODEL_TRANSLATIONS.get(model, model)
        message = f"لا يمكن حذف {translated_model} '{identifier}': {reason}"
        self.model = model
        self.identifier = identifier
        self.reason = reason
        super().__init__(message, 'DELETION_PROTECTED')
