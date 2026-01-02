"""Sales Report View - تقرير المبيعات - Professional Modern Design"""

from datetime import datetime
from typing import Dict, List

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QDateEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QFrame, QGridLayout,
    QScrollArea, QGraphicsDropShadowEffect, QProgressBar,
    QComboBox
)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QFont, QBrush, QColor

from ...config import Colors, Fonts, config
from ...widgets.cards import Card
from ...widgets.dialogs import MessageDialog
from ...services.api import api, ApiException
from ...services.export import ExportService, ExportError
from ...utils.error_handler import handle_ui_error


class SalesMetricCard(QFrame):
    """Modern metric card with gradient accent for sales data."""
    
    def __init__(self, title: str, value: str, icon: str, color: str,
                 subtitle: str = "", trend: str = "", parent=None):
        super().__init__(parent)
        self.accent_color = color
        self.setObjectName("sales_metric_card")
        self.setup_ui(title, value, icon, subtitle, trend)
        self._apply_style()
        
    def setup_ui(self, title: str, value: str, icon: str, subtitle: str, trend: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(8)
        
        # Top row with icon and trend
        top = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setFixedSize(44, 44)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet(f"""
            font-size: 22px;
            background: {self.accent_color}18;
            color: {self.accent_color};
            border-radius: 12px;
            border: 1px solid {self.accent_color}30;
        """)
        top.addWidget(icon_label)
        top.addStretch()
        
        # Trend indicator
        if trend:
            trend_label = QLabel(trend)
            trend_label.setFont(QFont(Fonts.FAMILY_AR, 10, QFont.Bold))
            is_positive = trend.startswith('+') or (not trend.startswith('-') and '%' in trend)
            trend_color = Colors.SUCCESS if is_positive else Colors.DANGER
            trend_label.setStyleSheet(f"""
                color: {trend_color};
                background: {trend_color}15;
                padding: 4px 10px;
                border-radius: 12px;
            """)
            top.addWidget(trend_label)
        layout.addLayout(top)
        
        # Value - large and prominent
        self.value_label = QLabel(value)
        self.value_label.setFont(QFont(Fonts.FAMILY_AR, 26, QFont.Bold))
        self.value_label.setStyleSheet(f"color: {self.accent_color}; background: transparent;")
        layout.addWidget(self.value_label)
        
        # Title
        title_label = QLabel(title)
        title_label.setFont(QFont(Fonts.FAMILY_AR, 12, QFont.Medium))
        title_label.setStyleSheet(f"color: {Colors.LIGHT_TEXT_SECONDARY}; background: transparent;")
        layout.addWidget(title_label)
        
        # Subtitle
        if subtitle:
            sub_label = QLabel(subtitle)
            sub_label.setFont(QFont(Fonts.FAMILY_AR, 10))
            sub_label.setStyleSheet(f"color: {Colors.LIGHT_TEXT_SECONDARY}80; background: transparent;")
            layout.addWidget(sub_label)
    
    def _apply_style(self):
        self.setStyleSheet(f"""
            QFrame#sales_metric_card {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {Colors.LIGHT_CARD}, stop:1 {self.accent_color}08);
                border: 1px solid {Colors.LIGHT_BORDER};
                border-radius: 16px;
                border-left: 4px solid {self.accent_color};
            }}
        """)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 15))
        self.setGraphicsEffect(shadow)
        
    def update_value(self, value: str, trend: str = ""):
        self.value_label.setText(value)


