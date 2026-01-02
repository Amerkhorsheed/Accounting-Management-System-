"""Expenses Report View - تقرير المصروفات - Professional Modern Design"""

from typing import List, Dict
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QDateEdit, QComboBox, QAbstractItemView, QProgressBar,
    QGridLayout, QFrame, QScrollArea, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QFont, QColor, QBrush

from ...config import Colors, Fonts, config
from ...widgets.cards import Card
from ...widgets.dialogs import MessageDialog
from ...services.api import api, ApiException
from ...services.export import ExportService, ExportError
from ...utils.error_handler import handle_ui_error


class ExpenseMetricCard(QFrame):
    """Modern metric card with gradient accent for expense data."""
    
    def __init__(self, title: str, value: str, icon: str, color: str,
                 subtitle: str = "", parent=None):
        super().__init__(parent)
        self.accent_color = color
        self.setObjectName("expense_metric_card")
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
            QFrame#expense_metric_card {{
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


class CategoryBar(QFrame):
    """Visual category bar with progress indicator."""
    
    def __init__(self, name: str, amount: float, percentage: float, 
                 count: int, color: str, parent=None):
        super().__init__(parent)
        self.setObjectName("category_bar")
        self.setup_ui(name, amount, percentage, count, color)
        
    def setup_ui(self, name: str, amount: float, percentage: float, 
                 count: int, color: str):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(16)
        
        # Color indicator
        color_dot = QLabel("●")
        color_dot.setFont(QFont(Fonts.FAMILY_AR, 14))
        color_dot.setStyleSheet(f"color: {color}; background: transparent;")
        color_dot.setFixedWidth(20)
        layout.addWidget(color_dot)
        
        # Category name
        name_label = QLabel(name)
        name_label.setFont(QFont(Fonts.FAMILY_AR, 12, QFont.Medium))
        name_label.setMinimumWidth(120)
        name_label.setStyleSheet("background: transparent;")
        layout.addWidget(name_label)
        
        # Progress bar
        progress = QProgressBar()
        progress.setRange(0, 100)
        progress.setValue(min(100, int(percentage)))
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
        
        # Percentage
        pct_label = QLabel(f"{percentage:.1f}%")
        pct_label.setFont(QFont(Fonts.FAMILY_AR, 11, QFont.Bold))
        pct_label.setAlignment(Qt.AlignRight)
        pct_label.setMinimumWidth(60)
        pct_label.setStyleSheet(f"color: {color}; background: transparent;")
        layout.addWidget(pct_label)
        
        # Amount
        amount_label = QLabel(f"{amount:,.0f} ل.س")
        amount_label.setFont(QFont(Fonts.FAMILY_AR, 11, QFont.Bold))
        amount_label.setAlignment(Qt.AlignRight)
        amount_label.setMinimumWidth(110)
        amount_label.setStyleSheet("background: transparent;")
        layout.addWidget(amount_label)
        
        # Count badge
        count_label = QLabel(f"{count}")
        count_label.setFont(QFont(Fonts.FAMILY_AR, 10))
        count_label.setAlignment(Qt.AlignCenter)
        count_label.setFixedSize(32, 24)
        count_label.setStyleSheet(f"""
            background: {color}20;
            color: {color};
            border-radius: 12px;
        """)
        layout.addWidget(count_label)
        
        self.setStyleSheet(f"""
            QFrame#category_bar {{
                background: {Colors.LIGHT_CARD};
                border: 1px solid {Colors.LIGHT_BORDER};
                border-radius: 10px;
            }}
            QFrame#category_bar:hover {{
                background: {Colors.LIGHT_BG};
                border-color: {color}50;
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


class ExpensesReportView(QWidget):
    """Professional Expenses report view with modern UI/UX."""
    
    back_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.report_data: Dict = {}
        self.expenses_list: List[Dict] = []
        self.categories: List[Dict] = []
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
                    stop:0 {Colors.DANGER}, stop:1 #F97316);
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
        title = QLabel("💸 تقرير المصروفات")
        title.setFont(QFont(Fonts.FAMILY_AR, 22, QFont.Bold))
        title.setStyleSheet("color: white; background: transparent;")
        title_section.addWidget(title)
        
        subtitle = QLabel("تحليل شامل للمصروفات حسب الفئة والفترة الزمنية")
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
                background: {Colors.PRIMARY};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 18px;
            }}
            QPushButton:hover {{ background: {Colors.PRIMARY}dd; }}
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
        
        # Category filter
        cat_label = QLabel("الفئة:")
        cat_label.setFont(QFont(Fonts.FAMILY_AR, 12, QFont.Medium))
        cat_label.setStyleSheet(f"color: {Colors.LIGHT_TEXT_SECONDARY}; background: transparent;")
        filters_layout.addWidget(cat_label)
        
        self.category_combo = QComboBox()
        self.category_combo.addItem("جميع الفئات", None)
        self.category_combo.setMinimumWidth(150)
        filters_layout.addWidget(self.category_combo)
        
        apply_btn = QPushButton("🔍 عرض التقرير")
        apply_btn.setCursor(Qt.PointingHandCursor)
        apply_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Colors.DANGER};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 24px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background: #DC2626; }}
        """)
        apply_btn.clicked.connect(self._apply_filters)
        filters_layout.addWidget(apply_btn)
        filters_layout.addStretch()
        
        layout.addWidget(filters_card)

        # ═══════════════════════════════════════════════════════════
        # KEY METRICS SECTION
        # ═══════════════════════════════════════════════════════════
        layout.addWidget(SectionHeader("📊 ملخص المصروفات", ""))
        
        metrics_grid = QGridLayout()
        metrics_grid.setSpacing(16)
        
        self.total_expenses_card = ExpenseMetricCard(
            "إجمالي المصروفات", "0 ل.س", "💸", Colors.DANGER,
            "Total Expenses"
        )
        metrics_grid.addWidget(self.total_expenses_card, 0, 0)
        
        self.expense_count_card = ExpenseMetricCard(
            "عدد المصروفات", "0", "📋", Colors.INFO,
            "Expense Count"
        )
        metrics_grid.addWidget(self.expense_count_card, 0, 1)
        
        self.average_expense_card = ExpenseMetricCard(
            "متوسط المصروف", "0 ل.س", "📈", Colors.WARNING,
            "Average Expense"
        )
        metrics_grid.addWidget(self.average_expense_card, 0, 2)
        
        # Status card
        self.status_card = QFrame()
        self.status_card.setObjectName("status_card")
        self._update_status_card(0)
        metrics_grid.addWidget(self.status_card, 0, 3)
        
        layout.addLayout(metrics_grid)

        # ═══════════════════════════════════════════════════════════
        # CATEGORY BREAKDOWN SECTION
        # ═══════════════════════════════════════════════════════════
        layout.addWidget(SectionHeader("📊 توزيع المصروفات حسب الفئة", ""))
        
        self.category_card = QFrame()
        self.category_card.setObjectName("category_card")
        self.category_card.setStyleSheet(f"""
            QFrame#category_card {{
                background: {Colors.LIGHT_CARD};
                border: 1px solid {Colors.LIGHT_BORDER};
                border-radius: 12px;
            }}
        """)
        category_layout = QVBoxLayout(self.category_card)
        category_layout.setContentsMargins(20, 16, 20, 16)
        category_layout.setSpacing(10)
        
        cat_note = QLabel("💡 توزيع المصروفات حسب الفئة مع النسب المئوية والمبالغ")
        cat_note.setFont(QFont(Fonts.FAMILY_AR, 10))
        cat_note.setStyleSheet(f"""
            color: {Colors.LIGHT_TEXT_SECONDARY};
            background: {Colors.DANGER}15;
            padding: 8px 12px;
            border-radius: 6px;
            border-left: 3px solid {Colors.DANGER};
        """)
        category_layout.addWidget(cat_note)
        
        # Container for category breakdown items
        self.category_breakdown_layout = QVBoxLayout()
        self.category_breakdown_layout.setSpacing(8)
        category_layout.addLayout(self.category_breakdown_layout)
        
        layout.addWidget(self.category_card)

        # ═══════════════════════════════════════════════════════════
        # EXPENSES TABLE SECTION
        # ═══════════════════════════════════════════════════════════
        layout.addWidget(SectionHeader("📋 قائمة المصروفات التفصيلية", ""))
        
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
        
        table_note = QLabel("💡 جميع المصروفات المسجلة خلال الفترة المحددة")
        table_note.setFont(QFont(Fonts.FAMILY_AR, 10))
        table_note.setStyleSheet(f"""
            color: {Colors.LIGHT_TEXT_SECONDARY};
            background: {Colors.INFO}15;
            padding: 8px 12px;
            border-radius: 6px;
            border-left: 3px solid {Colors.INFO};
        """)
        table_layout.addWidget(table_note)
        
        self.expenses_table = QTableWidget()
        self.expenses_table.setColumnCount(6)
        self.expenses_table.setHorizontalHeaderLabels([
            'التاريخ', 'الفئة', 'الوصف', 'المبلغ', 'المرجع', 'الحالة'
        ])
        self.expenses_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.expenses_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.expenses_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.expenses_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.expenses_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.expenses_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.expenses_table.verticalHeader().setVisible(False)
        self.expenses_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.expenses_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.expenses_table.setAlternatingRowColors(True)
        self.expenses_table.setMinimumHeight(300)
        self._style_table(self.expenses_table)
        table_layout.addWidget(self.expenses_table)
        
        layout.addWidget(table_card, 1)
        
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
                background: {Colors.DANGER}15;
                color: {Colors.DANGER};
            }}
            QHeaderView::section {{
                background: {Colors.LIGHT_BG};
                color: {Colors.LIGHT_TEXT};
                padding: 12px;
                border: none;
                border-bottom: 2px solid {Colors.DANGER};
                font-weight: bold;
                font-size: 12px;
            }}
        """)

    def _update_status_card(self, total: float):
        """Update the expense status card."""
        if total > 100000:
            status_icon = "🔴"
            status_text = "مرتفع جداً"
            status_color = Colors.DANGER
        elif total > 50000:
            status_icon = "🟠"
            status_text = "مرتفع"
            status_color = Colors.WARNING
        elif total > 10000:
            status_icon = "🟡"
            status_text = "متوسط"
            status_color = Colors.INFO
        else:
            status_icon = "🟢"
            status_text = "منخفض"
            status_color = Colors.SUCCESS
        
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
        
        desc_lbl = QLabel("مستوى الإنفاق")
        desc_lbl.setFont(QFont(Fonts.FAMILY_AR, 10))
        desc_lbl.setAlignment(Qt.AlignCenter)
        desc_lbl.setStyleSheet(f"color: {Colors.LIGHT_TEXT_SECONDARY}; background: transparent;")
        layout.addWidget(desc_lbl)

    def _load_categories(self):
        """Load expense categories for the filter dropdown."""
        try:
            self.categories = api.get_expense_categories()
            
            # Clear and repopulate category combo
            self.category_combo.clear()
            self.category_combo.addItem("جميع الفئات", None)
            
            for category in self.categories:
                self.category_combo.addItem(
                    category.get('name', ''),
                    category.get('id')
                )
        except Exception:
            pass
    
    @handle_ui_error
    def refresh(self):
        """Refresh the expenses report data from API."""
        self._load_categories()
        self._load_report()
    
    @handle_ui_error
    def _apply_filters(self):
        """Apply filters and reload the report."""
        self._load_report()
    
    def _load_report(self):
        """Load expenses report data from API."""
        start_date = self.from_date.date().toString('yyyy-MM-dd')
        end_date = self.to_date.date().toString('yyyy-MM-dd')
        category_id = self.category_combo.currentData()
        
        self.report_data = api.get_expenses_report(
            start_date=start_date,
            end_date=end_date,
            category_id=category_id
        )
        
        self._update_summary_cards()
        self._update_category_breakdown()
        self._update_expenses_table()
    
    def _update_summary_cards(self):
        """Update the summary cards with report data."""
        summary = self.report_data.get('summary', {})
        total_expenses = float(summary.get('total_expenses', 0))
        expense_count = int(summary.get('expense_count', 0))
        average_expense = float(summary.get('average_expense', 0))
        
        self.total_expenses_card.update_value(f"{total_expenses:,.0f} ل.س")
        self.expense_count_card.update_value(f"{expense_count:,}")
        self.average_expense_card.update_value(f"{average_expense:,.0f} ل.س")
        self._update_status_card(total_expenses)

    def _update_category_breakdown(self):
        """Update the category breakdown section with visual representation."""
        # Clear existing breakdown items
        while self.category_breakdown_layout.count():
            item = self.category_breakdown_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        by_category = self.report_data.get('by_category', [])
        
        if not by_category:
            no_data_label = QLabel("لا توجد بيانات للعرض")
            no_data_label.setAlignment(Qt.AlignCenter)
            no_data_label.setFont(QFont(Fonts.FAMILY_AR, 12))
            no_data_label.setStyleSheet(f"""
                color: {Colors.LIGHT_TEXT_SECONDARY};
                padding: 30px;
                background: {Colors.LIGHT_BG};
                border-radius: 8px;
            """)
            self.category_breakdown_layout.addWidget(no_data_label)
            return
        
        # Define colors for categories
        category_colors = [
            Colors.DANGER,
            Colors.WARNING,
            Colors.INFO,
            Colors.SUCCESS,
            Colors.PRIMARY,
            Colors.SECONDARY,
            "#9C27B0",  # Purple
            "#00BCD4",  # Cyan
            "#FF9800",  # Orange
            "#795548",  # Brown
        ]
        
        for i, category in enumerate(by_category):
            category_name = category.get('category_name', 'غير مصنف')
            total = float(category.get('total', 0))
            percentage = float(category.get('percentage', 0))
            count = int(category.get('count', 0))
            color = category_colors[i % len(category_colors)]
            
            bar = CategoryBar(category_name, total, percentage, count, color)
            self.category_breakdown_layout.addWidget(bar)
    
    def _update_expenses_table(self):
        """Update the expenses table with report data."""
        expenses = self.report_data.get('expenses', [])
        self.expenses_list = expenses
        
        self.expenses_table.setRowCount(len(expenses))
        
        for row, expense in enumerate(expenses):
            # Date
            date_str = expense.get('date', '')
            date_item = QTableWidgetItem(str(date_str))
            date_item.setData(Qt.UserRole, expense)
            date_item.setTextAlignment(Qt.AlignCenter)
            date_item.setFont(QFont(Fonts.FAMILY_AR, 11))
            self.expenses_table.setItem(row, 0, date_item)
            
            # Category
            category_name = expense.get('category', 'غير مصنف')
            cat_item = QTableWidgetItem(str(category_name))
            cat_item.setFont(QFont(Fonts.FAMILY_AR, 11, QFont.Medium))
            self.expenses_table.setItem(row, 1, cat_item)
            
            # Description
            description = expense.get('description', '')
            desc_item = QTableWidgetItem(str(description))
            desc_item.setFont(QFont(Fonts.FAMILY_AR, 11))
            self.expenses_table.setItem(row, 2, desc_item)
            
            # Amount
            amount = float(expense.get('amount', 0))
            amount_item = QTableWidgetItem(f"{amount:,.0f} ل.س")
            amount_item.setTextAlignment(Qt.AlignCenter)
            amount_item.setFont(QFont(Fonts.FAMILY_AR, 11, QFont.Bold))
            amount_item.setForeground(QBrush(QColor(Colors.DANGER)))
            self.expenses_table.setItem(row, 3, amount_item)
            
            # Reference
            reference = expense.get('reference', '')
            ref_item = QTableWidgetItem(str(reference) if reference else '-')
            ref_item.setTextAlignment(Qt.AlignCenter)
            ref_item.setFont(QFont(Fonts.FAMILY_AR, 11))
            self.expenses_table.setItem(row, 4, ref_item)
            
            # Status indicator based on amount
            if amount > 10000:
                status = "🔴 كبير"
            elif amount > 5000:
                status = "🟡 متوسط"
            else:
                status = "🟢 صغير"
            status_item = QTableWidgetItem(status)
            status_item.setTextAlignment(Qt.AlignCenter)
            self.expenses_table.setItem(row, 5, status_item)

    def _export_excel(self):
        """Export report to Excel."""
        if not self.expenses_list:
            MessageDialog.warning(self, "تنبيه", "لا توجد بيانات للتصدير")
            return
        
        try:
            columns = [
                ('date', 'التاريخ'),
                ('category', 'الفئة'),
                ('description', 'الوصف'),
                ('amount', 'المبلغ'),
                ('reference', 'المرجع')
            ]
            
            export_data = []
            for expense in self.expenses_list:
                export_data.append({
                    'date': expense.get('date', ''),
                    'category': expense.get('category', 'غير مصنف'),
                    'description': expense.get('description', ''),
                    'amount': float(expense.get('amount', 0)),
                    'reference': expense.get('reference', '') or '-'
                })
            
            filename = f"تقرير_المصروفات_{datetime.now().strftime('%Y%m%d')}.xlsx"
            
            summary = self.report_data.get('summary', {})
            by_category = self.report_data.get('by_category', [])
            
            start_date = self.from_date.date().toString('yyyy-MM-dd')
            end_date = self.to_date.date().toString('yyyy-MM-dd')
            
            summary_data = {
                'الفترة': f"{start_date} → {end_date}",
                'إجمالي المصروفات': f"{float(summary.get('total_expenses', 0)):,.0f} ل.س",
                'عدد المصروفات': str(summary.get('expense_count', 0)),
                'متوسط المصروف': f"{float(summary.get('average_expense', 0)):,.0f} ل.س"
            }
            
            for cat in by_category:
                cat_name = cat.get('category_name', 'غير مصنف')
                cat_total = float(cat.get('total', 0))
                cat_percent = float(cat.get('percentage', 0))
                summary_data[f'{cat_name}'] = f"{cat_total:,.0f} ل.س ({cat_percent:.1f}%)"
            
            success = ExportService.export_to_excel(
                data=export_data,
                columns=columns,
                filename=filename,
                title="تقرير المصروفات",
                parent=self,
                summary=summary_data
            )
            
            if success:
                MessageDialog.info(self, "نجاح", "تم التصدير بنجاح ✅")
                
        except ExportError as e:
            MessageDialog.error(self, "خطأ", e.message)
        except Exception as e:
            MessageDialog.error(self, "خطأ", f"فشل التصدير: {str(e)}")
    
    def _export_pdf(self):
        """Export report to PDF."""
        if not self.expenses_list:
            MessageDialog.warning(self, "تنبيه", "لا توجد بيانات للتصدير")
            return
        
        try:
            columns = [
                ('date', 'التاريخ'),
                ('category', 'الفئة'),
                ('description', 'الوصف'),
                ('amount', 'المبلغ'),
                ('reference', 'المرجع')
            ]
            
            export_data = []
            for expense in self.expenses_list:
                export_data.append({
                    'date': expense.get('date', ''),
                    'category': expense.get('category', 'غير مصنف'),
                    'description': expense.get('description', ''),
                    'amount': float(expense.get('amount', 0)),
                    'reference': expense.get('reference', '') or '-'
                })
            
            filename = f"تقرير_المصروفات_{datetime.now().strftime('%Y%m%d')}.pdf"
            
            summary = self.report_data.get('summary', {})
            by_category = self.report_data.get('by_category', [])
            
            start_date = self.from_date.date().toString('yyyy-MM-dd')
            end_date = self.to_date.date().toString('yyyy-MM-dd')
            
            summary_data = {
                'الفترة': f"{start_date} → {end_date}",
                'إجمالي المصروفات': f"{float(summary.get('total_expenses', 0)):,.0f} ل.س",
                'عدد المصروفات': str(summary.get('expense_count', 0)),
                'متوسط المصروف': f"{float(summary.get('average_expense', 0)):,.0f} ل.س"
            }
            
            for cat in by_category:
                cat_name = cat.get('category_name', 'غير مصنف')
                cat_total = float(cat.get('total', 0))
                cat_percent = float(cat.get('percentage', 0))
                summary_data[f'{cat_name}'] = f"{cat_total:,.0f} ل.س ({cat_percent:.1f}%)"
            
            success = ExportService.export_to_pdf(
                data=export_data,
                columns=columns,
                filename=filename,
                title="تقرير المصروفات",
                parent=self,
                summary=summary_data,
                date_range=(start_date, end_date)
            )
            
            if success:
                MessageDialog.info(self, "نجاح", "تم التصدير بنجاح ✅")
                
        except ExportError as e:
            MessageDialog.error(self, "خطأ", e.message)
        except Exception as e:
            MessageDialog.error(self, "خطأ", f"فشل التصدير: {str(e)}")
