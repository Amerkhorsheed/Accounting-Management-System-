"""Customer Report View - تقرير العملاء - Professional Modern Design"""

from datetime import datetime
from typing import Dict, List

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QDateEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QFrame, QGridLayout,
    QScrollArea, QGraphicsDropShadowEffect, QProgressBar
)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QFont, QBrush, QColor

from ...config import Colors, Fonts, config
from ...widgets.cards import Card
from ...widgets.dialogs import MessageDialog
from ...services.api import api, ApiException
from ...services.export import ExportService, ExportError
from ...utils.error_handler import handle_ui_error


class CustomerMetricCard(QFrame):
    """Modern metric card with gradient accent for customer data."""
    
    def __init__(self, title: str, value: str, icon: str, color: str,
                 subtitle: str = "", parent=None):
        super().__init__(parent)
        self.accent_color = color
        self.setObjectName("customer_metric_card")
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
            QFrame#customer_metric_card {{
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
        
    def update_value(self, value: str):
        self.value_label.setText(value)


class ActivityIndicator(QFrame):
    """Visual activity indicator with progress bar."""
    
    def __init__(self, title: str, active: int, total: int, parent=None):
        super().__init__(parent)
        self.setObjectName("activity_indicator")
        self.setup_ui(title, active, total)
        
    def setup_ui(self, title: str, active: int, total: int):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)
        
        # Header with title and value
        header = QHBoxLayout()
        title_label = QLabel(title)
        title_label.setFont(QFont(Fonts.FAMILY_AR, 12, QFont.Medium))
        header.addWidget(title_label)
        header.addStretch()
        
        pct = (active / total * 100) if total > 0 else 0
        self.value_label = QLabel(f"{active} / {total} ({pct:.0f}%)")
        self.value_label.setFont(QFont(Fonts.FAMILY_AR, 12, QFont.Bold))
        color = Colors.SUCCESS if pct >= 50 else Colors.WARNING if pct >= 25 else Colors.DANGER
        self.value_label.setStyleSheet(f"color: {color}; background: transparent;")
        header.addWidget(self.value_label)
        layout.addLayout(header)
        
        # Progress bar
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(int(pct))
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(10)
        self.progress.setStyleSheet(f"""
            QProgressBar {{
                background: {Colors.LIGHT_BORDER};
                border: none;
                border-radius: 5px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {color}, stop:1 {color}aa);
                border-radius: 5px;
            }}
        """)
        layout.addWidget(self.progress)
        
        self.setStyleSheet(f"""
            QFrame#activity_indicator {{
                background: {Colors.LIGHT_CARD};
                border: 1px solid {Colors.LIGHT_BORDER};
                border-radius: 12px;
            }}
        """)
        
    def update_value(self, active: int, total: int):
        pct = (active / total * 100) if total > 0 else 0
        self.value_label.setText(f"{active} / {total} ({pct:.0f}%)")
        self.progress.setValue(int(pct))
        color = Colors.SUCCESS if pct >= 50 else Colors.WARNING if pct >= 25 else Colors.DANGER
        self.value_label.setStyleSheet(f"color: {color}; background: transparent;")
        self.progress.setStyleSheet(f"""
            QProgressBar {{
                background: {Colors.LIGHT_BORDER};
                border: none;
                border-radius: 5px;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {color}, stop:1 {color}aa);
                border-radius: 5px;
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


class CustomerReportView(QWidget):
    """Professional Customer report view with modern UI/UX."""

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
                    stop:0 {Colors.INFO}, stop:1 #06B6D4);
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
        title = QLabel("👥 تقرير العملاء")
        title.setFont(QFont(Fonts.FAMILY_AR, 22, QFont.Bold))
        title.setStyleSheet("color: white; background: transparent;")
        title_section.addWidget(title)
        
        subtitle = QLabel("تحليل شامل لبيانات العملاء والمبيعات والمستحقات")
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
        self.from_date.setDate(QDate.currentDate().addMonths(-3))
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
                background: {Colors.INFO};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 24px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background: #0284C7; }}
        """)
        apply_btn.clicked.connect(self.refresh)
        filters_layout.addWidget(apply_btn)
        filters_layout.addStretch()
        
        layout.addWidget(filters_card)

        # ═══════════════════════════════════════════════════════════
        # KEY METRICS SECTION
        # ═══════════════════════════════════════════════════════════
        layout.addWidget(SectionHeader("📊 ملخص العملاء", ""))
        
        metrics_grid = QGridLayout()
        metrics_grid.setSpacing(16)
        
        self.total_customers_card = CustomerMetricCard(
            "إجمالي العملاء", "0", "👥", Colors.INFO,
            "Total Customers"
        )
        metrics_grid.addWidget(self.total_customers_card, 0, 0)
        
        self.active_customers_card = CustomerMetricCard(
            "العملاء النشطين", "0", "✅", Colors.SUCCESS,
            "Active Customers"
        )
        metrics_grid.addWidget(self.active_customers_card, 0, 1)
        
        self.total_receivables_card = CustomerMetricCard(
            "إجمالي المستحقات", config.format_usd(0), "💰", Colors.WARNING,
            "Total Receivables"
        )
        metrics_grid.addWidget(self.total_receivables_card, 0, 2)
        
        # Status card
        self.status_card = QFrame()
        self.status_card.setObjectName("status_card")
        self._update_status_card(0, 0)
        metrics_grid.addWidget(self.status_card, 0, 3)
        
        layout.addLayout(metrics_grid)

        # ═══════════════════════════════════════════════════════════
        # ACTIVITY INDICATOR
        # ═══════════════════════════════════════════════════════════
        layout.addWidget(SectionHeader("📈 نسبة نشاط العملاء", ""))
        
        self.activity_indicator = ActivityIndicator("العملاء النشطين من إجمالي العملاء", 0, 1)
        layout.addWidget(self.activity_indicator)

        # ═══════════════════════════════════════════════════════════
        # TOP CUSTOMERS TABLE
        # ═══════════════════════════════════════════════════════════
        layout.addWidget(SectionHeader("🏆 أفضل العملاء", ""))
        
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
        
        cust_note = QLabel("💡 أفضل 20 عميل حسب إجمالي المشتريات خلال الفترة المحددة")
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
        self.customers_table.setColumnCount(7)
        self.customers_table.setHorizontalHeaderLabels([
            'الترتيب', 'الكود', 'اسم العميل', 'عدد الفواتير', 
            'إجمالي المشتريات', 'الرصيد المستحق', 'الحالة'
        ])
        self.customers_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.customers_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.customers_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.customers_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.customers_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.customers_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.customers_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.customers_table.verticalHeader().setVisible(False)
        self.customers_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.customers_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.customers_table.setAlternatingRowColors(True)
        self.customers_table.setMinimumHeight(400)
        self._style_table(self.customers_table)
        customers_layout.addWidget(self.customers_table)
        
        layout.addWidget(customers_card, 1)
        
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
                background: {Colors.INFO}15;
                color: {Colors.INFO};
            }}
            QHeaderView::section {{
                background: {Colors.LIGHT_BG};
                color: {Colors.LIGHT_TEXT};
                padding: 12px;
                border: none;
                border-bottom: 2px solid {Colors.INFO};
                font-weight: bold;
                font-size: 12px;
            }}
        """)
        
    def _update_status_card(self, active: int, total: int):
        """Update the customer activity status card."""
        pct = (active / total * 100) if total > 0 else 0
        
        if pct >= 60:
            status_icon = "🌟"
            status_text = "نشاط ممتاز"
            status_color = Colors.SUCCESS
        elif pct >= 40:
            status_icon = "📈"
            status_text = "نشاط جيد"
            status_color = Colors.INFO
        elif pct >= 20:
            status_icon = "📊"
            status_text = "نشاط متوسط"
            status_color = Colors.WARNING
        else:
            status_icon = "📉"
            status_text = "نشاط ضعيف"
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
        
        desc_lbl = QLabel("مستوى النشاط")
        desc_lbl.setFont(QFont(Fonts.FAMILY_AR, 10))
        desc_lbl.setAlignment(Qt.AlignCenter)
        desc_lbl.setStyleSheet(f"color: {Colors.LIGHT_TEXT_SECONDARY}; background: transparent;")
        layout.addWidget(desc_lbl)

    @handle_ui_error
    def refresh(self):
        start_date = self.from_date.date().toString('yyyy-MM-dd')
        end_date = self.to_date.date().toString('yyyy-MM-dd')
        self.report_data = api.get_customer_report(start_date, end_date) or {}
        self._update_ui()

    def _update_ui(self):
        data = self.report_data or {}
        summary = data.get('summary', {})

        # Extract values
        total_customers = int(summary.get('total_customers', 0) or 0)
        active_customers = int(summary.get('active_customers', 0) or 0)
        total_receivables = float(summary.get('total_receivables_usd', 
                                              summary.get('total_receivables', 0)) or 0)

        # Update metric cards
        self.total_customers_card.update_value(f"{total_customers:,}")
        self.active_customers_card.update_value(f"{active_customers:,}")
        self.total_receivables_card.update_value(config.format_usd(total_receivables))
        
        # Update status card
        self._update_status_card(active_customers, total_customers)
        
        # Update activity indicator
        self.activity_indicator.update_value(active_customers, total_customers)

        # Update customers table
        self._update_customers_table(data)

    def _update_customers_table(self, data: Dict):
        """Update top customers table."""
        customers = data.get('top_customers', [])
        self.customers_table.setRowCount(len(customers))
        
        # Find max for percentage calculation
        max_total = max([float(c.get('invoices_total_usd', c.get('invoices_total', 0)) or 0) 
                        for c in customers], default=1)
        
        for r, cust in enumerate(customers):
            code = cust.get('code', '') or '-'
            name = cust.get('name', '') or 'غير محدد'
            invoices_count = int(cust.get('invoices_count', 0) or 0)
            invoices_total = float(cust.get('invoices_total_usd', 
                                           cust.get('invoices_total', 0)) or 0)
            balance = float(cust.get('balance_usd', cust.get('balance', 0)) or 0)
            
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
            
            # Code
            code_item = QTableWidgetItem(str(code))
            code_item.setTextAlignment(Qt.AlignCenter)
            code_item.setFont(QFont(Fonts.FAMILY_AR, 11))
            code_item.setForeground(QBrush(QColor(Colors.LIGHT_TEXT_SECONDARY)))
            self.customers_table.setItem(r, 1, code_item)
            
            # Customer name
            name_item = QTableWidgetItem(str(name))
            name_item.setFont(QFont(Fonts.FAMILY_AR, 11, QFont.Medium))
            self.customers_table.setItem(r, 2, name_item)
            
            # Invoice count
            count_item = QTableWidgetItem(f"{invoices_count:,}")
            count_item.setTextAlignment(Qt.AlignCenter)
            count_item.setForeground(QBrush(QColor(Colors.INFO)))
            self.customers_table.setItem(r, 3, count_item)
            
            # Total purchases
            total_item = QTableWidgetItem(config.format_usd(invoices_total))
            total_item.setTextAlignment(Qt.AlignCenter)
            total_item.setFont(QFont(Fonts.FAMILY_AR, 11, QFont.Bold))
            total_item.setForeground(QBrush(QColor(Colors.SUCCESS)))
            self.customers_table.setItem(r, 4, total_item)
            
            # Balance
            balance_item = QTableWidgetItem(config.format_usd(balance))
            balance_item.setTextAlignment(Qt.AlignCenter)
            balance_item.setFont(QFont(Fonts.FAMILY_AR, 11, QFont.Bold))
            if balance > 0:
                balance_item.setForeground(QBrush(QColor(Colors.DANGER)))
            else:
                balance_item.setForeground(QBrush(QColor(Colors.SUCCESS)))
            self.customers_table.setItem(r, 5, balance_item)
            
            # Status based on activity and balance
            pct = (invoices_total / max_total * 100) if max_total > 0 else 0
            if pct >= 30:
                status = "⭐ VIP"
            elif pct >= 15:
                status = "🔵 مميز"
            elif invoices_count > 0:
                status = "🟢 نشط"
            else:
                status = "⚪ غير نشط"
            status_item = QTableWidgetItem(status)
            status_item.setTextAlignment(Qt.AlignCenter)
            self.customers_table.setItem(r, 6, status_item)

    def _build_export_rows(self) -> List[Dict]:
        """Build rows for export."""
        data = self.report_data or {}
        export_rows: List[Dict] = []

        for i, cust in enumerate(data.get('top_customers', [])):
            export_rows.append({
                'rank': i + 1,
                'code': cust.get('code', ''),
                'name': cust.get('name', ''),
                'invoices_count': cust.get('invoices_count', 0),
                'invoices_total': float(cust.get('invoices_total_usd', 
                                                 cust.get('invoices_total', 0)) or 0),
                'balance': float(cust.get('balance_usd', cust.get('balance', 0)) or 0),
            })

        return export_rows

    def _export_excel(self):
        """Export report to Excel."""
        if not self.report_data.get('top_customers'):
            MessageDialog.warning(self, "تنبيه", "لا توجد بيانات للتصدير")
            return

        try:
            start_date = self.from_date.date().toString('yyyy-MM-dd')
            end_date = self.to_date.date().toString('yyyy-MM-dd')
            summary = self.report_data.get('summary', {})

            summary_data = {
                'الفترة': f"{start_date} → {end_date}",
                'إجمالي العملاء': summary.get('total_customers', 0),
                'العملاء النشطين': summary.get('active_customers', 0),
                'إجمالي المستحقات': config.format_usd(
                    float(summary.get('total_receivables_usd', 
                                     summary.get('total_receivables', 0)) or 0)
                ),
            }

            rows = self._build_export_rows()
            if not rows:
                MessageDialog.warning(self, "تنبيه", "لا توجد بيانات للتصدير")
                return

            columns = [
                ('rank', 'الترتيب'),
                ('code', 'الكود'),
                ('name', 'اسم العميل'),
                ('invoices_count', 'عدد الفواتير'),
                ('invoices_total', 'إجمالي المشتريات'),
                ('balance', 'الرصيد المستحق'),
            ]

            filename = f"تقرير_العملاء_{datetime.now().strftime('%Y%m%d')}.xlsx"
            ok = ExportService.export_to_excel(
                data=rows,
                columns=columns,
                filename=filename,
                title="تقرير العملاء",
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
        if not self.report_data.get('top_customers'):
            MessageDialog.warning(self, "تنبيه", "لا توجد بيانات للتصدير")
            return

        try:
            start_date = self.from_date.date().toString('yyyy-MM-dd')
            end_date = self.to_date.date().toString('yyyy-MM-dd')
            summary = self.report_data.get('summary', {})

            summary_data = {
                'الفترة': f"{start_date} → {end_date}",
                'إجمالي العملاء': summary.get('total_customers', 0),
                'العملاء النشطين': summary.get('active_customers', 0),
                'إجمالي المستحقات': config.format_usd(
                    float(summary.get('total_receivables_usd', 
                                     summary.get('total_receivables', 0)) or 0)
                ),
            }

            rows = self._build_export_rows()
            if not rows:
                MessageDialog.warning(self, "تنبيه", "لا توجد بيانات للتصدير")
                return

            columns = [
                ('rank', 'الترتيب'),
                ('code', 'الكود'),
                ('name', 'اسم العميل'),
                ('invoices_count', 'عدد الفواتير'),
                ('invoices_total', 'إجمالي المشتريات'),
                ('balance', 'الرصيد المستحق'),
            ]

            filename = f"تقرير_العملاء_{datetime.now().strftime('%Y%m%d')}.pdf"
            ok = ExportService.export_to_pdf(
                data=rows,
                columns=columns,
                filename=filename,
                title="تقرير العملاء",
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
