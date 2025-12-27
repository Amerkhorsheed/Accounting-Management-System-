"""
Expenses Models
"""
from django.db import models
from django.conf import settings
from decimal import Decimal
from apps.core.models import BaseModel
from apps.core.utils import generate_code


class ExpenseCategory(BaseModel):
    """
    Expense category model.
    """
    name = models.CharField(
        max_length=100,
        verbose_name='اسم الفئة'
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

    class Meta:
        verbose_name = 'فئة المصروفات'
        verbose_name_plural = 'فئات المصروفات'
        ordering = ['name']

    def __str__(self):
        return self.name


class Expense(BaseModel):
    """
    Expense record model.
    """
    
    class PaymentMethod(models.TextChoices):
        CASH = 'cash', 'نقداً'
        BANK = 'bank', 'تحويل بنكي'
        CHECK = 'check', 'شيك'
        CARD = 'card', 'بطاقة'

    expense_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='رقم المصروف'
    )
    category = models.ForeignKey(
        ExpenseCategory,
        on_delete=models.PROTECT,
        related_name='expenses',
        verbose_name='الفئة'
    )
    expense_date = models.DateField(
        verbose_name='تاريخ المصروف'
    )
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name='المبلغ'
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
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CASH,
        verbose_name='طريقة الدفع'
    )
    payee = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='المستفيد'
    )
    reference = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='المرجع'
    )
    description = models.TextField(
        verbose_name='الوصف'
    )
    attachment = models.FileField(
        upload_to='expenses/',
        blank=True,
        null=True,
        verbose_name='المرفق'
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
        related_name='approved_expenses',
        verbose_name='اعتمد بواسطة'
    )
    is_approved = models.BooleanField(
        default=False,
        verbose_name='معتمد'
    )

    class Meta:
        verbose_name = 'مصروف'
        verbose_name_plural = 'المصروفات'
        ordering = ['-expense_date', '-expense_number']

    def __str__(self):
        return f"{self.expense_number} - {self.description[:50]}"

    def save(self, *args, **kwargs):
        if not self.expense_number:
            self.expense_number = generate_code('EXP')
        self.total_amount = self.amount + self.tax_amount
        super().save(*args, **kwargs)
