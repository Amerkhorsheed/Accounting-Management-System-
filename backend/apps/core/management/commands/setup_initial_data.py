"""
Management command to setup initial data (currencies, tax rates, etc.)
"""
from django.core.management.base import BaseCommand
from apps.core.settings_models import Currency, TaxRate, SystemSettings


class Command(BaseCommand):
    help = 'Setup initial data for the accounting system'

    def handle(self, *args, **options):
        self.stdout.write('Setting up initial data...')
        
        # Create currencies
        syp, created = Currency.objects.get_or_create(
            code='SYP',
            defaults={
                'name': 'الليرة السورية',
                'name_en': 'Syrian Pound',
                'symbol': 'ل.س',
                'exchange_rate': 1.0,
                'is_primary': True,
                'decimal_places': 0,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('  Created currency: SYP - Syrian Pound'))
        
        usd, created = Currency.objects.get_or_create(
            code='USD',
            defaults={
                'name': 'الدولار الأمريكي',
                'name_en': 'US Dollar',
                'symbol': '$',
                'exchange_rate': 15000.0,
                'is_primary': False,
                'decimal_places': 2,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('  Created currency: USD - US Dollar'))
        
        # Create tax rate (disabled by default)
        tax, created = TaxRate.objects.get_or_create(
            code='VAT',
            defaults={
                'name': 'ضريبة القيمة المضافة',
                'rate': 0.00,
                'is_active': False,
                'is_default': True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('  Created tax rate: VAT (0% - disabled)'))
        
        # System settings
        settings = [
            ('company_name', 'شركتكم', 'Company Name'),
            ('company_name_en', 'Your Company', 'Company Name (English)'),
            ('company_address', '', 'Company Address'),
            ('company_phone', '', 'Company Phone'),
            ('company_tax_number', '', 'Tax Number'),
            ('show_dual_currency', 'true', 'Show dual currency'),
        ]
        
        for key, value, description in settings:
            obj, created = SystemSettings.objects.get_or_create(
                key=key,
                defaults={'value': value, 'description': description}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  Created setting: {key}'))
        
        self.stdout.write(self.style.SUCCESS('\nInitial data setup complete!'))
        self.stdout.write(f'Currencies: {Currency.objects.count()}')
        self.stdout.write(f'Tax Rates: {TaxRate.objects.count()}')
        self.stdout.write(f'Settings: {SystemSettings.objects.count()}')
