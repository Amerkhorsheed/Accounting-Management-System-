"""
Expenses View

Requirements: 4.1, 4.2 - Error handling for CRUD operations and form submissions
Requirements: 7.3 - Edit functionality for expenses
Requirements: 7.4 - Delete functionality for expenses
Requirements: 7.5 - Filtering by category and date range
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QComboBox, QDateEdit, QPushButton
)
from PySide6.QtGui import QFont
from PySide6.QtCore import QDate

from ...config import Fonts, Colors
from ...widgets.tables import DataTable
from ...widgets.forms import FormDialog
from ...widgets.dialogs import MessageDialog, ConfirmDialog
from ...services.api import api, ApiException
from ...utils.error_handler import handle_ui_error


class ExpensesView(QWidget):
    """
    Expenses management view with full CRUD and filtering.
    
    Requirements: 7.1 - Display expenses list
    Requirements: 7.2 - Add expense functionality
    Requirements: 7.3 - Edit expense functionality
    Requirements: 7.4 - Delete expense functionality
    Requirements: 7.5 - Filtering by category and date range
    """
    
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
        
        # Requirements: 7.5 - Filters section
        filters_frame = QFrame()
        filters_frame.setStyleSheet(f"background-color: {Colors.LIGHT_BG}; border-radius: 8px; padding: 12px;")
        filters_layout = QHBoxLayout(filters_frame)
        filters_layout.setSpacing(16)
        
        # Category filter dropdown
        filters_layout.addWidget(QLabel("الفئة:"))
        self.category_filter = QComboBox()
        self.category_filter.addItem("الكل", "")
        self.category_filter.setMinimumWidth(150)
        filters_layout.addWidget(self.category_filter)
        
        # Date range filter
        filters_layout.addWidget(QLabel("من:"))
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.date_from.setMaximumWidth(130)
        filters_layout.addWidget(self.date_from)
        
        filters_layout.addWidget(QLabel("إلى:"))
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setMaximumWidth(130)
        filters_layout.addWidget(self.date_to)
        
        # Apply filter button
        filter_btn = QPushButton("🔍 بحث")
        filter_btn.setProperty("class", "primary")
        filter_btn.clicked.connect(self.apply_filters)
        filters_layout.addWidget(filter_btn)
        
        # Clear filters button
        clear_btn = QPushButton("مسح")
        clear_btn.setProperty("class", "secondary")
        clear_btn.clicked.connect(self.clear_filters)
        filters_layout.addWidget(clear_btn)
        
        filters_layout.addStretch()
        layout.addWidget(filters_frame)
        
        columns = [
            {'key': 'expense_number', 'label': 'الرقم'},
            {'key': 'category_name', 'label': 'الفئة'},
            {'key': 'description', 'label': 'الوصف'},
            {'key': 'expense_date', 'label': 'التاريخ', 'type': 'date'},
            {'key': 'total_amount', 'label': 'المبلغ', 'type': 'currency'},
        ]
        
        # Requirements: 7.3, 7.4 - Enable edit and delete actions
        self.table = DataTable(columns, actions=['edit', 'delete'])
        self.table.add_btn.clicked.connect(self.add_expense)
        self.table.action_clicked.connect(self.on_action)
        self.table.row_double_clicked.connect(self.edit_expense)
        self.table.page_changed.connect(self.on_page_changed)
        self.table.sort_changed.connect(self.on_sort_changed)
        layout.addWidget(self.table)
    
    @handle_ui_error
    def load_categories(self):
        """Load expense categories for the form and filter."""
        response = api.get_expense_categories()
        if isinstance(response, dict) and 'results' in response:
            self.categories = response['results']
        else:
            self.categories = response if isinstance(response, list) else []
        
        # Update category filter dropdown
        current_category = self.category_filter.currentData()
        self.category_filter.clear()
        self.category_filter.addItem("الكل", "")
        for category in self.categories:
            self.category_filter.addItem(category.get('name', ''), category.get('id'))
        
        # Restore selection if possible
        if current_category:
            for i in range(self.category_filter.count()):
                if self.category_filter.itemData(i) == current_category:
                    self.category_filter.setCurrentIndex(i)
                    break
    
    def _get_category_options(self):
        """Get category options for form select field."""
        return [{'value': c['id'], 'label': c['name']} for c in self.categories]
    
    def _get_expense_fields(self):
        """Get form fields for expense create/edit."""
        category_options = self._get_category_options()
        return [
            {'key': 'category', 'label': 'الفئة', 'type': 'select', 'options': category_options, 'required': True},
            {'key': 'expense_date', 'label': 'التاريخ', 'type': 'date', 'required': True},
            {'key': 'amount', 'label': 'المبلغ', 'type': 'number', 'required': True},
            {'key': 'payee', 'label': 'المستفيد'},
            {'key': 'description', 'label': 'الوصف', 'type': 'textarea', 'required': True},
        ]
        
    def add_expense(self):
        """Add new expense."""
        # Load categories first
        self.load_categories()
        
        fields = self._get_expense_fields()
        dialog = FormDialog("إضافة مصروف", fields, parent=self)
        dialog.saved.connect(self.save_expense)
        dialog.exec()
    
    def edit_expense(self, row: int, data: dict):
        """
        Edit existing expense.
        
        Requirements: 7.3 - Handle double-click to open edit dialog
        """
        # Load categories first
        self.load_categories()
        
        fields = self._get_expense_fields()
        
        # Pre-populate form with current data
        edit_data = {
            'category': data.get('category'),
            'expense_date': data.get('expense_date'),
            'amount': data.get('amount'),
            'payee': data.get('payee', ''),
            'description': data.get('description', ''),
        }
        
        dialog = FormDialog("تعديل المصروف", fields, edit_data, parent=self)
        dialog.saved.connect(lambda d: self.update_expense(data.get('id'), d))
        dialog.exec()
    
    @handle_ui_error
    def save_expense(self, data: dict):
        """Save expense to API."""
        api.create_expense(data)
        MessageDialog.success(self, "نجاح", "تم إضافة المصروف بنجاح")
        self.refresh()
    
    @handle_ui_error
    def update_expense(self, expense_id: int, data: dict):
        """
        Update expense via API.
        
        Requirements: 7.3 - Call update API on save
        """
        editable_fields = ['category', 'expense_date', 'amount', 'payee', 'description']
        update_data = {k: v for k, v in data.items() if k in editable_fields and v is not None}
        
        api.update_expense(expense_id, update_data)
        MessageDialog.success(self, "نجاح", "تم تحديث المصروف بنجاح")
        self.refresh()
    
    def on_action(self, action: str, row: int, data: dict):
        """Handle table action."""
        if action == 'edit':
            self.edit_expense(row, data)
        elif action == 'delete':
            self.delete_expense(data)
    
    @handle_ui_error
    def delete_expense(self, data: dict):
        """
        Delete expense via API.
        
        Requirements: 7.4 - Delete with confirmation dialog
        """
        dialog = ConfirmDialog(
            "حذف المصروف",
            f"هل أنت متأكد من حذف المصروف '{data.get('expense_number')}'؟",
            parent=self
        )
        if dialog.exec():
            try:
                api.delete_expense(data.get('id'))
                MessageDialog.success(self, "نجاح", "تم حذف المصروف بنجاح")
                self.refresh()
            except ApiException as e:
                MessageDialog.error(self, "خطأ", f"فشل في حذف المصروف: {str(e)}")
    
    def _build_params(self) -> dict:
        """Build API parameters from filters."""
        params = self.table.get_pagination_params()
        params.update(self.table.get_sort_params())
        
        # Category filter
        category_id = self.category_filter.currentData()
        if category_id:
            params['category'] = category_id
        
        # Date range filter
        date_from = self.date_from.date().toString('yyyy-MM-dd')
        date_to = self.date_to.date().toString('yyyy-MM-dd')
        params['expense_date__gte'] = date_from
        params['expense_date__lte'] = date_to
        
        return params
    
    def apply_filters(self):
        """Apply filters and refresh."""
        self.table.current_page = 1
        self.refresh()
    
    def clear_filters(self):
        """Clear all filters."""
        self.category_filter.setCurrentIndex(0)
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.date_to.setDate(QDate.currentDate())
        self.table.current_page = 1
        self.refresh()
    
    def on_page_changed(self, page: int, page_size: int):
        """Handle page change."""
        self.refresh()
    
    def on_sort_changed(self, column: str, order: str):
        """Handle sort change."""
        self.refresh()
    
    @handle_ui_error
    def refresh(self):
        """Refresh expenses data from API."""
        # Load categories for filter dropdown
        self.load_categories()
        
        # Build params from filters
        params = self._build_params()
        
        response = api.get_expenses(params)
        if isinstance(response, dict):
            expenses = response.get('results', [])
            total = response.get('count', len(expenses))
        else:
            expenses = response if isinstance(response, list) else []
            total = len(expenses)
        
        self.table.set_data(expenses, total)
