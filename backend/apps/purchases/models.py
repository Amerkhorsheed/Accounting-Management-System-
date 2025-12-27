"""
Purchases Models - Supplier and Purchase Order Management
"""
from django.db import models
from django.conf import settings
from decimal import Decimal
from apps.core.models import BaseModel, AddressModel, ContactModel
from apps.core.utils import generate_code
from apps.inventory.models import Product, Warehouse


class Supplier(BaseModel, AddressModel, ContactModel):
    """
    Supplier/Vendor model.
    """
    name = models.CharField(
        max_length=255,
        verbose_name='اسم المورد'
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
        verbose_name='كود المورد'
    )
    tax_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='الرقم الضريبي'
    )
    commercial_register = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='السجل التجاري'
    )
    contact_person = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='الشخص المسؤول'
    )
    payment_terms = models.PositiveIntegerField(
        default=30,
        verbose_name='شروط الدفع (أيام)'
    )
    credit_limit = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='حد الائتمان'
    )
    opening_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='الرصيد الافتتاحي'
    )
    current_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='الرصيد الحالي'
    )
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name='ملاحظات'
    )

    class Meta:
        verbose_name = 'مورد'
        verbose_name_plural = 'الموردون'
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = generate_code('SUP', 5)
        super().save(*args, **kwargs)


class PurchaseOrder(BaseModel):
    """
    Purchase Order model.
    """
    
    class Status(models.TextChoices):
        DRAFT = 'draft', 'مسودة'
        PENDING = 'pending', 'قيد الانتظار'
        APPROVED = 'approved', 'معتمد'
        ORDERED = 'ordered', 'تم الطلب'
        PARTIAL = 'partial', 'استلام جزئي'
        RECEIVED = 'received', 'تم الاستلام'
        CANCELLED = 'cancelled', 'ملغي'

    order_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='رقم أمر الشراء'
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        related_name='purchase_orders',
        verbose_name='المورد'
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name='purchase_orders',
        verbose_name='المستودع'
    )
    order_date = models.DateField(
        verbose_name='تاريخ الطلب'
    )
    expected_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='تاريخ التسليم المتوقع'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name='الحالة'
    )
    
    # Amounts
    subtotal = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='المجموع الفرعي'
    )
    discount_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='مبلغ الخصم'
    )
    tax_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='مبلغ الضريبة'
    )
    total_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='المبلغ الإجمالي'
    )
    paid_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='المبلغ المدفوع'
    )
    
    reference = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='المرجع'
    )
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name='ملاحظات'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_purchase_orders',
        verbose_name='اعتمد بواسطة'
    )
    approved_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='تاريخ الاعتماد'
    )

    class Meta:
        verbose_name = 'أمر شراء'
        verbose_name_plural = 'أوامر الشراء'
        ordering = ['-order_date', '-order_number']

    def __str__(self):
        return f"{self.order_number} - {self.supplier.name}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = generate_code('PO')
        super().save(*args, **kwargs)

    @property
    def remaining_amount(self):
        return self.total_amount - self.paid_amount

    def calculate_totals(self):
        """Recalculate order totals from items."""
        items = self.items.all()
        self.subtotal = sum(item.total for item in items)
        self.tax_amount = sum(item.tax_amount for item in items)
        self.total_amount = self.subtotal + self.tax_amount - self.discount_amount
        self.save(update_fields=['subtotal', 'tax_amount', 'total_amount'])


class PurchaseOrderItem(BaseModel):
    """
    Purchase Order line item.
    """
    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='أمر الشراء'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='purchase_items',
        verbose_name='المنتج'
    )
    product_unit = models.ForeignKey(
        'inventory.ProductUnit',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='purchase_items',
        verbose_name='وحدة المنتج'
    )
    quantity = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name='الكمية'
    )
    base_quantity = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        default=Decimal('0.0000'),
        verbose_name='الكمية بالوحدة الأساسية'
    )
    received_quantity = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='الكمية المستلمة'
    )
    unit_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name='سعر الوحدة'
    )
    discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='نسبة الخصم'
    )
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('15.00'),
        verbose_name='نسبة الضريبة'
    )
    notes = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='ملاحظات'
    )

    class Meta:
        verbose_name = 'بند أمر الشراء'
        verbose_name_plural = 'بنود أمر الشراء'

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    @property
    def subtotal(self):
        return self.quantity * self.unit_price

    @property
    def discount_amount(self):
        return (self.subtotal * self.discount_percent) / 100

    @property
    def taxable_amount(self):
        return self.subtotal - self.discount_amount

    @property
    def tax_amount(self):
        return (self.taxable_amount * self.tax_rate) / 100

    @property
    def total(self):
        return self.taxable_amount + self.tax_amount

    @property
    def remaining_quantity(self):
        return self.quantity - self.received_quantity


class GoodsReceivedNote(BaseModel):
    """
    Goods Received Note (GRN) - for receiving goods against PO.
    """
    grn_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='رقم سند الاستلام'
    )
    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.PROTECT,
        related_name='grns',
        verbose_name='أمر الشراء'
    )
    received_date = models.DateField(
        verbose_name='تاريخ الاستلام'
    )
    supplier_invoice_no = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='رقم فاتورة المورد'
    )
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name='ملاحظات'
    )
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='received_grns',
        verbose_name='استلم بواسطة'
    )

    class Meta:
        verbose_name = 'سند استلام'
        verbose_name_plural = 'سندات الاستلام'
        ordering = ['-received_date', '-grn_number']

    def __str__(self):
        return f"{self.grn_number} - {self.purchase_order.order_number}"

    def save(self, *args, **kwargs):
        if not self.grn_number:
            self.grn_number = generate_code('GRN')
        super().save(*args, **kwargs)


class GRNItem(BaseModel):
    """
    Goods Received Note line item.
    """
    grn = models.ForeignKey(
        GoodsReceivedNote,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='سند الاستلام'
    )
    po_item = models.ForeignKey(
        PurchaseOrderItem,
        on_delete=models.PROTECT,
        related_name='grn_items',
        verbose_name='بند أمر الشراء'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='grn_items',
        verbose_name='المنتج'
    )
    quantity_received = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name='الكمية المستلمة'
    )
    notes = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='ملاحظات'
    )

    class Meta:
        verbose_name = 'بند سند الاستلام'
        verbose_name_plural = 'بنود سند الاستلام'

    def __str__(self):
        return f"{self.product.name} x {self.quantity_received}"


class SupplierPayment(BaseModel):
    """
    Payment to supplier.
    """
    
    class PaymentMethod(models.TextChoices):
        CASH = 'cash', 'نقداً'
        BANK = 'bank', 'تحويل بنكي'
        CHECK = 'check', 'شيك'
        CREDIT = 'credit', 'بطاقة ائتمان'

    payment_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='رقم سند الصرف'
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        related_name='payments',
        verbose_name='المورد'
    )
    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments',
        verbose_name='أمر الشراء'
    )
    payment_date = models.DateField(
        verbose_name='تاريخ الدفع'
    )
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name='المبلغ'
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CASH,
        verbose_name='طريقة الدفع'
    )
    reference = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='المرجع'
    )
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name='ملاحظات'
    )

    class Meta:
        verbose_name = 'سند صرف'
        verbose_name_plural = 'سندات الصرف'
        ordering = ['-payment_date', '-payment_number']

    def __str__(self):
        return f"{self.payment_number} - {self.supplier.name}: {self.amount}"

    def save(self, *args, **kwargs):
        if not self.payment_number:
            self.payment_number = generate_code('PAY')
        super().save(*args, **kwargs)
