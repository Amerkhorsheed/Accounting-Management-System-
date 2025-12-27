"""
System Settings Models - Configurable business settings stored in database
"""
from django.db import models
from decimal import Decimal
from apps.core.models import TimeStampedModel


class SystemSettings(TimeStampedModel):
    """
    Singleton model for storing system-wide settings.
    Uses key-value pairs for flexibility.
    """
    key = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='المفتاح'
    )
    value = models.TextField(
        verbose_name='القيمة'
    )
    description = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='الوصف'
    )

    class Meta:
        verbose_name = 'إعداد النظام'
        verbose_name_plural = 'إعدادات النظام'
        ordering = ['key']

    def __str__(self):
        return f"{self.key}: {self.value}"

    @classmethod
    def get_setting(cls, key: str, default=None):
        """Get a setting value by key."""
        try:
            return cls.objects.get(key=key).value
        except cls.DoesNotExist:
            return default

    @classmethod
    def set_setting(cls, key: str, value: str, description: str = ''):
        """Set a setting value."""
        obj, created = cls.objects.update_or_create(
            key=key,
            defaults={'value': value, 'description': description}
        )
        return obj


class Currency(TimeStampedModel):
    """
    Currency model for multi-currency support.
    """
    code = models.CharField(
        max_length=10,
        unique=True,
        verbose_name='رمز العملة'
    )
    name = models.CharField(
        max_length=50,
        verbose_name='اسم العملة'
    )
    name_en = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='الاسم بالإنجليزية'
    )
    symbol = models.CharField(
        max_length=10,
        verbose_name='الرمز'
    )
    exchange_rate = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        default=Decimal('1.0000'),
        verbose_name='سعر الصرف'
    )
    is_primary = models.BooleanField(
        default=False,
        verbose_name='العملة الأساسية'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='نشط'
    )
    decimal_places = models.PositiveSmallIntegerField(
        default=2,
        verbose_name='عدد الخانات العشرية'
    )

    class Meta:
        verbose_name = 'عملة'
        verbose_name_plural = 'العملات'
        ordering = ['-is_primary', 'code']

    def __str__(self):
        return f"{self.code} - {self.name}"

    def save(self, *args, **kwargs):
        # Ensure only one primary currency
        if self.is_primary:
            Currency.objects.filter(is_primary=True).exclude(pk=self.pk).update(is_primary=False)
            self.exchange_rate = Decimal('1.0000')  # Primary currency always = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_primary(cls):
        """Get the primary currency."""
        return cls.objects.filter(is_primary=True, is_active=True).first()

    @classmethod
    def convert(cls, amount: Decimal, from_currency, to_currency) -> Decimal:
        """Convert amount between currencies.
        
        Raises:
            Currency.DoesNotExist: If currency code is not found
            ValueError: If exchange rate is zero or negative
        """
        if from_currency == to_currency:
            return amount
        
        # Convert to primary currency first, then to target
        if isinstance(from_currency, str):
            from_currency = cls.objects.get(code=from_currency)
        if isinstance(to_currency, str):
            to_currency = cls.objects.get(code=to_currency)
        
        # Validate exchange rates are positive and non-zero
        if from_currency.exchange_rate <= 0:
            raise ValueError(f"سعر صرف العملة '{from_currency.code}' غير صالح: يجب أن يكون أكبر من صفر")
        if to_currency.exchange_rate <= 0:
            raise ValueError(f"سعر صرف العملة '{to_currency.code}' غير صالح: يجب أن يكون أكبر من صفر")
        
        # amount in primary = amount * from_rate
        # amount in target = amount_in_primary / to_rate
        primary_amount = amount * from_currency.exchange_rate
        target_amount = primary_amount / to_currency.exchange_rate
        
        return target_amount.quantize(Decimal(f'0.{"0" * to_currency.decimal_places}'))


class TaxRate(TimeStampedModel):
    """
    Tax rate configuration.
    Supports multiple tax types (VAT, Sales Tax, etc.)
    """
    name = models.CharField(
        max_length=100,
        verbose_name='اسم الضريبة'
    )
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='رمز الضريبة'
    )
    rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='نسبة الضريبة %'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='نشط'
    )
    is_default = models.BooleanField(
        default=False,
        verbose_name='الافتراضي'
    )
    description = models.TextField(
        blank=True,
        verbose_name='الوصف'
    )

    class Meta:
        verbose_name = 'معدل الضريبة'
        verbose_name_plural = 'معدلات الضريبة'
        ordering = ['-is_default', 'name']

    def __str__(self):
        return f"{self.name} ({self.rate}%)"

    def save(self, *args, **kwargs):
        if self.is_default:
            TaxRate.objects.filter(is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    @classmethod
    def get_default(cls):
        """Get the default tax rate."""
        tax = cls.objects.filter(is_default=True, is_active=True).first()
        return tax.rate if tax else Decimal('0.00')

    @classmethod
    def is_tax_enabled(cls):
        """Check if tax is enabled (has active tax rate > 0)."""
        return cls.objects.filter(is_active=True, rate__gt=0).exists()
