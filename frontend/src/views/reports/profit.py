"""Profit Report View - تقرير الأرباح - Professional Modern Design"""

from datetime import datetime
from typing import Dict, List

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QDateEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QFrame, QGridLayout,
    QScrollArea, QSizePolicy, QGraphicsDropShadowEffect,
    QProgressBar
)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QFont, QBrush, QColor, QPainter, QPen

from ...config import Colors, Fonts, config
from ...widgets.cards import Card
from ...widgets.dialogs import MessageDialog
from ...services.api import api, ApiException
from ...services.export import ExportService, ExportError
from ...utils.error_handler import handle_ui_error


class ProfitMetricCard(QFrame):
    """Modern metric card with gradient accent and trend indicator."""
    
    def __init__(self, title: str, value: str, icon: str, color: str, 
                 subtitle: str = "", is_negative: bool = False, parent=None):
        super().__init__(parent)
        self.accent_color = color
        self.is_negative = is_negative
        self.setObjectName("metric_card")
        self.setup_ui(title, value, icon, subtitle)
        self._apply_style()
        
    def setup_ui(self, title: str, value: str, icon: str, subtitle: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(8)
        
        # Top row with icon
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
        layout.addLayout(top)
        
        # Value - large and prominent
        self.value_label = QLabel(value)
        self.value_label.setFont(QFont(Fonts.FAMILY_AR, 26, QFont.Bold))
        color_style = Colors.DANGER if self.is_negative else self.accent_color
        self.value_label.setStyleSheet(f"color: {color_style}; background: transparent;")
        layout.addWidget(self.value_label)
        
        # Title
        title_label = QLabel(title)
        title_label.setFont(QFont(Fonts.FAMILY_AR, 12, QFont.Medium))
        title_label.setStyleSheet(f"color: {Colors.LIGHT_TEXT_SECONDARY}; background: transparent;")
        layout.addWidget(title_label)
        
        # Subtitle if provided
        if subtitle:
            sub_label = QLabel(subtitle)
            sub_label.setFont(QFont(Fonts.FAMILY_AR, 10))
            sub_label.setStyleSheet(f"color: {Colors.LIGHT_TEXT_SECONDARY}80; background: transparent;")
            layout.addWidget(sub_label)
    
    def _apply_style(self):
        self.setStyleSheet(f"""
            QFrame#metric_card {{
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
        
    def update_value(self, value: str, is_negative: bool = False):
        self.is_negative = is_negative
        self.value_label.setText(value)
        color_style = Colors.DANGER if is_negative else self.accent_color
        self.value_label.setStyleSheet(f"color: {color_style}; background: transparent;")


class MarginIndicator(QFrame):
    """Visual margin indicator with progress bar."""
    
    def __init__(self, title: str, value: float, parent=None):
        super().__init__(parent)
        self.setObjectName("margin_indicator")
        self.setup_ui(title, value)
        
    def setup_ui(self, title: str, value: float):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)
        
        # Header with title and value
        header = QHBoxLayout()
        title_label = QLabel(title)
        title_label.setFont(QFont(Fonts.FAMILY_AR, 12, QFont.Medium))
        header.addWidget(title_label)
        header.addStretch()
        
        self.value_label = QLabel(f"{value:.1f}%")
        self.value_label.setFont(QFont(Fonts.FAMILY_AR, 14, QFont.Bold))
        color = Colors.SUCCESS if value >= 0 else Colors.DANGER
        self.value_label.setStyleSheet(f"color: {color}; background: transparent;")
        header.addWidget(self.value_label)
        layout.addLayout(header)
        
        # Progress bar
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(max(0, min(100, int(abs(value)))))
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(8)
        bar_color = Colors.SUCCESS if value >= 0 else Colors.DANGER
        self.progress.setStyleSheet(f"""
            QProgressBar {{
                background: {Colors.LIGHT_BORDER};
                border: none;
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background: {bar_color};
                border-radius: 4px;
            }}
        """)
        layout.addWidget(self.progress)
        
        self.setStyleSheet(f"""
            QFrame#margin_indicator {{
                background: {Colors.LIGHT_CARD};
                border: 1px solid {Colors.LIGHT_BORDER};
                border-radius: 12px;
            }}
        """)
        
    def update_value(self, value: float):
        self.value_label.setText(f"{value:.1f}%")
        color = Colors.SUCCESS if value >= 0 else Colors.DANGER
        self.value_label.setStyleSheet(f"color: {color}; background: transparent;")
        self.progress.setValue(max(0, min(100, int(abs(value)))))
        bar_color = Colors.SUCCESS if value >= 0 else Colors.DANGER
        self.progress.setStyleSheet(f"""
            QProgressBar {{
                background: {Colors.LIGHT_BORDER};
                border: none;
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background: {bar_color};
                border-radius: 4px;
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


class ProfitReportView(QWidget):
    """Professional Profit report view with modern UI/UX."""

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
                    stop:0 {Colors.PRIMARY}, stop:1 {Colors.PRIMARY_LIGHT});
                border-radius: 16px;
                padding: 20px;
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
        title = QLabel("📊 تقرير الأرباح والخسائر")
        title.setFont(QFont(Fonts.FAMILY_AR, 22, QFont.Bold))
        title.setStyleSheet("color: white; background: transparent;")
        title_section.addWidget(title)
        
        subtitle = QLabel("تحليل شامل للإيرادات والمصروفات والربحية")
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
        layout.addWidget(SectionHeader("📈 المؤشرات الرئيسية", ""))
        
        metrics_grid = QGridLayout()
        metrics_grid.setSpacing(16)
        
        self.revenue_card = ProfitMetricCard(
            "إجمالي الإيرادات", config.format_usd(0), "💰", Colors.PRIMARY,
            "Revenue - المبيعات"
        )
        metrics_grid.addWidget(self.revenue_card, 0, 0)
        
        self.cogs_card = ProfitMetricCard(
            "تكلفة البضاعة المباعة", config.format_usd(0), "📦", Colors.WARNING,
            "Cost of Goods Sold"
        )
        metrics_grid.addWidget(self.cogs_card, 0, 1)
        
        self.gross_profit_card = ProfitMetricCard(
            "إجمالي الربح", config.format_usd(0), "📊", Colors.SUCCESS,
            "Gross Profit"
        )
        metrics_grid.addWidget(self.gross_profit_card, 0, 2)
        
        self.expenses_card = ProfitMetricCard(
            "إجمالي المصروفات", config.format_usd(0), "💸", Colors.DANGER,
            "Operating Expenses"
        )
        metrics_grid.addWidget(self.expenses_card, 1, 0)
        
        self.net_profit_card = ProfitMetricCard(
            "صافي الربح", config.format_usd(0), "✨", Colors.SUCCESS,
            "Net Profit - الربح الصافي"
        )
        metrics_grid.addWidget(self.net_profit_card, 1, 1)
        
        # Profit status card
        self.status_card = QFrame()
        self.status_card.setObjectName("status_card")
        self._update_status_card(0)
        metrics_grid.addWidget(self.status_card, 1, 2)
        
        layout.addLayout(metrics_grid)

        # ═══════════════════════════════════════════════════════════
        # MARGINS SECTION
        # ═══════════════════════════════════════════════════════════
        layout.addWidget(SectionHeader("📉 هوامش الربحية", ""))
        
        margins_layout = QHBoxLayout()
        margins_layout.setSpacing(16)
        
        self.gross_margin_indicator = MarginIndicator("هامش إجمالي الربح (Gross Margin)", 0)
        margins_layout.addWidget(self.gross_margin_indicator)
        
        self.net_margin_indicator = MarginIndicator("هامش صافي الربح (Net Margin)", 0)
        margins_layout.addWidget(self.net_margin_indicator)
        
        layout.addLayout(margins_layout)

        # ═══════════════════════════════════════════════════════════
        # EXPENSES BY CATEGORY
        # ═══════════════════════════════════════════════════════════
        layout.addWidget(SectionHeader("💸 تفصيل المصروفات حسب الفئة", ""))
        
        exp_card = QFrame()
        exp_card.setObjectName("table_card")
        exp_card.setStyleSheet(f"""
            QFrame#table_card {{
                background: {Colors.LIGHT_CARD};
                border: 1px solid {Colors.LIGHT_BORDER};
                border-radius: 12px;
            }}
        """)
        exp_layout = QVBoxLayout(exp_card)
        exp_layout.setContentsMargins(20, 16, 20, 16)
        exp_layout.setSpacing(12)
        
        exp_note = QLabel("💡 القيم بالليرة السورية (ل.س) - يتم تحويل الإجمالي إلى العملة المختارة في البطاقات")
        exp_note.setFont(QFont(Fonts.FAMILY_AR, 10))
        exp_note.setStyleSheet(f"""
            color: {Colors.LIGHT_TEXT_SECONDARY};
            background: {Colors.INFO}15;
            padding: 8px 12px;
            border-radius: 6px;
            border-left: 3px solid {Colors.INFO};
        """)
        exp_layout.addWidget(exp_note)
        
        self.expenses_table = QTableWidget()
        self.expenses_table.setColumnCount(4)
        self.expenses_table.setHorizontalHeaderLabels(['الفئة', 'الإجمالي (ل.س)', 'النسبة', 'الحالة'])
        self.expenses_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.expenses_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.expenses_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.expenses_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.expenses_table.verticalHeader().setVisible(False)
        self.expenses_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.expenses_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.expenses_table.setAlternatingRowColors(True)
        self.expenses_table.setMinimumHeight(200)
        self._style_table(self.expenses_table)
        exp_layout.addWidget(self.expenses_table)
        
        layout.addWidget(exp_card)

        # ═══════════════════════════════════════════════════════════
        # PROFIT BY CATEGORY
        # ═══════════════════════════════════════════════════════════
        layout.addWidget(SectionHeader("📊 الربحية حسب فئة المنتج", ""))
        
        cat_card = QFrame()
        cat_card.setObjectName("table_card2")
        cat_card.setStyleSheet(f"""
            QFrame#table_card2 {{
                background: {Colors.LIGHT_CARD};
                border: 1px solid {Colors.LIGHT_BORDER};
                border-radius: 12px;
            }}
        """)
        cat_layout = QVBoxLayout(cat_card)
        cat_layout.setContentsMargins(20, 16, 20, 16)
        cat_layout.setSpacing(12)
        
        cat_note = QLabel("💡 القيم حسب عملة الفواتير الأصلية - قد تختلف عن العملة المعروضة في البطاقات")
        cat_note.setFont(QFont(Fonts.FAMILY_AR, 10))
        cat_note.setStyleSheet(f"""
            color: {Colors.LIGHT_TEXT_SECONDARY};
            background: {Colors.WARNING}15;
            padding: 8px 12px;
            border-radius: 6px;
            border-left: 3px solid {Colors.WARNING};
        """)
        cat_layout.addWidget(cat_note)
        
        self.categories_table = QTableWidget()
        self.categories_table.setColumnCount(6)
        self.categories_table.setHorizontalHeaderLabels([
            'الفئة', 'الإيرادات', 'التكلفة', 'الربح', 'الهامش %', 'الحالة'
        ])
        self.categories_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for i in range(1, 6):
            self.categories_table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)
        self.categories_table.verticalHeader().setVisible(False)
        self.categories_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.categories_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.categories_table.setAlternatingRowColors(True)
        self.categories_table.setMinimumHeight(250)
        self._style_table(self.categories_table)
        cat_layout.addWidget(self.categories_table)
        
        layout.addWidget(cat_card, 1)
        
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
        
    def _update_status_card(self, net_profit: float):
        """Update the profit/loss status card."""
        is_profit = net_profit >= 0
        status_icon = "🎉" if is_profit else "⚠️"
        status_text = "ربح" if is_profit else "خسارة"
        status_color = Colors.SUCCESS if is_profit else Colors.DANGER
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
        status_lbl.setFont(QFont(Fonts.FAMILY_AR, 18, QFont.Bold))
        status_lbl.setAlignment(Qt.AlignCenter)
        status_lbl.setStyleSheet(f"color: {status_color}; background: transparent;")
        layout.addWidget(status_lbl)
        
        desc_lbl = QLabel("الحالة المالية للفترة")
        desc_lbl.setFont(QFont(Fonts.FAMILY_AR, 10))
        desc_lbl.setAlignment(Qt.AlignCenter)
        desc_lbl.setStyleSheet(f"color: {Colors.LIGHT_TEXT_SECONDARY}; background: transparent;")
        layout.addWidget(desc_lbl)

    @handle_ui_error
    def refresh(self):
        start_date = self.from_date.date().toString('yyyy-MM-dd')
        end_date = self.to_date.date().toString('yyyy-MM-dd')
        self.report_data = api.get_profit_report(start_date, end_date) or {}
        self._update_ui()

    def _update_ui(self):
        data = self.report_data or {}

        # Extract values with fallbacks
        revenue_usd = float(data.get('revenue_usd', data.get('revenue', 0)) or 0)
        cogs_usd = float(data.get('cost_of_goods_usd', data.get('cost_of_goods', 0)) or 0)
        gross_usd = float(data.get('gross_profit_usd', data.get('gross_profit', 0)) or 0)
        expenses_usd = float(((data.get('expenses') or {}).get('total_usd', 
                             (data.get('expenses') or {}).get('total', 0))) or 0)
        net_usd = float(data.get('net_profit_usd', data.get('net_profit', 0)) or 0)

        # Update metric cards
        self.revenue_card.update_value(config.format_usd(revenue_usd))
        self.cogs_card.update_value(config.format_usd(cogs_usd))
        self.gross_profit_card.update_value(config.format_usd(gross_usd), gross_usd < 0)
        self.expenses_card.update_value(config.format_usd(expenses_usd))
        self.net_profit_card.update_value(config.format_usd(net_usd), net_usd < 0)
        
        # Update status card
        self._update_status_card(net_usd)

        # Update margins
        gross_margin = float(data.get('gross_margin_usd', data.get('gross_margin', 0)) or 0)
        net_margin = float(data.get('net_margin_usd', data.get('net_margin', 0)) or 0)
        self.gross_margin_indicator.update_value(gross_margin)
        self.net_margin_indicator.update_value(net_margin)

        # Update expenses table
        self._update_expenses_table(data)
        
        # Update categories table
        self._update_categories_table(data)

    def _update_expenses_table(self, data: Dict):
        """Update expenses by category table."""
        exp = data.get('expenses') or {}
        exp_rows = exp.get('by_category') or []
        try:
            total_exp_syp = float(exp.get('total', 0) or 0)
        except Exception:
            total_exp_syp = 0.0

        self.expenses_table.setRowCount(len(exp_rows))
        for r, row in enumerate(exp_rows):
            cat = row.get('category__name', '') or 'بدون فئة'
            total = float(row.get('total', 0) or 0)
            pct = (total / total_exp_syp * 100) if total_exp_syp > 0 else 0

            # Category
            cat_item = QTableWidgetItem(str(cat))
            cat_item.setFont(QFont(Fonts.FAMILY_AR, 11, QFont.Medium))
            self.expenses_table.setItem(r, 0, cat_item)
            
            # Total
            total_item = QTableWidgetItem(f"{total:,.0f}")
            total_item.setTextAlignment(Qt.AlignCenter)
            total_item.setFont(QFont(Fonts.FAMILY_AR, 11))
            self.expenses_table.setItem(r, 1, total_item)
            
            # Percentage with visual bar
            pct_item = QTableWidgetItem(f"{pct:.1f}%")
            pct_item.setTextAlignment(Qt.AlignCenter)
            if pct > 30:
                pct_item.setForeground(QBrush(QColor(Colors.DANGER)))
            elif pct > 15:
                pct_item.setForeground(QBrush(QColor(Colors.WARNING)))
            else:
                pct_item.setForeground(QBrush(QColor(Colors.SUCCESS)))
            self.expenses_table.setItem(r, 2, pct_item)
            
            # Status indicator
            if pct > 30:
                status = "🔴 مرتفع"
            elif pct > 15:
                status = "🟡 متوسط"
            else:
                status = "🟢 منخفض"
            status_item = QTableWidgetItem(status)
            status_item.setTextAlignment(Qt.AlignCenter)
            self.expenses_table.setItem(r, 3, status_item)

    def _update_categories_table(self, data: Dict):
        """Update profit by category table."""
        cat_rows = data.get('profit_by_category') or []
        self.categories_table.setRowCount(len(cat_rows))
        
        for r, row in enumerate(cat_rows):
            category = row.get('category', '') or 'بدون فئة'
            rev = float(row.get('revenue', 0) or 0)
            cost = float(row.get('cost', 0) or 0)
            profit = float(row.get('profit', 0) or 0)
            margin = (profit / rev * 100) if rev > 0 else 0

            # Category
            cat_item = QTableWidgetItem(str(category))
            cat_item.setFont(QFont(Fonts.FAMILY_AR, 11, QFont.Medium))
            self.categories_table.setItem(r, 0, cat_item)
            
            # Revenue
            rev_item = QTableWidgetItem(f"{rev:,.2f}")
            rev_item.setTextAlignment(Qt.AlignCenter)
            rev_item.setForeground(QBrush(QColor(Colors.PRIMARY)))
            self.categories_table.setItem(r, 1, rev_item)
            
            # Cost
            cost_item = QTableWidgetItem(f"{cost:,.2f}")
            cost_item.setTextAlignment(Qt.AlignCenter)
            cost_item.setForeground(QBrush(QColor(Colors.WARNING)))
            self.categories_table.setItem(r, 2, cost_item)
            
            # Profit
            profit_item = QTableWidgetItem(f"{profit:,.2f}")
            profit_item.setTextAlignment(Qt.AlignCenter)
            if profit < 0:
                profit_item.setForeground(QBrush(QColor(Colors.DANGER)))
            else:
                profit_item.setForeground(QBrush(QColor(Colors.SUCCESS)))
            profit_item.setFont(QFont(Fonts.FAMILY_AR, 11, QFont.Bold))
            self.categories_table.setItem(r, 3, profit_item)
            
            # Margin
            margin_item = QTableWidgetItem(f"{margin:.1f}%")
            margin_item.setTextAlignment(Qt.AlignCenter)
            if margin < 0:
                margin_item.setForeground(QBrush(QColor(Colors.DANGER)))
            elif margin < 10:
                margin_item.setForeground(QBrush(QColor(Colors.WARNING)))
            else:
                margin_item.setForeground(QBrush(QColor(Colors.SUCCESS)))
            self.categories_table.setItem(r, 4, margin_item)
            
            # Status
            if profit < 0:
                status = "🔴 خسارة"
            elif margin < 10:
                status = "🟡 ضعيف"
            elif margin < 25:
                status = "🟢 جيد"
            else:
                status = "💎 ممتاز"
            status_item = QTableWidgetItem(status)
            status_item.setTextAlignment(Qt.AlignCenter)
            self.categories_table.setItem(r, 5, status_item)

    def _build_export_rows(self) -> List[Dict]:
        """Build rows for export."""
        data = self.report_data or {}
        export_rows: List[Dict] = []

        for row in (data.get('profit_by_category') or []):
            rev = float(row.get('revenue', 0) or 0)
            profit = float(row.get('profit', 0) or 0)
            export_rows.append({
                'section': 'ربحية حسب الفئة',
                'category': row.get('category', ''),
                'revenue': float(row.get('revenue', 0) or 0),
                'cost': float(row.get('cost', 0) or 0),
                'profit': float(row.get('profit', 0) or 0),
                'margin': (profit / rev * 100) if rev > 0 else 0,
                'expense_total': ''
            })

        exp = data.get('expenses') or {}
        for row in (exp.get('by_category') or []):
            export_rows.append({
                'section': 'مصروفات حسب الفئة',
                'category': row.get('category__name', '') or 'بدون فئة',
                'revenue': '',
                'cost': '',
                'profit': '',
                'margin': '',
                'expense_total': float(row.get('total', 0) or 0)
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

            summary = {
                'الفترة': f"{start_date} → {end_date}",
                'الإيرادات': config.format_usd(float(self.report_data.get('revenue_usd', 0) or 0)),
                'تكلفة البضاعة': config.format_usd(float(self.report_data.get('cost_of_goods_usd', 0) or 0)),
                'إجمالي الربح': config.format_usd(float(self.report_data.get('gross_profit_usd', 0) or 0)),
                'المصروفات': config.format_usd(float(((self.report_data.get('expenses') or {}).get('total_usd', 0)) or 0)),
                'صافي الربح': config.format_usd(float(self.report_data.get('net_profit_usd', 0) or 0)),
            }

            rows = self._build_export_rows()
            if not rows:
                MessageDialog.warning(self, "تنبيه", "لا توجد بيانات للتصدير")
                return

            columns = [
                ('section', 'القسم'),
                ('category', 'الفئة'),
                ('revenue', 'الإيرادات'),
                ('cost', 'التكلفة'),
                ('profit', 'الربح'),
                ('margin', 'الهامش %'),
                ('expense_total', 'إجمالي المصروف'),
            ]

            filename = f"تقرير_الأرباح_{datetime.now().strftime('%Y%m%d')}.xlsx"
            ok = ExportService.export_to_excel(
                data=rows,
                columns=columns,
                filename=filename,
                title="تقرير الأرباح والخسائر",
                parent=self,
                summary=summary
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

            summary = {
                'الفترة': f"{start_date} → {end_date}",
                'الإيرادات': config.format_usd(float(self.report_data.get('revenue_usd', 0) or 0)),
                'تكلفة البضاعة': config.format_usd(float(self.report_data.get('cost_of_goods_usd', 0) or 0)),
                'إجمالي الربح': config.format_usd(float(self.report_data.get('gross_profit_usd', 0) or 0)),
                'المصروفات': config.format_usd(float(((self.report_data.get('expenses') or {}).get('total_usd', 0)) or 0)),
                'صافي الربح': config.format_usd(float(self.report_data.get('net_profit_usd', 0) or 0)),
            }

            rows = self._build_export_rows()
            if not rows:
                MessageDialog.warning(self, "تنبيه", "لا توجد بيانات للتصدير")
                return

            columns = [
                ('section', 'القسم'),
                ('category', 'الفئة'),
                ('revenue', 'الإيرادات'),
                ('cost', 'التكلفة'),
                ('profit', 'الربح'),
                ('margin', 'الهامش %'),
                ('expense_total', 'إجمالي المصروف'),
            ]

            filename = f"تقرير_الأرباح_{datetime.now().strftime('%Y%m%d')}.pdf"
            ok = ExportService.export_to_pdf(
                data=rows,
                columns=columns,
                filename=filename,
                title="تقرير الأرباح والخسائر",
                parent=self,
                summary=summary,
                date_range=(start_date, end_date)
            )
            if ok:
                MessageDialog.info(self, "نجاح", "تم التصدير بنجاح ✅")
        except ExportError as e:
            MessageDialog.error(self, "خطأ", e.message)
        except Exception as e:
            MessageDialog.error(self, "خطأ", f"فشل التصدير: {str(e)}")
