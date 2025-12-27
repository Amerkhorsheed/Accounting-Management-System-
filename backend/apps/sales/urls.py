"""
Sales URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CustomerViewSet, InvoiceViewSet, PaymentViewSet, SalesReturnViewSet

router = DefaultRouter()
router.register('customers', CustomerViewSet)
router.register('invoices', InvoiceViewSet)
router.register('payments', PaymentViewSet)
router.register('returns', SalesReturnViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