class TrendBar(QFrame):
    """Visual trend bar for sales data."""
    
    def __init__(self, label: str, value: float, max_value: float, color: str, parent=None):
        super().__init__(parent)
        self.setObjectName("trend_bar")
        self.setup_ui(label, value, max_value, color)
        
    def setup_ui(self, label: str, value: float, max_value: float, color: str):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)
        
        # Label
        label_widget = QLabel(label)
        label_widget.setFont(QFont(Fonts.FAMILY_AR, 11))
        label_widget.setMinimumWidth(120)
        label_widget.setStyleSheet("background: transparent;")
        layout.addWidget(label_widget)
        
        # Progress bar
        progress = QProgressBar()
        progress.setRange(0, 100)
        pct = int((value / max_value * 100) if max_value > 0 else 0)
        progress.setValue(min(100, pct))
        progress.setTextVisible(False)
        progress.setFixedHeight(12)
        progress.setStyleSheet(f"""
            QProgressBar {{
                background: {Colors.LIGHT_BORDER};
                border: none;
                border-radius: 6px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {color}, stop:1 {color}aa);
                border-radius: 6px;
            }}
        """)
        layout.addWidget(progress, 1)
        
        # Value
        value_label = QLabel(config.format_usd(value))
        value_label.setFont(QFont(Fonts.FAMILY_AR, 11, QFont.Bold))
        value_label.setAlignment(Qt.AlignRight)
        value_label.setMinimumWidth(100)
        value_label.setStyleSheet(f"color: {color}; background: transparent;")
        layout.addWidget(value_label)
        
        self.setStyleSheet(f"""
            QFrame#trend_bar {{
                background: {Colors.LIGHT_CARD};
                border-radius: 8px;
            }}
        """)


class SectionHeader(QFrame):
    """Section header with icon and title."""
    
    def __init__(self, title: str, icon: str = "", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 12)
        
        if icon:
            icon_lbl = QLabel(icon)
            icon_lbl.setFont(QFont(Fonts.FAMILY_AR, 16))
            icon_lbl.setStyleSheet("background: transparent;")
            layout.addWidget(icon_lbl)
        
        title_lbl = QLabel(title)
        title_lbl.setFont(QFont(Fonts.FAMILY_AR, 16, QFont.Bold))
        title_lbl.setStyleSheet(f"color: {Colors.LIGHT_TEXT}; background: transparent;")
        layout.addWidget(title_lbl)
        layout.addStretch()
        
        self.setStyleSheet("background: transparent;")


