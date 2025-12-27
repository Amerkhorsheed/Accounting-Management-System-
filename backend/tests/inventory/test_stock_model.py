"""
Tests for Stock model.
"""
import pytest
from decimal import Decimal
from apps.inventory.models import Stock, Product, Warehouse, Category, Unit


@pytest.mark.django_db
class TestStockModel:
    """Test suite for Stock model."""
    
    @pytest.fixture(autouse=True)
    def setup_data(self, admin_user):
        """Setup test data."""
        self.category = Category.objects.create(name='Test Category')
        self.unit = Unit.objects.create(name='Piece', symbol='PC')
        self.product = Product.objects.create(
            name='Test Product',
            category=self.category,
            unit=self.unit,
            minimum_stock=Decimal('10.00')
        )
        self.warehouse = Warehouse.objects.create(
            name='Main Warehouse',
            code='WH001',
            manager=admin_user
        )
    
    def test_create_stock(self):
        """Test creating a stock record."""
        stock = Stock.objects.create(
            product=self.product,
            warehouse=self.warehouse,
            quantity=Decimal('100.00')
        )
        assert stock.product == self.product
        assert stock.warehouse == self.warehouse
        assert stock.quantity == Decimal('100.00')
    
    def test_stock_string_representation(self):
        """Test stock string representation."""
        stock = Stock.objects.create(
            product=self.product,
            warehouse=self.warehouse,
            quantity=Decimal('100.00')
        )
        assert str(stock) == 'Test Product - Main Warehouse: 100.00'
    
    def test_stock_available_quantity(self):
        """Test available_quantity property."""
        stock = Stock.objects.create(
            product=self.product,
            warehouse=self.warehouse,
            quantity=Decimal('100.00'),
            reserved_quantity=Decimal('30.00')
        )
        assert stock.available_quantity == Decimal('70.00')
    
    def test_stock_is_low_stock(self):
        """Test is_low_stock property."""
        # Stock below minimum
        stock_low = Stock.objects.create(
            product=self.product,
            warehouse=self.warehouse,
            quantity=Decimal('5.00')
        )
        assert stock_low.is_low_stock is True
        
        # Create another product for second stock test
        product2 = Product.objects.create(
            name='Test Product 2',
            category=self.category,
            unit=self.unit,
            minimum_stock=Decimal('10.00')
        )
        stock_ok = Stock.objects.create(
            product=product2,
            warehouse=self.warehouse,
            quantity=Decimal('50.00')
        )
        assert stock_ok.is_low_stock is False
    
    def test_stock_reserved_quantity(self):
        """Test reserved quantity tracking."""
        stock = Stock.objects.create(
            product=self.product,
            warehouse=self.warehouse,
            quantity=Decimal('100.00'),
            reserved_quantity=Decimal('25.00')
        )
        assert stock.reserved_quantity == Decimal('25.00')
    
    def test_stock_unique_constraint(self):
        """Test unique constraint on product and warehouse."""
        Stock.objects.create(
            product=self.product,
            warehouse=self.warehouse,
            quantity=Decimal('100.00')
        )
        
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            Stock.objects.create(
                product=self.product,
                warehouse=self.warehouse,
                quantity=Decimal('200.00')
            )
