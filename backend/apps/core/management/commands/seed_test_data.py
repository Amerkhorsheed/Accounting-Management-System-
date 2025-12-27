"""
Management command to seed test data for development/testing
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from decimal import Decimal
from datetime import date, timedelta

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed test data for development and testing'

    def handle(self, *args, **options):
        self.stdout.write('Seeding test data...\n')
        
        # First run setup_initial_data
        from django.core.management import call_command
        call_command('setup_initial_data')
        
        # Import models
        from apps.inventory.models import Category, Unit, Warehouse, Product, Stock
        from apps.sales.models import Customer
        from apps.purchases.models import Supplier
        from apps.expenses.models import ExpenseCategory
        
        # Get or create admin user
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123',
                first_name='مدير',
                last_name='النظام'
            )
            self.stdout.write(self.style.SUCCESS('Created admin user: admin / admin123'))
        
        # Create Units
        self.stdout.write('\nCreating units...')
        units_data = [
            {'name': 'قطعة', 'symbol': 'قطعة', 'is_base': True},
            {'name': 'كيلوغرام', 'symbol': 'كغ', 'is_base': True},
            {'name': 'لتر', 'symbol': 'لتر', 'is_base': True},
            {'name': 'متر', 'symbol': 'م', 'is_base': True},
            {'name': 'علبة', 'symbol': 'علبة', 'is_base': False},
            {'name': 'كرتون', 'symbol': 'كرتون', 'is_base': False},
        ]
        units = {}
        for data in units_data:
            unit, created = Unit.objects.get_or_create(
                name=data['name'],
                defaults=data
            )
            units[data['name']] = unit
            if created:
                self.stdout.write(f'  Created unit: {unit.name}')
        
        # Create Categories
        self.stdout.write('\nCreating categories...')
        categories_data = [
            {'name': 'إلكترونيات', 'name_en': 'Electronics'},
            {'name': 'أجهزة منزلية', 'name_en': 'Home Appliances'},
            {'name': 'مواد غذائية', 'name_en': 'Food & Beverages'},
            {'name': 'ملابس', 'name_en': 'Clothing'},
            {'name': 'أدوات مكتبية', 'name_en': 'Office Supplies'},
        ]
        categories = {}
        for data in categories_data:
            cat, created = Category.objects.get_or_create(
                name=data['name'],
                defaults=data
            )
            categories[data['name']] = cat
            if created:
                self.stdout.write(f'  Created category: {cat.name}')
        
        # Create Warehouse
        self.stdout.write('\nCreating warehouse...')
        warehouse, created = Warehouse.objects.get_or_create(
            code='WH-001',
            defaults={
                'name': 'المستودع الرئيسي',
                'address': 'دمشق - سوريا',
                'is_default': True,
                'manager': admin_user,
            }
        )
        if created:
            self.stdout.write(f'  Created warehouse: {warehouse.name}')
        
        # Create Products
        self.stdout.write('\nCreating products...')
        products_data = [
            {
                'name': 'هاتف ذكي سامسونج',
                'name_en': 'Samsung Smartphone',
                'category': categories['إلكترونيات'],
                'unit': units['قطعة'],
                'cost_price': Decimal('500000'),
                'sale_price': Decimal('650000'),
                'minimum_stock': Decimal('5'),
            },
            {
                'name': 'لابتوب HP',
                'name_en': 'HP Laptop',
                'category': categories['إلكترونيات'],
                'unit': units['قطعة'],
                'cost_price': Decimal('1500000'),
                'sale_price': Decimal('1800000'),
                'minimum_stock': Decimal('3'),
            },
            {
                'name': 'ثلاجة LG',
                'name_en': 'LG Refrigerator',
                'category': categories['أجهزة منزلية'],
                'unit': units['قطعة'],
                'cost_price': Decimal('2000000'),
                'sale_price': Decimal('2500000'),
                'minimum_stock': Decimal('2'),
            },
            {
                'name': 'غسالة أوتوماتيك',
                'name_en': 'Automatic Washer',
                'category': categories['أجهزة منزلية'],
                'unit': units['قطعة'],
                'cost_price': Decimal('1200000'),
                'sale_price': Decimal('1500000'),
                'minimum_stock': Decimal('2'),
            },
            {
                'name': 'أرز بسمتي 5 كغ',
                'name_en': 'Basmati Rice 5kg',
                'category': categories['مواد غذائية'],
                'unit': units['كيلوغرام'],
                'cost_price': Decimal('50000'),
                'sale_price': Decimal('65000'),
                'minimum_stock': Decimal('20'),
            },
            {
                'name': 'زيت زيتون 1 لتر',
                'name_en': 'Olive Oil 1L',
                'category': categories['مواد غذائية'],
                'unit': units['لتر'],
                'cost_price': Decimal('80000'),
                'sale_price': Decimal('100000'),
                'minimum_stock': Decimal('15'),
            },
            {
                'name': 'قميص رجالي',
                'name_en': 'Men Shirt',
                'category': categories['ملابس'],
                'unit': units['قطعة'],
                'cost_price': Decimal('30000'),
                'sale_price': Decimal('45000'),
                'minimum_stock': Decimal('10'),
            },
            {
                'name': 'أقلام حبر (علبة 12)',
                'name_en': 'Ink Pens (Box of 12)',
                'category': categories['أدوات مكتبية'],
                'unit': units['علبة'],
                'cost_price': Decimal('5000'),
                'sale_price': Decimal('8000'),
                'minimum_stock': Decimal('20'),
            },
        ]
        
        products = []
        for data in products_data:
            product, created = Product.objects.get_or_create(
                name=data['name'],
                defaults={
                    **data,
                    'created_by': admin_user,
                }
            )
            products.append(product)
            if created:
                self.stdout.write(f'  Created product: {product.name}')
                # Create initial stock
                Stock.objects.get_or_create(
                    product=product,
                    warehouse=warehouse,
                    defaults={'quantity': Decimal('50')}
                )
        
        # Create Customers
        self.stdout.write('\nCreating customers...')
        customers_data = [
            {
                'name': 'أحمد محمد',
                'name_en': 'Ahmed Mohammed',
                'customer_type': 'individual',
                'phone': '0911234567',
                'mobile': '0991234567',
                'email': 'ahmed@example.com',
                'address': 'دمشق - المزة',
                'credit_limit': Decimal('5000000'),
            },
            {
                'name': 'شركة النور للتجارة',
                'name_en': 'Al-Nour Trading Co.',
                'customer_type': 'company',
                'phone': '0112345678',
                'mobile': '0992345678',
                'email': 'info@alnour.com',
                'address': 'حلب - الشهباء',
                'credit_limit': Decimal('20000000'),
                'tax_number': '123456789',
            },
            {
                'name': 'محمود علي',
                'name_en': 'Mahmoud Ali',
                'customer_type': 'individual',
                'phone': '0913456789',
                'mobile': '0993456789',
                'email': 'mahmoud@example.com',
                'address': 'حمص - الوعر',
                'credit_limit': Decimal('3000000'),
            },
            {
                'name': 'مؤسسة الأمل',
                'name_en': 'Al-Amal Foundation',
                'customer_type': 'company',
                'phone': '0114567890',
                'mobile': '0994567890',
                'email': 'contact@alamal.org',
                'address': 'اللاذقية',
                'credit_limit': Decimal('15000000'),
            },
        ]
        
        for data in customers_data:
            customer, created = Customer.objects.get_or_create(
                name=data['name'],
                defaults={
                    **data,
                    'created_by': admin_user,
                }
            )
            if created:
                self.stdout.write(f'  Created customer: {customer.name}')
        
        # Create Suppliers
        self.stdout.write('\nCreating suppliers...')
        suppliers_data = [
            {
                'name': 'شركة الإلكترونيات المتحدة',
                'name_en': 'United Electronics Co.',
                'phone': '0115678901',
                'mobile': '0995678901',
                'email': 'sales@ue.com',
                'address': 'دمشق - برزة',
                'payment_terms': 30,
                'credit_limit': Decimal('50000000'),
            },
            {
                'name': 'مصنع الأجهزة المنزلية',
                'name_en': 'Home Appliances Factory',
                'phone': '0116789012',
                'mobile': '0996789012',
                'email': 'orders@haf.com',
                'address': 'حلب - الصناعية',
                'payment_terms': 45,
                'credit_limit': Decimal('100000000'),
            },
            {
                'name': 'شركة المواد الغذائية',
                'name_en': 'Food Materials Co.',
                'phone': '0117890123',
                'mobile': '0997890123',
                'email': 'info@foodco.com',
                'address': 'حمص - الصناعية',
                'payment_terms': 15,
                'credit_limit': Decimal('30000000'),
            },
        ]
        
        for data in suppliers_data:
            supplier, created = Supplier.objects.get_or_create(
                name=data['name'],
                defaults={
                    **data,
                    'created_by': admin_user,
                }
            )
            if created:
                self.stdout.write(f'  Created supplier: {supplier.name}')
        
        # Create Expense Categories
        self.stdout.write('\nCreating expense categories...')
        expense_categories_data = [
            {'name': 'إيجارات', 'description': 'إيجار المكاتب والمستودعات'},
            {'name': 'رواتب', 'description': 'رواتب الموظفين'},
            {'name': 'مرافق', 'description': 'كهرباء، ماء، إنترنت'},
            {'name': 'صيانة', 'description': 'صيانة المعدات والمباني'},
            {'name': 'نقل', 'description': 'مصاريف النقل والشحن'},
            {'name': 'تسويق', 'description': 'إعلانات وتسويق'},
            {'name': 'متنوعة', 'description': 'مصاريف متنوعة أخرى'},
        ]
        
        for data in expense_categories_data:
            cat, created = ExpenseCategory.objects.get_or_create(
                name=data['name'],
                defaults=data
            )
            if created:
                self.stdout.write(f'  Created expense category: {cat.name}')
        
        # Summary
        self.stdout.write(self.style.SUCCESS('\n' + '='*50))
        self.stdout.write(self.style.SUCCESS('Test data seeding complete!'))
        self.stdout.write(self.style.SUCCESS('='*50))
        self.stdout.write(f'\nSummary:')
        self.stdout.write(f'  Units: {Unit.objects.count()}')
        self.stdout.write(f'  Categories: {Category.objects.count()}')
        self.stdout.write(f'  Warehouses: {Warehouse.objects.count()}')
        self.stdout.write(f'  Products: {Product.objects.count()}')
        self.stdout.write(f'  Customers: {Customer.objects.count()}')
        self.stdout.write(f'  Suppliers: {Supplier.objects.count()}')
        self.stdout.write(f'  Expense Categories: {ExpenseCategory.objects.count()}')
        
        self.stdout.write(self.style.SUCCESS('\nYou can now login with:'))
        self.stdout.write(self.style.SUCCESS('  Username: admin'))
        self.stdout.write(self.style.SUCCESS('  Password: admin123'))
