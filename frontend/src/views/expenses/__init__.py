"""
Expenses View

Requirements: 4.1, 4.2 - Error handling for CRUD operations and form submissions
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtGui import QFont

from ...config import Fonts
from ...widgets.tables import DataTable
from ...widgets.forms import FormDialog
from ...widgets.dialogs import MessageDialog
from ...services.api import api, ApiException
from ...utils.error_handler import handle_ui_error


class ExpensesView(QWidget):
    """Expenses management view."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.categories = []
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        title = QLabel("إدارة المصروفات")
        title.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_H2, QFont.Bold))
        layout.addWidget(title)
        
        columns = [
            {'key': 'expense_number', 'label': 'الرقم'},
            {'key': 'category_name', 'label': 'الفئة'},
            {'key': 'description', 'label': 'الوصف'},
            {'key': 'expense_date', 'label': 'التاريخ', 'type': 'date'},
            {'key': 'total_amount', 'label': 'المبلغ', 'type': 'currency'},
        ]
        
        self.table = DataTable(columns)
        self.table.add_btn.clicked.connect(self.add_expense)
        layout.addWidget(self.table)
    
    @handle_ui_error
    def load_categories(self):
        """Load expense categories for the form."""
        response = api.get_expense_categories()
        if isinstance(response, dict) and 'results' in response:
            self.categories = response['results']
        else:
            self.categories = response if isinstance(response, list) else []
        
    def add_expense(self):
        # Load categories first
        self.load_categories()
        category_options = [{'value': c['id'], 'label': c['name']} for c in self.categories]
        
        fields = [
            {'key': 'category', 'label': 'الفئة', 'type': 'select', 'options': category_options, 'required': True},
            {'key': 'expense_date', 'label': 'التاريخ', 'type': 'date', 'required': True},
            {'key': 'amount', 'label': 'المبلغ', 'type': 'number', 'required': True},
            {'key': 'payee', 'label': 'المستفيد'},
            {'key': 'description', 'label': 'الوصف', 'type': 'textarea', 'required': True},
        ]
        dialog = FormDialog("إضافة مصروف", fields, parent=self)
        dialog.saved.connect(self.save_expense)
        dialog.exec()
    
    @handle_ui_error
    def save_expense(self, data: dict):
        """Save expense to API."""
        api.create_expense(data)
        MessageDialog.success(self, "نجاح", "تم إضافة المصروف بنجاح")
        self.refresh()
    
    @handle_ui_error
    def refresh(self):
        """Refresh expenses data from API."""
        response = api.get_expenses()
        if isinstance(response, dict) and 'results' in response:
            expenses = response['results']
        else:
            expenses = response if isinstance(response, list) else []
        self.table.set_data(expenses)
        
        # Also load categories
        self.load_categories()
