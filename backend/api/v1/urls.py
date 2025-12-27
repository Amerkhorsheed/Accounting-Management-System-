"""
API v1 URL Configuration
"""
from django.urls import path, include

urlpatterns = [
    # Core Settings (Currency, Tax, System Settings)
    path('core/', include('apps.core.urls')),
    
    # Authentication & Users
    path('auth/', include('apps.accounts.urls')),
    
    # Inventory Management
    path('inventory/', include('apps.inventory.urls')),
    
    # Purchase Management
    path('purchases/', include('apps.purchases.urls')),
    
    # Sales Management
    path('sales/', include('apps.sales.urls')),
    
    # Expense Management
    path('expenses/', include('apps.expenses.urls')),
    
    # Reports
    path('reports/', include('apps.reports.urls')),
]
