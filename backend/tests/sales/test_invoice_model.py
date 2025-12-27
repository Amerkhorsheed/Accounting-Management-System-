"""
Tests for Invoice model.
"""
import pytest
from decimal import Decimal
from datetime import date, timedelta
from apps.sales.models import Invoice, Customer
from apps.inventory.models import Warehouse, Category, Unit


@pytest.mark.django_db
class TestInvoiceModel:
    """Test suite for Invoice model."""
    
    @pytest.fixture(autouse=True)
    def setup_data(self, admin_user):
        """Setup test data."""
        self.customer = Customer.objects.create(name='Test Customer')
        self.category = Category.objects.create(name='Test Category')
        self.unit = Unit.objects.create(name='Piece', symbol='PC')
        self.warehouse = Warehouse.objects.create(
            name='Main Warehouse',
            code='WH001',
            manager=admin_user
        )
    
    def test_create_invoice(self, today):
        """Test creating an invoice."""
        invoice = Invoice.objects.create(
            customer=self.customer,
            warehouse=self.warehouse,
            invoice_date=today,
            invoice_type=Invoice.InvoiceType.CASH
        )
        assert invoice.customer == self.customer
        assert invoice.warehouse == self.warehouse
        assert invoice.invoice_date == today
    
    def test_invoice_auto_generate_number(self, today):
        """Test invoice number auto-generation."""
        invoice = Invoice.objects.create(
            customer=self.customer,
            warehouse=self.warehouse,
            invoice_date=today
        )
        assert invoice.invoice_number is not None
        assert invoice.invoice_number.startswith('INV')
    
    def test_invoice_string_representation(self, today):
        """Test invoice string representation."""
        invoice = Invoice.objects.create(
            invoice_number='INV001',
            customer=self.customer,
            warehouse=self.warehouse,
            invoice_date=today
        )
        assert str(invoice) == 'INV001 - Test Customer'
    
    def test_invoice_types(self, today):
        """Test all invoice types."""
        cash = Invoice.objects.create(
            customer=self.customer,
            warehouse=self.warehouse,
            invoice_date=today,
            invoice_type=Invoice.InvoiceType.CASH
        )
        assert cash.invoice_type == Invoice.InvoiceType.CASH
        
        credit = Invoice.objects.create(
            customer=self.customer,
            warehouse=self.warehouse,
            invoice_date=today,
            invoice_type=Invoice.InvoiceType.CREDIT
        )
        assert credit.invoice_type == Invoice.InvoiceType.CREDIT
        
        return_inv = Invoice.objects.create(
            customer=self.customer,
            warehouse=self.warehouse,
            invoice_date=today,
            invoice_type=Invoice.InvoiceType.RETURN
        )
        assert return_inv.invoice_type == Invoice.InvoiceType.RETURN
    
    def test_invoice_statuses(self, today):
        """Test all invoice statuses."""
        statuses = [
            Invoice.Status.DRAFT,
            Invoice.Status.CONFIRMED,
            Invoice.Status.PAID,
            Invoice.Status.PARTIAL,
            Invoice.Status.CANCELLED
        ]
        
        for status in statuses:
            invoice = Invoice.objects.create(
                customer=self.customer,
                warehouse=self.warehouse,
                invoice_date=today,
                status=status
            )
            assert invoice.status == status
    
    def test_invoice_remaining_amount(self, today):
        """Test remaining_amount property."""
        invoice = Invoice.objects.create(
            customer=self.customer,
            warehouse=self.warehouse,
            invoice_date=today,
            total_amount=Decimal('1000.00'),
            paid_amount=Decimal('300.00')
        )
        assert invoice.remaining_amount == Decimal('700.00')
    
    def test_invoice_amounts(self, today):
        """Test invoice amount fields."""
        invoice = Invoice.objects.create(
            customer=self.customer,
            warehouse=self.warehouse,
            invoice_date=today,
            subtotal=Decimal('1000.00'),
            discount_amount=Decimal('100.00'),
            tax_amount=Decimal('135.00'),
            total_amount=Decimal('1035.00')
        )
        assert invoice.subtotal == Decimal('1000.00')
        assert invoice.discount_amount == Decimal('100.00')
        assert invoice.tax_amount == Decimal('135.00')
        assert invoice.total_amount == Decimal('1035.00')
    
    def test_invoice_discount_percent(self, today):
        """Test invoice discount percent."""
        invoice = Invoice.objects.create(
            customer=self.customer,
            warehouse=self.warehouse,
            invoice_date=today,
            discount_percent=Decimal('10.00')
        )
        assert invoice.discount_percent == Decimal('10.00')
    
    def test_invoice_due_date(self, today, next_week):
        """Test invoice due date."""
        invoice = Invoice.objects.create(
            customer=self.customer,
            warehouse=self.warehouse,
            invoice_date=today,
            due_date=next_week,
            invoice_type=Invoice.InvoiceType.CREDIT
        )
        assert invoice.due_date == next_week
    
    def test_invoice_return_reference(self, today):
        """Test invoice return reference."""
        original = Invoice.objects.create(
            customer=self.customer,
            warehouse=self.warehouse,
            invoice_date=today
        )
        return_invoice = Invoice.objects.create(
            customer=self.customer,
            warehouse=self.warehouse,
            invoice_date=today,
            invoice_type=Invoice.InvoiceType.RETURN,
            return_for=original
        )
        assert return_invoice.return_for == original
        assert return_invoice in original.returns.all()
