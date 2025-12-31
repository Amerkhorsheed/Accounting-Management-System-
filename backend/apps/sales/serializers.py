"""
Sales Serializers
"""
from decimal import Decimal
from rest_framework import serializers
from .models import Customer, Invoice, InvoiceItem, Payment, SalesReturn, SalesReturnItem, PaymentAllocation


class CustomerListSerializer(serializers.ModelSerializer):
    """Serializer for Customer list view."""
    
    customer_type_display = serializers.CharField(source='get_customer_type_display', read_only=True)
    
    class Meta:
        model = Customer
        fields = [
            'id', 'code', 'name', 'name_en', 'customer_type', 'customer_type_display',
            'phone', 'mobile', 'email', 'current_balance', 'credit_limit', 'is_active'
        ]


class CustomerDetailSerializer(serializers.ModelSerializer):
    """Serializer for Customer detail view."""
    
    customer_type_display = serializers.CharField(source='get_customer_type_display', read_only=True)
    full_address = serializers.CharField(read_only=True)
    available_credit = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    salesperson_name = serializers.CharField(source='salesperson.full_name', read_only=True)
    
    class Meta:
        model = Customer
        fields = [
            'id', 'code', 'name', 'name_en', 'customer_type', 'customer_type_display',
            'tax_number', 'commercial_register', 'contact_person',
            'phone', 'mobile', 'email', 'fax', 'website',
            'address', 'city', 'region', 'postal_code', 'country', 'full_address',
            'credit_limit', 'available_credit', 'payment_terms', 'discount_percent',
            'opening_balance', 'current_balance',
            'salesperson', 'salesperson_name',
            'notes', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'code', 'current_balance', 'created_at', 'updated_at']
        extra_kwargs = {
            'name_en': {'required': False, 'allow_blank': True},
            'customer_type': {'required': False},
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
            'credit_limit': {'required': False},
            'payment_terms': {'required': False},
            'discount_percent': {'required': False},
            'opening_balance': {'required': False},
            'salesperson': {'required': False, 'allow_null': True},
            'notes': {'required': False, 'allow_blank': True},
            'is_active': {'required': False},
        }


