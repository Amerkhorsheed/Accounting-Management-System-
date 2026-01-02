"""
Sales Serializers
"""
from datetime import date
from decimal import Decimal
from rest_framework import serializers

from apps.core.utils import get_daily_fx, to_usd
from .models import Customer, Invoice, InvoiceItem, Payment, SalesReturn, SalesReturnItem, PaymentAllocation


class CustomerListSerializer(serializers.ModelSerializer):
    """Serializer for Customer list view."""
    
    customer_type_display = serializers.CharField(source='get_customer_type_display', read_only=True)
    credit_limit_usd = serializers.SerializerMethodField()
    available_credit_usd = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self._fx_old, self._fx_new = get_daily_fx(date.today())
        except Exception:
            self._fx_old, self._fx_new = None, None

    def get_credit_limit_usd(self, obj):
        credit_limit = obj.credit_limit or Decimal('0.00')
        if not self._fx_old or not self._fx_new:
            return Decimal('0.00')
        return to_usd(
            credit_limit,
            'SYP_OLD',
            usd_to_syp_old=self._fx_old,
            usd_to_syp_new=self._fx_new
        )

    def get_available_credit_usd(self, obj):
        credit_limit_usd = self.get_credit_limit_usd(obj)
        if credit_limit_usd <= 0:
            return Decimal('0.00')
        current_balance_usd = obj.current_balance_usd or Decimal('0.00')
        return credit_limit_usd - current_balance_usd
    
    class Meta:
        model = Customer
        fields = [
            'id', 'code', 'name', 'name_en', 'customer_type', 'customer_type_display',
            'phone', 'mobile', 'email',
            'current_balance', 'current_balance_usd',
            'credit_limit', 'credit_limit_usd', 'available_credit_usd',
            'is_active'
        ]