class SalesReportView(QWidget):
    """Professional Sales report view with modern UI/UX."""

    back_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.report_data: Dict = {}
        self.setup_ui()

    def go_back(self):
        self.back_requested.emit()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(20)

        # ═══════════════════════════════════════════════════════════
        # HEADER SECTION
        # ═══════════════════════════════════════════════════════════
        header_card = QFrame()
        header_card.setObjectName("header_card")
        header_card.setStyleSheet(f"""
            QFrame#header_card {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Colors.PRIMARY}, stop:1 #6366F1);
                border-radius: 16px;
            }}
        """)
        header_layout = QHBoxLayout(header_card)
        header_layout.setContentsMargins(24, 20, 24, 20)
        
        # Back button
        back_btn = QPushButton("→ رجوع")
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255,255,255,0.2);
                color: white;
                border: 1px solid rgba(255,255,255,0.3);
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background: rgba(255,255,255,0.3);
            }}
        """)
        back_btn.clicked.connect(self.go_back)
        header_layout.addWidget(back_btn)
        
        # Title section
        title_section = QVBoxLayout()
        title_section.setSpacing(4)
        title = QLabel("📊 تقرير المبيعات")
        title.setFont(QFont(Fonts.FAMILY_AR, 22, QFont.Bold))
        title.setStyleSheet("color: white; background: transparent;")
        title_section.addWidget(title)
        
        subtitle = QLabel("تحليل شامل لأداء المبيعات والعملاء والمنتجات")
        subtitle.setFont(QFont(Fonts.FAMILY_AR, 12))
        subtitle.setStyleSheet("color: rgba(255,255,255,0.85); background: transparent;")
        title_section.addWidget(subtitle)
        header_layout.addLayout(title_section)
        header_layout.addStretch()
        
        # Action buttons
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(10)
        
        refresh_btn = QPushButton("🔄 تحديث")
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255,255,255,0.15);
                color: white;
                border: 1px solid rgba(255,255,255,0.25);
                border-radius: 8px;
                padding: 10px 18px;
            }}
            QPushButton:hover {{ background: rgba(255,255,255,0.25); }}
        """)
        refresh_btn.clicked.connect(self.refresh)
        actions_layout.addWidget(refresh_btn)
        
        export_excel_btn = QPushButton("📊 Excel")
        export_excel_btn.setCursor(Qt.PointingHandCursor)
        export_excel_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Colors.SUCCESS};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 18px;
            }}
            QPushButton:hover {{ background: {Colors.SUCCESS}dd; }}
        """)
        export_excel_btn.clicked.connect(self._export_excel)
        actions_layout.addWidget(export_excel_btn)
        
        export_pdf_btn = QPushButton("📄 PDF")
        export_pdf_btn.setCursor(Qt.PointingHandCursor)
        export_pdf_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Colors.DANGER};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 18px;
            }}
            QPushButton:hover {{ background: {Colors.DANGER}dd; }}
        """)
        export_pdf_btn.clicked.connect(self._export_pdf)
        actions_layout.addWidget(export_pdf_btn)
        
        header_layout.addLayout(actions_layout)
        layout.addWidget(header_card)

        # ═══════════════════════════════════════════════════════════
        # FILTERS SECTION
        # ═══════════════════════════════════════════════════════════
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
        
        # Date range icon
        date_icon = QLabel("📅")
        date_icon.setFont(QFont(Fonts.FAMILY_AR, 16))
        date_icon.setStyleSheet("background: transparent;")
        filters_layout.addWidget(date_icon)
        
        from_label = QLabel("من:")
        from_label.setFont(QFont(Fonts.FAMILY_AR, 12, QFont.Medium))
        from_label.setStyleSheet(f"color: {Colors.LIGHT_TEXT_SECONDARY}; background: transparent;")
        filters_layout.addWidget(from_label)
        
        self.from_date = QDateEdit()
        self.from_date.setCalendarPopup(True)
        self.from_date.setDate(QDate.currentDate().addMonths(-1))
        self.from_date.setMinimumWidth(140)
        filters_layout.addWidget(self.from_date)
        
        to_label = QLabel("إلى:")
        to_label.setFont(QFont(Fonts.FAMILY_AR, 12, QFont.Medium))
        to_label.setStyleSheet(f"color: {Colors.LIGHT_TEXT_SECONDARY}; background: transparent;")
        filters_layout.addWidget(to_label)
        
        self.to_date = QDateEdit()
        self.to_date.setCalendarPopup(True)
        self.to_date.setDate(QDate.currentDate())
        self.to_date.setMinimumWidth(140)
        filters_layout.addWidget(self.to_date)
        
        # Group by selector
        group_label = QLabel("تجميع:")
        group_label.setFont(QFont(Fonts.FAMILY_AR, 12, QFont.Medium))
        group_label.setStyleSheet(f"color: {Colors.LIGHT_TEXT_SECONDARY}; background: transparent;")
        filters_layout.addWidget(group_label)
        
        self.group_by = QComboBox()
        self.group_by.addItem("يومي", "day")
        self.group_by.addItem("شهري", "month")
        self.group_by.setMinimumWidth(100)
        filters_layout.addWidget(self.group_by)
        
        apply_btn = QPushButton("🔍 عرض التقرير")
        apply_btn.setCursor(Qt.PointingHandCursor)
        apply_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Colors.PRIMARY};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 24px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background: {Colors.PRIMARY_DARK}; }}
        """)
        apply_btn.clicked.connect(self.refresh)
        filters_layout.addWidget(apply_btn)
        filters_layout.addStretch()
        
        layout.addWidget(filters_card)

        # ═══════════════════════════════════════════════════════════
        # KEY METRICS SECTION
        # ═══════════════════════════════════════════════════════════
        layout.addWidget(SectionHeader("📈 ملخص المبيعات", ""))
        
        metrics_grid = QGridLayout()
        metrics_grid.setSpacing(16)
        
        self.total_sales_card = SalesMetricCard(
            "إجمالي المبيعات", config.format_usd(0), "💰", Colors.PRIMARY,
            "Total Sales"
        )
        metrics_grid.addWidget(self.total_sales_card, 0, 0)
        
        self.invoice_count_card = SalesMetricCard(
            "عدد الفواتير", "0", "📄", Colors.INFO,
            "Invoice Count"
        )
        metrics_grid.addWidget(self.invoice_count_card, 0, 1)
        
        self.avg_sale_card = SalesMetricCard(
            "متوسط قيمة الفاتورة", config.format_usd(0), "📊", Colors.SUCCESS,
            "Average Sale Value"
        )
        metrics_grid.addWidget(self.avg_sale_card, 0, 2)
        
        # Performance status card
        self.status_card = QFrame()
        self.status_card.setObjectName("status_card")
        self._update_status_card(0, 0)
        metrics_grid.addWidget(self.status_card, 0, 3)
        
        layout.addLayout(metrics_grid)

        # ═══════════════════════════════════════════════════════════
        # TOP CUSTOMERS SECTION
        # ═══════════════════════════════════════════════════════════
        layout.addWidget(SectionHeader("👥 أفضل العملاء", ""))
        
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
        
        cust_note = QLabel("💡 أفضل 10 عملاء حسب إجمالي المشتريات خلال الفترة المحددة")
        cust_note.setFont(QFont(Fonts.FAMILY_AR, 10))
        cust_note.setStyleSheet(f"""
            color: {Colors.LIGHT_TEXT_SECONDARY};
            background: {Colors.INFO}15;
            padding: 8px 12px;
            border-radius: 6px;
            border-left: 3px solid {Colors.INFO};
        """)
        customers_layout.addWidget(cust_note)
        
        self.customers_table = QTableWidget()
        self.customers_table.setColumnCount(5)
        self.customers_table.setHorizontalHeaderLabels([
            'الترتيب', 'العميل', 'عدد الفواتير', 'الإجمالي', 'الحالة'
        ])
        self.customers_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.customers_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.customers_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.customers_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.customers_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.customers_table.verticalHeader().setVisible(False)
        self.customers_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.customers_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.customers_table.setAlternatingRowColors(True)
        self.customers_table.setMinimumHeight(280)
        self._style_table(self.customers_table)
        customers_layout.addWidget(self.customers_table)
        
        layout.addWidget(customers_card)

        # ═══════════════════════════════════════════════════════════
        # TOP PRODUCTS SECTION
        # ═══════════════════════════════════════════════════════════
        layout.addWidget(SectionHeader("📦 أفضل المنتجات مبيعاً", ""))
        
        products_card = QFrame()
        products_card.setObjectName("products_card")
        products_card.setStyleSheet(f"""
            QFrame#products_card {{
                background: {Colors.LIGHT_CARD};
                border: 1px solid {Colors.LIGHT_BORDER};
                border-radius: 12px;
            }}
        """)
        products_layout = QVBoxLayout(products_card)
        products_layout.setContentsMargins(20, 16, 20, 16)
        products_layout.setSpacing(12)
        
        prod_note = QLabel("💡 أفضل 10 منتجات حسب قيمة المبيعات خلال الفترة المحددة")
        prod_note.setFont(QFont(Fonts.FAMILY_AR, 10))
        prod_note.setStyleSheet(f"""
            color: {Colors.LIGHT_TEXT_SECONDARY};
            background: {Colors.SUCCESS}15;
            padding: 8px 12px;
            border-radius: 6px;
            border-left: 3px solid {Colors.SUCCESS};
        """)
        products_layout.addWidget(prod_note)
        
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(5)
        self.products_table.setHorizontalHeaderLabels([
            'الترتيب', 'المنتج', 'الكمية المباعة', 'إجمالي القيمة', 'الأداء'
        ])
        self.products_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.products_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.products_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.products_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.products_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.products_table.verticalHeader().setVisible(False)
        self.products_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.products_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.products_table.setAlternatingRowColors(True)
        self.products_table.setMinimumHeight(280)
        self._style_table(self.products_table)
        products_layout.addWidget(self.products_table)
        
        layout.addWidget(products_card)

        # ═══════════════════════════════════════════════════════════
        # SALES TREND SECTION
        # ═══════════════════════════════════════════════════════════
        layout.addWidget(SectionHeader("📈 اتجاه المبيعات", ""))
        
        trend_card = QFrame()
        trend_card.setObjectName("trend_card")
        trend_card.setStyleSheet(f"""
            QFrame#trend_card {{
                background: {Colors.LIGHT_CARD};
                border: 1px solid {Colors.LIGHT_BORDER};
                border-radius: 12px;
            }}
        """)
        trend_layout = QVBoxLayout(trend_card)
        trend_layout.setContentsMargins(20, 16, 20, 16)
        trend_layout.setSpacing(12)
        
        trend_note = QLabel("💡 توزيع المبيعات حسب الفترة الزمنية المحددة")
        trend_note.setFont(QFont(Fonts.FAMILY_AR, 10))
        trend_note.setStyleSheet(f"""
            color: {Colors.LIGHT_TEXT_SECONDARY};
            background: {Colors.WARNING}15;
            padding: 8px 12px;
            border-radius: 6px;
            border-left: 3px solid {Colors.WARNING};
        """)
        trend_layout.addWidget(trend_note)
        
        self.trend_table = QTableWidget()
        self.trend_table.setColumnCount(4)
        self.trend_table.setHorizontalHeaderLabels([
            'الفترة', 'عدد الفواتير', 'الإجمالي', 'النسبة'
        ])
        self.trend_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.trend_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.trend_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.trend_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.trend_table.verticalHeader().setVisible(False)
        self.trend_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.trend_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.trend_table.setAlternatingRowColors(True)
        self.trend_table.setMinimumHeight(250)
        self._style_table(self.trend_table)
        trend_layout.addWidget(self.trend_table)
        
        layout.addWidget(trend_card, 1)
        
        # Add stretch at bottom
        layout.addStretch()
        
        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    def _style_table(self, table: QTableWidget):
        """Apply modern styling to table."""
        table.setStyleSheet(f"""
            QTableWidget {{
                background: {Colors.LIGHT_CARD};
                border: 1px solid {Colors.LIGHT_BORDER};
                border-radius: 8px;
                gridline-color: {Colors.LIGHT_BORDER};
            }}
            QTableWidget::item {{
                padding: 10px 12px;
                border-bottom: 1px solid {Colors.LIGHT_BORDER}50;
            }}
            QTableWidget::item:selected {{
                background: {Colors.PRIMARY}15;
                color: {Colors.PRIMARY};
            }}
            QHeaderView::section {{
                background: {Colors.LIGHT_BG};
                color: {Colors.LIGHT_TEXT};
                padding: 12px;
                border: none;
                border-bottom: 2px solid {Colors.PRIMARY};
                font-weight: bold;
                font-size: 12px;
            }}
        """)
        
    def _update_status_card(self, total: float, count: int):
        """Update the sales performance status card."""
        if count > 20:
            status_icon = "🔥"
            status_text = "أداء ممتاز"
            status_color = Colors.SUCCESS
        elif count > 10:
            status_icon = "📈"
            status_text = "أداء جيد"
            status_color = Colors.INFO
        elif count > 0:
            status_icon = "📊"
            status_text = "أداء متوسط"
            status_color = Colors.WARNING
        else:
            status_icon = "📉"
            status_text = "لا توجد مبيعات"
            status_color = Colors.DANGER
        
        bg_color = f"{status_color}15"
        
        self.status_card.setStyleSheet(f"""
            QFrame#status_card {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {bg_color}, stop:1 {status_color}08);
                border: 2px solid {status_color}40;
                border-radius: 16px;
            }}
        """)
        
        # Clear existing layout
        if self.status_card.layout():
            while self.status_card.layout().count():
                item = self.status_card.layout().takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
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
        
        desc_lbl = QLabel("مستوى الأداء")
        desc_lbl.setFont(QFont(Fonts.FAMILY_AR, 10))
        desc_lbl.setAlignment(Qt.AlignCenter)
        desc_lbl.setStyleSheet(f"color: {Colors.LIGHT_TEXT_SECONDARY}; background: transparent;")
        layout.addWidget(desc_lbl)

    @handle_ui_error
    def refresh(self):
        start_date = self.from_date.date().toString('yyyy-MM-dd')
        end_date = self.to_date.date().toString('yyyy-MM-dd')
        group_by = self.group_by.currentData()
        self.report_data = api.get_sales_report(start_date, end_date, group_by) or {}
        self._update_ui()

    def _update_ui(self):
        data = self.report_data or {}
        summary = data.get('summary', {})

        # Extract values
        total = float(summary.get('total_usd', summary.get('total', 0)) or 0)
        count = int(summary.get('count', 0) or 0)
        avg = float(summary.get('average_usd', summary.get('average', 0)) or 0)

        # Update metric cards
        self.total_sales_card.update_value(config.format_usd(total))
        self.invoice_count_card.update_value(f"{count:,}")
        self.avg_sale_card.update_value(config.format_usd(avg))
        
        # Update status card
        self._update_status_card(total, count)

        # Update tables
        self._update_customers_table(data)
        self._update_products_table(data)
        self._update_trend_table(data)

    def _update_customers_table(self, data: Dict):
        """Update top customers table."""
        customers = data.get('top_customers', [])
        self.customers_table.setRowCount(len(customers))
        
        # Find max for percentage calculation
        max_total = max([float(c.get('total_usd', c.get('total', 0)) or 0) for c in customers], default=1)
        
        for r, cust in enumerate(customers):
            name = cust.get('customer__name', '') or 'غير محدد'
            count = int(cust.get('count', 0) or 0)
            total = float(cust.get('total_usd', cust.get('total', 0)) or 0)
            
            # Rank with medal
            rank = r + 1
            if rank == 1:
                rank_text = "🥇 1"
            elif rank == 2:
                rank_text = "🥈 2"
            elif rank == 3:
                rank_text = "🥉 3"
            else:
                rank_text = f"   {rank}"
            
            rank_item = QTableWidgetItem(rank_text)
            rank_item.setTextAlignment(Qt.AlignCenter)
            rank_item.setFont(QFont(Fonts.FAMILY_AR, 12, QFont.Bold))
            self.customers_table.setItem(r, 0, rank_item)
            
            # Customer name
            name_item = QTableWidgetItem(str(name))
            name_item.setFont(QFont(Fonts.FAMILY_AR, 11, QFont.Medium))
            self.customers_table.setItem(r, 1, name_item)
            
            # Invoice count
            count_item = QTableWidgetItem(f"{count:,}")
            count_item.setTextAlignment(Qt.AlignCenter)
            count_item.setForeground(QBrush(QColor(Colors.INFO)))
            self.customers_table.setItem(r, 2, count_item)
            
            # Total
            total_item = QTableWidgetItem(config.format_usd(total))
            total_item.setTextAlignment(Qt.AlignCenter)
            total_item.setFont(QFont(Fonts.FAMILY_AR, 11, QFont.Bold))
            total_item.setForeground(QBrush(QColor(Colors.SUCCESS)))
            self.customers_table.setItem(r, 3, total_item)
            
            # Status based on percentage
            pct = (total / max_total * 100) if max_total > 0 else 0
            if pct >= 50:
                status = "⭐ VIP"
            elif pct >= 25:
                status = "🔵 مميز"
            else:
                status = "🟢 عادي"
            status_item = QTableWidgetItem(status)
            status_item.setTextAlignment(Qt.AlignCenter)
            self.customers_table.setItem(r, 4, status_item)

    def _update_products_table(self, data: Dict):
        """Update top products table."""
        products = data.get('top_products', [])
        self.products_table.setRowCount(len(products))
        
        # Find max for percentage calculation
        max_value = max([float(p.get('total_value', 0) or 0) for p in products], default=1)
        
        for r, prod in enumerate(products):
            name = prod.get('product__name', '') or 'غير محدد'
            qty = float(prod.get('total_quantity', 0) or 0)
            value = float(prod.get('total_value', 0) or 0)
            
            # Rank with medal
            rank = r + 1
            if rank == 1:
                rank_text = "🥇 1"
            elif rank == 2:
                rank_text = "🥈 2"
            elif rank == 3:
                rank_text = "🥉 3"
            else:
                rank_text = f"   {rank}"
            
            rank_item = QTableWidgetItem(rank_text)
            rank_item.setTextAlignment(Qt.AlignCenter)
            rank_item.setFont(QFont(Fonts.FAMILY_AR, 12, QFont.Bold))
            self.products_table.setItem(r, 0, rank_item)
            
            # Product name
            name_item = QTableWidgetItem(str(name))
            name_item.setFont(QFont(Fonts.FAMILY_AR, 11, QFont.Medium))
            self.products_table.setItem(r, 1, name_item)
            
            # Quantity
            qty_item = QTableWidgetItem(f"{qty:,.0f}")
            qty_item.setTextAlignment(Qt.AlignCenter)
            qty_item.setForeground(QBrush(QColor(Colors.INFO)))
            self.products_table.setItem(r, 2, qty_item)
            
            # Total value
            value_item = QTableWidgetItem(f"{value:,.2f}")
            value_item.setTextAlignment(Qt.AlignCenter)
            value_item.setFont(QFont(Fonts.FAMILY_AR, 11, QFont.Bold))
            value_item.setForeground(QBrush(QColor(Colors.SUCCESS)))
            self.products_table.setItem(r, 3, value_item)
            
            # Performance indicator
            pct = (value / max_value * 100) if max_value > 0 else 0
            if pct >= 50:
                perf = "🔥 الأفضل"
            elif pct >= 25:
                perf = "📈 جيد"
            else:
                perf = "📊 عادي"
            perf_item = QTableWidgetItem(perf)
            perf_item.setTextAlignment(Qt.AlignCenter)
            self.products_table.setItem(r, 4, perf_item)

    def _update_trend_table(self, data: Dict):
        """Update sales trend table."""
        trend = data.get('trend', [])
        self.trend_table.setRowCount(len(trend))
        
        # Calculate total for percentage
        total_sales = sum([float(t.get('total_usd', t.get('total', 0)) or 0) for t in trend])
        
        for r, item in enumerate(trend):
            period = item.get('period', '')
            if period:
                if isinstance(period, str):
                    period_str = period
                else:
                    period_str = str(period)
            else:
                period_str = 'غير محدد'
            
            count = int(item.get('count', 0) or 0)
            total = float(item.get('total_usd', item.get('total', 0)) or 0)
            pct = (total / total_sales * 100) if total_sales > 0 else 0
            
            # Period
            period_item = QTableWidgetItem(period_str)
            period_item.setFont(QFont(Fonts.FAMILY_AR, 11, QFont.Medium))
            self.trend_table.setItem(r, 0, period_item)
            
            # Count
            count_item = QTableWidgetItem(f"{count:,}")
            count_item.setTextAlignment(Qt.AlignCenter)
            count_item.setForeground(QBrush(QColor(Colors.INFO)))
            self.trend_table.setItem(r, 1, count_item)
            
            # Total
            total_item = QTableWidgetItem(config.format_usd(total))
            total_item.setTextAlignment(Qt.AlignCenter)
            total_item.setFont(QFont(Fonts.FAMILY_AR, 11, QFont.Bold))
            total_item.setForeground(QBrush(QColor(Colors.SUCCESS)))
            self.trend_table.setItem(r, 2, total_item)
            
            # Percentage with color coding
            pct_item = QTableWidgetItem(f"{pct:.1f}%")
            pct_item.setTextAlignment(Qt.AlignCenter)
            if pct >= 20:
                pct_item.setForeground(QBrush(QColor(Colors.SUCCESS)))
            elif pct >= 10:
                pct_item.setForeground(QBrush(QColor(Colors.WARNING)))
            else:
                pct_item.setForeground(QBrush(QColor(Colors.LIGHT_TEXT_SECONDARY)))
            self.trend_table.setItem(r, 3, pct_item)

    def _build_export_rows(self) -> List[Dict]:
        """Build rows for export."""
        data = self.report_data or {}
        export_rows: List[Dict] = []

        # Add top customers
        for i, cust in enumerate(data.get('top_customers', [])):
            export_rows.append({
                'section': 'أفضل العملاء',
                'rank': i + 1,
                'name': cust.get('customer__name', ''),
                'count': cust.get('count', 0),
                'total': float(cust.get('total_usd', cust.get('total', 0)) or 0),
            })

        # Add top products
        for i, prod in enumerate(data.get('top_products', [])):
            export_rows.append({
                'section': 'أفضل المنتجات',
                'rank': i + 1,
                'name': prod.get('product__name', ''),
                'count': prod.get('total_quantity', 0),
                'total': float(prod.get('total_value', 0) or 0),
            })

        return export_rows

    def _export_excel(self):
        """Export report to Excel."""
        if not self.report_data:
            MessageDialog.warning(self, "تنبيه", "لا توجد بيانات للتصدير")
            return

        try:
            start_date = self.from_date.date().toString('yyyy-MM-dd')
            end_date = self.to_date.date().toString('yyyy-MM-dd')
            summary = self.report_data.get('summary', {})

            summary_data = {
                'الفترة': f"{start_date} → {end_date}",
                'إجمالي المبيعات': config.format_usd(float(summary.get('total_usd', summary.get('total', 0)) or 0)),
                'عدد الفواتير': summary.get('count', 0),
                'متوسط الفاتورة': config.format_usd(float(summary.get('average_usd', summary.get('average', 0)) or 0)),
            }

            rows = self._build_export_rows()
            if not rows:
                MessageDialog.warning(self, "تنبيه", "لا توجد بيانات للتصدير")
                return

            columns = [
                ('section', 'القسم'),
                ('rank', 'الترتيب'),
                ('name', 'الاسم'),
                ('count', 'العدد/الكمية'),
                ('total', 'الإجمالي'),
            ]

            filename = f"تقرير_المبيعات_{datetime.now().strftime('%Y%m%d')}.xlsx"
            ok = ExportService.export_to_excel(
                data=rows,
                columns=columns,
                filename=filename,
                title="تقرير المبيعات",
                parent=self,
                summary=summary_data
            )
            if ok:
                MessageDialog.info(self, "نجاح", "تم التصدير بنجاح ✅")
        except ExportError as e:
            MessageDialog.error(self, "خطأ", e.message)
        except Exception as e:
            MessageDialog.error(self, "خطأ", f"فشل التصدير: {str(e)}")

    def _export_pdf(self):
        """Export report to PDF."""
        if not self.report_data:
            MessageDialog.warning(self, "تنبيه", "لا توجد بيانات للتصدير")
            return

        try:
            start_date = self.from_date.date().toString('yyyy-MM-dd')
            end_date = self.to_date.date().toString('yyyy-MM-dd')
            summary = self.report_data.get('summary', {})

            summary_data = {
                'الفترة': f"{start_date} → {end_date}",
                'إجمالي المبيعات': config.format_usd(float(summary.get('total_usd', summary.get('total', 0)) or 0)),
                'عدد الفواتير': summary.get('count', 0),
                'متوسط الفاتورة': config.format_usd(float(summary.get('average_usd', summary.get('average', 0)) or 0)),
            }

            rows = self._build_export_rows()
            if not rows:
                MessageDialog.warning(self, "تنبيه", "لا توجد بيانات للتصدير")
                return

            columns = [
                ('section', 'القسم'),
                ('rank', 'الترتيب'),
                ('name', 'الاسم'),
                ('count', 'العدد/الكمية'),
                ('total', 'الإجمالي'),
            ]

            filename = f"تقرير_المبيعات_{datetime.now().strftime('%Y%m%d')}.pdf"
            ok = ExportService.export_to_pdf(
                data=rows,
                columns=columns,
                filename=filename,
                title="تقرير المبيعات",
                parent=self,
                summary=summary_data,
                date_range=(start_date, end_date)
            )
            if ok:
                MessageDialog.info(self, "نجاح", "تم التصدير بنجاح ✅")
        except ExportError as e:
            MessageDialog.error(self, "خطأ", e.message)
        except Exception as e:
            MessageDialog.error(self, "خطأ", f"فشل التصدير: {str(e)}")
