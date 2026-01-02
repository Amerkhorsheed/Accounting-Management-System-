from decimal import Decimal

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("purchases", "0002_purchase_order_item_units"),
    ]

    operations = [
        migrations.AddField(
            model_name="supplier",
            name="opening_balance_usd",
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal("0.00"),
                max_digits=15,
                verbose_name="الرصيد الافتتاحي (USD)",
            ),
        ),
        migrations.AddField(
            model_name="supplier",
            name="current_balance_usd",
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal("0.00"),
                max_digits=15,
                verbose_name="الرصيد الحالي (USD)",
            ),
        ),
        migrations.AddField(
            model_name="purchaseorder",
            name="transaction_currency",
            field=models.CharField(
                choices=[
                    ("USD", "USD"),
                    ("SYP_OLD", "الليرة السورية القديمة"),
                    ("SYP_NEW", "الليرة السورية الجديدة"),
                ],
                default="USD",
                max_length=10,
                verbose_name="عملة المعاملة",
            ),
        ),
        migrations.AddField(
            model_name="purchaseorder",
            name="fx_rate_date",
            field=models.DateField(
                blank=True,
                null=True,
                verbose_name="تاريخ سعر الصرف",
            ),
        ),
        migrations.AddField(
            model_name="purchaseorder",
            name="usd_to_syp_old_snapshot",
            field=models.DecimalField(
                blank=True,
                decimal_places=6,
                max_digits=18,
                null=True,
                verbose_name="سعر صرف الدولار مقابل الليرة القديمة",
            ),
        ),
        migrations.AddField(
            model_name="purchaseorder",
            name="usd_to_syp_new_snapshot",
            field=models.DecimalField(
                blank=True,
                decimal_places=6,
                max_digits=18,
                null=True,
                verbose_name="سعر صرف الدولار مقابل الليرة الجديدة",
            ),
        ),
        migrations.AddField(
            model_name="purchaseorder",
            name="total_amount_usd",
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal("0.00"),
                max_digits=15,
                verbose_name="المبلغ الإجمالي (USD)",
            ),
        ),
        migrations.AddField(
            model_name="purchaseorder",
            name="paid_amount_usd",
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal("0.00"),
                max_digits=15,
                verbose_name="المبلغ المدفوع (USD)",
            ),
        ),
        migrations.AddField(
            model_name="supplierpayment",
            name="transaction_currency",
            field=models.CharField(
                choices=[
                    ("USD", "USD"),
                    ("SYP_OLD", "الليرة السورية القديمة"),
                    ("SYP_NEW", "الليرة السورية الجديدة"),
                ],
                default="USD",
                max_length=10,
                verbose_name="عملة المعاملة",
            ),
        ),
        migrations.AddField(
            model_name="supplierpayment",
            name="fx_rate_date",
            field=models.DateField(
                blank=True,
                null=True,
                verbose_name="تاريخ سعر الصرف",
            ),
        ),
        migrations.AddField(
            model_name="supplierpayment",
            name="usd_to_syp_old_snapshot",
            field=models.DecimalField(
                blank=True,
                decimal_places=6,
                max_digits=18,
                null=True,
                verbose_name="سعر صرف الدولار مقابل الليرة القديمة",
            ),
        ),
        migrations.AddField(
            model_name="supplierpayment",
            name="usd_to_syp_new_snapshot",
            field=models.DecimalField(
                blank=True,
                decimal_places=6,
                max_digits=18,
                null=True,
                verbose_name="سعر صرف الدولار مقابل الليرة الجديدة",
            ),
        ),
        migrations.AddField(
            model_name="supplierpayment",
            name="amount_usd",
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal("0.00"),
                max_digits=15,
                verbose_name="المبلغ (USD)",
            ),
        ),
    ]
