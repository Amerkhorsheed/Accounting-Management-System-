"""
Tests for SupplierPayment model.
"""
import pytest
from decimal import Decimal
from apps.purchases.models import SupplierPayment, Supplier, PurchaseOrder
from apps.inventory.models import Warehouse


@pytest.mark.django_db
class TestSupplierPaymentModel:
    """Test suite for SupplierPayment model."""
    
    @pytest.fixture(autouse=True)
    def setup_data(self, admin_user, today):
        """Setup test data."""
        self.supplier = Supplier.objects.create(name='Test Supplier')
        self.warehouse = Warehouse.objects.create(
            name='Main Warehouse',
            code='WH001',
            manager=admin_user
        )
        self.purchase_order = PurchaseOrder.objects.create(
            supplier=self.supplier,
            warehouse=self.warehouse,
            order_date=today,
            total_amount=Decimal('5000.00')
        )
        self.today = today
    
    def test_create_supplier_payment(self):
        """Test creating a supplier payment."""
        payment = SupplierPayment.objects.create(
            supplier=self.supplier,
            purchase_order=self.purchase_order,
            payment_date=self.today,
            amount=Decimal('2000.00')
        )
        assert payment.supplier == self.supplier
        assert payment.purchase_order == self.purchase_order
        assert payment.amount == Decimal('2000.00')
    
    def test_supplier_payment_auto_generate_number(self):
        """Test supplier payment number auto-generation."""
        payment = SupplierPayment.objects.create(
            supplier=self.supplier,
            payment_date=self.today,
            amount=Decimal('2000.00')
        )
        assert payment.payment_number is not None
        assert payment.payment_number.startswith('PAY')
    
    def test_supplier_payment_string_representation(self):
        """Test supplier payment string representation."""
        payment = SupplierPayment.objects.create(
            payment_number='PAY001',
            supplier=self.supplier,
            payment_date=self.today,
            amount=Decimal('2000.00')
        )
        assert str(payment) == 'PAY001 - Test Supplier: 2000.00'
    
    def test_supplier_payment_methods(self):
        """Test all payment methods."""
        methods = [
            SupplierPayment.PaymentMethod.CASH,
            SupplierPayment.PaymentMethod.BANK,
            SupplierPayment.PaymentMethod.CHECK,
            SupplierPayment.PaymentMethod.CREDIT
        ]
        
        for method in methods:
            payment = SupplierPayment.objects.create(
                supplier=self.supplier,
                payment_date=self.today,
                amount=Decimal('1000.00'),
                payment_method=method
            )
            assert payment.payment_method == method
    
    def test_supplier_payment_without_purchase_order(self):
        """Test payment without specific purchase order (advance payment)."""
        payment = SupplierPayment.objects.create(
            supplier=self.supplier,
            payment_date=self.today,
            amount=Decimal('5000.00')
        )
        assert payment.purchase_order is None
    
    def test_supplier_payment_reference(self):
        """Test payment reference field."""
        payment = SupplierPayment.objects.create(
            supplier=self.supplier,
            payment_date=self.today,
            amount=Decimal('2000.00'),
            payment_method=SupplierPayment.PaymentMethod.CHECK,
            reference='CHK987654'
        )
        assert payment.reference == 'CHK987654'
