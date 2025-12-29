"""
Property-based tests for Invoice Cancellation.

Feature: desktop-full-crud-returns
Tests Property 9 from the design document.
"""
import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from decimal import Decimal
from datetime import date
import uuid

from apps.sales.models import (
    Customer, Invoice, InvoiceItem
)
from apps.sales.services import SalesService
from apps.inventory.models import (
    Product, Category, Unit, Warehouse, Stock, StockMovement
)
from apps.core.exceptions import ValidationException, InvalidOperationException
from django.contrib.auth import get_user_model

User = get_user_model()


# ============================================================================
# Strategies for test data generation
# ============================================================================

# Quantity strategy - positive decimals with reasonable bounds
quantity_strategy = st.decimals(
    min_value=Decimal('1.00'),
    max_value=Decimal('100.00'),
    places=2
).filter(lambda x: x > 0)

# Price strategy - positive decimals for prices
price_strategy = st.decimals(
    min_value=Decimal('1.00'),
    max_value=Decimal('1000.00'),
    places=2
).filter(lambda x: x > 0)


# ============================================================================
# Helper Functions
# ============================================================================

def create_test_data():
    """Create fresh test data for each test iteration."""
    unique_id = uuid.uuid4().hex[:12]
    
    # Create user
    user = User.objects.create_user(
        username=f'test_user_{unique_id}',
        password='password123',
        first_name='Test',
        last_name='User',
        is_active=True
    )
    
    # Create category
    category = Category.objects.create(name=f'Test Category {unique_id}')
    
    # Create unit
    unit = Unit.objects.create(
        name=f'Piece {unique_id}',
        symbol=f'P{unique_id[:6]}'
    )
    
    # Create warehouse
    warehouse = Warehouse.objects.create(
        name=f'Test Warehouse {unique_id}',
        code=f'WH{unique_id}',
        manager=user
    )
    
    # Create customer with explicit code
    customer = Customer.objects.create(
        name=f'Test Customer {unique_id}',
        code=f'TCUS{unique_id}',
        credit_limit=Decimal('100000.00'),
        current_balance=Decimal('0.00')
    )
    
    return user, category, unit, warehouse, customer


def create_product_with_stock(category, unit, warehouse, quantity, cost_price, sale_price):
    """Helper to create a product with initial stock."""
    unique_id = uuid.uuid4().hex[:12]
    product = Product.objects.create(
        name=f'Test Product {unique_id}',
        barcode=f'TBAR{unique_id}',
        code=f'TPRD{unique_id}',
        category=category,
        unit=unit,
        cost_price=cost_price,
        sale_price=sale_price,
        track_stock=True
    )
    Stock.objects.create(
        product=product,
        warehouse=warehouse,
        quantity=quantity
    )
    return product


def create_confirmed_invoice_with_item(customer, warehouse, product, quantity, unit_price, user):
    """Helper to create a confirmed invoice with one item."""
    unique_id = uuid.uuid4().hex[:8]
    invoice = Invoice.objects.create(
        invoice_number=f'INV-{unique_id}',
        customer=customer,
        warehouse=warehouse,
        invoice_date=date.today(),
        invoice_type=Invoice.InvoiceType.CREDIT,
        status=Invoice.Status.DRAFT,
        total_amount=Decimal('0.00'),
        created_by=user
    )
    InvoiceItem.objects.create(
        invoice=invoice,
        product=product,
        quantity=quantity,
        unit_price=unit_price,
        cost_price=product.cost_price,
        created_by=user
    )
    # Calculate totals
    invoice.calculate_totals()
    
    # Confirm the invoice to deduct stock and update customer balance
    invoice = SalesService.confirm_invoice(invoice.id, user=user)
    
    return invoice


# ============================================================================
# Property Tests
# ============================================================================

