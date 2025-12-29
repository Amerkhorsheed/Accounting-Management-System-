"""
Sales Returns Views and Dialogs

Requirements: 5.1, 5.2, 5.3, 5.7, 5.8, 5.9 - Sales Returns Management
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QFrame, QDialog,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QDoubleSpinBox, QScrollArea, QTextEdit,
    QDateEdit, QAbstractItemView, QComboBox
)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QFont
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime

from ...config import Colors, Fonts
from ...widgets.tables import DataTable
from ...widgets.dialogs import MessageDialog, ConfirmDialog
from ...widgets.cards import Card
from ...services.api import api, ApiException
from ...utils.error_handler import handle_ui_error


class SalesReturnDialog(QDialog):
    """
    Dialog for creating sales returns.
    
    Displays original invoice items and allows selecting
    quantities to return with reasons.
    
    Requirements: 5.2, 5.3, 5.7, 5.8 - Sales Return Creation
    """
    
    saved = Signal(dict)  # Emits return data
    
    def __init__(self, invoice: dict, parent=None):
        """
        Initialize the sales return dialog.
        
        Args:
            invoice: Invoice data with items
        """
        super().__init__(parent)
        self.invoice = invoice
        self.invoice_items = invoice.get('items', [])
        self.return_items = []  # Will hold return item data
        
        self.setWindowTitle(f"إنشاء مرتجع - فاتورة رقم {invoice.get('invoice_number', '')}")
        self.setMinimumWidth(900)
        self.setMinimumHeight(600)
        self.setup_ui()
        self.load_invoice_items()
    
    def setup_ui(self):
        """Initialize dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header with invoice info
        header_frame = QFrame()
        header_frame.setStyleSheet(f"background-color: {Colors.LIGHT_BG}; border-radius: 8px; padding: 12px;")
        header_layout = QVBoxLayout(header_frame)
        header_layout.setSpacing(8)
        
        # Invoice info row
        info_row = QHBoxLayout()
        
        invoice_label = QLabel(f"📄 فاتورة رقم: {self.invoice.get('invoice_number', '')}")
        invoice_label.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_H3, QFont.Bold))
        info_row.addWidget(invoice_label)
        
        customer_label = QLabel(f"👤 العميل: {self.invoice.get('customer_name', '')}")
        customer_label.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_BODY))
        info_row.addWidget(customer_label)
        
        date_label = QLabel(f"📅 التاريخ: {self.invoice.get('invoice_date', '')}")
        date_label.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_BODY))
        info_row.addWidget(date_label)
        
        total_label = QLabel(f"💰 الإجمالي: {float(self.invoice.get('total_amount', 0)):,.2f} ل.س")
        total_label.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_BODY, QFont.Bold))
        total_label.setStyleSheet(f"color: {Colors.PRIMARY};")
        info_row.addWidget(total_label)
        
        info_row.addStretch()
        header_layout.addLayout(info_row)
        
        layout.addWidget(header_frame)
        
        # Return date
        date_row = QHBoxLayout()
        date_row.addWidget(QLabel("تاريخ المرتجع:"))
        self.return_date_edit = QDateEdit()
        self.return_date_edit.setCalendarPopup(True)
        self.return_date_edit.setDate(QDate.currentDate())
        self.return_date_edit.setMaximumWidth(150)
        date_row.addWidget(self.return_date_edit)
        date_row.addStretch()
        layout.addLayout(date_row)
        
        # Items table
        items_label = QLabel("📦 منتجات الفاتورة - حدد الكميات المراد إرجاعها")
        items_label.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_H3, QFont.Bold))
        layout.addWidget(items_label)
        
        # Requirements: 5.2 - Display original invoice items with returnable quantities
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(7)
        self.items_table.setHorizontalHeaderLabels([
            'المنتج', 'الوحدة', 'الكمية الأصلية', 'المرتجع سابقاً', 
            'المتاح للإرجاع', 'كمية الإرجاع', 'الإجمالي'
        ])
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.items_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)
        self.items_table.setColumnWidth(5, 120)
        self.items_table.verticalHeader().setVisible(False)
        self.items_table.setAlternatingRowColors(True)
        self.items_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.items_table.setMinimumHeight(250)
        layout.addWidget(self.items_table)
        
        # Reason section - Requirements: 5.8 - Reason is required
        reason_frame = QFrame()
        reason_frame.setStyleSheet(f"background-color: {Colors.LIGHT_BG}; border-radius: 8px; padding: 12px;")
        reason_layout = QVBoxLayout(reason_frame)
        reason_layout.setSpacing(8)
        
        reason_label = QLabel("📝 سبب الإرجاع (مطلوب) *")
        reason_label.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_BODY, QFont.Bold))
        reason_label.setStyleSheet(f"color: {Colors.DANGER};")
        reason_layout.addWidget(reason_label)
        
        self.reason_input = QTextEdit()
        self.reason_input.setPlaceholderText("أدخل سبب الإرجاع...")
        self.reason_input.setMaximumHeight(80)
        reason_layout.addWidget(self.reason_input)
        
        # Notes (optional)
        notes_label = QLabel("ملاحظات إضافية (اختياري)")
        notes_label.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_BODY))
        reason_layout.addWidget(notes_label)
        
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("أدخل أي ملاحظات إضافية...")
        self.notes_input.setMaximumHeight(60)
        reason_layout.addWidget(self.notes_input)
        
        layout.addWidget(reason_frame)
        
        # Totals section - Requirements: 5.7 - Calculate return totals
        totals_frame = QFrame()
        totals_frame.setStyleSheet(f"""
            background-color: {Colors.PRIMARY}10; 
            border: 2px solid {Colors.PRIMARY}; 
            border-radius: 8px; 
            padding: 16px;
        """)
        totals_layout = QHBoxLayout(totals_frame)
        
        totals_layout.addStretch()
        
        # Return subtotal
        subtotal_container = QVBoxLayout()
        subtotal_label = QLabel("إجمالي المرتجع:")
        subtotal_label.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_BODY))
        subtotal_container.addWidget(subtotal_label)
        self.return_subtotal_label = QLabel("0.00 ل.س")
        self.return_subtotal_label.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_H2, QFont.Bold))
        self.return_subtotal_label.setStyleSheet(f"color: {Colors.PRIMARY};")
        subtotal_container.addWidget(self.return_subtotal_label)
        totals_layout.addLayout(subtotal_container)
        
        totals_layout.addSpacing(40)
        
        # Tax
        tax_container = QVBoxLayout()
        tax_label = QLabel("الضريبة:")
        tax_label.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_BODY))
        tax_container.addWidget(tax_label)
        self.return_tax_label = QLabel("0.00 ل.س")
        self.return_tax_label.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_H3, QFont.Bold))
        tax_container.addWidget(self.return_tax_label)
        totals_layout.addLayout(tax_container)
        
        totals_layout.addSpacing(40)
        
        # Grand total
        total_container = QVBoxLayout()
        grand_label = QLabel("الإجمالي الكلي:")
        grand_label.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_BODY))
        total_container.addWidget(grand_label)
        self.return_total_label = QLabel("0.00 ل.س")
        self.return_total_label.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_H1, QFont.Bold))
        self.return_total_label.setStyleSheet(f"color: {Colors.SUCCESS};")
        total_container.addWidget(self.return_total_label)
        totals_layout.addLayout(total_container)
        
        totals_layout.addStretch()
        
        layout.addWidget(totals_frame)
        
        # Error label
        self.error_label = QLabel()
        self.error_label.setStyleSheet(f"color: {Colors.DANGER}; font-weight: bold;")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setVisible(False)
        layout.addWidget(self.error_label)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        cancel_btn = QPushButton("إلغاء")
        cancel_btn.setProperty("class", "secondary")
        cancel_btn.setMinimumHeight(44)
        cancel_btn.setMinimumWidth(120)
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("✅ إنشاء المرتجع")
        save_btn.setProperty("class", "success")
        save_btn.setMinimumHeight(44)
        save_btn.setMinimumWidth(150)
        save_btn.clicked.connect(self.save)
        buttons_layout.addWidget(save_btn)
        
        layout.addLayout(buttons_layout)
    
    def load_invoice_items(self):
        """Load invoice items into the table."""
        self.items_table.setRowCount(len(self.invoice_items))
        self.quantity_spinners = []
        
        for row, item in enumerate(self.invoice_items):
            # Product name
            product_name = item.get('product_name', '')
            self.items_table.setItem(row, 0, QTableWidgetItem(product_name))
            
            # Unit
            unit_name = item.get('unit_name', '') or item.get('unit_symbol', '') or '-'
            self.items_table.setItem(row, 1, QTableWidgetItem(unit_name))
            
            # Original quantity
            original_qty = float(item.get('quantity', 0))
            self.items_table.setItem(row, 2, QTableWidgetItem(f"{original_qty:.2f}"))
            
            # Already returned quantity
            returned_qty = float(item.get('returned_quantity', 0))
            self.items_table.setItem(row, 3, QTableWidgetItem(f"{returned_qty:.2f}"))
            
            # Available for return - Requirements: 5.3 - Validate return quantity
            available_qty = original_qty - returned_qty
            available_item = QTableWidgetItem(f"{available_qty:.2f}")
            if available_qty <= 0:
                available_item.setForeground(Qt.red)
            self.items_table.setItem(row, 4, available_item)
            
            # Return quantity spinner - Requirements: 5.3 - Max validation
            qty_spinner = QDoubleSpinBox()
            qty_spinner.setRange(0, max(0, available_qty))
            qty_spinner.setDecimals(2)
            qty_spinner.setValue(0)
            qty_spinner.setSingleStep(1)
            qty_spinner.valueChanged.connect(lambda v, r=row: self.on_quantity_changed(r, v))
            self.items_table.setCellWidget(row, 5, qty_spinner)
            self.quantity_spinners.append(qty_spinner)
            
            # Line total (initially 0)
            self.items_table.setItem(row, 6, QTableWidgetItem("0.00"))
    
    def on_quantity_changed(self, row: int, value: float):
        """
        Handle quantity change for a row.
        
        Requirements: 5.7 - Calculate return totals including original discounts and taxes
        """
        if row >= len(self.invoice_items):
            return
        
        item = self.invoice_items[row]
        unit_price = float(item.get('unit_price', 0))
        discount_percent = float(item.get('discount_percent', 0))
        tax_rate = float(item.get('tax_rate', 0))
        
        # Calculate line total with discount and tax
        # Requirements: 5.7 - Apply original discounts and taxes proportionally
        subtotal = value * unit_price
        discount = (subtotal * discount_percent) / 100
        taxable = subtotal - discount
        tax = (taxable * tax_rate) / 100
        line_total = taxable + tax
        
        # Update line total in table
        total_item = QTableWidgetItem(f"{line_total:,.2f}")
        total_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.items_table.setItem(row, 6, total_item)
        
        # Update totals
        self.update_totals()
    
    def update_totals(self):
        """
        Update the return totals display.
        
        Requirements: 5.7 - Calculate return totals
        """
        total_subtotal = 0
        total_tax = 0
        
        for row, item in enumerate(self.invoice_items):
            if row >= len(self.quantity_spinners):
                continue
            
            return_qty = self.quantity_spinners[row].value()
            if return_qty <= 0:
                continue
            
            unit_price = float(item.get('unit_price', 0))
            discount_percent = float(item.get('discount_percent', 0))
            tax_rate = float(item.get('tax_rate', 0))
            
            subtotal = return_qty * unit_price
            discount = (subtotal * discount_percent) / 100
            taxable = subtotal - discount
            tax = (taxable * tax_rate) / 100
            
            total_subtotal += taxable
            total_tax += tax
        
        grand_total = total_subtotal + total_tax
        
        self.return_subtotal_label.setText(f"{total_subtotal:,.2f} ل.س")
        self.return_tax_label.setText(f"{total_tax:,.2f} ل.س")
        self.return_total_label.setText(f"{grand_total:,.2f} ل.س")
    
    def validate(self) -> bool:
        """
        Validate the return data.
        
        Requirements: 5.3, 5.8 - Validation rules
        """
        self.error_label.setVisible(False)
        
        # Check if at least one item has return quantity
        has_items = False
        for spinner in self.quantity_spinners:
            if spinner.value() > 0:
                has_items = True
                break
        
        if not has_items:
            self.error_label.setText("يجب تحديد كمية إرجاع لمنتج واحد على الأقل")
            self.error_label.setVisible(True)
            return False
        
        # Requirements: 5.8 - Reason is required
        reason = self.reason_input.toPlainText().strip()
        if not reason:
            self.error_label.setText("يجب إدخال سبب الإرجاع")
            self.error_label.setVisible(True)
            return False
        
        if len(reason) < 5:
            self.error_label.setText("سبب الإرجاع قصير جداً (5 أحرف على الأقل)")
            self.error_label.setVisible(True)
            return False
        
        return True
    
    def get_return_data(self) -> dict:
        """
        Get return data for API submission.
        
        Returns:
            {
                'return_date': date,
                'reason': str,
                'notes': str,
                'items': [
                    {
                        'invoice_item_id': int,
                        'quantity': Decimal,
                        'reason': str
                    }
                ]
            }
        """
        items = []
        for row, item in enumerate(self.invoice_items):
            if row >= len(self.quantity_spinners):
                continue
            
            return_qty = self.quantity_spinners[row].value()
            if return_qty > 0:
                items.append({
                    'invoice_item_id': item.get('id'),
                    'quantity': str(return_qty),
                    'reason': self.reason_input.toPlainText().strip()
                })
        
        return {
            'return_date': self.return_date_edit.date().toString('yyyy-MM-dd'),
            'reason': self.reason_input.toPlainText().strip(),
            'notes': self.notes_input.toPlainText().strip(),
            'items': items
        }
    
    def save(self):
        """Validate and save the return."""
        if not self.validate():
            return
        
        data = self.get_return_data()
        self.saved.emit(data)
        self.accept()



