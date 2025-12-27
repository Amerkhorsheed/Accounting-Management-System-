"""
Tests for StockMovement model.
"""
import pytest
from decimal import Decimal
from apps.inventory.models import StockMovement, Product, Warehouse, Category, Unit


@pytest.mark.django_db
class TestStockMovementModel:
    """Test suite for StockMovement model."""
    
    @pytest.fixture(autouse=True)
    def setup_data(self, admin_user, today):
        """Setup test data."""
        self.category = Category.objects.create(name='Test Category')
        self.unit = Unit.objects.create(name='Piece', symbol='PC')
        self.product = Product.objects.create(
            name='Test Product',
            category=self.category,
            unit=self.unit
        )
        self.warehouse = Warehouse.objects.create(
            name='Main Warehouse',
            code='WH001',
            manager=admin_user
        )
        self.user = admin_user
    
    def test_create_stock_movement(self):
        """Test creating a stock movement."""
        movement = StockMovement.objects.create(
            product=self.product,
            warehouse=self.warehouse,
            movement_type=StockMovement.MovementType.IN,
            source_type=StockMovement.SourceType.PURCHASE,
            quantity=Decimal('50.00'),
            unit_cost=Decimal('100.00'),
            balance_before=Decimal('0.00'),
            balance_after=Decimal('50.00'),
            created_by=self.user
        )
        assert movement.product == self.product
        assert movement.warehouse == self.warehouse
        assert movement.quantity == Decimal('50.00')
    
    def test_stock_movement_string_representation(self):
        """Test stock movement string representation."""
        movement = StockMovement.objects.create(
            product=self.product,
            warehouse=self.warehouse,
            movement_type=StockMovement.MovementType.IN,
            source_type=StockMovement.SourceType.PURCHASE,
            quantity=Decimal('50.00'),
            balance_before=Decimal('0.00'),
            balance_after=Decimal('50.00')
        )
        assert 'Test Product' in str(movement)
        assert '50.00' in str(movement)
    
    def test_stock_movement_types(self):
        """Test all movement types."""
        types = [
            StockMovement.MovementType.IN,
            StockMovement.MovementType.OUT,
            StockMovement.MovementType.ADJUSTMENT,
            StockMovement.MovementType.TRANSFER,
            StockMovement.MovementType.RETURN,
            StockMovement.MovementType.DAMAGE
        ]
        
        for movement_type in types:
            movement = StockMovement.objects.create(
                product=self.product,
                warehouse=self.warehouse,
                movement_type=movement_type,
                source_type=StockMovement.SourceType.ADJUSTMENT,
                quantity=Decimal('10.00'),
                balance_before=Decimal('0.00'),
                balance_after=Decimal('10.00')
            )
            assert movement.movement_type == movement_type
    
    def test_stock_movement_source_types(self):
        """Test all source types."""
        sources = [
            StockMovement.SourceType.PURCHASE,
            StockMovement.SourceType.SALE,
            StockMovement.SourceType.ADJUSTMENT,
            StockMovement.SourceType.TRANSFER,
            StockMovement.SourceType.OPENING,
            StockMovement.SourceType.RETURN
        ]
        
        for source_type in sources:
            movement = StockMovement.objects.create(
                product=self.product,
                warehouse=self.warehouse,
                movement_type=StockMovement.MovementType.IN,
                source_type=source_type,
                quantity=Decimal('10.00'),
                balance_before=Decimal('0.00'),
                balance_after=Decimal('10.00')
            )
            assert movement.source_type == source_type
    
    def test_stock_movement_balance_tracking(self):
        """Test balance tracking."""
        movement = StockMovement.objects.create(
            product=self.product,
            warehouse=self.warehouse,
            movement_type=StockMovement.MovementType.IN,
            source_type=StockMovement.SourceType.PURCHASE,
            quantity=Decimal('50.00'),
            balance_before=Decimal('100.00'),
            balance_after=Decimal('150.00')
        )
        assert movement.balance_before == Decimal('100.00')
        assert movement.balance_after == Decimal('150.00')
    
    def test_stock_movement_reference_tracking(self):
        """Test reference tracking."""
        movement = StockMovement.objects.create(
            product=self.product,
            warehouse=self.warehouse,
            movement_type=StockMovement.MovementType.IN,
            source_type=StockMovement.SourceType.PURCHASE,
            quantity=Decimal('50.00'),
            balance_before=Decimal('0.00'),
            balance_after=Decimal('50.00'),
            reference_number='PO001',
            reference_type='PurchaseOrder',
            reference_id=123
        )
        assert movement.reference_number == 'PO001'
        assert movement.reference_type == 'PurchaseOrder'
        assert movement.reference_id == 123
