"""
Inventory Serializers
"""
from rest_framework import serializers
from decimal import Decimal
from .models import Category, Unit, ProductUnit, Warehouse, Product, Stock, StockMovement


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model."""
    
    full_path = serializers.CharField(read_only=True)
    children_count = serializers.SerializerMethodField()
    products_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'name_en', 'parent', 'description', 
            'image', 'sort_order', 'is_active', 'full_path',
            'children_count', 'products_count', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def get_children_count(self, obj):
        return obj.children.filter(is_active=True, is_deleted=False).count()

    def get_products_count(self, obj):
        return obj.products.filter(is_active=True, is_deleted=False).count()


class CategoryTreeSerializer(serializers.ModelSerializer):
    """Serializer for Category with nested children."""
    
    children = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'name_en', 'children']

    def get_children(self, obj):
        children = obj.children.filter(is_active=True, is_deleted=False)
        return CategoryTreeSerializer(children, many=True).data


class UnitSerializer(serializers.ModelSerializer):
    """Serializer for Unit model - read operations."""
    
    products_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Unit
        fields = ['id', 'name', 'name_en', 'symbol', 'is_active', 'products_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_products_count(self, obj):
        """Get count of products using this unit via ProductUnit."""
        from .models import ProductUnit
        return ProductUnit.objects.filter(unit=obj, is_deleted=False).count()


class UnitCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating Units with validation."""
    
    class Meta:
        model = Unit
        fields = ['id', 'name', 'name_en', 'symbol', 'is_active']
        read_only_fields = ['id']
        extra_kwargs = {
            'name': {'required': True},
            'symbol': {'required': True},
            'name_en': {'required': False, 'allow_blank': True, 'allow_null': True},
            'is_active': {'required': False, 'default': True},
        }

    def validate_name(self, value):
        """Validate name is not empty and is unique among non-deleted units."""
        if not value or not value.strip():
            raise serializers.ValidationError('اسم الوحدة مطلوب')
        
        value = value.strip()
        queryset = Unit.objects.filter(name=value, is_deleted=False)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError('اسم الوحدة موجود مسبقاً')
        return value

    def validate_symbol(self, value):
        """Validate symbol is not empty and is unique among non-deleted units."""
        if not value or not value.strip():
            raise serializers.ValidationError('رمز الوحدة مطلوب')
        
        value = value.strip()
        queryset = Unit.objects.filter(symbol=value, is_deleted=False)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError('رمز الوحدة موجود مسبقاً')
        return value

    def to_representation(self, instance):
        """Return full unit details after creation/update."""
        return UnitSerializer(instance).data


