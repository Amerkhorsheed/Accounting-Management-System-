"""
Sales Models - Customer, Invoice, and Payment Management
"""
from django.db import models
from django.conf import settings
from decimal import Decimal
from apps.core.models import BaseModel, AddressModel, ContactModel
from apps.core.utils import generate_code
from apps.inventory.models import Product, Warehouse


class TransactionCurrency(models.TextChoices):
    USD = 'USD', 'USD'
    SYP_OLD = 'SYP_OLD', 'الليرة السورية القديمة'
    SYP_NEW = 'SYP_NEW', 'الليرة السورية الجديدة'


class Customer(BaseModel, AddressModel, ContactModel):
    """
    Customer model.
    """
    
    class CustomerType(models.TextChoices):
        INDIVIDUAL = 'individual', 'فرد'
        COMPANY = 'company', 'شركة'
        GOVERNMENT = 'government', 'حكومي'

    name = models.CharField(
        max_length=255,
        verbose_name='اسم العميل'
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
        verbose_name='كود العميل'
    )
    customer_type = models.CharField(
        max_length=20,
        choices=CustomerType.choices,
        default=CustomerType.INDIVIDUAL,
        verbose_name='نوع العميل'
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
    credit_limit = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='حد الائتمان'
    )
    payment_terms = models.PositiveIntegerField(
        default=0,
        verbose_name='شروط الدفع (أيام)'
    )
    discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='نسبة الخصم'
    )
    opening_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='الرصيد الافتتاحي'
    )
    opening_balance_usd = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='الرصيد الافتتاحي (USD)'
    )
    current_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='الرصيد الحالي'
    )
    current_balance_usd = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='الرصيد الحالي (USD)'
    )
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name='ملاحظات'
    )
    salesperson = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='customers',
        verbose_name='مندوب المبيعات'
    )

    class Meta:
        verbose_name = 'عميل'
        verbose_name_plural = 'العملاء'
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = generate_code('CUS', 5)
        super().save(*args, **kwargs)

    @property
    def available_credit(self):
        """Calculate available credit."""
        return self.credit_limit - self.current_balance

    @property
    def credit_warning_threshold(self) -> bool:
        """Returns True if balance >= 80% of credit limit."""
        if self.credit_limit <= 0:
            return False
        return self.current_balance >= (self.credit_limit * Decimal('0.8'))

    @property
    def is_over_credit_limit(self) -> bool:
        """Returns True if balance >= credit limit."""
        if self.credit_limit <= 0:
            return False
        return self.current_balance >= self.credit_limit


