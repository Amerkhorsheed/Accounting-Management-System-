from django.contrib import admin
from .models import (
    Supplier, PurchaseOrder, PurchaseOrderItem,
    GoodsReceivedNote, GRNItem, SupplierPayment
)


class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 0
    readonly_fields = ['subtotal', 'tax_amount', 'total']


class GRNItemInline(admin.TabularInline):
    model = GRNItem
    extra = 0


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'phone', 'current_balance', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'code', 'phone', 'email']
    ordering = ['name']


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'supplier', 'order_date', 'status', 'total_amount']
    list_filter = ['status', 'supplier', 'order_date']
    search_fields = ['order_number', 'supplier__name']
    inlines = [PurchaseOrderItemInline]
    ordering = ['-order_date']


@admin.register(GoodsReceivedNote)
class GRNAdmin(admin.ModelAdmin):
    list_display = ['grn_number', 'purchase_order', 'received_date', 'received_by']
    list_filter = ['received_date']
    search_fields = ['grn_number', 'purchase_order__order_number']
    inlines = [GRNItemInline]
    ordering = ['-received_date']


@admin.register(SupplierPayment)
class SupplierPaymentAdmin(admin.ModelAdmin):
    list_display = ['payment_number', 'supplier', 'payment_date', 'amount', 'payment_method']
    list_filter = ['payment_method', 'payment_date', 'supplier']
    search_fields = ['payment_number', 'supplier__name']
    ordering = ['-payment_date']
