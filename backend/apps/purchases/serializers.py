"""
Purchases Serializers
"""
from rest_framework import serializers
from .models import (
    Supplier, PurchaseOrder, PurchaseOrderItem,
    GoodsReceivedNote, GRNItem, SupplierPayment
)


class SupplierListSerializer(serializers.ModelSerializer):
    """Serializer for Supplier list view."""
    
    class Meta:
        model = Supplier
        fields = [
            'id', 'code', 'name', 'name_en', 'phone', 'mobile', 'email',
            'current_balance', 'credit_limit', 'is_active'
        ]


class SupplierDetailSerializer(serializers.ModelSerializer):
    """Serializer for Supplier detail view."""
    
    full_address = serializers.CharField(read_only=True)
    
    class Meta:
        model = Supplier
        fields = [
            'id', 'code', 'name', 'name_en', 'tax_number', 'commercial_register',
            'contact_person', 'phone', 'mobile', 'email', 'fax', 'website',
            'address', 'city', 'region', 'postal_code', 'country', 'full_address',
            'payment_terms', 'credit_limit', 'opening_balance', 'current_balance',
            'notes', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'code', 'current_balance', 'created_at', 'updated_at']
        extra_kwargs = {
            'name_en': {'required': False, 'allow_blank': True},
            'tax_number': {'required': False, 'allow_blank': True},
            'commercial_register': {'required': False, 'allow_blank': True},
            'contact_person': {'required': False, 'allow_blank': True},
            'phone': {'required': False, 'allow_blank': True},
            'mobile': {'required': False, 'allow_blank': True},
            'email': {'required': False, 'allow_blank': True},
            'fax': {'required': False, 'allow_blank': True},
            'website': {'required': False, 'allow_blank': True},
            'address': {'required': False, 'allow_blank': True},
            'city': {'required': False, 'allow_blank': True},
            'region': {'required': False, 'allow_blank': True},
            'postal_code': {'required': False, 'allow_blank': True},
            'country': {'required': False, 'allow_blank': True},
            'payment_terms': {'required': False},
            'credit_limit': {'required': False},
            'opening_balance': {'required': False},
            'notes': {'required': False, 'allow_blank': True},
            'is_active': {'required': False},
        }


class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    """Serializer for PurchaseOrder items."""
    
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_code = serializers.CharField(source='product.code', read_only=True)
    unit_name = serializers.SerializerMethodField()
    unit_symbol = serializers.SerializerMethodField()
    subtotal = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    discount_amount = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    tax_amount = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    total = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    remaining_quantity = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    
    class Meta:
        model = PurchaseOrderItem
        fields = [
            'id', 'product', 'product_name', 'product_code',
            'product_unit', 'unit_name', 'unit_symbol',
            'quantity', 'base_quantity', 'received_quantity', 'remaining_quantity',
            'unit_price', 'discount_percent', 'tax_rate',
            'subtotal', 'discount_amount', 'tax_amount', 'total', 'notes'
        ]
    
    def get_unit_name(self, obj):
        """Get the unit name from product_unit or product's default unit."""
        if obj.product_unit:
            return obj.product_unit.unit.name
        return obj.product.unit.name if obj.product else None
    
    def get_unit_symbol(self, obj):
        """Get the unit symbol from product_unit or product's default unit."""
        if obj.product_unit:
            return obj.product_unit.unit.symbol
        return obj.product.unit.symbol if obj.product else None


