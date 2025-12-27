# Data migration for default units
# Requirements: 7.1, 7.2

from django.db import migrations


def create_default_units(apps, schema_editor):
    """
    Create default units for tobacco products.
    Default units: قطعة (piece), علبة (pack), كروز (carton), كيلو (kilogram), كف (bulk portion), باكيت (packet)
    """
    Unit = apps.get_model('inventory', 'Unit')
    
    default_units = [
        {
            'name': 'قطعة',
            'name_en': 'piece',
            'symbol': 'قطعة',
        },
        {
            'name': 'علبة',
            'name_en': 'pack',
            'symbol': 'علبة',
        },
        {
            'name': 'كروز',
            'name_en': 'carton',
            'symbol': 'كروز',
        },
        {
            'name': 'كيلو',
            'name_en': 'kilogram',
            'symbol': 'كجم',
        },
        {
            'name': 'كف',
            'name_en': 'bulk portion',
            'symbol': 'كف',
        },
        {
            'name': 'باكيت',
            'name_en': 'packet',
            'symbol': 'باكيت',
        },
    ]
    
    for unit_data in default_units:
        # Only create if unit with same name doesn't exist
        if not Unit.objects.filter(name=unit_data['name'], is_deleted=False).exists():
            Unit.objects.create(**unit_data)


def reverse_default_units(apps, schema_editor):
    """
    Remove default units (reverse migration).
    Only removes units that are not in use by products.
    """
    Unit = apps.get_model('inventory', 'Unit')
    Product = apps.get_model('inventory', 'Product')
    ProductUnit = apps.get_model('inventory', 'ProductUnit')
    
    default_unit_names = ['قطعة', 'علبة', 'كروز', 'كيلو', 'كف', 'باكيت']
    
    for name in default_unit_names:
        try:
            unit = Unit.objects.get(name=name, is_deleted=False)
            # Only delete if not in use
            if not Product.objects.filter(unit=unit).exists() and \
               not ProductUnit.objects.filter(unit=unit).exists():
                unit.delete()
        except Unit.DoesNotExist:
            pass


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0002_units_management'),
    ]

    operations = [
        migrations.RunPython(create_default_units, reverse_default_units),
    ]
