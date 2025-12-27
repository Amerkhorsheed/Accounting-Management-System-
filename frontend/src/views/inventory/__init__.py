"""
Inventory Views - Products Management

Requirements: 4.1, 4.2 - Error handling for CRUD operations and form submissions
Requirements: 2.1 - Product-unit association management
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QFrame, QDialog,
    QScrollArea, QTabWidget, QComboBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from ...config import Colors, Fonts
from ...widgets.tables import DataTable
from ...widgets.forms import FormField, FormDialog
from ...widgets.dialogs import MessageDialog, ConfirmDialog
from ...widgets.product_units import ProductUnitConfigWidget
from ...services.api import api, ApiException
from ...utils.error_handler import handle_ui_error


class ProductDialog(QDialog):
    """
    Enhanced product dialog with tabs for basic info and unit configuration.
    
    Requirements: 2.1 - Product-unit association management
    """
    
    saved = Signal(dict, list)  # Emits (product_data, product_units)
    
    def __init__(self, title: str, categories: list, data: dict = None, parent=None):
        super().__init__(parent)
        self.categories = categories
        self.data = data or {}
        self.is_edit = bool(data and data.get('id'))
        self.setWindowTitle(title)
        self.setMinimumWidth(600)
        self.setMinimumHeight(550)
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Tab widget for organizing content
        self.tabs = QTabWidget()
        
        # Basic Info Tab
        basic_tab = QWidget()
        basic_layout = QVBoxLayout(basic_tab)
        basic_layout.setContentsMargins(16, 16, 16, 16)
        
        # Scroll area for basic fields
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(12)
        
        # Name field
        self.name_field = FormField(
            label='اسم المنتج',
            field_type='text',
            required=True
        )
        if 'name' in self.data:
            self.name_field.set_value(self.data['name'])
        form_layout.addWidget(self.name_field)
        
        # English name field
        self.name_en_field = FormField(
            label='الاسم بالإنجليزية',
            field_type='text',
            required=False
        )
        if 'name_en' in self.data:
            self.name_en_field.set_value(self.data['name_en'] or '')
        form_layout.addWidget(self.name_en_field)
        
        # Code field
        self.code_field = FormField(
            label='كود المنتج',
            field_type='text',
            required=False,
            placeholder='سيتم إنشاؤه تلقائياً إذا تُرك فارغاً'
        )
        if 'code' in self.data:
            self.code_field.set_value(self.data['code'] or '')
        form_layout.addWidget(self.code_field)
        
        # Barcode field
        self.barcode_field = FormField(
            label='الباركود',
            field_type='text',
            required=False
        )
        if 'barcode' in self.data:
            self.barcode_field.set_value(self.data['barcode'] or '')
        form_layout.addWidget(self.barcode_field)
        
        # Category field
        category_options = [{'value': c['id'], 'label': c['name']} for c in self.categories]
        self.category_field = FormField(
            label='الفئة',
            field_type='select',
            required=False,
            options=category_options
        )
        if 'category' in self.data:
            self.category_field.set_value(self.data['category'])
        form_layout.addWidget(self.category_field)
        
        # Cost price field
        self.cost_price_field = FormField(
            label='سعر التكلفة',
            field_type='number',
            required=True
        )
        if 'cost_price' in self.data:
            self.cost_price_field.set_value(float(self.data['cost_price'] or 0))
        form_layout.addWidget(self.cost_price_field)
        
        # Sale price field
        self.sale_price_field = FormField(
            label='سعر البيع',
            field_type='number',
            required=True
        )
        if 'sale_price' in self.data:
            self.sale_price_field.set_value(float(self.data['sale_price'] or 0))
        form_layout.addWidget(self.sale_price_field)
        
        # Minimum stock field
        self.minimum_stock_field = FormField(
            label='الحد الأدنى للمخزون',
            field_type='number',
            required=False
        )
        if 'minimum_stock' in self.data:
            self.minimum_stock_field.set_value(float(self.data['minimum_stock'] or 0))
        form_layout.addWidget(self.minimum_stock_field)
        
        # Tax settings section
        tax_section_label = QLabel("إعدادات الضريبة")
        tax_section_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 10px;")
        form_layout.addWidget(tax_section_label)
        
        # Is taxable checkbox
        self.is_taxable_field = FormField(
            label='خاضع للضريبة',
            field_type='checkbox',
            required=False
        )
        # Default to False (not taxable) for new products
        is_taxable = self.data.get('is_taxable', False) if self.data else False
        self.is_taxable_field.set_value(is_taxable)
        self.is_taxable_field.input_widget.stateChanged.connect(self.on_taxable_changed)
        form_layout.addWidget(self.is_taxable_field)
        
        # Tax rate field
        self.tax_rate_field = FormField(
            label='نسبة الضريبة (%)',
            field_type='number',
            required=False
        )
        tax_rate = float(self.data.get('tax_rate', 15) or 15) if self.data else 15
        self.tax_rate_field.set_value(tax_rate)
        # Initially hide/disable if not taxable
        self.tax_rate_field.setEnabled(is_taxable)
        form_layout.addWidget(self.tax_rate_field)
        
        # Description field
        self.description_field = FormField(
            label='الوصف',
            field_type='textarea',
            required=False
        )
        if 'description' in self.data:
            self.description_field.set_value(self.data['description'] or '')
        form_layout.addWidget(self.description_field)
        
        form_layout.addStretch()
        scroll.setWidget(form_widget)
        basic_layout.addWidget(scroll)
        
        self.tabs.addTab(basic_tab, "المعلومات الأساسية")
        
        # Units Tab
        units_tab = QWidget()
        units_layout = QVBoxLayout(units_tab)
        units_layout.setContentsMargins(16, 16, 16, 16)
        
        self.product_units_widget = ProductUnitConfigWidget()
        
        # Load existing product units if editing
        if self.is_edit and 'product_units' in self.data:
            self.product_units_widget.set_product_units(self.data['product_units'])
        
        # Load available units
        self.product_units_widget.load_available_units()
        
        units_layout.addWidget(self.product_units_widget)
        
        self.tabs.addTab(units_tab, "وحدات المنتج")
        
        layout.addWidget(self.tabs)
        
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
    
    def on_taxable_changed(self, state):
        """Enable/disable tax rate field based on is_taxable checkbox."""
        is_taxable = state == 2  # Qt.Checked = 2
        self.tax_rate_field.setEnabled(is_taxable)
        if not is_taxable:
            self.tax_rate_field.set_value(0)
    
    def save(self):
        """Validate and save form data."""
        # Validate basic fields
        is_valid = True
        
        if not self.name_field.validate():
            is_valid = False
            self.tabs.setCurrentIndex(0)  # Switch to basic tab
        if not self.cost_price_field.validate():
            is_valid = False
            self.tabs.setCurrentIndex(0)
        if not self.sale_price_field.validate():
            is_valid = False
            self.tabs.setCurrentIndex(0)
        
        if not is_valid:
            return
        
        # Validate product units
        if not self.product_units_widget.validate():
            self.tabs.setCurrentIndex(1)  # Switch to units tab
            return
        
        # Collect product data
        is_taxable = self.is_taxable_field.get_value()
        product_data = {
            'name': self.name_field.get_value(),
            'name_en': self.name_en_field.get_value() or None,
            'code': self.code_field.get_value() or None,
            'barcode': self.barcode_field.get_value() or None,
            'category': self.category_field.get_value(),
            'cost_price': self.cost_price_field.get_value(),
            'sale_price': self.sale_price_field.get_value(),
            'minimum_stock': self.minimum_stock_field.get_value() or 0,
            'description': self.description_field.get_value() or None,
            'is_taxable': is_taxable,
            'tax_rate': self.tax_rate_field.get_value() if is_taxable else 0,
        }
        
        # Include ID if editing
        if self.is_edit:
            product_data['id'] = self.data.get('id')
        
        # Get product units
        product_units = self.product_units_widget.get_product_units()
        
        self.saved.emit(product_data, product_units)
        self.accept()


class ProductsView(QWidget):
    """
    Products management view.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.categories = []
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize products view UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header = QHBoxLayout()
        
        title = QLabel("إدارة المنتجات")
        title.setProperty("class", "title")
        header.addWidget(title)
        
        header.addStretch()
        
        # Barcode search
        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("🔍 البحث بالباركود...")
        self.barcode_input.setFixedWidth(200)
        self.barcode_input.returnPressed.connect(self.search_by_barcode)
        header.addWidget(self.barcode_input)
        
        layout.addLayout(header)
        
        # Products table
        columns = [
            {'key': 'code', 'label': 'الكود', 'type': 'text'},
            {'key': 'barcode', 'label': 'الباركود', 'type': 'text'},
            {'key': 'name', 'label': 'اسم المنتج', 'type': 'text'},
            {'key': 'category_name', 'label': 'الفئة', 'type': 'text'},
            {'key': 'cost_price', 'label': 'سعر التكلفة', 'type': 'currency'},
            {'key': 'sale_price', 'label': 'سعر البيع', 'type': 'currency'},
            {'key': 'total_stock', 'label': 'المخزون', 'type': 'stock'},
        ]
        
        self.table = DataTable(columns)
        self.table.add_btn.clicked.connect(self.add_product)
        self.table.action_clicked.connect(self.on_action)
        self.table.row_double_clicked.connect(self.edit_product)
        
        layout.addWidget(self.table)
        
    @handle_ui_error
    def refresh(self):
        """Refresh products data from API."""
        response = api.get_products()
        # Handle paginated response
        if isinstance(response, dict) and 'results' in response:
            products = response['results']
        else:
            products = response if isinstance(response, list) else []
        self.table.set_data(products)
        
        # Also load categories for the form
        self.load_categories()
    
    @handle_ui_error
    def load_categories(self):
        """Load categories for product form."""
        response = api.get_categories()
        if isinstance(response, dict) and 'results' in response:
            self.categories = response['results']
        else:
            self.categories = response if isinstance(response, list) else []
        
    @handle_ui_error
    def search_by_barcode(self):
        """Search product by barcode."""
        barcode = self.barcode_input.text().strip()
        if barcode:
            product = api.get_product_by_barcode(barcode)
            if product:
                self.table.set_data([product])
                self.barcode_input.clear()
            
    def add_product(self):
        """Show add product dialog."""
        dialog = ProductDialog("إضافة منتج جديد", self.categories, parent=self)
        dialog.saved.connect(self.save_product_with_units)
        dialog.exec()
        
    def edit_product(self, row: int, data: dict):
        """Show edit product dialog."""
        # Load full product details including product_units
        try:
            product_detail = api.get_product(data.get('id'))
        except Exception:
            product_detail = data
        
        dialog = ProductDialog("تعديل المنتج", self.categories, product_detail, parent=self)
        dialog.saved.connect(lambda d, u: self.update_product_with_units(data.get('id'), d, u))
        dialog.exec()
        
    def on_action(self, action: str, row: int, data: dict):
        """Handle table action."""
        if action == 'edit':
            self.edit_product(row, data)
        elif action == 'delete':
            self.delete_product(data)
            
    @handle_ui_error
    def save_product(self, data: dict):
        """Save new product to API."""
        # Only send valid fields
        valid_fields = [
            'name', 'name_en', 'code', 'barcode', 'category', 'unit',
            'cost_price', 'sale_price', 'minimum_stock', 'description',
            'wholesale_price', 'minimum_price', 'is_taxable', 'tax_rate',
            'track_stock', 'maximum_stock', 'reorder_point', 'brand',
            'model', 'notes', 'is_active', 'product_type'
        ]
        create_data = {}
        for k, v in data.items():
            if k in valid_fields:
                # Skip empty optional fields
                if v == '' and k not in ['name']:
                    continue
                if v is None:
                    continue
                # Convert string numbers to proper types
                if k in ['cost_price', 'sale_price', 'minimum_stock', 'wholesale_price', 
                         'minimum_price', 'tax_rate', 'maximum_stock', 'reorder_point']:
                    if v is not None and v != '':
                        try:
                            create_data[k] = float(v)
                        except (ValueError, TypeError):
                            pass
                elif k in ['category', 'unit']:
                    if v is not None and v != '':
                        try:
                            create_data[k] = int(v)
                        except (ValueError, TypeError):
                            pass
                elif k in ['is_taxable', 'track_stock', 'is_active']:
                    create_data[k] = bool(v)
                else:
                    create_data[k] = v
        
        api.create_product(create_data)
        MessageDialog.success(self, "نجاح", "تم إضافة المنتج بنجاح")
        self.refresh()
    
    @handle_ui_error
    def save_product_with_units(self, data: dict, product_units: list):
        """Save new product with units to API."""
        # Prepare product data
        valid_fields = [
            'name', 'name_en', 'code', 'barcode', 'category', 'unit',
            'cost_price', 'sale_price', 'minimum_stock', 'description',
            'wholesale_price', 'minimum_price', 'is_taxable', 'tax_rate',
            'track_stock', 'maximum_stock', 'reorder_point', 'brand',
            'model', 'notes', 'is_active', 'product_type'
        ]
        create_data = {}
        for k, v in data.items():
            if k in valid_fields:
                if v == '' and k not in ['name']:
                    continue
                if v is None:
                    continue
                if k in ['cost_price', 'sale_price', 'minimum_stock', 'wholesale_price', 
                         'minimum_price', 'tax_rate', 'maximum_stock', 'reorder_point']:
                    if v is not None and v != '':
                        try:
                            create_data[k] = float(v)
                        except (ValueError, TypeError):
                            pass
                elif k in ['category', 'unit']:
                    if v is not None and v != '':
                        try:
                            create_data[k] = int(v)
                        except (ValueError, TypeError):
                            pass
                elif k in ['is_taxable', 'track_stock', 'is_active']:
                    create_data[k] = bool(v)
                else:
                    create_data[k] = v
        
        # Create product first
        product = api.create_product(create_data)
        product_id = product.get('id')
        
        # Create product units
        if product_id and product_units:
            for pu in product_units:
                if pu.get('is_deleted'):
                    continue
                unit_data = {
                    'product': product_id,
                    'unit': pu.get('unit') or pu.get('unit_id'),
                    'conversion_factor': float(pu.get('conversion_factor', 1)),
                    'is_base_unit': pu.get('is_base_unit', False),
                    'sale_price': float(pu.get('sale_price', 0)),
                    'cost_price': float(pu.get('cost_price', 0)),
                    'barcode': pu.get('barcode'),
                }
                try:
                    api.post(f'inventory/products/{product_id}/units/', unit_data)
                except Exception as e:
                    print(f"Error creating product unit: {e}")
        
        MessageDialog.success(self, "نجاح", "تم إضافة المنتج بنجاح")
        self.refresh()
        
    @handle_ui_error
    def update_product(self, product_id: int, data: dict):
        """Update existing product via API."""
        # Only send editable fields, remove read-only fields
        editable_fields = [
            'name', 'name_en', 'code', 'barcode', 'category', 'unit',
            'cost_price', 'sale_price', 'minimum_stock', 'description',
            'wholesale_price', 'minimum_price', 'is_taxable', 'tax_rate',
            'track_stock', 'maximum_stock', 'reorder_point', 'brand',
            'model', 'notes', 'is_active', 'product_type'
        ]
        update_data = {}
        for k, v in data.items():
            if k in editable_fields:
                # Skip empty optional fields
                if v == '' and k not in ['name']:
                    continue
                # Convert string numbers to proper types
                if k in ['cost_price', 'sale_price', 'minimum_stock', 'wholesale_price', 
                         'minimum_price', 'tax_rate', 'maximum_stock', 'reorder_point']:
                    if v is not None and v != '':
                        try:
                            update_data[k] = float(v)
                        except (ValueError, TypeError):
                            pass
                elif k in ['category', 'unit']:
                    if v is not None and v != '':
                        try:
                            update_data[k] = int(v)
                        except (ValueError, TypeError):
                            pass
                elif k in ['is_taxable', 'track_stock', 'is_active']:
                    update_data[k] = bool(v)
                else:
                    # For string fields, only include if not empty
                    if v is not None:
                        update_data[k] = v
        
        api.update_product(product_id, update_data)
        MessageDialog.success(self, "نجاح", "تم تحديث المنتج بنجاح")
        self.refresh()
    
    @handle_ui_error
    def update_product_with_units(self, product_id: int, data: dict, product_units: list):
        """Update existing product with units via API."""
        # Update product data
        editable_fields = [
            'name', 'name_en', 'code', 'barcode', 'category', 'unit',
            'cost_price', 'sale_price', 'minimum_stock', 'description',
            'wholesale_price', 'minimum_price', 'is_taxable', 'tax_rate',
            'track_stock', 'maximum_stock', 'reorder_point', 'brand',
            'model', 'notes', 'is_active', 'product_type'
        ]
        update_data = {}
        for k, v in data.items():
            if k in editable_fields:
                if v == '' and k not in ['name']:
                    continue
                if k in ['cost_price', 'sale_price', 'minimum_stock', 'wholesale_price', 
                         'minimum_price', 'tax_rate', 'maximum_stock', 'reorder_point']:
                    if v is not None and v != '':
                        try:
                            update_data[k] = float(v)
                        except (ValueError, TypeError):
                            pass
                elif k in ['category', 'unit']:
                    if v is not None and v != '':
                        try:
                            update_data[k] = int(v)
                        except (ValueError, TypeError):
                            pass
                elif k in ['is_taxable', 'track_stock', 'is_active']:
                    update_data[k] = bool(v)
                else:
                    if v is not None:
                        update_data[k] = v
        
        api.update_product(product_id, update_data)
        
        # Handle product units
        if product_units:
            for pu in product_units:
                unit_id = pu.get('unit') or pu.get('unit_id')
                pu_id = pu.get('id')
                
                if pu.get('is_deleted') and pu_id:
                    # Delete existing product unit
                    try:
                        api.delete(f'inventory/products/{product_id}/units/{pu_id}/')
                    except Exception as e:
                        print(f"Error deleting product unit: {e}")
                elif pu.get('is_new'):
                    # Create new product unit
                    unit_data = {
                        'product': product_id,
                        'unit': unit_id,
                        'conversion_factor': float(pu.get('conversion_factor', 1)),
                        'is_base_unit': pu.get('is_base_unit', False),
                        'sale_price': float(pu.get('sale_price', 0)),
                        'cost_price': float(pu.get('cost_price', 0)),
                        'barcode': pu.get('barcode'),
                    }
                    try:
                        api.post(f'inventory/products/{product_id}/units/', unit_data)
                    except Exception as e:
                        print(f"Error creating product unit: {e}")
                elif pu.get('is_modified') and pu_id:
                    # Update existing product unit
                    unit_data = {
                        'conversion_factor': float(pu.get('conversion_factor', 1)),
                        'is_base_unit': pu.get('is_base_unit', False),
                        'sale_price': float(pu.get('sale_price', 0)),
                        'cost_price': float(pu.get('cost_price', 0)),
                        'barcode': pu.get('barcode'),
                    }
                    try:
                        api.patch(f'inventory/products/{product_id}/units/{pu_id}/', unit_data)
                    except Exception as e:
                        print(f"Error updating product unit: {e}")
        
        MessageDialog.success(self, "نجاح", "تم تحديث المنتج بنجاح")
        self.refresh()
        
    @handle_ui_error
    def delete_product(self, data: dict):
        """Delete product via API."""
        dialog = ConfirmDialog(
            "حذف المنتج",
            f"هل أنت متأكد من حذف المنتج '{data.get('name')}'؟",
            parent=self
        )
        if dialog.exec():
            api.delete_product(data.get('id'))
            MessageDialog.success(self, "نجاح", "تم حذف المنتج بنجاح")
            self.refresh()
