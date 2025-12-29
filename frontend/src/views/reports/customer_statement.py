"""
Customer Statement View - كشف حساب العميل

This module provides the UI for viewing a customer's account statement
showing all transactions and running balance.

Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6
"""
from typing import List, Dict, Optional
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QGridLayout, QScrollArea,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QDateEdit, QAbstractItemView
)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QFont, QColor

from ...config import Colors, Fonts
from ...widgets.cards import Card
from ...widgets.dialogs import MessageDialog
from ...services.api import api, ApiException
from ...services.export import ExportService, ExportError
from ...utils.error_handler import handle_ui_error


class CustomerStatementView(QWidget):
    """
    Customer Statement View showing transaction history and running balance.
    
    Displays:
    - Customer selection
    - Date range filter
    - Opening balance, transactions, and closing balance
    - Running balance after each transaction
    - Transaction type (invoice/payment/return)
    - Export buttons (PDF/Excel placeholders)
    
    Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6
    """
    
    back_requested = Signal()  # Emitted when back button is clicked
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.customers_cache: List[Dict] = []
        self.selected_customer: Optional[Dict] = None
        self.statement_data: Dict = {}
        self.transactions: List[Dict] = []
        self.setup_ui()
    
    def go_back(self):
        """Navigate back to main reports view."""
        self.back_requested.emit()
        
    def setup_ui(self):
        """Initialize the customer statement UI."""
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
        
        title = QLabel("كشف حساب العميل")
        title.setProperty("class", "title")
        header.addWidget(title)
        header.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton("🔄 تحديث")
        refresh_btn.setProperty("class", "secondary")
        refresh_btn.clicked.connect(self.refresh)
        header.addWidget(refresh_btn)
        
        layout.addLayout(header)
        
        # Filters section
        # Requirements: 3.4 - Date range filtering
        filters_frame = Card()
        filters_layout = QHBoxLayout(filters_frame)
        filters_layout.setContentsMargins(16, 12, 16, 12)
        filters_layout.setSpacing(16)
        
        # Customer selection
        filters_layout.addWidget(QLabel("العميل:"))
        self.customer_combo = QComboBox()
        self.customer_combo.setMinimumWidth(250)
        self.customer_combo.setPlaceholderText("اختر العميل...")
        self.customer_combo.currentIndexChanged.connect(self._on_customer_selected)
        filters_layout.addWidget(self.customer_combo)
        
        # Date range filter
        # Requirements: 3.4 - Filter by date range
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
        apply_btn = QPushButton("عرض الكشف")
        apply_btn.clicked.connect(self._load_statement)
        filters_layout.addWidget(apply_btn)
        
        filters_layout.addStretch()
        
        # Export buttons
        # Requirements: 3.5 - Export to PDF and Excel
        export_excel_btn = QPushButton("📊 Excel")
        export_excel_btn.setProperty("class", "secondary")
        export_excel_btn.clicked.connect(self._export_excel)
        filters_layout.addWidget(export_excel_btn)
        
        export_pdf_btn = QPushButton("📄 PDF")
        export_pdf_btn.setProperty("class", "secondary")
        export_pdf_btn.clicked.connect(self._export_pdf)
        filters_layout.addWidget(export_pdf_btn)
        
        print_btn = QPushButton("🖨️ طباعة")
        print_btn.setProperty("class", "secondary")
        print_btn.clicked.connect(self._print_statement)
        filters_layout.addWidget(print_btn)
        
        layout.addWidget(filters_frame)
        
        # Customer info and balance summary
        # Requirements: 3.1 - Display opening balance and closing balance
        summary_frame = Card()
        summary_layout = QGridLayout(summary_frame)
        summary_layout.setContentsMargins(16, 16, 16, 16)
        summary_layout.setSpacing(12)
        
        # Customer info
        summary_layout.addWidget(QLabel("اسم العميل:"), 0, 0)
        self.customer_name_label = QLabel("-")
        self.customer_name_label.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_BODY, QFont.Bold))
        summary_layout.addWidget(self.customer_name_label, 0, 1)
        
        summary_layout.addWidget(QLabel("كود العميل:"), 0, 2)
        self.customer_code_label = QLabel("-")
        summary_layout.addWidget(self.customer_code_label, 0, 3)
        
        # Opening balance
        summary_layout.addWidget(QLabel("الرصيد الافتتاحي:"), 1, 0)
        self.opening_balance_label = QLabel("0.00 ل.س")
        self.opening_balance_label.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_BODY, QFont.Bold))
        summary_layout.addWidget(self.opening_balance_label, 1, 1)
        
        # Total debits (invoices)
        summary_layout.addWidget(QLabel("إجمالي المدين:"), 1, 2)
        self.total_debit_label = QLabel("0.00 ل.س")
        self.total_debit_label.setStyleSheet(f"color: {Colors.DANGER};")
        summary_layout.addWidget(self.total_debit_label, 1, 3)
        
        # Total credits (payments)
        summary_layout.addWidget(QLabel("إجمالي الدائن:"), 2, 0)
        self.total_credit_label = QLabel("0.00 ل.س")
        self.total_credit_label.setStyleSheet(f"color: {Colors.SUCCESS};")
        summary_layout.addWidget(self.total_credit_label, 2, 1)
        
        # Closing balance
        summary_layout.addWidget(QLabel("الرصيد الختامي:"), 2, 2)
        self.closing_balance_label = QLabel("0.00 ل.س")
        self.closing_balance_label.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_H3, QFont.Bold))
        self.closing_balance_label.setStyleSheet(f"color: {Colors.PRIMARY};")
        summary_layout.addWidget(self.closing_balance_label, 2, 3)
        
        layout.addWidget(summary_frame)
        
        # Transactions table
        # Requirements: 3.2, 3.3, 3.6 - Show transactions with running balance and type
        table_card = Card()
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(16, 16, 16, 16)
        table_layout.setSpacing(12)
        
        table_header = QHBoxLayout()
        table_title = QLabel("حركات الحساب")
        table_title.setProperty("class", "h2")
        table_header.addWidget(table_title)
        table_header.addStretch()
        
        self.transaction_count_label = QLabel("0 حركة")
        self.transaction_count_label.setProperty("class", "subtitle")
        table_header.addWidget(self.transaction_count_label)
        
        table_layout.addLayout(table_header)
        
        # Transactions table
        self.transactions_table = QTableWidget()
        self.transactions_table.setColumnCount(7)
        self.transactions_table.setHorizontalHeaderLabels([
            'التاريخ',
            'النوع',
            'المرجع',
            'البيان',
            'مدين',
            'دائن',
            'الرصيد'  # Running balance column
        ])
        self.transactions_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.transactions_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.transactions_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.transactions_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.transactions_table.verticalHeader().setVisible(False)
        self.transactions_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.transactions_table.setAlternatingRowColors(True)
        
        table_layout.addWidget(self.transactions_table)
        
        layout.addWidget(table_card, 1)
    
    @handle_ui_error
    def refresh(self):
        """Refresh customers list from API."""
        response = api.get_customers()
        if isinstance(response, dict) and 'results' in response:
            self.customers_cache = response['results']
        else:
            self.customers_cache = response if isinstance(response, list) else []
        
        # Update combo box
        current_selection = self.customer_combo.currentData()
        self.customer_combo.clear()
        self.customer_combo.addItem("-- اختر العميل --", None)
        
        for customer in self.customers_cache:
            display_text = f"{customer.get('name', '')} ({customer.get('code', '')})"
            self.customer_combo.addItem(display_text, customer)
        
        # Restore selection if possible
        if current_selection:
            for i in range(self.customer_combo.count()):
                if self.customer_combo.itemData(i) == current_selection:
                    self.customer_combo.setCurrentIndex(i)
                    break
    
    def _on_customer_selected(self, index: int):
        """Handle customer selection change."""
        if index <= 0:
            self.selected_customer = None
            self._clear_statement()
            return
        
        self.selected_customer = self.customer_combo.currentData()
        if self.selected_customer:
            self._load_statement()
    
    def _clear_statement(self):
        """Clear the statement display."""
        self.customer_name_label.setText("-")
        self.customer_code_label.setText("-")
        self.opening_balance_label.setText("0.00 ل.س")
        self.total_debit_label.setText("0.00 ل.س")
        self.total_credit_label.setText("0.00 ل.س")
        self.closing_balance_label.setText("0.00 ل.س")
        self.transactions_table.setRowCount(0)
        self.transaction_count_label.setText("0 حركة")
        self.transactions = []
        self.statement_data = {}
    
    @handle_ui_error
    def _load_statement(self):
        """
        Load customer statement from API.
        
        Requirements: 3.1, 3.2, 3.3, 3.4, 3.6
        """
        if not self.selected_customer:
            MessageDialog.warning(self, "تنبيه", "يرجى اختيار العميل أولاً")
            return
        
        customer_id = self.selected_customer.get('id')
        start_date = self.from_date.date().toString('yyyy-MM-dd')
        end_date = self.to_date.date().toString('yyyy-MM-dd')
        
        # Fetch statement data
        self.statement_data = api.get_customer_statement(
            customer_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # Update customer info
        self._update_customer_info()
        
        # Update summary
        self._update_summary()
        
        # Update transactions table
        self._update_transactions_table()
    
    def _update_customer_info(self):
        """Update customer info display."""
        if self.selected_customer:
            self.customer_name_label.setText(self.selected_customer.get('name', '-'))
            self.customer_code_label.setText(self.selected_customer.get('code', '-'))
    
    def _update_summary(self):
        """
        Update the balance summary.
        
        Requirements: 3.1 - Display opening balance and closing balance
        """
        opening = float(self.statement_data.get('opening_balance', 0))
        closing = float(self.statement_data.get('closing_balance', 0))
        
        # Backend returns total_invoices, total_payments, total_returns
        total_debit = float(self.statement_data.get('total_invoices', 0))
        total_payments = float(self.statement_data.get('total_payments', 0))
        total_returns = float(self.statement_data.get('total_returns', 0))
        total_credit = total_payments + total_returns
        
        self.opening_balance_label.setText(f"{opening:,.2f} ل.س")
        self.closing_balance_label.setText(f"{closing:,.2f} ل.س")
        self.total_debit_label.setText(f"{total_debit:,.2f} ل.س")
        self.total_credit_label.setText(f"{total_credit:,.2f} ل.س")
        
        # Color code closing balance
        if closing > 0:
            self.closing_balance_label.setStyleSheet(f"color: {Colors.DANGER};")
        elif closing < 0:
            self.closing_balance_label.setStyleSheet(f"color: {Colors.SUCCESS};")
        else:
            self.closing_balance_label.setStyleSheet(f"color: {Colors.PRIMARY};")
    
    def _update_transactions_table(self):
        """
        Update the transactions table with running balance.
        
        Requirements: 3.2, 3.3, 3.6 - Show transactions with type and running balance
        """
        self.transactions = self.statement_data.get('transactions', [])
        
        self.transactions_table.setRowCount(len(self.transactions))
        self.transaction_count_label.setText(f"{len(self.transactions)} حركة")
        
        for row, transaction in enumerate(self.transactions):
            # Date
            date_item = QTableWidgetItem(str(transaction.get('date', '')))
            self.transactions_table.setItem(row, 0, date_item)
            
            # Transaction type
            # Requirements: 3.6 - Display transaction type clearly
            trans_type = transaction.get('type', '')
            type_display = self._get_transaction_type_display(trans_type)
            type_item = QTableWidgetItem(type_display)
            type_item.setTextAlignment(Qt.AlignCenter)
            
            # Color code by type
            if trans_type == 'invoice':
                type_item.setForeground(QColor(Colors.DANGER))
            elif trans_type == 'payment':
                type_item.setForeground(QColor(Colors.SUCCESS))
            elif trans_type == 'return':
                type_item.setForeground(QColor(Colors.WARNING))
            
            self.transactions_table.setItem(row, 1, type_item)
            
            # Reference (invoice number, payment receipt, etc.)
            reference = transaction.get('reference', '')
            self.transactions_table.setItem(row, 2, QTableWidgetItem(str(reference)))
            
            # Description
            description = transaction.get('description', '')
            self.transactions_table.setItem(row, 3, QTableWidgetItem(str(description)))
            
            # Debit amount (increases balance - invoices)
            debit = float(transaction.get('debit', 0))
            debit_item = QTableWidgetItem(f"{debit:,.2f}" if debit > 0 else "-")
            debit_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if debit > 0:
                debit_item.setForeground(QColor(Colors.DANGER))
            self.transactions_table.setItem(row, 4, debit_item)
            
            # Credit amount (decreases balance - payments)
            credit = float(transaction.get('credit', 0))
            credit_item = QTableWidgetItem(f"{credit:,.2f}" if credit > 0 else "-")
            credit_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if credit > 0:
                credit_item.setForeground(QColor(Colors.SUCCESS))
            self.transactions_table.setItem(row, 5, credit_item)
            
            # Running balance
            # Requirements: 3.3 - Calculate running balance after each transaction
            balance = float(transaction.get('balance', 0))
            balance_item = QTableWidgetItem(f"{balance:,.2f}")
            balance_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            balance_item.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_BODY, QFont.Bold))
            
            # Color code balance
            if balance > 0:
                balance_item.setForeground(QColor(Colors.DANGER))
            elif balance < 0:
                balance_item.setForeground(QColor(Colors.SUCCESS))
            
            self.transactions_table.setItem(row, 6, balance_item)
    
    def _get_transaction_type_display(self, trans_type: str) -> str:
        """
        Get display text for transaction type.
        
        Requirements: 3.6 - Display transaction type clearly
        """
        type_map = {
            'invoice': 'فاتورة',
            'payment': 'دفعة',
            'return': 'مرتجع',
            'opening': 'رصيد افتتاحي',
            'adjustment': 'تسوية'
        }
        return type_map.get(trans_type, trans_type)
    
    def set_customer(self, customer: Dict):
        """
        Set the customer to display statement for.
        
        Used when navigating from other views (e.g., receivables report).
        """
        self.selected_customer = customer
        
        # Find and select in combo
        for i in range(self.customer_combo.count()):
            item_data = self.customer_combo.itemData(i)
            if item_data and item_data.get('id') == customer.get('id'):
                self.customer_combo.setCurrentIndex(i)
                break
        
        self._load_statement()
    
    def _export_excel(self):
        """
        Export statement to Excel.
        
        Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6
        """
        if not self.selected_customer:
            MessageDialog.warning(self, "تنبيه", "يرجى اختيار العميل أولاً")
            return
        
        if not self.transactions:
            MessageDialog.warning(self, "تنبيه", "لا توجد بيانات للتصدير")
            return
        
        try:
            # Define columns for export
            columns = [
                ('date', 'التاريخ'),
                ('type_display', 'النوع'),
                ('reference', 'المرجع'),
                ('description', 'البيان'),
                ('debit', 'مدين'),
                ('credit', 'دائن'),
                ('balance', 'الرصيد')
            ]
            
            # Prepare data with display values
            export_data = []
            for trans in self.transactions:
                trans_type = trans.get('type', '')
                type_display = self._get_transaction_type_display(trans_type)
                
                export_data.append({
                    'date': trans.get('date', ''),
                    'type_display': type_display,
                    'reference': trans.get('reference', ''),
                    'description': trans.get('description', ''),
                    'debit': float(trans.get('debit', 0)),
                    'credit': float(trans.get('credit', 0)),
                    'balance': float(trans.get('balance', 0))
                })
            
            # Generate filename with customer name and date
            customer_name = self.selected_customer.get('name', 'عميل')
            filename = f"كشف_حساب_{customer_name}_{datetime.now().strftime('%Y%m%d')}.xlsx"
            
            # Prepare summary data
            opening = float(self.statement_data.get('opening_balance', 0))
            closing = float(self.statement_data.get('closing_balance', 0))
            total_debit = float(self.statement_data.get('total_invoices', 0))
            total_payments = float(self.statement_data.get('total_payments', 0))
            total_returns = float(self.statement_data.get('total_returns', 0))
            
            summary_data = {
                'اسم العميل': self.selected_customer.get('name', ''),
                'كود العميل': self.selected_customer.get('code', ''),
                'الرصيد الافتتاحي': f"{opening:,.2f} ل.س",
                'إجمالي المدين': f"{total_debit:,.2f} ل.س",
                'إجمالي الدائن': f"{(total_payments + total_returns):,.2f} ل.س",
                'الرصيد الختامي': f"{closing:,.2f} ل.س"
            }
            
            # Export to Excel
            success = ExportService.export_to_excel(
                data=export_data,
                columns=columns,
                filename=filename,
                title="كشف حساب العميل",
                parent=self,
                summary=summary_data
            )
            
            if success:
                MessageDialog.info(self, "نجاح", "تم تصدير الكشف بنجاح")
                
        except ExportError as e:
            MessageDialog.error(self, "خطأ", e.message)
        except Exception as e:
            MessageDialog.error(self, "خطأ", f"فشل تصدير الكشف: {str(e)}")
    
    def _export_pdf(self):
        """
        Export statement to PDF.
        
        Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7
        """
        if not self.selected_customer:
            MessageDialog.warning(self, "تنبيه", "يرجى اختيار العميل أولاً")
            return
        
        if not self.transactions:
            MessageDialog.warning(self, "تنبيه", "لا توجد بيانات للتصدير")
            return
        
        try:
            # Define columns for export
            columns = [
                ('date', 'التاريخ'),
                ('type_display', 'النوع'),
                ('reference', 'المرجع'),
                ('description', 'البيان'),
                ('debit', 'مدين'),
                ('credit', 'دائن'),
                ('balance', 'الرصيد')
            ]
            
            # Prepare data with display values
            export_data = []
            for trans in self.transactions:
                trans_type = trans.get('type', '')
                type_display = self._get_transaction_type_display(trans_type)
                
                export_data.append({
                    'date': trans.get('date', ''),
                    'type_display': type_display,
                    'reference': trans.get('reference', ''),
                    'description': trans.get('description', ''),
                    'debit': float(trans.get('debit', 0)),
                    'credit': float(trans.get('credit', 0)),
                    'balance': float(trans.get('balance', 0))
                })
            
            # Generate filename with customer name and date
            customer_name = self.selected_customer.get('name', 'عميل')
            filename = f"كشف_حساب_{customer_name}_{datetime.now().strftime('%Y%m%d')}.pdf"
            
            # Prepare summary data
            opening = float(self.statement_data.get('opening_balance', 0))
            closing = float(self.statement_data.get('closing_balance', 0))
            total_debit = float(self.statement_data.get('total_invoices', 0))
            total_payments = float(self.statement_data.get('total_payments', 0))
            total_returns = float(self.statement_data.get('total_returns', 0))
            
            summary_data = {
                'اسم العميل': self.selected_customer.get('name', ''),
                'كود العميل': self.selected_customer.get('code', ''),
                'الرصيد الافتتاحي': f"{opening:,.2f} ل.س",
                'إجمالي المدين': f"{total_debit:,.2f} ل.س",
                'إجمالي الدائن': f"{(total_payments + total_returns):,.2f} ل.س",
                'الرصيد الختامي': f"{closing:,.2f} ل.س"
            }
            
            # Get date range
            start_date = self.from_date.date().toString('yyyy-MM-dd')
            end_date = self.to_date.date().toString('yyyy-MM-dd')
            
            # Export to PDF
            success = ExportService.export_to_pdf(
                data=export_data,
                columns=columns,
                filename=filename,
                title="كشف حساب العميل",
                parent=self,
                summary=summary_data,
                date_range=(start_date, end_date)
            )
            
            if success:
                MessageDialog.info(self, "نجاح", "تم تصدير الكشف بنجاح")
                
        except ExportError as e:
            MessageDialog.error(self, "خطأ", e.message)
        except Exception as e:
            MessageDialog.error(self, "خطأ", f"فشل تصدير الكشف: {str(e)}")
    
    def _print_statement(self):
        """
        Print the customer statement.
        
        Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
        """
        if not self.selected_customer:
            MessageDialog.warning(self, "تنبيه", "يرجى اختيار العميل أولاً")
            return
        
        if not self.transactions:
            MessageDialog.warning(self, "تنبيه", "لا توجد بيانات للطباعة")
            return
        
        try:
            # Prepare customer info
            customer_info = {
                'name': self.selected_customer.get('name', ''),
                'code': self.selected_customer.get('code', '')
            }
            
            # Get date range
            start_date = self.from_date.date().toString('yyyy-MM-dd')
            end_date = self.to_date.date().toString('yyyy-MM-dd')
            
            # Generate HTML content for printing
            html_content = ExportService.generate_statement_html(
                customer_info=customer_info,
                statement_data=self.statement_data,
                transactions=self.transactions,
                date_range=(start_date, end_date)
            )
            
            # Print the document
            ExportService.print_document(
                html_content=html_content,
                parent=self,
                title=f"كشف حساب - {customer_info['name']}"
            )
            
        except ExportError as e:
            MessageDialog.error(self, "خطأ", e.message)
        except Exception as e:
            MessageDialog.error(self, "خطأ", f"فشل الطباعة: {str(e)}")
