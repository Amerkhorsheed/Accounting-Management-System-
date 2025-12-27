"""
Purchases Views - Suppliers and Purchase Orders

Requirements: 4.1, 4.2 - Error handling for CRUD operations and form submissions
Requirements: 3.1, 3.2, 3.3, 3.4 - Purchase order creation and management
Requirements: 4.1, 4.2, 4.3 - Unit selection in purchases
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QDialog, QComboBox, QDateEdit, QTextEdit,
    QDoubleSpinBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QGridLayout, QFrame,
    QAbstractItemView, QLineEdit
)
from PySide6.QtCore import Qt, Signal, QDate, QEvent
from PySide6.QtGui import QFont

from ...config import Colors, Fonts
from ...widgets.tables import DataTable
from ...widgets.forms import FormDialog
from ...widgets.dialogs import MessageDialog, ConfirmDialog
from ...widgets.cards import Card
from ...widgets.unit_selector import UnitSelectorComboBox
from ...services.api import api, ApiException
from ...utils.error_handler import handle_ui_error


class SuppliersView(QWidget):
    """Suppliers management view."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        title = QLabel("إدارة الموردين")
        title.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_H2, QFont.Bold))
        layout.addWidget(title)
        
        columns = [
            {'key': 'code', 'label': 'الكود'},
            {'key': 'name', 'label': 'اسم المورد'},
            {'key': 'phone', 'label': 'الهاتف'},
            {'key': 'mobile', 'label': 'الجوال'},
            {'key': 'current_balance', 'label': 'الرصيد', 'type': 'currency'},
        ]
        
        self.table = DataTable(columns)
        self.table.add_btn.clicked.connect(self.add_supplier)
        self.table.action_clicked.connect(self.on_action)
        self.table.row_double_clicked.connect(self.edit_supplier)
        layout.addWidget(self.table)

    @handle_ui_error
    def refresh(self):
        """Refresh suppliers data from API."""
        response = api.get_suppliers()
        if isinstance(response, dict) and 'results' in response:
            suppliers = response['results']
        else:
            suppliers = response if isinstance(response, list) else []
        self.table.set_data(suppliers)
        
    def add_supplier(self):
        fields = [
            {'key': 'name', 'label': 'اسم المورد', 'required': True},
            {'key': 'name_en', 'label': 'الاسم بالإنجليزية'},
            {'key': 'phone', 'label': 'رقم الهاتف'},
            {'key': 'mobile', 'label': 'رقم الجوال'},
            {'key': 'email', 'label': 'البريد الإلكتروني'},
            {'key': 'address', 'label': 'العنوان', 'type': 'textarea'},
            {'key': 'tax_number', 'label': 'الرقم الضريبي'},
            {'key': 'credit_limit', 'label': 'حد الائتمان', 'type': 'number'},
            {'key': 'payment_terms', 'label': 'شروط الدفع (أيام)', 'type': 'number'},
        ]
        dialog = FormDialog("إضافة مورد جديد", fields, parent=self)
        dialog.saved.connect(self.save_supplier)
        dialog.exec()
    
    def edit_supplier(self, row: int, data: dict):
        """Edit existing supplier."""
        fields = [
            {'key': 'name', 'label': 'اسم المورد', 'required': True},
            {'key': 'name_en', 'label': 'الاسم بالإنجليزية'},
            {'key': 'phone', 'label': 'رقم الهاتف'},
            {'key': 'mobile', 'label': 'رقم الجوال'},
            {'key': 'email', 'label': 'البريد الإلكتروني'},
            {'key': 'address', 'label': 'العنوان', 'type': 'textarea'},
            {'key': 'tax_number', 'label': 'الرقم الضريبي'},
            {'key': 'credit_limit', 'label': 'حد الائتمان', 'type': 'number'},
            {'key': 'payment_terms', 'label': 'شروط الدفع (أيام)', 'type': 'number'},
        ]
        dialog = FormDialog("تعديل المورد", fields, data, parent=self)
        dialog.saved.connect(lambda d: self.update_supplier(data.get('id'), d))
        dialog.exec()
    
    @handle_ui_error
    def save_supplier(self, data: dict):
        """Save supplier to API."""
        valid_fields = [
            'name', 'name_en', 'phone', 'mobile', 'email', 'fax', 'website',
            'address', 'city', 'region', 'postal_code', 'country',
            'tax_number', 'commercial_register', 'contact_person',
            'credit_limit', 'payment_terms', 'opening_balance',
            'notes', 'is_active'
        ]
        create_data = {k: v for k, v in data.items() if k in valid_fields and v is not None and v != ''}
        
        api.create_supplier(create_data)
        MessageDialog.success(self, "نجاح", "تم إضافة المورد بنجاح")
        self.refresh()
    
    @handle_ui_error
    def update_supplier(self, supplier_id: int, data: dict):
        """Update supplier via API."""
        editable_fields = [
            'name', 'name_en', 'phone', 'mobile', 'email', 'fax', 'website',
            'address', 'city', 'region', 'postal_code', 'country',
            'tax_number', 'commercial_register', 'contact_person',
            'credit_limit', 'payment_terms', 'notes', 'is_active'
        ]
        update_data = {k: v for k, v in data.items() if k in editable_fields and v is not None}
        
        api.patch(f'purchases/suppliers/{supplier_id}/', update_data)
        MessageDialog.success(self, "نجاح", "تم تحديث المورد بنجاح")
        self.refresh()
    
    def on_action(self, action: str, row: int, data: dict):
        """Handle table action."""
        if action == 'edit':
            self.edit_supplier(row, data)
        elif action == 'delete':
            self.delete_supplier(data)
    
    @handle_ui_error
    def delete_supplier(self, data: dict):
        """Delete supplier via API."""
        dialog = ConfirmDialog(
            "حذف المورد",
            f"هل أنت متأكد من حذف المورد '{data.get('name')}'؟",
            parent=self
        )
        if dialog.exec():
            api.delete(f'purchases/suppliers/{data.get("id")}/')
            MessageDialog.success(self, "نجاح", "تم حذف المورد بنجاح")
            self.refresh()


