"""
Dialog Widgets
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from ..config import Colors, Fonts


class ConfirmDialog(QDialog):
    """
    Confirmation dialog for dangerous actions.
    """
    
    def __init__(self, title: str, message: str, 
                 confirm_text: str = "تأكيد", 
                 cancel_text: str = "إلغاء",
                 danger: bool = True,
                 parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(400)
        self.danger = danger
        self.setup_ui(message, confirm_text, cancel_text)
        
    def setup_ui(self, message: str, confirm_text: str, cancel_text: str):
        """Initialize dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)
        
        # Icon and message
        icon_text = "⚠️" if self.danger else "❓"
        icon = QLabel(icon_text)
        icon.setFont(QFont(Fonts.FAMILY_AR, 36))
        icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon)
        
        msg = QLabel(message)
        msg.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_BODY))
        msg.setWordWrap(True)
        msg.setAlignment(Qt.AlignCenter)
        layout.addWidget(msg)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        cancel_btn = QPushButton(cancel_text)
        cancel_btn.setProperty("class", "secondary")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        confirm_btn = QPushButton(confirm_text)
        if self.danger:
            confirm_btn.setProperty("class", "danger")
        confirm_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(confirm_btn)
        
        layout.addLayout(buttons_layout)


class MessageDialog:
    """
    Static methods for showing message dialogs.
    
    Requirements 5.1, 5.2, 5.3, 5.4: Error message clarity and actionability
    """
    
    @staticmethod
    def success(parent, title: str, message: str):
        """Show success message."""
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.exec()
        
    @staticmethod
    def error(parent, title: str, message: str, details: str = None):
        """
        Show error message with optional details.
        
        Requirement 5.2: Show business errors in dialogs with details
        
        Args:
            parent: Parent widget
            title: Dialog title
            message: Main error message
            details: Optional technical details (shown in expandable section)
        """
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle(title)
        msg.setText(message)
        if details:
            msg.setDetailedText(details)
        msg.exec()
    
    @staticmethod
    def validation_error(parent, title: str, field_errors: dict):
        """
        Show validation error with field-specific messages.
        
        Requirement 5.1: Show field-specific errors inline
        
        Args:
            parent: Parent widget
            title: Dialog title
            field_errors: Dictionary mapping field names to error messages
        """
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
            'description': 'الوصف',
            'category': 'الفئة',
            'supplier': 'المورد',
            'customer': 'العميل',
            'phone': 'الهاتف',
            'email': 'البريد الإلكتروني',
            'address': 'العنوان',
            'date': 'التاريخ',
            'amount': 'المبلغ',
            'total': 'الإجمالي',
            'discount': 'الخصم',
            'tax': 'الضريبة',
            'notes': 'الملاحظات',
            'status': 'الحالة',
            'items': 'العناصر',
            'product': 'المنتج',
            'unit': 'الوحدة',
            'general': 'خطأ عام',
            'non_field_errors': 'خطأ عام',
        }
        
        # Format field errors
        formatted_lines = []
        for field, messages in field_errors.items():
            translated_field = translations.get(field, field)
            if isinstance(messages, list):
                error_text = ', '.join(messages)
            else:
                error_text = str(messages)
            formatted_lines.append(f"• {translated_field}: {error_text}")
        
        message = "يرجى تصحيح الأخطاء التالية:\n\n" + '\n'.join(formatted_lines)
        
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.exec()
    
    @staticmethod
    def business_error(parent, title: str, message: str, rule_explanation: str = None):
        """
        Show business rule violation error.
        
        Requirement 5.2: WHEN a business rule violation occurs THEN the Error_Handler 
        SHALL explain the rule that was violated
        
        Args:
            parent: Parent widget
            title: Dialog title
            message: Main error message
            rule_explanation: Optional explanation of the business rule violated
        """
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle(title)
        
        if rule_explanation:
            full_message = f"{message}\n\n{rule_explanation}"
        else:
            full_message = message
        
        msg.setText(full_message)
        msg.exec()
        
    @staticmethod
    def warning(parent, title: str, message: str):
        """Show warning message."""
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.exec()
        
    @staticmethod
    def confirm(parent, title: str, message: str) -> bool:
        """Show confirmation dialog."""
        reply = QMessageBox.question(
            parent, title, message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        return reply == QMessageBox.Yes
