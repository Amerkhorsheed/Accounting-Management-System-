"""
Receivables Report View - تقرير المستحقات

This module provides the UI for viewing the receivables report showing
all outstanding customer balances, with filtering and summary cards.

Requirements: 4.1, 4.2, 4.3, 4.4, 4.5
"""
from typing import List, Dict, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QGridLayout, QScrollArea,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QDateEdit, QAbstractItemView
)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QFont, QColor

from ...config import Colors, Fonts
from ...widgets.cards import Card, StatCard
from ...widgets.dialogs import MessageDialog
from ...services.api import api, ApiException
from ...utils.error_handler import handle_ui_error


class ReceivablesReportView(QWidget):
    """
    Receivables Report View showing outstanding customer balances.
    
    Displays:
    - Summary cards (total outstanding, overdue amount, customer count)
    - Customer list table with balances sorted by amount
    - Filter controls (customer type, salesperson, date range)
    
    Requirements: 4.1, 4.2, 4.3, 4.4, 4.5
    """
    
    customer_selected = Signal(dict)  # Emitted when a customer row is clicked
    back_requested = Signal()  # Emitted when back button is clicked
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.report_data: Dict = {}
        self.customers_list: List[Dict] = []
        self.setup_ui()
    
    def go_back(self):
        """Navigate back to main reports view."""
        self.back_requested.emit()
        
    def setup_ui(self):
        """Initialize the receivables report UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header = QHBoxLayout()
        
        # Back button
        back_btn = QPushButton("→ رجوع")
        back_btn.setProperty("class", "secondary")
        back_btn.clicked.connect(self.go_back)
        header.addWidget(back_btn)
        
        title = QLabel("تقرير المستحقات")
        title.setProperty("class", "title")
        header.addWidget(title)
        header.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton("🔄 تحديث")
        refresh_btn.setProperty("class", "secondary")
        refresh_btn.clicked.connect(self.refresh)
        header.addWidget(refresh_btn)
        
        # Export buttons (placeholders)
        export_excel_btn = QPushButton("📊 Excel")
        export_excel_btn.setProperty("class", "secondary")
        export_excel_btn.clicked.connect(self._export_excel)
        header.addWidget(export_excel_btn)
        
        export_pdf_btn = QPushButton("📄 PDF")
        export_pdf_btn.setProperty("class", "secondary")
        export_pdf_btn.clicked.connect(self._export_pdf)
        header.addWidget(export_pdf_btn)
        
        layout.addLayout(header)
        
        # Filters section
        # Requirements: 4.4 - Allow filtering by customer type, salesperson, date range
        filters_frame = Card()
        filters_layout = QHBoxLayout(filters_frame)
        filters_layout.setContentsMargins(16, 12, 16, 12)
        filters_layout.setSpacing(16)
        
        # Customer type filter
        filters_layout.addWidget(QLabel("نوع العميل:"))
        self.customer_type_combo = QComboBox()
        self.customer_type_combo.addItem("الكل", None)
        self.customer_type_combo.addItem("فرد", "individual")
        self.customer_type_combo.addItem("شركة", "company")
        self.customer_type_combo.addItem("حكومي", "government")
        self.customer_type_combo.setMinimumWidth(120)
        filters_layout.addWidget(self.customer_type_combo)
        
        # Salesperson filter (placeholder - would need API to populate)
        filters_layout.addWidget(QLabel("مندوب المبيعات:"))
        self.salesperson_combo = QComboBox()
        self.salesperson_combo.addItem("الكل", None)
        self.salesperson_combo.setMinimumWidth(150)
        filters_layout.addWidget(self.salesperson_combo)
        
        # Date range filter
        filters_layout.addWidget(QLabel("من:"))
        self.from_date = QDateEdit()
        self.from_date.setCalendarPopup(True)
        self.from_date.setDate(QDate.currentDate().addMonths(-3))
        filters_layout.addWidget(self.from_date)
        
        filters_layout.addWidget(QLabel("إلى:"))
        self.to_date = QDateEdit()
        self.to_date.setCalendarPopup(True)
        self.to_date.setDate(QDate.currentDate())
        filters_layout.addWidget(self.to_date)
        
        # Apply filter button
        apply_btn = QPushButton("تطبيق")
        apply_btn.clicked.connect(self._apply_filters)
        filters_layout.addWidget(apply_btn)
        
        filters_layout.addStretch()
        
        layout.addWidget(filters_frame)
        
        # Summary cards section
        # Requirements: 4.1, 4.2 - Display total outstanding and customer count
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)
        
        # Total outstanding card
        self.total_card = StatCard(
            title="إجمالي المستحقات",
            value="0.00 ل.س",
            icon="💰",
            color=Colors.PRIMARY
        )
        cards_layout.addWidget(self.total_card)
        
        # Overdue amount card
        self.overdue_card = StatCard(
            title="المبالغ المتأخرة",
            value="0.00 ل.س",
            icon="⚠️",
            color=Colors.DANGER
        )
        cards_layout.addWidget(self.overdue_card)
        
        # Customers with balance count card
        self.customers_count_card = StatCard(
            title="عملاء لديهم رصيد",
            value="0",
            icon="👥",
            color=Colors.INFO
        )
        cards_layout.addWidget(self.customers_count_card)
        
        # Unpaid invoices count card
        self.invoices_count_card = StatCard(
            title="فواتير غير مسددة",
            value="0",
            icon="📋",
            color=Colors.WARNING
        )
        cards_layout.addWidget(self.invoices_count_card)
        
        layout.addLayout(cards_layout)
        
        # Customers table section
        # Requirements: 4.2, 4.3, 4.5 - List customers with balances, credit info, invoice counts
        table_card = Card()
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(16, 16, 16, 16)
        table_layout.setSpacing(12)
        
        table_header = QHBoxLayout()
        table_title = QLabel("قائمة العملاء")
        table_title.setProperty("class", "h2")
        table_header.addWidget(table_title)
        table_header.addStretch()
        table_layout.addLayout(table_header)
        
        # Customers table
        self.customers_table = QTableWidget()
        self.customers_table.setColumnCount(8)
        self.customers_table.setHorizontalHeaderLabels([
            'كود العميل',
            'اسم العميل',
            'نوع العميل',
            'الرصيد الحالي',
            'حد الائتمان',
            'الائتمان المتاح',
            'فواتير غير مسددة',
            'فواتير جزئية'
        ])
        self.customers_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.customers_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.customers_table.verticalHeader().setVisible(False)
        self.customers_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.customers_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.customers_table.setAlternatingRowColors(True)
        self.customers_table.doubleClicked.connect(self._on_customer_double_clicked)
        
        table_layout.addWidget(self.customers_table)
        
        layout.addWidget(table_card, 1)
    
    @handle_ui_error
    def refresh(self):
        """Refresh the receivables report data from API."""
        self._load_report()
    
    @handle_ui_error
    def _apply_filters(self):
        """Apply filters and reload the report."""
        self._load_report()
    
    def _load_report(self):
        """
        Load receivables report data from API.
        
        Requirements: 4.1-4.5
        """
        # Build filter parameters
        params = {}
        
        customer_type = self.customer_type_combo.currentData()
        if customer_type:
            params['customer_type'] = customer_type
        
        salesperson_id = self.salesperson_combo.currentData()
        if salesperson_id:
            params['salesperson'] = salesperson_id
        
        start_date = self.from_date.date().toString('yyyy-MM-dd')
        end_date = self.to_date.date().toString('yyyy-MM-dd')
        params['start_date'] = start_date
        params['end_date'] = end_date
        
        # Fetch report data
        self.report_data = api.get_receivables_report(
            customer_type=params.get('customer_type'),
            salesperson_id=params.get('salesperson'),
            start_date=params.get('start_date'),
            end_date=params.get('end_date')
        )
        
        # Update summary cards
        self._update_summary_cards()
        
        # Update customers table
        self._update_customers_table()
    
    def _update_summary_cards(self):
        """
        Update the summary cards with report data.
        
        Requirements: 4.1, 4.2
        """
        summary = self.report_data.get('summary', {})
        total_outstanding = float(summary.get('total_outstanding', 0))
        overdue_total = float(summary.get('total_overdue', 0))
        customers_count = int(summary.get('customer_count', 0))
        unpaid_invoices = int(summary.get('total_unpaid_invoices', 0))
        partial_invoices = int(summary.get('total_partial_invoices', 0))
        
        self.total_card.update_value(f"{total_outstanding:,.2f} ل.س")
        self.overdue_card.update_value(f"{overdue_total:,.2f} ل.س")
        self.customers_count_card.update_value(str(customers_count))
        self.invoices_count_card.update_value(str(unpaid_invoices + partial_invoices))
    
    def _update_customers_table(self):
        """
        Update the customers table with report data.
        
        Requirements: 4.2, 4.3, 4.5 - List customers sorted by balance, show credit info
        """
        customers = self.report_data.get('customers', [])
        self.customers_list = customers
        
        self.customers_table.setRowCount(len(customers))
        
        for row, customer in enumerate(customers):
            # Customer code
            code_item = QTableWidgetItem(str(customer.get('code', '')))
            code_item.setData(Qt.UserRole, customer)
            self.customers_table.setItem(row, 0, code_item)
            
            # Customer name
            self.customers_table.setItem(row, 1, QTableWidgetItem(
                str(customer.get('name', ''))
            ))
            
            # Customer type
            customer_type = customer.get('customer_type', '')
            type_display = {
                'individual': 'فرد',
                'company': 'شركة',
                'government': 'حكومي'
            }.get(customer_type, customer_type)
            self.customers_table.setItem(row, 2, QTableWidgetItem(type_display))
            
            # Current balance
            balance = float(customer.get('current_balance', 0))
            balance_item = QTableWidgetItem(f"{balance:,.2f}")
            balance_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            # Color code based on credit status
            credit_limit = float(customer.get('credit_limit', 0))
            if credit_limit > 0 and balance > credit_limit:
                balance_item.setForeground(QColor(Colors.DANGER))
            elif credit_limit > 0 and balance >= credit_limit * 0.8:
                balance_item.setForeground(QColor(Colors.WARNING))
            self.customers_table.setItem(row, 3, balance_item)
            
            # Credit limit
            credit_limit_item = QTableWidgetItem(
                f"{credit_limit:,.2f}" if credit_limit > 0 else "غير محدد"
            )
            credit_limit_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.customers_table.setItem(row, 4, credit_limit_item)
            
            # Available credit
            available = float(customer.get('available_credit', 0))
            available_item = QTableWidgetItem(
                f"{available:,.2f}" if credit_limit > 0 else "-"
            )
            available_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if credit_limit > 0:
                if available <= 0:
                    available_item.setForeground(QColor(Colors.DANGER))
                elif available < credit_limit * 0.2:
                    available_item.setForeground(QColor(Colors.WARNING))
                else:
                    available_item.setForeground(QColor(Colors.SUCCESS))
            self.customers_table.setItem(row, 5, available_item)
            
            # Unpaid invoices count
            unpaid_count = int(customer.get('unpaid_invoice_count', 0))
            unpaid_item = QTableWidgetItem(str(unpaid_count))
            unpaid_item.setTextAlignment(Qt.AlignCenter)
            if unpaid_count > 0:
                unpaid_item.setForeground(QColor(Colors.DANGER))
            self.customers_table.setItem(row, 6, unpaid_item)
            
            # Partial invoices count
            partial_count = int(customer.get('partial_invoice_count', 0))
            partial_item = QTableWidgetItem(str(partial_count))
            partial_item.setTextAlignment(Qt.AlignCenter)
            if partial_count > 0:
                partial_item.setForeground(QColor(Colors.WARNING))
            self.customers_table.setItem(row, 7, partial_item)
    
    def _on_customer_double_clicked(self, index):
        """Handle customer row double-click to view statement."""
        row = index.row()
        if row < len(self.customers_list):
            customer = self.customers_list[row]
            self.customer_selected.emit(customer)
    
    def _export_excel(self):
        """Export report to Excel (placeholder)."""
        MessageDialog.info(self, "معلومات", "تصدير Excel قيد التطوير")
    
    def _export_pdf(self):
        """Export report to PDF (placeholder)."""
        MessageDialog.info(self, "معلومات", "تصدير PDF قيد التطوير")
