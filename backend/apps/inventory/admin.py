from django.contrib import admin
from .models import Category, Unit, ProductUnit, Warehouse, Product, Stock, StockMovement


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'sort_order', 'is_active', 'created_at']
    list_filter = ['is_active', 'parent']
    search_fields = ['name', 'name_en', 'description']
    ordering = ['sort_order', 'name']


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ['name', 'symbol', 'name_en', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'name_en', 'symbol']


@admin.register(ProductUnit)
class ProductUnitAdmin(admin.ModelAdmin):
    list_display = ['product', 'unit', 'conversion_factor', 'is_base_unit', 'sale_price', 'cost_price', 'is_active']
    list_filter = ['is_base_unit', 'is_active', 'unit']
    search_fields = ['product__name', 'product__code', 'unit__name', 'barcode']
    raw_id_fields = ['product', 'unit']


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_default', 'manager', 'is_active']
    list_filter = ['is_default', 'is_active']
    search_fields = ['name', 'code', 'address']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'category', 'sale_price', 'cost_price', 'is_active']
    list_filter = ['category', 'product_type', 'is_active', 'is_taxable']
    search_fields = ['name', 'name_en', 'code', 'barcode', 'description']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['name']


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ['product', 'warehouse', 'quantity', 'reserved_quantity', 'updated_at']
    list_filter = ['warehouse']
    search_fields = ['product__name', 'product__code']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ['product', 'warehouse', 'movement_type', 'quantity', 'created_by', 'created_at']
    list_filter = ['movement_type', 'source_type', 'warehouse', 'created_at']
    search_fields = ['product__name', 'reference_number', 'notes']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
