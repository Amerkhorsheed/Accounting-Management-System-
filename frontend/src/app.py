"""
Main Application Window
"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QFrame, QLabel, QPushButton, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont, QIcon

from .config import config, Colors, Fonts
from .widgets.sidebar import Sidebar
from .widgets.header import Header
from .views.dashboard import DashboardView
from .views.inventory import ProductsView
from .views.inventory.stock_movements import StockMovementsView
from .views.sales import CustomersView, InvoicesView, POSView, SalesReturnsView
from .views.sales.payments import PaymentsView
from .views.purchases import SuppliersView, PurchaseOrdersView
from .views.expenses import ExpensesView
from .views.reports import ReportsView
from .views.settings import SettingsView
from .views.login import LoginDialog
from .styles.theme import ThemeManager
from .services.auth import AuthService


class MainApplication(QMainWindow):
    """Main application window with sidebar navigation."""
    
    theme_changed = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.current_user = None
        self.theme_manager = ThemeManager()
        self.setup_ui()
        self.apply_theme()
    
    def show(self):
        """Override show to display login dialog first."""
        # Show login dialog first
        login_dialog = LoginDialog(self)
        login_dialog.login_successful.connect(self.on_login_success)
        
        if login_dialog.exec():
            super().show()
            self.showMaximized()
            # Refresh dashboard on start
            self.dashboard_view.refresh()
        else:
            # User cancelled login, close app
            import sys
            sys.exit(0)
    
    def on_login_success(self, user: dict):
        """Handle successful login."""
        self.current_user = user
        self.header.set_user(user)
        
    def setup_ui(self):
        """Initialize the user interface."""
        # Window settings
        self.setWindowTitle("نظام إدارة المحاسبة")
        self.setMinimumSize(1200, 800)
        self.showMaximized()
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar
        self.sidebar = Sidebar()
        self.sidebar.navigation_clicked.connect(self.on_navigation)
        main_layout.addWidget(self.sidebar)
        
        # Content area
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Header
        self.header = Header()
        self.header.search_requested.connect(self.on_search)
        self.header.theme_toggled.connect(self.toggle_theme)
        content_layout.addWidget(self.header)
        
        # Stacked widget for views
        self.stack = QStackedWidget()
        self.setup_views()
        content_layout.addWidget(self.stack)
        
        main_layout.addWidget(content_widget, 1)
        
    def setup_views(self):
        """Create and add all views to the stack."""
        # Dashboard
        self.dashboard_view = DashboardView()
        # Connect dashboard receivables navigation (Requirements: 8.4)
        self.dashboard_view.navigate_to_receivables.connect(self._navigate_to_receivables_report)
        self.stack.addWidget(self.dashboard_view)
        
        # Inventory
        self.products_view = ProductsView()
        self.stack.addWidget(self.products_view)
        
        # Stock Movements - Requirements: 20.1 - Add Stock Movements under Inventory
        self.stock_movements_view = StockMovementsView()
        self.stack.addWidget(self.stock_movements_view)
        
        # Sales
        self.pos_view = POSView()
        self.stack.addWidget(self.pos_view)
        
        self.invoices_view = InvoicesView()
        self.stack.addWidget(self.invoices_view)
        
        self.customers_view = CustomersView()
        self.stack.addWidget(self.customers_view)
        
        # Sales Returns - Requirements: 20.1 - Add Sales Returns under Sales
        self.sales_returns_view = SalesReturnsView()
        self.stack.addWidget(self.sales_returns_view)
        
        # Payments - Requirements: 20.1 - Add Payments under Sales
        self.payments_view = PaymentsView()
        self.stack.addWidget(self.payments_view)
        
        # Purchases
        self.suppliers_view = SuppliersView()
        self.stack.addWidget(self.suppliers_view)
        
        self.purchase_orders_view = PurchaseOrdersView()
        self.stack.addWidget(self.purchase_orders_view)
        
        # Expenses
        self.expenses_view = ExpensesView()
        self.stack.addWidget(self.expenses_view)
        
        # Reports
        self.reports_view = ReportsView()
        self.stack.addWidget(self.reports_view)
        
        # Settings (includes Categories, Units, Warehouses, Expense Categories)
        # Requirements: 20.1 - Categories, Units, Warehouses, Expense Categories are under Settings
        self.settings_view = SettingsView()
        self.stack.addWidget(self.settings_view)
        
        # View mapping - Requirements: 20.2 - Register all new views in view stack
        self.views = {
            'dashboard': self.dashboard_view,
            'products': self.products_view,
            'stock_movements': self.stock_movements_view,
            'pos': self.pos_view,
            'invoices': self.invoices_view,
            'customers': self.customers_view,
            'sales_returns': self.sales_returns_view,
            'payments': self.payments_view,
            'suppliers': self.suppliers_view,
            'purchases': self.purchase_orders_view,
            'expenses': self.expenses_view,
            'reports': self.reports_view,
            'settings': self.settings_view,
        }
        
    def on_navigation(self, view_name: str):
        """Handle sidebar navigation."""
        if view_name in self.views:
            view = self.views[view_name]
            self.stack.setCurrentWidget(view)
            
            # Update header title - Requirements: 20.2 - Connect navigation signals
            titles = {
                'dashboard': 'لوحة التحكم',
                'products': 'المنتجات',
                'stock_movements': 'حركة المخزون',
                'pos': 'نقطة البيع',
                'invoices': 'الفواتير',
                'customers': 'العملاء',
                'sales_returns': 'مرتجعات المبيعات',
                'payments': 'المدفوعات',
                'suppliers': 'الموردون',
                'purchases': 'المشتريات',
                'expenses': 'المصروفات',
                'reports': 'التقارير',
                'settings': 'الإعدادات',
            }
            self.header.set_title(titles.get(view_name, ''))
            
            # Refresh view data
            if hasattr(view, 'refresh'):
                view.refresh()
        elif view_name == 'logout':
            self.logout()
    
    def _navigate_to_receivables_report(self):
        """
        Navigate to receivables report from dashboard.
        
        Requirements: 8.4 - Navigate to receivables report on card click
        """
        # Switch to reports view
        self.stack.setCurrentWidget(self.reports_view)
        self.header.set_title('التقارير')
        
        # Navigate to receivables report within reports view
        self.reports_view.go_to_receivables()
            
    def on_search(self, query: str):
        """Handle global search."""
        if not query or not query.strip():
            return
        
        query = query.strip()
        
        # Search products by barcode first
        from .services.api import api, ApiException
        try:
            product = api.get_product_by_barcode(query)
            if product:
                # Navigate to inventory and show product
                self.stack.setCurrentWidget(self.products_view)
                self.header.set_title('المنتجات')
                self.products_view.table.set_data([product])
                return
        except ApiException:
            pass
        
        # Search products by name
        try:
            response = api.get_products({'search': query})
            if isinstance(response, dict) and 'results' in response:
                products = response['results']
            else:
                products = response if isinstance(response, list) else []
            
            if products:
                self.stack.setCurrentWidget(self.products_view)
                self.header.set_title('المنتجات')
                self.products_view.table.set_data(products)
                return
        except ApiException:
            pass
        
        # Search customers
        try:
            response = api.get_customers({'search': query})
            if isinstance(response, dict) and 'results' in response:
                customers = response['results']
            else:
                customers = response if isinstance(response, list) else []
            
            if customers:
                self.stack.setCurrentWidget(self.customers_view)
                self.header.set_title('العملاء')
                self.customers_view.table.set_data(customers)
                return
        except ApiException:
            pass
        
        # No results found
        from .widgets.dialogs import MessageDialog
        MessageDialog.info(self, "البحث", f"لم يتم العثور على نتائج لـ: {query}")
        
    def toggle_theme(self):
        """Toggle between light and dark theme."""
        if config.THEME == 'light':
            config.THEME = 'dark'
        else:
            config.THEME = 'light'
        self.apply_theme()
        self.theme_changed.emit(config.THEME)
        
    def apply_theme(self):
        """Apply the current theme."""
        stylesheet = self.theme_manager.get_stylesheet(config.THEME)
        self.setStyleSheet(stylesheet)
        
    def logout(self):
        """Handle user logout."""
        reply = QMessageBox.question(
            self, 
            'تسجيل الخروج',
            'هل أنت متأكد من تسجيل الخروج؟',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Clear session
            self.current_user = None
            # Show login or close
            self.close()
