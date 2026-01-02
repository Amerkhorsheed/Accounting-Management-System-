from decimal import Decimal

from django.db import migrations, models


def disable_purchase_tax(apps, schema_editor):
    PurchaseOrder = apps.get_model("purchases", "PurchaseOrder")
    PurchaseOrderItem = apps.get_model("purchases", "PurchaseOrderItem")

    PurchaseOrderItem.objects.all().update(tax_rate=Decimal("0.00"))

    for po in PurchaseOrder.objects.all().iterator():
        items = PurchaseOrderItem.objects.filter(purchase_order_id=po.id)

        subtotal = Decimal("0.00")
        for it in items:
            line_subtotal = (it.quantity or Decimal("0.00")) * (it.unit_price or Decimal("0.00"))
            discount_amount = (line_subtotal * (it.discount_percent or Decimal("0.00"))) / Decimal("100")
            subtotal += line_subtotal - discount_amount

        po.subtotal = subtotal
        po.tax_amount = Decimal("0.00")
        po.total_amount = subtotal - (po.discount_amount or Decimal("0.00"))

        if po.transaction_currency == "USD":
            po.total_amount_usd = po.total_amount
            po.paid_amount_usd = po.paid_amount
        else:
            if po.usd_to_syp_old_snapshot and po.usd_to_syp_new_snapshot:
                from apps.core.utils import to_usd

                po.total_amount_usd = to_usd(
                    po.total_amount,
                    po.transaction_currency,
                    usd_to_syp_old=po.usd_to_syp_old_snapshot,
                    usd_to_syp_new=po.usd_to_syp_new_snapshot,
                )
                po.paid_amount_usd = to_usd(
                    po.paid_amount,
                    po.transaction_currency,
                    usd_to_syp_old=po.usd_to_syp_old_snapshot,
                    usd_to_syp_new=po.usd_to_syp_new_snapshot,
                )

        po.save(update_fields=["subtotal", "tax_amount", "total_amount", "total_amount_usd", "paid_amount_usd"])


class Migration(migrations.Migration):

    dependencies = [
        ("purchases", "0003_currency_fx_fields"),
    ]

    operations = [
        migrations.AlterField(
            model_name="purchaseorderitem",
            name="tax_rate",
            field=models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=5, verbose_name="نسبة الضريبة"),
        ),
        migrations.RunPython(disable_purchase_tax, migrations.RunPython.noop),
    ]