class SalesReturnsView(QWidget):
    """
    Sales Returns list view.
    
    Displays returns list with DataTable and filtering.
    
    Requirements: 5.9 - Display returns list
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Initialize the view UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("مرتجعات المبيعات")
        title.setProperty("class", "title")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)
        
        # Filters section
        filters_frame = QFrame()
        filters_frame.setStyleSheet(f"background-color: {Colors.LIGHT_BG}; border-radius: 8px; padding: 12px;")
        filters_layout = QHBoxLayout(filters_frame)
        filters_layout.setSpacing(16)
        
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
        
        # Invoice number filter
        filters_layout.addWidget(QLabel("رقم الفاتورة:"))
        self.invoice_filter = QLineEdit()
        self.invoice_filter.setPlaceholderText("بحث برقم الفاتورة...")
        self.invoice_filter.setMaximumWidth(180)
        filters_layout.addWidget(self.invoice_filter)
        
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
        
        # Returns table
        # Requirements: 5.9 - Display returns list with columns
        columns = [
            {'key': 'return_number', 'label': 'رقم المرتجع', 'type': 'text'},
            {'key': 'original_invoice_number', 'label': 'رقم الفاتورة', 'type': 'text'},
            {'key': 'customer_name', 'label': 'العميل', 'type': 'text'},
            {'key': 'return_date', 'label': 'التاريخ', 'type': 'date'},
            {'key': 'total_amount', 'label': 'المبلغ', 'type': 'currency'},
            {'key': 'reason', 'label': 'السبب', 'type': 'text'},
        ]
        
        self.table = DataTable(columns, actions=['view'])
        self.table.add_btn.setVisible(False)  # Returns are created from invoices
        self.table.action_clicked.connect(self.on_action)
        self.table.row_double_clicked.connect(self.view_return)
        self.table.page_changed.connect(self.on_page_changed)
        self.table.sort_changed.connect(self.on_sort_changed)
        
        layout.addWidget(self.table)
    
    @handle_ui_error
    def refresh(self):
        """Refresh returns data from API."""
        params = self._build_params()
        response = api.get_sales_returns(params)
        
        if isinstance(response, dict):
            returns = response.get('results', [])
            total = response.get('count', len(returns))
        else:
            returns = response if isinstance(response, list) else []
            total = len(returns)
        
        self.table.set_data(returns, total)
    
    def _build_params(self) -> dict:
        """Build API parameters from filters."""
        params = self.table.get_pagination_params()
        params.update(self.table.get_sort_params())
        
        # Date range
        date_from = self.date_from.date().toString('yyyy-MM-dd')
        date_to = self.date_to.date().toString('yyyy-MM-dd')
        params['date_from'] = date_from
        params['date_to'] = date_to
        
        # Invoice filter
        invoice_search = self.invoice_filter.text().strip()
        if invoice_search:
            params['search'] = invoice_search
        
        return params
    
    def apply_filters(self):
        """Apply filters and refresh."""
        self.table.current_page = 1
        self.refresh()
    
    def clear_filters(self):
        """Clear all filters."""
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.date_to.setDate(QDate.currentDate())
        self.invoice_filter.clear()
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
            self.view_return(row, data)
    
    @handle_ui_error
    def view_return(self, row: int, data: dict):
        """View return details."""
        return_id = data.get('id')
        if not return_id:
            return
        
        try:
            return_data = api.get_sales_return(return_id)
            
            # Build details message
            items_text = ""
            for item in return_data.get('items', []):
                product_name = item.get('product_name', '')
                quantity = float(item.get('quantity', 0))
                total = float(item.get('total', 0))
                items_text += f"\n  • {product_name}: {quantity:.2f} - {total:,.2f} ل.س"
            
            details = f"""
