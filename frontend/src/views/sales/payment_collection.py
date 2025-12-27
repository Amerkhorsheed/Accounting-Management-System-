"""
Payment Collection View - تحصيل المدفوعات

This module provides the UI for collecting payments from customers against their
outstanding credit invoices. It supports:
- Customer selection with balance display
- Unpaid invoices table with checkboxes for selection
- Payment amount input with allocation preview
- Multiple payment methods (cash, card, bank transfer, check)
- Manual and auto (FIFO) allocation strategies

Requirements: 2.1, 2.5, 2.6, 7.1, 7.3
"""
from decimal import Decimal
from typing import List, Dict, Optional, Any
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QFrame, QGridLayout,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QDoubleSpinBox, QComboBox, QCheckBox, QGroupBox,
    QSplitter, QTextEdit, QDateEdit, QAbstractItemView
)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QFont, QColor

from ...config import Colors, Fonts
from ...widgets.cards import Card
from ...widgets.dialogs import MessageDialog, ConfirmDialog
from ...services.api import api, ApiException
from ...utils.error_handler import handle_ui_error


class PaymentCollectionView(QWidget):
    """
    Payment Collection View for collecting customer payments.
    
    Allows selecting a customer, viewing their unpaid invoices,
    and recording payments with allocation to specific invoices.
    
    Requirements: 2.1, 2.5, 2.6, 7.1, 7.3
    """
    
    payment_completed = Signal(dict)  # Emitted when payment is successfully recorded
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.customers_cache: List[Dict] = []
        self.unpaid_invoices: List[Dict] = []
        self.selected_customer: Optional[Dict] = None
        self.allocations: Dict[int, Decimal] = {}  # invoice_id -> allocated amount
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize the payment collection UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("تحصيل المدفوعات")
        title.setProperty("class", "title")
        header.addWidget(title)
        header.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton("🔄 تحديث")
        refresh_btn.setProperty("class", "secondary")
        refresh_btn.clicked.connect(self.refresh)
        header.addWidget(refresh_btn)
        
        layout.addLayout(header)
        
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
        
        balance_layout.addWidget(QLabel("حد الائتمان:"), 1, 0)
        self.credit_limit_label = QLabel("0.00 ل.س")
        balance_layout.addWidget(self.credit_limit_label, 1, 1)
        
        balance_layout.addWidget(QLabel("الائتمان المتاح:"), 2, 0)
        self.available_credit_label = QLabel("0.00 ل.س")
        self.available_credit_label.setStyleSheet(f"color: {Colors.SUCCESS};")
        balance_layout.addWidget(self.available_credit_label, 2, 1)
        
        customer_layout.addWidget(balance_frame)
        left_layout.addWidget(customer_group)
        
        # Unpaid invoices section
        invoices_group = QGroupBox("الفواتير غير المسددة")
        invoices_layout = QVBoxLayout(invoices_group)
        
        # Invoices table
        self.invoices_table = QTableWidget()
        self.invoices_table.setColumnCount(7)
        self.invoices_table.setHorizontalHeaderLabels([
            '✓', 'رقم الفاتورة', 'التاريخ', 'تاريخ الاستحقاق',
            'المبلغ', 'المدفوع', 'المتبقي'
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
        
        # Right panel: Payment details and allocation
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
        date_row.addWidget(self.payment_date)
        right_layout.addLayout(date_row)
        
        # Payment amount
        amount_row = QHBoxLayout()
        amount_row.addWidget(QLabel("مبلغ الدفع:"))
        self.payment_amount = QDoubleSpinBox()
        self.payment_amount.setMaximum(999999999)
        self.payment_amount.setDecimals(2)
        self.payment_amount.setSuffix(" ل.س")
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
        
        # Allocation section
        right_layout.addWidget(self._create_separator())
        
        allocation_title = QLabel("توزيع المبلغ")
        allocation_title.setProperty("class", "h2")
        right_layout.addWidget(allocation_title)
        
        # Auto-allocate checkbox
        self.auto_allocate_check = QCheckBox("توزيع تلقائي (الأقدم أولاً)")
        self.auto_allocate_check.setChecked(True)
        self.auto_allocate_check.stateChanged.connect(self.on_auto_allocate_changed)
        right_layout.addWidget(self.auto_allocate_check)
        
        # Allocation preview
        self.allocation_table = QTableWidget()
        self.allocation_table.setColumnCount(3)
        self.allocation_table.setHorizontalHeaderLabels(['الفاتورة', 'المتبقي', 'المخصص'])
        self.allocation_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.allocation_table.verticalHeader().setVisible(False)
        self.allocation_table.setMaximumHeight(150)
        self.allocation_table.cellChanged.connect(self.on_allocation_cell_changed)
        right_layout.addWidget(self.allocation_table)
        
        # Store spinboxes for manual allocation
        self.allocation_spinboxes: Dict[int, QDoubleSpinBox] = {}
        
        # Summary
        right_layout.addWidget(self._create_separator())
        
        summary_layout = QGridLayout()
        summary_layout.addWidget(QLabel("إجمالي المحدد:"), 0, 0)
        self.selected_total_label = QLabel("0.00 ل.س")
        self.selected_total_label.setStyleSheet("font-weight: bold;")
        summary_layout.addWidget(self.selected_total_label, 0, 1)
        
        summary_layout.addWidget(QLabel("مبلغ الدفع:"), 1, 0)
        self.payment_total_label = QLabel("0.00 ل.س")
        self.payment_total_label.setStyleSheet(f"font-weight: bold; color: {Colors.PRIMARY};")
        summary_layout.addWidget(self.payment_total_label, 1, 1)
        
        summary_layout.addWidget(QLabel("الفرق:"), 2, 0)
        self.difference_label = QLabel("0.00 ل.س")
        summary_layout.addWidget(self.difference_label, 2, 1)
        
        right_layout.addLayout(summary_layout)
        
        # Action buttons
        right_layout.addStretch()
        
        actions_layout = QHBoxLayout()
        
        clear_btn = QPushButton("مسح")
        clear_btn.setProperty("class", "secondary")
        clear_btn.clicked.connect(self.clear_form)
        actions_layout.addWidget(clear_btn)
        
        actions_layout.addStretch()
        
        self.submit_btn = QPushButton("💰 تسجيل الدفعة")
        self.submit_btn.setProperty("class", "success")
        self.submit_btn.setMinimumHeight(50)
        self.submit_btn.clicked.connect(self.submit_payment)
        actions_layout.addWidget(self.submit_btn)
        
        right_layout.addLayout(actions_layout)
        
        splitter.addWidget(right_panel)
        
        # Set splitter sizes
        splitter.setSizes([600, 400])
        
        layout.addWidget(splitter, 1)
    
    def _create_separator(self) -> QFrame:
        """Create a horizontal separator line."""
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet(f"background-color: {Colors.LIGHT_BORDER};")
        return separator

    @handle_ui_error
    def refresh(self):
        """Refresh customers list from API."""
        response = api.get_customers()
        if isinstance(response, dict) and 'results' in response:
            self.customers_cache = response['results']
        else:
            self.customers_cache = response if isinstance(response, list) else []
        
        # Filter to only customers with balance > 0
        customers_with_balance = [
            c for c in self.customers_cache 
            if float(c.get('current_balance', 0)) > 0
        ]
        
        # Update combo box
        self.customer_combo.clear()
        self.customer_combo.addItem("-- اختر العميل --", None)
        
        for customer in customers_with_balance:
            balance = float(customer.get('current_balance', 0))
            display_text = f"{customer.get('name', '')} - رصيد: {balance:,.2f} ل.س"
            self.customer_combo.addItem(display_text, customer)
        
        # Clear selection
        self.selected_customer = None
        self.clear_form()
    
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
        balance = float(customer.get('current_balance', 0))
        credit_limit = float(customer.get('credit_limit', 0))
        available = max(0, credit_limit - balance)
        
        self.current_balance_label.setText(f"{balance:,.2f} ل.س")
        self.credit_limit_label.setText(f"{credit_limit:,.2f} ل.س")
        self.available_credit_label.setText(f"{available:,.2f} ل.س")
        
        # Color code the balance
        if balance > credit_limit and credit_limit > 0:
            self.current_balance_label.setStyleSheet(f"font-weight: bold; color: {Colors.DANGER};")
        elif balance >= credit_limit * 0.8 and credit_limit > 0:
            self.current_balance_label.setStyleSheet(f"font-weight: bold; color: {Colors.WARNING};")
        else:
            self.current_balance_label.setStyleSheet(f"font-weight: bold; color: {Colors.SUCCESS};")
    
    def _clear_customer_display(self):
        """Clear the customer balance display."""
        self.current_balance_label.setText("0.00 ل.س")
        self.credit_limit_label.setText("0.00 ل.س")
        self.available_credit_label.setText("0.00 ل.س")
        self.current_balance_label.setStyleSheet(f"font-weight: bold; color: {Colors.LIGHT_TEXT};")
        self.invoices_table.setRowCount(0)
        self.unpaid_invoices = []
        self.allocations = {}
        self._update_allocation_preview()
    
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
        self._update_allocation_preview()
    
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
            
            # Due date
            due_date_item = QTableWidgetItem(str(invoice.get('due_date', '')))
            # Highlight overdue invoices
            if invoice.get('is_overdue', False):
                due_date_item.setForeground(QColor(Colors.DANGER))
            self.invoices_table.setItem(row, 3, due_date_item)
            
            # Total amount
            total = float(invoice.get('total_amount', 0))
            self.invoices_table.setItem(row, 4, QTableWidgetItem(f"{total:,.2f}"))
            
            # Paid amount
            paid = float(invoice.get('paid_amount', 0))
            self.invoices_table.setItem(row, 5, QTableWidgetItem(f"{paid:,.2f}"))
            
            # Remaining amount
            remaining = float(invoice.get('remaining_amount', total - paid))
            remaining_item = QTableWidgetItem(f"{remaining:,.2f}")
            remaining_item.setForeground(QColor(Colors.DANGER))
            self.invoices_table.setItem(row, 6, remaining_item)
        
        self.invoices_table.blockSignals(False)
    
    def on_invoice_selection_changed(self, item: QTableWidgetItem):
        """Handle invoice checkbox state change."""
        if item.column() != 0:
            return
        
        self._update_selected_total()
        if self.auto_allocate_check.isChecked():
            self._auto_allocate()
        self._update_allocation_preview()
    
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
        self._update_allocation_preview()
    
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
        self._update_allocation_preview()
    
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
        total = sum(float(inv.get('remaining_amount', 0)) for inv in selected)
        self.selected_total_label.setText(f"{total:,.2f} ل.س")
        self._update_difference()
    
    def on_payment_amount_changed(self, value: float):
        """Handle payment amount change."""
        self.payment_total_label.setText(f"{value:,.2f} ل.س")
        self._update_difference()
        
        if self.auto_allocate_check.isChecked():
            self._auto_allocate()
        self._update_allocation_preview()
    
    def _update_difference(self):
        """Update the difference between payment and selected total."""
        payment = self.payment_amount.value()
        selected = self._get_selected_invoices()
        selected_total = sum(float(inv.get('remaining_amount', 0)) for inv in selected)
        
        difference = payment - selected_total
        self.difference_label.setText(f"{difference:,.2f} ل.س")
        
        if difference < 0:
            self.difference_label.setStyleSheet(f"color: {Colors.WARNING};")
        elif difference > 0:
            self.difference_label.setStyleSheet(f"color: {Colors.INFO};")
        else:
            self.difference_label.setStyleSheet(f"color: {Colors.SUCCESS};")
    
    def on_auto_allocate_changed(self, state: int):
        """Handle auto-allocate checkbox change."""
        if state == Qt.Checked:
            self._auto_allocate()
        else:
            self.allocations = {}
        self._update_allocation_preview()

    def _auto_allocate(self):
        """
        Auto-allocate payment amount to selected invoices using FIFO strategy.
        
        Allocates to oldest invoices first (by invoice_date).
        Requirements: 7.4
        """
        self.allocations = {}
        payment_amount = Decimal(str(self.payment_amount.value()))
        
        if payment_amount <= 0:
            return
        
        # Get selected invoices sorted by date (oldest first - FIFO)
        selected = self._get_selected_invoices()
        selected_sorted = sorted(selected, key=lambda x: x.get('invoice_date', ''))
        
        remaining_payment = payment_amount
        
        for invoice in selected_sorted:
            if remaining_payment <= 0:
                break
            
            invoice_id = invoice.get('id')
            invoice_remaining = Decimal(str(invoice.get('remaining_amount', 0)))
            
            # Allocate the minimum of remaining payment and invoice remaining
            allocation = min(remaining_payment, invoice_remaining)
            
            if allocation > 0:
                self.allocations[invoice_id] = allocation
                remaining_payment -= allocation
    
    def _update_allocation_preview(self):
        """
        Update the allocation preview table.
        
        When auto-allocate is enabled, shows read-only allocation amounts.
        When auto-allocate is disabled, shows editable spinboxes for manual allocation.
        
        Requirements: 7.1, 7.3
        """
        selected = self._get_selected_invoices()
        is_auto = self.auto_allocate_check.isChecked()
        
        self.allocation_table.blockSignals(True)
        self.allocation_table.setRowCount(len(selected))
        self.allocation_spinboxes.clear()
        
        for row, invoice in enumerate(selected):
            invoice_id = invoice.get('id')
            
            # Invoice number
            invoice_item = QTableWidgetItem(str(invoice.get('invoice_number', '')))
            invoice_item.setFlags(invoice_item.flags() & ~Qt.ItemIsEditable)
            self.allocation_table.setItem(row, 0, invoice_item)
            
            # Remaining amount
            remaining = float(invoice.get('remaining_amount', 0))
            remaining_item = QTableWidgetItem(f"{remaining:,.2f}")
            remaining_item.setFlags(remaining_item.flags() & ~Qt.ItemIsEditable)
            self.allocation_table.setItem(row, 1, remaining_item)
            
            # Allocated amount - editable spinbox when manual, read-only when auto
            allocated = float(self.allocations.get(invoice_id, 0))
            
            if is_auto:
                # Read-only display for auto-allocation
                allocated_item = QTableWidgetItem(f"{allocated:,.2f}")
                allocated_item.setFlags(allocated_item.flags() & ~Qt.ItemIsEditable)
                if allocated > 0:
                    allocated_item.setForeground(QColor(Colors.SUCCESS))
                self.allocation_table.setItem(row, 2, allocated_item)
            else:
                # Editable spinbox for manual allocation
                spinbox = QDoubleSpinBox()
                spinbox.setMaximum(remaining)
                spinbox.setDecimals(2)
                spinbox.setValue(allocated)
                spinbox.setSuffix(" ل.س")
                spinbox.setProperty("invoice_id", invoice_id)
                spinbox.valueChanged.connect(
                    lambda val, inv_id=invoice_id: self._on_manual_allocation_changed(inv_id, val)
                )
                self.allocation_table.setCellWidget(row, 2, spinbox)
                self.allocation_spinboxes[invoice_id] = spinbox
        
        self.allocation_table.blockSignals(False)
    
    def _on_manual_allocation_changed(self, invoice_id: int, value: float):
        """
        Handle manual allocation amount change.
        
        Updates the allocations dictionary and recalculates totals.
        Requirements: 7.1, 7.3
        """
        if value > 0:
            self.allocations[invoice_id] = Decimal(str(value))
        elif invoice_id in self.allocations:
            del self.allocations[invoice_id]
        
        self._update_allocation_summary()
    
    def _update_allocation_summary(self):
        """Update the allocation summary (total allocated vs payment amount)."""
        total_allocated = sum(float(amt) for amt in self.allocations.values())
        payment = self.payment_amount.value()
        
        difference = payment - total_allocated
        self.difference_label.setText(f"{difference:,.2f} ل.س")
        
        if difference < 0:
            self.difference_label.setStyleSheet(f"color: {Colors.DANGER};")
        elif difference > 0:
            self.difference_label.setStyleSheet(f"color: {Colors.INFO};")
        else:
            self.difference_label.setStyleSheet(f"color: {Colors.SUCCESS};")
    
    def on_allocation_cell_changed(self, row: int, column: int):
        """Handle allocation table cell change (for compatibility)."""
        # Update allocation summary when cell values change
        self._update_allocation_summary()
    
    def clear_form(self):
        """Clear the payment form."""
        self.payment_amount.setValue(0)
        self.payment_method.setCurrentIndex(0)
        self.reference_input.clear()
        self.notes_input.clear()
        self.payment_date.setDate(QDate.currentDate())
        self.auto_allocate_check.setChecked(True)
        self.allocations = {}
        self.deselect_all_invoices()
        self._update_allocation_preview()
    
    def _validate_payment(self) -> bool:
        """Validate payment data before submission."""
        if not self.selected_customer:
            MessageDialog.warning(self, "تنبيه", "يرجى اختيار العميل أولاً")
            return False
        
        payment_amount = self.payment_amount.value()
        if payment_amount <= 0:
            MessageDialog.warning(self, "تنبيه", "يرجى إدخال مبلغ الدفع")
            return False
        
        selected = self._get_selected_invoices()
        if not selected and not self.allocations:
            # Allow payment without specific invoice selection (general payment)
            confirm = ConfirmDialog(
                "تأكيد",
                "لم يتم تحديد فواتير محددة. هل تريد تسجيل الدفعة كدفعة عامة؟",
                danger=False,
                parent=self
            )
            if not confirm.exec():
                return False
        
        return True
    
    @handle_ui_error
    def submit_payment(self):
        """Submit the payment to the API."""
        if not self._validate_payment():
            return
        
        # Build allocations list
        allocations_list = []
        for invoice_id, amount in self.allocations.items():
            if amount > 0:
                allocations_list.append({
                    'invoice_id': invoice_id,
                    'amount': str(amount)
                })
        
        # Build payment data
        payment_data = {
            'customer': self.selected_customer.get('id'),
            'payment_date': self.payment_date.date().toString('yyyy-MM-dd'),
            'amount': str(self.payment_amount.value()),
            'payment_method': self.payment_method.currentData(),
            'reference': self.reference_input.text().strip() or None,
            'notes': self.notes_input.toPlainText().strip() or None,
            'allocations': allocations_list if allocations_list else None,
            'auto_allocate': self.auto_allocate_check.isChecked() and not allocations_list
        }
        
        # Confirm submission
        confirm = ConfirmDialog(
            "تأكيد تسجيل الدفعة",
            f"هل تريد تسجيل دفعة بمبلغ {self.payment_amount.value():,.2f} ل.س للعميل {self.selected_customer.get('name')}؟",
            confirm_text="تسجيل",
            danger=False,
            parent=self
        )
        
        if not confirm.exec():
            return
        
        # Submit to API
        result = api.collect_payment_with_allocation(payment_data)
        
        # Show success message
        MessageDialog.success(
            self,
            "نجاح",
            f"تم تسجيل الدفعة بنجاح\nرقم السند: {result.get('receipt_number', 'N/A')}"
        )
        
        # Emit signal
        self.payment_completed.emit(result)
        
        # Refresh the view
        self.clear_form()
        if self.selected_customer:
            customer_id = self.selected_customer.get('id')
            # Reload customer data to get updated balance
            try:
                updated_customer = api.get_customer(customer_id)
                self.selected_customer = updated_customer
                self._update_customer_display(updated_customer)
                self._load_unpaid_invoices(customer_id)
            except Exception:
                # If refresh fails, just reload the full list
                self.refresh()
