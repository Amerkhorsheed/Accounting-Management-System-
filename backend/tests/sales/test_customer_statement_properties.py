"""
Property-based tests for Customer Statement Opening Balance.

Feature: reports-fixes
Tests Property 5 from the design document.
"""
import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from decimal import Decimal
from datetime import date, timedelta
import uuid

from apps.sales.models import (
    Customer, Invoice, InvoiceItem, Payment, SalesReturn, SalesReturnItem
)
from apps.sales.services import SalesService
from apps.inventory.models import (
    Product, Category, Unit, Warehouse, Stock
)
from django.contrib.auth import get_user_model

User = get_user_model()


# ============================================================================
# Strategies for test data generation
# ============================================================================

# Amount strategy - positive decimals with reasonable bounds
amount_strategy = st.decimals(
    min_value=Decimal('10.00'),
    max_value=Decimal('1000.00'),
    places=2
).filter(lambda x: x > 0)

# Opening balance strategy - can be positive or negative
opening_balance_strategy = st.decimals(
    min_value=Decimal('-500.00'),
    max_value=Decimal('500.00'),
    places=2
)

# Number of transactions strategy
num_transactions_strategy = st.integers(min_value=1, max_value=5)


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
        current_balance=Decimal('0.00'),
        opening_balance=Decimal('0.00')
    )
    
    return user, category, unit, warehouse, customer


def create_product_with_stock(category, unit, warehouse, quantity):
    """Helper to create a product with initial stock."""
    unique_id = uuid.uuid4().hex[:12]
    product = Product.objects.create(
        name=f'Test Product {unique_id}',
        barcode=f'TBAR{unique_id}',
        code=f'TPRD{unique_id}',
        category=category,
        unit=unit,
        cost_price=Decimal('50.00'),
        sale_price=Decimal('100.00'),
        track_stock=True
    )
    Stock.objects.create(
        product=product,
        warehouse=warehouse,
        quantity=quantity
    )
    return product


def create_confirmed_invoice(customer, warehouse, product, amount, invoice_date, user):
    """Helper to create a confirmed invoice with specified total amount."""
    unique_id = uuid.uuid4().hex[:8]
    
    # Calculate quantity to achieve desired amount
    unit_price = Decimal('100.00')
    quantity = (amount / unit_price).quantize(Decimal('0.01'))
    if quantity < Decimal('0.01'):
        quantity = Decimal('0.01')
    
    invoice = Invoice.objects.create(
        invoice_number=f'INV-{unique_id}',
        customer=customer,
        warehouse=warehouse,
        invoice_date=invoice_date,
        status=Invoice.Status.CONFIRMED,
        invoice_type=Invoice.InvoiceType.CREDIT,
        subtotal=quantity * unit_price,
        total_amount=quantity * unit_price
    )
    InvoiceItem.objects.create(
        invoice=invoice,
        product=product,
        quantity=quantity,
        unit_price=unit_price,
        cost_price=product.cost_price
    )
    return invoice


def create_payment(customer, amount, payment_date, user):
    """Helper to create a payment."""
    unique_id = uuid.uuid4().hex[:8]
    payment = Payment.objects.create(
        payment_number=f'PAY-{unique_id}',
        customer=customer,
        payment_date=payment_date,
        amount=amount,
        payment_method='cash',
        received_by=user
    )
    return payment


def create_sales_return(invoice, amount, return_date, user):
    """Helper to create a sales return."""
    unique_id = uuid.uuid4().hex[:8]
    sales_return = SalesReturn.objects.create(
        return_number=f'RET-{unique_id}',
        original_invoice=invoice,
        return_date=return_date,
        total_amount=amount,
        reason='Test return'
    )
    return sales_return


# ============================================================================
# Property Tests
# ============================================================================

