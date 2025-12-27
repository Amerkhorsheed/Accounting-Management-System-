# Data migration to convert existing product units to ProductUnit model
# Requirements: 7.4

from decimal import Decimal
from django.db import migrations


def convert_existing_product_units(apps, schema_editor):
    """
    For each existing product, create a ProductUnit with the current unit as base.
    This preserves existing unit associations while enabling the new multi-unit system.
    """
    Product = apps.get_model('inventory', 'Product')
    ProductUnit = apps.get_model('inventory', 'ProductUnit')
    
    for product in Product.objects.filter(is_deleted=False):
        # Check if product already has a ProductUnit entry for its unit
        if not ProductUnit.objects.filter(
            product=product,
            unit=product.unit,
            is_deleted=False
        ).exists():
            # Create ProductUnit with the product's current unit as base unit
            ProductUnit.objects.create(
                product=product,
                unit=product.unit,
                conversion_factor=Decimal('1.0000'),
                is_base_unit=True,
                sale_price=product.sale_price,
                cost_price=product.cost_price,
                barcode=product.barcode,
            )


def reverse_convert_existing_product_units(apps, schema_editor):
    """
    Reverse migration - remove auto-created ProductUnit entries.
    Only removes ProductUnits that were created as base units with conversion_factor=1.
    """
    ProductUnit = apps.get_model('inventory', 'ProductUnit')
    
    # Delete ProductUnits that are base units with conversion_factor=1
    # These are the ones created by the forward migration
    ProductUnit.objects.filter(
        is_base_unit=True,
        conversion_factor=Decimal('1.0000'),
        is_deleted=False
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0003_default_units'),
    ]

    operations = [
        migrations.RunPython(
            convert_existing_product_units,
            reverse_convert_existing_product_units
        ),
    ]
