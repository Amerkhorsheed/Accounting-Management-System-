"""
Expenses Views
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Sum, Count

from .models import ExpenseCategory, Expense
from .serializers import ExpenseCategorySerializer, ExpenseSerializer
from apps.core.decorators import handle_view_error


class ExpenseCategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for ExpenseCategory."""
    
    queryset = ExpenseCategory.objects.filter(is_active=True, is_deleted=False)
    serializer_class = ExpenseCategorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['parent', 'is_active']
    search_fields = ['name', 'description']

    def destroy(self, request, *args, **kwargs):
        """Soft delete the expense category instead of hard delete."""
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        """Perform soft delete using the model's soft_delete method."""
        instance.soft_delete(user=self.request.user)


class ExpenseViewSet(viewsets.ModelViewSet):
    """ViewSet for Expense."""
    
    queryset = Expense.objects.filter(is_deleted=False).select_related('category', 'created_by')
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'payment_method', 'is_approved']
    search_fields = ['expense_number', 'description', 'payee', 'reference']
    ordering_fields = ['expense_date', 'amount', 'created_at']
    ordering = ['-expense_date']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def destroy(self, request, *args, **kwargs):
        """Soft delete the expense instead of hard delete."""
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        """Perform soft delete using the model's soft_delete method."""
        instance.soft_delete(user=self.request.user)

    @handle_view_error
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve an expense."""
        expense = self.get_object()
        expense.is_approved = True
        expense.approved_by = request.user
        expense.save()
        return Response(ExpenseSerializer(expense).data)

    @handle_view_error
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get expense summary by category."""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        queryset = self.queryset.filter(is_approved=True)
        
        if start_date:
            queryset = queryset.filter(expense_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(expense_date__lte=end_date)
        
        summary = queryset.values('category__name').annotate(
            total=Sum('total_amount'),
            count=Count('id')
        ).order_by('-total')
        
        total = queryset.aggregate(total=Sum('total_amount'))['total'] or 0
        
        return Response({
            'total': total,
            'by_category': list(summary)
        })