@pytest.mark.django_db(transaction=True)
class TestCustomerStatementOpeningBalanceProperties:
    """
    Property-based tests for customer statement opening balance calculation.
    
    Feature: reports-fixes
    """

    @given(
        customer_opening_balance=opening_balance_strategy,
        invoice_amount=amount_strategy,
        payment_amount=amount_strategy
    )
    @settings(
        deadline=None,
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_opening_balance_includes_transactions_before_start_date(
        self,
        customer_opening_balance,
        invoice_amount,
        payment_amount
    ):
        """
        Property 5: Customer Statement Opening Balance Calculation
        
        For any customer statement with a date range filter, the opening_balance
        SHALL equal the customer's opening_balance plus the sum of all debits
        minus credits from transactions before the start_date.
        
        **Validates: Requirements 6.1, 6.2**
        **Feature: reports-fixes, Property 5: Customer Statement Opening Balance Calculation**
        """
        # Create fresh test data for this iteration
        user, category, unit, warehouse, customer = create_test_data()
        
        # Set customer opening balance
        customer.opening_balance = customer_opening_balance
        customer.save()
        
        # Create product with enough stock
        product = create_product_with_stock(category, unit, warehouse, Decimal('10000.00'))
        
        # Define dates
        today = date.today()
        before_period = today - timedelta(days=30)  # Transaction before period
        period_start = today - timedelta(days=15)   # Start of filter period
        
        # Create invoice BEFORE the period start (should be included in opening balance)
        invoice_before = create_confirmed_invoice(
            customer, warehouse, product, invoice_amount, before_period, user
        )
        
        # Create payment BEFORE the period start (should be included in opening balance)
        payment_before = create_payment(customer, payment_amount, before_period, user)
        
        # Calculate expected opening balance
        # Opening balance = customer.opening_balance + invoices_before - payments_before
        expected_opening_balance = (
            customer_opening_balance + 
            invoice_before.total_amount - 
            payment_before.amount
        )
        
        # Get customer statement with date filter starting from period_start
        statement = SalesService.get_customer_statement(
            customer_id=customer.id,
            start_date=period_start,
            end_date=today
        )
        
        # Verify opening balance includes transactions before start_date
        assert statement['opening_balance'] == expected_opening_balance, (
            f"Opening balance should be {expected_opening_balance}, "
            f"but was {statement['opening_balance']}. "
            f"Customer opening: {customer_opening_balance}, "
            f"Invoice before: {invoice_before.total_amount}, "
            f"Payment before: {payment_before.amount}"
        )

    @given(
        customer_opening_balance=opening_balance_strategy,
        invoice_amount_before=amount_strategy,
        invoice_amount_during=amount_strategy,
        payment_amount_before=amount_strategy
    )
    @settings(
        deadline=None,
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_opening_balance_excludes_transactions_during_period(
        self,
        customer_opening_balance,
        invoice_amount_before,
        invoice_amount_during,
        payment_amount_before
    ):
        """
        Property 5: Customer Statement Opening Balance Calculation (continued)
        
        For any customer statement with a date range filter, the opening_balance
        SHALL NOT include transactions that occur on or after the start_date.
        
        **Validates: Requirements 6.1, 6.2**
        **Feature: reports-fixes, Property 5: Customer Statement Opening Balance Calculation**
        """
        # Create fresh test data for this iteration
        user, category, unit, warehouse, customer = create_test_data()
        
        # Set customer opening balance
        customer.opening_balance = customer_opening_balance
        customer.save()
        
        # Create product with enough stock
        product = create_product_with_stock(category, unit, warehouse, Decimal('10000.00'))
        
        # Define dates
        today = date.today()
        before_period = today - timedelta(days=30)  # Transaction before period
        period_start = today - timedelta(days=15)   # Start of filter period
        during_period = today - timedelta(days=10)  # Transaction during period
        
        # Create invoice BEFORE the period start
        invoice_before = create_confirmed_invoice(
            customer, warehouse, product, invoice_amount_before, before_period, user
        )
        
        # Create payment BEFORE the period start
        payment_before = create_payment(customer, payment_amount_before, before_period, user)
        
        # Create invoice DURING the period (should NOT be in opening balance)
        invoice_during = create_confirmed_invoice(
            customer, warehouse, product, invoice_amount_during, during_period, user
        )
        
        # Calculate expected opening balance (only transactions before period)
        expected_opening_balance = (
            customer_opening_balance + 
            invoice_before.total_amount - 
            payment_before.amount
        )
        
        # Get customer statement with date filter
        statement = SalesService.get_customer_statement(
            customer_id=customer.id,
            start_date=period_start,
            end_date=today
        )
        
        # Verify opening balance does NOT include transactions during period
        assert statement['opening_balance'] == expected_opening_balance, (
            f"Opening balance should be {expected_opening_balance} "
            f"(excluding transactions during period), "
            f"but was {statement['opening_balance']}"
        )
        
        # Verify the invoice during period appears in transactions list
        transaction_refs = [t['reference'] for t in statement['transactions']]
        assert invoice_during.invoice_number in transaction_refs, (
            f"Invoice during period ({invoice_during.invoice_number}) "
            f"should appear in transactions list"
        )

    @given(
        customer_opening_balance=opening_balance_strategy,
        invoice_amount=amount_strategy
    )
    @settings(
        deadline=None,
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_opening_balance_with_no_filter_equals_customer_opening_balance(
        self,
        customer_opening_balance,
        invoice_amount
    ):
        """
        Property 5: Customer Statement Opening Balance Calculation (edge case)
        
        For any customer statement WITHOUT a date range filter, the opening_balance
        SHALL equal the customer's opening_balance (no transactions to add).
        
        **Validates: Requirements 6.1, 6.2**
        **Feature: reports-fixes, Property 5: Customer Statement Opening Balance Calculation**
        """
        # Create fresh test data for this iteration
        user, category, unit, warehouse, customer = create_test_data()
        
        # Set customer opening balance
        customer.opening_balance = customer_opening_balance
        customer.save()
        
        # Create product with enough stock
        product = create_product_with_stock(category, unit, warehouse, Decimal('10000.00'))
        
        # Create an invoice (should appear in transactions, not affect opening balance)
        today = date.today()
        invoice = create_confirmed_invoice(
            customer, warehouse, product, invoice_amount, today, user
        )
        
        # Get customer statement WITHOUT date filter
        statement = SalesService.get_customer_statement(
            customer_id=customer.id,
            start_date=None,
            end_date=None
        )
        
        # Verify opening balance equals customer's opening_balance
        assert statement['opening_balance'] == customer_opening_balance, (
            f"Opening balance without filter should be {customer_opening_balance}, "
            f"but was {statement['opening_balance']}"
        )
