"""Customer Statement View - كشف حساب العميل - Professional Modern Design"""

from datetime import datetime
from typing import Dict, List, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QDateEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QFrame, QGridLayout,
    QScrollArea, QGraphicsDropShadowEffect, QComboBox
)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QFont, QBrush, QColor

from ...config import Colors, Fonts, config
from ...widgets.cards import Card
from ...widgets.dialogs import MessageDialog
from ...services.api import api, ApiException
from ...services.export import ExportService, ExportError
from ...utils.error_handler import handle_ui_error


class StatementMetricCard(QFrame):
    def __init__(self, title: str, value: str, icon: str, color: str, parent=None):
        super().__init__(parent)
        self.accent_color = color
        self.setObjectName("statement_metric_card")
        self.setup_ui(title, value, icon)
        self._apply_style()
        
    def setup_ui(self, title: str, value: str, icon: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(8)
        
        top = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setFixedSize(40, 40)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet(f"""
            font-size: 20px; background: {self.accent_color}18;
            color: {self.accent_color}; border-radius: 10px;
            border: 1px solid {self.accent_color}30;
        """)
        top.addWidget(icon_label)
        top.addStretch()
        layout.addLayout(top)
        
        self.value_label = QLabel(value)
        self.value_label.setFont(QFont(Fonts.FAMILY_AR, 22, QFont.Bold))
        self.value_label.setStyleSheet(f"color: {self.accent_color}; background: transparent;")
        layout.addWidget(self.value_label)
        
        title_label = QLabel(title)
        title_label.setFont(QFont(Fonts.FAMILY_AR, 11, QFont.Medium))
        title_label.setStyleSheet(f"color: {Colors.LIGHT_TEXT_SECONDARY}; background: transparent;")
        layout.addWidget(title_label)
    
    def _apply_style(self):
        self.setStyleSheet(f"""
            QFrame#statement_metric_card {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {Colors.LIGHT_CARD}, stop:1 {self.accent_color}08);
                border: 1px solid {Colors.LIGHT_BORDER}; border-radius: 14px;
                border-left: 4px solid {self.accent_color};
            }}
        """)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(3)
        shadow.setColor(QColor(0, 0, 0, 12))
        self.setGraphicsEffect(shadow)
        
    def update_value(self, value: str, color: str = None):
        self.value_label.setText(value)
        if color:
            self.value_label.setStyleSheet(f"color: {color}; background: transparent;")


class SectionHeader(QFrame):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 12)
        title_lbl = QLabel(title)
        title_lbl.setFont(QFont(Fonts.FAMILY_AR, 16, QFont.Bold))
        title_lbl.setStyleSheet(f"color: {Colors.LIGHT_TEXT}; background: transparent;")
        layout.addWidget(title_lbl)
        layout.addStretch()
        self.setStyleSheet("background: transparent;")


