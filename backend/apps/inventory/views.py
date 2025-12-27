"""
Inventory Views - API Endpoints
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.shortcuts import get_object_or_404

from apps.core.decorators import handle_view_error
from .models import Category, Unit, ProductUnit, Warehouse, Product, Stock, StockMovement
from .serializers import (
    CategorySerializer, CategoryTreeSerializer,
    UnitSerializer, UnitCreateSerializer,
    ProductUnitSerializer, ProductUnitCreateSerializer,
    WarehouseSerializer,
    ProductListSerializer, ProductDetailSerializer, ProductCreateSerializer,
    StockSerializer, StockAdjustmentSerializer, StockMovementSerializer,
    BarcodeSearchSerializer
)
from .services import InventoryService


class CategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for Category management."""
    
    queryset = Category.objects.filter(is_active=True, is_deleted=False)
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['parent', 'is_active']
    search_fields = ['name', 'name_en', 'description']
    ordering_fields = ['name', 'sort_order', 'created_at']
    ordering = ['sort_order', 'name']

    def destroy(self, request, *args, **kwargs):
        """Soft delete the category instead of hard delete."""
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        """Perform soft delete using the model's soft_delete method."""
        instance.soft_delete(user=self.request.user)

    @action(detail=False, methods=['get'])
    def tree(self, request):
        """Get categories as a tree structure."""
        root_categories = self.queryset.filter(parent__isnull=True)
        serializer = CategoryTreeSerializer(root_categories, many=True)
        return Response(serializer.data)