class Invoice(BaseModel):
    """
    Sales Invoice model.
    """
    
    class InvoiceType(models.TextChoices):
        CASH = 'cash', 'نقدي'
        CREDIT = 'credit', 'آجل'
        RETURN = 'return', 'مرتجع'

    class Status(models.TextChoices):
        DRAFT = 'draft', 'مسودة'
        CONFIRMED = 'confirmed', 'مؤكد'
        PAID = 'paid', 'مدفوع'
        PARTIAL = 'partial', 'مدفوع جزئياً'
        CANCELLED = 'cancelled', 'ملغي'

    invoice_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='رقم الفاتورة'
    )
    invoice_type = models.CharField(
        max_length=20,
        choices=InvoiceType.choices,
        default=InvoiceType.CASH,
        verbose_name='نوع الفاتورة'
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name='invoices',
        verbose_name='العميل'
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name='invoices',
        verbose_name='المستودع'
    )
    invoice_date = models.DateField(
        verbose_name='تاريخ الفاتورة'
    )
    due_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='تاريخ الاستحقاق'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name='الحالة'
    )

    transaction_currency = models.CharField(
        max_length=10,
        choices=TransactionCurrency.choices,
        default=TransactionCurrency.SYP_OLD,
        verbose_name='عملة المعاملة'
    )
    fx_rate_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='تاريخ سعر الصرف'
    )
    usd_to_syp_old_snapshot = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        blank=True,
        null=True,
        verbose_name='سعر صرف الدولار مقابل الليرة القديمة'
    )
    usd_to_syp_new_snapshot = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        blank=True,
        null=True,
        verbose_name='سعر صرف الدولار مقابل الليرة الجديدة'
    )
    
    # Amounts
    subtotal = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='المجموع الفرعي'
    )
    discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='نسبة الخصم'
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
    total_amount_usd = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='المبلغ الإجمالي (USD)'
    )
    paid_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='المبلغ المدفوع'
    )
    paid_amount_usd = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='المبلغ المدفوع (USD)'
    )
    
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name='ملاحظات'
    )
    internal_notes = models.TextField(
        blank=True,
        null=True,
        verbose_name='ملاحظات داخلية'
    )
    
    # Return reference
    return_for = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='returns',
        verbose_name='مرتجع لفاتورة'
    )

    class Meta:
        verbose_name = 'فاتورة'
        verbose_name_plural = 'الفواتير'
        ordering = ['-invoice_date', '-invoice_number']

    def __str__(self):
        return f"{self.invoice_number} - {self.customer.name}"

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = generate_code('INV')
        super().save(*args, **kwargs)

    @property
    def remaining_amount(self):
        return self.total_amount - self.paid_amount

    @property
    def remaining_amount_usd(self):
        return self.total_amount_usd - self.paid_amount_usd

    def calculate_totals(self):
        """Recalculate invoice totals from items."""
        items = self.items.all()
        self.subtotal = sum(item.subtotal for item in items)
        
        # Apply invoice-level discount
        if self.discount_percent > 0:
            self.discount_amount = (self.subtotal * self.discount_percent) / 100
        
        taxable = self.subtotal - self.discount_amount
        self.tax_amount = sum(item.tax_amount for item in items)
        self.total_amount = taxable + self.tax_amount

        if self.transaction_currency == TransactionCurrency.USD:
            self.total_amount_usd = self.total_amount
            self.paid_amount_usd = self.paid_amount
        elif self.usd_to_syp_old_snapshot is not None and self.usd_to_syp_new_snapshot is not None:
            from apps.core.utils import to_usd

            self.total_amount_usd = to_usd(
                self.total_amount,
                self.transaction_currency,
                usd_to_syp_old=self.usd_to_syp_old_snapshot,
                usd_to_syp_new=self.usd_to_syp_new_snapshot
            )
            self.paid_amount_usd = to_usd(
                self.paid_amount,
                self.transaction_currency,
                usd_to_syp_old=self.usd_to_syp_old_snapshot,
                usd_to_syp_new=self.usd_to_syp_new_snapshot
            )

        self.save(
            update_fields=[
                'subtotal',
                'discount_amount',
                'tax_amount',
                'total_amount',
                'total_amount_usd',
                'paid_amount_usd',
            ]
        )


class InvoiceItem(BaseModel):
    """
    Invoice line item.
    """
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='الفاتورة'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='invoice_items',
        verbose_name='المنتج'
    )
    product_unit = models.ForeignKey(
        'inventory.ProductUnit',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='invoice_items',
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
    unit_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name='سعر الوحدة'
    )
    cost_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='سعر التكلفة'
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
        verbose_name = 'بند الفاتورة'
        verbose_name_plural = 'بنود الفاتورة'

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    @property
    def subtotal(self):
        if self.quantity is None or self.unit_price is None:
            return Decimal('0.00')
        return self.quantity * self.unit_price

    @property
    def discount_amount(self):
        if self.discount_percent is None:
            return Decimal('0.00')
        return (self.subtotal * self.discount_percent) / 100

    @property
    def taxable_amount(self):
        return self.subtotal - self.discount_amount

    @property
    def tax_amount(self):
        if self.tax_rate is None:
            return Decimal('0.00')
        return (self.taxable_amount * self.tax_rate) / 100

    @property
    def total(self):
        return self.taxable_amount + self.tax_amount

    @property
    def profit(self):
        """Calculate profit for this item."""
        if self.quantity is None or self.unit_price is None or self.cost_price is None:
            return Decimal('0.00')
        return (self.unit_price - self.cost_price) * self.quantity


class Payment(BaseModel):
    """
    Customer payment model.
    """
    
    class PaymentMethod(models.TextChoices):
        CASH = 'cash', 'نقداً'
        CARD = 'card', 'بطاقة'
        BANK = 'bank', 'تحويل بنكي'
        CHECK = 'check', 'شيك'
        CREDIT = 'credit', 'ائتمان'

    payment_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='رقم سند القبض'
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name='payments',
        verbose_name='العميل'
    )
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments',
        verbose_name='الفاتورة'
    )
    payment_date = models.DateField(
        verbose_name='تاريخ الدفع'
    )

    transaction_currency = models.CharField(
        max_length=10,
        choices=TransactionCurrency.choices,
        default=TransactionCurrency.SYP_OLD,
        verbose_name='عملة المعاملة'
    )
    fx_rate_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='تاريخ سعر الصرف'
    )
    usd_to_syp_old_snapshot = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        blank=True,
        null=True,
        verbose_name='سعر صرف الدولار مقابل الليرة القديمة'
    )
    usd_to_syp_new_snapshot = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        blank=True,
        null=True,
        verbose_name='سعر صرف الدولار مقابل الليرة الجديدة'
    )
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name='المبلغ'
    )
    amount_usd = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='المبلغ (USD)'
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
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='received_payments',
        verbose_name='استلم بواسطة'
    )

    class Meta:
        verbose_name = 'سند قبض'
        verbose_name_plural = 'سندات القبض'
        ordering = ['-payment_date', '-payment_number']

    def __str__(self):
        return f"{self.payment_number} - {self.customer.name}: {self.amount}"

    def save(self, *args, **kwargs):
        if not self.payment_number:
            self.payment_number = generate_code('REC')
        super().save(*args, **kwargs)


