"""
Purchases Views - Suppliers and Purchase Orders

Requirements: 4.1, 4.2 - Error handling for CRUD operations and form submissions
Requirements: 3.1, 3.2, 3.3, 3.4 - Purchase order creation and management
Requirements: 4.1, 4.2, 4.3 - Unit selection in purchases
Requirements: 12.2, 12.4, 12.6 - Purchase order details, status actions, filtering
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QDialog, QComboBox, QDateEdit, QTextEdit,
    QDoubleSpinBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QGridLayout, QFrame,
    QAbstractItemView, QLineEdit, QSpinBox, QCheckBox
)
from PySide6.QtCore import Qt, Signal, QDate, QEvent
from PySide6.QtGui import QFont

from ...config import Colors, Fonts, config
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
            {'key': 'current_balance_display', 'label': 'الرصيد (ل.س)'},
            {'key': 'current_balance_usd_display', 'label': 'الرصيد (USD)'},
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
        for s in suppliers:
            try:
                s['current_balance_display'] = f"{float(s.get('current_balance', 0)):,.2f} ل.س"
            except (ValueError, TypeError):
                s['current_balance_display'] = str(s.get('current_balance', ''))
            try:
                s['current_balance_usd_display'] = config.format_usd(float(s.get('current_balance_usd', 0) or 0))
            except (ValueError, TypeError):
                s['current_balance_usd_display'] = str(s.get('current_balance_usd', ''))
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
        """
        Update supplier via API.
        
        Requirements: 3.3 - Edit supplier functionality
        """
        editable_fields = [
            'name', 'name_en', 'phone', 'mobile', 'email', 'fax', 'website',
            'address', 'city', 'region', 'postal_code', 'country',
            'tax_number', 'commercial_register', 'contact_person',
            'credit_limit', 'payment_terms', 'notes', 'is_active'
        ]
        update_data = {k: v for k, v in data.items() if k in editable_fields and v is not None}
        
        api.update_supplier(supplier_id, update_data)
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
        """
        Delete supplier via API.
        
        Requirements: 3.4, 3.5 - Delete with confirmation and handle deletion protection
        """
        dialog = ConfirmDialog(
            "حذف المورد",
            f"هل أنت متأكد من حذف المورد '{data.get('name')}'؟",
            parent=self
        )
        if dialog.exec():
            try:
                api.delete_supplier(data.get("id"))
                MessageDialog.success(self, "نجاح", "تم حذف المورد بنجاح")
                self.refresh()
            except ApiException as e:
                # Handle deletion protection error
                if e.error_code == 'DELETION_PROTECTED':
                    MessageDialog.error(
                        self,
                        "لا يمكن الحذف",
                        "لا يمكن حذف المورد لوجود أوامر شراء مرتبطة به"
                    )
                else:
                    raise


class PurchaseOrdersView(QWidget):
    """
    Purchase orders management view.
    
    Requirements: 3.1, 3.2, 3.3, 3.4 - Purchase order creation and management
    Requirements: 12.2, 12.4, 12.6 - Details dialog, status actions, filtering
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.suppliers_cache = []
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        title = QLabel("أوامر الشراء")
        title.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_H2, QFont.Bold))
        layout.addWidget(title)
        
        # Requirements: 12.6 - Add filtering section
        filter_frame = QFrame()
        filter_frame.setStyleSheet(f"background-color: {Colors.LIGHT_BG}; border-radius: 8px; padding: 12px;")
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setSpacing(16)
        
        # Status filter
        filter_layout.addWidget(QLabel("الحالة:"))
        self.status_filter = QComboBox()
        self.status_filter.addItem("الكل", None)
        self.status_filter.addItem("مسودة", "draft")
        self.status_filter.addItem("معتمد", "approved")
        self.status_filter.addItem("تم الطلب", "ordered")
        self.status_filter.addItem("مستلم جزئياً", "partial")
        self.status_filter.addItem("مستلم", "received")
        self.status_filter.addItem("ملغي", "cancelled")
        self.status_filter.currentIndexChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.status_filter)
        
        # Supplier filter
        filter_layout.addWidget(QLabel("المورد:"))
        self.supplier_filter = QComboBox()
        self.supplier_filter.addItem("الكل", None)
        self.supplier_filter.currentIndexChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.supplier_filter)
        
        # Date range filter
        filter_layout.addWidget(QLabel("من:"))
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.date_from.dateChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.date_from)
        
        filter_layout.addWidget(QLabel("إلى:"))
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        self.date_to.dateChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.date_to)
        
        # Clear filters button
        clear_btn = QPushButton("مسح الفلاتر")
        clear_btn.setProperty("class", "secondary")
        clear_btn.clicked.connect(self.clear_filters)
        filter_layout.addWidget(clear_btn)
        
        filter_layout.addStretch()
        layout.addWidget(filter_frame)
        
        columns = [
            {'key': 'order_number', 'label': 'رقم الأمر'},
            {'key': 'supplier_name', 'label': 'المورد'},
            {'key': 'order_date', 'label': 'التاريخ', 'type': 'date'},
            {'key': 'total_amount_display', 'label': 'المبلغ (USD)'},
            {'key': 'status_display', 'label': 'الحالة'},
        ]
        
        self.table = DataTable(columns)
        self.table.add_btn.setText("➕ أمر شراء جديد")
        self.table.add_btn.clicked.connect(self.add_purchase_order)
        self.table.action_clicked.connect(self.on_action)
        self.table.row_double_clicked.connect(self.show_order_details)
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
        # Load suppliers for filter
        self.load_suppliers()
        
        # Apply filters
        self.apply_filters()
    
    def load_suppliers(self):
        """Load suppliers for filter dropdown."""
        try:
            response = api.get_suppliers()
            if isinstance(response, dict) and 'results' in response:
                self.suppliers_cache = response['results']
            else:
                self.suppliers_cache = response if isinstance(response, list) else []
            
            # Update supplier filter combo
            current_supplier = self.supplier_filter.currentData()
            self.supplier_filter.blockSignals(True)
            self.supplier_filter.clear()
            self.supplier_filter.addItem("الكل", None)
            for supplier in self.suppliers_cache:
                self.supplier_filter.addItem(supplier.get('name', ''), supplier.get('id'))
            
            # Restore selection
            if current_supplier:
                for i in range(self.supplier_filter.count()):
                    if self.supplier_filter.itemData(i) == current_supplier:
                        self.supplier_filter.setCurrentIndex(i)
                        break
            self.supplier_filter.blockSignals(False)
        except Exception:
            pass
    
    @handle_ui_error
    def apply_filters(self):
        """Apply filters and refresh data."""
        params = {}
        
        # Status filter
        status = self.status_filter.currentData()
        if status:
            params['status'] = status
        
        # Supplier filter
        supplier_id = self.supplier_filter.currentData()
        if supplier_id:
            params['supplier'] = supplier_id
        
        # Date range filter
        params['order_date__gte'] = self.date_from.date().toString('yyyy-MM-dd')
        params['order_date__lte'] = self.date_to.date().toString('yyyy-MM-dd')
        
        response = api.get_purchase_orders(params)
        if isinstance(response, dict) and 'results' in response:
            orders = response['results']
        else:
            orders = response if isinstance(response, list) else []
        for o in orders:
            try:
                amount = float(o.get('total_amount_usd', 0) or 0)
                o['total_amount_display'] = config.format_usd(amount)
            except (ValueError, TypeError):
                o['total_amount_display'] = str(o.get('total_amount_usd', o.get('total_amount', '')))
        self.table.set_data(orders)
    
    def clear_filters(self):
        """Clear all filters."""
        self.status_filter.setCurrentIndex(0)
        self.supplier_filter.setCurrentIndex(0)
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.date_to.setDate(QDate.currentDate())
        self.apply_filters()
    
    @handle_ui_error
    def show_order_details(self, row: int, data: dict):
        """
        Show purchase order details dialog on double-click.
        
        Requirements: 12.2 - Display full PO with items on double-click
        """
        order_id = data.get('id')
        if order_id:
            # Fetch full order details with items
            order = api.get_purchase_order(order_id)
            dialog = PurchaseOrderDetailsDialog(order, parent=self)
            dialog.approve_requested.connect(self.approve_order)
            dialog.mark_ordered_requested.connect(self.mark_order_ordered)
            dialog.receive_requested.connect(self.receive_goods)
            dialog.payment_requested.connect(self.create_supplier_payment)
            dialog.exec()

    @handle_ui_error
    def create_supplier_payment(self, order: dict):
        dialog = SupplierPaymentDialog(order=order, parent=self)
        dialog.saved.connect(self.save_supplier_payment)
        dialog.exec()

    @handle_ui_error
    def save_supplier_payment(self, data: dict):
        api.create_supplier_payment(data)
        MessageDialog.success(self, "نجاح", "تم تسجيل دفعة المورد بنجاح")
        self.apply_filters()
    
    @handle_ui_error
    def approve_order(self, order: dict):
        """
        Approve a purchase order.
        
        Requirements: 12.4 - Status actions
        """
        order_id = order.get('id')
        if order_id:
            api.approve_purchase_order(order_id)
            MessageDialog.success(self, "نجاح", "تم اعتماد أمر الشراء بنجاح")
            self.apply_filters()
    
    @handle_ui_error
    def mark_order_ordered(self, order: dict):
        """
        Mark a purchase order as ordered.
        
        Requirements: 12.4 - Status actions
        """
        order_id = order.get('id')
        if order_id:
            api.mark_purchase_order_ordered(order_id)
            MessageDialog.success(self, "نجاح", "تم تحديث حالة أمر الشراء إلى 'تم الطلب'")
            self.apply_filters()
    
    @handle_ui_error
    def receive_goods(self, order: dict):
        """
        Open goods receipt dialog.
        
        Requirements: 12.4 - Receive goods action
        """
        dialog = GoodsReceiptDialog(order, parent=self)
        dialog.saved.connect(self.process_goods_receipt)
        dialog.exec()
    
    @handle_ui_error
    def process_goods_receipt(self, data: dict):
        """Process goods receipt."""
        order_id = data.get('order_id')
        if order_id:
            api.receive_goods(order_id, data)
            MessageDialog.success(self, "نجاح", "تم استلام البضاعة بنجاح")
            self.apply_filters()
    
    def on_action(self, action: str, row: int, data: dict):
        """Handle table action."""
        if action == 'view':
            self.show_order_details(row, data)
        elif action == 'edit':
            self.show_order_details(row, data)


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

        grid_layout.addWidget(QLabel("تاريخ سعر الصرف *"), 2, 0)
        self.fx_rate_date_edit = QDateEdit()
        self.fx_rate_date_edit.setCalendarPopup(True)
        self.fx_rate_date_edit.setDate(QDate.currentDate())
        grid_layout.addWidget(self.fx_rate_date_edit, 2, 1)

        grid_layout.addWidget(QLabel("USD → ل.س قديم *"), 2, 2)
        self.usd_to_syp_old_snapshot = QDoubleSpinBox()
        self.usd_to_syp_old_snapshot.setRange(0, 999999999999)
        self.usd_to_syp_old_snapshot.setDecimals(6)
        grid_layout.addWidget(self.usd_to_syp_old_snapshot, 2, 3)

        grid_layout.addWidget(QLabel("USD → ل.س جديد"), 3, 2)
        self.usd_to_syp_new_snapshot = QDoubleSpinBox()
        self.usd_to_syp_new_snapshot.setRange(0, 999999999999)
        self.usd_to_syp_new_snapshot.setDecimals(6)
        grid_layout.addWidget(self.usd_to_syp_new_snapshot, 3, 3)

        self._updating_fx = False
        self.usd_to_syp_old_snapshot.valueChanged.connect(self._on_old_fx_changed)
        self.usd_to_syp_new_snapshot.valueChanged.connect(self._on_new_fx_changed)

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
            
            val = QLabel(config.format_usd(0))
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

        self.pay_now_check = QCheckBox("💸 دفع الآن (اختياري)")
        self.pay_now_check.setChecked(False)
        self.pay_now_check.stateChanged.connect(self._on_pay_now_changed)
        summary_card_layout.addWidget(self.pay_now_check)

        payment_frame = QFrame()
        payment_layout = QGridLayout(payment_frame)
        payment_layout.setSpacing(6)

        payment_layout.addWidget(QLabel("تاريخ الدفع"), 0, 0)
        self.payment_date_edit = QDateEdit()
        self.payment_date_edit.setCalendarPopup(True)
        self.payment_date_edit.setDate(QDate.currentDate())
        payment_layout.addWidget(self.payment_date_edit, 0, 1)

        payment_layout.addWidget(QLabel("عملة الدفع"), 1, 0)
        self.payment_currency_combo = QComboBox()
        self.payment_currency_combo.addItem("USD", "USD")
        self.payment_currency_combo.addItem("ل.س قديم", "SYP_OLD")
        self.payment_currency_combo.addItem("ل.س جديد", "SYP_NEW")
        payment_layout.addWidget(self.payment_currency_combo, 1, 1)

        payment_layout.addWidget(QLabel("المبلغ"), 2, 0)
        self.payment_amount_spin = QDoubleSpinBox()
        self.payment_amount_spin.setRange(0, 999999999999)
        self.payment_amount_spin.setDecimals(2)
        payment_layout.addWidget(self.payment_amount_spin, 2, 1)

        payment_layout.addWidget(QLabel("طريقة الدفع"), 3, 0)
        self.payment_method_combo = QComboBox()
        self.payment_method_combo.addItem("نقداً", "cash")
        self.payment_method_combo.addItem("تحويل بنكي", "bank")
        self.payment_method_combo.addItem("شيك", "check")
        self.payment_method_combo.addItem("بطاقة ائتمان", "credit")
        payment_layout.addWidget(self.payment_method_combo, 3, 1)

        payment_layout.addWidget(QLabel("المرجع"), 4, 0)
        self.payment_reference_edit = QLineEdit()
        self.payment_reference_edit.setPlaceholderText("اختياري")
        payment_layout.addWidget(self.payment_reference_edit, 4, 1)

        full_pay_btn = QPushButton("دفع كامل")
        full_pay_btn.setProperty("class", "secondary")
        full_pay_btn.clicked.connect(self.set_full_payment_amount)
        payment_layout.addWidget(full_pay_btn, 5, 0, 1, 2)

        self.payment_frame = payment_frame
        summary_card_layout.addWidget(payment_frame)
        self._on_pay_now_changed()
        
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

        fx_old = float(self.usd_to_syp_old_snapshot.value() or 0)
        fx_new = float(self.usd_to_syp_new_snapshot.value() or 0)
        if fx_old <= 0 and fx_new <= 0:
            MessageDialog.warning(self, "تنبيه", "يجب إدخال سعر الصرف قبل إضافة المنتجات")
            return
        if fx_old <= 0 and fx_new > 0:
            fx_old = fx_new * 100
        
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
            cost_usd = product_found.get('cost_price_usd', None)
            if cost_usd is not None:
                unit_price = float(cost_usd or 0)
            else:
                unit_price = float(product_found.get('cost_price', 0) or 0) / fx_old
            
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
                    unit_cost_usd = selected_unit.get('cost_price_usd', None)
                    if unit_cost_usd is not None and float(unit_cost_usd or 0) > 0:
                        unit_price = float(unit_cost_usd or 0)
                    else:
                        unit_cost_price = float(selected_unit.get('cost_price', 0) or 0)
                        if unit_cost_price > 0:
                            unit_price = unit_cost_price / fx_old
            
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
                display_text = f"{product.get('name', '')}"
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
                    fx_old = float(self.usd_to_syp_old_snapshot.value() or 0)
                    cost_usd = product.get('cost_price_usd', None)
                    if cost_usd is not None:
                        self.price_spin.setValue(float(cost_usd or 0))
                    else:
                        cost_syp_old = float(product.get('cost_price', 0) or 0)
                        if fx_old > 0:
                            self.price_spin.setValue(cost_syp_old / fx_old)
                        else:
                            self.price_spin.setValue(cost_syp_old)
                    
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
        if pu_id is None:
            return

        selected_unit = self.unit_selector.get_selected_unit() or {}
        cost_usd = selected_unit.get('cost_price_usd', None)
        if cost_usd is not None and float(cost_usd or 0) > 0:
            self.price_spin.setValue(float(cost_usd or 0))
            return

        fx_old = float(self.usd_to_syp_old_snapshot.value() or 0)
        if cost_price > 0:
            if fx_old > 0:
                self.price_spin.setValue(cost_price / fx_old)
            else:
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
        self.subtotal_value.setText(config.format_usd(total))
        self.total_value.setText(config.format_usd(total))
        
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

        fx_old = float(self.usd_to_syp_old_snapshot.value() or 0)
        fx_new = float(self.usd_to_syp_new_snapshot.value() or 0)
        if fx_old <= 0 and fx_new <= 0:
            MessageDialog.warning(self, "تنبيه", "يجب إدخال سعر الصرف")
            return False

        if self.pay_now_check.isChecked():
            total_usd = sum(float(item.get('total', 0) or 0) for item in self.items)
            pay_amount = float(self.payment_amount_spin.value() or 0)
            if pay_amount <= 0:
                MessageDialog.warning(self, "تنبيه", "يرجى إدخال مبلغ دفع صحيح")
                return False

            pay_currency = self.payment_currency_combo.currentData() if hasattr(self, 'payment_currency_combo') else 'USD'
            pay_amount_usd = pay_amount
            if pay_currency == 'SYP_OLD':
                pay_amount_usd = (pay_amount / fx_old) if fx_old else pay_amount
            elif pay_currency == 'SYP_NEW':
                pay_amount_usd = (pay_amount / fx_new) if fx_new else pay_amount

            if pay_amount_usd > total_usd:
                MessageDialog.warning(self, "تنبيه", "مبلغ الدفعة أكبر من إجمالي أمر الشراء")
                return False

        return True
    
    def get_data(self) -> dict:
        """Get form data as dictionary."""
        fx_old = float(self.usd_to_syp_old_snapshot.value() or 0)
        fx_new = float(self.usd_to_syp_new_snapshot.value() or 0)
        data = {
            'supplier': self.supplier_combo.currentData(),
            'warehouse': self.warehouse_combo.currentData(),
            'order_date': self.order_date_edit.date().toString('yyyy-MM-dd'),
            'expected_date': self.expected_date_edit.date().toString('yyyy-MM-dd'),
            'fx_rate_date': self.fx_rate_date_edit.date().toString('yyyy-MM-dd'),
            'usd_to_syp_old_snapshot': fx_old if fx_old > 0 else None,
            'usd_to_syp_new_snapshot': fx_new if fx_new > 0 else None,
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

        if self.pay_now_check.isChecked() and float(self.payment_amount_spin.value() or 0) > 0:
            data.update({
                'payment_amount': float(self.payment_amount_spin.value()),
                'payment_method': self.payment_method_combo.currentData(),
                'payment_date': self.payment_date_edit.date().toString('yyyy-MM-dd'),
                'payment_transaction_currency': self.payment_currency_combo.currentData(),
                'payment_reference': self.payment_reference_edit.text().strip() or None,
                'payment_notes': None,
            })

            if (self.payment_currency_combo.currentData() or 'USD') != 'USD':
                data['payment_fx_rate_date'] = self.fx_rate_date_edit.date().toString('yyyy-MM-dd')
                data['payment_usd_to_syp_old_snapshot'] = fx_old if fx_old > 0 else None
                data['payment_usd_to_syp_new_snapshot'] = fx_new if fx_new > 0 else None
        
        notes = self.notes_edit.toPlainText().strip()
        if notes:
            data['notes'] = notes
        
        return data
    
    def save(self):
        """Emit saved signal with form data."""
        if self.validate():
            self.saved.emit(self.get_data())
            self.accept()

    def _on_old_fx_changed(self, value: float):
        if self._updating_fx:
            return
        if value and value > 0 and (self.usd_to_syp_new_snapshot.value() or 0) <= 0:
            self._updating_fx = True
            self.usd_to_syp_new_snapshot.setValue(value / 100)
            self._updating_fx = False

    def _on_new_fx_changed(self, value: float):
        if self._updating_fx:
            return
        if value and value > 0 and (self.usd_to_syp_old_snapshot.value() or 0) <= 0:
            self._updating_fx = True
            self.usd_to_syp_old_snapshot.setValue(value * 100)
            self._updating_fx = False

    def _on_pay_now_changed(self, *args):
        enabled = self.pay_now_check.isChecked() if hasattr(self, 'pay_now_check') else False
        if hasattr(self, 'payment_frame'):
            self.payment_frame.setVisible(enabled)

    def set_full_payment_amount(self):
        total_usd = sum(float(item.get('total', 0) or 0) for item in self.items)
        self.payment_amount_spin.setValue(total_usd)


class PurchaseOrderDetailsDialog(QDialog):
    """
    Dialog for viewing purchase order details with status actions.
    
    Requirements: 12.2 - Display full PO with items on double-click
    Requirements: 12.4 - Add approve, mark ordered, receive goods actions
    """
    
    approve_requested = Signal(dict)  # Emits order data when approve is requested
    mark_ordered_requested = Signal(dict)  # Emits order data when mark ordered is requested
    receive_requested = Signal(dict)  # Emits order data when receive goods is requested
    payment_requested = Signal(dict)
    
    def __init__(self, order: dict, parent=None):
        """
        Initialize the purchase order details dialog.
        
        Args:
            order: Full purchase order data with items
        """
        super().__init__(parent)
        self.order = order
        
        self.setWindowTitle(f"تفاصيل أمر الشراء - {order.get('order_number', '')}")
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        self.setup_ui()
    
    def setup_ui(self):
        """Initialize dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header with order info
        header_frame = QFrame()
        header_frame.setStyleSheet(f"background-color: {Colors.LIGHT_BG}; border-radius: 8px; padding: 16px;")
        header_layout = QVBoxLayout(header_frame)
        header_layout.setSpacing(12)
        
        # Order number and status
        title_row = QHBoxLayout()
        order_label = QLabel(f"📋 أمر شراء رقم: {self.order.get('order_number', '')}")
        order_label.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_H2, QFont.Bold))
        title_row.addWidget(order_label)
        
        status = self.order.get('status', '')
        status_display = self.order.get('status_display', status)
        status_label = QLabel(status_display)
        status_label.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_BODY, QFont.Bold))
        
        # Color code status
        status_colors = {
            'draft': Colors.WARNING,
            'approved': Colors.INFO,
            'ordered': Colors.PRIMARY,
            'partial': Colors.WARNING,
            'received': Colors.SUCCESS,
            'cancelled': Colors.DANGER,
        }
        status_color = status_colors.get(status, Colors.LIGHT_TEXT)
        status_label.setStyleSheet(f"""
            background-color: {status_color}20;
            color: {status_color};
            padding: 4px 12px;
            border-radius: 4px;
        """)
        title_row.addWidget(status_label)
        title_row.addStretch()
        header_layout.addLayout(title_row)
        
        # Order details grid
        details_grid = QHBoxLayout()
        details_grid.setSpacing(32)
        
        # Left column
        left_col = QVBoxLayout()
        left_col.setSpacing(8)
        left_col.addWidget(QLabel(f"🏢 المورد: {self.order.get('supplier_name', '')}"))
        left_col.addWidget(QLabel(f"📅 تاريخ الطلب: {self.order.get('order_date', '')}"))
        if self.order.get('expected_date'):
            left_col.addWidget(QLabel(f"📆 التسليم المتوقع: {self.order.get('expected_date', '')}"))
        warehouse_name = self.order.get('warehouse_name', self.order.get('warehouse', {}).get('name', ''))
        left_col.addWidget(QLabel(f"🏭 المستودع: {warehouse_name}"))
        details_grid.addLayout(left_col)
        
        # Right column - amounts
        right_col = QVBoxLayout()
        right_col.setSpacing(8)
        total = float(self.order.get('total_amount_usd', self.order.get('total_amount', 0)) or 0)
        paid = float(self.order.get('paid_amount_usd', self.order.get('paid_amount', 0)) or 0)
        remaining = float(self.order.get('remaining_amount_usd', total - paid) or 0)
        
        total_label = QLabel(f"💰 الإجمالي: {config.format_usd(total)}")
        total_label.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_BODY, QFont.Bold))
        right_col.addWidget(total_label)
        
        paid_label = QLabel(f"✅ المدفوع: {config.format_usd(paid)}")
        paid_label.setStyleSheet(f"color: {Colors.SUCCESS};")
        right_col.addWidget(paid_label)
        
        remaining_label = QLabel(f"⏳ المتبقي: {config.format_usd(remaining)}")
        if remaining > 0:
            remaining_label.setStyleSheet(f"color: {Colors.WARNING};")
        right_col.addWidget(remaining_label)
        
        details_grid.addLayout(right_col)
        details_grid.addStretch()
        header_layout.addLayout(details_grid)
        
        layout.addWidget(header_frame)
        
        # Items table
        items_label = QLabel("📦 بنود أمر الشراء")
        items_label.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_H3, QFont.Bold))
        layout.addWidget(items_label)
        
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(7)
        self.items_table.setHorizontalHeaderLabels([
            'المنتج', 'الوحدة', 'الكمية', 'المستلم', 'المتبقي', 'السعر', 'الإجمالي'
        ])
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.items_table.verticalHeader().setVisible(False)
        self.items_table.setAlternatingRowColors(True)
        self.items_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.items_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        # Populate items
        items = self.order.get('items', [])
        self.items_table.setRowCount(len(items))
        
        for row, item in enumerate(items):
            self.items_table.setItem(row, 0, QTableWidgetItem(item.get('product_name', '')))
            unit_name = item.get('unit_name', '') or item.get('unit_symbol', '') or '-'
            self.items_table.setItem(row, 1, QTableWidgetItem(unit_name))
            quantity = float(item.get('quantity', 0))
            received = float(item.get('received_quantity', 0))
            remaining_qty = quantity - received
            self.items_table.setItem(row, 2, QTableWidgetItem(f"{quantity:.2f}"))
            self.items_table.setItem(row, 3, QTableWidgetItem(f"{received:.2f}"))
            self.items_table.setItem(row, 4, QTableWidgetItem(f"{remaining_qty:.2f}"))
            self.items_table.setItem(row, 5, QTableWidgetItem(f"{float(item.get('unit_price', 0)):,.2f}"))
            self.items_table.setItem(row, 6, QTableWidgetItem(f"{float(item.get('total', 0)):,.2f}"))
        
        layout.addWidget(self.items_table)

        payments = self.order.get('payments', [])
        if payments:
            payments_label = QLabel("💸 سجل الدفعات")
            payments_label.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_H3, QFont.Bold))
            layout.addWidget(payments_label)

            payments_table = QTableWidget()
            payments_table.setColumnCount(5)
            payments_table.setHorizontalHeaderLabels([
                'رقم السند', 'التاريخ', 'المبلغ', 'الطريقة', 'المرجع'
            ])
            payments_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            payments_table.verticalHeader().setVisible(False)
            payments_table.setAlternatingRowColors(True)
            payments_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            payments_table.setSelectionBehavior(QAbstractItemView.SelectRows)

            payments_table.setRowCount(len(payments))
            for row, p in enumerate(payments):
                payments_table.setItem(row, 0, QTableWidgetItem(str(p.get('payment_number', ''))))
                payments_table.setItem(row, 1, QTableWidgetItem(str(p.get('payment_date', ''))))
                amount_usd = float(p.get('amount_usd', p.get('amount', 0)) or 0)
                payments_table.setItem(row, 2, QTableWidgetItem(config.format_usd(amount_usd)))
                payments_table.setItem(row, 3, QTableWidgetItem(str(p.get('payment_method_display', p.get('payment_method', '')))))
                payments_table.setItem(row, 4, QTableWidgetItem(str(p.get('reference', '') or '')))

            layout.addWidget(payments_table)
        
        # Notes if any
        notes = self.order.get('notes', '')
        if notes:
            notes_frame = QFrame()
            notes_frame.setStyleSheet(f"background-color: {Colors.LIGHT_BG}; border-radius: 8px; padding: 12px;")
            notes_layout = QVBoxLayout(notes_frame)
            notes_label = QLabel("📝 ملاحظات:")
            notes_label.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_BODY, QFont.Bold))
            notes_layout.addWidget(notes_label)
            notes_text = QLabel(notes)
            notes_text.setWordWrap(True)
            notes_layout.addWidget(notes_text)
            layout.addWidget(notes_frame)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        status = self.order.get('status', '')
        
        # Requirements: 12.4 - Add approve action for draft orders
        if status == 'draft':
            approve_btn = QPushButton("✅ اعتماد")
            approve_btn.setProperty("class", "success")
            approve_btn.setMinimumHeight(44)
            approve_btn.clicked.connect(self.request_approve)
            buttons_layout.addWidget(approve_btn)
        
        # Requirements: 12.4 - Add mark ordered action for approved orders
        if status == 'approved':
            ordered_btn = QPushButton("📤 تم الطلب")
            ordered_btn.setProperty("class", "primary")
            ordered_btn.setMinimumHeight(44)
            ordered_btn.clicked.connect(self.request_mark_ordered)
            buttons_layout.addWidget(ordered_btn)
        
        # Requirements: 12.4 - Add receive goods action for approved/ordered/partial orders
        if status in ['approved', 'ordered', 'partial']:
            receive_btn = QPushButton("📥 استلام بضاعة")
            receive_btn.setProperty("class", "primary")
            receive_btn.setMinimumHeight(44)
            receive_btn.clicked.connect(self.request_receive)
            buttons_layout.addWidget(receive_btn)

        remaining_usd = float(self.order.get('remaining_amount_usd', 0) or 0)
        if remaining_usd > 0:
            pay_btn = QPushButton("💸 تسجيل دفعة")
            pay_btn.setProperty("class", "success")
            pay_btn.setMinimumHeight(44)
            pay_btn.clicked.connect(self.request_payment)
            buttons_layout.addWidget(pay_btn)
        
        buttons_layout.addStretch()
        
        close_btn = QPushButton("إغلاق")
        close_btn.setProperty("class", "secondary")
        close_btn.setMinimumHeight(44)
        close_btn.setMinimumWidth(100)
        close_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(close_btn)
        
        layout.addLayout(buttons_layout)
    
    def request_approve(self):
        """Request to approve this order."""
        if ConfirmDialog(
            "اعتماد أمر الشراء",
            f"هل أنت متأكد من اعتماد أمر الشراء '{self.order.get('order_number')}'؟",
            danger=False,
            parent=self
        ).exec():
            self.approve_requested.emit(self.order)
            self.accept()
    
    def request_mark_ordered(self):
        """Request to mark this order as ordered."""
        if ConfirmDialog(
            "تحديث حالة أمر الشراء",
            f"هل أنت متأكد من تحديث حالة أمر الشراء '{self.order.get('order_number')}' إلى 'تم الطلب'؟",
            danger=False,
            parent=self
        ).exec():
            self.mark_ordered_requested.emit(self.order)
            self.accept()
    
    def request_receive(self):
        """Request to receive goods for this order."""
        self.receive_requested.emit(self.order)
        self.accept()

    def request_payment(self):
        self.payment_requested.emit(self.order)
        self.accept()


class SupplierPaymentDialog(QDialog):

    saved = Signal(dict)

    def __init__(self, order: dict = None, parent=None):
        super().__init__(parent)
        self.order = order or {}
        self.suppliers_cache = []
        self._updating_fx = False
        self.setWindowTitle("تسجيل دفعة مورد")
        self.setMinimumWidth(520)
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("💸 تسجيل دفعة مورد")
        title.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_H2, QFont.Bold))
        layout.addWidget(title)

        frame = Card()
        frame_layout = QGridLayout(frame)
        frame_layout.setSpacing(10)

        frame_layout.addWidget(QLabel("المورد *"), 0, 0)
        self.supplier_combo = QComboBox()
        frame_layout.addWidget(self.supplier_combo, 0, 1)

        frame_layout.addWidget(QLabel("أمر الشراء"), 0, 2)
        self.purchase_order_label = QLabel("-")
        frame_layout.addWidget(self.purchase_order_label, 0, 3)

        frame_layout.addWidget(QLabel("تاريخ الدفع *"), 1, 0)
        self.payment_date_edit = QDateEdit()
        self.payment_date_edit.setCalendarPopup(True)
        self.payment_date_edit.setDate(QDate.currentDate())
        frame_layout.addWidget(self.payment_date_edit, 1, 1)

        frame_layout.addWidget(QLabel("عملة الدفع *"), 1, 2)
        self.currency_combo = QComboBox()
        self.currency_combo.addItem("USD", "USD")
        self.currency_combo.addItem("ل.س قديم", "SYP_OLD")
        self.currency_combo.addItem("ل.س جديد", "SYP_NEW")
        frame_layout.addWidget(self.currency_combo, 1, 3)

        frame_layout.addWidget(QLabel("المبلغ *"), 2, 0)
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0.01, 999999999999)
        self.amount_spin.setDecimals(2)
        frame_layout.addWidget(self.amount_spin, 2, 1)

        frame_layout.addWidget(QLabel("طريقة الدفع *"), 2, 2)
        self.method_combo = QComboBox()
        self.method_combo.addItem("نقداً", "cash")
        self.method_combo.addItem("تحويل بنكي", "bank")
        self.method_combo.addItem("شيك", "check")
        self.method_combo.addItem("بطاقة ائتمان", "credit")
        frame_layout.addWidget(self.method_combo, 2, 3)

        frame_layout.addWidget(QLabel("تاريخ سعر الصرف"), 3, 0)
        self.fx_rate_date_edit = QDateEdit()
        self.fx_rate_date_edit.setCalendarPopup(True)
        self.fx_rate_date_edit.setDate(QDate.currentDate())
        frame_layout.addWidget(self.fx_rate_date_edit, 3, 1)

        frame_layout.addWidget(QLabel("USD → ل.س قديم"), 3, 2)
        self.usd_to_syp_old_snapshot = QDoubleSpinBox()
        self.usd_to_syp_old_snapshot.setRange(0, 999999999999)
        self.usd_to_syp_old_snapshot.setDecimals(6)
        frame_layout.addWidget(self.usd_to_syp_old_snapshot, 3, 3)

        frame_layout.addWidget(QLabel("USD → ل.س جديد"), 4, 2)
        self.usd_to_syp_new_snapshot = QDoubleSpinBox()
        self.usd_to_syp_new_snapshot.setRange(0, 999999999999)
        self.usd_to_syp_new_snapshot.setDecimals(6)
        frame_layout.addWidget(self.usd_to_syp_new_snapshot, 4, 3)

        frame_layout.addWidget(QLabel("المرجع"), 5, 0)
        self.reference_edit = QLineEdit()
        frame_layout.addWidget(self.reference_edit, 5, 1)

        frame_layout.addWidget(QLabel("ملاحظات"), 5, 2)
        self.notes_edit = QLineEdit()
        frame_layout.addWidget(self.notes_edit, 5, 3)

        layout.addWidget(frame)

        self.usd_to_syp_old_snapshot.valueChanged.connect(self._on_old_fx_changed)
        self.usd_to_syp_new_snapshot.valueChanged.connect(self._on_new_fx_changed)
        self.currency_combo.currentIndexChanged.connect(self._on_currency_changed)
        self._on_currency_changed()

        btns = QHBoxLayout()
        save_btn = QPushButton("✅ حفظ")
        save_btn.setProperty("class", "success")
        save_btn.setMinimumHeight(44)
        save_btn.clicked.connect(self.save)
        btns.addWidget(save_btn)
        btns.addStretch()
        cancel_btn = QPushButton("إلغاء")
        cancel_btn.setProperty("class", "secondary")
        cancel_btn.setMinimumHeight(44)
        cancel_btn.clicked.connect(self.reject)
        btns.addWidget(cancel_btn)
        layout.addLayout(btns)

    def load_data(self):
        response = api.get_suppliers()
        if isinstance(response, dict) and 'results' in response:
            self.suppliers_cache = response['results']
        else:
            self.suppliers_cache = response if isinstance(response, list) else []

        self.supplier_combo.clear()
        self.supplier_combo.addItem("اختر المورد...", None)
        for s in self.suppliers_cache:
            self.supplier_combo.addItem(s.get('name', ''), s.get('id'))

        supplier_id = self.order.get('supplier')
        if supplier_id:
            for i in range(self.supplier_combo.count()):
                if self.supplier_combo.itemData(i) == supplier_id:
                    self.supplier_combo.setCurrentIndex(i)
                    self.supplier_combo.setEnabled(False)
                    break

        po_number = self.order.get('order_number')
        if po_number:
            self.purchase_order_label.setText(str(po_number))

    def _on_currency_changed(self):
        currency = self.currency_combo.currentData()
        fx_enabled = currency != 'USD'
        self.fx_rate_date_edit.setEnabled(fx_enabled)
        self.usd_to_syp_old_snapshot.setEnabled(fx_enabled)
        self.usd_to_syp_new_snapshot.setEnabled(fx_enabled)

    def _on_old_fx_changed(self, value: float):
        if self._updating_fx:
            return
        if value and value > 0 and (self.usd_to_syp_new_snapshot.value() or 0) <= 0:
            self._updating_fx = True
            self.usd_to_syp_new_snapshot.setValue(value / 100)
            self._updating_fx = False

    def _on_new_fx_changed(self, value: float):
        if self._updating_fx:
            return
        if value and value > 0 and (self.usd_to_syp_old_snapshot.value() or 0) <= 0:
            self._updating_fx = True
            self.usd_to_syp_old_snapshot.setValue(value * 100)
            self._updating_fx = False

    def validate(self) -> bool:
        supplier_id = self.supplier_combo.currentData()
        if not supplier_id:
            MessageDialog.warning(self, "تنبيه", "يجب اختيار المورد")
            return False

        amount = float(self.amount_spin.value() or 0)
        if amount <= 0:
            MessageDialog.warning(self, "تنبيه", "يجب إدخال مبلغ صحيح")
            return False

        if self.order.get('id'):
            remaining_usd = float(self.order.get('remaining_amount_usd', 0) or 0)
            currency = self.currency_combo.currentData()
            fx_old = float(self.usd_to_syp_old_snapshot.value() or 0)
            fx_new = float(self.usd_to_syp_new_snapshot.value() or 0)
            amount_usd = amount
            if currency == 'SYP_OLD':
                amount_usd = (amount / fx_old) if fx_old else amount
            elif currency == 'SYP_NEW':
                amount_usd = (amount / fx_new) if fx_new else amount
            if amount_usd > remaining_usd:
                MessageDialog.warning(self, "تنبيه", "مبلغ الدفعة أكبر من المبلغ المتبقي")
                return False

        return True

    def get_data(self) -> dict:
        fx_old = float(self.usd_to_syp_old_snapshot.value() or 0)
        fx_new = float(self.usd_to_syp_new_snapshot.value() or 0)
        data = {
            'supplier': self.supplier_combo.currentData(),
            'purchase_order': self.order.get('id') if self.order.get('id') else None,
            'payment_date': self.payment_date_edit.date().toString('yyyy-MM-dd'),
            'transaction_currency': self.currency_combo.currentData(),
            'amount': float(self.amount_spin.value()),
            'payment_method': self.method_combo.currentData(),
            'fx_rate_date': self.fx_rate_date_edit.date().toString('yyyy-MM-dd'),
            'usd_to_syp_old_snapshot': fx_old if fx_old > 0 else None,
            'usd_to_syp_new_snapshot': fx_new if fx_new > 0 else None,
            'reference': self.reference_edit.text().strip() or None,
            'notes': self.notes_edit.text().strip() or None,
        }
        if not data['purchase_order']:
            data.pop('purchase_order')
        if data.get('transaction_currency') == 'USD':
            data.pop('fx_rate_date', None)
            data.pop('usd_to_syp_old_snapshot', None)
            data.pop('usd_to_syp_new_snapshot', None)
        return data

    def save(self):
        if self.validate():
            self.saved.emit(self.get_data())
            self.accept()


class GoodsReceiptDialog(QDialog):
    """
    Dialog for receiving goods against a purchase order.
    
    Requirements: 12.4, 12.5 - Receive goods action and stock update
    """
    
    saved = Signal(dict)  # Emits receipt data
    
    def __init__(self, order: dict, parent=None):
        """
        Initialize the goods receipt dialog.
        
        Args:
            order: Full purchase order data with items
        """
        super().__init__(parent)
        self.order = order
        self.receipt_items = []
        
        self.setWindowTitle(f"استلام بضاعة - {order.get('order_number', '')}")
        self.setMinimumWidth(800)
        self.setMinimumHeight(500)
        self.setup_ui()
    
    def setup_ui(self):
        """Initialize dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header_label = QLabel(f"📥 استلام بضاعة لأمر الشراء: {self.order.get('order_number', '')}")
        header_label.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_H2, QFont.Bold))
        layout.addWidget(header_label)
        
        # Receipt info
        info_frame = QFrame()
        info_frame.setStyleSheet(f"background-color: {Colors.LIGHT_BG}; border-radius: 8px; padding: 12px;")
        info_layout = QHBoxLayout(info_frame)
        
        info_layout.addWidget(QLabel("تاريخ الاستلام:"))
        self.received_date = QDateEdit()
        self.received_date.setCalendarPopup(True)
        self.received_date.setDate(QDate.currentDate())
        info_layout.addWidget(self.received_date)
        
        info_layout.addWidget(QLabel("رقم فاتورة المورد:"))
        self.supplier_invoice = QLineEdit()
        self.supplier_invoice.setPlaceholderText("اختياري")
        info_layout.addWidget(self.supplier_invoice)
        
        info_layout.addStretch()
        layout.addWidget(info_frame)
        
        # Items table
        items_label = QLabel("📦 البنود للاستلام")
        items_label.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_H3, QFont.Bold))
        layout.addWidget(items_label)
        
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(6)
        self.items_table.setHorizontalHeaderLabels([
            'المنتج', 'الكمية المطلوبة', 'المستلم سابقاً', 'المتبقي', 'الكمية للاستلام', 'ملاحظات'
        ])
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.items_table.verticalHeader().setVisible(False)
        self.items_table.setAlternatingRowColors(True)
        
        # Populate items
        items = self.order.get('items', [])
        self.items_table.setRowCount(len(items))
        
        for row, item in enumerate(items):
            quantity = float(item.get('quantity', 0))
            received = float(item.get('received_quantity', 0))
            remaining = quantity - received
            
            self.items_table.setItem(row, 0, QTableWidgetItem(item.get('product_name', '')))
            self.items_table.setItem(row, 1, QTableWidgetItem(f"{quantity:.2f}"))
            self.items_table.setItem(row, 2, QTableWidgetItem(f"{received:.2f}"))
            self.items_table.setItem(row, 3, QTableWidgetItem(f"{remaining:.2f}"))
            
            # Quantity to receive spinner
            qty_spin = QDoubleSpinBox()
            qty_spin.setRange(0, remaining)
            qty_spin.setValue(remaining)  # Default to remaining quantity
            qty_spin.setDecimals(2)
            self.items_table.setCellWidget(row, 4, qty_spin)
            
            # Notes
            notes_edit = QLineEdit()
            notes_edit.setPlaceholderText("ملاحظات...")
            self.items_table.setCellWidget(row, 5, notes_edit)
            
            # Store item reference
            self.receipt_items.append({
                'po_item_id': item.get('id'),
                'product_name': item.get('product_name', ''),
                'remaining': remaining,
                'qty_spin': qty_spin,
                'notes_edit': notes_edit
            })
        
        layout.addWidget(self.items_table)
        
        # Notes
        notes_layout = QHBoxLayout()
        notes_layout.addWidget(QLabel("ملاحظات عامة:"))
        self.notes_edit = QLineEdit()
        self.notes_edit.setPlaceholderText("ملاحظات إضافية...")
        notes_layout.addWidget(self.notes_edit)
        layout.addLayout(notes_layout)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        save_btn = QPushButton("✅ تأكيد الاستلام")
        save_btn.setProperty("class", "success")
        save_btn.setMinimumHeight(44)
        save_btn.clicked.connect(self.save)
        buttons_layout.addWidget(save_btn)
        
        buttons_layout.addStretch()
        
        cancel_btn = QPushButton("إلغاء")
        cancel_btn.setProperty("class", "secondary")
        cancel_btn.setMinimumHeight(44)
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(buttons_layout)
    
    def validate(self) -> bool:
        """Validate receipt data."""
        # Check if at least one item has quantity > 0
        has_items = False
        for item in self.receipt_items:
            qty = item['qty_spin'].value()
            if qty > 0:
                has_items = True
                break
        
        if not has_items:
            MessageDialog.warning(self, "تنبيه", "يجب تحديد كمية واحدة على الأقل للاستلام")
            return False
        
        return True
    
    def get_data(self) -> dict:
        """Get receipt data as dictionary."""
        items = []
        for item in self.receipt_items:
            qty = item['qty_spin'].value()
            if qty > 0:
                items.append({
                    'po_item_id': item['po_item_id'],
                    'quantity': qty,
                    'notes': item['notes_edit'].text().strip() or None
                })
        
        return {
            'order_id': self.order.get('id'),
            'received_date': self.received_date.date().toString('yyyy-MM-dd'),
            'supplier_invoice_no': self.supplier_invoice.text().strip() or None,
            'notes': self.notes_edit.text().strip() or None,
            'items': items
        }
    
    def save(self):
        """Emit saved signal with receipt data."""
        if self.validate():
            self.saved.emit(self.get_data())
            self.accept()
