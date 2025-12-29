# Views Package
from .dashboard import DashboardView
from .inventory import ProductsView
from .inventory.stock_movements import StockMovementsView
from .sales import CustomersView, InvoicesView, POSView, SalesReturnsView
from .sales.payments import PaymentsView
from .purchases import SuppliersView, PurchaseOrdersView
from .expenses import ExpensesView
from .reports import ReportsView
from .settings import SettingsView
