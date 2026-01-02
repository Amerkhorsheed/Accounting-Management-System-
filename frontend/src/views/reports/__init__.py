"""
Reports View

Requirements: 4.1, 4.3 - Error handling for report generation operations
Requirements: 4.1-4.5 - Receivables report
Requirements: 5.1-5.5 - Aging report
Requirements: 3.1-3.6 - Customer statement
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QGridLayout, QPushButton, QDateEdit, QComboBox,
    QTabWidget, QScrollArea, QStackedWidget
)
from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtGui import QFont

from ...config import Colors, Fonts, config
from ...widgets.cards import Card
from ...widgets.dialogs import MessageDialog
from ...services.api import api, ApiException
from ...utils.error_handler import handle_ui_error

# Import new report views
from .receivables import ReceivablesReportView
from .aging import AgingReportView
from .customer_statement import CustomerStatementView
from .suppliers import SuppliersReportView
from .expenses import ExpensesReportView


class ReportsView(QWidget):
    """
    Reports and analytics view with navigation to detailed report views.
    
    Requirements: 4.1-4.5, 5.1-5.5
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Stacked widget for switching between main view and detail views
        self.stack = QStackedWidget()
        
        # Main reports grid view
        self.main_view = QWidget()
        self._setup_main_view()
        self.stack.addWidget(self.main_view)
        
        # Receivables report view
        self.receivables_view = ReceivablesReportView()
        self.receivables_view.customer_selected.connect(self._on_customer_selected_from_receivables)
        self.receivables_view.back_requested.connect(self.go_to_main)
        self.stack.addWidget(self.receivables_view)
        
        # Aging report view
        self.aging_view = AgingReportView()
        self.aging_view.back_requested.connect(self.go_to_main)
        self.stack.addWidget(self.aging_view)
        
        # Customer statement view
        self.statement_view = CustomerStatementView()
        self.statement_view.back_requested.connect(self.go_to_main)
        self.stack.addWidget(self.statement_view)
        
        # Suppliers report view
        self.suppliers_view = SuppliersReportView()
        self.suppliers_view.back_requested.connect(self.go_to_main)
        self.stack.addWidget(self.suppliers_view)
        
        # Expenses report view
        self.expenses_view = ExpensesReportView()
        self.expenses_view.back_requested.connect(self.go_to_main)
        self.stack.addWidget(self.expenses_view)
        
        main_layout.addWidget(self.stack)
    
    def _setup_main_view(self):
        """Setup the main reports grid view."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)
        
        # Header with date filters
        header = QHBoxLayout()
        
        title = QLabel("التقارير والإحصائيات")
        title.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_H2, QFont.Bold))
        header.addWidget(title)
        
        header.addStretch()
        
        # Date range
        header.addWidget(QLabel("من:"))
        self.from_date = QDateEdit()
        self.from_date.setDate(QDate.currentDate().addMonths(-1))
        self.from_date.setCalendarPopup(True)
        header.addWidget(self.from_date)
        
        header.addWidget(QLabel("إلى:"))
        self.to_date = QDateEdit()
        self.to_date.setDate(QDate.currentDate())
        self.to_date.setCalendarPopup(True)
        header.addWidget(self.to_date)
        
        apply_btn = QPushButton("تطبيق")
        apply_btn.clicked.connect(self.apply_filter)
        header.addWidget(apply_btn)
        
        layout.addLayout(header)
        
        # Credit/Receivables reports section (new)
        # Requirements: 4.1-4.5, 5.1-5.5
        credit_section_label = QLabel("تقارير الائتمان والمستحقات")
        credit_section_label.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_H3, QFont.Bold))
        credit_section_label.setStyleSheet(f"color: {Colors.PRIMARY}; margin-top: 8px;")
        layout.addWidget(credit_section_label)
        
        credit_reports_grid = QGridLayout()
        credit_reports_grid.setSpacing(16)
        
        credit_reports = [
            ("💰", "تقرير المستحقات", "receivables", Colors.PRIMARY, 
             "عرض إجمالي المستحقات وأرصدة العملاء"),
            ("⏰", "تقرير أعمار الديون", "aging", Colors.DANGER,
             "تصنيف المستحقات حسب فترة التأخير"),
            ("📋", "كشف حساب العميل", "statement", Colors.INFO,
             "عرض حركات حساب العميل والرصيد"),
        ]
        
        for i, (icon, label, key, color, description) in enumerate(credit_reports):
            card = self._create_report_card(icon, label, key, color, description)
            credit_reports_grid.addWidget(card, 0, i)
        
        layout.addLayout(credit_reports_grid)
        
        # General reports section
        general_section_label = QLabel("التقارير العامة")
        general_section_label.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_H3, QFont.Bold))
        general_section_label.setStyleSheet(f"color: {Colors.PRIMARY}; margin-top: 16px;")
        layout.addWidget(general_section_label)
        
        # Report types grid
        reports_grid = QGridLayout()
        reports_grid.setSpacing(16)
        
        reports = [
            ("📊", "تقرير المبيعات", "sales", Colors.PRIMARY, "إحصائيات المبيعات"),
            ("💵", "تقرير الأرباح", "profit", Colors.SUCCESS, "صافي الأرباح والهوامش"),
            ("📦", "تقرير المخزون", "inventory", Colors.WARNING, "قيمة وكميات المخزون"),
            ("👥", "تقرير العملاء", "customers", Colors.INFO, "إحصائيات العملاء"),
            ("🏭", "تقرير الموردين", "suppliers", Colors.SECONDARY, "إحصائيات الموردين"),
            ("💸", "تقرير المصروفات", "expenses", Colors.DANGER, "تحليل المصروفات"),
        ]
        
        for i, (icon, label, key, color, description) in enumerate(reports):
            card = self._create_report_card(icon, label, key, color, description)
            reports_grid.addWidget(card, i // 3, i % 3)
            
        layout.addLayout(reports_grid)
        
        # Quick export section
        export_card = Card()
        export_layout = QHBoxLayout(export_card)
        export_layout.setContentsMargins(20, 20, 20, 20)
        
        export_lbl = QLabel("📥 تصدير البيانات:")
        export_layout.addWidget(export_lbl)
        
        export_layout.addStretch()
        
        excel_btn = QPushButton("تصدير Excel")
        excel_btn.setStyleSheet(f"background: {Colors.SUCCESS}; color: white; border-radius: 8px; padding: 10px 20px;")
        export_layout.addWidget(excel_btn)
        
        pdf_btn = QPushButton("تصدير PDF")
        pdf_btn.setStyleSheet(f"background: {Colors.DANGER}; color: white; border-radius: 8px; padding: 10px 20px;")
        export_layout.addWidget(pdf_btn)
        
        layout.addWidget(export_card)
        
        layout.addStretch()
        
        scroll.setWidget(content)
        
        main_view_layout = QVBoxLayout(self.main_view)
        main_view_layout.setContentsMargins(0, 0, 0, 0)
        main_view_layout.addWidget(scroll)
    
    def _create_report_card(self, icon: str, label: str, key: str, color: str, description: str) -> Card:
        """Create a report card widget."""
        card = Card()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setAlignment(Qt.AlignCenter)
        
        icon_lbl = QLabel(icon)
        icon_lbl.setFont(QFont(Fonts.FAMILY_AR, 32))
        icon_lbl.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(icon_lbl)
        
        name_lbl = QLabel(label)
        name_lbl.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_H3, QFont.Bold))
        name_lbl.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(name_lbl)
        
        desc_lbl = QLabel(description)
        desc_lbl.setProperty("class", "subtitle")
        desc_lbl.setAlignment(Qt.AlignCenter)
        desc_lbl.setWordWrap(True)
        card_layout.addWidget(desc_lbl)
        
        view_btn = QPushButton("عرض التقرير")
        view_btn.setStyleSheet(f"""
            QPushButton {{
                background: {color};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
            }}
            QPushButton:hover {{
                opacity: 0.9;
            }}
        """)
        view_btn.clicked.connect(lambda _, k=key: self.show_report(k))
        card_layout.addWidget(view_btn)
        
        return card
        
    def apply_filter(self):
        """Apply date filter and refresh reports."""
        MessageDialog.info(self, "معلومات", "تم تطبيق الفلتر")
    
    def _show_back_button(self, view_widget: QWidget):
        """Add a back button to return to main view."""
        # Find existing back button and remove if exists
        for child in view_widget.findChildren(QPushButton, "back_btn"):
            child.deleteLater()
    
    def _go_back_to_main(self):
        """Navigate back to main reports view."""
        self.stack.setCurrentWidget(self.main_view)
    
    def _on_customer_selected_from_receivables(self, customer: dict):
        """Handle customer selection from receivables report to show statement."""
        self.statement_view.set_customer(customer)
        self.stack.setCurrentWidget(self.statement_view)
        
    @handle_ui_error
    def show_report(self, report_type: str):
        """Show specific report."""
        start_date = self.from_date.date().toString('yyyy-MM-dd')
        end_date = self.to_date.date().toString('yyyy-MM-dd')
        
        # Handle new credit reports with navigation
        if report_type == 'receivables':
            self.receivables_view.refresh()
            self.stack.setCurrentWidget(self.receivables_view)
            return
        elif report_type == 'aging':
            self.aging_view.refresh()
            self.stack.setCurrentWidget(self.aging_view)
            return
        elif report_type == 'statement':
            self.statement_view.refresh()
            self.stack.setCurrentWidget(self.statement_view)
            return
        elif report_type == 'suppliers':
            self.suppliers_view.refresh()
            self.stack.setCurrentWidget(self.suppliers_view)
            return
        elif report_type == 'expenses':
            self.expenses_view.refresh()
            self.stack.setCurrentWidget(self.expenses_view)
            return
        
        # Handle existing reports with dialogs
        if report_type == 'sales':
            data = api.get_sales_report(start_date, end_date)
            summary = data.get('summary', {})
            total = float(summary.get('total_usd', summary.get('total', 0)) or 0)
            count = summary.get('count', 0)
            MessageDialog.info(self, "تقرير المبيعات", f"إجمالي المبيعات: {config.format_usd(total)}\nعدد الفواتير: {count}")
        elif report_type == 'profit':
            data = api.get_profit_report(start_date, end_date)
            net_profit = float(data.get('net_profit_usd', data.get('net_profit', 0)) or 0)
            gross_profit = float(data.get('gross_profit_usd', data.get('gross_profit', 0)) or 0)
            MessageDialog.info(self, "تقرير الأرباح", f"إجمالي الربح: {config.format_usd(gross_profit)}\nصافي الربح: {config.format_usd(net_profit)}")
        elif report_type == 'inventory':
            data = api.get_inventory_report()
            total_value = float(data.get('total_value', 0))
            item_count = data.get('item_count', 0)
            low_stock = data.get('low_stock_count', 0)
            MessageDialog.info(self, "تقرير المخزون", f"إجمالي قيمة المخزون: {total_value:,.2f} ل.س\nعدد الأصناف: {item_count}\nمنخفض المخزون: {low_stock}")
        elif report_type == 'customers':
            data = api.get_customer_report(start_date, end_date)
            summary = data.get('summary', {})
            total = summary.get('total_customers', 0)
            active = summary.get('active_customers', 0)
            receivables = float(summary.get('total_receivables_usd', summary.get('total_receivables', 0)) or 0)
            MessageDialog.info(self, "تقرير العملاء", f"إجمالي العملاء: {total}\nالعملاء النشطين: {active}\nإجمالي المستحقات: {config.format_usd(receivables)}")
        else:
            MessageDialog.info(self, "معلومات", "هذا التقرير قيد التطوير")
        
    def refresh(self):
        """Refresh reports view."""
        # Refresh the current view if it's a detail view
        current = self.stack.currentWidget()
        if current == self.receivables_view:
            self.receivables_view.refresh()
        elif current == self.aging_view:
            self.aging_view.refresh()
        elif current == self.statement_view:
            self.statement_view.refresh()
        elif current == self.suppliers_view:
            self.suppliers_view.refresh()
        elif current == self.expenses_view:
            self.expenses_view.refresh()
    
    def go_to_receivables(self):
        """Navigate directly to receivables report (for dashboard click)."""
        self.receivables_view.refresh()
        self.stack.setCurrentWidget(self.receivables_view)
    
    def go_to_aging(self):
        """Navigate directly to aging report."""
        self.aging_view.refresh()
        self.stack.setCurrentWidget(self.aging_view)
    
    def go_to_statement(self, customer: dict = None):
        """Navigate directly to customer statement."""
        self.statement_view.refresh()
        if customer:
            self.statement_view.set_customer(customer)
        self.stack.setCurrentWidget(self.statement_view)
    
    def go_to_suppliers(self):
        """Navigate directly to suppliers report."""
        self.suppliers_view.refresh()
        self.stack.setCurrentWidget(self.suppliers_view)
    
    def go_to_expenses(self):
        """Navigate directly to expenses report."""
        self.expenses_view.refresh()
        self.stack.setCurrentWidget(self.expenses_view)
    
    def go_to_main(self):
        """Navigate back to main reports grid."""
        self.stack.setCurrentWidget(self.main_view)
