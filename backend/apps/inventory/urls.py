"""
Inventory URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers as nested_routers
from .views import (
    CategoryViewSet, UnitViewSet, ProductUnitViewSet, WarehouseViewSet,
    ProductViewSet, StockViewSet, StockMovementViewSet
)

router = DefaultRouter()
router.register('categories', CategoryViewSet)
router.register('units', UnitViewSet)
router.register('product-units', ProductUnitViewSet, basename='product-units')
router.register('warehouses', WarehouseViewSet)
router.register('products', ProductViewSet)
router.register('stock', StockViewSet)
router.register('movements', StockMovementViewSet)

# Nested routes for product units under products
products_router = nested_routers.NestedDefaultRouter(router, 'products', lookup='product')
products_router.register('units', ProductUnitViewSet, basename='product-units-nested')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(products_router.urls)),
]
