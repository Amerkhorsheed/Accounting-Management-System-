"""Inventory Report View - تقرير المخزون - Professional Modern Design"""

from datetime import datetime
from typing import Dict, List

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QFrame, QGridLayout,
    QScrollArea, QGraphicsDropShadowEffect, QProgressBar
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QBrush, QColor

from ...config import Colors, Fonts, config
from ...widgets.cards import Card
from ...widgets.dialogs import MessageDialog
from ...services.api import api, ApiException
from ...services.export import ExportService, ExportError
from ...utils.error_handler import handle_ui_error


class InventoryMetricCard(QFrame):
    """Modern metric card with gradient accent for inventory data."""
    
    def __init__(self, title: str, value: str, icon: str, color: str,
                 subtitle: str = "", is_warning: bool = False, parent=None):
        super().__init__(parent)
        self.accent_color = color
        self.is_warning = is_warning
        self.setObjectName("inventory_metric_card")
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
        
        # Warning badge if needed
        if self.is_warning:
            warning_badge = QLabel("⚠️")
            warning_badge.setFont(QFont(Fonts.FAMILY_AR, 14))
            warning_badge.setStyleSheet("background: transparent;")
            top.addWidget(warning_badge)
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
            QFrame#inventory_metric_card {{
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
    
    def __init__(self, name: str, count: int, total: int, color: str, parent=None):
        super().__init__(parent)
        self.setObjectName("category_bar")
        self.setup_ui(name, count, total, color)
        
    def setup_ui(self, name: str, count: int, total: int, color: str):
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
        name_label = QLabel(name if name else "بدون فئة")
        name_label.setFont(QFont(Fonts.FAMILY_AR, 12, QFont.Medium))
        name_label.setMinimumWidth(150)
        name_label.setStyleSheet("background: transparent;")
        layout.addWidget(name_label)
        
        # Progress bar
        pct = (count / total * 100) if total > 0 else 0
        progress = QProgressBar()
        progress.setRange(0, 100)
        progress.setValue(min(100, int(pct)))
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
        pct_label = QLabel(f"{pct:.1f}%")
        pct_label.setFont(QFont(Fonts.FAMILY_AR, 11, QFont.Bold))
        pct_label.setAlignment(Qt.AlignRight)
        pct_label.setMinimumWidth(60)
        pct_label.setStyleSheet(f"color: {color}; background: transparent;")
        layout.addWidget(pct_label)
        
        # Count badge
        count_label = QLabel(f"{count}")
        count_label.setFont(QFont(Fonts.FAMILY_AR, 11, QFont.Bold))
        count_label.setAlignment(Qt.AlignCenter)
        count_label.setFixedSize(40, 28)
        count_label.setStyleSheet(f"""
            background: {color}20;
            color: {color};
            border-radius: 14px;
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


class InventoryReportView(QWidget):
    """Professional Inventory report view with modern UI/UX."""

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
                    stop:0 {Colors.WARNING}, stop:1 #F97316);
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
        title = QLabel("📦 تقرير المخزون")
        title.setFont(QFont(Fonts.FAMILY_AR, 22, QFont.Bold))
        title.setStyleSheet("color: white; background: transparent;")
        title_section.addWidget(title)
        
        subtitle = QLabel("تحليل شامل لقيمة وكميات المخزون والأصناف منخفضة المخزون")
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
        # KEY METRICS SECTION
        # ═══════════════════════════════════════════════════════════
        layout.addWidget(SectionHeader("📊 ملخص المخزون", ""))
        
        metrics_grid = QGridLayout()
        metrics_grid.setSpacing(16)
        
        self.total_value_card = InventoryMetricCard(
            "إجمالي قيمة المخزون", "0 ل.س", "💰", Colors.SUCCESS,
            "Total Inventory Value"
        )
        metrics_grid.addWidget(self.total_value_card, 0, 0)
        
        self.item_count_card = InventoryMetricCard(
            "عدد الأصناف", "0", "📦", Colors.INFO,
            "Total Items"
        )
        metrics_grid.addWidget(self.item_count_card, 0, 1)
        
        self.low_stock_card = InventoryMetricCard(
            "أصناف منخفضة المخزون", "0", "⚠️", Colors.DANGER,
            "Low Stock Items", is_warning=True
        )
        metrics_grid.addWidget(self.low_stock_card, 0, 2)
        
        # Status card
        self.status_card = QFrame()
        self.status_card.setObjectName("status_card")
        self._update_status_card(0, 0)
        metrics_grid.addWidget(self.status_card, 0, 3)
        
        layout.addLayout(metrics_grid)

        # ═══════════════════════════════════════════════════════════
        # CATEGORY BREAKDOWN SECTION
        # ═══════════════════════════════════════════════════════════
        layout.addWidget(SectionHeader("📊 توزيع المخزون حسب الفئة", ""))
        
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
        
        cat_note = QLabel("💡 توزيع الأصناف حسب الفئة مع النسب المئوية")
        cat_note.setFont(QFont(Fonts.FAMILY_AR, 10))
        cat_note.setStyleSheet(f"""
            color: {Colors.LIGHT_TEXT_SECONDARY};
            background: {Colors.INFO}15;
            padding: 8px 12px;
            border-radius: 6px;
            border-left: 3px solid {Colors.INFO};
        """)
        category_layout.addWidget(cat_note)
        
        # Container for category breakdown items
        self.category_breakdown_layout = QVBoxLayout()
        self.category_breakdown_layout.setSpacing(8)
        category_layout.addLayout(self.category_breakdown_layout)
        
        layout.addWidget(self.category_card)

        # ═══════════════════════════════════════════════════════════
        # LOW STOCK ITEMS TABLE
        # ═══════════════════════════════════════════════════════════
        layout.addWidget(SectionHeader("⚠️ الأصناف منخفضة المخزون", ""))
        
        low_stock_card = QFrame()
        low_stock_card.setObjectName("low_stock_card")
        low_stock_card.setStyleSheet(f"""
            QFrame#low_stock_card {{
                background: {Colors.LIGHT_CARD};
                border: 1px solid {Colors.LIGHT_BORDER};
                border-radius: 12px;
            }}
        """)
        low_stock_layout = QVBoxLayout(low_stock_card)
        low_stock_layout.setContentsMargins(20, 16, 20, 16)
        low_stock_layout.setSpacing(12)
        
        low_note = QLabel("💡 الأصناف التي وصلت إلى أو أقل من الحد الأدنى للمخزون - تحتاج إلى إعادة طلب")
        low_note.setFont(QFont(Fonts.FAMILY_AR, 10))
        low_note.setStyleSheet(f"""
            color: {Colors.LIGHT_TEXT_SECONDARY};
            background: {Colors.DANGER}15;
            padding: 8px 12px;
            border-radius: 6px;
            border-left: 3px solid {Colors.DANGER};
        """)
        low_stock_layout.addWidget(low_note)
        
        self.low_stock_table = QTableWidget()
        self.low_stock_table.setColumnCount(7)
        self.low_stock_table.setHorizontalHeaderLabels([
            'الكود', 'اسم المنتج', 'المستودع', 'الكمية الحالية', 
            'الحد الأدنى', 'النقص', 'الحالة'
        ])
        self.low_stock_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.low_stock_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.low_stock_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.low_stock_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.low_stock_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.low_stock_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.low_stock_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.low_stock_table.verticalHeader().setVisible(False)
        self.low_stock_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.low_stock_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.low_stock_table.setAlternatingRowColors(True)
        self.low_stock_table.setMinimumHeight(300)
        self._style_table(self.low_stock_table, Colors.DANGER)
        low_stock_layout.addWidget(self.low_stock_table)
        
        layout.addWidget(low_stock_card, 1)
        
        # Add stretch at bottom
        layout.addStretch()
        
        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    def _style_table(self, table: QTableWidget, accent_color: str = None):
        """Apply modern styling to table."""
        accent = accent_color or Colors.WARNING
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
                background: {accent}15;
                color: {accent};
            }}
            QHeaderView::section {{
                background: {Colors.LIGHT_BG};
                color: {Colors.LIGHT_TEXT};
                padding: 12px;
                border: none;
                border-bottom: 2px solid {accent};
                font-weight: bold;
                font-size: 12px;
            }}
        """)
        
    def _update_status_card(self, low_stock: int, total: int):
        """Update the inventory status card."""
        if total == 0:
            status_icon = "📦"
            status_text = "لا توجد بيانات"
            status_color = Colors.LIGHT_TEXT_SECONDARY
        elif low_stock == 0:
            status_icon = "✅"
            status_text = "مخزون ممتاز"
            status_color = Colors.SUCCESS
        elif low_stock <= 5:
            status_icon = "📊"
            status_text = "مخزون جيد"
            status_color = Colors.INFO
        elif low_stock <= 10:
            status_icon = "⚠️"
            status_text = "يحتاج مراجعة"
            status_color = Colors.WARNING
        else:
            status_icon = "🚨"
            status_text = "تحذير!"
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
        
        desc_lbl = QLabel("حالة المخزون")
        desc_lbl.setFont(QFont(Fonts.FAMILY_AR, 10))
        desc_lbl.setAlignment(Qt.AlignCenter)
        desc_lbl.setStyleSheet(f"color: {Colors.LIGHT_TEXT_SECONDARY}; background: transparent;")
        layout.addWidget(desc_lbl)

    @handle_ui_error
    def refresh(self):
        self.report_data = api.get_inventory_report() or {}
        self._update_ui()

    def _update_ui(self):
        data = self.report_data or {}

        # Extract values
        total_value = float(data.get('total_value', 0) or 0)
        item_count = int(data.get('item_count', 0) or 0)
        low_stock_count = int(data.get('low_stock_count', 0) or 0)

        # Update metric cards
        self.total_value_card.update_value(f"{total_value:,.0f} ل.س")
        self.item_count_card.update_value(f"{item_count:,}")
        self.low_stock_card.update_value(f"{low_stock_count:,}")
        
        # Update status card
        self._update_status_card(low_stock_count, item_count)

        # Update category breakdown
        self._update_category_breakdown(data)
        
        # Update low stock table
        self._update_low_stock_table(data)

    def _update_category_breakdown(self, data: Dict):
        """Update the category breakdown section."""
        # Clear existing breakdown items
        while self.category_breakdown_layout.count():
            item = self.category_breakdown_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        by_category = data.get('by_category', [])
        total_items = sum(cat.get('count', 0) for cat in by_category)
        
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
            Colors.PRIMARY,
            Colors.SUCCESS,
            Colors.WARNING,
            Colors.INFO,
            Colors.DANGER,
            Colors.SECONDARY,
            "#9C27B0",  # Purple
            "#00BCD4",  # Cyan
            "#FF9800",  # Orange
            "#795548",  # Brown
        ]
        
        for i, category in enumerate(by_category):
            category_name = category.get('category__name', '') or 'بدون فئة'
            count = int(category.get('count', 0))
            color = category_colors[i % len(category_colors)]
            
            bar = CategoryBar(category_name, count, total_items, color)
            self.category_breakdown_layout.addWidget(bar)

    def _update_low_stock_table(self, data: Dict):
        """Update low stock items table."""
        low_stock_items = data.get('low_stock_items', [])
        self.low_stock_table.setRowCount(len(low_stock_items))
        
        for r, item in enumerate(low_stock_items):
            code = item.get('product_code', '') or '-'
            name = item.get('product_name', '') or 'غير محدد'
            warehouse = item.get('warehouse', '') or '-'
            quantity = float(item.get('quantity', 0) or 0)
            minimum = float(item.get('minimum', 0) or 0)
            shortage = float(item.get('shortage', 0) or 0)
            
            # Code
            code_item = QTableWidgetItem(str(code))
            code_item.setTextAlignment(Qt.AlignCenter)
            code_item.setFont(QFont(Fonts.FAMILY_AR, 11))
            code_item.setForeground(QBrush(QColor(Colors.LIGHT_TEXT_SECONDARY)))
            self.low_stock_table.setItem(r, 0, code_item)
            
            # Product name
            name_item = QTableWidgetItem(str(name))
            name_item.setFont(QFont(Fonts.FAMILY_AR, 11, QFont.Medium))
            self.low_stock_table.setItem(r, 1, name_item)
            
            # Warehouse
            warehouse_item = QTableWidgetItem(str(warehouse))
            warehouse_item.setTextAlignment(Qt.AlignCenter)
            warehouse_item.setFont(QFont(Fonts.FAMILY_AR, 11))
            self.low_stock_table.setItem(r, 2, warehouse_item)
            
            # Current quantity
            qty_item = QTableWidgetItem(f"{quantity:,.0f}")
            qty_item.setTextAlignment(Qt.AlignCenter)
            qty_item.setFont(QFont(Fonts.FAMILY_AR, 11, QFont.Bold))
            if quantity == 0:
                qty_item.setForeground(QBrush(QColor(Colors.DANGER)))
            else:
                qty_item.setForeground(QBrush(QColor(Colors.WARNING)))
            self.low_stock_table.setItem(r, 3, qty_item)
            
            # Minimum
            min_item = QTableWidgetItem(f"{minimum:,.0f}")
            min_item.setTextAlignment(Qt.AlignCenter)
            min_item.setFont(QFont(Fonts.FAMILY_AR, 11))
            min_item.setForeground(QBrush(QColor(Colors.INFO)))
            self.low_stock_table.setItem(r, 4, min_item)
            
            # Shortage
            shortage_item = QTableWidgetItem(f"{shortage:,.0f}")
            shortage_item.setTextAlignment(Qt.AlignCenter)
            shortage_item.setFont(QFont(Fonts.FAMILY_AR, 11, QFont.Bold))
            shortage_item.setForeground(QBrush(QColor(Colors.DANGER)))
            self.low_stock_table.setItem(r, 5, shortage_item)
            
            # Status
            if quantity == 0:
                status = "🔴 نفذ"
            elif quantity <= minimum * 0.5:
                status = "🟠 حرج"
            else:
                status = "🟡 منخفض"
            status_item = QTableWidgetItem(status)
            status_item.setTextAlignment(Qt.AlignCenter)
            self.low_stock_table.setItem(r, 6, status_item)

    def _build_export_rows(self) -> List[Dict]:
        """Build rows for export."""
        data = self.report_data or {}
        export_rows: List[Dict] = []

        # Add low stock items
        for item in data.get('low_stock_items', []):
            export_rows.append({
                'code': item.get('product_code', ''),
                'name': item.get('product_name', ''),
                'warehouse': item.get('warehouse', ''),
                'quantity': float(item.get('quantity', 0) or 0),
                'minimum': float(item.get('minimum', 0) or 0),
                'shortage': float(item.get('shortage', 0) or 0),
            })

        return export_rows

    def _export_excel(self):
        """Export report to Excel."""
        if not self.report_data:
            MessageDialog.warning(self, "تنبيه", "لا توجد بيانات للتصدير")
            return

        try:
            summary_data = {
                'إجمالي قيمة المخزون': f"{float(self.report_data.get('total_value', 0) or 0):,.0f} ل.س",
                'عدد الأصناف': self.report_data.get('item_count', 0),
                'أصناف منخفضة المخزون': self.report_data.get('low_stock_count', 0),
            }
            
            # Add category breakdown to summary
            for cat in self.report_data.get('by_category', []):
                cat_name = cat.get('category__name', '') or 'بدون فئة'
                cat_count = cat.get('count', 0)
                summary_data[f'فئة: {cat_name}'] = f"{cat_count} صنف"

            rows = self._build_export_rows()
            
            columns = [
                ('code', 'الكود'),
                ('name', 'اسم المنتج'),
                ('warehouse', 'المستودع'),
                ('quantity', 'الكمية الحالية'),
                ('minimum', 'الحد الأدنى'),
                ('shortage', 'النقص'),
            ]

            filename = f"تقرير_المخزون_{datetime.now().strftime('%Y%m%d')}.xlsx"
            ok = ExportService.export_to_excel(
                data=rows,
                columns=columns,
                filename=filename,
                title="تقرير المخزون - الأصناف منخفضة المخزون",
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
            summary_data = {
                'إجمالي قيمة المخزون': f"{float(self.report_data.get('total_value', 0) or 0):,.0f} ل.س",
                'عدد الأصناف': self.report_data.get('item_count', 0),
                'أصناف منخفضة المخزون': self.report_data.get('low_stock_count', 0),
            }
            
            # Add category breakdown to summary
            for cat in self.report_data.get('by_category', []):
                cat_name = cat.get('category__name', '') or 'بدون فئة'
                cat_count = cat.get('count', 0)
                summary_data[f'فئة: {cat_name}'] = f"{cat_count} صنف"

            rows = self._build_export_rows()
            
            columns = [
                ('code', 'الكود'),
                ('name', 'اسم المنتج'),
                ('warehouse', 'المستودع'),
                ('quantity', 'الكمية الحالية'),
                ('minimum', 'الحد الأدنى'),
                ('shortage', 'النقص'),
            ]

            filename = f"تقرير_المخزون_{datetime.now().strftime('%Y%m%d')}.pdf"
            ok = ExportService.export_to_pdf(
                data=rows,
                columns=columns,
                filename=filename,
                title="تقرير المخزون - الأصناف منخفضة المخزون",
                parent=self,
                summary=summary_data
            )
            if ok:
                MessageDialog.info(self, "نجاح", "تم التصدير بنجاح ✅")
        except ExportError as e:
            MessageDialog.error(self, "خطأ", e.message)
        except Exception as e:
            MessageDialog.error(self, "خطأ", f"فشل التصدير: {str(e)}")
