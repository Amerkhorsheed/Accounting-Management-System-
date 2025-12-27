"""
Tests for Core Settings Models (SystemSettings, Currency, TaxRate).
"""
import pytest
from decimal import Decimal
from apps.core.settings_models import SystemSettings, Currency, TaxRate


@pytest.mark.django_db
class TestSystemSettingsModel:
    """Test suite for SystemSettings model."""
    
    def test_create_system_setting(self):
        """Test creating a system setting."""
        setting = SystemSettings.objects.create(
            key='company_name',
            value='Test Company',
            description='Company name for invoices'
        )
        assert setting.key == 'company_name'
        assert setting.value == 'Test Company'
    
    def test_system_setting_string_representation(self):
        """Test system setting string representation."""
        setting = SystemSettings.objects.create(
            key='tax_enabled',
            value='true'
        )
        assert str(setting) == 'tax_enabled: true'
    
    def test_get_setting_exists(self):
        """Test get_setting class method when setting exists."""
        SystemSettings.objects.create(
            key='company_name',
            value='Test Company'
        )
        value = SystemSettings.get_setting('company_name')
        assert value == 'Test Company'
    
    def test_get_setting_not_exists(self):
        """Test get_setting class method when setting doesn't exist."""
        value = SystemSettings.get_setting('nonexistent_key', default='default_value')
        assert value == 'default_value'
    
    def test_set_setting_create(self):
        """Test set_setting creates new setting."""
        setting = SystemSettings.set_setting(
            'new_key',
            'new_value',
            'New setting description'
        )
        assert setting.key == 'new_key'
        assert setting.value == 'new_value'
        assert setting.description == 'New setting description'
    
    def test_set_setting_update(self):
        """Test set_setting updates existing setting."""
        SystemSettings.objects.create(key='test_key', value='old_value')
        setting = SystemSettings.set_setting('test_key', 'new_value')
        
        assert setting.value == 'new_value'
        assert SystemSettings.objects.filter(key='test_key').count() == 1


@pytest.mark.django_db
class TestCurrencyModel:
    """Test suite for Currency model."""
    
    def test_create_currency(self):
        """Test creating a currency."""
        currency = Currency.objects.create(
            code='USD',
            name='US Dollar',
            name_en='US Dollar',
            symbol='$',
            exchange_rate=Decimal('3.75')
        )
        assert currency.code == 'USD'
        assert currency.symbol == '$'
        assert currency.exchange_rate == Decimal('3.75')
    
    def test_currency_string_representation(self):
        """Test currency string representation."""
        currency = Currency.objects.create(
            code='SAR',
            name='Saudi Riyal',
            symbol='ر.س'
        )
        assert str(currency) == 'SAR - Saudi Riyal'
    
    def test_currency_primary_flag(self):
        """Test primary currency flag."""
        currency = Currency.objects.create(
            code='SAR',
            name='Saudi Riyal',
            symbol='ر.س',
            is_primary=True
        )
        assert currency.is_primary is True
        assert currency.exchange_rate == Decimal('1.0000')
    
    def test_currency_only_one_primary(self):
        """Test that only one currency can be primary."""
        currency1 = Currency.objects.create(
            code='SAR',
            name='Saudi Riyal',
            symbol='ر.س',
            is_primary=True
        )
        currency2 = Currency.objects.create(
            code='USD',
            name='US Dollar',
            symbol='$',
            is_primary=True
        )
        
        currency1.refresh_from_db()
        assert currency1.is_primary is False
        assert currency2.is_primary is True
    
    def test_get_primary_currency(self):
        """Test get_primary class method."""
        Currency.objects.create(
            code='SAR',
            name='Saudi Riyal',
            symbol='ر.س',
            is_primary=True,
            is_active=True
        )
        primary = Currency.get_primary()
        assert primary.code == 'SAR'
    
    def test_currency_convert_same_currency(self):
        """Test converting between same currency."""
        sar = Currency.objects.create(
            code='SAR',
            name='Saudi Riyal',
            symbol='ر.س',
            exchange_rate=Decimal('1.0000')
        )
        result = Currency.convert(Decimal('100.00'), sar, sar)
        assert result == Decimal('100.00')
    
    def test_currency_convert_different_currencies(self):
        """Test converting between different currencies."""
        sar = Currency.objects.create(
            code='SAR',
            name='Saudi Riyal',
            symbol='ر.س',
            exchange_rate=Decimal('1.0000'),
            is_primary=True
        )
        usd = Currency.objects.create(
            code='USD',
            name='US Dollar',
            symbol='$',
            exchange_rate=Decimal('3.75')
        )
        # 100 SAR to USD = 100 * 1.0 / 3.75 = 26.67
        result = Currency.convert(Decimal('100.00'), sar, usd)
        assert result == Decimal('26.67')


@pytest.mark.django_db
class TestTaxRateModel:
    """Test suite for TaxRate model."""
    
    def test_create_tax_rate(self):
        """Test creating a tax rate."""
        tax = TaxRate.objects.create(
            name='VAT',
            code='VAT15',
            rate=Decimal('15.00')
        )
        assert tax.name == 'VAT'
        assert tax.code == 'VAT15'
        assert tax.rate == Decimal('15.00')
    
    def test_tax_rate_string_representation(self):
        """Test tax rate string representation."""
        tax = TaxRate.objects.create(
            name='VAT',
            code='VAT15',
            rate=Decimal('15.00')
        )
        assert str(tax) == 'VAT (15.00%)'
    
    def test_tax_rate_default_flag(self):
        """Test default tax rate flag."""
        tax = TaxRate.objects.create(
            name='VAT',
            code='VAT15',
            rate=Decimal('15.00'),
            is_default=True
        )
        assert tax.is_default is True
    
    def test_tax_rate_only_one_default(self):
        """Test that only one tax rate can be default."""
        tax1 = TaxRate.objects.create(
            name='VAT',
            code='VAT15',
            rate=Decimal('15.00'),
            is_default=True
        )
        tax2 = TaxRate.objects.create(
            name='Sales Tax',
            code='ST10',
            rate=Decimal('10.00'),
            is_default=True
        )
        
        tax1.refresh_from_db()
        assert tax1.is_default is False
        assert tax2.is_default is True
    
    def test_get_default_tax_rate(self):
        """Test get_default class method."""
        TaxRate.objects.create(
            name='VAT',
            code='VAT15',
            rate=Decimal('15.00'),
            is_default=True,
            is_active=True
        )
        default_rate = TaxRate.get_default()
        assert default_rate == Decimal('15.00')
    
    def test_get_default_no_tax(self):
        """Test get_default when no tax rate exists."""
        default_rate = TaxRate.get_default()
        assert default_rate == Decimal('0.00')
    
    def test_is_tax_enabled(self):
        """Test is_tax_enabled class method."""
        TaxRate.objects.create(
            name='VAT',
            code='VAT15',
            rate=Decimal('15.00'),
            is_active=True
        )
        assert TaxRate.is_tax_enabled() is True
    
    def test_is_tax_enabled_no_active_tax(self):
        """Test is_tax_enabled when no active tax."""
        assert TaxRate.is_tax_enabled() is False
