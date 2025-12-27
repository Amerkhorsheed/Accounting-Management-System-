"""
Tests for PurchaseOrder model.
"""
import pytest
from decimal import Decimal
from apps.purchases.models import PurchaseOrder, Supplier
from apps.inventory.models import Warehouse


@pytest.mark.django_db
class TestPurchaseOrderModel:
    """Test suite for PurchaseOrder model."""
    
    @pytest.fixture(autouse=True)
    def setup_data(self, admin_user, today):
        """Setup test data."""
        self.supplier = Supplier.objects.create(name='Test Supplier')
        self.warehouse = Warehouse.objects.create(
            name='Main Warehouse',
            code='WH001',
            manager=admin_user
        )
        self.today = today
    
    def test_create_purchase_order(self):
        """Test creating a purchase order."""
        po = PurchaseOrder.objects.create(
            supplier=self.supplier,
            warehouse=self.warehouse,
            order_date=self.today
        )
        assert po.supplier == self.supplier
        assert po.warehouse == self.warehouse
        assert po.order_date == self.today
    
    def test_purchase_order_auto_generate_number(self):
        """Test purchase order number auto-generation."""
        po = PurchaseOrder.objects.create(
            supplier=self.supplier,
            warehouse=self.warehouse,
            order_date=self.today
        )
        assert po.order_number is not None
        assert po.order_number.startswith('PO')
    
    def test_purchase_order_string_representation(self):
        """Test purchase order string representation."""
        po = PurchaseOrder.objects.create(
            order_number='PO001',
            supplier=self.supplier,
            warehouse=self.warehouse,
            order_date=self.today
        )
        assert str(po) == 'PO001 - Test Supplier'
    
    def test_purchase_order_statuses(self):
        """Test all purchase order statuses."""
        statuses = [
            PurchaseOrder.Status.DRAFT,
            PurchaseOrder.Status.PENDING,
            PurchaseOrder.Status.APPROVED,
            PurchaseOrder.Status.ORDERED,
            PurchaseOrder.Status.PARTIAL,
            PurchaseOrder.Status.RECEIVED,
            PurchaseOrder.Status.CANCELLED
        ]
        
        for status in statuses:
            po = PurchaseOrder.objects.create(
                supplier=self.supplier,
                warehouse=self.warehouse,
                order_date=self.today,
                status=status
            )
            assert po.status == status
    
    def test_purchase_order_remaining_amount(self):
        """Test remaining_amount property."""
        po = PurchaseOrder.objects.create(
            supplier=self.supplier,
            warehouse=self.warehouse,
            order_date=self.today,
            total_amount=Decimal('5000.00'),
            paid_amount=Decimal('2000.00')
        )
        assert po.remaining_amount == Decimal('3000.00')
    
    def test_purchase_order_amounts(self):
        """Test purchase order amount fields."""
        po = PurchaseOrder.objects.create(
            supplier=self.supplier,
            warehouse=self.warehouse,
            order_date=self.today,
            subtotal=Decimal('5000.00'),
            discount_amount=Decimal('500.00'),
            tax_amount=Decimal('675.00'),
            total_amount=Decimal('5175.00')
        )
        assert po.subtotal == Decimal('5000.00')
        assert po.discount_amount == Decimal('500.00')
        assert po.tax_amount == Decimal('675.00')
        assert po.total_amount == Decimal('5175.00')
    
    def test_purchase_order_expected_date(self, next_week):
        """Test purchase order expected date."""
        po = PurchaseOrder.objects.create(
            supplier=self.supplier,
            warehouse=self.warehouse,
            order_date=self.today,
            expected_date=next_week
        )
        assert po.expected_date == next_week
    
    def test_purchase_order_approval(self, admin_user):
        """Test purchase order approval fields."""
        po = PurchaseOrder.objects.create(
            supplier=self.supplier,
            warehouse=self.warehouse,
            order_date=self.today,
            approved_by=admin_user,
            status=PurchaseOrder.Status.APPROVED
        )
        assert po.approved_by == admin_user
        assert po.approved_at is None  # Set separately
