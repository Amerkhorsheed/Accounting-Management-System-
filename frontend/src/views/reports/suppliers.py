"""
Suppliers Report View - تقرير الموردين

This module provides the UI for viewing the suppliers report showing
supplier statistics, purchase history, and payment status.

Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6
"""
from typing import List, Dict
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QDateEdit, QAbstractItemView
)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QFont, QColor

from ...config import Colors, Fonts
from ...widgets.cards import Card, StatCard
from ...widgets.dialogs import MessageDialog
from ...services.api import api, ApiException
from ...services.export import ExportService, ExportError
from ...utils.error_handler import handle_ui_error


class SuppliersReportView(QWidget):
    """
    Suppliers Report View showing supplier statistics and purchase history.
    
    Displays:
    - Summary cards (total suppliers, active suppliers, total payables)
    - Supplier list table with purchase totals and outstanding balances
    - Date range filter
    
    Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6
    """
    
    back_requested = Signal()  # Emitted when back button is clicked
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.report_data: Dict = {}
        self.suppliers_list: List[Dict] = []
        self.setup_ui()
    
    def go_back(self):
        """Navigate back to main reports view."""
        self.back_requested.emit()
        
    def setup_ui(self):
        """Initialize the suppliers report UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header with back button and title
        # Requirements: 1.1 - Display suppliers report view
        header = QHBoxLayout()
        
        # Back button
        back_btn = QPushButton("→ رجوع")
        back_btn.setProperty("class", "secondary")
        back_btn.clicked.connect(self.go_back)
        header.addWidget(back_btn)
        
        title = QLabel("تقرير الموردين")
        title.setProperty("class", "title")
        header.addWidget(title)
        header.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton("🔄 تحديث")
        refresh_btn.setProperty("class", "secondary")
        refresh_btn.clicked.connect(self.refresh)
        header.addWidget(refresh_btn)
        
        # Export buttons (placeholders for future implementation)
        export_excel_btn = QPushButton("📊 Excel")
        export_excel_btn.setProperty("class", "secondary")
        export_excel_btn.clicked.connect(self._export_excel)
        header.addWidget(export_excel_btn)
        
        export_pdf_btn = QPushButton("📄 PDF")
        export_pdf_btn.setProperty("class", "secondary")
        export_pdf_btn.clicked.connect(self._export_pdf)
        header.addWidget(export_pdf_btn)
        
        layout.addLayout(header)
        
        # Date range filter section
        # Requirements: 1.5, 1.6 - Support filtering by date range
        filters_frame = Card()
        filters_layout = QHBoxLayout(filters_frame)
        filters_layout.setContentsMargins(16, 12, 16, 12)
        filters_layout.setSpacing(16)
        
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
        # Requirements: 1.2 - Display total suppliers, active suppliers, total payables
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)
        
        # Total suppliers card
        self.total_suppliers_card = StatCard(
            title="إجمالي الموردين",
            value="0",
            icon="🏭",
            color=Colors.PRIMARY
        )
        cards_layout.addWidget(self.total_suppliers_card)
        
        # Active suppliers card
        self.active_suppliers_card = StatCard(
            title="الموردين النشطين",
            value="0",
            icon="✅",
            color=Colors.SUCCESS
        )
        cards_layout.addWidget(self.active_suppliers_card)
        
        # Total payables card
        self.total_payables_card = StatCard(
            title="إجمالي المستحقات",
            value="0.00 ل.س",
            icon="💰",
            color=Colors.DANGER
        )
        cards_layout.addWidget(self.total_payables_card)
        
        # Total purchases card
        self.total_purchases_card = StatCard(
            title="إجمالي المشتريات",
            value="0.00 ل.س",
            icon="📦",
            color=Colors.INFO
        )
        cards_layout.addWidget(self.total_purchases_card)
        
        layout.addLayout(cards_layout)
        
        # Suppliers table section
        # Requirements: 1.3, 1.4 - List suppliers sorted by purchase amount with details
        table_card = Card()
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(16, 16, 16, 16)
        table_layout.setSpacing(12)
        
        table_header = QHBoxLayout()
        table_title = QLabel("قائمة الموردين")
        table_title.setProperty("class", "h2")
        table_header.addWidget(table_title)
        table_header.addStretch()
        table_layout.addLayout(table_header)
        
        # Suppliers table
        # Requirements: 1.4 - Show supplier name, code, total purchases, payments, balance
        self.suppliers_table = QTableWidget()
        self.suppliers_table.setColumnCount(7)
        self.suppliers_table.setHorizontalHeaderLabels([
            'كود المورد',
            'اسم المورد',
            'إجمالي المشتريات',
            'إجمالي المدفوعات',
            'الرصيد المستحق',
            'عدد الطلبات',
            'آخر عملية شراء'
        ])
        self.suppliers_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.suppliers_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.suppliers_table.verticalHeader().setVisible(False)
        self.suppliers_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.suppliers_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.suppliers_table.setAlternatingRowColors(True)
        
        table_layout.addWidget(self.suppliers_table)
        
        layout.addWidget(table_card, 1)
    
    @handle_ui_error
    def refresh(self):
        """Refresh the suppliers report data from API."""
        self._load_report()
    
    @handle_ui_error
    def _apply_filters(self):
        """Apply filters and reload the report."""
        self._load_report()
    
    def _load_report(self):
        """
        Load suppliers report data from API.
        
        Requirements: 1.5, 1.6 - Support date range filtering and recalculate
        """
        # Build filter parameters
        start_date = self.from_date.date().toString('yyyy-MM-dd')
        end_date = self.to_date.date().toString('yyyy-MM-dd')
        
        # Fetch report data
        self.report_data = api.get_suppliers_report(
            start_date=start_date,
            end_date=end_date
        )
        
        # Update summary cards
        self._update_summary_cards()
        
        # Update suppliers table
        self._update_suppliers_table()
    
    def _update_summary_cards(self):
        """
        Update the summary cards with report data.
        
        Requirements: 1.2 - Display total suppliers, active suppliers, total payables
        """
        summary = self.report_data.get('summary', {})
        total_suppliers = int(summary.get('total_suppliers', 0))
        active_suppliers = int(summary.get('active_suppliers', 0))
        total_payables = float(summary.get('total_payables', 0))
        total_purchases = float(summary.get('total_purchases', 0))
        
        self.total_suppliers_card.update_value(str(total_suppliers))
        self.active_suppliers_card.update_value(str(active_suppliers))
        self.total_payables_card.update_value(f"{total_payables:,.2f} ل.س")
        self.total_purchases_card.update_value(f"{total_purchases:,.2f} ل.س")
    
    def _update_suppliers_table(self):
        """
        Update the suppliers table with report data.
        
        Requirements: 1.3 - List suppliers sorted by total purchase amount descending
        Requirements: 1.4 - Show supplier name, code, purchases, payments, balance
        """
        suppliers = self.report_data.get('suppliers', [])
        self.suppliers_list = suppliers
        
        self.suppliers_table.setRowCount(len(suppliers))
        
        for row, supplier in enumerate(suppliers):
            # Supplier code
            code_item = QTableWidgetItem(str(supplier.get('code', '')))
            code_item.setData(Qt.UserRole, supplier)
            self.suppliers_table.setItem(row, 0, code_item)
            
            # Supplier name
            self.suppliers_table.setItem(row, 1, QTableWidgetItem(
                str(supplier.get('name', ''))
            ))
            
            # Total purchases
            total_purchases = float(supplier.get('total_purchases', 0))
            purchases_item = QTableWidgetItem(f"{total_purchases:,.2f}")
            purchases_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.suppliers_table.setItem(row, 2, purchases_item)
            
            # Total payments
            total_payments = float(supplier.get('total_payments', 0))
            payments_item = QTableWidgetItem(f"{total_payments:,.2f}")
            payments_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            payments_item.setForeground(QColor(Colors.SUCCESS))
            self.suppliers_table.setItem(row, 3, payments_item)
            
            # Outstanding balance
            outstanding = float(supplier.get('outstanding_balance', 0))
            balance_item = QTableWidgetItem(f"{outstanding:,.2f}")
            balance_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            # Color code based on balance
            if outstanding > 0:
                balance_item.setForeground(QColor(Colors.DANGER))
            else:
                balance_item.setForeground(QColor(Colors.SUCCESS))
            self.suppliers_table.setItem(row, 4, balance_item)
            
            # Purchase order count
            order_count = int(supplier.get('purchase_order_count', 0))
            count_item = QTableWidgetItem(str(order_count))
            count_item.setTextAlignment(Qt.AlignCenter)
            self.suppliers_table.setItem(row, 5, count_item)
            
            # Last purchase date
            last_purchase = supplier.get('last_purchase_date', '')
            date_item = QTableWidgetItem(str(last_purchase) if last_purchase else '-')
            date_item.setTextAlignment(Qt.AlignCenter)
            self.suppliers_table.setItem(row, 6, date_item)
    
    def _export_excel(self):
        """
        Export report to Excel.
        
        Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6
        """
        if not self.suppliers_list:
            MessageDialog.warning(self, "تنبيه", "لا توجد بيانات للتصدير")
            return
        
        try:
            # Define columns for export
            columns = [
                ('code', 'كود المورد'),
                ('name', 'اسم المورد'),
                ('total_purchases', 'إجمالي المشتريات'),
                ('total_payments', 'إجمالي المدفوعات'),
                ('outstanding_balance', 'الرصيد المستحق'),
                ('purchase_order_count', 'عدد الطلبات'),
                ('last_purchase_date', 'آخر عملية شراء')
            ]
            
            # Prepare data
            export_data = []
            for supplier in self.suppliers_list:
                export_data.append({
                    'code': supplier.get('code', ''),
                    'name': supplier.get('name', ''),
                    'total_purchases': float(supplier.get('total_purchases', 0)),
                    'total_payments': float(supplier.get('total_payments', 0)),
                    'outstanding_balance': float(supplier.get('outstanding_balance', 0)),
                    'purchase_order_count': int(supplier.get('purchase_order_count', 0)),
                    'last_purchase_date': supplier.get('last_purchase_date', '') or '-'
                })
            
            # Generate filename with date
            filename = f"تقرير_الموردين_{datetime.now().strftime('%Y%m%d')}.xlsx"
            
            # Prepare summary data
            summary = self.report_data.get('summary', {})
            summary_data = {
                'إجمالي الموردين': str(summary.get('total_suppliers', 0)),
                'الموردين النشطين': str(summary.get('active_suppliers', 0)),
                'إجمالي المستحقات': f"{float(summary.get('total_payables', 0)):,.2f} ل.س",
                'إجمالي المشتريات': f"{float(summary.get('total_purchases', 0)):,.2f} ل.س"
            }
            
            # Export to Excel
            success = ExportService.export_to_excel(
                data=export_data,
                columns=columns,
                filename=filename,
                title="تقرير الموردين",
                parent=self,
                summary=summary_data
            )
            
            if success:
                MessageDialog.info(self, "نجاح", "تم تصدير التقرير بنجاح")
                
        except ExportError as e:
            MessageDialog.error(self, "خطأ", e.message)
        except Exception as e:
            MessageDialog.error(self, "خطأ", f"فشل تصدير التقرير: {str(e)}")
    
    def _export_pdf(self):
        """
        Export report to PDF.
        
        Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7
        """
        if not self.suppliers_list:
            MessageDialog.warning(self, "تنبيه", "لا توجد بيانات للتصدير")
            return
        
        try:
            # Define columns for export
            columns = [
                ('code', 'كود المورد'),
                ('name', 'اسم المورد'),
                ('total_purchases', 'إجمالي المشتريات'),
                ('total_payments', 'إجمالي المدفوعات'),
                ('outstanding_balance', 'الرصيد المستحق'),
                ('purchase_order_count', 'عدد الطلبات')
            ]
            
            # Prepare data
            export_data = []
            for supplier in self.suppliers_list:
                export_data.append({
                    'code': supplier.get('code', ''),
                    'name': supplier.get('name', ''),
                    'total_purchases': float(supplier.get('total_purchases', 0)),
                    'total_payments': float(supplier.get('total_payments', 0)),
                    'outstanding_balance': float(supplier.get('outstanding_balance', 0)),
                    'purchase_order_count': int(supplier.get('purchase_order_count', 0))
                })
            
            # Generate filename with date
            filename = f"تقرير_الموردين_{datetime.now().strftime('%Y%m%d')}.pdf"
            
            # Prepare summary data
            summary = self.report_data.get('summary', {})
            summary_data = {
                'إجمالي الموردين': str(summary.get('total_suppliers', 0)),
                'الموردين النشطين': str(summary.get('active_suppliers', 0)),
                'إجمالي المستحقات': f"{float(summary.get('total_payables', 0)):,.2f} ل.س",
                'إجمالي المشتريات': f"{float(summary.get('total_purchases', 0)):,.2f} ل.س"
            }
            
            # Get date range
            start_date = self.from_date.date().toString('yyyy-MM-dd')
            end_date = self.to_date.date().toString('yyyy-MM-dd')
            
            # Export to PDF
            success = ExportService.export_to_pdf(
                data=export_data,
                columns=columns,
                filename=filename,
                title="تقرير الموردين",
                parent=self,
                summary=summary_data,
                date_range=(start_date, end_date)
            )
            
            if success:
                MessageDialog.info(self, "نجاح", "تم تصدير التقرير بنجاح")
                
        except ExportError as e:
            MessageDialog.error(self, "خطأ", e.message)
        except Exception as e:
            MessageDialog.error(self, "خطأ", f"فشل تصدير التقرير: {str(e)}")
