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
            'current_balance', 'current_balance_usd', 'credit_limit', 'is_active'
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
            'payment_terms', 'credit_limit', 'opening_balance', 'opening_balance_usd', 'current_balance', 'current_balance_usd',
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
            'tax_amount', 'total_amount', 'total_amount_usd',
            'paid_amount', 'paid_amount_usd',
            'remaining_amount', 'remaining_amount_usd',
            'transaction_currency'
        ]


class PurchaseOrderDetailSerializer(serializers.ModelSerializer):
    """Serializer for PurchaseOrder detail view."""
    
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    remaining_amount = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    items = PurchaseOrderItemSerializer(many=True, read_only=True)
    payments = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.full_name', read_only=True)
    
    class Meta:
        model = PurchaseOrder
        fields = [
            'id', 'order_number', 'supplier', 'supplier_name',
            'warehouse', 'warehouse_name',
            'order_date', 'expected_date', 'status', 'status_display',
            'subtotal', 'discount_amount', 'tax_amount',
            'total_amount', 'total_amount_usd',
            'paid_amount', 'paid_amount_usd',
            'remaining_amount', 'remaining_amount_usd',
            'transaction_currency', 'fx_rate_date', 'usd_to_syp_old_snapshot', 'usd_to_syp_new_snapshot',
            'reference', 'notes',
            'created_by', 'created_by_name', 'created_at',
            'approved_by', 'approved_by_name', 'approved_at',
            'items', 'payments'
        ]
        read_only_fields = ['id', 'order_number', 'subtotal', 'tax_amount', 'total_amount', 'created_at']

    def get_payments(self, obj):
        qs = obj.payments.filter(is_deleted=False).order_by('-payment_date', '-payment_number')
        return SupplierPaymentSerializer(qs, many=True).data


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

    # Optional initial payment (paid now) fields
    payment_amount = serializers.DecimalField(max_digits=15, decimal_places=2, required=False, allow_null=True, write_only=True)
    payment_method = serializers.CharField(required=False, allow_blank=True, allow_null=True, write_only=True)
    payment_date = serializers.DateField(required=False, allow_null=True, write_only=True)
    payment_transaction_currency = serializers.CharField(required=False, allow_blank=True, allow_null=True, write_only=True)
    payment_fx_rate_date = serializers.DateField(required=False, allow_null=True, write_only=True)
    payment_usd_to_syp_old_snapshot = serializers.DecimalField(max_digits=18, decimal_places=6, required=False, allow_null=True, write_only=True)
    payment_usd_to_syp_new_snapshot = serializers.DecimalField(max_digits=18, decimal_places=6, required=False, allow_null=True, write_only=True)
    payment_reference = serializers.CharField(required=False, allow_blank=True, allow_null=True, write_only=True)
    payment_notes = serializers.CharField(required=False, allow_blank=True, allow_null=True, write_only=True)
    
    class Meta:
        model = PurchaseOrder
        fields = [
            'supplier', 'warehouse', 'order_date', 'expected_date',
            'discount_amount',
            'fx_rate_date', 'usd_to_syp_old_snapshot', 'usd_to_syp_new_snapshot',
            'reference', 'notes', 'items', 'confirm',
            'payment_amount', 'payment_method', 'payment_date',
            'payment_transaction_currency', 'payment_fx_rate_date',
            'payment_usd_to_syp_old_snapshot', 'payment_usd_to_syp_new_snapshot',
            'payment_reference', 'payment_notes'
        ]

    def validate_items(self, value):
        """Validate that at least one item is provided."""
        if not value:
            raise serializers.ValidationError("At least one item is required.")
        return value

    def create(self, validated_data):
        from django.db import transaction
        from decimal import Decimal
        from .services import PurchaseService
        
        items_data = validated_data.pop('items')
        confirm = validated_data.pop('confirm', False)

        payment_amount = validated_data.pop('payment_amount', None)
        payment_method = validated_data.pop('payment_method', None)
        payment_date = validated_data.pop('payment_date', None)
        payment_transaction_currency = validated_data.pop('payment_transaction_currency', None)
        payment_fx_rate_date = validated_data.pop('payment_fx_rate_date', None)
        payment_usd_to_syp_old_snapshot = validated_data.pop('payment_usd_to_syp_old_snapshot', None)
        payment_usd_to_syp_new_snapshot = validated_data.pop('payment_usd_to_syp_new_snapshot', None)
        payment_reference = validated_data.pop('payment_reference', None)
        payment_notes = validated_data.pop('payment_notes', None)

        has_initial_payment = payment_amount is not None and Decimal(str(payment_amount or 0)) > 0
        user = self.context.get('request').user if self.context.get('request') else None

        service_items = []
        for item_data in items_data:
            product = item_data.get('product')
            product_unit = item_data.get('product_unit')

            if 'discount_percent' not in item_data or item_data.get('discount_percent') is None:
                item_data['discount_percent'] = Decimal('0.00')
            item_data['tax_rate'] = Decimal('0.00')

            service_items.append(
                {
                    'product_id': product.id,
                    'product_unit_id': product_unit.id if product_unit else None,
                    'quantity': item_data.get('quantity'),
                    'unit_price': item_data.get('unit_price'),
                    'discount_percent': item_data.get('discount_percent'),
                    'tax_rate': item_data.get('tax_rate'),
                    'notes': item_data.get('notes'),
                }
            )

        with transaction.atomic():
            purchase_order = PurchaseService.create_purchase_order(
                supplier_id=validated_data['supplier'].id,
                warehouse_id=validated_data['warehouse'].id,
                order_date=validated_data['order_date'],
                items=service_items,
                discount_amount=validated_data.get('discount_amount', Decimal('0.00')),
                expected_date=validated_data.get('expected_date'),
                fx_rate_date=validated_data.get('fx_rate_date'),
                usd_to_syp_old_snapshot=validated_data.get('usd_to_syp_old_snapshot'),
                usd_to_syp_new_snapshot=validated_data.get('usd_to_syp_new_snapshot'),
                reference=validated_data.get('reference'),
                notes=validated_data.get('notes'),
                user=user
            )

            if confirm:
                PurchaseService.approve_purchase_order(purchase_order.id, user=user)
                purchase_order.refresh_from_db()

                PurchaseService.receive_goods(
                    po_id=purchase_order.id,
                    received_date=purchase_order.order_date,
                    items=[
                        {'po_item_id': po_item.id, 'quantity': po_item.quantity}
                        for po_item in purchase_order.items.all()
                    ],
                    supplier_invoice_no=None,
                    notes=None,
                    user=user
                )

                purchase_order.refresh_from_db()

                if has_initial_payment:
                    PurchaseService.make_supplier_payment(
                        supplier_id=validated_data['supplier'].id,
                        payment_date=payment_date or purchase_order.order_date,
                        amount=Decimal(str(payment_amount)),
                        payment_method=(payment_method or 'cash'),
                        purchase_order_id=purchase_order.id,
                        transaction_currency=payment_transaction_currency or 'USD',
                        fx_rate_date=payment_fx_rate_date or purchase_order.order_date,
                        usd_to_syp_old_snapshot=payment_usd_to_syp_old_snapshot,
                        usd_to_syp_new_snapshot=payment_usd_to_syp_new_snapshot,
                        reference=payment_reference,
                        notes=payment_notes,
                        user=user
                    )
                    purchase_order.refresh_from_db()
            elif has_initial_payment:
                raise serializers.ValidationError({'payment_amount': 'لا يمكن تسجيل دفعة قبل تأكيد/استلام أمر الشراء'})

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
    purchase_order_number = serializers.CharField(source='purchase_order.order_number', read_only=True)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    
    class Meta:
        model = SupplierPayment
        fields = [
            'id', 'payment_number', 'supplier', 'supplier_name',
            'purchase_order', 'purchase_order_number', 'payment_date',
            'transaction_currency', 'fx_rate_date', 'usd_to_syp_old_snapshot', 'usd_to_syp_new_snapshot',
            'amount', 'amount_usd',
            'payment_method', 'payment_method_display',
            'reference', 'notes',
            'created_by', 'created_by_name',
            'created_at'
        ]
        read_only_fields = ['id', 'payment_number', 'created_at']
