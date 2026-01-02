"""
Inventory Models - Products, Categories, Stock Management
"""
from django.db import models
from django.conf import settings
from decimal import Decimal
from apps.core.models import BaseModel, TimeStampedModel
from apps.core.utils import generate_barcode, generate_code


class Category(BaseModel):
    """
    Product category with hierarchical structure.
    """
    name = models.CharField(
        max_length=100,
        verbose_name='اسم الفئة'
    )
    name_en = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='الاسم بالإنجليزية'
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='الفئة الأب'
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='الوصف'
    )
    image = models.ImageField(
        upload_to='categories/',
        blank=True,
        null=True,
        verbose_name='الصورة'
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name='ترتيب العرض'
    )

    class Meta:
        verbose_name = 'فئة'
        verbose_name_plural = 'الفئات'
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name

    @property
    def full_path(self):
        """Get full category path with parents."""
        if self.parent:
            return f"{self.parent.full_path} > {self.name}"
        return self.name


class Unit(BaseModel):
    """
    Unit of measure for products.
    """
    name = models.CharField(
        max_length=50,
        verbose_name='اسم الوحدة'
    )
    name_en = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='الاسم بالإنجليزية'
    )
    symbol = models.CharField(
        max_length=10,
        verbose_name='الرمز'
    )

    class Meta:
        verbose_name = 'وحدة قياس'
        verbose_name_plural = 'وحدات القياس'
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['name'],
                condition=models.Q(is_deleted=False),
                name='unique_unit_name'
            ),
            models.UniqueConstraint(
                fields=['symbol'],
                condition=models.Q(is_deleted=False),
                name='unique_unit_symbol'
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.symbol})"


class ProductUnit(BaseModel):
    """
    Product-specific unit configuration with conversion factor and pricing.
    """
    product = models.ForeignKey(
        'Product',
        on_delete=models.CASCADE,
        related_name='product_units',
        verbose_name='المنتج'
    )
    unit = models.ForeignKey(
        Unit,
        on_delete=models.PROTECT,
        related_name='product_units',
        verbose_name='الوحدة'
    )
    conversion_factor = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        default=Decimal('1.0000'),
        verbose_name='معامل التحويل'
    )
    is_base_unit = models.BooleanField(
        default=False,
        verbose_name='الوحدة الأساسية'
    )
    sale_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='سعر البيع'
    )
    sale_price_usd = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='سعر البيع (USD)'
    )
    cost_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='سعر التكلفة'
    )
    cost_price_usd = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='سعر التكلفة (USD)'
    )
    barcode = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='الباركود'
    )

    class Meta:
        verbose_name = 'وحدة المنتج'
        verbose_name_plural = 'وحدات المنتج'
        unique_together = ['product', 'unit']
        constraints = [
            models.CheckConstraint(
                check=models.Q(conversion_factor__gt=0),
                name='positive_conversion_factor'
            ),
        ]

    def __str__(self):
        return f"{self.product.name} - {self.unit.name}"

    def convert_to_base(self, quantity: Decimal) -> Decimal:
        """Convert quantity from this unit to base unit."""
        return quantity * self.conversion_factor

    def convert_from_base(self, base_quantity: Decimal) -> Decimal:
        """Convert quantity from base unit to this unit."""
        return base_quantity / self.conversion_factor


class Warehouse(BaseModel):
    """
    Warehouse/storage location.
    """
    name = models.CharField(
        max_length=100,
        verbose_name='اسم المستودع'
    )
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='رمز المستودع'
    )
    address = models.TextField(
        blank=True,
        null=True,
        verbose_name='العنوان'
    )
    is_default = models.BooleanField(
        default=False,
        verbose_name='المستودع الافتراضي'
    )
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_warehouses',
        verbose_name='مدير المستودع'
    )

    class Meta:
        verbose_name = 'مستودع'
        verbose_name_plural = 'المستودعات'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.is_default:
            # Ensure only one default warehouse
            Warehouse.objects.filter(is_default=True).update(is_default=False)
        super().save(*args, **kwargs)


