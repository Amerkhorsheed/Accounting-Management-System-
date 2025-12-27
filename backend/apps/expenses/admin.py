from django.contrib import admin
from .models import ExpenseCategory, Expense


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'is_active']
    list_filter = ['is_active', 'parent']
    search_fields = ['name']


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['expense_number', 'category', 'expense_date', 'total_amount', 'is_approved']
    list_filter = ['is_approved', 'category', 'payment_method', 'expense_date']
    search_fields = ['expense_number', 'description', 'payee']
    ordering = ['-expense_date']
