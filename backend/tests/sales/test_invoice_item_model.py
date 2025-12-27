"""
Tests for InvoiceItem model.
"""
import pytest
from decimal import Decimal
from apps.sales.models import Invoice, InvoiceItem, Customer
from apps.inventory.models import Product, Warehouse, Category, Unit


@pytest.mark.django_db
class TestInvoiceItemModel:
    """Test suite for InvoiceItem model."""
    
    @pytest.fixture(autouse=True)
    def setup_data(self, admin_user, today):
        """Setup test data."""
        self.customer = Customer.objects.create(name='Test Customer')
        self.category = Category.objects.create(name='Test Category')
        self.unit = Unit.objects.create(name='Piece', symbol='PC')
        self.warehouse = Warehouse.objects.create(
            name='Main Warehouse',
            code='WH001',
            manager=admin_user
        )
        self.product = Product.objects.create(
            name='Test Product',
            category=self.category,
            unit=self.unit,
            sale_price=Decimal('100.00'),
            cost_price=Decimal('60.00')
        )
        self.invoice = Invoice.objects.create(
            customer=self.customer,
            warehouse=self.warehouse,
            invoice_date=today
        )
    
    def test_create_invoice_item(self):
        """Test creating an invoice item."""
        item = InvoiceItem.objects.create(
            invoice=self.invoice,
            product=self.product,
            quantity=Decimal('5.00'),
            unit_price=Decimal('100.00')
        )
        assert item.invoice == self.invoice
        assert item.product == self.product
        assert item.quantity == Decimal('5.00')
        assert item.unit_price == Decimal('100.00')
    
    def test_invoice_item_string_representation(self):
        """Test invoice item string representation."""
        item = InvoiceItem.objects.create(
            invoice=self.invoice,
            product=self.product,
            quantity=Decimal('5.00'),
            unit_price=Decimal('100.00')
        )
        assert str(item) == 'Test Product x 5.00'
    
    def test_invoice_item_subtotal(self):
        """Test subtotal property."""
        item = InvoiceItem.objects.create(
            invoice=self.invoice,
            product=self.product,
            quantity=Decimal('5.00'),
            unit_price=Decimal('100.00')
        )
        assert item.subtotal == Decimal('500.00')
    
    def test_invoice_item_discount_amount(self):
        """Test discount_amount property."""
        item = InvoiceItem.objects.create(
            invoice=self.invoice,
            product=self.product,
            quantity=Decimal('5.00'),
            unit_price=Decimal('100.00'),
            discount_percent=Decimal('10.00')
        )
        # Subtotal = 500, Discount = 500 * 0.10 = 50
        assert item.discount_amount == Decimal('50.00')
    
    def test_invoice_item_taxable_amount(self):
        """Test taxable_amount property."""
        item = InvoiceItem.objects.create(
            invoice=self.invoice,
            product=self.product,
            quantity=Decimal('5.00'),
            unit_price=Decimal('100.00'),
            discount_percent=Decimal('10.00')
        )
        # Taxable = Subtotal - Discount = 500 - 50 = 450
        assert item.taxable_amount == Decimal('450.00')
    
    def test_invoice_item_tax_amount(self):
        """Test tax_amount property."""
        item = InvoiceItem.objects.create(
            invoice=self.invoice,
            product=self.product,
            quantity=Decimal('5.00'),
            unit_price=Decimal('100.00'),
            discount_percent=Decimal('10.00'),
            tax_rate=Decimal('15.00')
        )
        # Tax = Taxable * 0.15 = 450 * 0.15 = 67.50
        assert item.tax_amount == Decimal('67.50')
    
    def test_invoice_item_total(self):
        """Test total property."""
        item = InvoiceItem.objects.create(
            invoice=self.invoice,
            product=self.product,
            quantity=Decimal('5.00'),
            unit_price=Decimal('100.00'),
            discount_percent=Decimal('10.00'),
            tax_rate=Decimal('15.00')
        )
        # Total = Taxable + Tax = 450 + 67.50 = 517.50
        assert item.total == Decimal('517.50')
    
    def test_invoice_item_profit(self):
        """Test profit property."""
        item = InvoiceItem.objects.create(
            invoice=self.invoice,
            product=self.product,
            quantity=Decimal('5.00'),
            unit_price=Decimal('100.00'),
            cost_price=Decimal('60.00')
        )
        # Profit = (100 - 60) * 5 = 200
        assert item.profit == Decimal('200.00')
    
    def test_invoice_item_with_zero_values(self):
        """Test invoice item with zero values."""
        item = InvoiceItem.objects.create(
            invoice=self.invoice,
            product=self.product,
            quantity=Decimal('0.00'),
            unit_price=Decimal('0.00'),
            cost_price=Decimal('0.00')
        )
        assert item.subtotal == Decimal('0.00')
        assert item.profit == Decimal('0.00')
