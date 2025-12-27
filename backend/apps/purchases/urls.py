"""
Purchases URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SupplierViewSet, PurchaseOrderViewSet,
    GRNViewSet, SupplierPaymentViewSet
)

router = DefaultRouter()
router.register('suppliers', SupplierViewSet)
router.register('orders', PurchaseOrderViewSet)
router.register('grn', GRNViewSet)
router.register('payments', SupplierPaymentViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