class PurchaseOrdersView(QWidget):
    """
    Purchase orders management view.
    
    Requirements: 3.1, 3.2, 3.3, 3.4 - Purchase order creation and management
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        title = QLabel("أوامر الشراء")
        title.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_H2, QFont.Bold))
        layout.addWidget(title)
        
        columns = [
            {'key': 'order_number', 'label': 'رقم الأمر'},
            {'key': 'supplier_name', 'label': 'المورد'},
            {'key': 'order_date', 'label': 'التاريخ', 'type': 'date'},
            {'key': 'total_amount', 'label': 'المبلغ', 'type': 'currency'},
            {'key': 'status_display', 'label': 'الحالة'},
        ]
        
        self.table = DataTable(columns)
        self.table.add_btn.setText("➕ أمر شراء جديد")
        self.table.add_btn.clicked.connect(self.add_purchase_order)
        self.table.action_clicked.connect(self.on_action)
        layout.addWidget(self.table)
    
    def add_purchase_order(self):
        """Open dialog to create new purchase order."""
        dialog = PurchaseOrderFormDialog(parent=self)
        dialog.saved.connect(self.save_purchase_order)
        dialog.exec()
    
    @handle_ui_error
    def save_purchase_order(self, data: dict):
        """Save purchase order via API."""
        try:
            api.create_purchase_order(data)
            MessageDialog.success(self, "نجاح", "تم إنشاء أمر الشراء بنجاح")
            self.refresh()
        except ApiException as e:
            MessageDialog.error(self, "خطأ", str(e))
        
    @handle_ui_error
    def refresh(self):
        """Refresh purchase orders data from API."""
        response = api.get_purchase_orders()
        if isinstance(response, dict) and 'results' in response:
            orders = response['results']
        else:
            orders = response if isinstance(response, list) else []
        self.table.set_data(orders)
    
    def on_action(self, action: str, row: int, data: dict):
        """Handle table action."""
        if action == 'view':
            order_id = data.get('id')
            if order_id:
                try:
                    details = f"""
