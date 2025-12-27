# Generated migration for Units Management feature

import django.db.models.deletion
from decimal import Decimal
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('inventory', '0001_initial'),
    ]

    operations = [
        # Remove is_base field from Unit model
        migrations.RemoveField(
            model_name='unit',
            name='is_base',
        ),
        # Add name_en field to Unit model
        migrations.AddField(
            model_name='unit',
            name='name_en',
            field=models.CharField(
                blank=True,
                max_length=50,
                null=True,
                verbose_name='الاسم بالإنجليزية'
            ),
        ),
        # Add unique constraints for Unit name and symbol
        migrations.AddConstraint(
            model_name='unit',
            constraint=models.UniqueConstraint(
                condition=models.Q(('is_deleted', False)),
                fields=('name',),
                name='unique_unit_name'
            ),
        ),
        migrations.AddConstraint(
            model_name='unit',
            constraint=models.UniqueConstraint(
                condition=models.Q(('is_deleted', False)),
                fields=('symbol',),
                name='unique_unit_symbol'
            ),
        ),
        # Create ProductUnit model
        migrations.CreateModel(
            name='ProductUnit',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                (
                    'created_at',
                    models.DateTimeField(
                        auto_now_add=True,
                        verbose_name='تاريخ الإنشاء'
                    ),
                ),
                (
                    'updated_at',
                    models.DateTimeField(
                        auto_now=True,
                        verbose_name='تاريخ التحديث'
                    ),
                ),
                (
                    'is_deleted',
                    models.BooleanField(
                        default=False,
                        verbose_name='محذوف'
                    ),
                ),
                (
                    'deleted_at',
                    models.DateTimeField(
                        blank=True,
                        null=True,
                        verbose_name='تاريخ الحذف'
                    ),
                ),
                (
                    'is_active',
                    models.BooleanField(
                        default=True,
                        verbose_name='نشط'
                    ),
                ),
                (
                    'conversion_factor',
                    models.DecimalField(
                        decimal_places=4,
                        default=Decimal('1.0000'),
                        max_digits=15,
                        verbose_name='معامل التحويل'
                    ),
                ),
                (
                    'is_base_unit',
                    models.BooleanField(
                        default=False,
                        verbose_name='الوحدة الأساسية'
                    ),
                ),
                (
                    'sale_price',
                    models.DecimalField(
                        decimal_places=2,
                        default=Decimal('0.00'),
                        max_digits=15,
                        verbose_name='سعر البيع'
                    ),
                ),
                (
                    'cost_price',
                    models.DecimalField(
                        decimal_places=2,
                        default=Decimal('0.00'),
                        max_digits=15,
                        verbose_name='سعر التكلفة'
                    ),
                ),
                (
                    'barcode',
                    models.CharField(
                        blank=True,
                        max_length=50,
                        null=True,
                        verbose_name='الباركود'
                    ),
                ),
                (
                    'created_by',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='%(class)s_created',
                        to=settings.AUTH_USER_MODEL,
                        verbose_name='أنشئ بواسطة',
                    ),
                ),
                (
                    'deleted_by',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='%(class)s_deleted',
                        to=settings.AUTH_USER_MODEL,
                        verbose_name='حذف بواسطة',
                    ),
                ),
                (
                    'product',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='product_units',
                        to='inventory.product',
                        verbose_name='المنتج',
                    ),
                ),
                (
                    'unit',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='product_units',
                        to='inventory.unit',
                        verbose_name='الوحدة',
                    ),
                ),
                (
                    'updated_by',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='%(class)s_updated',
                        to=settings.AUTH_USER_MODEL,
                        verbose_name='عدّل بواسطة',
                    ),
                ),
            ],
            options={
                'verbose_name': 'وحدة المنتج',
                'verbose_name_plural': 'وحدات المنتج',
                'unique_together': {('product', 'unit')},
            },
        ),
        # Add check constraint for positive conversion_factor
        migrations.AddConstraint(
            model_name='productunit',
            constraint=models.CheckConstraint(
                check=models.Q(('conversion_factor__gt', 0)),
                name='positive_conversion_factor'
            ),
        ),
    ]
