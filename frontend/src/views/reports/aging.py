"""
Aging Report View - تقرير أعمار الديون

This module provides the UI for viewing the aging report showing
overdue invoices categorized by age buckets.

Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
"""
from typing import List, Dict, Optional
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QGridLayout, QScrollArea,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QDateEdit, QAbstractItemView, QTabWidget
)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QFont, QColor

from ...config import Colors, Fonts, config
from ...widgets.cards import Card, StatCard
from ...widgets.dialogs import MessageDialog
from ...services.api import api, ApiException
from ...services.export import ExportService, ExportError
from ...utils.error_handler import handle_ui_error


class AgingReportView(QWidget):
    """
    Aging Report View showing overdue invoices by age categories.
    
    Displays:
    - Aging buckets visualization (cards showing totals per category)
    - Customer breakdown table with aging details
    - Visual highlighting for severely overdue amounts (>60 days)
    - Drill-down to individual invoices per category
    
    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
    """
    
    invoice_selected = Signal(dict)  # Emitted when an invoice is clicked
    back_requested = Signal()  # Emitted when back button is clicked
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.report_data: Dict = {}
        self.aging_buckets: Dict = {}
        self.setup_ui()
    
    def go_back(self):
        """Navigate back to main reports view."""
        self.back_requested.emit()
        
    def setup_ui(self):
        """Initialize the aging report UI."""
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
        
        title = QLabel("تقرير أعمار الديون")
        title.setProperty("class", "title")
        header.addWidget(title)
        header.addStretch()
        
        # As of date selector
        header.addWidget(QLabel("كما في تاريخ:"))
        self.as_of_date = QDateEdit()
        self.as_of_date.setCalendarPopup(True)
        self.as_of_date.setDate(QDate.currentDate())
        header.addWidget(self.as_of_date)
        
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
        
        # Aging buckets cards section
        # Requirements: 5.1, 5.3 - Categorize by age and display totals
        buckets_layout = QHBoxLayout()
        buckets_layout.setSpacing(12)
        
        # Current (not overdue) card
        self.current_card = self._create_bucket_card(
            "جاري (غير متأخر)",
            "0.00 ل.س",
            "✅",
            Colors.SUCCESS
        )
        buckets_layout.addWidget(self.current_card)
        
        # 1-30 days card
        self.days_1_30_card = self._create_bucket_card(
            "1-30 يوم",
            "0.00 ل.س",
            "📅",
            Colors.INFO
        )
        buckets_layout.addWidget(self.days_1_30_card)
        
        # 31-60 days card
        self.days_31_60_card = self._create_bucket_card(
            "31-60 يوم",
            "0.00 ل.س",
            "⏰",
            Colors.WARNING
        )
        buckets_layout.addWidget(self.days_31_60_card)
        
        # 61-90 days card - highlighted as severe
        # Requirements: 5.5 - Highlight severely overdue (>60 days)
        self.days_61_90_card = self._create_bucket_card(
            "61-90 يوم",
            "0.00 ل.س",
            "⚠️",
            Colors.DANGER
        )
        buckets_layout.addWidget(self.days_61_90_card)
        
        # Over 90 days card - highlighted as severe
        self.days_over_90_card = self._create_bucket_card(
            "أكثر من 90 يوم",
            "0.00 ل.س",
            "🚨",
            Colors.DANGER
        )
        buckets_layout.addWidget(self.days_over_90_card)
        
        layout.addLayout(buckets_layout)
        
        # Total outstanding summary
        total_frame = Card()
        total_layout = QHBoxLayout(total_frame)
        total_layout.setContentsMargins(16, 12, 16, 12)
        
        total_label = QLabel("إجمالي المستحقات:")
        total_label.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_H3, QFont.Bold))
        total_layout.addWidget(total_label)
        
        self.total_amount_label = QLabel("0.00 ل.س")
        self.total_amount_label.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_H2, QFont.Bold))
        self.total_amount_label.setStyleSheet(f"color: {Colors.PRIMARY};")
        total_layout.addWidget(self.total_amount_label)
        
        total_layout.addStretch()
        
        # Overdue percentage
        overdue_label = QLabel("نسبة المتأخر:")
        total_layout.addWidget(overdue_label)
        
        self.overdue_percent_label = QLabel("0%")
        self.overdue_percent_label.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_H3, QFont.Bold))
        total_layout.addWidget(self.overdue_percent_label)
        
        layout.addWidget(total_frame)
        
        # Tabbed view for customer breakdown and invoice details
        # Requirements: 5.4 - Allow drilling down to individual invoices
        self.tabs = QTabWidget()
        
        # Customer breakdown tab
        customer_tab = QWidget()
        customer_layout = QVBoxLayout(customer_tab)
        customer_layout.setContentsMargins(0, 12, 0, 0)
        
        self.customer_table = QTableWidget()
        self.customer_table.setColumnCount(7)
        self.customer_table.setHorizontalHeaderLabels([
            'العميل',
            'جاري',
            '1-30 يوم',
            '31-60 يوم',
            '61-90 يوم',
            '>90 يوم',
            'الإجمالي'
        ])
        self.customer_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.customer_table.verticalHeader().setVisible(False)
        self.customer_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.customer_table.setAlternatingRowColors(True)
        self.customer_table.doubleClicked.connect(self._on_customer_double_clicked)
        
        customer_layout.addWidget(self.customer_table)
        self.tabs.addTab(customer_tab, "تفصيل العملاء")
        
        # Invoice details tab
        invoice_tab = QWidget()
        invoice_layout = QVBoxLayout(invoice_tab)
        invoice_layout.setContentsMargins(0, 12, 0, 0)
        
        self.invoice_table = QTableWidget()
        self.invoice_table.setColumnCount(8)
        self.invoice_table.setHorizontalHeaderLabels([
            'رقم الفاتورة',
            'العميل',
            'تاريخ الفاتورة',
            'تاريخ الاستحقاق',
            'المبلغ',
            'المدفوع',
            'المتبقي',
            'أيام التأخير'
        ])
        self.invoice_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.invoice_table.verticalHeader().setVisible(False)
        self.invoice_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.invoice_table.setAlternatingRowColors(True)
        
        invoice_layout.addWidget(self.invoice_table)
        self.tabs.addTab(invoice_tab, "تفصيل الفواتير")
        
        layout.addWidget(self.tabs, 1)
    
    def _create_bucket_card(self, title: str, value: str, icon: str, color: str) -> Card:
        """Create an aging bucket card."""
        card = Card()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(8)
        card_layout.setAlignment(Qt.AlignCenter)
        
        # Icon
        icon_label = QLabel(icon)
        icon_label.setFont(QFont(Fonts.FAMILY_AR, 24))
        icon_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(icon_label)
        
        # Title
        title_label = QLabel(title)
        title_label.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_BODY))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setProperty("class", "subtitle")
        card_layout.addWidget(title_label)
        
        # Value
        value_label = QLabel(value)
        value_label.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_H3, QFont.Bold))
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setStyleSheet(f"color: {color};")
        value_label.setObjectName("bucket_value")
        card_layout.addWidget(value_label)
        
        # Invoice count
        count_label = QLabel("0 فاتورة")
        count_label.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_SMALL))
        count_label.setAlignment(Qt.AlignCenter)
        count_label.setProperty("class", "subtitle")
        count_label.setObjectName("bucket_count")
        card_layout.addWidget(count_label)
        
        return card
    
    def _update_bucket_card(self, card: Card, amount: float, count: int, color: str):
        """Update a bucket card with new values."""
        value_label = card.findChild(QLabel, "bucket_value")
        count_label = card.findChild(QLabel, "bucket_count")
        
        if value_label:
            value_label.setText(config.format_usd(amount))
            value_label.setStyleSheet(f"color: {color};")
        
        if count_label:
            count_label.setText(f"{count} فاتورة")
    
    @handle_ui_error
    def refresh(self):
        """Refresh the aging report data from API."""
        self._load_report()
    
    def _load_report(self):
        """
        Load aging report data from API.
        
        Requirements: 5.1, 5.2, 5.3
        """
        as_of_date = self.as_of_date.date().toString('yyyy-MM-dd')
        
        # Fetch report data
        self.report_data = api.get_aging_report(as_of_date=as_of_date)
        
        # Extract aging buckets (backend returns 'buckets' not 'aging_buckets')
        self.aging_buckets = self.report_data.get('buckets', {})
        
        # Update bucket cards
        self._update_bucket_cards()
        
        # Update customer breakdown table
        self._update_customer_table()
        
        # Update invoice details table
        self._update_invoice_table()
    
    def _update_bucket_cards(self):
        """
        Update the aging bucket cards with report data.
        
        Requirements: 5.1, 5.3 - Display totals for each aging category
        """
        buckets = self.aging_buckets
        
        # Current (not overdue)
        current = buckets.get('current', {})
        self._update_bucket_card(
            self.current_card,
            float(current.get('total_usd', current.get('total', 0)) or 0),
            int(current.get('invoice_count', 0)),
            Colors.SUCCESS
        )
        
        # 1-30 days
        days_1_30 = buckets.get('1_30', {})
        self._update_bucket_card(
            self.days_1_30_card,
            float(days_1_30.get('total_usd', days_1_30.get('total', 0)) or 0),
            int(days_1_30.get('invoice_count', 0)),
            Colors.INFO
        )
        
        # 31-60 days
        days_31_60 = buckets.get('31_60', {})
        self._update_bucket_card(
            self.days_31_60_card,
            float(days_31_60.get('total_usd', days_31_60.get('total', 0)) or 0),
            int(days_31_60.get('invoice_count', 0)),
            Colors.WARNING
        )
        
        # 61-90 days - severe
        days_61_90 = buckets.get('61_90', {})
        self._update_bucket_card(
            self.days_61_90_card,
            float(days_61_90.get('total_usd', days_61_90.get('total', 0)) or 0),
            int(days_61_90.get('invoice_count', 0)),
            Colors.DANGER
        )
        
        # Over 90 days - severe
        over_90 = buckets.get('over_90', {})
        self._update_bucket_card(
            self.days_over_90_card,
            float(over_90.get('total_usd', over_90.get('total', 0)) or 0),
            int(over_90.get('invoice_count', 0)),
            Colors.DANGER
        )
        
        # Update total from summary
        summary = self.report_data.get('summary', {})
        total = float(summary.get('total_outstanding_usd', summary.get('total_outstanding', 0)) or 0)
        self.total_amount_label.setText(config.format_usd(total))
        
        # Calculate overdue percentage (everything except current)
        overdue = (
            float(days_1_30.get('total_usd', days_1_30.get('total', 0)) or 0) +
            float(days_31_60.get('total_usd', days_31_60.get('total', 0)) or 0) +
            float(days_61_90.get('total_usd', days_61_90.get('total', 0)) or 0) +
            float(over_90.get('total_usd', over_90.get('total', 0)) or 0)
        )
        
        if total > 0:
            overdue_percent = (overdue / total) * 100
            self.overdue_percent_label.setText(f"{overdue_percent:.1f}%")
            
            # Color code the percentage
            if overdue_percent > 50:
                self.overdue_percent_label.setStyleSheet(f"color: {Colors.DANGER};")
            elif overdue_percent > 25:
                self.overdue_percent_label.setStyleSheet(f"color: {Colors.WARNING};")
            else:
                self.overdue_percent_label.setStyleSheet(f"color: {Colors.SUCCESS};")
        else:
            self.overdue_percent_label.setText("0%")
            self.overdue_percent_label.setStyleSheet(f"color: {Colors.SUCCESS};")
    
    def _update_customer_table(self):
        """
        Update the customer breakdown table.
        
        Requirements: 5.4 - Allow drilling down to see details
        """
        customers = self.report_data.get('customer_breakdown', [])
        
        self.customer_table.setRowCount(len(customers))
        
        for row, customer in enumerate(customers):
            # Customer name
            name_item = QTableWidgetItem(str(customer.get('customer_name', '')))
            name_item.setData(Qt.UserRole, customer)
            self.customer_table.setItem(row, 0, name_item)
            
            # Current amount
            current = float(customer.get('current_usd', customer.get('current', 0)) or 0)
            current_item = QTableWidgetItem(config.format_usd(current))
            current_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if current > 0:
                current_item.setForeground(QColor(Colors.SUCCESS))
            self.customer_table.setItem(row, 1, current_item)
            
            # 1-30 days
            days_1_30 = float(customer.get('1_30_usd', customer.get('1_30', 0)) or 0)
            days_1_30_item = QTableWidgetItem(config.format_usd(days_1_30))
            days_1_30_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if days_1_30 > 0:
                days_1_30_item.setForeground(QColor(Colors.INFO))
            self.customer_table.setItem(row, 2, days_1_30_item)
            
            # 31-60 days
            days_31_60 = float(customer.get('31_60_usd', customer.get('31_60', 0)) or 0)
            days_31_60_item = QTableWidgetItem(config.format_usd(days_31_60))
            days_31_60_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if days_31_60 > 0:
                days_31_60_item.setForeground(QColor(Colors.WARNING))
            self.customer_table.setItem(row, 3, days_31_60_item)
            
            # 61-90 days - severe highlighting
            # Requirements: 5.5 - Highlight severely overdue
            days_61_90 = float(customer.get('61_90_usd', customer.get('61_90', 0)) or 0)
            days_61_90_item = QTableWidgetItem(config.format_usd(days_61_90))
            days_61_90_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if days_61_90 > 0:
                days_61_90_item.setForeground(QColor(Colors.DANGER))
                days_61_90_item.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_BODY, QFont.Bold))
            self.customer_table.setItem(row, 4, days_61_90_item)
            
            # Over 90 days - severe highlighting
            over_90 = float(customer.get('over_90_usd', customer.get('over_90', 0)) or 0)
            over_90_item = QTableWidgetItem(config.format_usd(over_90))
            over_90_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if over_90 > 0:
                over_90_item.setForeground(QColor(Colors.DANGER))
                over_90_item.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_BODY, QFont.Bold))
                over_90_item.setBackground(QColor(Colors.DANGER + "20"))  # Light red background
            self.customer_table.setItem(row, 5, over_90_item)
            
            # Total
            total = float(customer.get('total_usd', customer.get('total', 0)) or 0)
            total_item = QTableWidgetItem(config.format_usd(total))
            total_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            total_item.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_BODY, QFont.Bold))
            self.customer_table.setItem(row, 6, total_item)
    
    def _update_invoice_table(self):
        """
        Update the invoice details table.
        
        Requirements: 5.2, 5.4, 5.5 - Show individual invoices with overdue highlighting
        """
        # Collect all invoices from all buckets
        invoices = []
        for bucket_key, bucket_data in self.aging_buckets.items():
            bucket_invoices = bucket_data.get('invoices', [])
            invoices.extend(bucket_invoices)
        
        # Sort by days overdue descending
        invoices.sort(key=lambda x: x.get('days_overdue', 0), reverse=True)
        
        self.invoice_table.setRowCount(len(invoices))
        
        for row, invoice in enumerate(invoices):
            # Invoice number
            number_item = QTableWidgetItem(str(invoice.get('invoice_number', '')))
            number_item.setData(Qt.UserRole, invoice)
            self.invoice_table.setItem(row, 0, number_item)
            
            # Customer name
            self.invoice_table.setItem(row, 1, QTableWidgetItem(
                str(invoice.get('customer_name', ''))
            ))
            
            # Invoice date
            self.invoice_table.setItem(row, 2, QTableWidgetItem(
                str(invoice.get('invoice_date', ''))
            ))
            
            # Due date
            due_date_item = QTableWidgetItem(str(invoice.get('due_date', '')))
            self.invoice_table.setItem(row, 3, due_date_item)
            
            # Total amount
            total = float(invoice.get('total_amount_usd', invoice.get('total_amount', 0)) or 0)
            total_item = QTableWidgetItem(config.format_usd(total))
            total_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.invoice_table.setItem(row, 4, total_item)
            
            # Paid amount
            paid = float(invoice.get('paid_amount_usd', invoice.get('paid_amount', 0)) or 0)
            paid_item = QTableWidgetItem(config.format_usd(paid))
            paid_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.invoice_table.setItem(row, 5, paid_item)
            
            # Remaining amount
            remaining = float(invoice.get('remaining_amount_usd', invoice.get('remaining_amount', 0)) or 0)
            remaining_item = QTableWidgetItem(config.format_usd(remaining))
            remaining_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            remaining_item.setForeground(QColor(Colors.DANGER))
            self.invoice_table.setItem(row, 6, remaining_item)
            
            # Days overdue
            days_overdue = int(invoice.get('days_overdue', 0))
            days_item = QTableWidgetItem(str(days_overdue) if days_overdue > 0 else "جاري")
            days_item.setTextAlignment(Qt.AlignCenter)
            
            # Color code and highlight based on days overdue
            # Requirements: 5.5 - Highlight severely overdue (>60 days)
            if days_overdue > 90:
                days_item.setForeground(QColor(Colors.DANGER))
                days_item.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_BODY, QFont.Bold))
                days_item.setBackground(QColor(Colors.DANGER + "20"))
            elif days_overdue > 60:
                days_item.setForeground(QColor(Colors.DANGER))
                days_item.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_BODY, QFont.Bold))
            elif days_overdue > 30:
                days_item.setForeground(QColor(Colors.WARNING))
            elif days_overdue > 0:
                days_item.setForeground(QColor(Colors.INFO))
            else:
                days_item.setForeground(QColor(Colors.SUCCESS))
            
            self.invoice_table.setItem(row, 7, days_item)
    
    def _on_customer_double_clicked(self, index):
        """Handle customer row double-click."""
        row = index.row()
        item = self.customer_table.item(row, 0)
        if item:
            customer = item.data(Qt.UserRole)
            if customer:
                # Could navigate to customer statement or filter invoices
                MessageDialog.info(
                    self,
                    "معلومات العميل",
                    f"العميل: {customer.get('name', '')}\n"
                    f"إجمالي المستحقات: {config.format_usd(float(customer.get('total_usd', customer.get('total', 0)) or 0))}"
                )
    
    def _export_excel(self):
        """
        Export report to Excel.
        
        Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6
        """
        customer_breakdown = self.report_data.get('customer_breakdown', [])
        
        if not customer_breakdown:
            MessageDialog.warning(self, "تنبيه", "لا توجد بيانات للتصدير")
            return
        
        try:
            # Define columns for export
            columns = [
                ('customer_name', 'العميل'),
                ('current', 'جاري'),
                ('1_30', '1-30 يوم'),
                ('31_60', '31-60 يوم'),
                ('61_90', '61-90 يوم'),
                ('over_90', '>90 يوم'),
                ('total', 'الإجمالي')
            ]
            
            # Prepare data
            export_data = []
            for customer in customer_breakdown:
                export_data.append({
                    'customer_name': customer.get('customer_name', ''),
                    'current': float(customer.get('current', 0)),
                    '1_30': float(customer.get('1_30', 0)),
                    '31_60': float(customer.get('31_60', 0)),
                    '61_90': float(customer.get('61_90', 0)),
                    'over_90': float(customer.get('over_90', 0)),
                    'total': float(customer.get('total', 0))
                })
            
            # Generate filename with date
            as_of_date = self.as_of_date.date().toString('yyyy-MM-dd')
            filename = f"تقرير_أعمار_الديون_{as_of_date}.xlsx"
            
            # Prepare summary data
            summary = self.report_data.get('summary', {})
            buckets = self.aging_buckets
            summary_data = {
                'إجمالي المستحقات': config.format_usd(float(summary.get('total_outstanding_usd', summary.get('total_outstanding', 0)) or 0)),
                'جاري (غير متأخر)': config.format_usd(float(buckets.get('current', {}).get('total_usd', buckets.get('current', {}).get('total', 0)) or 0)),
                '1-30 يوم': config.format_usd(float(buckets.get('1_30', {}).get('total_usd', buckets.get('1_30', {}).get('total', 0)) or 0)),
                '31-60 يوم': config.format_usd(float(buckets.get('31_60', {}).get('total_usd', buckets.get('31_60', {}).get('total', 0)) or 0)),
                '61-90 يوم': config.format_usd(float(buckets.get('61_90', {}).get('total_usd', buckets.get('61_90', {}).get('total', 0)) or 0)),
                'أكثر من 90 يوم': config.format_usd(float(buckets.get('over_90', {}).get('total_usd', buckets.get('over_90', {}).get('total', 0)) or 0))
            }
            
            # Export to Excel
            success = ExportService.export_to_excel(
                data=export_data,
                columns=columns,
                filename=filename,
                title="تقرير أعمار الديون",
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
        customer_breakdown = self.report_data.get('customer_breakdown', [])
        
        if not customer_breakdown:
            MessageDialog.warning(self, "تنبيه", "لا توجد بيانات للتصدير")
            return
        
        try:
            # Define columns for export
            columns = [
                ('customer_name', 'العميل'),
                ('current', 'جاري'),
                ('1_30', '1-30 يوم'),
                ('31_60', '31-60 يوم'),
                ('61_90', '61-90 يوم'),
                ('over_90', '>90 يوم'),
                ('total', 'الإجمالي')
            ]
            
            # Prepare data
            export_data = []
            for customer in customer_breakdown:
                export_data.append({
                    'customer_name': customer.get('customer_name', ''),
                    'current': float(customer.get('current', 0)),
                    '1_30': float(customer.get('1_30', 0)),
                    '31_60': float(customer.get('31_60', 0)),
                    '61_90': float(customer.get('61_90', 0)),
                    'over_90': float(customer.get('over_90', 0)),
                    'total': float(customer.get('total', 0))
                })
            
            # Generate filename with date
            as_of_date = self.as_of_date.date().toString('yyyy-MM-dd')
            filename = f"تقرير_أعمار_الديون_{as_of_date}.pdf"
            
            # Prepare summary data
            summary = self.report_data.get('summary', {})
            buckets = self.aging_buckets
            summary_data = {
                'إجمالي المستحقات': config.format_usd(float(summary.get('total_outstanding_usd', summary.get('total_outstanding', 0)) or 0)),
                'جاري (غير متأخر)': config.format_usd(float(buckets.get('current', {}).get('total_usd', buckets.get('current', {}).get('total', 0)) or 0)),
                '1-30 يوم': config.format_usd(float(buckets.get('1_30', {}).get('total_usd', buckets.get('1_30', {}).get('total', 0)) or 0)),
                '31-60 يوم': config.format_usd(float(buckets.get('31_60', {}).get('total_usd', buckets.get('31_60', {}).get('total', 0)) or 0)),
                '61-90 يوم': config.format_usd(float(buckets.get('61_90', {}).get('total_usd', buckets.get('61_90', {}).get('total', 0)) or 0)),
                'أكثر من 90 يوم': config.format_usd(float(buckets.get('over_90', {}).get('total_usd', buckets.get('over_90', {}).get('total', 0)) or 0))
            }
            
            # Export to PDF
            success = ExportService.export_to_pdf(
                data=export_data,
                columns=columns,
                filename=filename,
                title="تقرير أعمار الديون",
                parent=self,
                summary=summary_data,
                date_range=(as_of_date, as_of_date)
            )
            
            if success:
                MessageDialog.info(self, "نجاح", "تم تصدير التقرير بنجاح")
                
        except ExportError as e:
            MessageDialog.error(self, "خطأ", e.message)
        except Exception as e:
            MessageDialog.error(self, "خطأ", f"فشل تصدير التقرير: {str(e)}")