class SalesReturn(BaseModel):
    """
    Sales return model.
    """
    return_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='رقم المرتجع'
    )
    original_invoice = models.ForeignKey(
        Invoice,
        on_delete=models.PROTECT,
        related_name='sales_returns',
        verbose_name='الفاتورة الأصلية'
    )
    return_date = models.DateField(
        verbose_name='تاريخ المرتجع'
    )
    transaction_currency = models.CharField(
        max_length=10,
        choices=TransactionCurrency.choices,
        default=TransactionCurrency.SYP_OLD,
        verbose_name='عملة المعاملة'
    )
    fx_rate_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='تاريخ سعر الصرف'
    )
    usd_to_syp_old_snapshot = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        blank=True,
        null=True,
        verbose_name='سعر صرف الدولار مقابل الليرة القديمة'
    )
    usd_to_syp_new_snapshot = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        blank=True,
        null=True,
        verbose_name='سعر صرف الدولار مقابل الليرة الجديدة'
    )
    total_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='المبلغ الإجمالي'
    )
    total_amount_usd = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='المبلغ الإجمالي (USD)'
    )
    reason = models.TextField(
        verbose_name='سبب الإرجاع'
    )
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name='ملاحظات'
    )

    class Meta:
        verbose_name = 'مرتجع مبيعات'
        verbose_name_plural = 'مرتجعات المبيعات'
        ordering = ['-return_date', '-return_number']

    def __str__(self):
        return f"{self.return_number} - {self.original_invoice.invoice_number}"

    def save(self, *args, **kwargs):
        if not self.return_number:
            self.return_number = generate_code('RET')
        super().save(*args, **kwargs)


class SalesReturnItem(BaseModel):
    """
    Sales return line item.
    """
    sales_return = models.ForeignKey(
        SalesReturn,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='المرتجع'
    )
    invoice_item = models.ForeignKey(
        InvoiceItem,
        on_delete=models.PROTECT,
        related_name='return_items',
        verbose_name='بند الفاتورة'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='return_items',
        verbose_name='المنتج'
    )
    quantity = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name='الكمية المرتجعة'
    )
    unit_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name='سعر الوحدة'
    )
    reason = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='سبب الإرجاع'
    )

    class Meta:
        verbose_name = 'بند المرتجع'
        verbose_name_plural = 'بنود المرتجع'

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    @property
    def total(self):
        return self.quantity * self.unit_price


class PaymentAllocation(BaseModel):
    """
    Tracks allocation of payments to specific invoices.
    Enables partial payments across multiple invoices.
    """
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name='allocations',
        verbose_name='سند القبض'
    )
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.PROTECT,
        related_name='payment_allocations',
        verbose_name='الفاتورة'
    )
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name='المبلغ المخصص'
    )
    amount_usd = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='المبلغ المخصص (USD)'
    )

    class Meta:
        verbose_name = 'تخصيص دفعة'
        verbose_name_plural = 'تخصيصات الدفعات'
        unique_together = ['payment', 'invoice']

    def __str__(self):
        return f"{self.payment.payment_number} -> {self.invoice.invoice_number}: {self.amount}"


class CreditLimitOverride(BaseModel):
    """
    Audit log for credit limit override decisions.
    Records when a user bypasses credit limit restrictions.
    """
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='credit_overrides',
        verbose_name='العميل'
    )
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='credit_overrides',
        verbose_name='الفاتورة'
    )
    override_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name='مبلغ التجاوز'
    )
    reason = models.TextField(
        verbose_name='سبب التجاوز'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='approved_credit_overrides',
        verbose_name='تمت الموافقة بواسطة'
    )

    class Meta:
        verbose_name = 'تجاوز حد الائتمان'
        verbose_name_plural = 'تجاوزات حد الائتمان'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.customer.name} - تجاوز: {self.override_amount}"
