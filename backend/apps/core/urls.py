"""
Core URLs - Settings and Configuration
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .settings_views import SystemSettingsViewSet, CurrencyViewSet, TaxRateViewSet, AppContextViewSet, DailyExchangeRateViewSet

router = DefaultRouter()
router.register('settings', SystemSettingsViewSet)
router.register('currencies', CurrencyViewSet)
router.register('taxes', TaxRateViewSet)
router.register('app-context', AppContextViewSet, basename='app-context')
router.register('daily-exchange-rates', DailyExchangeRateViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