class PurchaseOrderListSerializer(serializers.ModelSerializer):
    """Serializer for PurchaseOrder list view."""
    
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    supplier_code = serializers.CharField(source='supplier.code', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    remaining_amount = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    
    class Meta:
        model = PurchaseOrder
        fields = [
            'id', 'order_number', 'supplier', 'supplier_name', 'supplier_code',
            'warehouse', 'warehouse_name', 'order_date', 'expected_date',
            'status', 'status_display', 'subtotal', 'discount_amount',
            'tax_amount', 'total_amount', 'paid_amount', 'remaining_amount'
        ]


class PurchaseOrderDetailSerializer(serializers.ModelSerializer):
    """Serializer for PurchaseOrder detail view."""
    
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    remaining_amount = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    items = PurchaseOrderItemSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.full_name', read_only=True)
    
    class Meta:
        model = PurchaseOrder
        fields = [
            'id', 'order_number', 'supplier', 'supplier_name',
            'warehouse', 'warehouse_name',
            'order_date', 'expected_date', 'status', 'status_display',
            'subtotal', 'discount_amount', 'tax_amount', 'total_amount',
            'paid_amount', 'remaining_amount',
            'reference', 'notes',
            'created_by', 'created_by_name', 'created_at',
            'approved_by', 'approved_by_name', 'approved_at',
            'items'
        ]
        read_only_fields = ['id', 'order_number', 'subtotal', 'tax_amount', 'total_amount', 'created_at']


class PurchaseOrderItemCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating PurchaseOrder items (write-only)."""
    
    class Meta:
        model = PurchaseOrderItem
        fields = [
            'product', 'product_unit', 'quantity', 'unit_price',
            'discount_percent', 'tax_rate', 'notes'
        ]
        extra_kwargs = {
            'product_unit': {'required': False, 'allow_null': True},
            'discount_percent': {'required': False},
            'tax_rate': {'required': False},
            'notes': {'required': False},
        }


class PurchaseOrderCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating PurchaseOrder."""
    
    items = PurchaseOrderItemCreateSerializer(many=True)
    # Non-model fields for auto-approval
    confirm = serializers.BooleanField(required=False, default=False, write_only=True)
    
    class Meta:
        model = PurchaseOrder
        fields = [
            'supplier', 'warehouse', 'order_date', 'expected_date',
            'discount_amount', 'reference', 'notes', 'items', 'confirm'
        ]

    def validate_items(self, value):
        """Validate that at least one item is provided."""
        if not value:
            raise serializers.ValidationError("At least one item is required.")
        return value

    def create(self, validated_data):
        from django.db import transaction
        from django.utils import timezone
        from decimal import Decimal
        from apps.inventory.services import InventoryService
        from apps.inventory.models import StockMovement, ProductUnit
        
        items_data = validated_data.pop('items')
        # Pop non-model fields
        confirm = validated_data.pop('confirm', False)
        
        with transaction.atomic():
            # Create the purchase order
            purchase_order = PurchaseOrder.objects.create(**validated_data)
            user = self.context.get('request').user if self.context.get('request') else None
            
            # Create all items
            for item_data in items_data:
                product = item_data.get('product')
                product_unit = item_data.get('product_unit')
                quantity = Decimal(str(item_data.get('quantity', 0)))
                
                # Calculate base_quantity based on product_unit or default to base unit
                # Requirements: 4.4, 4.6
                if product_unit:
                    base_quantity = product_unit.convert_to_base(quantity)
                else:
                    # Default to base unit - find the base unit for this product
                    base_unit = ProductUnit.objects.filter(
                        product=product,
                        is_base_unit=True,
                        is_deleted=False
                    ).first()
                    
                    if base_unit:
                        base_quantity = base_unit.convert_to_base(quantity)
                    else:
                        # No ProductUnit configured, use quantity as-is (legacy behavior)
                        base_quantity = quantity
                
                # Set default discount_percent if not provided
                if 'discount_percent' not in item_data or item_data.get('discount_percent') is None:
                    item_data['discount_percent'] = Decimal('0.00')
                
                # Set default tax_rate from product if not provided
                if 'tax_rate' not in item_data or item_data.get('tax_rate') is None:
                    if product and product.is_taxable:
                        item_data['tax_rate'] = product.tax_rate
                    else:
                        item_data['tax_rate'] = Decimal('15.00')  # Default tax rate
                
                # Add base_quantity to item_data
                item_data['base_quantity'] = base_quantity
                
                PurchaseOrderItem.objects.create(purchase_order=purchase_order, **item_data)
            
            # Calculate totals after all items are created
            purchase_order.calculate_totals()
            
            # Auto-confirm: approve and receive goods immediately
            if confirm:
                # Approve the order
                purchase_order.status = PurchaseOrder.Status.APPROVED
                purchase_order.approved_by = user
                purchase_order.approved_at = timezone.now()
                purchase_order.save()
                
                # Create GRN and receive all items
                grn = GoodsReceivedNote.objects.create(
                    purchase_order=purchase_order,
                    received_date=purchase_order.order_date,
                    received_by=user,
                    created_by=user
                )
                
                total_received_value = Decimal('0')
                
                # Receive all items and update stock
                for po_item in purchase_order.items.all():
                    # Create GRN item
                    GRNItem.objects.create(
                        grn=grn,
                        po_item=po_item,
                        product=po_item.product,
                        quantity_received=po_item.quantity,
                        created_by=user
                    )
                    
                    # Mark as fully received
                    po_item.received_quantity = po_item.quantity
                    po_item.save()
                    
                    # Calculate value for supplier balance
                    total_received_value += po_item.quantity * po_item.unit_price
                    
                    # Use base_quantity for stock addition (Requirements: 4.4)
                    stock_quantity = po_item.base_quantity if po_item.base_quantity else po_item.quantity
                    
                    # Add stock using base_quantity
                    InventoryService.add_stock(
                        product_id=po_item.product_id,
                        warehouse_id=purchase_order.warehouse_id,
                        quantity=stock_quantity,
                        unit_cost=po_item.unit_price,
                        source_type=StockMovement.SourceType.PURCHASE,
                        reference_number=grn.grn_number,
                        reference_type='GRN',
                        reference_id=grn.id,
                        user=user,
                        notes=f"استلام من أمر الشراء {purchase_order.order_number}"
                    )
                
                # Update PO status to received
                purchase_order.status = PurchaseOrder.Status.RECEIVED
                purchase_order.save()
                
                # Update supplier balance (increase what we owe them)
                supplier = purchase_order.supplier
                supplier.current_balance += total_received_value
                supplier.save()
        
        return purchase_order


class GRNItemSerializer(serializers.ModelSerializer):
    """Serializer for GRN items."""
    
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = GRNItem
        fields = ['id', 'po_item', 'product', 'product_name', 'quantity_received', 'notes']


class GRNSerializer(serializers.ModelSerializer):
    """Serializer for GoodsReceivedNote."""
    
    po_number = serializers.CharField(source='purchase_order.order_number', read_only=True)
    items = GRNItemSerializer(many=True, read_only=True)
    received_by_name = serializers.CharField(source='received_by.full_name', read_only=True)
    
    class Meta:
        model = GoodsReceivedNote
        fields = [
            'id', 'grn_number', 'purchase_order', 'po_number',
            'received_date', 'supplier_invoice_no', 'notes',
            'received_by', 'received_by_name', 'created_at', 'items'
        ]
        read_only_fields = ['id', 'grn_number', 'created_at']


class SupplierPaymentSerializer(serializers.ModelSerializer):
    """Serializer for SupplierPayment."""
    
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    
    class Meta:
        model = SupplierPayment
        fields = [
            'id', 'payment_number', 'supplier', 'supplier_name',
            'purchase_order', 'payment_date', 'amount',
            'payment_method', 'payment_method_display',
            'reference', 'notes', 'created_at'
        ]
        read_only_fields = ['id', 'payment_number', 'created_at']
