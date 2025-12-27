"""
Tests for SalesReturn and SalesReturnItem models.
"""
import pytest
from decimal import Decimal
from apps.sales.models import SalesReturn, SalesReturnItem, Invoice, InvoiceItem, Customer
from apps.inventory.models import Product, Warehouse, Category, Unit


@pytest.mark.django_db
class TestSalesReturnModel:
    """Test suite for SalesReturn model."""
    
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
            sale_price=Decimal('100.00')
        )
        self.invoice = Invoice.objects.create(
            customer=self.customer,
            warehouse=self.warehouse,
            invoice_date=today,
            total_amount=Decimal('1000.00')
        )
        self.today = today
    
    def test_create_sales_return(self):
        """Test creating a sales return."""
        sales_return = SalesReturn.objects.create(
            original_invoice=self.invoice,
            return_date=self.today,
            total_amount=Decimal('200.00'),
            reason='Defective product'
        )
        assert sales_return.original_invoice == self.invoice
        assert sales_return.return_date == self.today
        assert sales_return.total_amount == Decimal('200.00')
        assert sales_return.reason == 'Defective product'
    
    def test_sales_return_auto_generate_number(self):
        """Test sales return number auto-generation."""
        sales_return = SalesReturn.objects.create(
            original_invoice=self.invoice,
            return_date=self.today,
            total_amount=Decimal('200.00'),
            reason='Defective product'
        )
        assert sales_return.return_number is not None
        assert sales_return.return_number.startswith('RET')
    
    def test_sales_return_string_representation(self):
        """Test sales return string representation."""
        sales_return = SalesReturn.objects.create(
            return_number='RET001',
            original_invoice=self.invoice,
            return_date=self.today,
            total_amount=Decimal('200.00'),
            reason='Defective product'
        )
        assert 'RET001' in str(sales_return)
        assert self.invoice.invoice_number in str(sales_return)


@pytest.mark.django_db
class TestSalesReturnItemModel:
    """Test suite for SalesReturnItem model."""
    
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
            sale_price=Decimal('100.00')
        )
        self.invoice = Invoice.objects.create(
            customer=self.customer,
            warehouse=self.warehouse,
            invoice_date=today
        )
        self.invoice_item = InvoiceItem.objects.create(
            invoice=self.invoice,
            product=self.product,
            quantity=Decimal('10.00'),
            unit_price=Decimal('100.00')
        )
        self.sales_return = SalesReturn.objects.create(
            original_invoice=self.invoice,
            return_date=today,
            total_amount=Decimal('200.00'),
            reason='Defective product'
        )
    
    def test_create_sales_return_item(self):
        """Test creating a sales return item."""
        return_item = SalesReturnItem.objects.create(
            sales_return=self.sales_return,
            invoice_item=self.invoice_item,
            product=self.product,
            quantity=Decimal('2.00'),
            unit_price=Decimal('100.00'),
            reason='Damaged'
        )
        assert return_item.sales_return == self.sales_return
        assert return_item.invoice_item == self.invoice_item
        assert return_item.product == self.product
        assert return_item.quantity == Decimal('2.00')
        assert return_item.unit_price == Decimal('100.00')
    
    def test_sales_return_item_string_representation(self):
        """Test sales return item string representation."""
        return_item = SalesReturnItem.objects.create(
            sales_return=self.sales_return,
            invoice_item=self.invoice_item,
            product=self.product,
            quantity=Decimal('2.00'),
            unit_price=Decimal('100.00')
        )
        assert 'Test Product' in str(return_item)
        assert '2.00' in str(return_item)
    
    def test_sales_return_item_total(self):
        """Test sales return item total property."""
        return_item = SalesReturnItem.objects.create(
            sales_return=self.sales_return,
            invoice_item=self.invoice_item,
            product=self.product,
            quantity=Decimal('2.00'),
            unit_price=Decimal('100.00')
        )
        assert return_item.total == Decimal('200.00')