class ProductUnitSerializer(serializers.ModelSerializer):
    """Serializer for ProductUnit model - read operations."""
    
    unit_id = serializers.IntegerField(source='unit.id', read_only=True)
    unit_name = serializers.CharField(source='unit.name', read_only=True)
    unit_name_en = serializers.CharField(source='unit.name_en', read_only=True)
    unit_symbol = serializers.CharField(source='unit.symbol', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_code = serializers.CharField(source='product.code', read_only=True)
    
    class Meta:
        model = ProductUnit
        fields = [
            'id', 'product', 'product_name', 'product_code',
            'unit', 'unit_id', 'unit_name', 'unit_name_en', 'unit_symbol',
            'conversion_factor', 'is_base_unit',
            'sale_price', 'cost_price', 'barcode',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ProductUnitCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating ProductUnits with validation."""
    
    class Meta:
        model = ProductUnit
        fields = [
            'id', 'product', 'unit', 'conversion_factor', 'is_base_unit',
            'sale_price', 'cost_price', 'barcode', 'is_active'
        ]
        read_only_fields = ['id']
        extra_kwargs = {
            'product': {'required': True},
            'unit': {'required': True},
            'conversion_factor': {'required': False},
            'is_base_unit': {'required': False},
            'sale_price': {'required': False},
            'cost_price': {'required': False},
            'barcode': {'required': False, 'allow_blank': True, 'allow_null': True},
            'is_active': {'required': False, 'default': True},
        }

    def validate_conversion_factor(self, value):
        """Validate conversion factor is positive."""
        if value is not None and value <= 0:
            raise serializers.ValidationError('معامل التحويل يجب أن يكون أكبر من صفر')
        return value

    def validate_sale_price(self, value):
        """Validate sale price is not negative."""
        if value is not None and value < 0:
            raise serializers.ValidationError('سعر البيع لا يمكن أن يكون سالباً')
        return value

    def validate_cost_price(self, value):
        """Validate cost price is not negative."""
        if value is not None and value < 0:
            raise serializers.ValidationError('سعر التكلفة لا يمكن أن يكون سالباً')
        return value

    def validate(self, attrs):
        """Cross-field validation for ProductUnit."""
        product = attrs.get('product') or (self.instance.product if self.instance else None)
        unit = attrs.get('unit') or (self.instance.unit if self.instance else None)
        is_base_unit = attrs.get('is_base_unit', False)
        conversion_factor = attrs.get('conversion_factor', Decimal('1.0000'))
        
        if not product or not unit:
            return attrs
        
        # Check for duplicate product-unit combination
        queryset = ProductUnit.objects.filter(
            product=product,
            unit=unit,
            is_deleted=False
        )
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError({
                'unit': 'هذه الوحدة مضافة للمنتج مسبقاً'
            })
        
        # If this is set as base unit, conversion factor must be 1
        if is_base_unit and conversion_factor != Decimal('1.0000'):
            raise serializers.ValidationError({
                'conversion_factor': 'معامل التحويل للوحدة الأساسية يجب أن يكون 1'
            })
        
        return attrs

    def create(self, validated_data):
        """Create ProductUnit with base unit logic."""
        product = validated_data.get('product')
        is_base_unit = validated_data.get('is_base_unit', False)
        
        # If this is the first unit for the product, make it the base unit
        existing_units = ProductUnit.objects.filter(
            product=product,
            is_deleted=False
        ).count()
        
        if existing_units == 0:
            validated_data['is_base_unit'] = True
            validated_data['conversion_factor'] = Decimal('1.0000')
        elif is_base_unit:
            # If setting this as base unit, unset any existing base unit
            ProductUnit.objects.filter(
                product=product,
                is_base_unit=True,
                is_deleted=False
            ).update(is_base_unit=False)
        
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Update ProductUnit with base unit logic."""
        is_base_unit = validated_data.get('is_base_unit', instance.is_base_unit)
        product = instance.product
        
        if is_base_unit and not instance.is_base_unit:
            # If setting this as base unit, unset any existing base unit
            ProductUnit.objects.filter(
                product=product,
                is_base_unit=True,
                is_deleted=False
            ).exclude(pk=instance.pk).update(is_base_unit=False)
            # Base unit must have conversion factor of 1
            validated_data['conversion_factor'] = Decimal('1.0000')
        
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        """Return full ProductUnit details after creation/update."""
        return ProductUnitSerializer(instance).data


class WarehouseSerializer(serializers.ModelSerializer):
    """Serializer for Warehouse model."""
    
    manager_name = serializers.CharField(source='manager.full_name', read_only=True)
    
    class Meta:
        model = Warehouse
        fields = [
            'id', 'name', 'code', 'address', 'is_default', 
            'manager', 'manager_name', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ProductListSerializer(serializers.ModelSerializer):
    """Serializer for Product list view (minimal data)."""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    unit_name = serializers.CharField(source='unit.name', read_only=True)
    unit_symbol = serializers.CharField(source='unit.symbol', read_only=True)
    total_stock = serializers.SerializerMethodField()
    product_units = serializers.SerializerMethodField()
    stock_conversions = serializers.SerializerMethodField()
    base_unit_info = serializers.SerializerMethodField()
    is_low_stock = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'code', 'barcode', 'name', 'name_en', 'category', 'category_name',
            'unit', 'unit_name', 'unit_symbol', 'cost_price', 'sale_price', 
            'is_active', 'total_stock', 'image', 'minimum_stock', 'track_stock',
            'is_taxable', 'tax_rate', 'product_units', 'stock_conversions', 
            'base_unit_info', 'is_low_stock'
        ]
        read_only_fields = ['id']

    def get_total_stock(self, obj):
        return sum(stock.quantity for stock in obj.stock_levels.all())

    def get_is_low_stock(self, obj):
        """
        Check if total stock is below minimum.
        
        Both total_stock and minimum_stock are in base unit quantities.
        Requirements: 5.4 - Low stock alerts use base unit quantities
        """
        total_stock = sum(stock.quantity for stock in obj.stock_levels.all())
        return total_stock <= obj.minimum_stock

    def get_base_unit_info(self, obj):
        """Get base unit information for the product."""
        base_unit = obj.product_units.filter(
            is_base_unit=True, is_deleted=False
        ).select_related('unit').first()
        if base_unit:
            return {
                'unit_id': base_unit.unit.id,
                'unit_name': base_unit.unit.name,
                'unit_symbol': base_unit.unit.symbol
            }
        # Fallback to product's default unit
        if obj.unit:
            return {
                'unit_id': obj.unit.id,
                'unit_name': obj.unit.name,
                'unit_symbol': obj.unit.symbol
            }
        return None

    def get_stock_conversions(self, obj):
        """
        Get total stock converted to all available units.
        
        Returns list of {unit_name, unit_symbol, quantity} for each non-base unit.
        Requirements: 5.1, 5.2, 5.3
        """
        from decimal import Decimal
        
        total_stock = sum(stock.quantity for stock in obj.stock_levels.all())
        conversions = []
        
        # Get all product units except base unit
        product_units = obj.product_units.filter(
            is_deleted=False, is_active=True
        ).select_related('unit')
        
        for pu in product_units:
            if pu.is_base_unit:
                continue  # Skip base unit
            
            # Convert from base unit to this unit: base_quantity / conversion_factor
            if pu.conversion_factor and pu.conversion_factor > 0:
                converted_qty = total_stock / pu.conversion_factor
                conversions.append({
                    'unit_id': pu.unit.id,
                    'unit_name': pu.unit.name,
                    'unit_symbol': pu.unit.symbol,
                    'quantity': str(converted_qty.quantize(Decimal('0.01'))),
                    'conversion_factor': str(pu.conversion_factor)
                })
        
        return conversions

    def get_product_units(self, obj):
        """Get available units for this product (for sales/purchases unit selection)."""
        product_units = obj.product_units.filter(is_deleted=False, is_active=True).select_related('unit')
        return [
            {
                'id': pu.id,
                'unit_id': pu.unit.id,
                'unit_name': pu.unit.name,
                'unit_symbol': pu.unit.symbol,
                'conversion_factor': str(pu.conversion_factor),
                'is_base_unit': pu.is_base_unit,
                'sale_price': str(pu.sale_price),
                'cost_price': str(pu.cost_price),
                'barcode': pu.barcode
            }
            for pu in product_units
        ]


class ProductDetailSerializer(serializers.ModelSerializer):
    """Serializer for Product detail view (full data)."""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    unit_name = serializers.CharField(source='unit.name', read_only=True)
    unit_symbol = serializers.CharField(source='unit.symbol', read_only=True)
    profit_margin = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    price_with_tax = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    stock_levels = serializers.SerializerMethodField()
    product_units = serializers.SerializerMethodField()
    stock_conversions = serializers.SerializerMethodField()
    base_unit_info = serializers.SerializerMethodField()
    is_low_stock = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'code', 'barcode', 'name', 'name_en', 'description',
            'product_type', 'category', 'category_name', 'unit', 'unit_name', 'unit_symbol',
            'cost_price', 'sale_price', 'wholesale_price', 'minimum_price',
            'is_taxable', 'tax_rate', 'price_with_tax', 'profit_margin',
            'track_stock', 'minimum_stock', 'maximum_stock', 'reorder_point',
            'image', 'brand', 'model', 'notes',
            'is_active', 'stock_levels', 'product_units', 'stock_conversions',
            'base_unit_info', 'is_low_stock', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_is_low_stock(self, obj):
        """
        Check if total stock is below minimum.
        
        Both total_stock and minimum_stock are in base unit quantities.
        Requirements: 5.4 - Low stock alerts use base unit quantities
        """
        total_stock = sum(stock.quantity for stock in obj.stock_levels.all())
        return total_stock <= obj.minimum_stock

    def get_base_unit_info(self, obj):
        """Get base unit information for the product."""
        base_unit = obj.product_units.filter(
            is_base_unit=True, is_deleted=False
        ).select_related('unit').first()
        if base_unit:
            return {
                'unit_id': base_unit.unit.id,
                'unit_name': base_unit.unit.name,
                'unit_symbol': base_unit.unit.symbol
            }
        # Fallback to product's default unit
        if obj.unit:
            return {
                'unit_id': obj.unit.id,
                'unit_name': obj.unit.name,
                'unit_symbol': obj.unit.symbol
            }
        return None

    def get_stock_conversions(self, obj):
        """
        Get total stock converted to all available units.
        
        Requirements: 5.1, 5.2, 5.3
        """
        from decimal import Decimal
        
        total_stock = sum(stock.quantity for stock in obj.stock_levels.all())
        conversions = []
        
        product_units = obj.product_units.filter(
            is_deleted=False, is_active=True
        ).select_related('unit')
        
        for pu in product_units:
            if pu.is_base_unit:
                continue
            
            if pu.conversion_factor and pu.conversion_factor > 0:
                converted_qty = total_stock / pu.conversion_factor
                conversions.append({
                    'unit_id': pu.unit.id,
                    'unit_name': pu.unit.name,
                    'unit_symbol': pu.unit.symbol,
                    'quantity': str(converted_qty.quantize(Decimal('0.01'))),
                    'conversion_factor': str(pu.conversion_factor)
                })
        
        return conversions

    def get_stock_levels(self, obj):
        stocks = obj.stock_levels.select_related('warehouse').all()
        return [
            {
                'warehouse_id': s.warehouse.id,
                'warehouse_name': s.warehouse.name,
                'quantity': s.quantity,
                'reserved': s.reserved_quantity,
                'available': s.available_quantity,
                'is_low_stock': s.is_low_stock
            }
            for s in stocks
        ]

    def get_product_units(self, obj):
        """Get all units configured for this product with full details."""
        product_units = obj.product_units.filter(is_deleted=False).select_related('unit')
        return ProductUnitSerializer(product_units, many=True).data


class ProductCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating Products."""
    
    # Make unit optional for creation - will use default if not provided
    unit = serializers.PrimaryKeyRelatedField(
        queryset=Unit.objects.filter(is_active=True, is_deleted=False),
        required=False,
        allow_null=True
    )
    
    # Make category optional
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.filter(is_active=True, is_deleted=False),
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = Product
        fields = [
            'code', 'barcode', 'name', 'name_en', 'description',
            'product_type', 'category', 'unit',
            'cost_price', 'sale_price', 'wholesale_price', 'minimum_price',
            'is_taxable', 'tax_rate',
            'track_stock', 'minimum_stock', 'maximum_stock', 'reorder_point',
            'image', 'brand', 'model', 'notes', 'is_active'
        ]
        extra_kwargs = {
            'code': {'required': False, 'allow_blank': True},
            'barcode': {'required': False, 'allow_blank': True, 'allow_null': True},
            'name_en': {'required': False, 'allow_blank': True},
            'description': {'required': False, 'allow_blank': True},
            'product_type': {'required': False},
            'cost_price': {'required': False},
            'sale_price': {'required': False},
            'wholesale_price': {'required': False},
            'minimum_price': {'required': False},
            'is_taxable': {'required': False},
            'tax_rate': {'required': False},
            'track_stock': {'required': False},
            'minimum_stock': {'required': False},
            'maximum_stock': {'required': False},
            'reorder_point': {'required': False},
            'brand': {'required': False, 'allow_blank': True},
            'model': {'required': False, 'allow_blank': True},
            'notes': {'required': False, 'allow_blank': True},
            'is_active': {'required': False},
        }
    
    def validate_code(self, value):
        """Validate code uniqueness, excluding current instance on update."""
        if value:
            queryset = Product.objects.filter(code=value, is_deleted=False)
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise serializers.ValidationError('كود المنتج موجود مسبقاً')
        return value
    
    def validate_barcode(self, value):
        """Validate barcode uniqueness, excluding current instance on update."""
        if value:
            queryset = Product.objects.filter(barcode=value, is_deleted=False)
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise serializers.ValidationError('الباركود موجود مسبقاً')
        return value

    def validate_name(self, value):
        """Ensure name is not empty or whitespace only."""
        if not value or not value.strip():
            raise serializers.ValidationError('اسم المنتج مطلوب')
        return value.strip()

    def validate_sale_price(self, value):
        """Ensure sale price is not negative."""
        if value is not None and value < 0:
            raise serializers.ValidationError('سعر البيع لا يمكن أن يكون سالباً')
        return value

    def validate_cost_price(self, value):
        """Ensure cost price is not negative."""
        if value is not None and value < 0:
            raise serializers.ValidationError('سعر التكلفة لا يمكن أن يكون سالباً')
        return value

    def validate(self, attrs):
        """Cross-field validation."""
        # Only check unit on create, not on update
        if self.instance is None:  # Creating new product
            if not attrs.get('unit'):
                # Get first available active unit as default
                default_unit = Unit.objects.filter(
                    is_active=True, 
                    is_deleted=False
                ).first()
                if default_unit:
                    attrs['unit'] = default_unit
                else:
                    raise serializers.ValidationError({
                        'unit': 'يجب تحديد وحدة القياس أو إنشاء وحدة افتراضية'
                    })
        
        # Validate minimum_price <= sale_price if both are set
        sale_price = attrs.get('sale_price')
        minimum_price = attrs.get('minimum_price')
        if sale_price is not None and minimum_price is not None:
            if minimum_price > sale_price:
                raise serializers.ValidationError({
                    'minimum_price': 'أقل سعر بيع لا يمكن أن يكون أكبر من سعر البيع'
                })
        
        return attrs

    def to_representation(self, instance):
        """Return full product details after creation/update."""
        return ProductDetailSerializer(instance).data


class StockSerializer(serializers.ModelSerializer):
    """Serializer for Stock model."""
    
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_code = serializers.CharField(source='product.code', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    available_quantity = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)
    unit_conversions = serializers.SerializerMethodField()
    base_unit_name = serializers.SerializerMethodField()
    base_unit_symbol = serializers.SerializerMethodField()
    
    class Meta:
        model = Stock
        fields = [
            'id', 'product', 'product_name', 'product_code',
            'warehouse', 'warehouse_name',
            'quantity', 'reserved_quantity', 'available_quantity',
            'is_low_stock', 'updated_at', 'unit_conversions',
            'base_unit_name', 'base_unit_symbol'
        ]
        read_only_fields = ['id', 'updated_at']

    def get_base_unit_name(self, obj):
        """Get the base unit name for the product."""
        base_unit = obj.product.product_units.filter(
            is_base_unit=True, is_deleted=False
        ).select_related('unit').first()
        if base_unit:
            return base_unit.unit.name
        # Fallback to product's default unit
        return obj.product.unit.name if obj.product.unit else None

    def get_base_unit_symbol(self, obj):
        """Get the base unit symbol for the product."""
        base_unit = obj.product.product_units.filter(
            is_base_unit=True, is_deleted=False
        ).select_related('unit').first()
        if base_unit:
            return base_unit.unit.symbol
        # Fallback to product's default unit
        return obj.product.unit.symbol if obj.product.unit else None

    def get_unit_conversions(self, obj):
        """
        Get stock quantity converted to all available units for the product.
        
        Returns list of {unit_name, unit_symbol, quantity} for each non-base unit.
        Requirements: 5.1, 5.2, 5.3
        """
        from decimal import Decimal
        
        base_quantity = obj.quantity
        conversions = []
        
        # Get all product units except base unit
        product_units = obj.product.product_units.filter(
            is_deleted=False, is_active=True
        ).select_related('unit')
        
        for pu in product_units:
            if pu.is_base_unit:
                continue  # Skip base unit, it's shown as the main quantity
            
            # Convert from base unit to this unit: base_quantity / conversion_factor
            if pu.conversion_factor and pu.conversion_factor > 0:
                converted_qty = base_quantity / pu.conversion_factor
                conversions.append({
                    'unit_id': pu.unit.id,
                    'unit_name': pu.unit.name,
                    'unit_symbol': pu.unit.symbol,
                    'quantity': str(converted_qty.quantize(Decimal('0.01'))),
                    'conversion_factor': str(pu.conversion_factor)
                })
        
        return conversions


class StockAdjustmentSerializer(serializers.Serializer):
    """Serializer for stock adjustment."""
    
    product_id = serializers.IntegerField()
    warehouse_id = serializers.IntegerField()
    quantity = serializers.DecimalField(max_digits=15, decimal_places=2)
    adjustment_type = serializers.ChoiceField(choices=['add', 'subtract', 'set'])
    reason = serializers.CharField(max_length=255)
    notes = serializers.CharField(required=False, allow_blank=True)


class StockMovementSerializer(serializers.ModelSerializer):
    """
    Serializer for StockMovement model.
    
    Requirements:
    - 6.1: Display stock movements list with columns (date, product, warehouse, type, quantity, balance before, balance after, reference)
    - 6.3: Display full details including source document reference
    """
    
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_code = serializers.CharField(source='product.code', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    movement_type_display = serializers.CharField(source='get_movement_type_display', read_only=True)
    source_type_display = serializers.CharField(source='get_source_type_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    
    class Meta:
        model = StockMovement
        fields = [
            'id', 'product', 'product_name', 'product_code', 
            'warehouse', 'warehouse_name',
            'movement_type', 'movement_type_display',
            'source_type', 'source_type_display',
            'quantity', 'unit_cost', 'reference_number',
            'reference_type', 'reference_id',
            'balance_before', 'balance_after',
            'notes', 'created_by', 'created_by_name', 'created_at'
        ]
        read_only_fields = ['__all__']


class BarcodeSearchSerializer(serializers.Serializer):
    """Serializer for barcode search."""
    
    barcode = serializers.CharField(max_length=50)