class CustomerDetailSerializer(serializers.ModelSerializer):
    """Serializer for Customer detail view."""
    
    customer_type_display = serializers.CharField(source='get_customer_type_display', read_only=True)
    full_address = serializers.CharField(read_only=True)
    available_credit = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    credit_limit_usd = serializers.SerializerMethodField()
    available_credit_usd = serializers.SerializerMethodField()
    salesperson_name = serializers.CharField(source='salesperson.full_name', read_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self._fx_old, self._fx_new = get_daily_fx(date.today())
        except Exception:
            self._fx_old, self._fx_new = None, None

    def get_credit_limit_usd(self, obj):
        credit_limit = obj.credit_limit or Decimal('0.00')
        if not self._fx_old or not self._fx_new:
            return Decimal('0.00')
        return to_usd(
            credit_limit,
            'SYP_OLD',
            usd_to_syp_old=self._fx_old,
            usd_to_syp_new=self._fx_new
        )

    def get_available_credit_usd(self, obj):
        credit_limit_usd = self.get_credit_limit_usd(obj)
        if credit_limit_usd <= 0:
            return Decimal('0.00')
        current_balance_usd = obj.current_balance_usd or Decimal('0.00')
        return credit_limit_usd - current_balance_usd
    
    class Meta:
        model = Customer
        fields = [
            'id', 'code', 'name', 'name_en', 'customer_type', 'customer_type_display',
            'tax_number', 'commercial_register', 'contact_person',
            'phone', 'mobile', 'email', 'fax', 'website',
            'address', 'city', 'region', 'postal_code', 'country', 'full_address',
            'credit_limit', 'credit_limit_usd', 'available_credit', 'available_credit_usd',
            'payment_terms', 'discount_percent',
            'opening_balance', 'opening_balance_usd', 'current_balance', 'current_balance_usd',
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
    remaining_amount_usd = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
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
            'status', 'status_display',
            'transaction_currency',
            'subtotal', 'discount_amount',
            'tax_amount', 'total_amount', 'total_amount_usd',
            'paid_amount', 'paid_amount_usd',
            'remaining_amount', 'remaining_amount_usd',
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
    remaining_amount_usd = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
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
            'transaction_currency',
            'fx_rate_date', 'usd_to_syp_old_snapshot', 'usd_to_syp_new_snapshot',
            'subtotal', 'discount_percent', 'discount_amount',
            'tax_amount', 'total_amount', 'total_amount_usd',
            'paid_amount', 'paid_amount_usd',
            'remaining_amount', 'remaining_amount_usd',
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
    override_credit_limit = serializers.BooleanField(write_only=True, required=False, default=False)
    override_reason = serializers.CharField(write_only=True, required=False, allow_null=True, allow_blank=True)
    
    class Meta:
        model = Invoice
        fields = [
            'invoice_type', 'customer', 'warehouse',
            'invoice_date', 'due_date',
            'transaction_currency',
            'fx_rate_date', 'usd_to_syp_old_snapshot', 'usd_to_syp_new_snapshot',
            'discount_percent', 'discount_amount',
            'notes', 'internal_notes', 'items',
            # Non-model fields must be listed here too for DRF to include them
            'confirm', 'paid_amount', 'payment_method',
            'override_credit_limit', 'override_reason',
        ]
        # Tell DRF these are not model fields
        extra_kwargs = {
            'due_date': {'required': False, 'allow_null': True},
            'transaction_currency': {'required': False},
            'fx_rate_date': {'required': False, 'allow_null': True},
            'usd_to_syp_old_snapshot': {'required': False, 'allow_null': True},
            'usd_to_syp_new_snapshot': {'required': False, 'allow_null': True},
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
        from decimal import Decimal
        from .services import SalesService

        items_data = validated_data.pop('items')
        confirm = validated_data.pop('confirm', False)
        paid_amount = validated_data.pop('paid_amount', None)
        payment_method = validated_data.pop('payment_method', None)
        override_credit_limit = validated_data.pop('override_credit_limit', False)
        override_reason = validated_data.pop('override_reason', None)

        created_by = validated_data.pop('created_by', None)

        customer = validated_data.get('customer')
        warehouse = validated_data.get('warehouse')

        service_items = []
        for item in items_data:
            product = item.get('product')
            product_unit = item.get('product_unit')
            payload = {
                'product_id': product.id if product else None,
                'quantity': item.get('quantity'),
                'discount_percent': item.get('discount_percent', Decimal('0.00')),
                'notes': item.get('notes'),
            }

            if product_unit:
                payload['product_unit_id'] = product_unit.id

            if item.get('unit_price') is not None:
                payload['unit_price'] = item.get('unit_price')

            if item.get('cost_price') is not None:
                payload['cost_price'] = item.get('cost_price')

            if item.get('tax_rate') is not None:
                payload['tax_rate'] = item.get('tax_rate')

            service_items.append(payload)

        with transaction.atomic():
            invoice = SalesService.create_invoice(
                customer_id=customer.id if customer else None,
                warehouse_id=warehouse.id if warehouse else None,
                invoice_date=validated_data.get('invoice_date'),
                items=service_items,
                invoice_type=validated_data.get('invoice_type', 'cash'),
                discount_percent=validated_data.get('discount_percent', Decimal('0.00')),
                discount_amount=validated_data.get('discount_amount', Decimal('0.00')),
                due_date=validated_data.get('due_date'),
                notes=validated_data.get('notes'),
                internal_notes=validated_data.get('internal_notes'),
                user=created_by,
                override_credit_limit=override_credit_limit,
                override_reason=override_reason,
                transaction_currency=validated_data.get('transaction_currency', 'SYP_OLD'),
                fx_rate_date=validated_data.get('fx_rate_date'),
                usd_to_syp_old_snapshot=validated_data.get('usd_to_syp_old_snapshot'),
                usd_to_syp_new_snapshot=validated_data.get('usd_to_syp_new_snapshot'),
            )

            if confirm:
                SalesService.confirm_invoice(
                    invoice.id,
                    user=created_by,
                    paid_amount=paid_amount,
                    payment_method=payment_method
                )
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
            'invoice', 'payment_date',
            'transaction_currency', 'fx_rate_date', 'usd_to_syp_old_snapshot', 'usd_to_syp_new_snapshot',
            'amount', 'amount_usd',
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
    invoice_transaction_currency = serializers.CharField(source='invoice.transaction_currency', read_only=True)
    invoice_total_usd = serializers.DecimalField(
        source='invoice.total_amount_usd', max_digits=15, decimal_places=2, read_only=True
    )
    invoice_remaining_usd = serializers.DecimalField(
        source='invoice.remaining_amount_usd', max_digits=15, decimal_places=2, read_only=True
    )
    
    class Meta:
        model = PaymentAllocation
        fields = [
            'id', 'payment', 'invoice', 'invoice_number', 'invoice_date',
            'invoice_total', 'invoice_remaining',
            'invoice_transaction_currency', 'invoice_total_usd', 'invoice_remaining_usd',
            'amount', 'amount_usd'
        ]
        read_only_fields = ['id']


class PaymentAllocationCreateSerializer(serializers.Serializer):
    """Serializer for creating payment allocations."""
    
    invoice_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=15, decimal_places=2, required=False, allow_null=True)
    amount_usd = serializers.DecimalField(max_digits=15, decimal_places=2, required=False, allow_null=True)

    def validate(self, attrs):
        amount = attrs.get('amount')
        amount_usd = attrs.get('amount_usd')

        amount_ok = amount is not None and amount > Decimal('0')
        amount_usd_ok = amount_usd is not None and amount_usd > Decimal('0')

        if not amount_ok and not amount_usd_ok:
            raise serializers.ValidationError({'amount': 'يجب إدخال مبلغ التخصيص'})

        return attrs


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
            'invoice', 'payment_date',
            'transaction_currency', 'fx_rate_date', 'usd_to_syp_old_snapshot', 'usd_to_syp_new_snapshot',
            'amount', 'amount_usd',
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
    transaction_currency = serializers.ChoiceField(
        choices=Payment._meta.get_field('transaction_currency').choices,
        required=False
    )
    fx_rate_date = serializers.DateField(required=False, allow_null=True)
    usd_to_syp_old_snapshot = serializers.DecimalField(max_digits=18, decimal_places=6, required=False, allow_null=True)
    usd_to_syp_new_snapshot = serializers.DecimalField(max_digits=18, decimal_places=6, required=False, allow_null=True)
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
    transaction_currency = serializers.CharField(required=False, allow_null=True)
    fx_rate_date = serializers.DateField(required=False, allow_null=True)
    usd_to_syp_old_snapshot = serializers.DecimalField(max_digits=18, decimal_places=6, required=False, allow_null=True)
    usd_to_syp_new_snapshot = serializers.DecimalField(max_digits=18, decimal_places=6, required=False, allow_null=True)
    total_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    paid_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    remaining_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_amount_usd = serializers.DecimalField(max_digits=15, decimal_places=2, required=False)
    paid_amount_usd = serializers.DecimalField(max_digits=15, decimal_places=2, required=False)
    remaining_amount_usd = serializers.DecimalField(max_digits=15, decimal_places=2, required=False)
    status = serializers.CharField()
    is_overdue = serializers.BooleanField()
