from django.contrib import admin
from .models import Customer, Invoice, InvoiceItem, Payment, SalesReturn, SalesReturnItem


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 0
    readonly_fields = ['subtotal', 'tax_amount', 'total', 'profit']


class SalesReturnItemInline(admin.TabularInline):
    model = SalesReturnItem
    extra = 0


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'customer_type', 'phone', 'current_balance', 'is_active']
    list_filter = ['customer_type', 'is_active', 'salesperson']
    search_fields = ['name', 'code', 'phone', 'email']
    ordering = ['name']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'customer', 'invoice_date', 'invoice_type', 'status', 'total_amount']
    list_filter = ['status', 'invoice_type', 'customer', 'invoice_date']
    search_fields = ['invoice_number', 'customer__name']
    inlines = [InvoiceItemInline]
    ordering = ['-invoice_date']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['payment_number', 'customer', 'payment_date', 'amount', 'payment_method']
    list_filter = ['payment_method', 'payment_date', 'customer']
    search_fields = ['payment_number', 'customer__name']
    ordering = ['-payment_date']


@admin.register(SalesReturn)
class SalesReturnAdmin(admin.ModelAdmin):
    list_display = ['return_number', 'original_invoice', 'return_date', 'total_amount']
    list_filter = ['return_date']
    search_fields = ['return_number', 'original_invoice__invoice_number']
    inlines = [SalesReturnItemInline]
    ordering = ['-return_date']
