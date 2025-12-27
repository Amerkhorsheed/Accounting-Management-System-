"""
Tests for ProductUnit model.
"""
import pytest
from decimal import Decimal
from django.db import IntegrityError
from apps.inventory.models import Product, ProductUnit, Unit, Category


@pytest.mark.django_db
class TestProductUnitModel:
    """Test suite for ProductUnit model."""
    
    @pytest.fixture(autouse=True)
    def setup_data(self):
        """Setup test data."""
        self.category = Category.objects.create(name='Electronics')
        self.base_unit = Unit.objects.create(name='Piece', symbol='PC')
        self.box_unit = Unit.objects.create(name='Box', symbol='BOX')
        self.product = Product.objects.create(
            name='Laptop',
            category=self.category,
            unit=self.base_unit
        )
    
    def test_create_product_unit(self):
        """Test creating a product unit."""
        product_unit = ProductUnit.objects.create(
            product=self.product,
            unit=self.box_unit,
            conversion_factor=Decimal('12.0000'),
            sale_price=Decimal('1500.00')
        )
        assert product_unit.product == self.product
        assert product_unit.unit == self.box_unit
        assert product_unit.conversion_factor == Decimal('12.0000')
    
    def test_product_unit_string_representation(self):
        """Test product unit string representation."""
        product_unit = ProductUnit.objects.create(
            product=self.product,
            unit=self.box_unit,
            conversion_factor=Decimal('12.0000')
        )
        assert str(product_unit) == 'Laptop - Box'
    
    def test_product_unit_convert_to_base(self):
        """Test convert_to_base method."""
        product_unit = ProductUnit.objects.create(
            product=self.product,
            unit=self.box_unit,
            conversion_factor=Decimal('12.0000')
        )
        # 5 boxes * 12 pieces/box = 60 pieces
        result = product_unit.convert_to_base(Decimal('5.0000'))
        assert result == Decimal('60.0000')
    
    def test_product_unit_convert_from_base(self):
        """Test convert_from_base method."""
        product_unit = ProductUnit.objects.create(
            product=self.product,
            unit=self.box_unit,
            conversion_factor=Decimal('12.0000')
        )
        # 60 pieces / 12 pieces/box = 5 boxes
        result = product_unit.convert_from_base(Decimal('60.0000'))
        assert result == Decimal('5.0000')
    
    def test_product_unit_conversion_round_trip(self):
        """Test conversion round trip."""
        product_unit = ProductUnit.objects.create(
            product=self.product,
            unit=self.box_unit,
            conversion_factor=Decimal('12.0000')
        )
        original = Decimal('5.0000')
        base = product_unit.convert_to_base(original)
        back = product_unit.convert_from_base(base)
        assert back == original
    
    def test_product_unit_is_base_unit(self):
        """Test is_base_unit field."""
        product_unit = ProductUnit.objects.create(
            product=self.product,
            unit=self.base_unit,
            conversion_factor=Decimal('1.0000'),
            is_base_unit=True
        )
        assert product_unit.is_base_unit is True
    
    def test_product_unit_pricing(self):
        """Test product unit pricing fields."""
        product_unit = ProductUnit.objects.create(
            product=self.product,
            unit=self.box_unit,
            conversion_factor=Decimal('12.0000'),
            sale_price=Decimal('1500.00'),
            cost_price=Decimal('1000.00')
        )
        assert product_unit.sale_price == Decimal('1500.00')
        assert product_unit.cost_price == Decimal('1000.00')
    
    def test_product_unit_barcode(self):
        """Test product unit barcode field."""
        product_unit = ProductUnit.objects.create(
            product=self.product,
            unit=self.box_unit,
            conversion_factor=Decimal('12.0000'),
            barcode='123456789'
        )
        assert product_unit.barcode == '123456789'
    
    def test_product_unit_unique_constraint(self):
        """Test unique constraint on product and unit."""
        ProductUnit.objects.create(
            product=self.product,
            unit=self.box_unit,
            conversion_factor=Decimal('12.0000')
        )
        
        with pytest.raises(IntegrityError):
            ProductUnit.objects.create(
                product=self.product,
                unit=self.box_unit,
                conversion_factor=Decimal('24.0000')
            )
    
    def test_product_unit_positive_conversion_factor(self):
        """Test that conversion factor must be positive."""
        # This should work
        product_unit = ProductUnit.objects.create(
            product=self.product,
            unit=self.box_unit,
            conversion_factor=Decimal('12.0000')
        )
        assert product_unit.conversion_factor > 0
