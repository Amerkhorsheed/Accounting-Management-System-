"""Receivables Report View - تقرير المستحقات - Professional Modern Design"""

from datetime import datetime
from typing import Dict, List

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


class ReceivableMetricCard(QFrame):
    def __init__(self, title: str, value: str, icon: str, color: str, subtitle: str = "", parent=None):
        super().__init__(parent)
        self.accent_color = color
        self.setObjectName("receivable_metric_card")
        self.setup_ui(title, value, icon, subtitle)
        self._apply_style()
        
    def setup_ui(self, title: str, value: str, icon: str, subtitle: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(8)
        top = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setFixedSize(44, 44)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet(f"""
            font-size: 22px; background: {self.accent_color}18;
            color: {self.accent_color}; border-radius: 12px;
            border: 1px solid {self.accent_color}30;
        """)
        top.addWidget(icon_label)
        top.addStretch()
        layout.addLayout(top)
        self.value_label = QLabel(value)
        self.value_label.setFont(QFont(Fonts.FAMILY_AR, 26, QFont.Bold))
        self.value_label.setStyleSheet(f"color: {self.accent_color}; background: transparent;")
        layout.addWidget(self.value_label)
        title_label = QLabel(title)
        title_label.setFont(QFont(Fonts.FAMILY_AR, 12, QFont.Medium))
        title_label.setStyleSheet(f"color: {Colors.LIGHT_TEXT_SECONDARY}; background: transparent;")
        layout.addWidget(title_label)
        if subtitle:
            sub_label = QLabel(subtitle)
            sub_label.setFont(QFont(Fonts.FAMILY_AR, 10))
            sub_label.setStyleSheet(f"color: {Colors.LIGHT_TEXT_SECONDARY}80; background: transparent;")
            layout.addWidget(sub_label)
    
    def _apply_style(self):
        self.setStyleSheet(f"""
            QFrame#receivable_metric_card {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {Colors.LIGHT_CARD}, stop:1 {self.accent_color}08);
                border: 1px solid {Colors.LIGHT_BORDER}; border-radius: 16px;
                border-left: 4px solid {self.accent_color};
            }}
        """)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 15))
        self.setGraphicsEffect(shadow)
        
    def update_value(self, value: str):
        self.value_label.setText(value)


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


