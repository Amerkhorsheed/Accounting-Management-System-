"""
Warehouses Management View - Settings Page for Warehouse Management

Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6 - Full CRUD for Warehouses
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QFrame, QDialog,
    QFormLayout, QCheckBox, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from ...config import Colors, Fonts
from ...widgets.tables import DataTable
from ...widgets.forms import FormField
from ...widgets.dialogs import MessageDialog, ConfirmDialog
from ...services.api import api, ApiException
from ...utils.error_handler import handle_ui_error


class WarehouseDialog(QDialog):
    """
    Dialog for creating/editing warehouses.
    
    Requirements: 10.2, 10.3 - Add/edit dialog with code, name, address, is_default
    """
    
    saved = Signal(dict)
    
    def __init__(self, title: str, data: dict = None, parent=None):
        super().__init__(parent)
        self.data = data or {}
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
        
        # Code field - Required
        self.code_field = FormField(
            label='رمز المستودع',
            field_type='text',
            required=True,
            placeholder='مثال: WH001، MAIN، BRANCH1'
        )
        if 'code' in self.data:
            self.code_field.set_value(self.data['code'])
        form_layout.addWidget(self.code_field)
        
        # Name field - Required
        self.name_field = FormField(
            label='اسم المستودع',
            field_type='text',
            required=True,
            placeholder='مثال: المستودع الرئيسي، فرع دمشق'
        )
        if 'name' in self.data:
            self.name_field.set_value(self.data['name'])
        form_layout.addWidget(self.name_field)
        
        # Address field - Optional
        self.address_field = FormField(
            label='العنوان',
            field_type='textarea',
            required=False,
            placeholder='عنوان المستودع (اختياري)'
        )
        if 'address' in self.data:
            self.address_field.set_value(self.data['address'] or '')
        form_layout.addWidget(self.address_field)
        
        # Is Default checkbox
        self.is_default_field = FormField(
            label='المستودع الافتراضي',
            field_type='checkbox',
            required=False
        )
        is_default = self.data.get('is_default', False)
        self.is_default_field.set_value(is_default)
        form_layout.addWidget(self.is_default_field)
        
        # Active checkbox
        self.is_active_field = FormField(
            label='نشط',
            field_type='checkbox',
            required=False
        )
        # Default to active for new warehouses
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
        
        if not self.code_field.validate():
            is_valid = False
        if not self.name_field.validate():
            is_valid = False
            
        if not is_valid:
            return
            
        # Collect data
        result = {
            'code': self.code_field.get_value(),
            'name': self.name_field.get_value(),
            'address': self.address_field.get_value() or None,
            'is_default': self.is_default_field.get_value(),
            'is_active': self.is_active_field.get_value(),
        }
        
        # Include ID if editing
        if self.is_edit:
            result['id'] = self.data.get('id')
            
        self.saved.emit(result)
        self.accept()


class WarehousesView(QWidget):
    """
    Warehouses management view for settings.
    
    Requirements: 10.1 - Display warehouses list with code, name, address, is_default columns
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize warehouses management view UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header = QHBoxLayout()
        
        title = QLabel("إدارة المستودعات")
        title.setProperty("class", "title")
        title.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_H2, QFont.Bold))
        header.addWidget(title)
        
        header.addStretch()
        
        layout.addLayout(header)
        
        # Description
        desc = QLabel("إدارة مواقع التخزين والمستودعات")
        desc.setProperty("class", "subtitle")
        desc.setStyleSheet(f"color: {Colors.LIGHT_TEXT_SECONDARY}; margin-bottom: 16px;")
        layout.addWidget(desc)
        
        # Warehouses table
        # Requirements: 10.1 - Show code, name, address, is_default columns
        columns = [
            {'key': 'code', 'label': 'الرمز', 'type': 'text'},
            {'key': 'name', 'label': 'اسم المستودع', 'type': 'text'},
            {'key': 'address_display', 'label': 'العنوان', 'type': 'text'},
            {'key': 'is_default_display', 'label': 'افتراضي', 'type': 'text'},
            {'key': 'is_active_display', 'label': 'الحالة', 'type': 'text'},
        ]
        
        self.table = DataTable(columns)
        self.table.add_btn.setText("➕ إضافة مستودع")
        self.table.add_btn.clicked.disconnect()  # Disconnect default handler
        self.table.add_btn.clicked.connect(self.add_warehouse)
        self.table.action_clicked.connect(self.on_action)
        self.table.row_double_clicked.connect(self.edit_warehouse)
        self.table.page_changed.connect(self.on_page_changed)
        
        layout.addWidget(self.table)
        
    @handle_ui_error
    def refresh(self):
        """Refresh warehouses data from API."""
        # Get pagination params
        params = self.table.get_pagination_params()
        
        response = api.get_warehouses(params)
        
        # Handle paginated response
        if isinstance(response, dict) and 'results' in response:
            warehouses = response['results']
            total = response.get('count', len(warehouses))
        else:
            warehouses = response if isinstance(response, list) else []
            total = len(warehouses)
        
        # Format data for display
        for warehouse in warehouses:
            # Format address for display (truncate if too long)
            address = warehouse.get('address', '')
            if address and len(address) > 50:
                warehouse['address_display'] = address[:50] + '...'
            else:
                warehouse['address_display'] = address or '-'
            
            # Format is_default for display
            warehouse['is_default_display'] = '✓ نعم' if warehouse.get('is_default', False) else '-'
            
            # Format is_active for display
            warehouse['is_active_display'] = 'نشط' if warehouse.get('is_active', True) else 'غير نشط'
            
        self.table.set_data(warehouses, total)
    
    def on_page_changed(self, page: int, page_size: int):
        """Handle page change."""
        self.refresh()
        
    def add_warehouse(self):
        """Show add warehouse dialog."""
        dialog = WarehouseDialog("إضافة مستودع جديد", parent=self)
        dialog.saved.connect(self.save_warehouse)
        dialog.exec()
        
    def edit_warehouse(self, row: int, data: dict):
        """Show edit warehouse dialog."""
        # Convert display status back to boolean for editing
        edit_data = data.copy()
        edit_data['is_active'] = data.get('is_active_display') == 'نشط'
        edit_data['is_default'] = '✓' in data.get('is_default_display', '')
        # Use original address, not truncated display version
        edit_data['address'] = data.get('address', '')
        
        dialog = WarehouseDialog("تعديل المستودع", edit_data, parent=self)
        dialog.saved.connect(lambda d: self.update_warehouse(data.get('id'), d))
        dialog.exec()
        
    def on_action(self, action: str, row: int, data: dict):
        """Handle table action."""
        if action == 'edit':
            self.edit_warehouse(row, data)
        elif action == 'delete':
            self.delete_warehouse(data)
        elif action == 'add':
            self.add_warehouse()
            
    @handle_ui_error
    def save_warehouse(self, data: dict):
        """Save new warehouse to API."""
        create_data = {
            'code': data['code'],
            'name': data['name'],
            'is_default': data.get('is_default', False),
            'is_active': data.get('is_active', True),
        }
        
        # Only include address if provided
        if data.get('address'):
            create_data['address'] = data['address']
            
        api.create_warehouse(create_data)
        MessageDialog.success(self, "نجاح", "تم إضافة المستودع بنجاح")
        self.refresh()
        
    @handle_ui_error
    def update_warehouse(self, warehouse_id: int, data: dict):
        """Update existing warehouse via API."""
        update_data = {
            'code': data['code'],
            'name': data['name'],
            'is_default': data.get('is_default', False),
            'is_active': data.get('is_active', True),
        }
        
        # Include address (can be null)
        update_data['address'] = data.get('address') or None
            
        api.update_warehouse(warehouse_id, update_data)
        MessageDialog.success(self, "نجاح", "تم تحديث المستودع بنجاح")
        self.refresh()
        
    @handle_ui_error
    def delete_warehouse(self, data: dict):
        """
        Delete warehouse via API.
        
        Requirements: 10.4, 10.5 - Show confirmation dialog, prevent deletion if has stock
        """
        # Check if warehouse is default
        if data.get('is_default_display') == '✓ نعم':
            MessageDialog.business_error(
                self,
                "لا يمكن الحذف",
                "لا يمكن حذف المستودع الافتراضي.",
                "يجب تعيين مستودع آخر كافتراضي قبل حذف هذا المستودع."
            )
            return
        
        dialog = ConfirmDialog(
            "حذف المستودع",
            f"هل أنت متأكد من حذف المستودع '{data.get('name')}'؟",
            parent=self
        )
        if dialog.exec():
            try:
                api.delete_warehouse(data.get('id'))
                MessageDialog.success(self, "نجاح", "تم حذف المستودع بنجاح")
                self.refresh()
            except ApiException as e:
                # Handle warehouse has stock error
                if 'WAREHOUSE_HAS_STOCK' in str(e.error_code) or 'مخزون' in str(e.message):
                    MessageDialog.business_error(
                        self,
                        "لا يمكن الحذف",
                        "لا يمكن حذف هذا المستودع لأنه يحتوي على مخزون.",
                        "يجب نقل أو حذف جميع المخزون من هذا المستودع قبل حذفه."
                    )
                else:
                    raise


# Alias for backward compatibility
WarehousesManagementView = WarehousesView
