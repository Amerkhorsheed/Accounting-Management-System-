"""
Tests for PurchaseOrderItem model.
"""
import pytest
from decimal import Decimal
from apps.purchases.models import PurchaseOrderItem, PurchaseOrder, Supplier
from apps.inventory.models import Product, Warehouse, Category, Unit


@pytest.mark.django_db
class TestPurchaseOrderItemModel:
    """Test suite for PurchaseOrderItem model."""
    
    @pytest.fixture(autouse=True)
    def setup_data(self, admin_user, today):
        """Setup test data."""
        self.supplier = Supplier.objects.create(name='Test Supplier')
        self.warehouse = Warehouse.objects.create(
            name='Main Warehouse',
            code='WH001',
            manager=admin_user
        )
        self.category = Category.objects.create(name='Test Category')
        self.unit = Unit.objects.create(name='Piece', symbol='PC')
        self.product = Product.objects.create(
            name='Test Product',
            category=self.category,
            unit=self.unit,
            cost_price=Decimal('50.00')
        )
        self.purchase_order = PurchaseOrder.objects.create(
            supplier=self.supplier,
            warehouse=self.warehouse,
            order_date=today
        )
    
    def test_create_purchase_order_item(self):
        """Test creating a purchase order item."""
        po_item = PurchaseOrderItem.objects.create(
            purchase_order=self.purchase_order,
            product=self.product,
            quantity=Decimal('100.00'),
            unit_price=Decimal('50.00')
        )
        assert po_item.purchase_order == self.purchase_order
        assert po_item.product == self.product
        assert po_item.quantity == Decimal('100.00')
        assert po_item.unit_price == Decimal('50.00')
    
    def test_purchase_order_item_string_representation(self):
        """Test purchase order item string representation."""
        po_item = PurchaseOrderItem.objects.create(
            purchase_order=self.purchase_order,
            product=self.product,
            quantity=Decimal('100.00'),
            unit_price=Decimal('50.00')
        )
        assert str(po_item) == 'Test Product x 100.00'
    
    def test_purchase_order_item_subtotal(self):
        """Test subtotal property."""
        po_item = PurchaseOrderItem.objects.create(
            purchase_order=self.purchase_order,
            product=self.product,
            quantity=Decimal('100.00'),
            unit_price=Decimal('50.00')
        )
        assert po_item.subtotal == Decimal('5000.00')
    
    def test_purchase_order_item_discount_amount(self):
        """Test discount_amount property."""
        po_item = PurchaseOrderItem.objects.create(
            purchase_order=self.purchase_order,
            product=self.product,
            quantity=Decimal('100.00'),
            unit_price=Decimal('50.00'),
            discount_percent=Decimal('10.00')
        )
        # Discount = 5000 * 0.10 = 500
        assert po_item.discount_amount == Decimal('500.00')
    
    def test_purchase_order_item_taxable_amount(self):
        """Test taxable_amount property."""
        po_item = PurchaseOrderItem.objects.create(
            purchase_order=self.purchase_order,
            product=self.product,
            quantity=Decimal('100.00'),
            unit_price=Decimal('50.00'),
            discount_percent=Decimal('10.00')
        )
        # Taxable = Subtotal - Discount = 5000 - 500 = 4500
        assert po_item.taxable_amount == Decimal('4500.00')
    
    def test_purchase_order_item_tax_amount(self):
        """Test tax_amount property."""
        po_item = PurchaseOrderItem.objects.create(
            purchase_order=self.purchase_order,
            product=self.product,
            quantity=Decimal('100.00'),
            unit_price=Decimal('50.00'),
            discount_percent=Decimal('10.00'),
            tax_rate=Decimal('15.00')
        )
        # Tax = Taxable * 0.15 = 4500 * 0.15 = 675
        assert po_item.tax_amount == Decimal('675.00')
    
    def test_purchase_order_item_total(self):
        """Test total property."""
        po_item = PurchaseOrderItem.objects.create(
            purchase_order=self.purchase_order,
            product=self.product,
            quantity=Decimal('100.00'),
            unit_price=Decimal('50.00'),
            discount_percent=Decimal('10.00'),
            tax_rate=Decimal('15.00')
        )
        # Total = Taxable + Tax = 4500 + 675 = 5175
        assert po_item.total == Decimal('5175.00')
    
    def test_purchase_order_item_remaining_quantity(self):
        """Test remaining_quantity property."""
        po_item = PurchaseOrderItem.objects.create(
            purchase_order=self.purchase_order,
            product=self.product,
            quantity=Decimal('100.00'),
            received_quantity=Decimal('60.00'),
            unit_price=Decimal('50.00')
        )
        assert po_item.remaining_quantity == Decimal('40.00')
