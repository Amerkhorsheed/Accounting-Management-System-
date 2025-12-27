"""
Tests for CreditLimitOverride model.
"""
import pytest
from decimal import Decimal
from apps.sales.models import CreditLimitOverride, Customer, Invoice
from apps.inventory.models import Warehouse


@pytest.mark.django_db
class TestCreditLimitOverrideModel:
    """Test suite for CreditLimitOverride model."""
    
    @pytest.fixture(autouse=True)
    def setup_data(self, admin_user, today):
        """Setup test data."""
        self.customer = Customer.objects.create(
            name='Test Customer',
            credit_limit=Decimal('10000.00')
        )
        self.warehouse = Warehouse.objects.create(
            name='Main Warehouse',
            code='WH001',
            manager=admin_user
        )
        self.invoice = Invoice.objects.create(
            customer=self.customer,
            warehouse=self.warehouse,
            invoice_date=today,
            total_amount=Decimal('12000.00')
        )
        self.user = admin_user
    
    def test_create_credit_limit_override(self):
        """Test creating a credit limit override."""
        override = CreditLimitOverride.objects.create(
            customer=self.customer,
            invoice=self.invoice,
            override_amount=Decimal('2000.00'),
            reason='Trusted customer with good payment history',
            approved_by=self.user
        )
        assert override.customer == self.customer
        assert override.invoice == self.invoice
        assert override.override_amount == Decimal('2000.00')
        assert override.approved_by == self.user
    
    def test_credit_limit_override_string_representation(self):
        """Test credit limit override string representation."""
        override = CreditLimitOverride.objects.create(
            customer=self.customer,
            invoice=self.invoice,
            override_amount=Decimal('2000.00'),
            reason='Special approval',
            approved_by=self.user
        )
        assert 'Test Customer' in str(override)
        assert '2000.00' in str(override)
    
    def test_credit_limit_override_without_invoice(self):
        """Test credit limit override without specific invoice."""
        override = CreditLimitOverride.objects.create(
            customer=self.customer,
            override_amount=Decimal('5000.00'),
            reason='Credit limit increase',
            approved_by=self.user
        )
        assert override.invoice is None
        assert override.override_amount == Decimal('5000.00')
    
    def test_credit_limit_override_ordering(self):
        """Test credit limit override ordering (newest first)."""
        import time
        override1 = CreditLimitOverride.objects.create(
            customer=self.customer,
            override_amount=Decimal('1000.00'),
            reason='First override',
            approved_by=self.user
        )
        time.sleep(0.01)  # Ensure different timestamps
        override2 = CreditLimitOverride.objects.create(
            customer=self.customer,
            override_amount=Decimal('2000.00'),
            reason='Second override',
            approved_by=self.user
        )
        
        overrides = list(CreditLimitOverride.objects.all())
        assert overrides[0] == override2
        assert overrides[1] == override1