رقم المرتجع: {return_data.get('return_number', '')}
الفاتورة الأصلية: {return_data.get('original_invoice_number', '')}
العميل: {return_data.get('customer_name', '')}
التاريخ: {return_data.get('return_date', '')}
السبب: {return_data.get('reason', '')}

المنتجات المرتجعة:{items_text}

الإجمالي: {float(return_data.get('total_amount', 0)):,.2f} ل.س
            """.strip()
            
            MessageDialog.info(self, "تفاصيل المرتجع", details)
            
        except ApiException as e:
            MessageDialog.error(self, "خطأ", f"فشل في تحميل تفاصيل المرتجع: {str(e)}")



class InvoiceDetailsDialog(QDialog):
    """
    Dialog for viewing invoice details with return and cancel actions.
    
    Requirements: 4.2 - Display full invoice with items on double-click
    Requirements: 4.4 - Add cancel button for confirmed invoices
    Requirements: 5.1 - Add return button for confirmed/paid invoices
    """
    
    return_requested = Signal(dict)  # Emits invoice data when return is requested
    cancel_requested = Signal(dict)  # Emits invoice data when cancel is requested
    
    def __init__(self, invoice: dict, parent=None):
        """
        Initialize the invoice details dialog.
        
        Args:
            invoice: Full invoice data with items
        """
        super().__init__(parent)
        self.invoice = invoice
        
        self.setWindowTitle(f"تفاصيل الفاتورة - {invoice.get('invoice_number', '')}")
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        self.setup_ui()
    
    def setup_ui(self):
        """Initialize dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header with invoice info
        header_frame = QFrame()
        header_frame.setStyleSheet(f"background-color: {Colors.LIGHT_BG}; border-radius: 8px; padding: 16px;")
        header_layout = QVBoxLayout(header_frame)
        header_layout.setSpacing(12)
        
        # Invoice number and status
        title_row = QHBoxLayout()
        invoice_label = QLabel(f"📄 فاتورة رقم: {self.invoice.get('invoice_number', '')}")
        invoice_label.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_H2, QFont.Bold))
        title_row.addWidget(invoice_label)
        
        status = self.invoice.get('status', '')
        status_display = self.invoice.get('status_display', status)
        status_label = QLabel(status_display)
        status_label.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_BODY, QFont.Bold))
        
        # Color code status
        status_colors = {
            'draft': Colors.WARNING,
            'confirmed': Colors.INFO,
            'paid': Colors.SUCCESS,
            'partial': Colors.PRIMARY,
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
        
        # Invoice details grid
        details_grid = QHBoxLayout()
        details_grid.setSpacing(32)
        
        # Left column
        left_col = QVBoxLayout()
        left_col.setSpacing(8)
        left_col.addWidget(QLabel(f"👤 العميل: {self.invoice.get('customer_name', '')}"))
        left_col.addWidget(QLabel(f"📅 التاريخ: {self.invoice.get('invoice_date', '')}"))
        invoice_type = 'آجل' if self.invoice.get('invoice_type') == 'credit' else 'نقدي'
        left_col.addWidget(QLabel(f"📋 النوع: {invoice_type}"))
        if self.invoice.get('due_date'):
            left_col.addWidget(QLabel(f"📆 الاستحقاق: {self.invoice.get('due_date', '')}"))
        details_grid.addLayout(left_col)
        
        # Right column - amounts
        right_col = QVBoxLayout()
        right_col.setSpacing(8)
        total = float(self.invoice.get('total_amount', 0))
        paid = float(self.invoice.get('paid_amount', 0))
        remaining = float(self.invoice.get('remaining_amount', 0))
        
        total_label = QLabel(f"💰 الإجمالي: {total:,.2f} ل.س")
        total_label.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_BODY, QFont.Bold))
        right_col.addWidget(total_label)
        
        paid_label = QLabel(f"✅ المدفوع: {paid:,.2f} ل.س")
        paid_label.setStyleSheet(f"color: {Colors.SUCCESS};")
        right_col.addWidget(paid_label)
        
        remaining_label = QLabel(f"⏳ المتبقي: {remaining:,.2f} ل.س")
        if remaining > 0:
            remaining_label.setStyleSheet(f"color: {Colors.WARNING};")
        right_col.addWidget(remaining_label)
        
        details_grid.addLayout(right_col)
        details_grid.addStretch()
        header_layout.addLayout(details_grid)
        
        layout.addWidget(header_frame)
        
        # Items table
        items_label = QLabel("📦 منتجات الفاتورة")
        items_label.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_H3, QFont.Bold))
        layout.addWidget(items_label)
        
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(6)
        self.items_table.setHorizontalHeaderLabels([
            'المنتج', 'الوحدة', 'الكمية', 'السعر', 'الخصم', 'الإجمالي'
        ])
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.items_table.verticalHeader().setVisible(False)
        self.items_table.setAlternatingRowColors(True)
        self.items_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.items_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        # Populate items
        items = self.invoice.get('items', [])
        self.items_table.setRowCount(len(items))
        
        for row, item in enumerate(items):
            self.items_table.setItem(row, 0, QTableWidgetItem(item.get('product_name', '')))
            unit_name = item.get('unit_name', '') or item.get('unit_symbol', '') or '-'
            self.items_table.setItem(row, 1, QTableWidgetItem(unit_name))
            self.items_table.setItem(row, 2, QTableWidgetItem(f"{float(item.get('quantity', 0)):.2f}"))
            self.items_table.setItem(row, 3, QTableWidgetItem(f"{float(item.get('unit_price', 0)):,.2f}"))
            discount = float(item.get('discount_percent', 0))
            self.items_table.setItem(row, 4, QTableWidgetItem(f"{discount:.1f}%"))
            self.items_table.setItem(row, 5, QTableWidgetItem(f"{float(item.get('total', 0)):,.2f}"))
        
        layout.addWidget(self.items_table)
        
        # Notes if any
        notes = self.invoice.get('notes', '')
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
        
        # Requirements: 5.1 - Add return button for confirmed/paid invoices
        status = self.invoice.get('status', '')
        if status in ['confirmed', 'paid', 'partial']:
            return_btn = QPushButton("↩️ إنشاء مرتجع")
            return_btn.setProperty("class", "primary")
            return_btn.setMinimumHeight(44)
            return_btn.clicked.connect(self.request_return)
            buttons_layout.addWidget(return_btn)
        
        # Requirements: 4.4 - Add cancel button for confirmed invoices
        if status in ['confirmed']:
            cancel_btn = QPushButton("❌ إلغاء الفاتورة")
            cancel_btn.setProperty("class", "danger")
            cancel_btn.setMinimumHeight(44)
            cancel_btn.clicked.connect(self.request_cancel)
            buttons_layout.addWidget(cancel_btn)
        
        buttons_layout.addStretch()
        
        close_btn = QPushButton("إغلاق")
        close_btn.setProperty("class", "secondary")
        close_btn.setMinimumHeight(44)
        close_btn.setMinimumWidth(100)
        close_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(close_btn)
        
        layout.addLayout(buttons_layout)
    
    def request_return(self):
        """Request to create a return for this invoice."""
        self.return_requested.emit(self.invoice)
        self.accept()
    
    def request_cancel(self):
        """Request to cancel this invoice."""
        self.cancel_requested.emit(self.invoice)
        self.accept()