رقم الطلب: {data.get('order_number', '')}
التاريخ: {data.get('order_date', '')}
المورد: {data.get('supplier_name', '')}
الحالة: {data.get('status_display', data.get('status', ''))}
المجموع: {float(data.get('total_amount', 0)):,.2f} ل.س
                    """.strip()
                    MessageDialog.info(self, "تفاصيل طلب الشراء", details)
                except Exception as e:
                    MessageDialog.error(self, "خطأ", f"فشل في عرض التفاصيل: {str(e)}")


class PurchaseOrderFormDialog(QDialog):
    """
    Dialog for creating/editing purchase orders.
    
    Requirements: 4.1, 4.2, 4.3, 4.4, 4.5 - Purchase order form fields and validation
    """
    
    saved = Signal(dict)
    
    def __init__(self, data=None, parent=None):
        super().__init__(parent)
        self.data = data or {}
        self.items = []
        self.suppliers_cache = []
        self.warehouses_cache = []
        self.products_cache = []
        
        self.setWindowTitle("أمر شراء جديد")
        self.setup_ui()
        self.load_data()
        self.showMaximized()
    
    def setup_ui(self):
        """Build the form UI with two columns and cards."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)
        
        # Professional font sizing
        self.setFont(QFont(Fonts.FAMILY_AR, 10))

        # Header Section
        header_layout = QHBoxLayout()
        title_label = QLabel("إنشاء أمر شراء جديد")
        title_label.setProperty("class", "title")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        # Main Content Area: Split into two columns
        content_layout = QHBoxLayout()
        content_layout.setSpacing(10)

        # Left Column: Order Details and Items
        left_column = QVBoxLayout()
        left_column.setSpacing(8)

        # 1. Order Header Info Card (Optimized Space)
        info_card = Card()
        info_card_layout = QVBoxLayout(info_card)
        info_card_layout.setContentsMargins(12, 6, 12, 6)
        info_card_layout.setSpacing(4)

        info_title = QLabel("📋 معلومات أمر الشراء")
        info_title.setFont(QFont(Fonts.FAMILY_AR, 10, QFont.Bold))
        info_card_layout.addWidget(info_title)
        
        self.info_card = info_card

        grid_layout = QGridLayout()
        grid_layout.setSpacing(6)

        # Supplier
        grid_layout.addWidget(QLabel("المورد *"), 0, 0)
        self.supplier_combo = QComboBox()
        self.supplier_combo.setPlaceholderText("اختر المورد...")
        grid_layout.addWidget(self.supplier_combo, 0, 1)

        # Warehouse
        grid_layout.addWidget(QLabel("المستودع *"), 0, 2)
        self.warehouse_combo = QComboBox()
        self.warehouse_combo.setPlaceholderText("اختر المستودع...")
        grid_layout.addWidget(self.warehouse_combo, 0, 3)

        # Order Date
        grid_layout.addWidget(QLabel("تاريخ الطلب *"), 1, 0)
        self.order_date_edit = QDateEdit()
        self.order_date_edit.setCalendarPopup(True)
        self.order_date_edit.setDate(QDate.currentDate())
        grid_layout.addWidget(self.order_date_edit, 1, 1)

        # Expected Delivery Date
        grid_layout.addWidget(QLabel("تاريخ التسليم المتوقع"), 1, 2)
        self.expected_date_edit = QDateEdit()
        self.expected_date_edit.setCalendarPopup(True)
        self.expected_date_edit.setDate(QDate.currentDate().addDays(7))
        grid_layout.addWidget(self.expected_date_edit, 1, 3)

        info_card_layout.addLayout(grid_layout)
        left_column.addWidget(info_card)

        # 2. Product Entry Section (Optimized Space)
        entry_widget = Card()
        entry_widget_layout = QVBoxLayout(entry_widget)
        entry_widget_layout.setContentsMargins(12, 6, 12, 6)
        entry_widget_layout.setSpacing(4)

        entry_title = QLabel("📦 إضافة منتجات")
        entry_title.setFont(QFont(Fonts.FAMILY_AR, 10, QFont.Bold))
        entry_widget_layout.addWidget(entry_title)

        # Item Entry Row
        entry_layout = QHBoxLayout()
        entry_layout.setSpacing(8)

        self.product_combo = QComboBox()
        self.product_combo.setPlaceholderText("اختر المنتج...")
        self.product_combo.setMinimumWidth(180)
        entry_layout.addWidget(self.product_combo, 2)

        # Unit selector - Requirements: 4.1 - Display available units for selected product
        self.unit_selector = UnitSelectorComboBox(price_type='cost')
        self.unit_selector.setMinimumWidth(140)
        self.unit_selector.unit_changed.connect(self.on_unit_changed)
        entry_layout.addWidget(self.unit_selector, 2)

        self.quantity_spin = QDoubleSpinBox()
        self.quantity_spin.setRange(0.01, 999999)
        self.quantity_spin.setValue(1)
        self.quantity_spin.setPrefix("الكمية: ")
        entry_layout.addWidget(self.quantity_spin, 1)

        self.price_spin = QDoubleSpinBox()
        self.price_spin.setRange(0, 999999999)
        self.price_spin.setPrefix("السعر: ")
        self.price_spin.setMinimumWidth(120)
        entry_layout.addWidget(self.price_spin, 1)

        add_btn = QPushButton("➕ إضافة للمسودة")
        add_btn.setMinimumHeight(32)
        add_btn.setProperty("class", "primary")
        add_btn.clicked.connect(self.add_item)
        entry_layout.addWidget(add_btn, 1)

        entry_widget_layout.addLayout(entry_layout)
        left_column.addWidget(entry_widget)
        self.entry_widget = entry_widget

        # 3. Barcode Scanner Section (Integrated)
        barcode_row = QHBoxLayout()
        barcode_row.setSpacing(8)

        barcode_label = QLabel("📷 مسح باركود مباشر:")
        barcode_label.setFont(QFont(Fonts.FAMILY_AR, 10, QFont.Bold))
        barcode_row.addWidget(barcode_label)

        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("ضع المؤشر هنا وامسح بالباركود...")
        self.barcode_input.setMinimumHeight(32)
        self.barcode_input.setFont(QFont(Fonts.FAMILY_AR, 10))
        self.barcode_input.returnPressed.connect(self.add_item_by_barcode)
        barcode_row.addWidget(self.barcode_input, 1)

        entry_widget_layout.addLayout(barcode_row)
        left_column.addWidget(entry_widget)

        # 4. Items Table Section Card (Dominant Stretch)
        items_card = Card()
        items_card_layout = QVBoxLayout(items_card)
        items_card_layout.setContentsMargins(12, 12, 12, 12)
        items_card_layout.setSpacing(8)

        items_title = QLabel("📦 قائمة المنتجات المختارة")
        items_title.setFont(QFont(Fonts.FAMILY_AR, 11, QFont.Bold))
        items_card_layout.addWidget(items_title)

        # Items Table
        # Requirements: 4.1, 4.2 - Add unit column for unit selection display
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(6)
        self.items_table.setHorizontalHeaderLabels(['المنتج', 'الوحدة', 'الكمية', 'السعر', 'الإجمالي', ''])
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.items_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)
        self.items_table.setColumnWidth(5, 25)
        self.items_table.verticalHeader().setVisible(False)
        self.items_table.setAlternatingRowColors(True)
        self.items_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.items_table.setShowGrid(False)
        self.items_table.setStyleSheet(f"""
            QTableWidget {{
                border: 1px solid {Colors.LIGHT_BORDER};
                border-radius: 6px;
                background-color: white;
            }}
            QTableWidget::item {{
                padding: 2px;
                border-bottom: 1px solid {Colors.LIGHT_BORDER};
            }}
            QTableWidget::item:alternate {{
                background-color: {Colors.TABLE_ROW_ALT_LIGHT};
            }}
            QTableWidget::item:selected {{
                background-color: {Colors.PRIMARY}20;
                color: {Colors.PRIMARY};
            }}
            QHeaderView::section {{
                background-color: {Colors.PRIMARY};
                color: white;
                padding: 10px;
                border: none;
                font-weight: bold;
                font-size: 11px;
            }}
            QScrollBar:vertical {{
                background: {Colors.LIGHT_BG};
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {Colors.PRIMARY_LIGHT};
                border-radius: 4px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {Colors.PRIMARY};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
        """)
        # Professional compact row height
        self.items_table.verticalHeader().setDefaultSectionSize(32)
        self.items_table.setFont(QFont(Fonts.FAMILY_AR, 10))
        # Ensure scrollbars show when needed
        self.items_table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.items_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        items_card_layout.addWidget(self.items_table, 1)

        # Add items_card with high stretch factor
        left_column.addWidget(items_card, 100) # Dominant!!!
        content_layout.addLayout(left_column, 10) # 10/11 = ~90% horizontal space

        # Right Column: Summary and Notes
        right_column = QVBoxLayout()
        right_column.setSpacing(8)

        # Summary Card (Narrower for table space)
        summary_card = Card()
        summary_card.setFixedWidth(240)
        summary_card_layout = QVBoxLayout(summary_card)
        summary_card_layout.setContentsMargins(12, 12, 12, 12)
        summary_card_layout.setSpacing(8)

        summary_title = QLabel("💰 ملخص التكاليف")
        summary_title.setFont(QFont(Fonts.FAMILY_AR, 11, QFont.Bold))
        summary_card_layout.addWidget(summary_title)

        # Totals Display
        totals_layout = QVBoxLayout()
        totals_layout.setSpacing(8)

        def add_total_row(label, value_attr, is_grand=False):
            row = QHBoxLayout()
            lbl = QLabel(label)
            if is_grand:
                lbl.setFont(QFont(Fonts.FAMILY_AR, 12, QFont.Bold))
            else:
                lbl.setProperty("class", "body")
            
            val = QLabel("0.00 ل.س")
            if is_grand:
                val.setFont(QFont(Fonts.FAMILY_AR, 14, QFont.Bold))
                val.setStyleSheet(f"color: {Colors.PRIMARY};")
            else:
                val.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_BODY, QFont.Bold))
            
            setattr(self, value_attr, val)
            row.addWidget(lbl)
            row.addStretch()
            row.addWidget(val)
            totals_layout.addLayout(row)

        add_total_row("إجمالي المنتجات:", "subtotal_value")
        
        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet(f"background-color: {Colors.LIGHT_BORDER};")
        totals_layout.addWidget(line)
        
        add_total_row("الإجمالي الكلي:", "total_value", is_grand=True)

        summary_card_layout.addLayout(totals_layout)
        
        # Notes Section
        notes_label = QLabel("📝 ملاحظات إضافية")
        notes_label.setFont(QFont(Fonts.FAMILY_AR, 10, QFont.Bold))
        summary_card_layout.addWidget(notes_label)
        
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("اكتب أي ملاحظات هنا...")
        self.notes_edit.setMaximumHeight(80)
        self.notes_edit.setStyleSheet(f"background-color: {Colors.LIGHT_BG}; border: 1px solid {Colors.LIGHT_BORDER}; border-radius: 6px;")
        summary_card_layout.addWidget(self.notes_edit)
        
        summary_card_layout.addStretch()
        
        save_btn = QPushButton("✅ حفظ أمر الشراء")
        save_btn.setProperty("class", "success")
        save_btn.setMinimumHeight(45)
        save_btn.setFont(QFont(Fonts.FAMILY_AR, 12, QFont.Bold))
        save_btn.clicked.connect(self.save)
        summary_card_layout.addWidget(save_btn)

        cancel_btn = QPushButton("إلغاء")
        cancel_btn.setProperty("class", "secondary")
        cancel_btn.setMinimumHeight(35)
        cancel_btn.clicked.connect(self.reject)
        summary_card_layout.addWidget(cancel_btn)

        right_column.addWidget(summary_card)
        self.right_column = summary_card
        
        # Error Label
        self.error_label = QLabel()
        self.error_label.setStyleSheet(f"color: {Colors.DANGER}; font-weight: bold;")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setVisible(False)
        right_column.addWidget(self.error_label)

        content_layout.addLayout(right_column, 1)
        main_layout.addLayout(content_layout)

    def add_item_by_barcode(self):
        """Add item by barcode scan."""
        barcode = self.barcode_input.text().strip()
        if not barcode:
            return
        
        # Find product by barcode in cache
        product_found = None
        for product in self.products_cache:
            if product.get('barcode') == barcode:
                product_found = product
                break
        
        if not product_found:
            # Try API lookup
            try:
                product_found = api.get(f'inventory/products/barcode/{barcode}/')
            except ApiException:
                MessageDialog.warning(self, "تنبيه", f"لم يتم العثور على منتج بالباركود: {barcode}")
                self.barcode_input.clear()
                self.barcode_input.setFocus()
                return
        
        if product_found:
            product_id = product_found.get('id')
            product_name = product_found.get('name', '')
            unit_price = float(product_found.get('cost_price', 0))
            
            # Get product units for unit selection
            product_units = product_found.get('product_units', [])
            
            # Find base unit or first unit
            selected_unit = None
            unit_name = ''
            unit_symbol = ''
            product_unit_id = None
            
            if product_units:
                # Find base unit
                for pu in product_units:
                    if pu.get('is_base_unit', False):
                        selected_unit = pu
                        break
                # If no base unit, use first unit
                if not selected_unit and product_units:
                    selected_unit = product_units[0]
                
                if selected_unit:
                    unit_name = selected_unit.get('unit_name', '')
                    unit_symbol = selected_unit.get('unit_symbol', '')
                    product_unit_id = selected_unit.get('id')
                    # Use unit-specific cost price if available
                    unit_cost_price = float(selected_unit.get('cost_price', 0))
                    if unit_cost_price > 0:
                        unit_price = unit_cost_price
            
            # Check if product with same unit already in list
            for item in self.items:
                if item['product'] == product_id and item.get('product_unit') == product_unit_id:
                    item['quantity'] += 1
                    item['total'] = item['quantity'] * item['unit_price']
                    self.update_items_table()
                    self.barcode_input.clear()
                    self.barcode_input.setFocus()
                    return
            
            # Add new item with quantity 1
            self.items.append({
                'product': product_id,
                'product_name': product_name,
                'product_unit': product_unit_id,
                'unit_name': unit_name,
                'unit_symbol': unit_symbol,
                'quantity': 1,
                'unit_price': unit_price,
                'total': unit_price
            })
            
            self.update_items_table()
        
        # Clear and refocus for next scan
        self.barcode_input.clear()
        self.barcode_input.setFocus()

    def load_data(self):
        """Load suppliers, warehouses, products from API."""
        try:
            # Load suppliers
            suppliers_response = api.get_suppliers()
            if isinstance(suppliers_response, dict) and 'results' in suppliers_response:
                self.suppliers_cache = suppliers_response['results']
            else:
                self.suppliers_cache = suppliers_response if isinstance(suppliers_response, list) else []
            
            self.supplier_combo.clear()
            self.supplier_combo.addItem("اختر المورد...", None)
            for supplier in self.suppliers_cache:
                display_text = f"{supplier.get('name', '')} ({supplier.get('code', '')})"
                self.supplier_combo.addItem(display_text, supplier.get('id'))
            
            # Load warehouses
            warehouses_response = api.get_warehouses()
            if isinstance(warehouses_response, dict) and 'results' in warehouses_response:
                self.warehouses_cache = warehouses_response['results']
            else:
                self.warehouses_cache = warehouses_response if isinstance(warehouses_response, list) else []
            
            self.warehouse_combo.clear()
            self.warehouse_combo.addItem("اختر المستودع...", None)
            for warehouse in self.warehouses_cache:
                self.warehouse_combo.addItem(warehouse.get('name', ''), warehouse.get('id'))
            
            # Select default warehouse if available
            for i, warehouse in enumerate(self.warehouses_cache):
                if warehouse.get('is_default'):
                    self.warehouse_combo.setCurrentIndex(i + 1)
                    break
            
            # Load products
            products_response = api.get_products()
            if isinstance(products_response, dict) and 'results' in products_response:
                self.products_cache = products_response['results']
            else:
                self.products_cache = products_response if isinstance(products_response, list) else []
            
            self.product_combo.clear()
            self.product_combo.addItem("اختر المنتج...", None)
            for product in self.products_cache:
                display_text = f"{product.get('name', '')} - {float(product.get('cost_price', 0)):,.2f} ل.س"
                self.product_combo.addItem(display_text, product.get('id'))
            
            # Update price when product is selected
            self.product_combo.currentIndexChanged.connect(self.on_product_changed)
            
        except ApiException as e:
            MessageDialog.error(self, "خطأ", f"فشل في تحميل البيانات: {str(e)}")
    
    def on_product_changed(self, index: int):
        """Update price and unit selector when product is selected (use cost_price for purchases)."""
        product_id = self.product_combo.currentData()
        if product_id:
            for product in self.products_cache:
                if product.get('id') == product_id:
                    # Update price with base cost price
                    self.price_spin.setValue(float(product.get('cost_price', 0)))
                    
                    # Update unit selector with product units
                    # Requirements: 4.1 - Display available units for selected product
                    product_units = product.get('product_units', [])
                    self.unit_selector.set_product_units(product_units, product_id)
                    break
        else:
            # Clear unit selector when no product selected
            self.unit_selector.clear_units()
    
    def on_unit_changed(self, pu_id: int, unit_name: str, unit_symbol: str, 
                        sale_price: float, cost_price: float, conversion_factor: float):
        """
        Handle unit selection change - auto-populate cost price.
        
        Requirements: 4.2 - Allow entering unit-specific cost
        """
        if cost_price > 0:
            self.price_spin.setValue(cost_price)
    
    def add_item(self):
        """Add item to the items list."""
        product_id = self.product_combo.currentData()
        if not product_id:
            MessageDialog.warning(self, "تنبيه", "يرجى اختيار منتج")
            return
        
        quantity = self.quantity_spin.value()
        unit_price = self.price_spin.value()
        
        if quantity <= 0:
            MessageDialog.warning(self, "تنبيه", "يرجى إدخال كمية صحيحة")
            return
        
        # Get product name
        product_name = ""
        for product in self.products_cache:
            if product.get('id') == product_id:
                product_name = product.get('name', '')
                break
        
        # Get selected unit information
        # Requirements: 4.1, 4.2 - Unit selection in purchases
        selected_unit = self.unit_selector.get_selected_unit()
        product_unit_id = None
        unit_name = ''
        unit_symbol = ''
        
        if selected_unit:
            product_unit_id = selected_unit.get('id')
            unit_name = selected_unit.get('unit_name', '')
            unit_symbol = selected_unit.get('unit_symbol', '')
        
        # Check if product with same unit already in list
        for item in self.items:
            if item['product'] == product_id and item.get('product_unit') == product_unit_id:
                item['quantity'] += quantity
                item['total'] = item['quantity'] * item['unit_price']
                self.update_items_table()
                # Reset inputs
                self.product_combo.setCurrentIndex(0)
                self.quantity_spin.setValue(1)
                self.price_spin.setValue(0)
                self.unit_selector.clear_units()
                return
        
        # Add new item
        self.items.append({
            'product': product_id,
            'product_name': product_name,
            'product_unit': product_unit_id,
            'unit_name': unit_name,
            'unit_symbol': unit_symbol,
            'quantity': quantity,
            'unit_price': unit_price,
            'total': quantity * unit_price
        })
        
        self.update_items_table()
        
        # Reset inputs
        self.product_combo.setCurrentIndex(0)
        self.quantity_spin.setValue(1)
        self.price_spin.setValue(0)
        self.unit_selector.clear_units()

    def update_items_table(self):
        """Update items table display."""
        self.items_table.setRowCount(len(self.items))
        
        for i, item in enumerate(self.items):
            # Product name
            self.items_table.setItem(i, 0, QTableWidgetItem(item['product_name']))
            
            # Unit name - Requirements: 4.5 - Display selected unit name/symbol
            unit_display = item.get('unit_name', '') or item.get('unit_symbol', '') or '-'
            self.items_table.setItem(i, 1, QTableWidgetItem(unit_display))
            
            # Quantity
            self.items_table.setItem(i, 2, QTableWidgetItem(f"{item['quantity']:.2f}"))
            
            # Price
            self.items_table.setItem(i, 3, QTableWidgetItem(f"{item['unit_price']:,.2f}"))
            
            # Total - Requirements: 4.3 - Calculate line total
            self.items_table.setItem(i, 4, QTableWidgetItem(f"{item['total']:,.2f}"))
            
            # Delete button
            delete_btn = QPushButton("🗑️")
            delete_btn.setFixedSize(30, 30)
            delete_btn.setStyleSheet("border: none; background: transparent;")
            delete_btn.clicked.connect(lambda _, idx=i: self.remove_item(idx))
            self.items_table.setCellWidget(i, 5, delete_btn)
        
        # Update summary
        total = sum(item['total'] for item in self.items)
        self.subtotal_value.setText(f"{total:,.2f} ل.س")
        self.total_value.setText(f"{total:,.2f} ل.س")
        
        # Auto-scroll to last item - Requirements: 2.3
        if self.items:
            last_row = len(self.items) - 1
            last_item = self.items_table.item(last_row, 0)
            if last_item:
                self.items_table.scrollToItem(last_item, QAbstractItemView.EnsureVisible)
    
    def remove_item(self, index: int):
        """Remove item from the list."""
        if 0 <= index < len(self.items):
            self.items.pop(index)
            self.update_items_table()
    
    def validate(self) -> bool:
        """Validate form data."""
        self.error_label.setVisible(False)
        
        supplier_id = self.supplier_combo.currentData()
        warehouse_id = self.warehouse_combo.currentData()
        
        # Validate supplier - required
        if not supplier_id:
            MessageDialog.warning(self, "تنبيه", "يجب اختيار المورد")
            return False
        
        # Validate warehouse - required
        if not warehouse_id:
            self.error_label.setText("يجب اختيار المستودع")
            self.error_label.setVisible(True)
            return False
        
        # Validate items - at least one required
        if not self.items:
            MessageDialog.warning(self, "تنبيه", "يجب إضافة منتج واحد على الأقل")
            return False
        
        return True
    
    def get_data(self) -> dict:
        """Get form data as dictionary."""
        data = {
            'supplier': self.supplier_combo.currentData(),
            'warehouse': self.warehouse_combo.currentData(),
            'order_date': self.order_date_edit.date().toString('yyyy-MM-dd'),
            'expected_date': self.expected_date_edit.date().toString('yyyy-MM-dd'),
            'confirm': True,
            'items': [
                {
                    'product': item['product'],
                    'product_unit': item.get('product_unit'),  # Include product_unit for unit tracking
                    'quantity': item['quantity'],
                    'unit_price': item['unit_price']
                }
                for item in self.items
            ]
        }
        
        notes = self.notes_edit.toPlainText().strip()
        if notes:
            data['notes'] = notes
        
        return data
    
    def save(self):
        """Emit saved signal with form data."""
        if self.validate():
            self.saved.emit(self.get_data())
            self.accept()
