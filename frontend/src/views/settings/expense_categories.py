"""
Expense Categories Management View - Settings Page for Expense Category Management

Requirements: 11.1, 11.2, 11.3, 11.4, 11.5 - Full CRUD for Expense Categories
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from ...config import Colors, Fonts
from ...widgets.tables import DataTable
from ...widgets.forms import FormField
from ...widgets.dialogs import MessageDialog, ConfirmDialog
from ...services.api import api, ApiException
from ...utils.error_handler import handle_ui_error


class ExpenseCategoryDialog(QDialog):
    """
    Dialog for creating/editing expense categories.
    
    Requirements: 11.2, 11.3 - Add/edit dialog with name, parent, description
    """
    
    saved = Signal(dict)
    
    def __init__(self, title: str, data: dict = None, categories: list = None, parent=None):
        super().__init__(parent)
        self.data = data or {}
        self.categories = categories or []
        self.is_edit = bool(data and data.get('id'))
        self.setWindowTitle(title)
        self.setMinimumWidth(450)
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Form fields
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(12)
        
        # Name field (Arabic) - Required
        self.name_field = FormField(
            label='اسم الفئة',
            field_type='text',
            required=True,
            placeholder='مثال: رواتب، إيجار، مرافق'
        )
        if 'name' in self.data:
            self.name_field.set_value(self.data['name'])
        form_layout.addWidget(self.name_field)
        
        # Parent category field - Optional
        parent_options = [{'label': '-- بدون فئة أب --', 'value': None}]
        current_id = self.data.get('id')
        for cat in self.categories:
            # Don't allow selecting self as parent
            if current_id and cat.get('id') == current_id:
                continue
            parent_options.append({
                'label': cat.get('name', ''),
                'value': cat.get('id')
            })
        
        self.parent_field = FormField(
            label='الفئة الأب',
            field_type='select',
            required=False,
            options=parent_options
        )
        if 'parent' in self.data and self.data['parent']:
            self.parent_field.set_value(self.data['parent'])
        form_layout.addWidget(self.parent_field)
        
        # Description field - Optional
        self.description_field = FormField(
            label='الوصف',
            field_type='textarea',
            required=False,
            placeholder='وصف اختياري للفئة'
        )
        if 'description' in self.data:
            self.description_field.set_value(self.data['description'] or '')
        form_layout.addWidget(self.description_field)
        
        # Active checkbox
        self.is_active_field = FormField(
            label='نشط',
            field_type='checkbox',
            required=False
        )
        # Default to active for new categories
        is_active = self.data.get('is_active', True)
        self.is_active_field.set_value(is_active)
        form_layout.addWidget(self.is_active_field)
        
        layout.addWidget(form_widget)
        layout.addStretch()
        
        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        cancel_btn = QPushButton("إلغاء")
        cancel_btn.setProperty("class", "secondary")
        cancel_btn.setMinimumHeight(40)
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("حفظ")
        save_btn.setMinimumHeight(40)
        save_btn.clicked.connect(self.save)
        buttons_layout.addWidget(save_btn)
        
        layout.addLayout(buttons_layout)
        
    def save(self):
        """Validate and save form data."""
        # Validate required fields
        is_valid = True
        
        if not self.name_field.validate():
            is_valid = False
            
        if not is_valid:
            return
            
        # Collect data
        result = {
            'name': self.name_field.get_value(),
            'parent': self.parent_field.get_value(),
            'description': self.description_field.get_value() or None,
            'is_active': self.is_active_field.get_value(),
        }
        
        # Include ID if editing
        if self.is_edit:
            result['id'] = self.data.get('id')
            
        self.saved.emit(result)
        self.accept()


class ExpenseCategoriesView(QWidget):
    """
    Expense categories management view for settings.
    
    Requirements: 11.1 - Display expense categories list with name, parent, expense count columns
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.all_categories = []  # Store all categories for parent selection
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize expense categories management view UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header = QHBoxLayout()
        
        title = QLabel("إدارة فئات المصروفات")
        title.setProperty("class", "title")
        title.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_H2, QFont.Bold))
        header.addWidget(title)
        
        header.addStretch()
        
        layout.addLayout(header)
        
        # Description
        desc = QLabel("إدارة فئات المصروفات (رواتب، إيجار، مرافق، إلخ)")
        desc.setProperty("class", "subtitle")
        desc.setStyleSheet(f"color: {Colors.LIGHT_TEXT_SECONDARY}; margin-bottom: 16px;")
        layout.addWidget(desc)
        
        # Expense categories table
        # Requirements: 11.1 - Show name, parent, expense count columns
        columns = [
            {'key': 'name', 'label': 'اسم الفئة', 'type': 'text'},
            {'key': 'parent_name', 'label': 'الفئة الأب', 'type': 'text'},
            {'key': 'expenses_count', 'label': 'عدد المصروفات', 'type': 'text'},
            {'key': 'is_active_display', 'label': 'الحالة', 'type': 'text'},
        ]
        
        self.table = DataTable(columns)
        self.table.add_btn.setText("➕ إضافة فئة")
        self.table.add_btn.clicked.disconnect()  # Disconnect default handler
        self.table.add_btn.clicked.connect(self.add_category)
        self.table.action_clicked.connect(self.on_action)
        self.table.row_double_clicked.connect(self.edit_category)
        self.table.page_changed.connect(self.on_page_changed)
        
        layout.addWidget(self.table)
        
    @handle_ui_error
    def refresh(self):
        """Refresh expense categories data from API."""
        # Get pagination params
        params = self.table.get_pagination_params()
        
        response = api.get('expenses/categories/', params)
        
        # Handle paginated response
        if isinstance(response, dict) and 'results' in response:
            categories = response['results']
            total = response.get('count', len(categories))
        else:
            categories = response if isinstance(response, list) else []
            total = len(categories)
        
        # Store all categories for parent selection (fetch all without pagination)
        all_response = api.get('expenses/categories/')
        if isinstance(all_response, dict) and 'results' in all_response:
            self.all_categories = all_response['results']
        else:
            self.all_categories = all_response if isinstance(all_response, list) else []
        
        # Build parent lookup
        parent_lookup = {cat['id']: cat['name'] for cat in self.all_categories}
        
        # Format data for display
        for category in categories:
            # Get parent name
            parent_id = category.get('parent')
            category['parent_name'] = parent_lookup.get(parent_id, '-') if parent_id else '-'
            
            # Format is_active for display
            category['is_active_display'] = 'نشط' if category.get('is_active', True) else 'غير نشط'
            
            # Get expenses count (may need to be added to serializer)
            if 'expenses_count' not in category:
                category['expenses_count'] = 0
            
        self.table.set_data(categories, total)
    
    def on_page_changed(self, page: int, page_size: int):
        """Handle page change."""
        self.refresh()
        
    def add_category(self):
        """Show add expense category dialog."""
        dialog = ExpenseCategoryDialog(
            "إضافة فئة مصروفات جديدة",
            categories=self.all_categories,
            parent=self
        )
        dialog.saved.connect(self.save_category)
        dialog.exec()
        
    def edit_category(self, row: int, data: dict):
        """Show edit expense category dialog."""
        # Convert display status back to boolean for editing
        edit_data = data.copy()
        edit_data['is_active'] = data.get('is_active_display') == 'نشط'
        
        dialog = ExpenseCategoryDialog(
            "تعديل فئة المصروفات",
            edit_data,
            categories=self.all_categories,
            parent=self
        )
        dialog.saved.connect(lambda d: self.update_category(data.get('id'), d))
        dialog.exec()
        
    def on_action(self, action: str, row: int, data: dict):
        """Handle table action."""
        if action == 'edit':
            self.edit_category(row, data)
        elif action == 'delete':
            self.delete_category(data)
        elif action == 'add':
            self.add_category()
            
    @handle_ui_error
    def save_category(self, data: dict):
        """Save new expense category to API."""
        create_data = {
            'name': data['name'],
            'is_active': data.get('is_active', True),
        }
        
        # Only include optional fields if provided
        if data.get('parent'):
            create_data['parent'] = data['parent']
        if data.get('description'):
            create_data['description'] = data['description']
            
        api.create_expense_category(create_data)
        MessageDialog.success(self, "نجاح", "تم إضافة فئة المصروفات بنجاح")
        self.refresh()
        
    @handle_ui_error
    def update_category(self, category_id: int, data: dict):
        """Update existing expense category via API."""
        update_data = {
            'name': data['name'],
            'is_active': data.get('is_active', True),
        }
        
        # Include optional fields (can be null)
        update_data['parent'] = data.get('parent') or None
        update_data['description'] = data.get('description') or None
            
        api.update_expense_category(category_id, update_data)
        MessageDialog.success(self, "نجاح", "تم تحديث فئة المصروفات بنجاح")
        self.refresh()
        
    @handle_ui_error
    def delete_category(self, data: dict):
        """
        Delete expense category via API.
        
        Requirements: 11.4, 11.5 - Show confirmation dialog, prevent deletion if has expenses
        """
        expenses_count = data.get('expenses_count', 0)
        
        # Show warning if category has expenses
        if expenses_count > 0:
            MessageDialog.business_error(
                self,
                "لا يمكن الحذف",
                f"لا يمكن حذف هذه الفئة لأنها تحتوي على {expenses_count} مصروف.",
                "يجب نقل أو حذف جميع المصروفات من هذه الفئة قبل حذفها."
            )
            return
        
        dialog = ConfirmDialog(
            "حذف فئة المصروفات",
            f"هل أنت متأكد من حذف الفئة '{data.get('name')}'؟",
            parent=self
        )
        if dialog.exec():
            try:
                api.delete_expense_category(data.get('id'))
                MessageDialog.success(self, "نجاح", "تم حذف فئة المصروفات بنجاح")
                self.refresh()
            except ApiException as e:
                # Handle category in use error
                if 'CATEGORY_HAS_EXPENSES' in str(e.error_code) or 'مصروفات' in str(e.message):
                    MessageDialog.business_error(
                        self,
                        "لا يمكن الحذف",
                        "لا يمكن حذف هذه الفئة لأنها تحتوي على مصروفات.",
                        "يجب نقل أو حذف جميع المصروفات من هذه الفئة قبل حذفها."
                    )
                else:
                    raise
