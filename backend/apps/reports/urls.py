"""
Reports URLs
"""
from django.urls import path
from .views import (
    DashboardView, SalesReportView, ProfitReportView,
    InventoryReportView, CustomerReportView, ReceivablesReportView,
    AgingReportView, SuppliersReportView, ExpensesReportView
)

urlpatterns = [
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('sales/', SalesReportView.as_view(), name='sales-report'),
    path('profit/', ProfitReportView.as_view(), name='profit-report'),
    path('inventory/', InventoryReportView.as_view(), name='inventory-report'),
    path('customers/', CustomerReportView.as_view(), name='customer-report'),
    path('receivables/', ReceivablesReportView.as_view(), name='receivables-report'),
    path('aging/', AgingReportView.as_view(), name='aging-report'),
    path('suppliers/', SuppliersReportView.as_view(), name='suppliers-report'),
    path('expenses/', ExpensesReportView.as_view(), name='expenses-report'),
]
