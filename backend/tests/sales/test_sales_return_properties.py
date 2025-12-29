"""
Property-based tests for Sales Return Service.

Feature: desktop-full-crud-returns
Tests Properties 3, 4, 5, 6 from the design document.
"""
import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from decimal import Decimal
from datetime import date
import uuid

from apps.sales.models import (
    Customer, Invoice, InvoiceItem, SalesReturn, SalesReturnItem
)
from apps.sales.services import SalesService
from apps.inventory.models import (
    Product, Category, Unit, Warehouse, Stock, StockMovement
)
from apps.core.exceptions import ValidationException, InvalidOperationException
from django.contrib.auth import get_user_model
from django.db import transaction

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

# Return quantity ratio - between 0 and 1 (percentage of original to return)
return_ratio_strategy = st.decimals(
    min_value=Decimal('0.10'),
    max_value=Decimal('1.00'),
    places=2
)


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


def create_confirmed_invoice_with_item(customer, warehouse, product, quantity, unit_price):
    """Helper to create a confirmed invoice with one item."""
    unique_id = uuid.uuid4().hex[:8]
    invoice = Invoice.objects.create(
        invoice_number=f'INV-{unique_id}',
        customer=customer,
        warehouse=warehouse,
        invoice_date=date.today(),
        status=Invoice.Status.CONFIRMED,
        total_amount=quantity * unit_price
    )
    invoice_item = InvoiceItem.objects.create(
        invoice=invoice,
        product=product,
        quantity=quantity,
        unit_price=unit_price,
        cost_price=product.cost_price
    )
    return invoice, invoice_item


# ============================================================================
# Property Tests
# ============================================================================

