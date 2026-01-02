"""
Payments View - إدارة المدفوعات

This module provides the UI for viewing and managing customer payments.
It supports:
- Payments list with DataTable
- Payment creation with invoice allocation
- Payment details dialog
- Filtering by customer, date range, and payment method

Requirements: 13.1, 13.2, 13.3, 13.4, 13.5
"""
from decimal import Decimal
from typing import List, Dict, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QComboBox, QDateEdit,
    QDialog, QGridLayout, QDoubleSpinBox, QTextEdit,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QGroupBox, QCheckBox, QSplitter
)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QFont, QColor

from ...config import Colors, Fonts, config
from ...widgets.tables import DataTable
from ...widgets.cards import Card
from ...widgets.unit_selector import UnitSelectorComboBox
from ...widgets.dialogs import MessageDialog, ConfirmDialog
from ...services.api import api, ApiException
from ...utils.error_handler import handle_ui_error


class PaymentsView(QWidget):
    """
    Payments management view.
    
    Displays payments list with filtering and supports:
    - Viewing all payments
    - Creating new payments with allocation
    - Viewing payment details
    - Filtering by customer, date range, payment method
    
    Requirements: 13.1, 13.2, 13.3, 13.4, 13.5
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.customers_cache: List[Dict] = []
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize payments view UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("إدارة المدفوعات")
        title.setProperty("class", "title")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)
        
        # Requirements: 13.5 - Filters section
        filters_frame = QFrame()
        filters_frame.setStyleSheet(f"background-color: {Colors.LIGHT_BG}; border-radius: 8px; padding: 12px;")
        filters_layout = QHBoxLayout(filters_frame)
        filters_layout.setSpacing(16)
        
        # Customer filter
        filters_layout.addWidget(QLabel("العميل:"))
        self.customer_filter = QComboBox()
        self.customer_filter.addItem("الكل", "")
        self.customer_filter.setMinimumWidth(180)
        self.customer_filter.setEditable(True)
        self.customer_filter.setInsertPolicy(QComboBox.NoInsert)
        filters_layout.addWidget(self.customer_filter)
        
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
        
        # Payment method filter
        filters_layout.addWidget(QLabel("طريقة الدفع:"))
        self.method_filter = QComboBox()
        self.method_filter.addItem("الكل", "")
        self.method_filter.addItem("نقداً", "cash")
        self.method_filter.addItem("بطاقة", "card")
        self.method_filter.addItem("تحويل بنكي", "bank")
        self.method_filter.addItem("شيك", "check")
        self.method_filter.addItem("ائتمان", "credit")
        self.method_filter.setMinimumWidth(120)
        filters_layout.addWidget(self.method_filter)
        
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
        
        # Requirements: 13.1 - Payments table
        columns = [
            {'key': 'payment_number', 'label': 'رقم السند', 'type': 'text'},
            {'key': 'customer_name', 'label': 'العميل', 'type': 'text'},
            {'key': 'payment_date', 'label': 'التاريخ', 'type': 'date'},
            {'key': 'amount', 'label': 'المبلغ', 'type': 'currency'},
            {'key': 'amount_usd', 'label': 'المبلغ (عرض)', 'type': 'currency'},
            {'key': 'transaction_currency', 'label': 'العملة', 'type': 'text'},
            {'key': 'payment_method_display', 'label': 'طريقة الدفع', 'type': 'text'},
        ]
        
        self.table = DataTable(columns, actions=['view'])
        self.table.add_btn.setText("➕ دفعة جديدة")
        self.table.add_btn.clicked.connect(self.add_payment)
        self.table.action_clicked.connect(self.on_action)
        self.table.row_double_clicked.connect(self.view_payment_details)
        self.table.page_changed.connect(self.on_page_changed)
        self.table.sort_changed.connect(self.on_sort_changed)
        
        layout.addWidget(self.table)
    
    @handle_ui_error
    def refresh(self):
        """Refresh payments data from API."""
        # Load customers for filter dropdown
        self._load_customers()
        
        # Build params from filters
        params = self._build_params()
        
        response = api.get_payments(params)
        if isinstance(response, dict):
            payments = response.get('results', [])
            total = response.get('count', len(payments))
        else:
            payments = response if isinstance(response, list) else []
            total = len(payments)
        
        self.table.set_data(payments, total)
    
    def _load_customers(self):
        """Load customers for filter dropdown."""
        try:
            response = api.get_customers()
            if isinstance(response, dict) and 'results' in response:
                self.customers_cache = response['results']
            else:
                self.customers_cache = response if isinstance(response, list) else []
            
            # Update customer filter combo (preserve current selection)
            current_customer = self.customer_filter.currentData()
            self.customer_filter.clear()
            self.customer_filter.addItem("الكل", "")
            for customer in self.customers_cache:
                display_text = f"{customer.get('name', '')} ({customer.get('code', '')})"
                self.customer_filter.addItem(display_text, customer.get('id'))
            
            # Restore selection if possible
            if current_customer:
                for i in range(self.customer_filter.count()):
                    if self.customer_filter.itemData(i) == current_customer:
                        self.customer_filter.setCurrentIndex(i)
                        break
        except ApiException:
            pass  # Silently fail - customers will just not be loaded
    
    def _build_params(self) -> dict:
        """Build API parameters from filters."""
        params = self.table.get_pagination_params()
        params.update(self.table.get_sort_params())
        
        # Customer filter
        customer_id = self.customer_filter.currentData()
        if customer_id:
            params['customer'] = customer_id
        
        # Date range
        date_from = self.date_from.date().toString('yyyy-MM-dd')
        date_to = self.date_to.date().toString('yyyy-MM-dd')
        params['payment_date__gte'] = date_from
        params['payment_date__lte'] = date_to
        
        # Payment method filter
        method = self.method_filter.currentData()
        if method:
            params['payment_method'] = method
        
        return params
    
    def apply_filters(self):
        """Apply filters and refresh."""
        self.table.current_page = 1
        self.refresh()
    
    def clear_filters(self):
        """Clear all filters."""
        self.customer_filter.setCurrentIndex(0)
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.date_to.setDate(QDate.currentDate())
        self.method_filter.setCurrentIndex(0)
        self.table.current_page = 1
        self.refresh()
    
    def on_page_changed(self, page: int, page_size: int):
        """Handle page change."""
        self.refresh()
    
    def on_sort_changed(self, column: str, order: str):
        """Handle sort change."""
        self.refresh()
    
    def on_action(self, action: str, row: int, data: dict):
        """Handle table action."""
        if action == 'view':
            self.view_payment_details(row, data)
        elif action == 'add':
            self.add_payment()
    
    def add_payment(self):
        """
        Open dialog to create new payment.
        
        Requirements: 13.2 - Payment creation with allocation
        """
        dialog = PaymentCreateDialog(parent=self)
        dialog.saved.connect(self.on_payment_saved)
        dialog.exec()
    
    @handle_ui_error
    def on_payment_saved(self, data: dict):
        """Handle payment saved."""
        MessageDialog.success(
            self, 
            "نجاح", 
            f"تم تسجيل الدفعة بنجاح\nرقم السند: {data.get('payment_number', 'N/A')}"
        )
        self.refresh()
    
    @handle_ui_error
    def view_payment_details(self, row: int, data: dict):
        """
        View payment details.
        
        Requirements: 13.3 - Display payment details on double-click
        """
        payment_id = data.get('id')
        if payment_id:
            try:
                payment = api.get_payment(payment_id)
                dialog = PaymentDetailsDialog(payment, parent=self)
                dialog.exec()
            except ApiException as e:
                MessageDialog.error(self, "خطأ", f"فشل في تحميل تفاصيل الدفعة: {str(e)}")




class PaymentCreateDialog(QDialog):
    """
    Dialog for creating a new payment with invoice allocation.
    
    Requirements: 13.2, 13.4
    - Create payment form with customer, amount, method
    - Add invoice allocation section
    - Support multiple invoice allocation
    """
    
    saved = Signal(dict)  # Emits the created payment data
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.customers_cache: List[Dict] = []
        self.unpaid_invoices: List[Dict] = []
        self.selected_customer: Optional[Dict] = None
        self.allocations: Dict[int, Decimal] = {}  # invoice_id -> allocated amount
        self._fx_syncing = False
        
        self.setWindowTitle("تسجيل دفعة جديدة")
        self.setMinimumWidth(900)
        self.setMinimumHeight(600)
        self.setup_ui()
        self._load_customers()
    
    def setup_ui(self):
        """Initialize dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Main content splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel: Customer selection and invoices
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(16)
        
        # Customer selection section
        customer_group = QGroupBox("اختيار العميل")
        customer_layout = QVBoxLayout(customer_group)
        
        # Customer dropdown
        customer_row = QHBoxLayout()
        customer_label = QLabel("العميل:")
        customer_row.addWidget(customer_label)
        
        self.customer_combo = QComboBox()
        self.customer_combo.setMinimumWidth(250)
        self.customer_combo.setPlaceholderText("اختر العميل...")
        self.customer_combo.currentIndexChanged.connect(self.on_customer_selected)
        customer_row.addWidget(self.customer_combo, 1)
        
        customer_layout.addLayout(customer_row)
        
        # Customer balance display
        balance_frame = QFrame()
        balance_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.LIGHT_BG};
                border: 1px solid {Colors.LIGHT_BORDER};
                border-radius: 8px;
                padding: 12px;
            }}
        """)
        balance_layout = QGridLayout(balance_frame)
        balance_layout.setSpacing(8)
        
        balance_layout.addWidget(QLabel("الرصيد الحالي:"), 0, 0)
        self.current_balance_label = QLabel("0.00 ل.س")
        self.current_balance_label.setStyleSheet(f"font-weight: bold; color: {Colors.DANGER};")
        balance_layout.addWidget(self.current_balance_label, 0, 1)
        
        customer_layout.addWidget(balance_frame)
        left_layout.addWidget(customer_group)
        
        # Unpaid invoices section
        invoices_group = QGroupBox("الفواتير غير المسددة")
        invoices_layout = QVBoxLayout(invoices_group)
        
        # Invoices table
        self.invoices_table = QTableWidget()
        self.invoices_table.setColumnCount(6)
        self.invoices_table.setHorizontalHeaderLabels([
            '✓', 'رقم الفاتورة', 'التاريخ', 'المبلغ', 'المتبقي', 'المخصص'
        ])
        self.invoices_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.invoices_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.invoices_table.setColumnWidth(0, 40)
        self.invoices_table.verticalHeader().setVisible(False)
        self.invoices_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.invoices_table.setAlternatingRowColors(True)
        self.invoices_table.itemChanged.connect(self.on_invoice_selection_changed)
        
        invoices_layout.addWidget(self.invoices_table)
        
        # Select all / deselect all buttons
        select_buttons = QHBoxLayout()
        select_all_btn = QPushButton("تحديد الكل")
        select_all_btn.setProperty("class", "secondary")
        select_all_btn.clicked.connect(self.select_all_invoices)
        select_buttons.addWidget(select_all_btn)
        
        deselect_all_btn = QPushButton("إلغاء التحديد")
        deselect_all_btn.setProperty("class", "secondary")
        deselect_all_btn.clicked.connect(self.deselect_all_invoices)
        select_buttons.addWidget(deselect_all_btn)
        
        select_buttons.addStretch()
        invoices_layout.addLayout(select_buttons)
        
        left_layout.addWidget(invoices_group, 1)
        splitter.addWidget(left_panel)
        
        # Right panel: Payment details
        right_panel = Card()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(20, 20, 20, 20)
        right_layout.setSpacing(16)
        
        # Payment details section
        payment_title = QLabel("تفاصيل الدفعة")
        payment_title.setProperty("class", "h2")
        right_layout.addWidget(payment_title)
        
        # Payment date
        date_row = QHBoxLayout()
        date_row.addWidget(QLabel("تاريخ الدفع:"))
        self.payment_date = QDateEdit()
        self.payment_date.setCalendarPopup(True)
        self.payment_date.setDate(QDate.currentDate())
        self.payment_date.dateChanged.connect(self.load_fx_for_date)
        date_row.addWidget(self.payment_date)
        right_layout.addLayout(date_row)

        # Transaction currency
        currency_row = QHBoxLayout()
        currency_row.addWidget(QLabel("العملة:"))
        self.currency_combo = QComboBox()
        self.currency_combo.addItem("USD", "USD")
        self.currency_combo.addItem("الليرة القديمة", "SYP_OLD")
        self.currency_combo.addItem("الليرة الجديدة", "SYP_NEW")
        self.currency_combo.currentIndexChanged.connect(self.on_currency_changed)
        currency_row.addWidget(self.currency_combo)
        right_layout.addLayout(currency_row)

        # FX snapshot (only relevant for non-USD)
        fx_row = QHBoxLayout()
        fx_row.setSpacing(6)
        fx_row.addWidget(QLabel("FX:"))
        self.usd_to_syp_new_snapshot = QDoubleSpinBox()
        self.usd_to_syp_new_snapshot.setRange(0, 999999999999)
        self.usd_to_syp_new_snapshot.setDecimals(6)
        self.usd_to_syp_new_snapshot.setPrefix("1$=")
        self.usd_to_syp_new_snapshot.setSuffix(" جديد")
        self.usd_to_syp_new_snapshot.valueChanged.connect(self.on_fx_new_changed)
        fx_row.addWidget(self.usd_to_syp_new_snapshot, 1)

        self.usd_to_syp_old_snapshot = QDoubleSpinBox()
        self.usd_to_syp_old_snapshot.setRange(0, 99999999999999)
        self.usd_to_syp_old_snapshot.setDecimals(6)
        self.usd_to_syp_old_snapshot.setPrefix("1$=")
        self.usd_to_syp_old_snapshot.setSuffix(" قديم")
        self.usd_to_syp_old_snapshot.valueChanged.connect(self.on_fx_old_changed)
        fx_row.addWidget(self.usd_to_syp_old_snapshot, 1)
        right_layout.addLayout(fx_row)
        
        # Payment amount
        amount_row = QHBoxLayout()
        amount_row.addWidget(QLabel("مبلغ الدفع:"))
        self.payment_amount = QDoubleSpinBox()
        self.payment_amount.setMaximum(999999999)
        self.payment_amount.setDecimals(2)
        self.payment_amount.setSuffix("")
        self.payment_amount.valueChanged.connect(self.on_payment_amount_changed)
        amount_row.addWidget(self.payment_amount)
        right_layout.addLayout(amount_row)
        
        # Payment method
        method_row = QHBoxLayout()
        method_row.addWidget(QLabel("طريقة الدفع:"))
        self.payment_method = QComboBox()
        self.payment_method.addItem("نقداً", "cash")
        self.payment_method.addItem("بطاقة", "card")
        self.payment_method.addItem("تحويل بنكي", "bank")
        self.payment_method.addItem("شيك", "check")
        method_row.addWidget(self.payment_method)
        right_layout.addLayout(method_row)
        
        # Reference number
        ref_row = QHBoxLayout()
        ref_row.addWidget(QLabel("رقم المرجع:"))
        self.reference_input = QLineEdit()
        self.reference_input.setPlaceholderText("رقم الشيك / التحويل (اختياري)")
        ref_row.addWidget(self.reference_input)
        right_layout.addLayout(ref_row)
        
        # Notes
        notes_label = QLabel("ملاحظات:")
        right_layout.addWidget(notes_label)
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(80)
        self.notes_input.setPlaceholderText("ملاحظات إضافية (اختياري)")
        right_layout.addWidget(self.notes_input)
        
        # Separator
        right_layout.addWidget(self._create_separator())
        
        # Auto-allocate checkbox
        self.auto_allocate_check = QCheckBox("توزيع تلقائي (الأقدم أولاً)")
        self.auto_allocate_check.setChecked(True)
        self.auto_allocate_check.stateChanged.connect(self.on_auto_allocate_changed)
        right_layout.addWidget(self.auto_allocate_check)
        
        # Summary
        right_layout.addWidget(self._create_separator())
        
        summary_layout = QGridLayout()
        summary_layout.addWidget(QLabel("إجمالي المحدد:"), 0, 0)
        self.selected_total_label = QLabel(config.format_usd(0))
        self.selected_total_label.setStyleSheet("font-weight: bold;")
        summary_layout.addWidget(self.selected_total_label, 0, 1)
        
        summary_layout.addWidget(QLabel("مبلغ الدفع:"), 1, 0)
        self.payment_total_label = QLabel(config.format_usd(0))
        self.payment_total_label.setStyleSheet(f"font-weight: bold; color: {Colors.PRIMARY};")
        summary_layout.addWidget(self.payment_total_label, 1, 1)
        
        summary_layout.addWidget(QLabel("الفرق:"), 2, 0)
        self.difference_label = QLabel(config.format_usd(0))
        summary_layout.addWidget(self.difference_label, 2, 1)
        
        right_layout.addLayout(summary_layout)
        
        # Error label
        self.error_label = QLabel()
        self.error_label.setStyleSheet(f"color: {Colors.DANGER};")
        self.error_label.setVisible(False)
        right_layout.addWidget(self.error_label)
        
        # Action buttons
        right_layout.addStretch()
        
        actions_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("إلغاء")
        cancel_btn.setProperty("class", "secondary")
        cancel_btn.clicked.connect(self.reject)
        actions_layout.addWidget(cancel_btn)
        
        actions_layout.addStretch()
        
        self.submit_btn = QPushButton("💰 تسجيل الدفعة")
        self.submit_btn.setProperty("class", "success")
        self.submit_btn.setMinimumHeight(50)
        self.submit_btn.clicked.connect(self.submit_payment)
        actions_layout.addWidget(self.submit_btn)
        
        right_layout.addLayout(actions_layout)
        
        splitter.addWidget(right_panel)
        
        # Set splitter sizes
        splitter.setSizes([500, 400])
        
        layout.addWidget(splitter, 1)

        self.on_currency_changed(self.currency_combo.currentIndex())
    
    def _create_separator(self) -> QFrame:
        """Create a horizontal separator line."""
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet(f"background-color: {Colors.LIGHT_BORDER};")
        return separator
    
    @handle_ui_error
    def _load_customers(self):
        """Load customers list from API."""
        response = api.get_customers()
        if isinstance(response, dict) and 'results' in response:
            self.customers_cache = response['results']
        else:
            self.customers_cache = response if isinstance(response, list) else []
        
        # Update combo box
        self.customer_combo.clear()
        self.customer_combo.addItem("-- اختر العميل --", None)
        
        for customer in self.customers_cache:
            balance_usd = float(customer.get('current_balance_usd', customer.get('current_balance', 0)) or 0)
            display_text = f"{customer.get('name', '')} - رصيد: {config.format_usd(balance_usd)}"
            self.customer_combo.addItem(display_text, customer)
    
    @handle_ui_error
    def on_customer_selected(self, index: int):
        """Handle customer selection change."""
        if index <= 0:
            self.selected_customer = None
            self._clear_customer_display()
            return
        
        customer = self.customer_combo.currentData()
        if not customer:
            return
        
        self.selected_customer = customer
        self._update_customer_display(customer)
        self._load_unpaid_invoices(customer.get('id'))
    
    def _update_customer_display(self, customer: Dict):
        """Update the customer balance display."""
        balance_usd = float(customer.get('current_balance_usd', 0) or 0)
        balance_tx = self._usd_to_transaction_amount(balance_usd)
        self.current_balance_label.setText(self._format_amount(balance_tx))
        
        # Color code the balance
        if balance_usd > 0:
            self.current_balance_label.setStyleSheet(f"font-weight: bold; color: {Colors.DANGER};")
        else:
            self.current_balance_label.setStyleSheet(f"font-weight: bold; color: {Colors.SUCCESS};")
    
    def _clear_customer_display(self):
        """Clear the customer balance display."""
        self.current_balance_label.setText("0.00 ل.س")
        self.current_balance_label.setStyleSheet(f"font-weight: bold; color: {Colors.LIGHT_TEXT};")
        self.invoices_table.setRowCount(0)
        self.unpaid_invoices = []
        self.allocations = {}
        self._update_summary()
    
    @handle_ui_error
    def _load_unpaid_invoices(self, customer_id: int):
        """Load unpaid invoices for the selected customer."""
        response = api.get_customer_unpaid_invoices(customer_id)
        
        if isinstance(response, dict) and 'results' in response:
            self.unpaid_invoices = response['results']
        elif isinstance(response, list):
            self.unpaid_invoices = response
        else:
            self.unpaid_invoices = []
        
        self._populate_invoices_table()
        self.allocations = {}
        self._update_summary()
    
    def _populate_invoices_table(self):
        """Populate the invoices table with unpaid invoices."""
        self.invoices_table.blockSignals(True)
        self.invoices_table.setRowCount(len(self.unpaid_invoices))
        
        for row, invoice in enumerate(self.unpaid_invoices):
            # Checkbox
            checkbox_item = QTableWidgetItem()
            checkbox_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            checkbox_item.setCheckState(Qt.Unchecked)
            checkbox_item.setData(Qt.UserRole, invoice.get('id'))
            self.invoices_table.setItem(row, 0, checkbox_item)
            
            # Invoice number
            self.invoices_table.setItem(row, 1, QTableWidgetItem(
                str(invoice.get('invoice_number', ''))
            ))
            
            # Invoice date
            self.invoices_table.setItem(row, 2, QTableWidgetItem(
                str(invoice.get('invoice_date', ''))
            ))
            
            # Total amount
            total_usd = float(invoice.get('total_amount_usd', invoice.get('total_amount', 0)) or 0)
            total = self._usd_to_transaction_amount(total_usd)
            self.invoices_table.setItem(row, 3, QTableWidgetItem(f"{total:,.2f}"))
            
            # Remaining amount
            remaining_usd = float(invoice.get('remaining_amount_usd', invoice.get('remaining_amount', 0)) or 0)
            remaining = self._usd_to_transaction_amount(remaining_usd)
            remaining_item = QTableWidgetItem(f"{remaining:,.2f}")
            remaining_item.setForeground(QColor(Colors.DANGER))
            self.invoices_table.setItem(row, 4, remaining_item)
            
            # Allocated amount (initially 0)
            allocated_item = QTableWidgetItem("0.00")
            if self.auto_allocate_check.isChecked():
                allocated_item.setFlags(allocated_item.flags() & ~Qt.ItemIsEditable)
            self.invoices_table.setItem(row, 5, allocated_item)
        
        self.invoices_table.blockSignals(False)
    
    def on_invoice_selection_changed(self, item: QTableWidgetItem):
        """Handle invoice checkbox state change."""
        if item is None:
            return

        if item.column() == 0:
            self._update_selected_total()
            if self.auto_allocate_check.isChecked():
                self._auto_allocate()
            self._update_allocation_display()
            self._update_summary()
            return

        if item.column() != 5 or self.auto_allocate_check.isChecked():
            return

        row = item.row()
        if not (0 <= row < len(self.unpaid_invoices)):
            return

        invoice = self.unpaid_invoices[row]
        invoice_id = invoice.get('id')
        if not invoice_id:
            return

        try:
            entered_tx = float(str(item.text()).replace(',', '').strip() or 0)
        except Exception:
            entered_tx = 0.0

        if entered_tx < 0:
            entered_tx = 0.0

        entered_usd = self._transaction_to_usd(entered_tx)
        remaining_usd = Decimal(str(invoice.get('remaining_amount_usd', invoice.get('remaining_amount', 0)) or 0))

        if entered_usd > remaining_usd:
            entered_usd = remaining_usd

        checkbox_item = self.invoices_table.item(row, 0)
        if checkbox_item and entered_usd > 0 and checkbox_item.checkState() != Qt.Checked:
            self.invoices_table.blockSignals(True)
            checkbox_item.setCheckState(Qt.Checked)
            self.invoices_table.blockSignals(False)

        if entered_usd <= 0:
            self.allocations.pop(int(invoice_id), None)
        else:
            self.allocations[int(invoice_id)] = entered_usd

        self.invoices_table.blockSignals(True)
        item.setText(f"{self._usd_to_transaction_amount(float(entered_usd)):,.2f}")
        self.invoices_table.blockSignals(False)

        self._update_selected_total()
        self._update_summary()
    
    def select_all_invoices(self):
        """Select all invoices in the table."""
        self.invoices_table.blockSignals(True)
        for row in range(self.invoices_table.rowCount()):
            item = self.invoices_table.item(row, 0)
            if item:
                item.setCheckState(Qt.Checked)
        self.invoices_table.blockSignals(False)
        
        self._update_selected_total()
        if self.auto_allocate_check.isChecked():
            self._auto_allocate()
        self._update_allocation_display()
        self._update_summary()
    
    def deselect_all_invoices(self):
        """Deselect all invoices in the table."""
        self.invoices_table.blockSignals(True)
        for row in range(self.invoices_table.rowCount()):
            item = self.invoices_table.item(row, 0)
            if item:
                item.setCheckState(Qt.Unchecked)
        self.invoices_table.blockSignals(False)
        
        self.allocations = {}
        self._update_selected_total()
        self._update_allocation_display()
        self._update_summary()
    
    def _get_selected_invoices(self) -> List[Dict]:
        """Get list of selected invoices."""
        selected = []
        for row in range(self.invoices_table.rowCount()):
            item = self.invoices_table.item(row, 0)
            if item and item.checkState() == Qt.Checked:
                if row < len(self.unpaid_invoices):
                    selected.append(self.unpaid_invoices[row])
        return selected
    
    def _update_selected_total(self):
        """Update the selected invoices total display."""
        selected = self._get_selected_invoices()
        total_usd = sum(float(inv.get('remaining_amount_usd', inv.get('remaining_amount', 0)) or 0) for inv in selected)
        self.selected_total_label.setText(self._format_amount_usd(total_usd))
    
    def on_payment_amount_changed(self, value: float):
        """Handle payment amount change."""
        self.payment_total_label.setText(self._format_amount(float(value or 0)))
        
        if self.auto_allocate_check.isChecked():
            self._auto_allocate()
        self._update_allocation_display()
        self._update_summary()
    
    def on_auto_allocate_changed(self, state: int):
        """Handle auto-allocate checkbox change."""
        if state == Qt.Checked:
            self._auto_allocate()
        else:
            self.allocations = {}

        self.invoices_table.blockSignals(True)
        try:
            editable = state != Qt.Checked
            for row in range(self.invoices_table.rowCount()):
                cell = self.invoices_table.item(row, 5)
                if cell is None:
                    continue
                if editable:
                    cell.setFlags(cell.flags() | Qt.ItemIsEditable)
                else:
                    cell.setFlags(cell.flags() & ~Qt.ItemIsEditable)
        finally:
            self.invoices_table.blockSignals(False)
        self._update_allocation_display()
        self._update_summary()
    
    def _auto_allocate(self):
        """
        Auto-allocate payment amount to selected invoices using FIFO strategy.
        
        Requirements: 13.4 - Support multiple invoice allocation
        """
        self.allocations = {}
        payment_amount_usd = self._transaction_to_usd(self.payment_amount.value())
        
        if payment_amount_usd <= 0:
            return
        
        # Get selected invoices sorted by date (oldest first - FIFO)
        selected = self._get_selected_invoices()
        selected_sorted = sorted(selected, key=lambda x: x.get('invoice_date', ''))
        
        remaining_payment = payment_amount_usd
        
        for invoice in selected_sorted:
            if remaining_payment <= 0:
                break
            
            invoice_id = invoice.get('id')
            invoice_remaining = Decimal(str(invoice.get('remaining_amount_usd', invoice.get('remaining_amount', 0)) or 0))
            
            # Allocate the minimum of remaining payment and invoice remaining
            allocation = min(remaining_payment, invoice_remaining)
            
            if allocation > 0:
                self.allocations[invoice_id] = allocation
                remaining_payment -= allocation
    
    def _update_allocation_display(self):
        """Update the allocation column in the invoices table."""
        self.invoices_table.blockSignals(True)
        
        for row in range(self.invoices_table.rowCount()):
            if row < len(self.unpaid_invoices):
                invoice_id = self.unpaid_invoices[row].get('id')
                allocated_usd = float(self.allocations.get(invoice_id, 0) or 0)
                allocated = self._usd_to_transaction_amount(allocated_usd)
                
                allocated_item = self.invoices_table.item(row, 5)
                if allocated_item:
                    allocated_item.setText(f"{allocated:,.2f}")
                    if allocated > 0:
                        allocated_item.setForeground(QColor(Colors.SUCCESS))
                    else:
                        allocated_item.setForeground(QColor(Colors.LIGHT_TEXT))
        
        self.invoices_table.blockSignals(False)
    
    def _update_summary(self):
        """Update the summary section."""
        payment_tx = float(self.payment_amount.value() or 0)
        payment_usd = float(self._transaction_to_usd(payment_tx))
        selected = self._get_selected_invoices()
        selected_total_usd = sum(float(inv.get('remaining_amount_usd', inv.get('remaining_amount', 0)) or 0) for inv in selected)
        
        difference_usd = payment_usd - selected_total_usd
        self.difference_label.setText(self._format_amount_usd(difference_usd))
        
        if difference_usd < 0:
            self.difference_label.setStyleSheet(f"color: {Colors.WARNING};")
        elif difference_usd > 0:
            self.difference_label.setStyleSheet(f"color: {Colors.INFO};")
        else:
            self.difference_label.setStyleSheet(f"color: {Colors.SUCCESS};")
    
    def _validate_payment(self) -> bool:
        """Validate payment data before submission."""
        self.error_label.setVisible(False)
        
        if not self.selected_customer:
            self.error_label.setText("يرجى اختيار العميل أولاً")
            self.error_label.setVisible(True)
            return False
        
        payment_amount = self.payment_amount.value()
        if payment_amount <= 0:
            self.error_label.setText("يرجى إدخال مبلغ الدفع")
            self.error_label.setVisible(True)
            return False

        currency = self.currency_combo.currentData() or 'USD'
        if currency != 'USD':
            fx_old = float(self.usd_to_syp_old_snapshot.value() or 0)
            fx_new = float(self.usd_to_syp_new_snapshot.value() or 0)
            if fx_old <= 0 or fx_new <= 0:
                self.error_label.setText("يرجى إدخال سعر الصرف")
                self.error_label.setVisible(True)
                return False
        
        return True
    
    @handle_ui_error
    def submit_payment(self):
        """Submit the payment to the API."""
        if not self._validate_payment():
            return
        
        # Build allocations list
        allocations_list = []
        for invoice_id, amount_usd in self.allocations.items():
            if amount_usd and amount_usd > 0:
                allocations_list.append({
                    'invoice_id': invoice_id,
                    'amount_usd': str(amount_usd)
                })
        
        # Build payment data
        tx_currency = self.currency_combo.currentData() or 'USD'
        fx_old = float(self.usd_to_syp_old_snapshot.value() or 0)
        fx_new = float(self.usd_to_syp_new_snapshot.value() or 0)
        payment_date = self.payment_date.date().toString('yyyy-MM-dd')
        payment_data = {
            'customer': self.selected_customer.get('id'),
            'payment_date': payment_date,
            'amount': str(self.payment_amount.value()),
            'transaction_currency': tx_currency,
            'fx_rate_date': payment_date,
            'usd_to_syp_old_snapshot': fx_old if fx_old > 0 else None,
            'usd_to_syp_new_snapshot': fx_new if fx_new > 0 else None,
            'payment_method': self.payment_method.currentData(),
            'reference': self.reference_input.text().strip() or None,
            'notes': self.notes_input.toPlainText().strip() or None,
            'allocations': allocations_list if allocations_list else None,
            'auto_allocate': self.auto_allocate_check.isChecked() and not allocations_list
        }
        
        # Submit to API
        result = api.collect_payment_with_allocation(payment_data)
        
        # Emit signal and close
        self.saved.emit(result)
        self.accept()

    def _format_amount(self, amount: float) -> str:
        currency = self.currency_combo.currentData() or 'USD'
        if currency == 'USD':
            return f"${float(amount or 0):,.2f}"
        if currency == 'SYP_NEW':
            return f"{float(amount or 0):,.2f} ل.س جديدة"
        return f"{float(amount or 0):,.2f} ل.س"

    def _format_amount_usd(self, amount_usd: float) -> str:
        tx_amount = self._usd_to_transaction_amount(float(amount_usd or 0))
        return self._format_amount(tx_amount)

    def _usd_to_transaction_amount(self, amount_usd: float) -> float:
        currency = self.currency_combo.currentData() or 'USD'
        if currency == 'USD':
            return float(amount_usd or 0)
        if currency == 'SYP_NEW':
            rate = float(self.usd_to_syp_new_snapshot.value() or 0)
            return float(amount_usd or 0) * rate if rate > 0 else 0.0
        if currency == 'SYP_OLD':
            rate = float(self.usd_to_syp_old_snapshot.value() or 0)
            return float(amount_usd or 0) * rate if rate > 0 else 0.0
        return float(amount_usd or 0)

    def _transaction_to_usd(self, amount: float) -> Decimal:
        currency = self.currency_combo.currentData() or 'USD'
        amount_dec = Decimal(str(amount or 0))
        if currency == 'USD':
            return amount_dec
        if currency == 'SYP_NEW':
            rate = Decimal(str(self.usd_to_syp_new_snapshot.value() or 0))
            return (amount_dec / rate) if rate > 0 else Decimal('0')
        if currency == 'SYP_OLD':
            rate = Decimal(str(self.usd_to_syp_old_snapshot.value() or 0))
            return (amount_dec / rate) if rate > 0 else Decimal('0')
        return amount_dec

    def on_currency_changed(self, index: int):
        currency = self.currency_combo.currentData() or 'USD'
        if currency == 'USD':
            self.payment_amount.setSuffix(" $")
            self.usd_to_syp_new_snapshot.setEnabled(False)
            self.usd_to_syp_old_snapshot.setEnabled(False)
        elif currency == 'SYP_NEW':
            self.payment_amount.setSuffix(" ل.س جديدة")
            self.usd_to_syp_new_snapshot.setEnabled(True)
            self.usd_to_syp_old_snapshot.setEnabled(True)
        else:
            self.payment_amount.setSuffix(" ل.س")
            self.usd_to_syp_new_snapshot.setEnabled(True)
            self.usd_to_syp_old_snapshot.setEnabled(True)

        self.load_fx_for_date()
        self.on_payment_amount_changed(self.payment_amount.value())
        if self.selected_customer:
            self._update_customer_display(self.selected_customer)
        self._update_selected_total()
        self._update_allocation_display()
        self._update_summary()

    def on_fx_new_changed(self, value: float):
        if self._fx_syncing:
            return
        self._fx_syncing = True
        try:
            self.usd_to_syp_old_snapshot.setValue(value * 100.0)
        finally:
            self._fx_syncing = False

    def on_fx_old_changed(self, value: float):
        if self._fx_syncing:
            return
        self._fx_syncing = True
        try:
            self.usd_to_syp_new_snapshot.setValue(value / 100.0 if value else 0.0)
        finally:
            self._fx_syncing = False

    def load_fx_for_date(self, qdate=None):
        if (self.currency_combo.currentData() or 'USD') == 'USD':
            return
        try:
            rate_date = self.payment_date.date().toString('yyyy-MM-dd')
            ctx = api.get_app_context(rate_date=rate_date, strict_fx=False)
            fx = ctx.get('daily_fx') if isinstance(ctx, dict) else None
            if fx:
                self._fx_syncing = True
                try:
                    self.usd_to_syp_old_snapshot.setValue(float(fx.get('usd_to_syp_old') or 0))
                    self.usd_to_syp_new_snapshot.setValue(float(fx.get('usd_to_syp_new') or 0))
                finally:
                    self._fx_syncing = False
        except ApiException:
            pass



class PaymentDetailsDialog(QDialog):
    """
    Dialog for displaying payment details with allocations.
    
    Requirements: 13.3 - Display payment details on double-click with allocations list
    """
    
    def __init__(self, payment: dict, parent=None):
        super().__init__(parent)
        self.payment = payment
        
        self.setWindowTitle(f"تفاصيل الدفعة - {payment.get('payment_number', '')}")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        self.setup_ui()
    
    def setup_ui(self):
        """Initialize dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header = QHBoxLayout()
        title = QLabel(f"سند قبض رقم: {self.payment.get('payment_number', '')}")
        title.setProperty("class", "title")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)
        
        # Payment info card
        info_card = Card()
        info_layout = QGridLayout(info_card)
        info_layout.setContentsMargins(20, 20, 20, 20)
        info_layout.setSpacing(12)
        
        # Row 0: Customer
        info_layout.addWidget(QLabel("العميل:"), 0, 0)
        customer_label = QLabel(self.payment.get('customer_name', ''))
        customer_label.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(customer_label, 0, 1)
        
        # Row 1: Date
        info_layout.addWidget(QLabel("تاريخ الدفع:"), 1, 0)
        date_label = QLabel(self.payment.get('payment_date', ''))
        info_layout.addWidget(date_label, 1, 1)
        
        # Row 2: Amount
        info_layout.addWidget(QLabel("المبلغ:"), 2, 0)
        amount = float(self.payment.get('amount', 0) or 0)
        amount_usd = float(self.payment.get('amount_usd', 0) or 0)
        currency = self.payment.get('transaction_currency') or 'USD'
        amount_label = QLabel(self._format_amount_by_currency(amount, currency))
        amount_label.setStyleSheet(f"font-weight: bold; color: {Colors.SUCCESS}; font-size: 16px;")
        info_layout.addWidget(amount_label, 2, 1)

        info_layout.addWidget(QLabel("عرض:"), 2, 2)
        amount_usd_label = QLabel(config.format_usd(amount_usd))
        amount_usd_label.setStyleSheet(f"font-weight: bold; color: {Colors.PRIMARY};")
        info_layout.addWidget(amount_usd_label, 2, 3)
        
        # Row 3: Payment method
        info_layout.addWidget(QLabel("طريقة الدفع:"), 3, 0)
        method_label = QLabel(self.payment.get('payment_method_display', ''))
        info_layout.addWidget(method_label, 3, 1)
        
        # Row 4: Reference
        reference = self.payment.get('reference', '')
        if reference:
            info_layout.addWidget(QLabel("المرجع:"), 4, 0)
            ref_label = QLabel(reference)
            info_layout.addWidget(ref_label, 4, 1)
        
        # Row 5: Received by
        received_by = self.payment.get('received_by_name', '')
        if received_by:
            info_layout.addWidget(QLabel("استلم بواسطة:"), 5, 0)
            received_label = QLabel(received_by)
            info_layout.addWidget(received_label, 5, 1)
        
        # Row 6: Notes
        notes = self.payment.get('notes', '')
        if notes:
            info_layout.addWidget(QLabel("ملاحظات:"), 6, 0)
            notes_label = QLabel(notes)
            notes_label.setWordWrap(True)
            info_layout.addWidget(notes_label, 6, 1)
        
        layout.addWidget(info_card)
        
        # Allocations section
        allocations = self.payment.get('allocations', [])
        if allocations:
            allocations_group = QGroupBox("توزيع المبلغ على الفواتير")
            allocations_layout = QVBoxLayout(allocations_group)
            
            # Allocations table
            allocations_table = QTableWidget()
            allocations_table.setColumnCount(5)
            allocations_table.setHorizontalHeaderLabels([
                'رقم الفاتورة', 'تاريخ الفاتورة', 'إجمالي الفاتورة', 'المبلغ المخصص', 'عرض'
            ])
            allocations_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            allocations_table.verticalHeader().setVisible(False)
            allocations_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            allocations_table.setSelectionBehavior(QAbstractItemView.SelectRows)
            allocations_table.setAlternatingRowColors(True)
            
            allocations_table.setRowCount(len(allocations))
            
            for row, allocation in enumerate(allocations):
                invoice = allocation.get('invoice', {})
                
                # Invoice number
                allocations_table.setItem(row, 0, QTableWidgetItem(
                    str(invoice.get('invoice_number', allocation.get('invoice_number', '')))
                ))
                
                # Invoice date
                allocations_table.setItem(row, 1, QTableWidgetItem(
                    str(invoice.get('invoice_date', allocation.get('invoice_date', '')))
                ))
                
                # Invoice total
                invoice_total_usd = float(allocation.get('invoice_total_usd', 0) or 0)
                allocations_table.setItem(row, 2, QTableWidgetItem(config.format_usd(invoice_total_usd)))
                
                # Allocated amount
                inv_currency = allocation.get('invoice_transaction_currency') or currency
                allocated = float(allocation.get('amount', 0) or 0)
                allocated_item = QTableWidgetItem(self._format_amount_by_currency(allocated, inv_currency))
                allocated_item.setForeground(QColor(Colors.SUCCESS))
                allocations_table.setItem(row, 3, allocated_item)

                allocated_usd = float(allocation.get('amount_usd', 0) or 0)
                allocated_usd_item = QTableWidgetItem(config.format_usd(allocated_usd))
                allocated_usd_item.setForeground(QColor(Colors.PRIMARY))
                allocations_table.setItem(row, 4, allocated_usd_item)
            
            allocations_layout.addWidget(allocations_table)
            layout.addWidget(allocations_group)
        else:
            # No allocations - show linked invoice if any
            invoice_id = self.payment.get('invoice')
            if invoice_id:
                invoice_group = QGroupBox("الفاتورة المرتبطة")
                invoice_layout = QVBoxLayout(invoice_group)
                
                invoice_label = QLabel(f"الفاتورة رقم: {self.payment.get('invoice', 'N/A')}")
                invoice_layout.addWidget(invoice_label)
                
                layout.addWidget(invoice_group)
            else:
                no_alloc_label = QLabel("لم يتم توزيع هذه الدفعة على فواتير محددة")
                no_alloc_label.setStyleSheet(f"color: {Colors.LIGHT_TEXT}; font-style: italic;")
                no_alloc_label.setAlignment(Qt.AlignCenter)
                layout.addWidget(no_alloc_label)

        layout.addStretch()

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        close_btn = QPushButton("إغلاق")
        close_btn.setProperty("class", "secondary")
        close_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(close_btn)

        layout.addLayout(buttons_layout)

    def _format_amount_by_currency(self, amount: float, currency: str) -> str:
        if currency == 'USD':
            return f"${float(amount or 0):,.2f}"
        if currency == 'SYP_NEW':
            return f"{float(amount or 0):,.2f} ل.س جديدة"
        return f"{float(amount or 0):,.2f} ل.س"