class CustomerStatementView(QWidget):
    """Professional Customer Statement view with modern UI."""
    
    back_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.customers_cache: List[Dict] = []
        self.selected_customer: Optional[Dict] = None
        self.statement_data: Dict = {}
        self.transactions: List[Dict] = []
        self.setup_ui()
    
    def go_back(self):
        self.back_requested.emit()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(20)

        # Header
        header_card = QFrame()
        header_card.setObjectName("header_card")
        header_card.setStyleSheet(f"""
            QFrame#header_card {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0891B2, stop:1 #06B6D4);
                border-radius: 16px;
            }}
        """)
        header_layout = QHBoxLayout(header_card)
        header_layout.setContentsMargins(24, 20, 24, 20)
        
        back_btn = QPushButton("→ رجوع")
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255,255,255,0.2); color: white;
                border: 1px solid rgba(255,255,255,0.3);
                border-radius: 8px; padding: 10px 20px; font-weight: 500;
            }}
            QPushButton:hover {{ background: rgba(255,255,255,0.3); }}
        """)
        back_btn.clicked.connect(self.go_back)
        header_layout.addWidget(back_btn)
        
        title_section = QVBoxLayout()
        title_section.setSpacing(4)
        title = QLabel("📋 كشف حساب العميل")
        title.setFont(QFont(Fonts.FAMILY_AR, 22, QFont.Bold))
        title.setStyleSheet("color: white; background: transparent;")
        title_section.addWidget(title)
        subtitle = QLabel("عرض تفصيلي لحركات حساب العميل والرصيد الجاري")
        subtitle.setFont(QFont(Fonts.FAMILY_AR, 12))
        subtitle.setStyleSheet("color: rgba(255,255,255,0.85); background: transparent;")
        title_section.addWidget(subtitle)
        header_layout.addLayout(title_section)
        header_layout.addStretch()
        
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(10)
        
        refresh_btn = QPushButton("🔄 تحديث")
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.setStyleSheet(f"""
            QPushButton {{ background: rgba(255,255,255,0.15); color: white;
                border: 1px solid rgba(255,255,255,0.25); border-radius: 8px; padding: 10px 18px; }}
            QPushButton:hover {{ background: rgba(255,255,255,0.25); }}
        """)
        refresh_btn.clicked.connect(self.refresh)
        actions_layout.addWidget(refresh_btn)
        
        export_excel_btn = QPushButton("📊 Excel")
        export_excel_btn.setCursor(Qt.PointingHandCursor)
        export_excel_btn.setStyleSheet(f"""
            QPushButton {{ background: {Colors.SUCCESS}; color: white;
                border: none; border-radius: 8px; padding: 10px 18px; }}
            QPushButton:hover {{ background: {Colors.SUCCESS}dd; }}
        """)
        export_excel_btn.clicked.connect(self._export_excel)
        actions_layout.addWidget(export_excel_btn)
        
        export_pdf_btn = QPushButton("📄 PDF")
        export_pdf_btn.setCursor(Qt.PointingHandCursor)
        export_pdf_btn.setStyleSheet(f"""
            QPushButton {{ background: {Colors.DANGER}; color: white;
                border: none; border-radius: 8px; padding: 10px 18px; }}
            QPushButton:hover {{ background: {Colors.DANGER}dd; }}
        """)
        export_pdf_btn.clicked.connect(self._export_pdf)
        actions_layout.addWidget(export_pdf_btn)
        
        print_btn = QPushButton("🖨️ طباعة")
        print_btn.setCursor(Qt.PointingHandCursor)
        print_btn.setStyleSheet(f"""
            QPushButton {{ background: #7C3AED; color: white;
                border: none; border-radius: 8px; padding: 10px 18px; }}
            QPushButton:hover {{ background: #6D28D9; }}
        """)
        print_btn.clicked.connect(self._print_statement)
        actions_layout.addWidget(print_btn)
        
        header_layout.addLayout(actions_layout)
        layout.addWidget(header_card)

        # Filters
        filters_card = QFrame()
        filters_card.setObjectName("filters_card")
        filters_card.setStyleSheet(f"""
            QFrame#filters_card {{
                background: {Colors.LIGHT_CARD};
                border: 1px solid {Colors.LIGHT_BORDER};
                border-radius: 12px;
            }}
        """)
        filters_layout = QHBoxLayout(filters_card)
        filters_layout.setContentsMargins(20, 16, 20, 16)
        filters_layout.setSpacing(16)
        
        filters_layout.addWidget(QLabel("👤"))
        filters_layout.addWidget(QLabel("العميل:"))
        self.customer_combo = QComboBox()
        self.customer_combo.setMinimumWidth(250)
        self.customer_combo.setPlaceholderText("اختر العميل...")
        self.customer_combo.currentIndexChanged.connect(self._on_customer_selected)
        filters_layout.addWidget(self.customer_combo)
        
        filters_layout.addWidget(QLabel("📅"))
        filters_layout.addWidget(QLabel("من:"))
        self.from_date = QDateEdit()
        self.from_date.setCalendarPopup(True)
        self.from_date.setDate(QDate.currentDate().addMonths(-3))
        self.from_date.setMinimumWidth(130)
        filters_layout.addWidget(self.from_date)
        
        filters_layout.addWidget(QLabel("إلى:"))
        self.to_date = QDateEdit()
        self.to_date.setCalendarPopup(True)
        self.to_date.setDate(QDate.currentDate())
        self.to_date.setMinimumWidth(130)
        filters_layout.addWidget(self.to_date)
        
        apply_btn = QPushButton("🔍 عرض الكشف")
        apply_btn.setCursor(Qt.PointingHandCursor)
        apply_btn.setStyleSheet(f"""
            QPushButton {{ background: {Colors.PRIMARY}; color: white;
                border: none; border-radius: 8px; padding: 10px 24px; font-weight: 600; }}
            QPushButton:hover {{ background: {Colors.PRIMARY_DARK}; }}
        """)
        apply_btn.clicked.connect(self._load_statement)
        filters_layout.addWidget(apply_btn)
        filters_layout.addStretch()
        layout.addWidget(filters_card)

        # Customer Info Card
        self.customer_info_card = QFrame()
        self.customer_info_card.setObjectName("customer_info_card")
        self.customer_info_card.setStyleSheet(f"""
            QFrame#customer_info_card {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Colors.INFO}15, stop:1 {Colors.INFO}08);
                border: 1px solid {Colors.INFO}30;
                border-radius: 12px;
            }}
        """)
        info_layout = QHBoxLayout(self.customer_info_card)
        info_layout.setContentsMargins(20, 16, 20, 16)
        
        info_left = QVBoxLayout()
        self.customer_name_label = QLabel("اختر العميل لعرض الكشف")
        self.customer_name_label.setFont(QFont(Fonts.FAMILY_AR, 16, QFont.Bold))
        self.customer_name_label.setStyleSheet(f"color: {Colors.LIGHT_TEXT}; background: transparent;")
        info_left.addWidget(self.customer_name_label)
        self.customer_code_label = QLabel("")
        self.customer_code_label.setFont(QFont(Fonts.FAMILY_AR, 11))
        self.customer_code_label.setStyleSheet(f"color: {Colors.LIGHT_TEXT_SECONDARY}; background: transparent;")
        info_left.addWidget(self.customer_code_label)
        info_layout.addLayout(info_left)
        info_layout.addStretch()
        layout.addWidget(self.customer_info_card)

        # Metrics
        layout.addWidget(SectionHeader("📊 ملخص الحساب"))
        
        metrics_grid = QGridLayout()
        metrics_grid.setSpacing(14)
        
        self.opening_card = StatementMetricCard(
            "الرصيد الافتتاحي", config.format_usd(0), "📂", Colors.INFO
        )
        metrics_grid.addWidget(self.opening_card, 0, 0)
        
        self.debit_card = StatementMetricCard(
            "إجمالي المدين (فواتير)", config.format_usd(0), "📈", Colors.DANGER
        )
        metrics_grid.addWidget(self.debit_card, 0, 1)
        
        self.credit_card = StatementMetricCard(
            "إجمالي الدائن (مدفوعات)", config.format_usd(0), "📉", Colors.SUCCESS
        )
        metrics_grid.addWidget(self.credit_card, 0, 2)
        
        self.closing_card = StatementMetricCard(
            "الرصيد الختامي", config.format_usd(0), "💰", Colors.PRIMARY
        )
        metrics_grid.addWidget(self.closing_card, 0, 3)
        
        layout.addLayout(metrics_grid)

        # Transactions Table
        layout.addWidget(SectionHeader("📝 حركات الحساب"))
        
        table_card = QFrame()
        table_card.setObjectName("table_card")
        table_card.setStyleSheet(f"""
            QFrame#table_card {{
                background: {Colors.LIGHT_CARD};
                border: 1px solid {Colors.LIGHT_BORDER};
                border-radius: 12px;
            }}
        """)
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(20, 16, 20, 16)
        table_layout.setSpacing(12)
        
        table_header = QHBoxLayout()
        note = QLabel("💡 الرصيد الموجب يعني مستحق على العميل - الرصيد السالب يعني مستحق للعميل")
        note.setFont(QFont(Fonts.FAMILY_AR, 10))
        note.setStyleSheet(f"""
            color: {Colors.LIGHT_TEXT_SECONDARY};
            background: {Colors.WARNING}15;
            padding: 8px 12px; border-radius: 6px;
            border-left: 3px solid {Colors.WARNING};
        """)
        table_header.addWidget(note)
        table_header.addStretch()
        self.transaction_count_label = QLabel("0 حركة")
        self.transaction_count_label.setFont(QFont(Fonts.FAMILY_AR, 11))
        self.transaction_count_label.setStyleSheet(f"color: {Colors.LIGHT_TEXT_SECONDARY}; background: transparent;")
        table_header.addWidget(self.transaction_count_label)
        table_layout.addLayout(table_header)
        
        self.transactions_table = QTableWidget()
        self.transactions_table.setColumnCount(7)
        self.transactions_table.setHorizontalHeaderLabels([
            'التاريخ', 'النوع', 'المرجع', 'البيان', 'مدين', 'دائن', 'الرصيد'
        ])
        self.transactions_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        for i in [0, 1, 2, 4, 5, 6]:
            self.transactions_table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)
        self.transactions_table.verticalHeader().setVisible(False)
        self.transactions_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.transactions_table.setAlternatingRowColors(True)
        self.transactions_table.setMinimumHeight(350)
        self._style_table(self.transactions_table)
        table_layout.addWidget(self.transactions_table)
        
        layout.addWidget(table_card, 1)
        layout.addStretch()
        
        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    def _style_table(self, table: QTableWidget):
        table.setStyleSheet(f"""
            QTableWidget {{ background: {Colors.LIGHT_CARD}; border: 1px solid {Colors.LIGHT_BORDER};
                border-radius: 8px; gridline-color: {Colors.LIGHT_BORDER}; }}
            QTableWidget::item {{ padding: 10px 12px; border-bottom: 1px solid {Colors.LIGHT_BORDER}50; }}
            QTableWidget::item:selected {{ background: {Colors.PRIMARY}15; color: {Colors.PRIMARY}; }}
            QHeaderView::section {{ background: {Colors.LIGHT_BG}; color: {Colors.LIGHT_TEXT};
                padding: 12px; border: none; border-bottom: 2px solid {Colors.PRIMARY};
                font-weight: bold; font-size: 12px; }}
        """)

    @handle_ui_error
    def refresh(self):
        response = api.get_customers()
        if isinstance(response, dict) and 'results' in response:
            self.customers_cache = response['results']
        else:
            self.customers_cache = response if isinstance(response, list) else []
        
        current_selection = self.customer_combo.currentData()
        self.customer_combo.clear()
        self.customer_combo.addItem("-- اختر العميل --", None)
        
        for customer in self.customers_cache:
            display_text = f"{customer.get('name', '')} ({customer.get('code', '')})"
            self.customer_combo.addItem(display_text, customer)
        
        if current_selection:
            for i in range(self.customer_combo.count()):
                if self.customer_combo.itemData(i) == current_selection:
                    self.customer_combo.setCurrentIndex(i)
                    break

    def _on_customer_selected(self, index: int):
        if index <= 0:
            self.selected_customer = None
            self._clear_statement()
            return
        self.selected_customer = self.customer_combo.currentData()
        if self.selected_customer:
            self._load_statement()

    def _clear_statement(self):
        self.customer_name_label.setText("اختر العميل لعرض الكشف")
        self.customer_code_label.setText("")
        self.opening_card.update_value(config.format_usd(0))
        self.debit_card.update_value(config.format_usd(0))
        self.credit_card.update_value(config.format_usd(0))
        self.closing_card.update_value(config.format_usd(0))
        self.transactions_table.setRowCount(0)
        self.transaction_count_label.setText("0 حركة")
        self.transactions = []
        self.statement_data = {}

    @handle_ui_error
    def _load_statement(self):
        if not self.selected_customer:
            MessageDialog.warning(self, "تنبيه", "يرجى اختيار العميل أولاً")
            return
        
        customer_id = self.selected_customer.get('id')
        start_date = self.from_date.date().toString('yyyy-MM-dd')
        end_date = self.to_date.date().toString('yyyy-MM-dd')
        
        self.statement_data = api.get_customer_statement(
            customer_id, start_date=start_date, end_date=end_date
        )
        
        self._update_customer_info()
        self._update_summary()
        self._update_transactions_table()

    def _update_customer_info(self):
        if self.selected_customer:
            self.customer_name_label.setText(self.selected_customer.get('name', '-'))
            self.customer_code_label.setText(f"كود العميل: {self.selected_customer.get('code', '-')}")

    def _update_summary(self):
        opening = float(self.statement_data.get('opening_balance_usd', self.statement_data.get('opening_balance', 0)) or 0)
        closing = float(self.statement_data.get('closing_balance_usd', self.statement_data.get('closing_balance', 0)) or 0)
        total_debit = float(self.statement_data.get('total_invoices_usd', self.statement_data.get('total_invoices', 0)) or 0)
        total_payments = float(self.statement_data.get('total_payments_usd', self.statement_data.get('total_payments', 0)) or 0)
        total_returns = float(self.statement_data.get('total_returns_usd', self.statement_data.get('total_returns', 0)) or 0)
        total_credit = total_payments + total_returns
        
        self.opening_card.update_value(config.format_usd(opening))
        self.debit_card.update_value(config.format_usd(total_debit))
        self.credit_card.update_value(config.format_usd(total_credit))
        
        closing_color = Colors.DANGER if closing > 0 else Colors.SUCCESS if closing < 0 else Colors.PRIMARY
        self.closing_card.update_value(config.format_usd(closing), closing_color)

    def _update_transactions_table(self):
        self.transactions = self.statement_data.get('transactions', [])
        self.transactions_table.setRowCount(len(self.transactions))
        self.transaction_count_label.setText(f"{len(self.transactions)} حركة")
        
        for row, transaction in enumerate(self.transactions):
            date_item = QTableWidgetItem(str(transaction.get('date', '')))
            date_item.setTextAlignment(Qt.AlignCenter)
            self.transactions_table.setItem(row, 0, date_item)
            
            trans_type = transaction.get('type', '')
            type_display = self._get_transaction_type_display(trans_type)
            type_item = QTableWidgetItem(type_display)
            type_item.setTextAlignment(Qt.AlignCenter)
            if trans_type == 'invoice':
                type_item.setForeground(QColor(Colors.DANGER))
            elif trans_type == 'payment':
                type_item.setForeground(QColor(Colors.SUCCESS))
            elif trans_type == 'return':
                type_item.setForeground(QColor(Colors.WARNING))
            self.transactions_table.setItem(row, 1, type_item)
            
            reference = transaction.get('reference', '')
            ref_item = QTableWidgetItem(str(reference))
            ref_item.setForeground(QColor(Colors.PRIMARY))
            self.transactions_table.setItem(row, 2, ref_item)
            
            description = transaction.get('description', '')
            self.transactions_table.setItem(row, 3, QTableWidgetItem(str(description)))
            
            debit = float(transaction.get('debit_usd', transaction.get('debit', 0)) or 0)
            debit_item = QTableWidgetItem(config.format_usd(debit) if debit > 0 else "-")
            debit_item.setTextAlignment(Qt.AlignCenter)
            if debit > 0:
                debit_item.setForeground(QColor(Colors.DANGER))
            self.transactions_table.setItem(row, 4, debit_item)
            
            credit = float(transaction.get('credit_usd', transaction.get('credit', 0)) or 0)
            credit_item = QTableWidgetItem(config.format_usd(credit) if credit > 0 else "-")
            credit_item.setTextAlignment(Qt.AlignCenter)
            if credit > 0:
                credit_item.setForeground(QColor(Colors.SUCCESS))
            self.transactions_table.setItem(row, 5, credit_item)
            
            balance = float(transaction.get('balance_usd', transaction.get('balance', 0)) or 0)
            balance_item = QTableWidgetItem(config.format_usd(balance))
            balance_item.setTextAlignment(Qt.AlignCenter)
            balance_item.setFont(QFont(Fonts.FAMILY_AR, 11, QFont.Bold))
            if balance > 0:
                balance_item.setForeground(QColor(Colors.DANGER))
            elif balance < 0:
                balance_item.setForeground(QColor(Colors.SUCCESS))
            self.transactions_table.setItem(row, 6, balance_item)

    def _get_transaction_type_display(self, trans_type: str) -> str:
        type_map = {
            'invoice': '📄 فاتورة',
            'payment': '💵 دفعة',
            'return': '↩️ مرتجع',
            'opening': '📂 رصيد افتتاحي',
            'adjustment': '⚙️ تسوية'
        }
        return type_map.get(trans_type, trans_type)

    def set_customer(self, customer: Dict):
        self.selected_customer = customer
        for i in range(self.customer_combo.count()):
            item_data = self.customer_combo.itemData(i)
            if item_data and item_data.get('id') == customer.get('id'):
                self.customer_combo.setCurrentIndex(i)
                break
        self._load_statement()

    def _export_excel(self):
        if not self.selected_customer:
            MessageDialog.warning(self, "تنبيه", "يرجى اختيار العميل أولاً")
            return
        if not self.transactions:
            MessageDialog.warning(self, "تنبيه", "لا توجد بيانات للتصدير")
            return
        
        try:
            columns = [
                ('date', 'التاريخ'), ('type_display', 'النوع'), ('reference', 'المرجع'),
                ('description', 'البيان'), ('debit', 'مدين'), ('credit', 'دائن'), ('balance', 'الرصيد')
            ]
            
            export_data = []
            for trans in self.transactions:
                trans_type = trans.get('type', '')
                export_data.append({
                    'date': trans.get('date', ''),
                    'type_display': self._get_transaction_type_display(trans_type).replace('📄 ', '').replace('💵 ', '').replace('↩️ ', '').replace('📂 ', '').replace('⚙️ ', ''),
                    'reference': trans.get('reference', ''),
                    'description': trans.get('description', ''),
                    'debit': float(trans.get('debit_usd', trans.get('debit', 0)) or 0),
                    'credit': float(trans.get('credit_usd', trans.get('credit', 0)) or 0),
                    'balance': float(trans.get('balance_usd', trans.get('balance', 0)) or 0)
                })
            
            customer_name = self.selected_customer.get('name', 'عميل')
            filename = f"كشف_حساب_{customer_name}_{datetime.now().strftime('%Y%m%d')}.xlsx"
            
            opening = float(self.statement_data.get('opening_balance_usd', self.statement_data.get('opening_balance', 0)) or 0)
            closing = float(self.statement_data.get('closing_balance_usd', self.statement_data.get('closing_balance', 0)) or 0)
            total_debit = float(self.statement_data.get('total_invoices_usd', self.statement_data.get('total_invoices', 0)) or 0)
            total_payments = float(self.statement_data.get('total_payments_usd', self.statement_data.get('total_payments', 0)) or 0)
            total_returns = float(self.statement_data.get('total_returns_usd', self.statement_data.get('total_returns', 0)) or 0)
            
            summary_data = {
                'اسم العميل': self.selected_customer.get('name', ''),
                'كود العميل': self.selected_customer.get('code', ''),
                'الرصيد الافتتاحي': config.format_usd(opening),
                'إجمالي المدين': config.format_usd(total_debit),
                'إجمالي الدائن': config.format_usd(total_payments + total_returns),
                'الرصيد الختامي': config.format_usd(closing)
            }
            
            success = ExportService.export_to_excel(
                data=export_data, columns=columns, filename=filename,
                title="كشف حساب العميل", parent=self, summary=summary_data
            )
            
            if success:
                MessageDialog.info(self, "نجاح", "تم تصدير الكشف بنجاح")
                
        except ExportError as e:
            MessageDialog.error(self, "خطأ", e.message)
        except Exception as e:
            MessageDialog.error(self, "خطأ", f"فشل تصدير الكشف: {str(e)}")

    def _export_pdf(self):
        if not self.selected_customer:
            MessageDialog.warning(self, "تنبيه", "يرجى اختيار العميل أولاً")
            return
        if not self.transactions:
            MessageDialog.warning(self, "تنبيه", "لا توجد بيانات للتصدير")
            return
        
        try:
            columns = [
                ('date', 'التاريخ'), ('type_display', 'النوع'), ('reference', 'المرجع'),
                ('description', 'البيان'), ('debit', 'مدين'), ('credit', 'دائن'), ('balance', 'الرصيد')
            ]
            
            export_data = []
            for trans in self.transactions:
                trans_type = trans.get('type', '')
                export_data.append({
                    'date': trans.get('date', ''),
                    'type_display': self._get_transaction_type_display(trans_type).replace('📄 ', '').replace('💵 ', '').replace('↩️ ', '').replace('📂 ', '').replace('⚙️ ', ''),
                    'reference': trans.get('reference', ''),
                    'description': trans.get('description', ''),
                    'debit': float(trans.get('debit_usd', trans.get('debit', 0)) or 0),
                    'credit': float(trans.get('credit_usd', trans.get('credit', 0)) or 0),
                    'balance': float(trans.get('balance_usd', trans.get('balance', 0)) or 0)
                })
            
            customer_name = self.selected_customer.get('name', 'عميل')
            filename = f"كشف_حساب_{customer_name}_{datetime.now().strftime('%Y%m%d')}.pdf"
            
            opening = float(self.statement_data.get('opening_balance_usd', self.statement_data.get('opening_balance', 0)) or 0)
            closing = float(self.statement_data.get('closing_balance_usd', self.statement_data.get('closing_balance', 0)) or 0)
            total_debit = float(self.statement_data.get('total_invoices_usd', self.statement_data.get('total_invoices', 0)) or 0)
            total_payments = float(self.statement_data.get('total_payments_usd', self.statement_data.get('total_payments', 0)) or 0)
            total_returns = float(self.statement_data.get('total_returns_usd', self.statement_data.get('total_returns', 0)) or 0)
            
            summary_data = {
                'اسم العميل': self.selected_customer.get('name', ''),
                'كود العميل': self.selected_customer.get('code', ''),
                'الرصيد الافتتاحي': config.format_usd(opening),
                'إجمالي المدين': config.format_usd(total_debit),
                'إجمالي الدائن': config.format_usd(total_payments + total_returns),
                'الرصيد الختامي': config.format_usd(closing)
            }
            
            start_date = self.from_date.date().toString('yyyy-MM-dd')
            end_date = self.to_date.date().toString('yyyy-MM-dd')
            
            success = ExportService.export_to_pdf(
                data=export_data, columns=columns, filename=filename,
                title="كشف حساب العميل", parent=self, summary=summary_data,
                date_range=(start_date, end_date)
            )
            
            if success:
                MessageDialog.info(self, "نجاح", "تم تصدير الكشف بنجاح")
                
        except ExportError as e:
            MessageDialog.error(self, "خطأ", e.message)
        except Exception as e:
            MessageDialog.error(self, "خطأ", f"فشل تصدير الكشف: {str(e)}")

    def _print_statement(self):
        if not self.selected_customer:
            MessageDialog.warning(self, "تنبيه", "يرجى اختيار العميل أولاً")
            return
        if not self.transactions:
            MessageDialog.warning(self, "تنبيه", "لا توجد بيانات للطباعة")
            return
        
        try:
            customer_info = {
                'name': self.selected_customer.get('name', ''),
                'code': self.selected_customer.get('code', '')
            }
            start_date = self.from_date.date().toString('yyyy-MM-dd')
            end_date = self.to_date.date().toString('yyyy-MM-dd')
            
            html_content = ExportService.generate_statement_html(
                customer_info=customer_info,
                statement_data=self.statement_data,
                transactions=self.transactions,
                date_range=(start_date, end_date)
            )
            
            ExportService.print_document(
                html_content=html_content,
                parent=self,
                title=f"كشف حساب - {customer_info['name']}"
            )
            
        except ExportError as e:
            MessageDialog.error(self, "خطأ", e.message)
        except Exception as e:
            MessageDialog.error(self, "خطأ", f"فشل الطباعة: {str(e)}")
