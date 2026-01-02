"""Aging Report View - تقرير أعمار الديون - Professional Modern Design"""

from datetime import datetime
from typing import Dict, List

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QDateEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QFrame, QGridLayout,
    QScrollArea, QGraphicsDropShadowEffect, QTabWidget
)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QFont, QBrush, QColor

from ...config import Colors, Fonts, config
from ...widgets.cards import Card
from ...widgets.dialogs import MessageDialog
from ...services.api import api, ApiException
from ...services.export import ExportService, ExportError
from ...utils.error_handler import handle_ui_error


class AgingMetricCard(QFrame):
    """Modern metric card for aging buckets."""
    
    def __init__(self, title: str, value: str, icon: str, color: str, subtitle: str = "", parent=None):
        super().__init__(parent)
        self.accent_color = color
        self.setObjectName("aging_metric_card")
        self.setup_ui(title, value, icon, subtitle)
        self._apply_style()
        
    def setup_ui(self, title: str, value: str, icon: str, subtitle: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)
        
        # Icon and title row
        top = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setFixedSize(36, 36)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet(f"""
            font-size: 18px; background: {self.accent_color}18;
            color: {self.accent_color}; border-radius: 10px;
            border: 1px solid {self.accent_color}30;
        """)
        top.addWidget(icon_label)
        top.addStretch()
        layout.addLayout(top)
        
        # Value
        self.value_label = QLabel(value)
        self.value_label.setFont(QFont(Fonts.FAMILY_AR, 20, QFont.Bold))
        self.value_label.setStyleSheet(f"color: {self.accent_color}; background: transparent;")
        layout.addWidget(self.value_label)
        
        # Title
        title_label = QLabel(title)
        title_label.setFont(QFont(Fonts.FAMILY_AR, 11, QFont.Medium))
        title_label.setStyleSheet(f"color: {Colors.LIGHT_TEXT_SECONDARY}; background: transparent;")
        layout.addWidget(title_label)
        
        # Count label
        self.count_label = QLabel(subtitle)
        self.count_label.setFont(QFont(Fonts.FAMILY_AR, 9))
        self.count_label.setStyleSheet(f"color: {Colors.LIGHT_TEXT_SECONDARY}80; background: transparent;")
        layout.addWidget(self.count_label)
    
    def _apply_style(self):
        self.setStyleSheet(f"""
            QFrame#aging_metric_card {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {Colors.LIGHT_CARD}, stop:1 {self.accent_color}08);
                border: 1px solid {Colors.LIGHT_BORDER}; border-radius: 14px;
                border-top: 3px solid {self.accent_color};
            }}
        """)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(3)
        shadow.setColor(QColor(0, 0, 0, 12))
        self.setGraphicsEffect(shadow)
        
    def update_value(self, value: str, count: int = 0):
        self.value_label.setText(value)
        self.count_label.setText(f"{count} فاتورة")


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


