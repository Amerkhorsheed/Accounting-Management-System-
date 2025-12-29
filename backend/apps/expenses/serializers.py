"""
Expenses Serializers
"""
from rest_framework import serializers
from .models import ExpenseCategory, Expense


class ExpenseCategorySerializer(serializers.ModelSerializer):
    """Serializer for ExpenseCategory."""
    
    expenses_count = serializers.SerializerMethodField()
    children_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ExpenseCategory
        fields = ['id', 'name', 'parent', 'description', 'is_active', 'expenses_count', 'children_count']
        read_only_fields = ['id', 'expenses_count', 'children_count']
    
    def get_expenses_count(self, obj):
        """Get count of expenses in this category."""
        return obj.expenses.filter(is_deleted=False).count()
    
    def get_children_count(self, obj):
        """Get count of child categories."""
        return obj.children.filter(is_deleted=False, is_active=True).count()


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
