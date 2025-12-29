"""
Property-based tests for Customer Deletion Protection.

Feature: desktop-full-crud-returns
Tests Property 1 (Customer) from the design document.
"""
import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from decimal import Decimal
from datetime import date
import uuid

from apps.sales.models import Customer, Invoice, InvoiceItem
from apps.inventory.models import Product, Category, Unit, Warehouse, Stock
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()


# ============================================================================
# Strategies for test data generation
# ============================================================================

# Invoice total strategy - positive decimals for invoice amounts
invoice_total_strategy = st.decimals(
    min_value=Decimal('10.00'),
    max_value=Decimal('10000.00'),
    places=2
).filter(lambda x: x > 0)

# Paid amount ratio - between 0 and 0.99 (partial payment)
partial_payment_ratio_strategy = st.decimals(
    min_value=Decimal('0.00'),
    max_value=Decimal('0.99'),
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
        is_active=True,
        role=User.Role.ADMIN
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


def create_product(category, unit):
    """Helper to create a product."""
    unique_id = uuid.uuid4().hex[:12]
    return Product.objects.create(
        name=f'Test Product {unique_id}',
        barcode=f'TBAR{unique_id}',
        code=f'TPRD{unique_id}',
        category=category,
        unit=unit,
        cost_price=Decimal('50.00'),
        sale_price=Decimal('100.00'),
        track_stock=True
    )


def create_invoice_with_outstanding_balance(customer, warehouse, product, total_amount, paid_amount):
    """Helper to create an invoice with outstanding balance."""
    unique_id = uuid.uuid4().hex[:8]
    invoice = Invoice.objects.create(
        invoice_number=f'INV-{unique_id}',
        customer=customer,
        warehouse=warehouse,
        invoice_date=date.today(),
        status=Invoice.Status.CONFIRMED,
        total_amount=total_amount,
        paid_amount=paid_amount
    )
    # Create an invoice item
    InvoiceItem.objects.create(
        invoice=invoice,
        product=product,
        quantity=Decimal('1.00'),
        unit_price=total_amount,
        cost_price=product.cost_price
    )
    return invoice


# ============================================================================
# Property Tests
# ============================================================================

@pytest.mark.django_db(transaction=True)
class TestCustomerDeletionProtectionProperties:
    """
    Property-based tests for customer deletion protection.
    
    Feature: desktop-full-crud-returns
    Property 1: Entity Deletion Protection (Customer)
    """

    @given(
        invoice_total=invoice_total_strategy,
        payment_ratio=partial_payment_ratio_strategy
    )
    @settings(
        deadline=None,
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_customer_with_outstanding_invoices_cannot_be_deleted(
        self,
        invoice_total,
        payment_ratio
    ):
        """
        Property 1: Entity Deletion Protection (Customer)
        
        For any customer that has outstanding invoices (non-cancelled invoices with
        remaining balance > 0), attempting to delete the customer SHALL result in
        a rejection with an appropriate error message, and the customer SHALL
        remain unchanged in the database.
        
        **Validates: Requirements 1.5**
        **Feature: desktop-full-crud-returns, Property 1: Entity Deletion Protection (Customer)**
        """
        # Create fresh test data for this iteration
        user, category, unit, warehouse, customer = create_test_data()
        
        # Create product for invoice
        product = create_product(category, unit)
        
        # Calculate paid amount (partial payment)
        paid_amount = (invoice_total * payment_ratio).quantize(Decimal('0.01'))
        
        # Ensure there's an outstanding balance
        assume(paid_amount < invoice_total)
        
        # Create invoice with outstanding balance
        invoice = create_invoice_with_outstanding_balance(
            customer, warehouse, product,
            invoice_total, paid_amount
        )
        
        # Verify invoice has outstanding balance
        assert invoice.total_amount > invoice.paid_amount
        
        # Store customer ID for verification
        customer_id = customer.id
        customer_code = customer.code
        
        # Create authenticated API client
        client = APIClient()
        client.force_authenticate(user=user)
        
        # Attempt to delete customer via API
        response = client.delete(f'/api/v1/sales/customers/{customer_id}/')
        
        # Verify deletion was rejected
        assert response.status_code == status.HTTP_400_BAD_REQUEST, (
            f"Expected 400 Bad Request, got {response.status_code}"
        )
        
        # Verify error response contains deletion protection code
        assert response.data.get('code') == 'DELETION_PROTECTED', (
            f"Expected error code 'DELETION_PROTECTED', got {response.data.get('code')}"
        )
        
        # Verify customer still exists in database
        assert Customer.objects.filter(id=customer_id).exists(), (
            "Customer should still exist after failed deletion attempt"
        )
        
        # Verify customer data is unchanged
        customer.refresh_from_db()
        assert customer.code == customer_code, (
            "Customer data should be unchanged after failed deletion"
        )
        assert customer.is_deleted is False, (
            "Customer should not be marked as deleted"
        )

    @given(
        invoice_total=invoice_total_strategy
    )
    @settings(
        deadline=None,
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_customer_with_fully_paid_invoices_can_be_deleted(
        self,
        invoice_total
    ):
        """
        Complementary property: Customer with fully paid invoices CAN be deleted.
        
        For any customer that has only fully paid invoices (paid_amount >= total_amount),
        deletion SHALL succeed.
        
        **Validates: Requirements 1.4**
        **Feature: desktop-full-crud-returns, Property 1: Entity Deletion Protection (Customer)**
        """
        # Create fresh test data for this iteration
        user, category, unit, warehouse, customer = create_test_data()
        
        # Create product for invoice
        product = create_product(category, unit)
        
        # Create fully paid invoice
        invoice = create_invoice_with_outstanding_balance(
            customer, warehouse, product,
            invoice_total, invoice_total  # paid_amount == total_amount
        )
        
        # Verify invoice is fully paid
        assert invoice.total_amount == invoice.paid_amount
        
        # Store customer ID for verification
        customer_id = customer.id
        
        # Create authenticated API client
        client = APIClient()
        client.force_authenticate(user=user)
        
        # Attempt to delete customer via API
        response = client.delete(f'/api/v1/sales/customers/{customer_id}/')
        
        # Verify deletion succeeded
        assert response.status_code == status.HTTP_204_NO_CONTENT, (
            f"Expected 204 No Content, got {response.status_code}. "
            f"Response: {response.data if hasattr(response, 'data') else 'No data'}"
        )
        
        # Verify customer is soft-deleted
        customer.refresh_from_db()
        assert customer.is_deleted is True, (
            "Customer should be marked as deleted after successful deletion"
        )

    @given(
        invoice_total=invoice_total_strategy
    )
    @settings(
        deadline=None,
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    def test_customer_with_cancelled_invoices_can_be_deleted(
        self,
        invoice_total
    ):
        """
        Complementary property: Customer with only cancelled invoices CAN be deleted.
        
        For any customer that has only cancelled invoices, deletion SHALL succeed
        regardless of the invoice amounts.
        
        **Validates: Requirements 1.4, 1.5**
        **Feature: desktop-full-crud-returns, Property 1: Entity Deletion Protection (Customer)**
        """
        # Create fresh test data for this iteration
        user, category, unit, warehouse, customer = create_test_data()
        
        # Create product for invoice
        product = create_product(category, unit)
        
        # Create cancelled invoice with outstanding balance
        unique_id = uuid.uuid4().hex[:8]
        invoice = Invoice.objects.create(
            invoice_number=f'INV-{unique_id}',
            customer=customer,
            warehouse=warehouse,
            invoice_date=date.today(),
            status=Invoice.Status.CANCELLED,  # Cancelled status
            total_amount=invoice_total,
            paid_amount=Decimal('0.00')  # Unpaid but cancelled
        )
        
        # Verify invoice is cancelled
        assert invoice.status == Invoice.Status.CANCELLED
        
        # Store customer ID for verification
        customer_id = customer.id
        
        # Create authenticated API client
        client = APIClient()
        client.force_authenticate(user=user)
        
        # Attempt to delete customer via API
        response = client.delete(f'/api/v1/sales/customers/{customer_id}/')
        
        # Verify deletion succeeded
        assert response.status_code == status.HTTP_204_NO_CONTENT, (
            f"Expected 204 No Content, got {response.status_code}. "
            f"Response: {response.data if hasattr(response, 'data') else 'No data'}"
        )
        
        # Verify customer is soft-deleted
        customer.refresh_from_db()
        assert customer.is_deleted is True, (
            "Customer should be marked as deleted after successful deletion"
        )
