# Generated migration for adding product_unit and base_quantity to InvoiceItem

from decimal import Decimal
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0002_units_management'),
        ('sales', '0002_credit_sales_payments'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoiceitem',
            name='product_unit',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='invoice_items',
                to='inventory.productunit',
                verbose_name='وحدة المنتج'
            ),
        ),
        migrations.AddField(
            model_name='invoiceitem',
            name='base_quantity',
            field=models.DecimalField(
                decimal_places=4,
                default=Decimal('0.0000'),
                max_digits=15,
                verbose_name='الكمية بالوحدة الأساسية'
            ),
        ),
    ]
