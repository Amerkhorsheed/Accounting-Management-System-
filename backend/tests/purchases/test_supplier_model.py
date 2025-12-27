"""
Tests for Supplier model.
"""
import pytest
from decimal import Decimal
from apps.purchases.models import Supplier


@pytest.mark.django_db
class TestSupplierModel:
    """Test suite for Supplier model."""
    
    def test_create_supplier(self):
        """Test creating a supplier."""
        supplier = Supplier.objects.create(
            name='Test Supplier',
            name_en='Test Supplier EN'
        )
        assert supplier.name == 'Test Supplier'
        assert supplier.name_en == 'Test Supplier EN'
    
    def test_supplier_auto_generate_code(self):
        """Test supplier code auto-generation."""
        supplier = Supplier.objects.create(name='Test Supplier')
        assert supplier.code is not None
        assert supplier.code.startswith('SUP')
    
    def test_supplier_string_representation(self):
        """Test supplier string representation."""
        supplier = Supplier.objects.create(
            name='Test Supplier',
            code='SUP001'
        )
        assert str(supplier) == 'SUP001 - Test Supplier'
    
    def test_supplier_payment_terms(self):
        """Test supplier payment terms."""
        supplier = Supplier.objects.create(
            name='Test Supplier',
            payment_terms=30
        )
        assert supplier.payment_terms == 30
    
    def test_supplier_payment_terms_default(self):
        """Test supplier payment terms default value."""
        supplier = Supplier.objects.create(name='Test Supplier')
        assert supplier.payment_terms == 30
    
    def test_supplier_credit_limit(self):
        """Test supplier credit limit."""
        supplier = Supplier.objects.create(
            name='Test Supplier',
            credit_limit=Decimal('50000.00')
        )
        assert supplier.credit_limit == Decimal('50000.00')
    
    def test_supplier_balance_tracking(self):
        """Test supplier balance tracking."""
        supplier = Supplier.objects.create(
            name='Test Supplier',
            opening_balance=Decimal('5000.00'),
            current_balance=Decimal('7500.00')
        )
        assert supplier.opening_balance == Decimal('5000.00')
        assert supplier.current_balance == Decimal('7500.00')
    
    def test_supplier_contact_info(self):
        """Test supplier contact information."""
        supplier = Supplier.objects.create(
            name='Test Supplier',
            phone='1234567890',
            mobile='0987654321',
            email='supplier@example.com'
        )
        assert supplier.phone == '1234567890'
        assert supplier.mobile == '0987654321'
        assert supplier.email == 'supplier@example.com'
    
    def test_supplier_address_info(self):
        """Test supplier address information."""
        supplier = Supplier.objects.create(
            name='Test Supplier',
            address='456 Supplier St',
            city='Jeddah',
            region='Western'
        )
        assert supplier.address == '456 Supplier St'
        assert supplier.city == 'Jeddah'
        assert supplier.region == 'Western'
    
    def test_supplier_tax_and_commercial_info(self):
        """Test supplier tax and commercial information."""
        supplier = Supplier.objects.create(
            name='Test Supplier',
            tax_number='987654321',
            commercial_register='CR987654'
        )
        assert supplier.tax_number == '987654321'
        assert supplier.commercial_register == 'CR987654'
    
    def test_supplier_contact_person(self):
        """Test supplier contact person."""
        supplier = Supplier.objects.create(
            name='Test Supplier',
            contact_person='John Doe'
        )
        assert supplier.contact_person == 'John Doe'
