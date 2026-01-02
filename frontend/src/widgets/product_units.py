"""
Product Units Configuration Widget

Requirements: 2.1, 2.3, 2.4 - Product-unit association with conversion factors
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QDialog, QFrame, QComboBox, QLineEdit,
    QDoubleSpinBox, QCheckBox, QFormLayout, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from decimal import Decimal

from ..config import Colors, Fonts, config
from ..widgets.forms import FormField
from ..widgets.dialogs import MessageDialog, ConfirmDialog
from ..services.api import api, ApiException
from ..utils.error_handler import handle_ui_error


class ProductUnitDialog(QDialog):
    """
    Dialog for adding/editing product unit assignments.
    
    Requirements: 2.2, 2.4, 2.6 - Add/edit unit assignment with validation
    """
    
    saved = Signal(dict)
    
    def __init__(self, title: str, units: list, data: dict = None, 
                 existing_unit_ids: list = None, parent=None):
        """
        Initialize the dialog.
        
        Args:
            title: Dialog title
            units: List of available units from API
            data: Existing product unit data for editing (optional)
            existing_unit_ids: List of unit IDs already assigned to the product
            parent: Parent widget
        """
        super().__init__(parent)
        self.units = units
        self.data = data or {}
        self.is_edit = bool(data and data.get('id'))
        self.existing_unit_ids = existing_unit_ids or []
        self.setWindowTitle(title)
        self.setMinimumWidth(450)
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Form layout
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(12)
        
        # Unit selector (only for new assignments)
        if not self.is_edit:
            unit_label = QLabel("الوحدة *")
            unit_label.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_BODY))
            form_layout.addWidget(unit_label)
            
            self.unit_combo = QComboBox()
            self.unit_combo.setMinimumHeight(36)
            
            # Filter out already assigned units
            for unit in self.units:
                if unit.get('id') not in self.existing_unit_ids:
                    display_text = f"{unit.get('name')} ({unit.get('symbol')})"
                    self.unit_combo.addItem(display_text, unit.get('id'))
            
            form_layout.addWidget(self.unit_combo)
        else:
            # Show unit name as read-only for editing
            unit_label = QLabel("الوحدة")
            unit_label.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_BODY))
            form_layout.addWidget(unit_label)
            
            unit_display = QLabel(f"{self.data.get('unit_name', '')} ({self.data.get('unit_symbol', '')})")
            unit_display.setStyleSheet(f"color: {Colors.LIGHT_TEXT}; padding: 8px; background: {Colors.LIGHT_BG}; border-radius: 4px;")
            form_layout.addWidget(unit_display)
        
        # Base unit checkbox
        self.is_base_unit_field = FormField(
            label='الوحدة الأساسية',
            field_type='checkbox',
            required=False
        )
        self.is_base_unit_field.set_value(self.data.get('is_base_unit', False))
        self.is_base_unit_field.value_changed.connect(self.on_base_unit_changed)
        form_layout.addWidget(self.is_base_unit_field)
        
        # Conversion factor
        self.conversion_factor_field = FormField(
            label='معامل التحويل',
            field_type='number',
            required=True,
            placeholder='مثال: 10 (1 كروز = 10 علب)'
        )
        # Set default or existing value
        conversion_factor = self.data.get('conversion_factor', 1.0)
        if isinstance(conversion_factor, str):
            conversion_factor = float(conversion_factor)
        self.conversion_factor_field.set_value(conversion_factor)
        # Set minimum to 0.0001 and decimals to 4
        if hasattr(self.conversion_factor_field.input_widget, 'setMinimum'):
            self.conversion_factor_field.input_widget.setMinimum(0.0001)
            self.conversion_factor_field.input_widget.setDecimals(4)
        form_layout.addWidget(self.conversion_factor_field)
        
        # Sale price
        self.sale_price_field = FormField(
            label='سعر البيع (USD)',
            field_type='number',
            required=False,
            placeholder='سعر البيع لهذه الوحدة'
        )
        sale_price = self.data.get('sale_price_usd', None)
        if sale_price is None:
            sale_price = self.data.get('sale_price', 0)
            try:
                sale_price = float(config.convert_to_secondary(float(sale_price or 0)))
            except Exception:
                sale_price = 0
        if isinstance(sale_price, str):
            sale_price = float(sale_price)
        self.sale_price_field.set_value(sale_price)
        form_layout.addWidget(self.sale_price_field)
        
        # Cost price
        self.cost_price_field = FormField(
            label='سعر التكلفة (USD)',
            field_type='number',
            required=False,
            placeholder='سعر التكلفة لهذه الوحدة'
        )
        cost_price = self.data.get('cost_price_usd', None)
        if cost_price is None:
            cost_price = self.data.get('cost_price', 0)
            try:
                cost_price = float(config.convert_to_secondary(float(cost_price or 0)))
            except Exception:
                cost_price = 0
        if isinstance(cost_price, str):
            cost_price = float(cost_price)
        self.cost_price_field.set_value(cost_price)
        form_layout.addWidget(self.cost_price_field)
        
        # Barcode
        self.barcode_field = FormField(
            label='الباركود',
            field_type='text',
            required=False,
            placeholder='باركود خاص بهذه الوحدة (اختياري)'
        )
        self.barcode_field.set_value(self.data.get('barcode', '') or '')
        form_layout.addWidget(self.barcode_field)
        
        layout.addWidget(form_widget)
        layout.addStretch()
        
        # Update conversion factor state based on base unit
        self.on_base_unit_changed(self.is_base_unit_field.get_value())
        
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
    
    def on_base_unit_changed(self, is_base):
        """Handle base unit checkbox change."""
        if is_base:
            # Base unit must have conversion factor of 1
            self.conversion_factor_field.set_value(1.0)
            self.conversion_factor_field.input_widget.setEnabled(False)
        else:
            self.conversion_factor_field.input_widget.setEnabled(True)
        
    def save(self):
        """Validate and save form data."""
        # Validate conversion factor
        conversion_factor = self.conversion_factor_field.get_value()
        if conversion_factor <= 0:
            self.conversion_factor_field.set_error("معامل التحويل يجب أن يكون أكبر من صفر")
            return
        
        sale_price_usd = self.sale_price_field.get_value() or 0
        cost_price_usd = self.cost_price_field.get_value() or 0

        # Collect data
        result = {
            'conversion_factor': conversion_factor,
            'is_base_unit': self.is_base_unit_field.get_value(),
            'sale_price_usd': sale_price_usd,
            'cost_price_usd': cost_price_usd,
            'sale_price': config.convert_to_primary(float(sale_price_usd or 0), from_currency='USD'),
            'cost_price': config.convert_to_primary(float(cost_price_usd or 0), from_currency='USD'),
            'barcode': self.barcode_field.get_value() or None,
        }
        
        # Add unit ID for new assignments
        if not self.is_edit:
            unit_id = self.unit_combo.currentData()
            if not unit_id:
                MessageDialog.error(self, "خطأ", "يرجى اختيار وحدة")
                return
            result['unit'] = unit_id
        else:
            # Include existing data for editing
            result['id'] = self.data.get('id')
            result['unit'] = self.data.get('unit')
            result['unit_name'] = self.data.get('unit_name')
            result['unit_symbol'] = self.data.get('unit_symbol')
            
        self.saved.emit(result)
        self.accept()


class ProductUnitConfigWidget(QWidget):
    """
    Widget for configuring product units with conversion factors and prices.
    
    Requirements: 2.1, 2.3, 2.4 - Product-unit association management
    """
    
    # Signal emitted when product units are modified
    units_changed = Signal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.product_id = None
        self.product_units = []  # List of product unit configurations
        self.available_units = []  # List of all available units from API
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # Header with title and add button
        header = QHBoxLayout()
        
        title = QLabel("وحدات المنتج")
        title.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_H3, QFont.Bold))
        header.addWidget(title)
        
        header.addStretch()
        
        self.add_btn = QPushButton("➕ إضافة وحدة")
        self.add_btn.setMinimumHeight(36)
        self.add_btn.clicked.connect(self.add_unit)
        header.addWidget(self.add_btn)
        
        layout.addLayout(header)
        
        # Description
        desc = QLabel("تحديد الوحدات المتاحة للمنتج مع معاملات التحويل والأسعار")
        desc.setStyleSheet(f"color: {Colors.LIGHT_TEXT_SECONDARY}; font-size: 11px;")
        layout.addWidget(desc)
        
        # Units table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            'الوحدة', 'الرمز', 'معامل التحويل', 'سعر البيع (USD)', 
            'سعر التكلفة (USD)', 'أساسية', 'إجراءات'
        ])
        
        # Configure table
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setMinimumHeight(150)
        
        # Header style
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setDefaultAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        # Set column widths
        self.table.setColumnWidth(0, 120)  # Unit name
        self.table.setColumnWidth(1, 60)   # Symbol
        self.table.setColumnWidth(2, 100)  # Conversion factor
        self.table.setColumnWidth(3, 100)  # Sale price
        self.table.setColumnWidth(4, 100)  # Cost price
        self.table.setColumnWidth(5, 60)   # Is base
        
        layout.addWidget(self.table)
        
        # Info label
        self.info_label = QLabel("💡 يجب تحديد وحدة أساسية واحدة على الأقل (معامل التحويل = 1)")
        self.info_label.setStyleSheet(f"color: {Colors.INFO}; font-size: 11px; padding: 8px;")
        layout.addWidget(self.info_label)
    
    def set_product_id(self, product_id: int):
        """Set the product ID and load its units."""
        self.product_id = product_id
        self.load_product_units()
    
    def load_available_units(self):
        """Load all available units from API."""
        try:
            response = api.get('inventory/units/')
            if isinstance(response, dict) and 'results' in response:
                self.available_units = response['results']
            else:
                self.available_units = response if isinstance(response, list) else []
            # Filter to only active units
            self.available_units = [u for u in self.available_units if u.get('is_active', True)]
        except Exception as e:
            self.available_units = []
            print(f"Error loading units: {e}")
    
    @handle_ui_error
    def load_product_units(self):
        """Load product units from API."""
        if not self.product_id:
            self.product_units = []
            self.refresh_table()
            return
            
        try:
            response = api.get(f'inventory/products/{self.product_id}/units/')
            if isinstance(response, dict) and 'results' in response:
                self.product_units = response['results']
            else:
                self.product_units = response if isinstance(response, list) else []
        except Exception as e:
            self.product_units = []
            print(f"Error loading product units: {e}")
        
        self.refresh_table()
    
    def set_product_units(self, product_units: list):
        """Set product units directly (for use in product form before saving)."""
        self.product_units = product_units or []
        self.refresh_table()
    
    def get_product_units(self) -> list:
        """Get current product units configuration."""
        return self.product_units
    
    def refresh_table(self):
        """Refresh the table display."""
        self.table.setRowCount(len(self.product_units))
        
        for row, pu in enumerate(self.product_units):
            # Unit name
            unit_name = pu.get('unit_name', '')
            name_item = QTableWidgetItem(unit_name)
            name_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 0, name_item)
            
            # Symbol
            symbol = pu.get('unit_symbol', '')
            symbol_item = QTableWidgetItem(symbol)
            symbol_item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
            self.table.setItem(row, 1, symbol_item)
            
            # Conversion factor
            conversion_factor = pu.get('conversion_factor', '1')
            cf_item = QTableWidgetItem(str(conversion_factor))
            cf_item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
            self.table.setItem(row, 2, cf_item)
            
            # Sale price
            sale_price = pu.get('sale_price_usd', None)
            if sale_price is None:
                sale_price = pu.get('sale_price', '0')
                try:
                    sale_price = float(config.convert_to_secondary(float(sale_price or 0)))
                except Exception:
                    sale_price = 0
            sp_item = QTableWidgetItem(f"{float(sale_price):,.2f}")
            sp_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 3, sp_item)
            
            # Cost price
            cost_price = pu.get('cost_price_usd', None)
            if cost_price is None:
                cost_price = pu.get('cost_price', '0')
                try:
                    cost_price = float(config.convert_to_secondary(float(cost_price or 0)))
                except Exception:
                    cost_price = 0
            cp_item = QTableWidgetItem(f"{float(cost_price):,.2f}")
            cp_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 4, cp_item)
            
            # Is base unit indicator
            is_base = pu.get('is_base_unit', False)
            base_item = QTableWidgetItem("✓" if is_base else "")
            base_item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
            if is_base:
                base_item.setForeground(Qt.darkGreen)
            self.table.setItem(row, 5, base_item)
            
            # Actions column
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 4, 4, 4)
            actions_layout.setSpacing(4)
            
            edit_btn = QPushButton("✏️")
            edit_btn.setFixedSize(30, 30)
            edit_btn.setStyleSheet("border: none; background: transparent;")
            edit_btn.setToolTip("تعديل")
            edit_btn.clicked.connect(lambda _, r=row: self.edit_unit(r))
            actions_layout.addWidget(edit_btn)
            
            delete_btn = QPushButton("🗑️")
            delete_btn.setFixedSize(30, 30)
            delete_btn.setStyleSheet("border: none; background: transparent;")
            delete_btn.setToolTip("حذف")
            delete_btn.clicked.connect(lambda _, r=row: self.delete_unit(r))
            actions_layout.addWidget(delete_btn)
            
            self.table.setCellWidget(row, 6, actions_widget)
        
        # Update info label based on base unit status
        has_base_unit = any(pu.get('is_base_unit', False) for pu in self.product_units)
        if not has_base_unit and len(self.product_units) > 0:
            self.info_label.setText("⚠️ تحذير: لم يتم تحديد وحدة أساسية!")
            self.info_label.setStyleSheet(f"color: {Colors.WARNING}; font-size: 11px; padding: 8px;")
        else:
            self.info_label.setText("💡 يجب تحديد وحدة أساسية واحدة على الأقل (معامل التحويل = 1)")
            self.info_label.setStyleSheet(f"color: {Colors.INFO}; font-size: 11px; padding: 8px;")
    
    def add_unit(self):
        """Show dialog to add a new unit assignment."""
        # Load available units if not loaded
        if not self.available_units:
            self.load_available_units()
        
        # Get IDs of already assigned units
        existing_unit_ids = [pu.get('unit') or pu.get('unit_id') for pu in self.product_units]
        
        # Check if there are any units left to add
        available_to_add = [u for u in self.available_units if u.get('id') not in existing_unit_ids]
        if not available_to_add:
            MessageDialog.warning(self, "تنبيه", "تم إضافة جميع الوحدات المتاحة لهذا المنتج")
            return
        
        # Determine if this should be base unit (first unit added)
        is_first_unit = len(self.product_units) == 0
        default_data = {'is_base_unit': is_first_unit, 'conversion_factor': 1.0} if is_first_unit else {}
        
        dialog = ProductUnitDialog(
            "إضافة وحدة للمنتج",
            self.available_units,
            data=default_data,
            existing_unit_ids=existing_unit_ids,
            parent=self
        )
        dialog.saved.connect(self.save_new_unit)
        dialog.exec()
    
    def save_new_unit(self, data: dict):
        """Save a new unit assignment."""
        # Find unit details
        unit_id = data.get('unit')
        unit_info = next((u for u in self.available_units if u.get('id') == unit_id), None)
        
        if unit_info:
            # If this is set as base unit, unset any existing base unit
            if data.get('is_base_unit'):
                for pu in self.product_units:
                    pu['is_base_unit'] = False
            
            # Create new product unit entry
            new_pu = {
                'unit': unit_id,
                'unit_id': unit_id,
                'unit_name': unit_info.get('name'),
                'unit_symbol': unit_info.get('symbol'),
                'conversion_factor': str(data.get('conversion_factor', 1)),
                'is_base_unit': data.get('is_base_unit', False),
                'sale_price_usd': str(data.get('sale_price_usd', 0)),
                'cost_price_usd': str(data.get('cost_price_usd', 0)),
                'sale_price': str(data.get('sale_price', 0)),
                'cost_price': str(data.get('cost_price', 0)),
                'barcode': data.get('barcode'),
                'is_new': True  # Mark as new for saving
            }
            
            self.product_units.append(new_pu)
            self.refresh_table()
            self.units_changed.emit(self.product_units)
    
    def edit_unit(self, row: int):
        """Show dialog to edit a unit assignment."""
        if row < 0 or row >= len(self.product_units):
            return
            
        pu_data = self.product_units[row]
        
        dialog = ProductUnitDialog(
            "تعديل وحدة المنتج",
            self.available_units,
            data=pu_data,
            parent=self
        )
        dialog.saved.connect(lambda d: self.update_unit(row, d))
        dialog.exec()
    
    def update_unit(self, row: int, data: dict):
        """Update an existing unit assignment."""
        if row < 0 or row >= len(self.product_units):
            return
        
        # If this is set as base unit, unset any existing base unit
        if data.get('is_base_unit'):
            for i, pu in enumerate(self.product_units):
                if i != row:
                    pu['is_base_unit'] = False
        
        # Update the product unit
        self.product_units[row].update({
            'conversion_factor': str(data.get('conversion_factor', 1)),
            'is_base_unit': data.get('is_base_unit', False),
            'sale_price_usd': str(data.get('sale_price_usd', 0)),
            'cost_price_usd': str(data.get('cost_price_usd', 0)),
            'sale_price': str(data.get('sale_price', 0)),
            'cost_price': str(data.get('cost_price', 0)),
            'barcode': data.get('barcode'),
            'is_modified': True  # Mark as modified for saving
        })
        
        self.refresh_table()
        self.units_changed.emit(self.product_units)
    
    def delete_unit(self, row: int):
        """Delete a unit assignment."""
        if row < 0 or row >= len(self.product_units):
            return
            
        pu_data = self.product_units[row]
        
        # Check if this is the base unit
        if pu_data.get('is_base_unit'):
            MessageDialog.warning(
                self, 
                "لا يمكن الحذف", 
                "لا يمكن حذف الوحدة الأساسية. يرجى تعيين وحدة أخرى كوحدة أساسية أولاً."
            )
            return
        
        # Confirm deletion
        dialog = ConfirmDialog(
            "حذف الوحدة",
            f"هل أنت متأكد من حذف الوحدة '{pu_data.get('unit_name')}'؟",
            parent=self
        )
        
        if dialog.exec():
            # Mark for deletion if it has an ID (exists in database)
            if pu_data.get('id'):
                pu_data['is_deleted'] = True
                # Keep in list but mark as deleted for API call
            else:
                # Remove from list if it's a new unsaved unit
                self.product_units.pop(row)
            
            self.refresh_table()
            self.units_changed.emit(self.product_units)
    
    def validate(self) -> bool:
        """
        Validate the product units configuration.
        
        Returns:
            True if valid, False otherwise
        """
        # Filter out deleted units
        active_units = [pu for pu in self.product_units if not pu.get('is_deleted')]
        
        if not active_units:
            # No units is valid - product will use default unit
            return True
        
        # Check for exactly one base unit
        base_units = [pu for pu in active_units if pu.get('is_base_unit')]
        if len(base_units) == 0:
            MessageDialog.warning(
                self,
                "خطأ في التحقق",
                "يجب تحديد وحدة أساسية واحدة على الأقل"
            )
            return False
        
        if len(base_units) > 1:
            MessageDialog.warning(
                self,
                "خطأ في التحقق",
                "يجب أن تكون هناك وحدة أساسية واحدة فقط"
            )
            return False
        
        # Check conversion factors are positive
        for pu in active_units:
            cf = float(pu.get('conversion_factor', 0))
            if cf <= 0:
                MessageDialog.warning(
                    self,
                    "خطأ في التحقق",
                    f"معامل التحويل للوحدة '{pu.get('unit_name')}' يجب أن يكون أكبر من صفر"
                )
                return False
        
        return True
    
    def clear(self):
        """Clear all product units."""
        self.product_id = None
        self.product_units = []
        self.refresh_table()