class Product(BaseModel):
    """
    Product/item in inventory.
    """
    
    class ProductType(models.TextChoices):
        GOODS = 'goods', 'بضاعة'
        SERVICE = 'service', 'خدمة'
        CONSUMABLE = 'consumable', 'مستهلك'

    # Basic Information
    name = models.CharField(
        max_length=255,
        verbose_name='اسم المنتج'
    )
    name_en = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='الاسم بالإنجليزية'
    )
    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='كود المنتج'
    )
    barcode = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        verbose_name='الباركود'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
        verbose_name='الفئة'
    )
    product_type = models.CharField(
        max_length=20,
        choices=ProductType.choices,
        default=ProductType.GOODS,
        verbose_name='نوع المنتج'
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='الوصف'
    )
    
    # Units
    unit = models.ForeignKey(
        Unit,
        on_delete=models.PROTECT,
        related_name='products',
        verbose_name='وحدة القياس'
    )
    
    # Pricing
    cost_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='سعر التكلفة'
    )
    cost_price_usd = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='سعر التكلفة (USD)'
    )
    sale_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='سعر البيع'
    )
    sale_price_usd = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='سعر البيع (USD)'
    )
    wholesale_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='سعر الجملة'
    )
    wholesale_price_usd = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='سعر الجملة (USD)'
    )
    minimum_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='أقل سعر بيع'
    )
    minimum_price_usd = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='أقل سعر بيع (USD)'
    )
    
    # Tax
    is_taxable = models.BooleanField(
        default=False,
        verbose_name='خاضع للضريبة'
    )
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='نسبة الضريبة'
    )
    
    # Stock Settings
    track_stock = models.BooleanField(
        default=True,
        verbose_name='تتبع المخزون'
    )
    minimum_stock = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='الحد الأدنى للمخزون'
    )
    maximum_stock = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='الحد الأقصى للمخزون'
    )
    reorder_point = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='نقطة إعادة الطلب'
    )
    
    # Media
    image = models.ImageField(
        upload_to='products/',
        blank=True,
        null=True,
        verbose_name='صورة المنتج'
    )
    
    # Additional Info
    brand = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='العلامة التجارية'
    )
    model = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='الموديل'
    )
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name='ملاحظات'
    )

    class Meta:
        verbose_name = 'منتج'
        verbose_name_plural = 'المنتجات'
        ordering = ['name']
        indexes = [
            models.Index(fields=['barcode']),
            models.Index(fields=['code']),
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = generate_code('PRD')
        if not self.barcode:
            self.barcode = generate_barcode()
        super().save(*args, **kwargs)

    @property
    def profit_margin(self):
        """Calculate profit margin percentage."""
        cost = self.cost_price_usd if self.cost_price_usd is not None and self.cost_price_usd > 0 else self.cost_price
        sale = self.sale_price_usd if self.sale_price_usd is not None and self.sale_price_usd > 0 else self.sale_price
        if cost and cost > 0:
            return ((sale - cost) / cost) * 100
        return Decimal('0.00')

    @property
    def price_with_tax(self):
        """Calculate sale price including tax."""
        sale = self.sale_price_usd if self.sale_price_usd is not None and self.sale_price_usd > 0 else self.sale_price
        if self.is_taxable:
            tax_amount = (sale * self.tax_rate) / 100
            return sale + tax_amount
        return sale


class Stock(TimeStampedModel):
    """
    Stock levels per product per warehouse.
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='stock_levels',
        verbose_name='المنتج'
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name='stock_levels',
        verbose_name='المستودع'
    )
    quantity = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='الكمية'
    )
    reserved_quantity = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='الكمية المحجوزة'
    )

    class Meta:
        verbose_name = 'مخزون'
        verbose_name_plural = 'المخزون'
        unique_together = ['product', 'warehouse']

    def __str__(self):
        return f"{self.product.name} - {self.warehouse.name}: {self.quantity}"

    @property
    def available_quantity(self):
        """Get available quantity (total - reserved)."""
        return self.quantity - self.reserved_quantity

    @property
    def is_low_stock(self):
        """
        Check if stock is below minimum.
        
        Both quantity and minimum_stock are stored in base unit quantities,
        ensuring accurate comparison regardless of which unit was used for
        sales or purchases.
        
        Requirements: 5.4 - Low stock alerts use base unit quantities
        """
        return self.quantity <= self.product.minimum_stock


class StockMovement(TimeStampedModel):
    """
    Stock movement/transaction history.
    """
    
    class MovementType(models.TextChoices):
        IN = 'in', 'وارد'
        OUT = 'out', 'صادر'
        ADJUSTMENT = 'adjustment', 'تسوية'
        TRANSFER = 'transfer', 'تحويل'
        RETURN = 'return', 'مرتجع'
        DAMAGE = 'damage', 'تالف'

    class SourceType(models.TextChoices):
        PURCHASE = 'purchase', 'مشتريات'
        SALE = 'sale', 'مبيعات'
        ADJUSTMENT = 'adjustment', 'تسوية يدوية'
        TRANSFER = 'transfer', 'تحويل بين مستودعات'
        OPENING = 'opening', 'رصيد افتتاحي'
        RETURN = 'return', 'مرتجع'

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='movements',
        verbose_name='المنتج'
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.CASCADE,
        related_name='movements',
        verbose_name='المستودع'
    )
    movement_type = models.CharField(
        max_length=20,
        choices=MovementType.choices,
        verbose_name='نوع الحركة'
    )
    source_type = models.CharField(
        max_length=20,
        choices=SourceType.choices,
        verbose_name='مصدر الحركة'
    )
    quantity = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name='الكمية'
    )
    unit_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='تكلفة الوحدة'
    )
    reference_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='رقم المرجع'
    )
    reference_type = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='نوع المرجع'
    )
    reference_id = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name='معرف المرجع'
    )
    balance_before = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name='الرصيد قبل'
    )
    balance_after = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name='الرصيد بعد'
    )
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name='ملاحظات'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='stock_movements',
        verbose_name='بواسطة'
    )

    class Meta:
        verbose_name = 'حركة مخزون'
        verbose_name_plural = 'حركات المخزون'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['product', 'warehouse']),
            models.Index(fields=['created_at']),
            models.Index(fields=['reference_type', 'reference_id']),
        ]

    def __str__(self):
        return f"{self.product.name} - {self.get_movement_type_display()}: {self.quantity}"
