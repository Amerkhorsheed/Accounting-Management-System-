"""
Units Management View - Settings Page for Unit Management

Requirements: 6.1, 6.2, 6.3, 6.4, 6.5 - Unit management interface
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


class UnitDialog(QDialog):
    """
    Dialog for creating/editing units.
    
    Requirements: 6.3, 6.4, 6.5 - Add/edit dialog with validation and Arabic support
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
        
        # Name field (Arabic) - Required
        self.name_field = FormField(
            label='اسم الوحدة',
            field_type='text',
            required=True,
            placeholder='مثال: كروز، علبة، قطعة'
        )
        if 'name' in self.data:
            self.name_field.set_value(self.data['name'])
        form_layout.addWidget(self.name_field)
        
        # Symbol field - Required
        self.symbol_field = FormField(
            label='الرمز',
            field_type='text',
            required=True,
            placeholder='مثال: كروز، علبة، قطعة'
        )
        if 'symbol' in self.data:
            self.symbol_field.set_value(self.data['symbol'])
        form_layout.addWidget(self.symbol_field)
        
        # English name field - Optional
        self.name_en_field = FormField(
            label='الاسم بالإنجليزية',
            field_type='text',
            required=False,
            placeholder='مثال: carton, pack, piece'
        )
        if 'name_en' in self.data:
            self.name_en_field.set_value(self.data['name_en'] or '')
        form_layout.addWidget(self.name_en_field)
        
        # Active checkbox
        self.is_active_field = FormField(
            label='نشط',
            field_type='checkbox',
            required=False
        )
        # Default to active for new units
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
        if not self.symbol_field.validate():
            is_valid = False
            
        if not is_valid:
            return
            
        # Collect data
        result = {
            'name': self.name_field.get_value(),
            'symbol': self.symbol_field.get_value(),
            'name_en': self.name_en_field.get_value() or None,
            'is_active': self.is_active_field.get_value(),
        }
        
        # Include ID if editing
        if self.is_edit:
            result['id'] = self.data.get('id')
            
        self.saved.emit(result)
        self.accept()


class UnitsManagementView(QWidget):
    """
    Units management view for settings.
    
    Requirements: 6.1, 6.2 - Settings page with table display
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize units management view UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header = QHBoxLayout()
        
        title = QLabel("إدارة وحدات القياس")
        title.setProperty("class", "title")
        title.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_H2, QFont.Bold))
        header.addWidget(title)
        
        header.addStretch()
        
        layout.addLayout(header)
        
        # Description
        desc = QLabel("إدارة وحدات القياس المستخدمة في المنتجات (كروز، علبة، قطعة، كيلو، كف، باكيت)")
        desc.setProperty("class", "subtitle")
        desc.setStyleSheet(f"color: {Colors.LIGHT_TEXT_SECONDARY}; margin-bottom: 16px;")
        layout.addWidget(desc)
        
        # Units table
        columns = [
            {'key': 'name', 'label': 'اسم الوحدة', 'type': 'text'},
            {'key': 'symbol', 'label': 'الرمز', 'type': 'text'},
            {'key': 'name_en', 'label': 'الاسم بالإنجليزية', 'type': 'text'},
            {'key': 'is_active', 'label': 'الحالة', 'type': 'status'},
        ]
        
        self.table = DataTable(columns)
        self.table.add_btn.setText("➕ إضافة وحدة")
        self.table.add_btn.clicked.disconnect()  # Disconnect default handler
        self.table.add_btn.clicked.connect(self.add_unit)
        self.table.action_clicked.connect(self.on_action)
        self.table.row_double_clicked.connect(self.edit_unit)
        
        layout.addWidget(self.table)
        
    @handle_ui_error
    def refresh(self):
        """Refresh units data from API."""
        response = api.get('inventory/units/')
        
        # Handle paginated response
        if isinstance(response, dict) and 'results' in response:
            units = response['results']
            total = response.get('count', len(units))
        else:
            units = response if isinstance(response, list) else []
            total = len(units)
        
        # Format is_active for display
        for unit in units:
            unit['is_active'] = 'نشط' if unit.get('is_active', True) else 'غير نشط'
            
        self.table.set_data(units, total)
        
    def add_unit(self):
        """Show add unit dialog."""
        dialog = UnitDialog("إضافة وحدة جديدة", parent=self)
        dialog.saved.connect(self.save_unit)
        dialog.exec()
        
    def edit_unit(self, row: int, data: dict):
        """Show edit unit dialog."""
        # Convert display status back to boolean for editing
        edit_data = data.copy()
        edit_data['is_active'] = data.get('is_active') == 'نشط'
        
        dialog = UnitDialog("تعديل الوحدة", edit_data, parent=self)
        dialog.saved.connect(lambda d: self.update_unit(data.get('id'), d))
        dialog.exec()
        
    def on_action(self, action: str, row: int, data: dict):
        """Handle table action."""
        if action == 'edit':
            self.edit_unit(row, data)
        elif action == 'delete':
            self.delete_unit(data)
        elif action == 'add':
            self.add_unit()
            
    @handle_ui_error
    def save_unit(self, data: dict):
        """Save new unit to API."""
        create_data = {
            'name': data['name'],
            'symbol': data['symbol'],
            'is_active': data.get('is_active', True),
        }
        
        # Only include name_en if provided
        if data.get('name_en'):
            create_data['name_en'] = data['name_en']
            
        api.post('inventory/units/', create_data)
        MessageDialog.success(self, "نجاح", "تم إضافة الوحدة بنجاح")
        self.refresh()
        
    @handle_ui_error
    def update_unit(self, unit_id: int, data: dict):
        """Update existing unit via API."""
        update_data = {
            'name': data['name'],
            'symbol': data['symbol'],
            'is_active': data.get('is_active', True),
        }
        
        # Include name_en (can be null)
        update_data['name_en'] = data.get('name_en') or None
            
        api.patch(f'inventory/units/{unit_id}/', update_data)
        MessageDialog.success(self, "نجاح", "تم تحديث الوحدة بنجاح")
        self.refresh()
        
    @handle_ui_error
    def delete_unit(self, data: dict):
        """Delete unit via API."""
        dialog = ConfirmDialog(
            "حذف الوحدة",
            f"هل أنت متأكد من حذف الوحدة '{data.get('name')}'؟\n\nلا يمكن حذف الوحدات المستخدمة في المنتجات.",
            parent=self
        )
        if dialog.exec():
            try:
                api.delete(f'inventory/units/{data.get("id")}/')
                MessageDialog.success(self, "نجاح", "تم حذف الوحدة بنجاح")
                self.refresh()
            except ApiException as e:
                # Handle unit in use error
                if 'UNIT_IN_USE' in str(e.error_code) or 'مستخدمة' in str(e.message):
                    MessageDialog.business_error(
                        self,
                        "لا يمكن الحذف",
                        "لا يمكن حذف هذه الوحدة لأنها مستخدمة في منتجات.",
                        "يجب إزالة الوحدة من جميع المنتجات قبل حذفها."
                    )
                else:
                    raise
