"""
Tests for AddressModel and ContactModel.
"""
import pytest
from apps.sales.models import Customer  # Using Customer as it has both Address and Contact models


@pytest.mark.django_db
class TestAddressModel:
    """Test suite for AddressModel."""
    
    def test_address_fields(self):
        """Test all address fields."""
        customer = Customer.objects.create(
            name='Test Customer',
            address='123 Test Street',
            city='Riyadh',
            region='Central',
            postal_code='12345',
            country='Saudi Arabia'
        )
        assert customer.address == '123 Test Street'
        assert customer.city == 'Riyadh'
        assert customer.region == 'Central'
        assert customer.postal_code == '12345'
        assert customer.country == 'Saudi Arabia'
    
    def test_full_address_property(self):
        """Test full_address property."""
        customer = Customer.objects.create(
            name='Test Customer',
            address='123 Test Street',
            city='Riyadh',
            region='Central',
            postal_code='12345',
            country='Saudi Arabia'
        )
        expected = '123 Test Street, Riyadh, Central, 12345, Saudi Arabia'
        assert customer.full_address == expected
    
    def test_full_address_with_missing_fields(self):
        """Test full_address with some fields missing."""
        customer = Customer.objects.create(
            name='Test Customer',
            city='Riyadh',
            country='Saudi Arabia'
        )
        expected = 'Riyadh, Saudi Arabia'
        assert customer.full_address == expected
    
    def test_default_country(self):
        """Test default country value."""
        customer = Customer.objects.create(name='Test Customer')
        assert customer.country == 'المملكة العربية السعودية'


@pytest.mark.django_db
class TestContactModel:
    """Test suite for ContactModel."""
    
    def test_contact_fields(self):
        """Test all contact fields."""
        customer = Customer.objects.create(
            name='Test Customer',
            phone='0112345678',
            mobile='0501234567',
            email='test@example.com',
            fax='0112345679',
            website='https://example.com'
        )
        assert customer.phone == '0112345678'
        assert customer.mobile == '0501234567'
        assert customer.email == 'test@example.com'
        assert customer.fax == '0112345679'
        assert customer.website == 'https://example.com'
    
    def test_contact_fields_optional(self):
        """Test that contact fields are optional."""
        customer = Customer.objects.create(name='Test Customer')
        assert customer.phone is None or customer.phone == ''
        assert customer.mobile is None or customer.mobile == ''
        assert customer.email is None or customer.email == ''
        assert customer.fax is None or customer.fax == ''
        assert customer.website is None or customer.website == ''
