"""
Dashboard View

Requirements: 4.1, 4.3 - Error handling for data loading and refresh operations
Requirements: 8.1, 8.2, 8.3, 8.4 - Credit summary on dashboard
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QScrollArea
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QCursor

from ...config import Colors, Fonts, config
from ...widgets.cards import StatCard, Card
from ...services.api import api, ApiException
from ...utils.error_handler import handle_ui_error


class ClickableStatCard(StatCard):
    """
    StatCard that emits a signal when clicked.
    Used for navigation to related reports.
    
    Requirements: 8.4 - Navigate to receivables report on card click
    """
    clicked = Signal()
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        
    def mousePressEvent(self, event):
        """Handle mouse press to emit clicked signal."""
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class DashboardView(QWidget):
    """
    Main dashboard view with statistics and overview.
    
    Requirements: 8.1, 8.2, 8.3, 8.4 - Credit summary display and navigation
    """
    
    # Signal to navigate to receivables report
    navigate_to_receivables = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
        # Setup auto-refresh timer (30 seconds)
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start(30000)
        
    def setup_ui(self):
        """Initialize dashboard UI."""
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)
        
        # Welcome section
        welcome = QLabel("مرحباً بك في نظام إدارة المحاسبة")
        welcome.setProperty("class", "title")
        layout.addWidget(welcome)
        
        subtitle = QLabel("نظرة عامة على أداء عملك اليوم")
        subtitle.setProperty("class", "subtitle")
        layout.addWidget(subtitle)
        
        # Stats cards grid
        stats_layout = QGridLayout()
        stats_layout.setSpacing(20)
        
        # Row 1: Main stats
        self.sales_card = StatCard(
            title="المبيعات اليوم",
            value="0.00 ر.س",
            icon="💰",
            color=Colors.SUCCESS,
            change="+12.5%"
        )
        stats_layout.addWidget(self.sales_card, 0, 0)
        
        self.purchases_card = StatCard(
            title="المشتريات اليوم",
            value="0.00 ر.س",
            icon="🛒",
            color=Colors.PRIMARY
        )
        stats_layout.addWidget(self.purchases_card, 0, 1)
        
        self.expenses_card = StatCard(
            title="المصروفات اليوم",
            value="0.00 ر.س",
            icon="💸",
            color=Colors.WARNING
        )
        stats_layout.addWidget(self.expenses_card, 0, 2)
        
        self.profit_card = StatCard(
            title="صافي الربح",
            value="0.00 ر.س",
            icon="📈",
            color=Colors.SECONDARY,
            change="+8.3%"
        )
        stats_layout.addWidget(self.profit_card, 0, 3)
        
        # Row 2: Count stats
        self.invoices_card = StatCard(
            title="فواتير اليوم",
            value="0",
            icon="📄",
            color=Colors.INFO
        )
        stats_layout.addWidget(self.invoices_card, 1, 0)
        
        self.customers_card = StatCard(
            title="العملاء",
            value="0",
            icon="👥",
            color=Colors.PRIMARY
        )
        stats_layout.addWidget(self.customers_card, 1, 1)
        
        self.products_card = StatCard(
            title="المنتجات",
            value="0",
            icon="📦",
            color=Colors.SECONDARY
        )
        stats_layout.addWidget(self.products_card, 1, 2)
        
        self.low_stock_card = StatCard(
            title="منتجات منخفضة المخزون",
            value="0",
            icon="⚠️",
            color=Colors.DANGER
        )
        stats_layout.addWidget(self.low_stock_card, 1, 3)
        
        # Row 3: Credit/Receivables summary (Requirements: 8.1, 8.2, 8.3, 8.4)
        # Total receivables - clickable to navigate to receivables report
        self.receivables_card = ClickableStatCard(
            title="إجمالي المستحقات",
            value="0.00 ل.س",
            icon="💳",
            color=Colors.INFO
        )
        self.receivables_card.clicked.connect(self._on_receivables_clicked)
        stats_layout.addWidget(self.receivables_card, 2, 0)
        
        # Customers with outstanding balance - clickable
        self.customers_with_balance_card = ClickableStatCard(
            title="عملاء لديهم رصيد",
            value="0",
            icon="👤",
            color=Colors.PRIMARY
        )
        self.customers_with_balance_card.clicked.connect(self._on_receivables_clicked)
        stats_layout.addWidget(self.customers_with_balance_card, 2, 1)
        
        # Total overdue amount - clickable
        self.overdue_card = ClickableStatCard(
            title="المبالغ المتأخرة",
            value="0.00 ل.س",
            icon="⏰",
            color=Colors.DANGER
        )
        self.overdue_card.clicked.connect(self._on_receivables_clicked)
        stats_layout.addWidget(self.overdue_card, 2, 2)
        
        layout.addLayout(stats_layout)
        
        # Charts section
        charts_layout = QHBoxLayout()
        charts_layout.setSpacing(20)
        
        # Sales chart placeholder
        sales_chart = Card()
        sales_chart_layout = QVBoxLayout(sales_chart)
        sales_chart_layout.setContentsMargins(20, 20, 20, 20)
        
        chart_title = QLabel("📊 المبيعات خلال الأسبوع")
        chart_title.setProperty("class", "h2")
        sales_chart_layout.addWidget(chart_title)
        
        chart_placeholder = QLabel("مخطط المبيعات")
        chart_placeholder.setAlignment(Qt.AlignCenter)
        chart_placeholder.setMinimumHeight(200)
        chart_placeholder.setProperty("class", "subtitle")
        chart_placeholder.setStyleSheet(f"""
            background: {Colors.LIGHT_BG}80;
            border-radius: 8px;
        """)
        sales_chart_layout.addWidget(chart_placeholder)
        
        charts_layout.addWidget(sales_chart, 2)
        
        # Top products
        top_products = Card()
        top_products_layout = QVBoxLayout(top_products)
        top_products_layout.setContentsMargins(20, 20, 20, 20)
        
        products_title = QLabel("🏆 أكثر المنتجات مبيعاً")
        products_title.setProperty("class", "h2")
        top_products_layout.addWidget(products_title)
        
        for i in range(5):
            row = QFrame()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 8, 0, 8)
            
            rank = QLabel(f"{i+1}")
            rank.setFixedSize(24, 24)
            rank.setAlignment(Qt.AlignCenter)
            rank.setStyleSheet(f"""
                background: {Colors.PRIMARY}20;
                color: {Colors.PRIMARY};
                border-radius: 4px;
                font-weight: bold;
            """)
            row_layout.addWidget(rank)
            
            name = QLabel("اسم المنتج")
            name.setProperty("class", "subtitle")
            row_layout.addWidget(name, 1)
            
            sales = QLabel("0 وحدة")
            row_layout.addWidget(sales)
            
            top_products_layout.addWidget(row)
        
        charts_layout.addWidget(top_products, 1)
        self.top_products_layout = top_products_layout
        
        layout.addLayout(charts_layout)
        
        # Recent activity
        activity_card = Card()
        self.activity_layout = QVBoxLayout(activity_card)
        self.activity_layout.setContentsMargins(20, 20, 20, 20)
        
        activity_title = QLabel("🕐 آخر العمليات")
        activity_title.setProperty("class", "h2")
        self.activity_layout.addWidget(activity_title)
        
        layout.addWidget(activity_card)
        
        layout.addStretch()
        
        scroll.setWidget(content)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)
        
    @handle_ui_error
    def refresh(self):
        """Refresh dashboard data from API."""
        # Load dashboard data
        data = api.get_dashboard()
        self.update_stats(data)
    
    def _on_receivables_clicked(self):
        """
        Handle click on receivables cards to navigate to receivables report.
        
        Requirements: 8.4 - Navigate to receivables report on card click
        """
        self.navigate_to_receivables.emit()
        
    def update_stats(self, data: dict):
        """Update dashboard statistics including credit summary."""
        # Sales data
        if 'sales' in data:
            sales_data = data['sales']
            if isinstance(sales_data, dict):
                self.sales_card.update_value(config.format_usd(float(sales_data.get('total_usd', sales_data.get('total', 0)) or 0)))
                # Update invoice count from sales count
                self.invoices_card.update_value(str(sales_data.get('count', 0)))
            else:
                self.sales_card.update_value(config.format_usd(float(sales_data or 0)))
        
        # Purchases data
        if 'purchases' in data:
            purchases_data = data['purchases']
            if isinstance(purchases_data, dict):
                self.purchases_card.update_value(config.format_usd(float(purchases_data.get('total_usd', purchases_data.get('total', 0)) or 0)))
            else:
                self.purchases_card.update_value(config.format_usd(float(purchases_data or 0)))
        
        # Expenses data
        if 'expenses' in data:
            expenses_data = data['expenses']
            if isinstance(expenses_data, dict):
                self.expenses_card.update_value(config.format_usd(float(expenses_data.get('total_usd', expenses_data.get('total', 0)) or 0)))
            else:
                self.expenses_card.update_value(config.format_usd(float(expenses_data or 0)))
        
        # Profit data
        if 'profit' in data:
            profit_data = data['profit']
            if isinstance(profit_data, dict):
                self.profit_card.update_value(config.format_usd(float(profit_data.get('net_usd', profit_data.get('net', 0)) or 0)))
            else:
                self.profit_card.update_value(config.format_usd(float(profit_data or 0)))
        
        # Counts data
        if 'counts' in data:
            counts = data['counts']
            if 'products' in counts:
                self.products_card.update_value(str(counts['products']))
            if 'customers' in counts:
                self.customers_card.update_value(str(counts['customers']))
            if 'low_stock' in counts:
                self.low_stock_card.update_value(str(counts['low_stock']))
        
        # Credit summary data (Requirements: 8.1, 8.2, 8.3)
        if 'credit' in data:
            credit_data = data['credit']
            
            # Total receivables (Requirement 8.1)
            receivables_total = float(credit_data.get('receivables_total_usd', credit_data.get('receivables_total', 0)) or 0)
            self.receivables_card.update_value(config.format_usd(receivables_total))
            
            # Customers with balance count (Requirement 8.2)
            customers_with_balance = int(credit_data.get('customers_with_balance', 0))
            self.customers_with_balance_card.update_value(str(customers_with_balance))
            
            # Total overdue amount (Requirement 8.3)
            overdue_total = float(credit_data.get('overdue_total_usd', credit_data.get('overdue_total', 0)) or 0)
            self.overdue_card.update_value(config.format_usd(overdue_total))
        
        # Update top products
        if 'top_products' in data:
            self._update_top_products(data['top_products'])
            
        # Update recent activity
        if 'recent_activity' in data:
            self._update_recent_activity(data['recent_activity'])

    def _update_top_products(self, products):
        """Update the top products list in the UI."""
        # Clear existing items (except title)
        while self.top_products_layout.count() > 1:
            child = self.top_products_layout.takeAt(1)
            if child.widget():
                child.widget().deleteLater()
        
        for i, product in enumerate(products):
            row = QFrame()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 8, 0, 8)
            
            rank = QLabel(f"{i+1}")
            rank.setFixedSize(24, 24)
            rank.setAlignment(Qt.AlignCenter)
            rank.setStyleSheet(f"""
                background: {Colors.PRIMARY}20;
                color: {Colors.PRIMARY};
                border-radius: 4px;
                font-weight: bold;
            """)
            row_layout.addWidget(rank)
            
            name = QLabel(product.get('product__name', 'اسم المنتج'))
            name.setProperty("class", "subtitle")
            row_layout.addWidget(name, 1)
            
            sales = QLabel(f"{float(product.get('total_quantity', 0)):g} وحدة")
            row_layout.addWidget(sales)
            
            self.top_products_layout.addWidget(row)

    def _update_recent_activity(self, activities):
        """Update the recent activity list in the UI."""
        # Clear existing items (except title)
        while self.activity_layout.count() > 1:
            child = self.activity_layout.takeAt(1)
            if child.widget():
                child.widget().deleteLater()
        
        for i, activity in enumerate(activities):
            row = QFrame()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 12, 0, 12)
            
            icon = QLabel("📄")
            row_layout.addWidget(icon)
            
            desc = QLabel(f"فاتورة رقم {activity.get('invoice_number', '')} - {activity.get('customer__name') or 'نقدي'}")
            row_layout.addWidget(desc, 1)
            
            amount = QLabel(config.format_usd(float(activity.get('total_amount_usd', activity.get('total_amount', 0)) or 0)))
            amount.setStyleSheet(f"color: {Colors.SUCCESS}; font-weight: bold;")
            row_layout.addWidget(amount)
            
            # Simple date display (last 10 chars of created_at timestamp usually looks like HH:MM:SS)
            created_at = activity.get('created_at', '')
            time_str = ""
            if isinstance(created_at, str) and 'T' in created_at:
                time_str = created_at.split('T')[1][:5]
            
            time_label = QLabel(time_str)
            time_label.setProperty("class", "subtitle")
            row_layout.addWidget(time_label)
            
            self.activity_layout.addWidget(row)
            
            if i < len(activities) - 1:
                divider = QFrame()
                divider.setFixedHeight(1)
                divider.setStyleSheet(f"background: {Colors.LIGHT_BORDER};")
                self.activity_layout.addWidget(divider)
