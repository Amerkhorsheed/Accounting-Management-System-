"""
Tests for Customer model.
"""
import pytest
from decimal import Decimal
from apps.sales.models import Customer
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestCustomerModel:
    """Test suite for Customer model."""
    
    def test_create_customer(self):
        """Test creating a customer."""
        customer = Customer.objects.create(
            name='Test Customer',
            customer_type=Customer.CustomerType.INDIVIDUAL
        )
        assert customer.name == 'Test Customer'
        assert customer.customer_type == Customer.CustomerType.INDIVIDUAL
    
    def test_customer_auto_generate_code(self):
        """Test customer code auto-generation."""
        customer = Customer.objects.create(name='Test Customer')
        assert customer.code is not None
        assert customer.code.startswith('CUS')
    
    def test_customer_string_representation(self):
        """Test customer string representation."""
        customer = Customer.objects.create(
            name='Test Customer',
            code='CUS001'
        )
        assert str(customer) == 'CUS001 - Test Customer'
    
    def test_customer_types(self):
        """Test all customer types."""
        individual = Customer.objects.create(
            name='Individual',
            customer_type=Customer.CustomerType.INDIVIDUAL
        )
        assert individual.customer_type == Customer.CustomerType.INDIVIDUAL
        
        company = Customer.objects.create(
            name='Company',
            customer_type=Customer.CustomerType.COMPANY
        )
        assert company.customer_type == Customer.CustomerType.COMPANY
        
        government = Customer.objects.create(
            name='Government',
            customer_type=Customer.CustomerType.GOVERNMENT
        )
        assert government.customer_type == Customer.CustomerType.GOVERNMENT
    
    def test_customer_available_credit(self):
        """Test available_credit property."""
        customer = Customer.objects.create(
            name='Test Customer',
            credit_limit=Decimal('10000.00'),
            current_balance=Decimal('3000.00')
        )
        assert customer.available_credit == Decimal('7000.00')
    
    def test_customer_credit_warning_threshold(self):
        """Test credit_warning_threshold property."""
        customer = Customer.objects.create(
            name='Test Customer',
            credit_limit=Decimal('10000.00'),
            current_balance=Decimal('8000.00')
        )
        assert customer.credit_warning_threshold is True
        
        customer.current_balance = Decimal('7000.00')
        assert customer.credit_warning_threshold is False
    
    def test_customer_is_over_credit_limit(self):
        """Test is_over_credit_limit property."""
        customer = Customer.objects.create(
            name='Test Customer',
            credit_limit=Decimal('10000.00'),
            current_balance=Decimal('11000.00')
        )
        assert customer.is_over_credit_limit is True
        
        customer.current_balance = Decimal('9000.00')
        assert customer.is_over_credit_limit is False
    
    def test_customer_no_credit_limit(self):
        """Test customer with no credit limit."""
        customer = Customer.objects.create(
            name='Test Customer',
            credit_limit=Decimal('0.00'),
            current_balance=Decimal('5000.00')
        )
        assert customer.credit_warning_threshold is False
        assert customer.is_over_credit_limit is False
    
    def test_customer_payment_terms(self):
        """Test customer payment terms."""
        customer = Customer.objects.create(
            name='Test Customer',
            payment_terms=30
        )
        assert customer.payment_terms == 30
    
    def test_customer_discount_percent(self):
        """Test customer discount percent."""
        customer = Customer.objects.create(
            name='Test Customer',
            discount_percent=Decimal('5.00')
        )
        assert customer.discount_percent == Decimal('5.00')
    
    def test_customer_balance_tracking(self):
        """Test customer balance tracking."""
        customer = Customer.objects.create(
            name='Test Customer',
            opening_balance=Decimal('1000.00'),
            current_balance=Decimal('1500.00')
        )
        assert customer.opening_balance == Decimal('1000.00')
        assert customer.current_balance == Decimal('1500.00')
    
    def test_customer_contact_info(self):
        """Test customer contact information."""
        customer = Customer.objects.create(
            name='Test Customer',
            phone='1234567890',
            mobile='0987654321',
            email='test@example.com'
        )
        assert customer.phone == '1234567890'
        assert customer.mobile == '0987654321'
        assert customer.email == 'test@example.com'
    
    def test_customer_address_info(self):
        """Test customer address information."""
        customer = Customer.objects.create(
            name='Test Customer',
            address='123 Test St',
            city='Riyadh',
            region='Central'
        )
        assert customer.address == '123 Test St'
        assert customer.city == 'Riyadh'
        assert customer.region == 'Central'
    
    def test_customer_tax_and_commercial_info(self):
        """Test customer tax and commercial information."""
        customer = Customer.objects.create(
            name='Test Company',
            customer_type=Customer.CustomerType.COMPANY,
            tax_number='123456789',
            commercial_register='CR123456'
        )
        assert customer.tax_number == '123456789'
        assert customer.commercial_register == 'CR123456'
    
    def test_customer_salesperson_assignment(self, salesperson_user):
        """Test customer salesperson assignment."""
        customer = Customer.objects.create(
            name='Test Customer',
            salesperson=salesperson_user
        )
        assert customer.salesperson == salesperson_user
