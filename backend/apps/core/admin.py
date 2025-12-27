from django.contrib import admin
from .settings_models import SystemSettings, Currency, TaxRate


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ['key', 'value', 'description', 'updated_at']
    search_fields = ['key', 'description']
    ordering = ['key']


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'symbol', 'exchange_rate', 'is_primary', 'is_active']
    list_filter = ['is_primary', 'is_active']
    search_fields = ['code', 'name']
    ordering = ['-is_primary', 'code']


@admin.register(TaxRate)
class TaxRateAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'rate', 'is_default', 'is_active']
    list_filter = ['is_default', 'is_active']
    search_fields = ['name', 'code']
    ordering = ['-is_default', 'name']