class InvoiceItemSerializer(serializers.ModelSerializer):
    """Serializer for Invoice items."""
    
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_code = serializers.CharField(source='product.code', read_only=True)
    product_barcode = serializers.CharField(source='product.barcode', read_only=True)
    unit_name = serializers.SerializerMethodField()
    unit_symbol = serializers.SerializerMethodField()
    subtotal = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    discount_amount = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    tax_amount = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    total = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    profit = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    returned_quantity = serializers.SerializerMethodField()
    
    class Meta:
        model = InvoiceItem
        fields = [
            'id', 'product', 'product_name', 'product_code', 'product_barcode',
            'product_unit', 'unit_name', 'unit_symbol',
            'quantity', 'base_quantity', 'unit_price', 'cost_price',
            'discount_percent', 'tax_rate',
            'subtotal', 'discount_amount', 'tax_amount', 'total', 'profit', 'returned_quantity', 'notes'
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

    def get_returned_quantity(self, obj):
        from django.db.models import Sum
        total = SalesReturnItem.objects.filter(invoice_item=obj).aggregate(s=Sum('quantity'))['s']
        return total or 0


class InvoiceListSerializer(serializers.ModelSerializer):
    """Serializer for Invoice list view."""
    
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    customer_code = serializers.CharField(source='customer.code', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    invoice_type_display = serializers.CharField(source='get_invoice_type_display', read_only=True)
    remaining_amount = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    returns_total = serializers.SerializerMethodField()
    net_total = serializers.SerializerMethodField()
    net_remaining = serializers.SerializerMethodField()
    refund_amount = serializers.SerializerMethodField()
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'invoice_type', 'invoice_type_display',
            'customer', 'customer_name', 'customer_code', 
            'warehouse', 'warehouse_name', 'invoice_date', 'due_date',
            'status', 'status_display', 'subtotal', 'discount_amount',
            'tax_amount', 'total_amount', 'paid_amount', 'remaining_amount',
            'returns_total', 'net_total', 'net_remaining', 'refund_amount'
        ]

    def get_returns_total(self, obj):
        from django.db.models import Sum
        total = SalesReturn.objects.filter(original_invoice=obj).aggregate(s=Sum('total_amount'))['s']
        return total or Decimal('0.00')

    def get_net_total(self, obj):
        net = (obj.total_amount or Decimal('0.00')) - self.get_returns_total(obj)
        return net if net > 0 else Decimal('0.00')

    def get_net_remaining(self, obj):
        net_remaining = self.get_net_total(obj) - (obj.paid_amount or Decimal('0.00'))
        return net_remaining if net_remaining > 0 else Decimal('0.00')

    def get_refund_amount(self, obj):
        refund = (obj.paid_amount or Decimal('0.00')) - self.get_net_total(obj)
        return refund if refund > 0 else Decimal('0.00')


class InvoiceDetailSerializer(serializers.ModelSerializer):
    """Serializer for Invoice detail view."""
    
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    customer_phone = serializers.CharField(source='customer.phone', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    invoice_type_display = serializers.CharField(source='get_invoice_type_display', read_only=True)
    remaining_amount = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    returns_total = serializers.SerializerMethodField()
    net_total = serializers.SerializerMethodField()
    net_remaining = serializers.SerializerMethodField()
    refund_amount = serializers.SerializerMethodField()
    items = InvoiceItemSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'invoice_type', 'invoice_type_display',
            'customer', 'customer_name', 'customer_phone',
            'warehouse', 'warehouse_name',
            'invoice_date', 'due_date', 'status', 'status_display',
            'subtotal', 'discount_percent', 'discount_amount',
            'tax_amount', 'total_amount', 'paid_amount', 'remaining_amount',
            'returns_total', 'net_total', 'net_remaining', 'refund_amount',
            'notes', 'internal_notes', 'return_for',
            'created_by', 'created_by_name', 'created_at', 'updated_at',
            'items'
        ]
        read_only_fields = ['id', 'invoice_number', 'subtotal', 'tax_amount', 'total_amount', 'created_at', 'updated_at']

    def get_returns_total(self, obj):
        from django.db.models import Sum
        total = SalesReturn.objects.filter(original_invoice=obj).aggregate(s=Sum('total_amount'))['s']
        return total or Decimal('0.00')

    def get_net_total(self, obj):
        net = (obj.total_amount or Decimal('0.00')) - self.get_returns_total(obj)
        return net if net > 0 else Decimal('0.00')

    def get_net_remaining(self, obj):
        net_remaining = self.get_net_total(obj) - (obj.paid_amount or Decimal('0.00'))
        return net_remaining if net_remaining > 0 else Decimal('0.00')

    def get_refund_amount(self, obj):
        refund = (obj.paid_amount or Decimal('0.00')) - self.get_net_total(obj)
        return refund if refund > 0 else Decimal('0.00')


class InvoiceItemCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Invoice items (write-only)."""
    
    class Meta:
        model = InvoiceItem
        fields = [
            'product', 'product_unit', 'quantity', 'unit_price', 'cost_price',
            'discount_percent', 'tax_rate', 'notes'
        ]
        extra_kwargs = {
            'product_unit': {'required': False, 'allow_null': True},
            'cost_price': {'required': False},
            'discount_percent': {'required': False},
            'tax_rate': {'required': False},
            'notes': {'required': False},
        }


class InvoiceCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Invoice."""
    
    items = InvoiceItemCreateSerializer(many=True)
    # Non-model fields for atomic invoice creation and confirmation
    # Declared at class level with write_only=True, NOT in Meta.fields
    confirm = serializers.BooleanField(write_only=True, required=False, default=False)
    paid_amount = serializers.DecimalField(max_digits=15, decimal_places=2, write_only=True, required=False, allow_null=True)
    payment_method = serializers.CharField(max_length=20, write_only=True, required=False, allow_null=True, allow_blank=True)
    
    class Meta:
        model = Invoice
        fields = [
            'invoice_type', 'customer', 'warehouse',
            'invoice_date', 'due_date',
            'discount_percent', 'discount_amount',
            'notes', 'internal_notes', 'items',
            # Non-model fields must be listed here too for DRF to include them
            'confirm', 'paid_amount', 'payment_method',
        ]
        # Tell DRF these are not model fields
        extra_kwargs = {
            'due_date': {'required': False, 'allow_null': True},
            'discount_percent': {'required': False},
            'discount_amount': {'required': False},
            'notes': {'required': False, 'allow_blank': True},
            'internal_notes': {'required': False, 'allow_blank': True},
        }

    def validate_items(self, value):
        """Validate that at least one item is provided."""
        if not value:
            raise serializers.ValidationError("At least one item is required.")
        return value

    def create(self, validated_data):
        from django.db import transaction
        from apps.inventory.models import Product
        from decimal import Decimal
        
        items_data = validated_data.pop('items')
        # Pop non-model fields before creating invoice
        confirm = validated_data.pop('confirm', False)
        paid_amount = validated_data.pop('paid_amount', None)
        payment_method = validated_data.pop('payment_method', None)
        
        with transaction.atomic():
            # Create the invoice
            invoice = Invoice.objects.create(**validated_data)
            
            # Create all items
            for item_data in items_data:
                product = item_data.get('product')
                product_unit = item_data.get('product_unit')
                
                # Set default cost_price from product_unit or product if not provided
                if 'cost_price' not in item_data or item_data.get('cost_price') is None:
                    if product_unit and product_unit.cost_price:
                        item_data['cost_price'] = product_unit.cost_price
                    else:
                        item_data['cost_price'] = product.cost_price if product else Decimal('0.00')
                
                # Set default unit_price from product_unit or product if not provided
                if 'unit_price' not in item_data or item_data.get('unit_price') is None:
                    if product_unit and product_unit.sale_price:
                        item_data['unit_price'] = product_unit.sale_price
                    else:
                        item_data['unit_price'] = product.sale_price if product else Decimal('0.00')
                
                # Set default tax_rate from product only if not explicitly provided
                # Note: tax_rate=0 is a valid explicit value (no tax)
                if 'tax_rate' not in item_data:
                    if product and product.is_taxable:
                        item_data['tax_rate'] = product.tax_rate
                    else:
                        item_data['tax_rate'] = Decimal('0.00')
                elif item_data.get('tax_rate') is None:
                    item_data['tax_rate'] = Decimal('0.00')
                
                # Set default discount_percent if not provided
                if 'discount_percent' not in item_data or item_data.get('discount_percent') is None:
                    item_data['discount_percent'] = Decimal('0.00')
                
                InvoiceItem.objects.create(invoice=invoice, **item_data)
            
            # Calculate totals after all items are created
            invoice.calculate_totals()
            
            # Atomic confirmation if requested
            if confirm:
                from .services import SalesService
                SalesService.confirm_invoice(
                    invoice.id,
                    user=invoice.created_by,
                    paid_amount=paid_amount,
                    payment_method=payment_method
                )
                # Refresh to get updated status and paid_amount
                invoice.refresh_from_db()
        
        return invoice


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment."""
    
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    received_by_name = serializers.CharField(source='received_by.full_name', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'payment_number', 'customer', 'customer_name',
            'invoice', 'payment_date', 'amount',
            'payment_method', 'payment_method_display',
            'reference', 'notes',
            'received_by', 'received_by_name', 'created_at'
        ]
        read_only_fields = ['id', 'payment_number', 'created_at']


class SalesReturnItemSerializer(serializers.ModelSerializer):
    """Serializer for SalesReturn items."""
    
    product_name = serializers.CharField(source='product.name', read_only=True)
    total = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    
    class Meta:
        model = SalesReturnItem
        fields = [
            'id', 'invoice_item', 'product', 'product_name',
            'quantity', 'unit_price', 'total', 'reason'
        ]


class SalesReturnSerializer(serializers.ModelSerializer):
    """Serializer for SalesReturn."""
    
    original_invoice_number = serializers.CharField(source='original_invoice.invoice_number', read_only=True)
    customer_name = serializers.CharField(source='original_invoice.customer.name', read_only=True)
    items = SalesReturnItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = SalesReturn
        fields = [
            'id', 'return_number', 'original_invoice', 'original_invoice_number',
            'customer_name', 'return_date', 'total_amount',
            'reason', 'notes', 'created_at', 'items'
        ]
        read_only_fields = ['id', 'return_number', 'total_amount', 'created_at']


class SalesReturnItemCreateSerializer(serializers.Serializer):
    """
    Serializer for creating SalesReturn items.
    
    Requirements: 5.2, 5.3
    - Display original invoice items with returnable quantities
    - Validate return quantity does not exceed available quantity
    """
    invoice_item_id = serializers.IntegerField()
    quantity = serializers.DecimalField(max_digits=15, decimal_places=2)
    reason = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    
    def validate_quantity(self, value):
        """Validate quantity is positive."""
        from decimal import Decimal
        if value <= Decimal('0'):
            raise serializers.ValidationError('الكمية يجب أن تكون أكبر من صفر')
        return value


class SalesReturnCreateSerializer(serializers.Serializer):
    """
    Serializer for creating SalesReturn.
    
    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8
    - Create return for confirmed/paid invoices
    - Validate return quantities
    - Add returned quantities back to stock
    - Create stock movement records
    - Reduce customer balance
    - Calculate return totals with proportional discounts/taxes
    - Require reason for return
    """
    original_invoice = serializers.PrimaryKeyRelatedField(queryset=Invoice.objects.all())
    return_date = serializers.DateField()
    reason = serializers.CharField()
    notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    items = SalesReturnItemCreateSerializer(many=True)
    
    def validate_reason(self, value):
        """Validate reason is provided (Requirement 5.8)."""
        if not value or not value.strip():
            raise serializers.ValidationError('يجب تحديد سبب الإرجاع')
        return value.strip()
    
    def validate_items(self, value):
        """Validate at least one item is provided."""
        if not value:
            raise serializers.ValidationError('يجب تحديد عنصر واحد على الأقل للإرجاع')
        return value
    
    def validate(self, attrs):
        """
        Cross-field validation.
        
        Requirements: 5.1, 5.3
        - Validate invoice status (must be confirmed, paid, or partial)
        - Validate return quantities don't exceed available quantities
        """
        from decimal import Decimal
        from django.db.models import Sum
        
        invoice = attrs.get('original_invoice')
        items = attrs.get('items', [])
        
        # Requirement 5.1: Validate invoice status
        allowed_statuses = [Invoice.Status.CONFIRMED, Invoice.Status.PAID, Invoice.Status.PARTIAL]
        if invoice.status not in allowed_statuses:
            raise serializers.ValidationError({
                'original_invoice': f'لا يمكن إنشاء مرتجع لفاتورة بحالة {invoice.get_status_display()}. يمكن إنشاء مرتجع للفواتير المؤكدة أو المدفوعة فقط.'
            })
        
        # Requirement 5.3: Validate return quantities
        for item_data in items:
            invoice_item_id = item_data.get('invoice_item_id')
            return_quantity = item_data.get('quantity')
            
            try:
                invoice_item = InvoiceItem.objects.get(id=invoice_item_id, invoice=invoice)
            except InvoiceItem.DoesNotExist:
                raise serializers.ValidationError({
                    'items': f'بند الفاتورة رقم {invoice_item_id} غير موجود في هذه الفاتورة'
                })
            
            # Calculate already returned quantity for this item
            already_returned = SalesReturnItem.objects.filter(
                invoice_item=invoice_item
            ).aggregate(total=Sum('quantity'))['total'] or Decimal('0')
            
            available_quantity = invoice_item.quantity - already_returned
            
            if return_quantity > available_quantity:
                raise serializers.ValidationError({
                    'items': f'كمية الإرجاع ({return_quantity}) تتجاوز الكمية المتاحة للإرجاع ({available_quantity}) للمنتج {invoice_item.product.name}'
                })
        
        return attrs
    
    def create(self, validated_data):
        """
        Create sales return using SalesService.
        
        Requirements: 5.4, 5.5, 5.6, 5.7
        """
        from .services import SalesService
        
        invoice = validated_data['original_invoice']
        items_data = validated_data['items']
        
        # Transform items data to match SalesService.create_sales_return format
        items = [
            {
                'invoice_item_id': item['invoice_item_id'],
                'quantity': item['quantity'],
                'reason': item.get('reason')
            }
            for item in items_data
        ]
        
        # Get user from context
        user = self.context.get('request').user if self.context.get('request') else None
        
        return SalesService.create_sales_return(
            invoice_id=invoice.id,
            return_date=validated_data['return_date'],
            items=items,
            reason=validated_data['reason'],
            notes=validated_data.get('notes'),
            user=user
        )


class PaymentAllocationSerializer(serializers.ModelSerializer):
    """Serializer for PaymentAllocation."""
    
    invoice_number = serializers.CharField(source='invoice.invoice_number', read_only=True)
    invoice_date = serializers.DateField(source='invoice.invoice_date', read_only=True)
    invoice_total = serializers.DecimalField(
        source='invoice.total_amount', max_digits=15, decimal_places=2, read_only=True
    )
    invoice_remaining = serializers.DecimalField(
        source='invoice.remaining_amount', max_digits=15, decimal_places=2, read_only=True
    )
    
    class Meta:
        model = PaymentAllocation
        fields = [
            'id', 'payment', 'invoice', 'invoice_number', 'invoice_date',
            'invoice_total', 'invoice_remaining', 'amount'
        ]
        read_only_fields = ['id']


class PaymentAllocationCreateSerializer(serializers.Serializer):
    """Serializer for creating payment allocations."""
    
    invoice_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=15, decimal_places=2)


class PaymentWithAllocationsSerializer(serializers.ModelSerializer):
    """Serializer for Payment with allocations."""
    
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    received_by_name = serializers.CharField(source='received_by.full_name', read_only=True)
    allocations = PaymentAllocationSerializer(many=True, read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'payment_number', 'customer', 'customer_name',
            'invoice', 'payment_date', 'amount',
            'payment_method', 'payment_method_display',
            'reference', 'notes',
            'received_by', 'received_by_name', 'created_at',
            'allocations'
        ]
        read_only_fields = ['id', 'payment_number', 'created_at']


class CollectPaymentWithAllocationSerializer(serializers.Serializer):
    """Serializer for collecting payment with allocations in one operation."""
    
    customer = serializers.PrimaryKeyRelatedField(queryset=Customer.objects.all())
    payment_date = serializers.DateField()
    amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    payment_method = serializers.ChoiceField(choices=Payment.PaymentMethod.choices)
    reference = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    allocations = PaymentAllocationCreateSerializer(many=True, required=False)
    auto_allocate = serializers.BooleanField(default=False)


class UnpaidInvoiceSerializer(serializers.Serializer):
    """Serializer for unpaid invoice list."""
    
    id = serializers.IntegerField()
    invoice_number = serializers.CharField()
    invoice_date = serializers.DateField()
    due_date = serializers.DateField(allow_null=True)
    total_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    paid_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    remaining_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    status = serializers.CharField()
    is_overdue = serializers.BooleanField()
