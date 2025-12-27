"""
Tests for PaymentAllocation model.
"""
import pytest
from decimal import Decimal
from django.db import IntegrityError
from apps.sales.models import PaymentAllocation, Payment, Invoice, Customer
from apps.inventory.models import Warehouse


@pytest.mark.django_db
class TestPaymentAllocationModel:
    """Test suite for PaymentAllocation model."""
    
    @pytest.fixture(autouse=True)
    def setup_data(self, admin_user, today):
        """Setup test data."""
        self.customer = Customer.objects.create(name='Test Customer')
        self.warehouse = Warehouse.objects.create(
            name='Main Warehouse',
            code='WH001',
            manager=admin_user
        )
        self.invoice1 = Invoice.objects.create(
            customer=self.customer,
            warehouse=self.warehouse,
            invoice_date=today,
            total_amount=Decimal('1000.00')
        )
        self.invoice2 = Invoice.objects.create(
            customer=self.customer,
            warehouse=self.warehouse,
            invoice_date=today,
            total_amount=Decimal('500.00')
        )
        self.payment = Payment.objects.create(
            customer=self.customer,
            payment_date=today,
            amount=Decimal('800.00')
        )
    
    def test_create_payment_allocation(self):
        """Test creating a payment allocation."""
        allocation = PaymentAllocation.objects.create(
            payment=self.payment,
            invoice=self.invoice1,
            amount=Decimal('500.00')
        )
        assert allocation.payment == self.payment
        assert allocation.invoice == self.invoice1
        assert allocation.amount == Decimal('500.00')
    
    def test_payment_allocation_string_representation(self):
        """Test payment allocation string representation."""
        allocation = PaymentAllocation.objects.create(
            payment=self.payment,
            invoice=self.invoice1,
            amount=Decimal('500.00')
        )
        expected = f"{self.payment.payment_number} -> {self.invoice1.invoice_number}: 500.00"
        assert str(allocation) == expected
    
    def test_payment_allocation_multiple_invoices(self):
        """Test allocating one payment to multiple invoices."""
        allocation1 = PaymentAllocation.objects.create(
            payment=self.payment,
            invoice=self.invoice1,
            amount=Decimal('500.00')
        )
        allocation2 = PaymentAllocation.objects.create(
            payment=self.payment,
            invoice=self.invoice2,
            amount=Decimal('300.00')
        )
        
        allocations = PaymentAllocation.objects.filter(payment=self.payment)
        assert allocations.count() == 2
        assert sum(a.amount for a in allocations) == Decimal('800.00')
    
    def test_payment_allocation_unique_constraint(self):
        """Test unique constraint on payment and invoice."""
        PaymentAllocation.objects.create(
            payment=self.payment,
            invoice=self.invoice1,
            amount=Decimal('500.00')
        )
        
        with pytest.raises(IntegrityError):
            PaymentAllocation.objects.create(
                payment=self.payment,
                invoice=self.invoice1,
                amount=Decimal('300.00')
            )
