"""
Tests for Payment model.
"""
import pytest
from decimal import Decimal
from apps.sales.models import Payment, Customer, Invoice
from apps.inventory.models import Warehouse


@pytest.mark.django_db
class TestPaymentModel:
    """Test suite for Payment model."""
    
    @pytest.fixture(autouse=True)
    def setup_data(self, admin_user, today):
        """Setup test data."""
        self.customer = Customer.objects.create(name='Test Customer')
        self.warehouse = Warehouse.objects.create(
            name='Main Warehouse',
            code='WH001',
            manager=admin_user
        )
        self.invoice = Invoice.objects.create(
            customer=self.customer,
            warehouse=self.warehouse,
            invoice_date=today,
            total_amount=Decimal('1000.00')
        )
        self.user = admin_user
        self.today = today
    
    def test_create_payment(self):
        """Test creating a payment."""
        payment = Payment.objects.create(
            customer=self.customer,
            invoice=self.invoice,
            payment_date=self.today,
            amount=Decimal('500.00'),
            received_by=self.user
        )
        assert payment.customer == self.customer
        assert payment.invoice == self.invoice
        assert payment.amount == Decimal('500.00')
    
    def test_payment_auto_generate_number(self):
        """Test payment number auto-generation."""
        payment = Payment.objects.create(
            customer=self.customer,
            payment_date=self.today,
            amount=Decimal('500.00')
        )
        assert payment.payment_number is not None
        assert payment.payment_number.startswith('REC')
    
    def test_payment_string_representation(self):
        """Test payment string representation."""
        payment = Payment.objects.create(
            payment_number='REC001',
            customer=self.customer,
            payment_date=self.today,
            amount=Decimal('500.00')
        )
        assert str(payment) == 'REC001 - Test Customer: 500.00'
    
    def test_payment_methods(self):
        """Test all payment methods."""
        methods = [
            Payment.PaymentMethod.CASH,
            Payment.PaymentMethod.CARD,
            Payment.PaymentMethod.BANK,
            Payment.PaymentMethod.CHECK,
            Payment.PaymentMethod.CREDIT
        ]
        
        for method in methods:
            payment = Payment.objects.create(
                customer=self.customer,
                payment_date=self.today,
                amount=Decimal('500.00'),
                payment_method=method
            )
            assert payment.payment_method == method
    
    def test_payment_without_invoice(self):
        """Test payment without specific invoice (advance payment)."""
        payment = Payment.objects.create(
            customer=self.customer,
            payment_date=self.today,
            amount=Decimal('500.00')
        )
        assert payment.invoice is None
    
    def test_payment_reference(self):
        """Test payment reference field."""
        payment = Payment.objects.create(
            customer=self.customer,
            payment_date=self.today,
            amount=Decimal('500.00'),
            payment_method=Payment.PaymentMethod.CHECK,
            reference='CHK123456'
        )
        assert payment.reference == 'CHK123456'