class UnitViewSet(viewsets.ModelViewSet):
    """ViewSet for Unit management."""
    
    queryset = Unit.objects.filter(is_deleted=False)
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'name_en', 'symbol']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action in ['create', 'update', 'partial_update']:
            return UnitCreateSerializer
        return UnitSerializer

    def perform_create(self, serializer):
        """Save unit with created_by user."""
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        """Save unit with updated_by user."""
        serializer.save(updated_by=self.request.user)

    def destroy(self, request, *args, **kwargs):
        """
        Soft delete the unit if not in use.
        Returns error if unit is associated with any ProductUnit.
        """
        instance = self.get_object()
        
        # Check if unit is in use by any ProductUnit
        from .models import ProductUnit
        product_units_count = ProductUnit.objects.filter(
            unit=instance, 
            is_deleted=False
        ).count()
        
        if product_units_count > 0:
            return Response(
                {
                    'detail': 'لا يمكن حذف الوحدة لأنها مستخدمة في منتجات',
                    'code': 'UNIT_IN_USE',
                    'products_count': product_units_count
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Also check if unit is used directly by products (legacy)
        products_count = instance.products.filter(is_deleted=False).count()
        if products_count > 0:
            return Response(
                {
                    'detail': 'لا يمكن حذف الوحدة لأنها مستخدمة في منتجات',
                    'code': 'UNIT_IN_USE',
                    'products_count': products_count
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        """Perform soft delete using the model's soft_delete method."""
        instance.soft_delete(user=self.request.user)


class ProductUnitViewSet(viewsets.ModelViewSet):
    """
    ViewSet for ProductUnit management.
    Provides nested routes under products for managing product-specific units.
    """
    
    queryset = ProductUnit.objects.filter(is_deleted=False).select_related('product', 'unit')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['product', 'unit', 'is_base_unit', 'is_active']
    search_fields = ['unit__name', 'unit__symbol', 'barcode']
    ordering_fields = ['conversion_factor', 'sale_price', 'created_at']
    ordering = ['-is_base_unit', 'unit__name']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action in ['create', 'update', 'partial_update']:
            return ProductUnitCreateSerializer
        return ProductUnitSerializer

    def get_queryset(self):
        """
        Filter queryset by product_id if provided in URL kwargs.
        Supports nested routes: /products/{product_id}/units/
        """
        queryset = ProductUnit.objects.filter(is_deleted=False).select_related('product', 'unit')
        
        # Support nested route filtering
        product_id = self.kwargs.get('product_pk') or self.request.query_params.get('product')
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        
        return queryset

    def perform_create(self, serializer):
        """Save ProductUnit with created_by user."""
        # If product_pk is in URL, use it
        product_id = self.kwargs.get('product_pk')
        if product_id:
            product = get_object_or_404(Product, pk=product_id, is_deleted=False)
            serializer.save(created_by=self.request.user, product=product)
        else:
            serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        """Save ProductUnit with updated_by user."""
        serializer.save(updated_by=self.request.user)

    def destroy(self, request, *args, **kwargs):
        """
        Soft delete the ProductUnit.
        Prevents deletion of the base unit if it's the only unit or if other units exist.
        """
        instance = self.get_object()
        
        # Check if this is the base unit
        if instance.is_base_unit:
            # Check if there are other units for this product
            other_units = ProductUnit.objects.filter(
                product=instance.product,
                is_deleted=False
            ).exclude(pk=instance.pk).count()
            
            if other_units > 0:
                return Response(
                    {
                        'detail': 'لا يمكن حذف الوحدة الأساسية. يجب تعيين وحدة أخرى كوحدة أساسية أولاً',
                        'code': 'CANNOT_REMOVE_BASE_UNIT'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        """Perform soft delete using the model's soft_delete method."""
        instance.soft_delete(user=self.request.user)

    @action(detail=False, methods=['get'])
    def by_product(self, request):
        """
        Get all units for a specific product.
        Query param: product_id
        """
        product_id = request.query_params.get('product_id')
        if not product_id:
            return Response(
                {'detail': 'معرف المنتج مطلوب'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        product_units = self.get_queryset().filter(product_id=product_id)
        serializer = ProductUnitSerializer(product_units, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def set_base(self, request, pk=None):
        """
        Set this ProductUnit as the base unit for its product.
        This will unset any existing base unit.
        """
        instance = self.get_object()
        
        # Unset any existing base unit for this product
        ProductUnit.objects.filter(
            product=instance.product,
            is_base_unit=True,
            is_deleted=False
        ).exclude(pk=instance.pk).update(is_base_unit=False)
        
        # Set this as base unit with conversion factor 1
        instance.is_base_unit = True
        instance.conversion_factor = 1
        instance.save(update_fields=['is_base_unit', 'conversion_factor', 'updated_at'])
        
        serializer = ProductUnitSerializer(instance)
        return Response(serializer.data)


class WarehouseViewSet(viewsets.ModelViewSet):
    """ViewSet for Warehouse management."""
    
    queryset = Warehouse.objects.filter(is_active=True, is_deleted=False)
    serializer_class = WarehouseSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['is_default', 'is_active']
    search_fields = ['name', 'code', 'address']

    def destroy(self, request, *args, **kwargs):
        """Soft delete the warehouse instead of hard delete."""
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        """Perform soft delete using the model's soft_delete method."""
        instance.soft_delete(user=self.request.user)


class ProductViewSet(viewsets.ModelViewSet):
    """ViewSet for Product management."""
    
    queryset = Product.objects.filter(is_deleted=False).select_related('category', 'unit')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'product_type', 'is_active', 'is_taxable', 'track_stock']
    search_fields = ['name', 'name_en', 'code', 'barcode', 'description', 'brand']
    ordering_fields = ['name', 'code', 'sale_price', 'cost_price', 'created_at']
    ordering = ['name']

    def get_serializer_class(self):
        if self.action == 'list':
            return ProductListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ProductCreateSerializer
        return ProductDetailSerializer

    def get_queryset(self):
        """
        Filter out soft-deleted products.
        This ensures deleted products don't appear in any queries.
        """
        return Product.objects.filter(is_deleted=False).select_related('category', 'unit')

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    def destroy(self, request, *args, **kwargs):
        """
        Override destroy to perform soft delete instead of hard delete.
        Sets is_deleted=True and records deletion metadata.
        """
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        """
        Perform soft delete using the model's soft_delete method.
        """
        instance.soft_delete(user=self.request.user)

    @handle_view_error
    @action(detail=False, methods=['get', 'post'])
    def by_barcode(self, request):
        """
        Find product by barcode.
        Accepts both GET (with query params) and POST (with request body).
        """
        # Handle both GET query params and POST body
        if request.method == 'GET':
            data = request.query_params
        else:
            data = request.data
            
        serializer = BarcodeSearchSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        
        product = InventoryService.get_product_by_barcode(
            serializer.validated_data['barcode']
        )
        
        if product:
            return Response(ProductDetailSerializer(product).data)
        
        return Response(
            {'detail': 'المنتج غير موجود'},
            status=status.HTTP_404_NOT_FOUND
        )

    @handle_view_error
    @action(detail=True, methods=['get'])
    def stock(self, request, pk=None):
        """Get stock information for a product."""
        stock_info = InventoryService.get_product_stock(pk)
        return Response(stock_info)

    @handle_view_error
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Get products with low stock."""
        warehouse_id = request.query_params.get('warehouse')
        products = InventoryService.get_low_stock_products(warehouse_id)
        return Response(products)


class StockViewSet(viewsets.ModelViewSet):
    """ViewSet for Stock management."""
    
    queryset = Stock.objects.select_related('product', 'warehouse')
    serializer_class = StockSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['warehouse', 'product']
    search_fields = ['product__name', 'product__code', 'warehouse__name']

    @handle_view_error
    @action(detail=False, methods=['post'])
    def adjust(self, request):
        """Adjust stock level."""
        serializer = StockAdjustmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        stock = InventoryService.adjust_stock(
            product_id=serializer.validated_data['product_id'],
            warehouse_id=serializer.validated_data['warehouse_id'],
            quantity=serializer.validated_data['quantity'],
            adjustment_type=serializer.validated_data['adjustment_type'],
            reason=serializer.validated_data['reason'],
            user=request.user,
            notes=serializer.validated_data.get('notes')
        )
        return Response(StockSerializer(stock).data)

    @handle_view_error
    @action(detail=False, methods=['get'])
    def valuation(self, request):
        """Get stock valuation report."""
        warehouse_id = request.query_params.get('warehouse')
        method = request.query_params.get('method', 'average')
        
        valuation = InventoryService.get_stock_valuation(warehouse_id, method)
        return Response(valuation)


class StockMovementViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing stock movements (read-only)."""
    
    queryset = StockMovement.objects.select_related(
        'product', 'warehouse', 'created_by'
    )
    serializer_class = StockMovementSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['product', 'warehouse', 'movement_type', 'source_type']
    search_fields = ['product__name', 'reference_number', 'notes']
    ordering_fields = ['created_at', 'quantity']
    ordering = ['-created_at']
