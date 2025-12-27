"""
Core URLs - Settings and Configuration
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .settings_views import SystemSettingsViewSet, CurrencyViewSet, TaxRateViewSet

router = DefaultRouter()
router.register('settings', SystemSettingsViewSet)
router.register('currencies', CurrencyViewSet)
router.register('taxes', TaxRateViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
