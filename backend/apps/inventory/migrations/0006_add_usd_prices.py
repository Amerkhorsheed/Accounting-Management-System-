from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0005_alter_product_is_taxable_alter_product_tax_rate"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="cost_price_usd",
            field=models.DecimalField(
                blank=True,
                null=True,
                decimal_places=2,
                max_digits=15,
                verbose_name="سعر التكلفة (USD)",
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="sale_price_usd",
            field=models.DecimalField(
                blank=True,
                null=True,
                decimal_places=2,
                max_digits=15,
                verbose_name="سعر البيع (USD)",
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="wholesale_price_usd",
            field=models.DecimalField(
                blank=True,
                null=True,
                decimal_places=2,
                max_digits=15,
                verbose_name="سعر الجملة (USD)",
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="minimum_price_usd",
            field=models.DecimalField(
                blank=True,
                null=True,
                decimal_places=2,
                max_digits=15,
                verbose_name="أقل سعر بيع (USD)",
            ),
        ),
        migrations.AddField(
            model_name="productunit",
            name="sale_price_usd",
            field=models.DecimalField(
                blank=True,
                null=True,
                decimal_places=2,
                max_digits=15,
                verbose_name="سعر البيع (USD)",
            ),
        ),
        migrations.AddField(
            model_name="productunit",
            name="cost_price_usd",
            field=models.DecimalField(
                blank=True,
                null=True,
                decimal_places=2,
                max_digits=15,
                verbose_name="سعر التكلفة (USD)",
            ),
        ),
    ]