class ReceivablesReportView(QWidget):
    """Professional Receivables report view."""
    
    customer_selected = Signal(dict)
    back_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.report_data: Dict = {}
        self.customers_list: List[Dict] = []
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
                    stop:0 {Colors.PRIMARY}, stop:1 #8B5CF6);
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
        title = QLabel("💰 تقرير المستحقات")
        title.setFont(QFont(Fonts.FAMILY_AR, 22, QFont.Bold))
        title.setStyleSheet("color: white; background: transparent;")
        title_section.addWidget(title)
        subtitle = QLabel("تحليل شامل لأرصدة العملاء والمستحقات المالية")
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
        
        filters_layout.addWidget(QLabel("📅"))
        filters_layout.addWidget(QLabel("نوع العميل:"))
        self.customer_type_combo = QComboBox()
        self.customer_type_combo.addItem("الكل", None)
        self.customer_type_combo.addItem("آجل", "credit")
        self.customer_type_combo.addItem("نقدي", "cash")
        self.customer_type_combo.setMinimumWidth(100)
        filters_layout.addWidget(self.customer_type_combo)
        
        apply_btn = QPushButton("🔍 عرض التقرير")
        apply_btn.setCursor(Qt.PointingHandCursor)
        apply_btn.setStyleSheet(f"""
            QPushButton {{ background: {Colors.PRIMARY}; color: white;
                border: none; border-radius: 8px; padding: 10px 24px; font-weight: 600; }}
            QPushButton:hover {{ background: {Colors.PRIMARY_DARK}; }}
        """)
        apply_btn.clicked.connect(self.refresh)
        filters_layout.addWidget(apply_btn)
        filters_layout.addStretch()
        layout.addWidget(filters_card)

        # Metrics
        layout.addWidget(SectionHeader("📊 ملخص المستحقات"))
        
        metrics_grid = QGridLayout()
        metrics_grid.setSpacing(16)
        
        self.total_receivables_card = ReceivableMetricCard(
            "إجمالي المستحقات", config.format_usd(0), "💰", Colors.PRIMARY, "Total Receivables"
        )
        metrics_grid.addWidget(self.total_receivables_card, 0, 0)
        
        self.overdue_card = ReceivableMetricCard(
            "المستحقات المتأخرة", config.format_usd(0), "⚠️", Colors.DANGER, "Overdue Amount"
        )
        metrics_grid.addWidget(self.overdue_card, 0, 1)
        
        self.customer_count_card = ReceivableMetricCard(
            "عدد العملاء", "0", "👥", Colors.INFO, "Customers with Balance"
        )
        metrics_grid.addWidget(self.customer_count_card, 0, 2)
        
        self.status_card = QFrame()
        self.status_card.setObjectName("status_card")
        self._update_status_card(0, 0)
        metrics_grid.addWidget(self.status_card, 0, 3)
        
        layout.addLayout(metrics_grid)

        # Customers Table
        layout.addWidget(SectionHeader("👥 أرصدة العملاء"))
        
        customers_card = QFrame()
        customers_card.setObjectName("customers_card")
        customers_card.setStyleSheet(f"""
            QFrame#customers_card {{
                background: {Colors.LIGHT_CARD};
                border: 1px solid {Colors.LIGHT_BORDER};
                border-radius: 12px;
            }}
        """)
        customers_layout = QVBoxLayout(customers_card)
        customers_layout.setContentsMargins(20, 16, 20, 16)
        customers_layout.setSpacing(12)
        
        note = QLabel("💡 العملاء مرتبين حسب الرصيد المستحق - انقر على العميل لعرض كشف الحساب")
        note.setFont(QFont(Fonts.FAMILY_AR, 10))
        note.setStyleSheet(f"""
            color: {Colors.LIGHT_TEXT_SECONDARY};
            background: {Colors.PRIMARY}15;
            padding: 8px 12px; border-radius: 6px;
            border-left: 3px solid {Colors.PRIMARY};
        """)
        customers_layout.addWidget(note)
        
        self.customers_table = QTableWidget()
        self.customers_table.setColumnCount(6)
        self.customers_table.setHorizontalHeaderLabels([
            'الكود', 'اسم العميل', 'نوع العميل', 'حد الائتمان', 'الرصيد المستحق', 'الحالة'
        ])
        self.customers_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.customers_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        for i in range(2, 6):
            self.customers_table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)
        self.customers_table.verticalHeader().setVisible(False)
        self.customers_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.customers_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.customers_table.setAlternatingRowColors(True)
        self.customers_table.setMinimumHeight(400)
        self.customers_table.cellDoubleClicked.connect(self._on_customer_clicked)
        self._style_table(self.customers_table)
        customers_layout.addWidget(self.customers_table)
        
        layout.addWidget(customers_card, 1)
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

    def _update_status_card(self, overdue: float, total: float):
        pct = (overdue / total * 100) if total > 0 else 0
        if pct >= 50:
            status_icon, status_text, status_color = "🚨", "تحذير!", Colors.DANGER
        elif pct >= 25:
            status_icon, status_text, status_color = "⚠️", "يحتاج متابعة", Colors.WARNING
        elif pct > 0:
            status_icon, status_text, status_color = "📊", "جيد", Colors.INFO
        else:
            status_icon, status_text, status_color = "✅", "ممتاز", Colors.SUCCESS
        
        self.status_card.setStyleSheet(f"""
            QFrame#status_card {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {status_color}15, stop:1 {status_color}08);
                border: 2px solid {status_color}40; border-radius: 16px;
            }}
        """)
        
        if self.status_card.layout():
            while self.status_card.layout().count():
                item = self.status_card.layout().takeAt(0)
                if item.widget(): item.widget().deleteLater()
        else:
            QVBoxLayout(self.status_card)
        
        layout = self.status_card.layout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignCenter)
        
        icon_lbl = QLabel(status_icon)
        icon_lbl.setFont(QFont(Fonts.FAMILY_AR, 36))
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet("background: transparent;")
        layout.addWidget(icon_lbl)
        
        status_lbl = QLabel(status_text)
        status_lbl.setFont(QFont(Fonts.FAMILY_AR, 16, QFont.Bold))
        status_lbl.setAlignment(Qt.AlignCenter)
        status_lbl.setStyleSheet(f"color: {status_color}; background: transparent;")
        layout.addWidget(status_lbl)
        
        desc_lbl = QLabel("حالة التحصيل")
        desc_lbl.setFont(QFont(Fonts.FAMILY_AR, 10))
        desc_lbl.setAlignment(Qt.AlignCenter)
        desc_lbl.setStyleSheet(f"color: {Colors.LIGHT_TEXT_SECONDARY}; background: transparent;")
        layout.addWidget(desc_lbl)

    def _on_customer_clicked(self, row: int, col: int):
        """Handle customer row double-click to show statement."""
        if row < len(self.customers_list):
            customer = self.customers_list[row]
            self.customer_selected.emit(customer)

    @handle_ui_error
    def refresh(self):
        """Refresh the receivables report data."""
        self._load_report()

    def _load_report(self):
        """Load receivables report data from API."""
        customer_type = self.customer_type_combo.currentData()
        
        params = {}
        if customer_type:
            params['customer_type'] = customer_type
        
        self.report_data = api.get_receivables_report(**params)
        self._update_ui()

    def _update_ui(self):
        """Update all UI elements with report data."""
        data = self.report_data or {}
        
        # Extract summary values
        total_receivables = float(data.get('total_receivables_usd', data.get('total_receivables', 0)) or 0)
        overdue_amount = float(data.get('overdue_amount_usd', data.get('overdue_amount', 0)) or 0)
        customer_count = int(data.get('customer_count', 0))
        
        # Update metric cards
        self.total_receivables_card.update_value(config.format_usd(total_receivables))
        self.overdue_card.update_value(config.format_usd(overdue_amount))
        self.customer_count_card.update_value(str(customer_count))
        
        # Update status card
        self._update_status_card(overdue_amount, total_receivables)
        
        # Update customers table
        self.customers_list = data.get('customers', [])
        self._update_customers_table()

    def _update_customers_table(self):
        """Update the customers table with receivables data."""
        self.customers_table.setRowCount(len(self.customers_list))
        
        for row, customer in enumerate(self.customers_list):
            # Code
            code = str(customer.get('code', ''))
            code_item = QTableWidgetItem(code)
            code_item.setTextAlignment(Qt.AlignCenter)
            code_item.setFont(QFont(Fonts.FAMILY_AR, 10))
            code_item.setForeground(QBrush(QColor(Colors.LIGHT_TEXT_SECONDARY)))
            self.customers_table.setItem(row, 0, code_item)
            
            # Name
            name = str(customer.get('name', ''))
            name_item = QTableWidgetItem(name)
            name_item.setFont(QFont(Fonts.FAMILY_AR, 11, QFont.Medium))
            self.customers_table.setItem(row, 1, name_item)
            
            # Customer type
            cust_type = customer.get('customer_type', '')
            type_display = 'آجل' if cust_type == 'credit' else 'نقدي'
            type_item = QTableWidgetItem(type_display)
            type_item.setTextAlignment(Qt.AlignCenter)
            if cust_type == 'credit':
                type_item.setForeground(QBrush(QColor(Colors.WARNING)))
            else:
                type_item.setForeground(QBrush(QColor(Colors.SUCCESS)))
            self.customers_table.setItem(row, 2, type_item)
            
            # Credit limit
            credit_limit = float(customer.get('credit_limit_usd', customer.get('credit_limit', 0)) or 0)
            limit_item = QTableWidgetItem(config.format_usd(credit_limit))
            limit_item.setTextAlignment(Qt.AlignCenter)
            self.customers_table.setItem(row, 3, limit_item)
            
            # Balance
            balance = float(customer.get('balance_usd', customer.get('balance', 0)) or 0)
            balance_item = QTableWidgetItem(config.format_usd(balance))
            balance_item.setTextAlignment(Qt.AlignCenter)
            balance_item.setFont(QFont(Fonts.FAMILY_AR, 11, QFont.Bold))
            if balance > 0:
                balance_item.setForeground(QBrush(QColor(Colors.DANGER)))
            else:
                balance_item.setForeground(QBrush(QColor(Colors.SUCCESS)))
            self.customers_table.setItem(row, 4, balance_item)
            
            # Status
            if balance <= 0:
                status = "✅ مسدد"
                status_color = Colors.SUCCESS
            elif credit_limit > 0 and balance > credit_limit:
                status = "🚨 تجاوز الحد"
                status_color = Colors.DANGER
            elif balance > 0:
                status = "⏳ مستحق"
                status_color = Colors.WARNING
            else:
                status = "✅ جيد"
                status_color = Colors.SUCCESS
            
            status_item = QTableWidgetItem(status)
            status_item.setTextAlignment(Qt.AlignCenter)
            status_item.setForeground(QBrush(QColor(status_color)))
            self.customers_table.setItem(row, 5, status_item)

    def _export_excel(self):
        """Export receivables report to Excel."""
        if not self.customers_list:
            MessageDialog.warning(self, "تنبيه", "لا توجد بيانات للتصدير")
            return
        
        try:
            columns = [
                ('code', 'الكود'),
                ('name', 'اسم العميل'),
                ('customer_type_display', 'نوع العميل'),
                ('credit_limit', 'حد الائتمان'),
                ('balance', 'الرصيد المستحق')
            ]
            
            export_data = []
            for customer in self.customers_list:
                cust_type = customer.get('customer_type', '')
                export_data.append({
                    'code': customer.get('code', ''),
                    'name': customer.get('name', ''),
                    'customer_type_display': 'آجل' if cust_type == 'credit' else 'نقدي',
                    'credit_limit': float(customer.get('credit_limit_usd', customer.get('credit_limit', 0)) or 0),
                    'balance': float(customer.get('balance_usd', customer.get('balance', 0)) or 0)
                })
            
            filename = f"تقرير_المستحقات_{datetime.now().strftime('%Y%m%d')}.xlsx"
            
            data = self.report_data or {}
            summary_data = {
                'إجمالي المستحقات': config.format_usd(float(data.get('total_receivables_usd', data.get('total_receivables', 0)) or 0)),
                'المستحقات المتأخرة': config.format_usd(float(data.get('overdue_amount_usd', data.get('overdue_amount', 0)) or 0)),
                'عدد العملاء': str(int(data.get('customer_count', 0)))
            }
            
            success = ExportService.export_to_excel(
                data=export_data,
                columns=columns,
                filename=filename,
                title="تقرير المستحقات",
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
        """Export receivables report to PDF."""
        if not self.customers_list:
            MessageDialog.warning(self, "تنبيه", "لا توجد بيانات للتصدير")
            return
        
        try:
            columns = [
                ('code', 'الكود'),
                ('name', 'اسم العميل'),
                ('customer_type_display', 'نوع العميل'),
                ('credit_limit', 'حد الائتمان'),
                ('balance', 'الرصيد المستحق')
            ]
            
            export_data = []
            for customer in self.customers_list:
                cust_type = customer.get('customer_type', '')
                export_data.append({
                    'code': customer.get('code', ''),
                    'name': customer.get('name', ''),
                    'customer_type_display': 'آجل' if cust_type == 'credit' else 'نقدي',
                    'credit_limit': float(customer.get('credit_limit_usd', customer.get('credit_limit', 0)) or 0),
                    'balance': float(customer.get('balance_usd', customer.get('balance', 0)) or 0)
                })
            
            filename = f"تقرير_المستحقات_{datetime.now().strftime('%Y%m%d')}.pdf"
            
            data = self.report_data or {}
            summary_data = {
                'إجمالي المستحقات': config.format_usd(float(data.get('total_receivables_usd', data.get('total_receivables', 0)) or 0)),
                'المستحقات المتأخرة': config.format_usd(float(data.get('overdue_amount_usd', data.get('overdue_amount', 0)) or 0)),
                'عدد العملاء': str(int(data.get('customer_count', 0)))
            }
            
            success = ExportService.export_to_pdf(
                data=export_data,
                columns=columns,
                filename=filename,
                title="تقرير المستحقات",
                parent=self,
                summary=summary_data
            )
            
            if success:
                MessageDialog.info(self, "نجاح", "تم تصدير التقرير بنجاح")
                
        except ExportError as e:
            MessageDialog.error(self, "خطأ", e.message)
        except Exception as e:
            MessageDialog.error(self, "خطأ", f"فشل تصدير التقرير: {str(e)}")
