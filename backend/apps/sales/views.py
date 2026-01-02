"""
Sales Views - API Endpoints
"""
from django.db import models
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.core.decorators import handle_view_error
from .models import Customer, Invoice, Payment, SalesReturn
from .serializers import (
    CustomerListSerializer, CustomerDetailSerializer,
    InvoiceListSerializer, InvoiceDetailSerializer, InvoiceCreateSerializer,
    PaymentSerializer, SalesReturnSerializer, SalesReturnCreateSerializer,
    PaymentAllocationSerializer, PaymentWithAllocationsSerializer,
    CollectPaymentWithAllocationSerializer, UnpaidInvoiceSerializer
)
from .services import SalesService


class CustomerViewSet(viewsets.ModelViewSet):
    """ViewSet for Customer management."""
    
    queryset = Customer.objects.filter(is_deleted=False)
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['customer_type', 'salesperson', 'is_active']
    search_fields = ['name', 'name_en', 'code', 'phone', 'mobile', 'email', 'tax_number']
    ordering_fields = ['name', 'code', 'current_balance', 'created_at']
    ordering = ['name']

    def get_serializer_class(self):
        if self.action == 'list':
            return CustomerListSerializer
        return CustomerDetailSerializer

    def perform_create(self, serializer):
        """Create customer with auto-generated code and audit fields."""
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        """Update customer with audit fields."""
        serializer.save(updated_by=self.request.user)

    def destroy(self, request, *args, **kwargs):
        """
        Soft delete the customer instead of hard delete.
        
        Requirements: 1.4, 1.5 - Deletion protection for customers with outstanding invoices
        """
        instance = self.get_object()
        
        # Check for outstanding invoices (non-cancelled, non-deleted invoices with remaining balance)
        outstanding_invoices = Invoice.objects.filter(
            customer=instance,
            is_deleted=False
        ).exclude(
            status='cancelled'
        ).filter(
            total_amount__gt=models.F('paid_amount')
        )
        
        if outstanding_invoices.exists():
            return Response(
                {
                    'detail': 'لا يمكن حذف العميل لوجود فواتير مستحقة',
                    'code': 'DELETION_PROTECTED',
                    'outstanding_count': outstanding_invoices.count()
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        """Perform soft delete using the model's soft_delete method."""
        instance.soft_delete(user=self.request.user)

    @handle_view_error
    @action(detail=True, methods=['get'])
    def statement(self, request, pk=None):
        """Get customer account statement."""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        statement = SalesService.get_customer_statement(pk, start_date, end_date)
        return Response(statement)

    @handle_view_error
    @action(detail=True, methods=['get'])
    def invoices(self, request, pk=None):
        """Get customer invoices."""
        invoices = Invoice.objects.filter(customer_id=pk, is_deleted=False)
        serializer = InvoiceListSerializer(invoices, many=True)
        return Response(serializer.data)


class InvoiceViewSet(viewsets.ModelViewSet):
    """ViewSet for Invoice management."""
    
    queryset = Invoice.objects.filter(is_deleted=False).select_related(
        'customer', 'warehouse', 'created_by'
    )
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['customer', 'warehouse', 'status', 'invoice_type']
    search_fields = ['invoice_number', 'customer__name', 'customer__code']
    ordering_fields = ['invoice_date', 'invoice_number', 'total_amount']
    ordering = ['-invoice_date', '-invoice_number']

    def get_serializer_class(self):
        if self.action == 'list':
            return InvoiceListSerializer
        elif self.action == 'create':
            return InvoiceCreateSerializer
        return InvoiceDetailSerializer

    def create(self, request, *args, **kwargs):
        """
        Create invoice and return full details for receipt printing.
        
        Returns InvoiceDetailSerializer data instead of InvoiceCreateSerializer
        to include all fields needed for receipt printing (items with product_name, etc.)
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # Return full invoice details using InvoiceDetailSerializer
        # This includes items with product_name needed for receipt printing
        invoice = serializer.instance
        detail_serializer = InvoiceDetailSerializer(invoice)
        headers = self.get_success_headers(detail_serializer.data)
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        """Update invoice with audit fields."""
        serializer.save(updated_by=self.request.user)

    def destroy(self, request, *args, **kwargs):
        """Soft delete the invoice instead of hard delete."""
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        """Perform soft delete using the model's soft_delete method."""
        instance.soft_delete(user=self.request.user)

    @handle_view_error
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """Confirm an invoice."""
        invoice = SalesService.confirm_invoice(pk, request.user)
        return Response(InvoiceDetailSerializer(invoice).data)

    @handle_view_error
    @action(detail=True, methods=['get'])
    def profit(self, request, pk=None):
        """Get invoice profit analysis."""
        profit_data = SalesService.get_invoice_profit(pk)
        return Response(profit_data)

    @handle_view_error
    @action(detail=True, methods=['post'])
    def return_items(self, request, pk=None):
        """Create a sales return."""
        try:
            payload = request.data.copy()
        except Exception:
            payload = dict(request.data)
        payload['original_invoice'] = pk

        serializer = SalesReturnCreateSerializer(
            data=payload,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        sales_return = serializer.save()
        return Response(SalesReturnSerializer(sales_return).data)

    @handle_view_error
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel an invoice and reverse all effects.
        
        Request body:
            reason: Required - Reason for cancellation
            
        Requirements: 4.4, 4.5
        - Validates invoice can be cancelled (confirmed, paid, or partial status)
        - Reverses stock movements (adds stock back)
        - Reverses customer balance changes
        - Updates invoice status to cancelled
        """
        reason = request.data.get('reason')
        
        invoice = SalesService.cancel_invoice(
            invoice_id=pk,
            reason=reason,
            user=request.user
        )
        return Response(InvoiceDetailSerializer(invoice).data)


class PaymentViewSet(viewsets.ModelViewSet):
    """ViewSet for Payment management."""
    
    queryset = Payment.objects.filter(is_deleted=False).select_related('customer', 'invoice')
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['customer', 'payment_method', 'invoice']
    search_fields = ['payment_number', 'customer__name', 'reference']
    ordering = ['-payment_date', '-payment_number']

    def get_serializer_class(self):
        if self.action == 'collect_with_allocation':
            return CollectPaymentWithAllocationSerializer
        return PaymentSerializer

    def destroy(self, request, *args, **kwargs):
        """Soft delete the payment instead of hard delete."""
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        """Perform soft delete using the model's soft_delete method."""
        instance.soft_delete(user=self.request.user)

    def create(self, request, *args, **kwargs):
        """Create payment using SalesService for proper balance updates."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        
        # Use service for proper balance updates
        payment = SalesService.receive_payment(
            customer_id=data['customer'].id,
            payment_date=data['payment_date'],
            amount=data['amount'],
            payment_method=data['payment_method'],
            invoice_id=data.get('invoice').id if data.get('invoice') else None,
            transaction_currency=data.get('transaction_currency') or 'SYP_OLD',
            fx_rate_date=data.get('fx_rate_date'),
            usd_to_syp_old_snapshot=data.get('usd_to_syp_old_snapshot'),
            usd_to_syp_new_snapshot=data.get('usd_to_syp_new_snapshot'),
            reference=data.get('reference'),
            notes=data.get('notes'),
            user=request.user
        )
        
        # Return the created payment with proper serialization
        output_serializer = PaymentSerializer(payment)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    @handle_view_error
    @action(detail=False, methods=['get'])
    def customer_unpaid_invoices(self, request):
        """
        Get list of unpaid/partial invoices for a customer.
        
        Query params:
            customer_id: Required - The customer's ID
            
        Returns list of invoices with id, number, date, total, paid, remaining.
        Requirements: 2.1, 7.1, 7.3
        """
        customer_id = request.query_params.get('customer_id')
        if not customer_id:
            return Response(
                {'detail': 'يجب تحديد العميل (customer_id)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from .credit_service import CreditService
        invoices = CreditService.get_customer_unpaid_invoices(int(customer_id))
        
        serializer = UnpaidInvoiceSerializer(invoices, many=True)
        return Response(serializer.data)

    @handle_view_error
    @action(detail=True, methods=['post'])
    def allocate(self, request, pk=None):
        """
        Allocate payment to specific invoices.
        
        Request body:
            allocations: List of {invoice_id, amount} objects
            auto_allocate: Boolean - if true, uses FIFO strategy
            
        Requirements: 7.1, 7.4, 7.5
        """
        from .credit_service import CreditService
        
        allocations_data = request.data.get('allocations', [])
        auto_allocate = request.data.get('auto_allocate', False)
        
        created_allocations = CreditService.allocate_payment(
            payment_id=int(pk),
            allocations=allocations_data if not auto_allocate else None,
            auto_allocate=auto_allocate
        )
        
        serializer = PaymentAllocationSerializer(created_allocations, many=True)
        return Response(serializer.data)

    @handle_view_error
    @action(detail=False, methods=['post'])
    def collect_with_allocation(self, request):
        """
        Create payment with invoice allocations in one transaction.
        
        Request body:
            customer: Customer ID
            payment_date: Date of payment
            amount: Payment amount
            payment_method: Payment method (cash, card, bank, check, credit)
            reference: Optional reference number
            notes: Optional notes
            allocations: Optional list of {invoice_id, amount} objects
            auto_allocate: Boolean - if true, uses FIFO strategy
            
        Requirements: 2.1, 7.1, 7.3
        """
        from .credit_service import CreditService
        
        serializer = CollectPaymentWithAllocationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        # Create the payment first
        payment = SalesService.receive_payment(
            customer_id=data['customer'].id,
            payment_date=data['payment_date'],
            amount=data['amount'],
            payment_method=data['payment_method'],
            invoice_id=None,  # No single invoice - using allocations
            transaction_currency=data.get('transaction_currency') or 'SYP_OLD',
            fx_rate_date=data.get('fx_rate_date'),
            usd_to_syp_old_snapshot=data.get('usd_to_syp_old_snapshot'),
            usd_to_syp_new_snapshot=data.get('usd_to_syp_new_snapshot'),
            reference=data.get('reference'),
            notes=data.get('notes'),
            user=request.user
        )
        
        # Allocate the payment
        allocations_data = data.get('allocations', [])
        auto_allocate = data.get('auto_allocate', False)
        
        if allocations_data or auto_allocate:
            CreditService.allocate_payment(
                payment_id=payment.id,
                allocations=allocations_data if not auto_allocate else None,
                auto_allocate=auto_allocate
            )
        
        # Return payment with allocations
        payment.refresh_from_db()
        output_serializer = PaymentWithAllocationsSerializer(payment)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


class SalesReturnViewSet(viewsets.ModelViewSet):
    """
    ViewSet for sales returns management.
    
    Supports:
    - GET: List all sales returns
    - GET /{id}: Get sales return details
    - POST: Create a new sales return
    
    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9
    """
    
    queryset = SalesReturn.objects.select_related('original_invoice').prefetch_related('items')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['original_invoice']
    search_fields = ['return_number', 'original_invoice__invoice_number', 'reason']
    ordering = ['-return_date', '-return_number']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return SalesReturnCreateSerializer
        return SalesReturnSerializer

    def create(self, request, *args, **kwargs):
        """
        Create a new sales return.
        
        Request body:
            original_invoice: Invoice ID
            return_date: Date of return
            reason: Required - Reason for return
            notes: Optional notes
            items: List of items to return
                - invoice_item_id: ID of the invoice item
                - quantity: Quantity to return
                - reason: Optional reason for this item
        
        Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sales_return = serializer.save()
        
        # Return the created sales return with full details
        output_serializer = SalesReturnSerializer(sales_return)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)