class AgingReportView(QWidget):
    """Professional Aging report view with modern UI."""
    
    invoice_selected = Signal(dict)
    back_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.report_data: Dict = {}
        self.aging_buckets: Dict = {}
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
                    stop:0 #DC2626, stop:1 #F97316);
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
        title = QLabel("⏰ تقرير أعمار الديون")
        title.setFont(QFont(Fonts.FAMILY_AR, 22, QFont.Bold))
        title.setStyleSheet("color: white; background: transparent;")
        title_section.addWidget(title)
        subtitle = QLabel("تحليل المستحقات حسب فترات التأخير")
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
            QPushButton {{ background: #7C3AED; color: white;
                border: none; border-radius: 8px; padding: 10px 18px; }}
            QPushButton:hover {{ background: #6D28D9; }}
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
        filters_layout.addWidget(QLabel("كما في تاريخ:"))
        self.as_of_date = QDateEdit()
        self.as_of_date.setCalendarPopup(True)
        self.as_of_date.setDate(QDate.currentDate())
        self.as_of_date.setMinimumWidth(140)
        filters_layout.addWidget(self.as_of_date)
        
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

        # Aging Buckets
        layout.addWidget(SectionHeader("📊 فترات التأخير"))
        
        buckets_grid = QGridLayout()
        buckets_grid.setSpacing(12)
        
        self.current_card = AgingMetricCard(
            "جاري (غير متأخر)", config.format_usd(0), "✅", Colors.SUCCESS, "0 فاتورة"
        )
        buckets_grid.addWidget(self.current_card, 0, 0)
        
        self.days_1_30_card = AgingMetricCard(
            "1-30 يوم", config.format_usd(0), "📅", Colors.INFO, "0 فاتورة"
        )
        buckets_grid.addWidget(self.days_1_30_card, 0, 1)
        
        self.days_31_60_card = AgingMetricCard(
            "31-60 يوم", config.format_usd(0), "⏰", Colors.WARNING, "0 فاتورة"
        )
        buckets_grid.addWidget(self.days_31_60_card, 0, 2)
        
        self.days_61_90_card = AgingMetricCard(
            "61-90 يوم", config.format_usd(0), "⚠️", Colors.DANGER, "0 فاتورة"
        )
        buckets_grid.addWidget(self.days_61_90_card, 0, 3)
        
        self.days_over_90_card = AgingMetricCard(
            "أكثر من 90 يوم", config.format_usd(0), "🚨", "#7C3AED", "0 فاتورة"
        )
        buckets_grid.addWidget(self.days_over_90_card, 0, 4)
        
        layout.addLayout(buckets_grid)

        # Summary Card
        summary_card = QFrame()
        summary_card.setObjectName("summary_card")
        summary_card.setStyleSheet(f"""
            QFrame#summary_card {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Colors.PRIMARY}15, stop:1 {Colors.PRIMARY}08);
                border: 1px solid {Colors.PRIMARY}30;
                border-radius: 12px;
            }}
        """)
        summary_layout = QHBoxLayout(summary_card)
        summary_layout.setContentsMargins(24, 16, 24, 16)
        
        total_section = QVBoxLayout()
        total_lbl = QLabel("إجمالي المستحقات")
        total_lbl.setFont(QFont(Fonts.FAMILY_AR, 12))
        total_lbl.setStyleSheet(f"color: {Colors.LIGHT_TEXT_SECONDARY}; background: transparent;")
        total_section.addWidget(total_lbl)
        self.total_amount_label = QLabel(config.format_usd(0))
        self.total_amount_label.setFont(QFont(Fonts.FAMILY_AR, 24, QFont.Bold))
        self.total_amount_label.setStyleSheet(f"color: {Colors.PRIMARY}; background: transparent;")
        total_section.addWidget(self.total_amount_label)
        summary_layout.addLayout(total_section)
        
        summary_layout.addStretch()
        
        overdue_section = QVBoxLayout()
        overdue_lbl = QLabel("نسبة المتأخر")
        overdue_lbl.setFont(QFont(Fonts.FAMILY_AR, 12))
        overdue_lbl.setStyleSheet(f"color: {Colors.LIGHT_TEXT_SECONDARY}; background: transparent;")
        overdue_section.addWidget(overdue_lbl)
        self.overdue_percent_label = QLabel("0%")
        self.overdue_percent_label.setFont(QFont(Fonts.FAMILY_AR, 24, QFont.Bold))
        self.overdue_percent_label.setStyleSheet(f"color: {Colors.SUCCESS}; background: transparent;")
        overdue_section.addWidget(self.overdue_percent_label)
        summary_layout.addLayout(overdue_section)
        
        summary_layout.addStretch()
        
        # Status indicator
        self.status_frame = QFrame()
        self.status_frame.setFixedSize(100, 80)
        self._update_status_indicator(0)
        summary_layout.addWidget(self.status_frame)
        
        layout.addWidget(summary_card)

        # Tabs for customer and invoice details
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {Colors.LIGHT_BORDER};
                border-radius: 8px;
                background: {Colors.LIGHT_CARD};
            }}
            QTabBar::tab {{
                background: {Colors.LIGHT_BG};
                color: {Colors.LIGHT_TEXT_SECONDARY};
                padding: 10px 20px;
                border: 1px solid {Colors.LIGHT_BORDER};
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                margin-right: 4px;
            }}
            QTabBar::tab:selected {{
                background: {Colors.LIGHT_CARD};
                color: {Colors.PRIMARY};
                font-weight: bold;
            }}
        """)

        # Customer breakdown tab
        customer_tab = QWidget()
        customer_layout = QVBoxLayout(customer_tab)
        customer_layout.setContentsMargins(16, 16, 16, 16)
        
        cust_note = QLabel("💡 انقر مرتين على العميل لعرض تفاصيل الفواتير")
        cust_note.setFont(QFont(Fonts.FAMILY_AR, 10))
        cust_note.setStyleSheet(f"""
            color: {Colors.LIGHT_TEXT_SECONDARY};
            background: {Colors.INFO}15;
            padding: 8px 12px; border-radius: 6px;
            border-left: 3px solid {Colors.INFO};
        """)
        customer_layout.addWidget(cust_note)
        
        self.customer_table = QTableWidget()
        self.customer_table.setColumnCount(7)
        self.customer_table.setHorizontalHeaderLabels([
            'العميل', 'جاري', '1-30 يوم', '31-60 يوم', '61-90 يوم', '>90 يوم', 'الإجمالي'
        ])
        self.customer_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for i in range(1, 7):
            self.customer_table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)
        self.customer_table.verticalHeader().setVisible(False)
        self.customer_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.customer_table.setAlternatingRowColors(True)
        self.customer_table.doubleClicked.connect(self._on_customer_double_clicked)
        self._style_table(self.customer_table)
        customer_layout.addWidget(self.customer_table)
        self.tabs.addTab(customer_tab, "👥 تفصيل العملاء")
        
        # Invoice details tab
        invoice_tab = QWidget()
        invoice_layout = QVBoxLayout(invoice_tab)
        invoice_layout.setContentsMargins(16, 16, 16, 16)
        
        inv_note = QLabel("💡 الفواتير مرتبة حسب أيام التأخير - الأكثر تأخيراً أولاً")
        inv_note.setFont(QFont(Fonts.FAMILY_AR, 10))
        inv_note.setStyleSheet(f"""
            color: {Colors.LIGHT_TEXT_SECONDARY};
            background: {Colors.WARNING}15;
            padding: 8px 12px; border-radius: 6px;
            border-left: 3px solid {Colors.WARNING};
        """)
        invoice_layout.addWidget(inv_note)
        
        self.invoice_table = QTableWidget()
        self.invoice_table.setColumnCount(8)
        self.invoice_table.setHorizontalHeaderLabels([
            'رقم الفاتورة', 'العميل', 'تاريخ الفاتورة', 'تاريخ الاستحقاق',
            'المبلغ', 'المدفوع', 'المتبقي', 'أيام التأخير'
        ])
        self.invoice_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        for i in [0, 2, 3, 4, 5, 6, 7]:
            self.invoice_table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)
        self.invoice_table.verticalHeader().setVisible(False)
        self.invoice_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.invoice_table.setAlternatingRowColors(True)
        self._style_table(self.invoice_table)
        invoice_layout.addWidget(self.invoice_table)
        self.tabs.addTab(invoice_tab, "📄 تفصيل الفواتير")
        
        layout.addWidget(self.tabs, 1)
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

    def _update_status_indicator(self, overdue_pct: float):
        if overdue_pct >= 50:
            icon, color = "🚨", Colors.DANGER
        elif overdue_pct >= 25:
            icon, color = "⚠️", Colors.WARNING
        elif overdue_pct > 0:
            icon, color = "📊", Colors.INFO
        else:
            icon, color = "✅", Colors.SUCCESS
        
        self.status_frame.setStyleSheet(f"""
            QFrame {{
                background: {color}15;
                border: 2px solid {color}40;
                border-radius: 12px;
            }}
        """)
        
        if self.status_frame.layout():
            while self.status_frame.layout().count():
                item = self.status_frame.layout().takeAt(0)
                if item.widget(): item.widget().deleteLater()
        else:
            QVBoxLayout(self.status_frame)
        
        layout = self.status_frame.layout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setAlignment(Qt.AlignCenter)
        
        icon_lbl = QLabel(icon)
        icon_lbl.setFont(QFont(Fonts.FAMILY_AR, 24))
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet("background: transparent;")
        layout.addWidget(icon_lbl)

    @handle_ui_error
    def refresh(self):
        self._load_report()

    def _load_report(self):
        as_of_date = self.as_of_date.date().toString('yyyy-MM-dd')
        self.report_data = api.get_aging_report(as_of_date=as_of_date)
        self.aging_buckets = self.report_data.get('buckets', {})
        self._update_bucket_cards()
        self._update_customer_table()
        self._update_invoice_table()

    def _update_bucket_cards(self):
        buckets = self.aging_buckets
        
        current = buckets.get('current', {})
        self.current_card.update_value(
            config.format_usd(float(current.get('total_usd', current.get('total', 0)) or 0)),
            int(current.get('invoice_count', 0))
        )
        
        days_1_30 = buckets.get('1_30', {})
        self.days_1_30_card.update_value(
            config.format_usd(float(days_1_30.get('total_usd', days_1_30.get('total', 0)) or 0)),
            int(days_1_30.get('invoice_count', 0))
        )
        
        days_31_60 = buckets.get('31_60', {})
        self.days_31_60_card.update_value(
            config.format_usd(float(days_31_60.get('total_usd', days_31_60.get('total', 0)) or 0)),
            int(days_31_60.get('invoice_count', 0))
        )
        
        days_61_90 = buckets.get('61_90', {})
        self.days_61_90_card.update_value(
            config.format_usd(float(days_61_90.get('total_usd', days_61_90.get('total', 0)) or 0)),
            int(days_61_90.get('invoice_count', 0))
        )
        
        over_90 = buckets.get('over_90', {})
        self.days_over_90_card.update_value(
            config.format_usd(float(over_90.get('total_usd', over_90.get('total', 0)) or 0)),
            int(over_90.get('invoice_count', 0))
        )
        
        # Update summary
        summary = self.report_data.get('summary', {})
        total = float(summary.get('total_outstanding_usd', summary.get('total_outstanding', 0)) or 0)
        self.total_amount_label.setText(config.format_usd(total))
        
        overdue = (
            float(days_1_30.get('total_usd', days_1_30.get('total', 0)) or 0) +
            float(days_31_60.get('total_usd', days_31_60.get('total', 0)) or 0) +
            float(days_61_90.get('total_usd', days_61_90.get('total', 0)) or 0) +
            float(over_90.get('total_usd', over_90.get('total', 0)) or 0)
        )
        
        if total > 0:
            overdue_pct = (overdue / total) * 100
            self.overdue_percent_label.setText(f"{overdue_pct:.1f}%")
            if overdue_pct > 50:
                self.overdue_percent_label.setStyleSheet(f"color: {Colors.DANGER}; background: transparent;")
            elif overdue_pct > 25:
                self.overdue_percent_label.setStyleSheet(f"color: {Colors.WARNING}; background: transparent;")
            else:
                self.overdue_percent_label.setStyleSheet(f"color: {Colors.SUCCESS}; background: transparent;")
            self._update_status_indicator(overdue_pct)
        else:
            self.overdue_percent_label.setText("0%")
            self.overdue_percent_label.setStyleSheet(f"color: {Colors.SUCCESS}; background: transparent;")
            self._update_status_indicator(0)

    def _update_customer_table(self):
        customers = self.report_data.get('customer_breakdown', [])
        self.customer_table.setRowCount(len(customers))
        
        for row, customer in enumerate(customers):
            name_item = QTableWidgetItem(str(customer.get('customer_name', '')))
            name_item.setData(Qt.UserRole, customer)
            name_item.setFont(QFont(Fonts.FAMILY_AR, 11, QFont.Medium))
            self.customer_table.setItem(row, 0, name_item)
            
            current = float(customer.get('current_usd', customer.get('current', 0)) or 0)
            current_item = QTableWidgetItem(config.format_usd(current))
            current_item.setTextAlignment(Qt.AlignCenter)
            if current > 0:
                current_item.setForeground(QColor(Colors.SUCCESS))
            self.customer_table.setItem(row, 1, current_item)
            
            days_1_30 = float(customer.get('1_30_usd', customer.get('1_30', 0)) or 0)
            days_1_30_item = QTableWidgetItem(config.format_usd(days_1_30))
            days_1_30_item.setTextAlignment(Qt.AlignCenter)
            if days_1_30 > 0:
                days_1_30_item.setForeground(QColor(Colors.INFO))
            self.customer_table.setItem(row, 2, days_1_30_item)
            
            days_31_60 = float(customer.get('31_60_usd', customer.get('31_60', 0)) or 0)
            days_31_60_item = QTableWidgetItem(config.format_usd(days_31_60))
            days_31_60_item.setTextAlignment(Qt.AlignCenter)
            if days_31_60 > 0:
                days_31_60_item.setForeground(QColor(Colors.WARNING))
            self.customer_table.setItem(row, 3, days_31_60_item)
            
            days_61_90 = float(customer.get('61_90_usd', customer.get('61_90', 0)) or 0)
            days_61_90_item = QTableWidgetItem(config.format_usd(days_61_90))
            days_61_90_item.setTextAlignment(Qt.AlignCenter)
            if days_61_90 > 0:
                days_61_90_item.setForeground(QColor(Colors.DANGER))
                days_61_90_item.setFont(QFont(Fonts.FAMILY_AR, 11, QFont.Bold))
            self.customer_table.setItem(row, 4, days_61_90_item)
            
            over_90 = float(customer.get('over_90_usd', customer.get('over_90', 0)) or 0)
            over_90_item = QTableWidgetItem(config.format_usd(over_90))
            over_90_item.setTextAlignment(Qt.AlignCenter)
            if over_90 > 0:
                over_90_item.setForeground(QColor("#7C3AED"))
                over_90_item.setFont(QFont(Fonts.FAMILY_AR, 11, QFont.Bold))
            self.customer_table.setItem(row, 5, over_90_item)
            
            total = float(customer.get('total_usd', customer.get('total', 0)) or 0)
            total_item = QTableWidgetItem(config.format_usd(total))
            total_item.setTextAlignment(Qt.AlignCenter)
            total_item.setFont(QFont(Fonts.FAMILY_AR, 11, QFont.Bold))
            total_item.setForeground(QColor(Colors.PRIMARY))
            self.customer_table.setItem(row, 6, total_item)

    def _update_invoice_table(self):
        invoices = []
        for bucket_key, bucket_data in self.aging_buckets.items():
            bucket_invoices = bucket_data.get('invoices', [])
            invoices.extend(bucket_invoices)
        
        invoices.sort(key=lambda x: x.get('days_overdue', 0), reverse=True)
        self.invoice_table.setRowCount(len(invoices))
        
        for row, invoice in enumerate(invoices):
            number_item = QTableWidgetItem(str(invoice.get('invoice_number', '')))
            number_item.setData(Qt.UserRole, invoice)
            number_item.setFont(QFont(Fonts.FAMILY_AR, 10))
            number_item.setForeground(QColor(Colors.PRIMARY))
            self.invoice_table.setItem(row, 0, number_item)
            
            self.invoice_table.setItem(row, 1, QTableWidgetItem(str(invoice.get('customer_name', ''))))
            self.invoice_table.setItem(row, 2, QTableWidgetItem(str(invoice.get('invoice_date', ''))))
            self.invoice_table.setItem(row, 3, QTableWidgetItem(str(invoice.get('due_date', ''))))
            
            total = float(invoice.get('total_amount_usd', invoice.get('total_amount', 0)) or 0)
            total_item = QTableWidgetItem(config.format_usd(total))
            total_item.setTextAlignment(Qt.AlignCenter)
            self.invoice_table.setItem(row, 4, total_item)
            
            paid = float(invoice.get('paid_amount_usd', invoice.get('paid_amount', 0)) or 0)
            paid_item = QTableWidgetItem(config.format_usd(paid))
            paid_item.setTextAlignment(Qt.AlignCenter)
            paid_item.setForeground(QColor(Colors.SUCCESS))
            self.invoice_table.setItem(row, 5, paid_item)
            
            remaining = float(invoice.get('remaining_amount_usd', invoice.get('remaining_amount', 0)) or 0)
            remaining_item = QTableWidgetItem(config.format_usd(remaining))
            remaining_item.setTextAlignment(Qt.AlignCenter)
            remaining_item.setForeground(QColor(Colors.DANGER))
            remaining_item.setFont(QFont(Fonts.FAMILY_AR, 11, QFont.Bold))
            self.invoice_table.setItem(row, 6, remaining_item)
            
            days_overdue = int(invoice.get('days_overdue', 0))
            days_item = QTableWidgetItem(str(days_overdue) if days_overdue > 0 else "جاري")
            days_item.setTextAlignment(Qt.AlignCenter)
            
            if days_overdue > 90:
                days_item.setForeground(QColor("#7C3AED"))
                days_item.setFont(QFont(Fonts.FAMILY_AR, 11, QFont.Bold))
            elif days_overdue > 60:
                days_item.setForeground(QColor(Colors.DANGER))
                days_item.setFont(QFont(Fonts.FAMILY_AR, 11, QFont.Bold))
            elif days_overdue > 30:
                days_item.setForeground(QColor(Colors.WARNING))
            elif days_overdue > 0:
                days_item.setForeground(QColor(Colors.INFO))
            else:
                days_item.setForeground(QColor(Colors.SUCCESS))
            
            self.invoice_table.setItem(row, 7, days_item)

    def _on_customer_double_clicked(self, index):
        row = index.row()
        item = self.customer_table.item(row, 0)
        if item:
            customer = item.data(Qt.UserRole)
            if customer:
                MessageDialog.info(
                    self, "معلومات العميل",
                    f"العميل: {customer.get('customer_name', '')}\n"
                    f"إجمالي المستحقات: {config.format_usd(float(customer.get('total_usd', customer.get('total', 0)) or 0))}"
                )

    def _export_excel(self):
        customer_breakdown = self.report_data.get('customer_breakdown', [])
        
        if not customer_breakdown:
            MessageDialog.warning(self, "تنبيه", "لا توجد بيانات للتصدير")
            return
        
        try:
            columns = [
                ('customer_name', 'العميل'),
                ('current', 'جاري'),
                ('1_30', '1-30 يوم'),
                ('31_60', '31-60 يوم'),
                ('61_90', '61-90 يوم'),
                ('over_90', '>90 يوم'),
                ('total', 'الإجمالي')
            ]
            
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
            
            as_of_date = self.as_of_date.date().toString('yyyy-MM-dd')
            filename = f"تقرير_أعمار_الديون_{as_of_date}.xlsx"
            
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
            
            success = ExportService.export_to_excel(
                data=export_data, columns=columns, filename=filename,
                title="تقرير أعمار الديون", parent=self, summary=summary_data
            )
            
            if success:
                MessageDialog.info(self, "نجاح", "تم تصدير التقرير بنجاح")
                
        except ExportError as e:
            MessageDialog.error(self, "خطأ", e.message)
        except Exception as e:
            MessageDialog.error(self, "خطأ", f"فشل تصدير التقرير: {str(e)}")

    def _export_pdf(self):
        customer_breakdown = self.report_data.get('customer_breakdown', [])
        
        if not customer_breakdown:
            MessageDialog.warning(self, "تنبيه", "لا توجد بيانات للتصدير")
            return
        
        try:
            columns = [
                ('customer_name', 'العميل'),
                ('current', 'جاري'),
                ('1_30', '1-30 يوم'),
                ('31_60', '31-60 يوم'),
                ('61_90', '61-90 يوم'),
                ('over_90', '>90 يوم'),
                ('total', 'الإجمالي')
            ]
            
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
            
            as_of_date = self.as_of_date.date().toString('yyyy-MM-dd')
            filename = f"تقرير_أعمار_الديون_{as_of_date}.pdf"
            
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
            
            success = ExportService.export_to_pdf(
                data=export_data, columns=columns, filename=filename,
                title="تقرير أعمار الديون", parent=self, summary=summary_data,
                date_range=(as_of_date, as_of_date)
            )
            
            if success:
                MessageDialog.info(self, "نجاح", "تم تصدير التقرير بنجاح")
                
        except ExportError as e:
            MessageDialog.error(self, "خطأ", e.message)
        except Exception as e:
            MessageDialog.error(self, "خطأ", f"فشل تصدير التقرير: {str(e)}")
