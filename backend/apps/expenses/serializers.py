"""
Expenses Serializers
"""
from rest_framework import serializers
from .models import ExpenseCategory, Expense


class ExpenseCategorySerializer(serializers.ModelSerializer):
    """Serializer for ExpenseCategory."""
    
    class Meta:
        model = ExpenseCategory
        fields = ['id', 'name', 'parent', 'description', 'is_active']
        read_only_fields = ['id']


class ExpenseSerializer(serializers.ModelSerializer):
    """Serializer for Expense."""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.full_name', read_only=True)
    
    class Meta:
        model = Expense
        fields = [
            'id', 'expense_number', 'category', 'category_name',
            'expense_date', 'amount', 'tax_amount', 'total_amount',
            'payment_method', 'payment_method_display',
            'payee', 'reference', 'description', 'attachment', 'notes',
            'is_approved', 'approved_by', 'approved_by_name',
            'created_by', 'created_by_name', 'created_at'
        ]
        read_only_fields = ['id', 'expense_number', 'total_amount', 'created_at']
