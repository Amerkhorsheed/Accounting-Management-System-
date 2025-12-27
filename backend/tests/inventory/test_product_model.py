"""
Tests for Product model.
"""
import pytest
from decimal import Decimal
from apps.inventory.models import Product, Category, Unit


@pytest.mark.django_db
class TestProductModel:
    """Test suite for Product model."""
    
    @pytest.fixture(autouse=True)
    def setup_data(self):
        """Setup test data."""
        self.category = Category.objects.create(name='Electronics')
        self.unit = Unit.objects.create(name='Piece', symbol='PC')
    
    def test_create_product(self):
        """Test creating a product."""
        product = Product.objects.create(
            name='Laptop',
            category=self.category,
            unit=self.unit,
            cost_price=Decimal('1000.00'),
            sale_price=Decimal('1500.00')
        )
        assert product.name == 'Laptop'
        assert product.category == self.category
        assert product.unit == self.unit
        assert product.cost_price == Decimal('1000.00')
        assert product.sale_price == Decimal('1500.00')
    
    def test_product_auto_generate_code(self):
        """Test product code auto-generation."""
        product = Product.objects.create(
            name='Laptop',
            category=self.category,
            unit=self.unit
        )
        assert product.code is not None
        assert product.code.startswith('PRD')
    
    def test_product_auto_generate_barcode(self):
        """Test product barcode auto-generation."""
        product = Product.objects.create(
            name='Laptop',
            category=self.category,
            unit=self.unit
        )
        assert product.barcode is not None
        assert len(product.barcode) > 0
    
    def test_product_string_representation(self):
        """Test product string representation."""
        product = Product.objects.create(
            name='Laptop',
            code='PRD001',
            category=self.category,
            unit=self.unit
        )
        assert str(product) == 'PRD001 - Laptop'
    
    def test_product_types(self):
        """Test all product types."""
        goods = Product.objects.create(
            name='Laptop',
            category=self.category,
            unit=self.unit,
            product_type=Product.ProductType.GOODS
        )
        assert goods.product_type == Product.ProductType.GOODS
        
        service = Product.objects.create(
            name='Repair Service',
            category=self.category,
            unit=self.unit,
            product_type=Product.ProductType.SERVICE
        )
        assert service.product_type == Product.ProductType.SERVICE
        
        consumable = Product.objects.create(
            name='Paper',
            category=self.category,
            unit=self.unit,
            product_type=Product.ProductType.CONSUMABLE
        )
        assert consumable.product_type == Product.ProductType.CONSUMABLE
    
    def test_product_profit_margin(self):
        """Test profit_margin property."""
        product = Product.objects.create(
            name='Laptop',
            category=self.category,
            unit=self.unit,
            cost_price=Decimal('1000.00'),
            sale_price=Decimal('1500.00')
        )
        # Profit margin = ((1500 - 1000) / 1000) * 100 = 50%
        assert product.profit_margin == Decimal('50.00')
    
    def test_product_profit_margin_zero_cost(self):
        """Test profit_margin with zero cost price."""
        product = Product.objects.create(
            name='Laptop',
            category=self.category,
            unit=self.unit,
            cost_price=Decimal('0.00'),
            sale_price=Decimal('1500.00')
        )
        assert product.profit_margin == Decimal('0.00')
    
    def test_product_price_with_tax(self):
        """Test price_with_tax property."""
        product = Product.objects.create(
            name='Laptop',
            category=self.category,
            unit=self.unit,
            sale_price=Decimal('1000.00'),
            is_taxable=True,
            tax_rate=Decimal('15.00')
        )
        # Price with tax = 1000 + (1000 * 0.15) = 1150
        assert product.price_with_tax == Decimal('1150.00')
    
    def test_product_price_with_tax_not_taxable(self):
        """Test price_with_tax for non-taxable product."""
        product = Product.objects.create(
            name='Laptop',
            category=self.category,
            unit=self.unit,
            sale_price=Decimal('1000.00'),
            is_taxable=False
        )
        assert product.price_with_tax == Decimal('1000.00')
    
    def test_product_track_stock(self):
        """Test track_stock field."""
        product = Product.objects.create(
            name='Laptop',
            category=self.category,
            unit=self.unit,
            track_stock=True
        )
        assert product.track_stock is True
    
    def test_product_stock_levels(self):
        """Test product stock level fields."""
        product = Product.objects.create(
            name='Laptop',
            category=self.category,
            unit=self.unit,
            minimum_stock=Decimal('10.00'),
            maximum_stock=Decimal('100.00'),
            reorder_point=Decimal('20.00')
        )
        assert product.minimum_stock == Decimal('10.00')
        assert product.maximum_stock == Decimal('100.00')
        assert product.reorder_point == Decimal('20.00')
    
    def test_product_pricing_fields(self):
        """Test all pricing fields."""
        product = Product.objects.create(
            name='Laptop',
            category=self.category,
            unit=self.unit,
            cost_price=Decimal('1000.00'),
            sale_price=Decimal('1500.00'),
            wholesale_price=Decimal('1300.00'),
            minimum_price=Decimal('1200.00')
        )
        assert product.cost_price == Decimal('1000.00')
        assert product.sale_price == Decimal('1500.00')
        assert product.wholesale_price == Decimal('1300.00')
        assert product.minimum_price == Decimal('1200.00')
    
    def test_product_brand_and_model(self):
        """Test brand and model fields."""
        product = Product.objects.create(
            name='Laptop',
            category=self.category,
            unit=self.unit,
            brand='Dell',
            model='XPS 15'
        )
        assert product.brand == 'Dell'
        assert product.model == 'XPS 15'