@pytest.mark.django_db(transaction=True)
class TestInvoiceCancellationProperties:
    """
    Property-based tests for invoice cancellation functionality.
    
    Feature: desktop-full-crud-returns
    """

    @given(
        original_qty=quantity_strategy,
        unit_price=price_strategy
    )
    @settings(
        deadline=None,
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_cancellation_stock_restoration(
        self,
        original_qty,
        unit_price
    ):
        """
        Property 9a: Invoice Cancellation Stock Restoration
        
        For any successfully cancelled invoice, the stock quantity for each
        product SHALL increase by exactly the quantity that was originally
        deducted (in base units).
        
        **Validates: Requirements 4.5**
        **Feature: desktop-full-crud-returns, Property 9: Invoice Cancellation Reversal**
        """
        # Create fresh test data for this iteration
        user, category, unit, warehouse, customer = create_test_data()
        
        # Setup: Create product with enough stock
        initial_stock = original_qty * 3
        cost_price = unit_price * Decimal('0.7')
        
        product = create_product_with_stock(
            category, unit, warehouse,
            initial_stock, cost_price, unit_price
        )
        
        # Get stock before invoice creation
        stock_before_invoice = Stock.objects.get(
            product=product,
            warehouse=warehouse
        ).quantity
        
        # Create and confirm invoice (this deducts stock)
        invoice = create_confirmed_invoice_with_item(
            customer, warehouse, product,
            original_qty, unit_price, user
        )
        
        # Verify stock was deducted
        stock_after_invoice = Stock.objects.get(
            product=product,
            warehouse=warehouse
        ).quantity
        
        assert stock_after_invoice == stock_before_invoice - original_qty, (
            f"Stock should be deducted by {original_qty} after invoice confirmation"
        )
        
        # Cancel the invoice
        cancelled_invoice = SalesService.cancel_invoice(
            invoice_id=invoice.id,
            reason='Property test - stock restoration',
            user=user
        )
        
        # Verify stock was restored
        stock_after_cancel = Stock.objects.get(
            product=product,
            warehouse=warehouse
        ).quantity
        
        assert stock_after_cancel == stock_before_invoice, (
            f"Stock should be restored to {stock_before_invoice} after cancellation, "
            f"but was {stock_after_cancel}"
        )
        
        # Verify invoice status is cancelled
        assert cancelled_invoice.status == Invoice.Status.CANCELLED

    @given(
        original_qty=quantity_strategy,
        unit_price=price_strategy
    )
    @settings(
        deadline=None,
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_cancellation_customer_balance_reversal(
        self,
        original_qty,
        unit_price
    ):
        """
        Property 9b: Invoice Cancellation Customer Balance Reversal
        
        For any successfully cancelled credit invoice, the customer's
        current_balance SHALL decrease by exactly the unpaid portion
        of the invoice (total_amount - paid_amount).
        
        **Validates: Requirements 4.5**
        **Feature: desktop-full-crud-returns, Property 9: Invoice Cancellation Reversal**
        """
        # Create fresh test data for this iteration
        user, category, unit, warehouse, customer = create_test_data()
        
        # Setup: Create product with enough stock
        initial_stock = original_qty * 3
        cost_price = unit_price * Decimal('0.7')
        
        product = create_product_with_stock(
            category, unit, warehouse,
            initial_stock, cost_price, unit_price
        )
        
        # Set initial customer balance
        initial_balance = Decimal('1000.00')
        customer.current_balance = initial_balance
        customer.save()
        
        # Create and confirm credit invoice
        invoice = create_confirmed_invoice_with_item(
            customer, warehouse, product,
            original_qty, unit_price, user
        )
        
        # Get customer balance after invoice (should have increased)
        customer.refresh_from_db()
        balance_after_invoice = customer.current_balance
        
        # Get the actual invoice total (includes tax if applicable)
        invoice.refresh_from_db()
        actual_invoice_total = invoice.total_amount
        
        # For credit invoices with no payment, balance increases by total
        assert balance_after_invoice == initial_balance + actual_invoice_total, (
            f"Customer balance should increase by {actual_invoice_total} after credit invoice, "
            f"but balance went from {initial_balance} to {balance_after_invoice}"
        )
        
        # Cancel the invoice
        SalesService.cancel_invoice(
            invoice_id=invoice.id,
            reason='Property test - balance reversal',
            user=user
        )
        
        # Verify customer balance was restored
        customer.refresh_from_db()
        balance_after_cancel = customer.current_balance
        
        assert balance_after_cancel == initial_balance, (
            f"Customer balance should be restored to {initial_balance} after cancellation, "
            f"but was {balance_after_cancel}"
        )

    @given(
        original_qty=quantity_strategy,
        unit_price=price_strategy
    )
    @settings(
        deadline=None,
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_cancellation_creates_stock_movement(
        self,
        original_qty,
        unit_price
    ):
        """
        Property 9c: Invoice Cancellation Stock Movement Creation
        
        For any successfully cancelled invoice, a StockMovement record
        with source_type="adjustment" SHALL be created for each item,
        with quantity matching the original invoice quantity.
        
        **Validates: Requirements 4.5**
        **Feature: desktop-full-crud-returns, Property 9: Invoice Cancellation Reversal**
        """
        # Create fresh test data for this iteration
        user, category, unit, warehouse, customer = create_test_data()
        
        # Setup: Create product with enough stock
        initial_stock = original_qty * 3
        cost_price = unit_price * Decimal('0.7')
        
        product = create_product_with_stock(
            category, unit, warehouse,
            initial_stock, cost_price, unit_price
        )
        
        # Create and confirm invoice
        invoice = create_confirmed_invoice_with_item(
            customer, warehouse, product,
            original_qty, unit_price, user
        )
        
        # Count movements before cancellation
        movements_before = StockMovement.objects.filter(
            product=product,
            warehouse=warehouse
        ).count()
        
        # Cancel the invoice
        SalesService.cancel_invoice(
            invoice_id=invoice.id,
            reason='Property test - movement creation',
            user=user
        )
        
        # Verify a new movement was created
        movements_after = StockMovement.objects.filter(
            product=product,
            warehouse=warehouse
        ).count()
        
        assert movements_after > movements_before, (
            "A new stock movement should be created for the cancellation"
        )
        
        # Find the cancellation movement
        cancel_movement = StockMovement.objects.filter(
            product=product,
            warehouse=warehouse,
            source_type=StockMovement.SourceType.ADJUSTMENT,
            reference_id=invoice.id,
            reference_type='invoice_cancellation'
        ).first()
        
        assert cancel_movement is not None, (
            "A stock movement with source_type='adjustment' and "
            "reference_type='invoice_cancellation' should exist"
        )
        assert cancel_movement.quantity == original_qty, (
            f"Movement quantity should be {original_qty}, "
            f"but was {cancel_movement.quantity}"
        )
        assert cancel_movement.movement_type == StockMovement.MovementType.IN, (
            "Cancellation movement should be of type 'in'"
        )

    @given(
        original_qty=quantity_strategy,
        unit_price=price_strategy
    )
    @settings(
        deadline=None,
        max_examples=50,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_cancellation_requires_reason(
        self,
        original_qty,
        unit_price
    ):
        """
        Property 9d: Invoice Cancellation Requires Reason
        
        Any attempt to cancel an invoice without providing a reason
        SHALL be rejected with a ValidationException.
        
        **Validates: Requirements 4.4**
        **Feature: desktop-full-crud-returns, Property 9: Invoice Cancellation Reversal**
        """
        # Create fresh test data for this iteration
        user, category, unit, warehouse, customer = create_test_data()
        
        # Setup: Create product with enough stock
        initial_stock = original_qty * 3
        cost_price = unit_price * Decimal('0.7')
        
        product = create_product_with_stock(
            category, unit, warehouse,
            initial_stock, cost_price, unit_price
        )
        
        # Create and confirm invoice
        invoice = create_confirmed_invoice_with_item(
            customer, warehouse, product,
            original_qty, unit_price, user
        )
        
        # Attempt to cancel without reason - should fail
        with pytest.raises(ValidationException):
            SalesService.cancel_invoice(
                invoice_id=invoice.id,
                reason='',
                user=user
            )
        
        # Attempt to cancel with None reason - should fail
        with pytest.raises(ValidationException):
            SalesService.cancel_invoice(
                invoice_id=invoice.id,
                reason=None,
                user=user
            )
        
        # Verify invoice is still in original status
        invoice.refresh_from_db()
        assert invoice.status != Invoice.Status.CANCELLED, (
            "Invoice should not be cancelled when reason is not provided"
        )

    @given(
        original_qty=quantity_strategy,
        unit_price=price_strategy
    )
    @settings(
        deadline=None,
        max_examples=50,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_cancellation_only_for_valid_statuses(
        self,
        original_qty,
        unit_price
    ):
        """
        Property 9e: Invoice Cancellation Status Validation
        
        Only invoices with status CONFIRMED, PAID, or PARTIAL can be cancelled.
        Attempting to cancel a DRAFT or already CANCELLED invoice SHALL be rejected.
        
        **Validates: Requirements 4.4**
        **Feature: desktop-full-crud-returns, Property 9: Invoice Cancellation Reversal**
        """
        # Create fresh test data for this iteration
        user, category, unit, warehouse, customer = create_test_data()
        
        # Setup: Create product with enough stock
        initial_stock = original_qty * 3
        cost_price = unit_price * Decimal('0.7')
        
        product = create_product_with_stock(
            category, unit, warehouse,
            initial_stock, cost_price, unit_price
        )
        
        # Create a draft invoice (not confirmed)
        unique_id = uuid.uuid4().hex[:8]
        draft_invoice = Invoice.objects.create(
            invoice_number=f'INV-{unique_id}',
            customer=customer,
            warehouse=warehouse,
            invoice_date=date.today(),
            invoice_type=Invoice.InvoiceType.CREDIT,
            status=Invoice.Status.DRAFT,
            total_amount=original_qty * unit_price,
            created_by=user
        )
        InvoiceItem.objects.create(
            invoice=draft_invoice,
            product=product,
            quantity=original_qty,
            unit_price=unit_price,
            cost_price=product.cost_price,
            created_by=user
        )
        
        # Attempt to cancel draft invoice - should fail
        with pytest.raises(InvalidOperationException):
            SalesService.cancel_invoice(
                invoice_id=draft_invoice.id,
                reason='Test cancellation',
                user=user
            )
        
        # Verify draft invoice is still draft
        draft_invoice.refresh_from_db()
        assert draft_invoice.status == Invoice.Status.DRAFT

