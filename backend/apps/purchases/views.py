"""
Purchases Views - API Endpoints
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.core.decorators import handle_view_error
from .models import (
    Supplier, PurchaseOrder, PurchaseOrderItem,
    GoodsReceivedNote, SupplierPayment
)
from .serializers import (
    SupplierListSerializer, SupplierDetailSerializer,
    PurchaseOrderListSerializer, PurchaseOrderDetailSerializer,
    PurchaseOrderCreateSerializer, GRNSerializer, SupplierPaymentSerializer
)
from .services import PurchaseService


class SupplierViewSet(viewsets.ModelViewSet):
    """ViewSet for Supplier management."""
    
    queryset = Supplier.objects.filter(is_deleted=False)
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'name_en', 'code', 'phone', 'mobile', 'email']
    ordering_fields = ['name', 'code', 'current_balance', 'created_at']
    ordering = ['name']

    def get_serializer_class(self):
        if self.action == 'list':
            return SupplierListSerializer
        return SupplierDetailSerializer

    def perform_create(self, serializer):
        """Create supplier with auto-generated code and audit fields."""
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        """Update supplier with audit fields."""
        serializer.save(updated_by=self.request.user)

    def destroy(self, request, *args, **kwargs):
        """
        Soft delete the supplier instead of hard delete.
        
        Requirements: 3.4, 3.5 - Deletion protection for suppliers with purchase orders
        """
        instance = self.get_object()
        
        # Check for purchase orders (non-deleted purchase orders)
        existing_orders = PurchaseOrder.objects.filter(
            supplier=instance,
            is_deleted=False
        )
        
        if existing_orders.exists():
            return Response(
                {
                    'detail': 'لا يمكن حذف المورد لوجود أوامر شراء مرتبطة به',
                    'code': 'DELETION_PROTECTED',
                    'order_count': existing_orders.count()
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        """Perform soft delete using the model's soft_delete method."""
        instance.soft_delete(user=self.request.user)

    @action(detail=True, methods=['get'])
    @handle_view_error
    def statement(self, request, pk=None):
        """Get supplier account statement."""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        statement = PurchaseService.get_supplier_statement(pk, start_date, end_date)
        return Response(statement)


class PurchaseOrderViewSet(viewsets.ModelViewSet):
    """ViewSet for PurchaseOrder management."""
    
    queryset = PurchaseOrder.objects.filter(is_deleted=False).select_related(
        'supplier', 'warehouse', 'created_by', 'approved_by'
    )
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['supplier', 'warehouse', 'status']
    search_fields = ['order_number', 'supplier__name', 'reference']
    ordering_fields = ['order_date', 'order_number', 'total_amount']
    ordering = ['-order_date', '-order_number']

    def get_serializer_class(self):
        if self.action == 'list':
            return PurchaseOrderListSerializer
        elif self.action == 'create':
            return PurchaseOrderCreateSerializer
        return PurchaseOrderDetailSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def destroy(self, request, *args, **kwargs):
        """Soft delete the purchase order instead of hard delete."""
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        """Perform soft delete using the model's soft_delete method."""
        instance.soft_delete(user=self.request.user)

    @action(detail=True, methods=['post'])
    @handle_view_error
    def approve(self, request, pk=None):
        """Approve a purchase order."""
        po = PurchaseService.approve_purchase_order(pk, request.user)
        return Response(PurchaseOrderDetailSerializer(po).data)

    @action(detail=True, methods=['post'])
    @handle_view_error
    def mark_ordered(self, request, pk=None):
        """
        Mark a purchase order as ordered.
        
        Requirements: 12.4 - Status actions
        """
        po = PurchaseService.mark_purchase_order_ordered(pk, request.user)
        return Response(PurchaseOrderDetailSerializer(po).data)

    @action(detail=True, methods=['post'])
    @handle_view_error
    def receive(self, request, pk=None):
        """Receive goods against PO."""
        grn = PurchaseService.receive_goods(
            po_id=pk,
            received_date=request.data.get('received_date'),
            items=request.data.get('items', []),
            supplier_invoice_no=request.data.get('supplier_invoice_no'),
            notes=request.data.get('notes'),
            user=request.user
        )
        return Response(GRNSerializer(grn).data)


class GRNViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing GRNs."""
    
    queryset = GoodsReceivedNote.objects.select_related(
        'purchase_order', 'received_by'
    ).prefetch_related('items')
    serializer_class = GRNSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['purchase_order']
    search_fields = ['grn_number', 'purchase_order__order_number', 'supplier_invoice_no']
    ordering = ['-received_date', '-grn_number']


class SupplierPaymentViewSet(viewsets.ModelViewSet):
    """ViewSet for SupplierPayment management."""
    
    queryset = SupplierPayment.objects.filter(is_deleted=False).select_related(
        'supplier', 'purchase_order', 'created_by'
    )
    serializer_class = SupplierPaymentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {
        'supplier': ['exact'],
        'payment_method': ['exact'],
        'purchase_order': ['exact'],
        'transaction_currency': ['exact'],
        'payment_date': ['gte', 'lte'],
    }
    search_fields = ['payment_number', 'supplier__name', 'reference']
    ordering = ['-payment_date', '-payment_number']

    def create(self, request, *args, **kwargs):
        """Create supplier payment using PurchaseService for proper balance updates."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        payment = PurchaseService.make_supplier_payment(
            supplier_id=data['supplier'].id,
            payment_date=data['payment_date'],
            amount=data['amount'],
            payment_method=data['payment_method'],
            purchase_order_id=data.get('purchase_order').id if data.get('purchase_order') else None,
            transaction_currency=data.get('transaction_currency') or 'USD',
            fx_rate_date=data.get('fx_rate_date'),
            usd_to_syp_old_snapshot=data.get('usd_to_syp_old_snapshot'),
            usd_to_syp_new_snapshot=data.get('usd_to_syp_new_snapshot'),
            reference=data.get('reference'),
            notes=data.get('notes'),
            user=request.user
        )

        output_serializer = SupplierPaymentSerializer(payment)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def destroy(self, request, *args, **kwargs):
        """Soft delete the supplier payment instead of hard delete."""
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        """Perform soft delete using the model's soft_delete method."""
        instance.soft_delete(user=self.request.user)