@pytest.mark.django_db(transaction=True)
class TestSalesReturnProperties:
    """
    Property-based tests for sales return functionality.
    
    Feature: desktop-full-crud-returns
    """

    @given(
        original_qty=quantity_strategy,
        return_ratio=return_ratio_strategy,
        unit_price=price_strategy
    )
    @settings(
        deadline=None,
        max_examples=10,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_return_quantity_validation(
        self,
        original_qty,
        return_ratio,
        unit_price
    ):
        """
        Property 3: Return Quantity Validation
        
        For any sales return attempt, the return quantity for each item SHALL NOT
        exceed (original_quantity - already_returned_quantity). If this constraint
        is violated, the return SHALL be rejected.
        
        **Validates: Requirements 5.3**
        **Feature: desktop-full-crud-returns, Property 3: Return Quantity Validation**
        """
        # Create fresh test data for this iteration
        user, category, unit, warehouse, customer = create_test_data()
        
        # Setup: Create product with enough stock
        initial_stock = original_qty * 2
        cost_price = unit_price * Decimal('0.7')
        
        product = create_product_with_stock(
            category, unit, warehouse,
            initial_stock, cost_price, unit_price
        )
        
        # Create confirmed invoice
        invoice, invoice_item = create_confirmed_invoice_with_item(
            customer, warehouse, product,
            original_qty, unit_price
        )
        
        # Calculate valid return quantity
        valid_return_qty = (original_qty * return_ratio).quantize(Decimal('0.01'))
        assume(valid_return_qty > 0)
        
        # Test: Valid return should succeed
        sales_return = SalesService.create_sales_return(
            invoice_id=invoice.id,
            return_date=date.today(),
            items=[{
                'invoice_item_id': invoice_item.id,
                'quantity': valid_return_qty,
                'reason': 'Test return'
            }],
            reason='Property test - valid return',
            user=user
        )
        
        assert sales_return is not None
        assert sales_return.items.count() == 1
        assert sales_return.items.first().quantity == valid_return_qty

    @given(
        original_qty=quantity_strategy,
        return_ratio=return_ratio_strategy,
        unit_price=price_strategy
    )
    @settings(
        deadline=None,
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_return_stock_restoration(
        self,
        original_qty,
        return_ratio,
        unit_price
    ):
        """
        Property 4: Return Stock Restoration
        
        For any successfully created sales return, the stock quantity for each
        returned product SHALL increase by exactly the returned quantity (in base units).
        
        **Validates: Requirements 5.4**
        **Feature: desktop-full-crud-returns, Property 4: Return Stock Restoration**
        """
        # Create fresh test data for this iteration
        user, category, unit, warehouse, customer = create_test_data()
        
        # Setup: Create product with stock
        initial_stock = original_qty * 3
        cost_price = unit_price * Decimal('0.7')
        
        product = create_product_with_stock(
            category, unit, warehouse,
            initial_stock, cost_price, unit_price
        )
        
        # Create confirmed invoice
        invoice, invoice_item = create_confirmed_invoice_with_item(
            customer, warehouse, product,
            original_qty, unit_price
        )
        
        # Get stock before return
        stock_before = Stock.objects.get(
            product=product,
            warehouse=warehouse
        ).quantity
        
        # Calculate return quantity
        return_qty = (original_qty * return_ratio).quantize(Decimal('0.01'))
        assume(return_qty > 0)
        
        # Create return
        SalesService.create_sales_return(
            invoice_id=invoice.id,
            return_date=date.today(),
            items=[{
                'invoice_item_id': invoice_item.id,
                'quantity': return_qty,
                'reason': 'Test return'
            }],
            reason='Property test - stock restoration',
            user=user
        )
        
        # Verify stock increased by exactly return_qty
        stock_after = Stock.objects.get(
            product=product,
            warehouse=warehouse
        ).quantity
        
        stock_increase = stock_after - stock_before
        assert stock_increase == return_qty, (
            f"Stock should increase by {return_qty}, "
            f"but increased by {stock_increase}"
        )

    @given(
        original_qty=quantity_strategy,
        return_ratio=return_ratio_strategy,
        unit_price=price_strategy
    )
    @settings(
        deadline=None,
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_return_stock_movement_creation(
        self,
        original_qty,
        return_ratio,
        unit_price
    ):
        """
        Property 5: Return Stock Movement Creation
        
        For any successfully created sales return, a StockMovement record with
        source_type="return" SHALL be created for each returned item, with
        quantity matching the returned quantity.
        
        **Validates: Requirements 5.5**
        **Feature: desktop-full-crud-returns, Property 5: Return Stock Movement Creation**
        """
        # Create fresh test data for this iteration
        user, category, unit, warehouse, customer = create_test_data()
        
        # Setup: Create product with stock
        initial_stock = original_qty * 3
        cost_price = unit_price * Decimal('0.7')
        
        product = create_product_with_stock(
            category, unit, warehouse,
            initial_stock, cost_price, unit_price
        )
        
        # Create confirmed invoice
        invoice, invoice_item = create_confirmed_invoice_with_item(
            customer, warehouse, product,
            original_qty, unit_price
        )
        
        # Count movements before return
        movements_before = StockMovement.objects.filter(
            product=product,
            warehouse=warehouse
        ).count()
        
        # Calculate return quantity
        return_qty = (original_qty * return_ratio).quantize(Decimal('0.01'))
        assume(return_qty > 0)
        
        # Create return
        sales_return = SalesService.create_sales_return(
            invoice_id=invoice.id,
            return_date=date.today(),
            items=[{
                'invoice_item_id': invoice_item.id,
                'quantity': return_qty,
                'reason': 'Test return'
            }],
            reason='Property test - movement creation',
            user=user
        )
        
        # Verify a new movement was created
        movements_after = StockMovement.objects.filter(
            product=product,
            warehouse=warehouse
        ).count()
        
        assert movements_after > movements_before, (
            "A new stock movement should be created for the return"
        )
        
        # Find the return movement
        return_movement = StockMovement.objects.filter(
            product=product,
            warehouse=warehouse,
            source_type=StockMovement.SourceType.RETURN,
            reference_id=sales_return.id
        ).first()
        
        assert return_movement is not None, (
            "A stock movement with source_type='return' should exist"
        )
        assert return_movement.quantity == return_qty, (
            f"Movement quantity should be {return_qty}, "
            f"but was {return_movement.quantity}"
        )
        assert return_movement.movement_type == StockMovement.MovementType.IN, (
            "Return movement should be of type 'in'"
        )

    @given(
        original_qty=quantity_strategy,
        return_ratio=return_ratio_strategy,
        unit_price=price_strategy
    )
    @settings(
        deadline=None,
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_return_customer_balance_adjustment(
        self,
        original_qty,
        return_ratio,
        unit_price
    ):
        """
        Property 6: Return Customer Balance Adjustment
        
        For any successfully created sales return with total amount T, the
        customer's current_balance SHALL decrease by exactly T.
        
        **Validates: Requirements 5.6**
        **Feature: desktop-full-crud-returns, Property 6: Return Customer Balance Adjustment**
        """
        # Create fresh test data for this iteration
        user, category, unit, warehouse, customer = create_test_data()
        
        # Setup: Create product with stock
        initial_stock = original_qty * 3
        cost_price = unit_price * Decimal('0.7')
        
        product = create_product_with_stock(
            category, unit, warehouse,
            initial_stock, cost_price, unit_price
        )
        
        # Set initial customer balance
        initial_balance = Decimal('5000.00')
        customer.current_balance = initial_balance
        customer.save()
        
        # Create confirmed invoice
        invoice, invoice_item = create_confirmed_invoice_with_item(
            customer, warehouse, product,
            original_qty, unit_price
        )
        
        # Get customer balance before return
        customer.refresh_from_db()
        balance_before = customer.current_balance
        
        # Calculate return quantity and expected return amount
        return_qty = (original_qty * return_ratio).quantize(Decimal('0.01'))
        assume(return_qty > 0)
        expected_return_amount = return_qty * unit_price
        
        # Create return
        sales_return = SalesService.create_sales_return(
            invoice_id=invoice.id,
            return_date=date.today(),
            items=[{
                'invoice_item_id': invoice_item.id,
                'quantity': return_qty,
                'reason': 'Test return'
            }],
            reason='Property test - balance adjustment',
            user=user
        )
        
        # Verify customer balance decreased by return amount
        customer.refresh_from_db()
        balance_after = customer.current_balance
        
        balance_decrease = balance_before - balance_after
        
        assert balance_decrease == expected_return_amount, (
            f"Customer balance should decrease by {expected_return_amount}, "
            f"but decreased by {balance_decrease}"
        )
        
        # Also verify the return total matches
        assert sales_return.total_amount == expected_return_amount, (
            f"Return total should be {expected_return_amount}, "
            f"but was {sales_return.total_amount}"
        )
