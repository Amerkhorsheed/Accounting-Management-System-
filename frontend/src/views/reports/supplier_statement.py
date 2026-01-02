"""Supplier Statement View - كشف حساب المورد - Professional Modern Design"""

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


class SupplierMetricCard(QFrame):
    def __init__(self, title: str, value: str, icon: str, color: str, parent=None):
        super().__init__(parent)
        self.accent_color = color
        self.setObjectName("supplier_metric_card")
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
            QFrame#supplier_metric_card {{
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


class SupplierStatementView(QWidget):
    """Professional Supplier Statement view with modern UI."""
    
    back_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.suppliers_cache: List[Dict] = []
        self.selected_supplier: Optional[Dict] = None
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
                    stop:0 #7C3AED, stop:1 #A855F7);
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
        title = QLabel("🏭 كشف حساب المورد")
        title.setFont(QFont(Fonts.FAMILY_AR, 22, QFont.Bold))
        title.setStyleSheet("color: white; background: transparent;")
        title_section.addWidget(title)
        subtitle = QLabel("عرض تفصيلي لحركات حساب المورد والرصيد الجاري")
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
        
        filters_layout.addWidget(QLabel("🏭"))
        filters_layout.addWidget(QLabel("المورد:"))
        self.supplier_combo = QComboBox()
        self.supplier_combo.setMinimumWidth(250)
        self.supplier_combo.setPlaceholderText("اختر المورد...")
        self.supplier_combo.currentIndexChanged.connect(self._on_supplier_selected)
        filters_layout.addWidget(self.supplier_combo)
        
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

        # Supplier Info Card
        self.supplier_info_card = QFrame()
        self.supplier_info_card.setObjectName("supplier_info_card")
        self.supplier_info_card.setStyleSheet(f"""
            QFrame#supplier_info_card {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7C3AED15, stop:1 #7C3AED08);
                border: 1px solid #7C3AED30;
                border-radius: 12px;
            }}
        """)
        info_layout = QHBoxLayout(self.supplier_info_card)
        info_layout.setContentsMargins(20, 16, 20, 16)
        
        info_left = QVBoxLayout()
        self.supplier_name_label = QLabel("اختر المورد لعرض الكشف")
        self.supplier_name_label.setFont(QFont(Fonts.FAMILY_AR, 16, QFont.Bold))
        self.supplier_name_label.setStyleSheet(f"color: {Colors.LIGHT_TEXT}; background: transparent;")
        info_left.addWidget(self.supplier_name_label)
        self.supplier_code_label = QLabel("")
        self.supplier_code_label.setFont(QFont(Fonts.FAMILY_AR, 11))
        self.supplier_code_label.setStyleSheet(f"color: {Colors.LIGHT_TEXT_SECONDARY}; background: transparent;")
        info_left.addWidget(self.supplier_code_label)
        info_layout.addLayout(info_left)
        info_layout.addStretch()
        layout.addWidget(self.supplier_info_card)

        # Metrics
        layout.addWidget(SectionHeader("📊 ملخص الحساب"))
        
        metrics_grid = QGridLayout()
        metrics_grid.setSpacing(14)
        
        self.opening_card = SupplierMetricCard(
            "الرصيد الافتتاحي", config.format_usd(0), "📂", Colors.INFO
        )
        metrics_grid.addWidget(self.opening_card, 0, 0)
        
        self.debit_card = SupplierMetricCard(
            "إجمالي المشتريات", config.format_usd(0), "📦", Colors.DANGER
        )
        metrics_grid.addWidget(self.debit_card, 0, 1)
        
        self.credit_card = SupplierMetricCard(
            "إجمالي المدفوعات", config.format_usd(0), "💵", Colors.SUCCESS
        )
        metrics_grid.addWidget(self.credit_card, 0, 2)
        
        self.closing_card = SupplierMetricCard(
            "الرصيد الختامي", config.format_usd(0), "💰", "#7C3AED"
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
        note = QLabel("💡 الرصيد الموجب يعني مستحق للمورد - الرصيد السالب يعني مستحق من المورد")
        note.setFont(QFont(Fonts.FAMILY_AR, 10))
        note.setStyleSheet(f"""
            color: {Colors.LIGHT_TEXT_SECONDARY};
            background: #7C3AED15;
            padding: 8px 12px; border-radius: 6px;
            border-left: 3px solid #7C3AED;
        """)
        table_header.addWidget(note)
        table_header.addStretch()
        self.transaction_count_label = QLabel("0 حركة")
        self.transaction_count_label.setFont(QFont(Fonts.FAMILY_AR, 11))
        self.transaction_count_label.setStyleSheet(f"color: {Colors.LIGHT_TEXT_SECONDARY}; background: transparent;")
        table_header.addWidget(self.transaction_count_label)
        table_layout.addLayout(table_header)
        
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            'التاريخ', 'النوع', 'المرجع', 'البيان', 'مدين', 'دائن', 'الرصيد'
        ])
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        for i in [0, 1, 2, 4, 5, 6]:
            self.table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setMinimumHeight(350)
        self._style_table(self.table)
        table_layout.addWidget(self.table)
        
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
                padding: 12px; border: none; border-bottom: 2px solid #7C3AED;
                font-weight: bold; font-size: 12px; }}
        """)

    @handle_ui_error
    def refresh(self):
        self._load_suppliers()

    @handle_ui_error
    def _load_suppliers(self):
        response = api.get_suppliers()
        if isinstance(response, dict) and 'results' in response:
            self.suppliers_cache = response['results']
        else:
            self.suppliers_cache = response if isinstance(response, list) else []
        
        current_id = self.selected_supplier.get('id') if self.selected_supplier else None
        
        self.supplier_combo.blockSignals(True)
        self.supplier_combo.clear()
        self.supplier_combo.addItem("-- اختر المورد --", None)
        for s in self.suppliers_cache:
            display_text = f"{s.get('name', '')} ({s.get('code', '')})"
            self.supplier_combo.addItem(display_text, s)
        self.supplier_combo.blockSignals(False)
        
        if current_id:
            for i in range(self.supplier_combo.count()):
                data = self.supplier_combo.itemData(i)
                if data and data.get('id') == current_id:
                    self.supplier_combo.setCurrentIndex(i)
                    break

    def set_supplier(self, supplier: dict):
        self.selected_supplier = supplier
        for i in range(self.supplier_combo.count()):
            item_data = self.supplier_combo.itemData(i)
            if item_data and item_data.get('id') == supplier.get('id'):
                self.supplier_combo.setCurrentIndex(i)
                break
        self._load_statement()

    def _on_supplier_selected(self, index: int):
        if index <= 0:
            self.selected_supplier = None
            self._clear_display()
            return
        supplier = self.supplier_combo.currentData()
        self.selected_supplier = supplier if isinstance(supplier, dict) else None

    def _clear_display(self):
        self.supplier_name_label.setText("اختر المورد لعرض الكشف")
        self.supplier_code_label.setText("")
        self.opening_card.update_value(config.format_usd(0))
        self.debit_card.update_value(config.format_usd(0))
        self.credit_card.update_value(config.format_usd(0))
        self.closing_card.update_value(config.format_usd(0))
        self.table.setRowCount(0)
        self.transaction_count_label.setText("0 حركة")
        self.transactions = []
        self.statement_data = {}

    @handle_ui_error
    def _load_statement(self):
        if not self.selected_supplier:
            MessageDialog.warning(self, "تنبيه", "يرجى اختيار المورد أولاً")
            return
        
        supplier_id = self.selected_supplier.get('id')
        if not supplier_id:
            return
        
        start_date = self.from_date.date().toString('yyyy-MM-dd')
        end_date = self.to_date.date().toString('yyyy-MM-dd')
        
        self.statement_data = api.get_supplier_statement(supplier_id, start_date=start_date, end_date=end_date)
        self.transactions = self.statement_data.get('transactions', []) if isinstance(self.statement_data, dict) else []
        
        self._update_supplier_info()
        self._update_summary()
        self._populate_table()

    def _update_supplier_info(self):
        if self.selected_supplier:
            self.supplier_name_label.setText(self.selected_supplier.get('name', '-'))
            self.supplier_code_label.setText(f"كود المورد: {self.selected_supplier.get('code', '-')}")

    def _update_summary(self):
        opening = float(self.statement_data.get('opening_balance_usd', self.statement_data.get('opening_balance', 0)) or 0)
        closing = float(self.statement_data.get('closing_balance_usd', self.statement_data.get('closing_balance', 0)) or 0)
        total_debit = float(self.statement_data.get('total_purchases_usd', self.statement_data.get('total_purchases', 0)) or 0)
        total_credit = float(self.statement_data.get('total_payments_usd', self.statement_data.get('total_payments', 0)) or 0)
        
        self.opening_card.update_value(config.format_usd(opening))
        self.debit_card.update_value(config.format_usd(total_debit))
        self.credit_card.update_value(config.format_usd(total_credit))
        
        closing_color = Colors.DANGER if closing > 0 else Colors.SUCCESS if closing < 0 else "#7C3AED"
        self.closing_card.update_value(config.format_usd(closing), closing_color)

    def _populate_table(self):
        self.table.setRowCount(len(self.transactions))
        self.transaction_count_label.setText(f"{len(self.transactions)} حركة")
        
        for row, t in enumerate(self.transactions):
            date_str = str(t.get('date', ''))
            date_item = QTableWidgetItem(date_str)
            date_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, date_item)
            
            t_type = str(t.get('type', ''))
            type_display = self._get_transaction_type_display(t_type)
            type_item = QTableWidgetItem(type_display)
            type_item.setTextAlignment(Qt.AlignCenter)
            if t_type == 'purchase':
                type_item.setForeground(QColor(Colors.DANGER))
            elif t_type == 'payment':
                type_item.setForeground(QColor(Colors.SUCCESS))
            self.table.setItem(row, 1, type_item)
            
            reference = str(t.get('reference', ''))
            ref_item = QTableWidgetItem(reference)
            ref_item.setForeground(QColor("#7C3AED"))
            self.table.setItem(row, 2, ref_item)
            
            description = str(t.get('description', ''))
            self.table.setItem(row, 3, QTableWidgetItem(description))
            
            debit_usd = float(t.get('debit_usd', t.get('debit', 0)) or 0)
            debit_item = QTableWidgetItem(config.format_usd(debit_usd) if debit_usd > 0 else "-")
            debit_item.setTextAlignment(Qt.AlignCenter)
            if debit_usd > 0:
                debit_item.setForeground(QColor(Colors.DANGER))
            self.table.setItem(row, 4, debit_item)
            
            credit_usd = float(t.get('credit_usd', t.get('credit', 0)) or 0)
            credit_item = QTableWidgetItem(config.format_usd(credit_usd) if credit_usd > 0 else "-")
            credit_item.setTextAlignment(Qt.AlignCenter)
            if credit_usd > 0:
                credit_item.setForeground(QColor(Colors.SUCCESS))
            self.table.setItem(row, 5, credit_item)
            
            balance_usd = float(t.get('balance_usd', t.get('balance', 0)) or 0)
            bal_item = QTableWidgetItem(config.format_usd(balance_usd))
            bal_item.setTextAlignment(Qt.AlignCenter)
            bal_item.setFont(QFont(Fonts.FAMILY_AR, 11, QFont.Bold))
            if balance_usd > 0:
                bal_item.setForeground(QColor(Colors.DANGER))
            elif balance_usd < 0:
                bal_item.setForeground(QColor(Colors.SUCCESS))
            self.table.setItem(row, 6, bal_item)

    def _get_transaction_type_display(self, t_type: str) -> str:
        type_map = {
            'purchase': '📦 مشتريات',
            'payment': '💵 دفعة',
            'return': '↩️ مرتجع',
            'opening': '📂 رصيد افتتاحي'
        }
        return type_map.get(t_type, t_type)

    def _export_excel(self):
        if not self.selected_supplier:
            MessageDialog.warning(self, "تنبيه", "يرجى اختيار المورد أولاً")
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
            for t in self.transactions:
                t_type = t.get('type', '')
                export_data.append({
                    'date': t.get('date', ''),
                    'type_display': self._get_transaction_type_display(t_type).replace('📦 ', '').replace('💵 ', '').replace('↩️ ', '').replace('📂 ', ''),
                    'reference': t.get('reference', ''),
                    'description': t.get('description', ''),
                    'debit': float(t.get('debit_usd', t.get('debit', 0)) or 0),
                    'credit': float(t.get('credit_usd', t.get('credit', 0)) or 0),
                    'balance': float(t.get('balance_usd', t.get('balance', 0)) or 0),
                })
            
            supplier_name = self.selected_supplier.get('name', 'مورد')
            filename = f"كشف_حساب_مورد_{supplier_name}_{datetime.now().strftime('%Y%m%d')}.xlsx"
            
            opening = float(self.statement_data.get('opening_balance_usd', self.statement_data.get('opening_balance', 0)) or 0)
            closing = float(self.statement_data.get('closing_balance_usd', self.statement_data.get('closing_balance', 0)) or 0)
            total_debit = float(self.statement_data.get('total_purchases_usd', self.statement_data.get('total_purchases', 0)) or 0)
            total_credit = float(self.statement_data.get('total_payments_usd', self.statement_data.get('total_payments', 0)) or 0)
            
            summary_data = {
                'اسم المورد': supplier_name,
                'كود المورد': self.selected_supplier.get('code', ''),
                'الرصيد الافتتاحي': config.format_usd(opening),
                'إجمالي المشتريات': config.format_usd(total_debit),
                'إجمالي المدفوعات': config.format_usd(total_credit),
                'الرصيد الختامي': config.format_usd(closing)
            }
            
            success = ExportService.export_to_excel(
                data=export_data, columns=columns, filename=filename,
                title="كشف حساب المورد", parent=self, summary=summary_data
            )
            
            if success:
                MessageDialog.info(self, "نجاح", "تم تصدير الكشف بنجاح")
        except ExportError as e:
            MessageDialog.error(self, "خطأ", e.message)
        except Exception as e:
            MessageDialog.error(self, "خطأ", f"فشل تصدير الكشف: {str(e)}")

    def _export_pdf(self):
        if not self.selected_supplier:
            MessageDialog.warning(self, "تنبيه", "يرجى اختيار المورد أولاً")
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
            for t in self.transactions:
                t_type = t.get('type', '')
                export_data.append({
                    'date': t.get('date', ''),
                    'type_display': self._get_transaction_type_display(t_type).replace('📦 ', '').replace('💵 ', '').replace('↩️ ', '').replace('📂 ', ''),
                    'reference': t.get('reference', ''),
                    'description': t.get('description', ''),
                    'debit': float(t.get('debit_usd', t.get('debit', 0)) or 0),
                    'credit': float(t.get('credit_usd', t.get('credit', 0)) or 0),
                    'balance': float(t.get('balance_usd', t.get('balance', 0)) or 0),
                })
            
            supplier_name = self.selected_supplier.get('name', 'مورد')
            filename = f"كشف_حساب_مورد_{supplier_name}_{datetime.now().strftime('%Y%m%d')}.pdf"
            
            opening = float(self.statement_data.get('opening_balance_usd', self.statement_data.get('opening_balance', 0)) or 0)
            closing = float(self.statement_data.get('closing_balance_usd', self.statement_data.get('closing_balance', 0)) or 0)
            total_debit = float(self.statement_data.get('total_purchases_usd', self.statement_data.get('total_purchases', 0)) or 0)
            total_credit = float(self.statement_data.get('total_payments_usd', self.statement_data.get('total_payments', 0)) or 0)
            
            summary_data = {
                'اسم المورد': supplier_name,
                'كود المورد': self.selected_supplier.get('code', ''),
                'الرصيد الافتتاحي': config.format_usd(opening),
                'إجمالي المشتريات': config.format_usd(total_debit),
                'إجمالي المدفوعات': config.format_usd(total_credit),
                'الرصيد الختامي': config.format_usd(closing)
            }
            
            start_date = self.from_date.date().toString('yyyy-MM-dd')
            end_date = self.to_date.date().toString('yyyy-MM-dd')
            
            success = ExportService.export_to_pdf(
                data=export_data, columns=columns, filename=filename,
                title="كشف حساب المورد", parent=self, summary=summary_data,
                date_range=(start_date, end_date)
            )
            
            if success:
                MessageDialog.info(self, "نجاح", "تم تصدير الكشف بنجاح")
        except ExportError as e:
            MessageDialog.error(self, "خطأ", e.message)
        except Exception as e:
            MessageDialog.error(self, "خطأ", f"فشل تصدير الكشف: {str(e)}")
