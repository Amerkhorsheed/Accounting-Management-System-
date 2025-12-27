"""
Tests for GoodsReceivedNote and GRNItem models.
"""
import pytest
from decimal import Decimal
from apps.purchases.models import GoodsReceivedNote, GRNItem, PurchaseOrder, PurchaseOrderItem, Supplier
from apps.inventory.models import Product, Warehouse, Category, Unit


@pytest.mark.django_db
class TestGoodsReceivedNoteModel:
    """Test suite for GoodsReceivedNote model."""
    
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
            unit=self.unit
        )
        self.purchase_order = PurchaseOrder.objects.create(
            supplier=self.supplier,
            warehouse=self.warehouse,
            order_date=today
        )
        self.user = admin_user
        self.today = today
    
    def test_create_grn(self):
        """Test creating a goods received note."""
        grn = GoodsReceivedNote.objects.create(
            purchase_order=self.purchase_order,
            received_date=self.today,
            received_by=self.user
        )
        assert grn.purchase_order == self.purchase_order
        assert grn.received_date == self.today
        assert grn.received_by == self.user
    
    def test_grn_auto_generate_number(self):
        """Test GRN number auto-generation."""
        grn = GoodsReceivedNote.objects.create(
            purchase_order=self.purchase_order,
            received_date=self.today,
            received_by=self.user
        )
        assert grn.grn_number is not None
        assert grn.grn_number.startswith('GRN')
    
    def test_grn_string_representation(self):
        """Test GRN string representation."""
        grn = GoodsReceivedNote.objects.create(
            grn_number='GRN001',
            purchase_order=self.purchase_order,
            received_date=self.today,
            received_by=self.user
        )
        assert 'GRN001' in str(grn)
        assert self.purchase_order.order_number in str(grn)
    
    def test_grn_supplier_invoice_number(self):
        """Test GRN supplier invoice number field."""
        grn = GoodsReceivedNote.objects.create(
            purchase_order=self.purchase_order,
            received_date=self.today,
            supplier_invoice_no='SUP-INV-123',
            received_by=self.user
        )
        assert grn.supplier_invoice_no == 'SUP-INV-123'


@pytest.mark.django_db
class TestGRNItemModel:
    """Test suite for GRNItem model."""
    
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
            unit=self.unit
        )
        self.purchase_order = PurchaseOrder.objects.create(
            supplier=self.supplier,
            warehouse=self.warehouse,
            order_date=today
        )
        self.po_item = PurchaseOrderItem.objects.create(
            purchase_order=self.purchase_order,
            product=self.product,
            quantity=Decimal('100.00'),
            unit_price=Decimal('50.00')
        )
        self.grn = GoodsReceivedNote.objects.create(
            purchase_order=self.purchase_order,
            received_date=today,
            received_by=admin_user
        )
    
    def test_create_grn_item(self):
        """Test creating a GRN item."""
        grn_item = GRNItem.objects.create(
            grn=self.grn,
            po_item=self.po_item,
            product=self.product,
            quantity_received=Decimal('80.00')
        )
        assert grn_item.grn == self.grn
        assert grn_item.po_item == self.po_item
        assert grn_item.product == self.product
        assert grn_item.quantity_received == Decimal('80.00')
    
    def test_grn_item_string_representation(self):
        """Test GRN item string representation."""
        grn_item = GRNItem.objects.create(
            grn=self.grn,
            po_item=self.po_item,
            product=self.product,
            quantity_received=Decimal('80.00')
        )
        assert 'Test Product' in str(grn_item)
        assert '80.00' in str(grn_item)
    
    def test_grn_item_partial_receipt(self):
        """Test partial receipt of ordered quantity."""
        grn_item = GRNItem.objects.create(
            grn=self.grn,
            po_item=self.po_item,
            product=self.product,
            quantity_received=Decimal('60.00')
        )
        # Ordered 100, received 60
        assert grn_item.quantity_received < self.po_item.quantity
