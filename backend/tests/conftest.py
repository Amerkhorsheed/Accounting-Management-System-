"""
Shared test fixtures and utilities for all tests.
"""
import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.inventory.models import Category, Unit, Product, Warehouse, Stock
from apps.sales.models import Customer
from apps.purchases.models import Supplier
from apps.expenses.models import ExpenseCategory

User = get_user_model()


# ============================================================================
# User Fixtures
# ============================================================================

@pytest.fixture
def admin_user(db):
    """Create an admin user."""
    return User.objects.create_user(
        username='admin_test',
        password='admin123',
        email='admin@test.com',
        role=User.Role.ADMIN,
        is_staff=True,
        is_superuser=True,
        is_active=True
    )


@pytest.fixture
def manager_user(db):
    """Create a manager user."""
    return User.objects.create_user(
        username='manager_test',
        password='manager123',
        email='manager@test.com',
        role=User.Role.MANAGER,
        is_active=True
    )


@pytest.fixture
def accountant_user(db):
    """Create an accountant user."""
    return User.objects.create_user(
        username='accountant_test',
        password='accountant123',
        email='accountant@test.com',
        role=User.Role.ACCOUNTANT,
        is_active=True
    )


@pytest.fixture
def salesperson_user(db):
    """Create a salesperson user."""
    return User.objects.create_user(
        username='sales_test',
        password='sales123',
        email='sales@test.com',
        role=User.Role.SALESPERSON,
        is_active=True
    )


@pytest.fixture
def warehouse_user(db):
    """Create a warehouse user."""
    return User.objects.create_user(
        username='warehouse_test',
        password='warehouse123',
        email='warehouse@test.com',
        role=User.Role.WAREHOUSE,
        is_active=True
    )


@pytest.fixture
def viewer_user(db):
    """Create a viewer user."""
    return User.objects.create_user(
        username='viewer_test',
        password='viewer123',
        email='viewer@test.com',
        role=User.Role.VIEWER,
        is_active=True
    )


# ============================================================================
# API Client Fixtures
# ============================================================================

@pytest.fixture
def api_client():
    """Create an unauthenticated API client."""
    return APIClient()


@pytest.fixture
def admin_client(admin_user):
    """Create an authenticated API client with admin user."""
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client


@pytest.fixture
def manager_client(manager_user):
    """Create an authenticated API client with manager user."""
    client = APIClient()
    client.force_authenticate(user=manager_user)
    return client


@pytest.fixture
def accountant_client(accountant_user):
    """Create an authenticated API client with accountant user."""
    client = APIClient()
    client.force_authenticate(user=accountant_user)
    return client


@pytest.fixture
def salesperson_client(salesperson_user):
    """Create an authenticated API client with salesperson user."""
    client = APIClient()
    client.force_authenticate(user=salesperson_user)
    return client


@pytest.fixture
def warehouse_client(warehouse_user):
    """Create an authenticated API client with warehouse user."""
    client = APIClient()
    client.force_authenticate(user=warehouse_user)
    return client


# ============================================================================
# Inventory Fixtures
# ============================================================================

@pytest.fixture
def category(db):
    """Create a test category."""
    return Category.objects.create(
        name='Test Category',
        name_en='Test Category EN',
        description='Test category description'
    )


@pytest.fixture
def parent_category(db):
    """Create a parent category."""
    return Category.objects.create(
        name='Parent Category',
        description='Parent category'
    )


@pytest.fixture
def child_category(db, parent_category):
    """Create a child category."""
    return Category.objects.create(
        name='Child Category',
        parent=parent_category,
        description='Child category'
    )


@pytest.fixture
def unit(db):
    """Create a test unit."""
    return Unit.objects.create(
        name='Piece',
        name_en='Piece',
        symbol='PC'
    )


@pytest.fixture
def unit_kg(db):
    """Create a kilogram unit."""
    return Unit.objects.create(
        name='كيلوجرام',
        name_en='Kilogram',
        symbol='KG'
    )


@pytest.fixture
def unit_box(db):
    """Create a box unit."""
    return Unit.objects.create(
        name='صندوق',
        name_en='Box',
        symbol='BOX'
    )


@pytest.fixture
def warehouse(db, admin_user):
    """Create a test warehouse."""
    return Warehouse.objects.create(
        name='Main Warehouse',
        code='WH001',
        address='123 Test Street',
        is_default=True,
        manager=admin_user
    )


@pytest.fixture
def warehouse_secondary(db, manager_user):
    """Create a secondary warehouse."""
    return Warehouse.objects.create(
        name='Secondary Warehouse',
        code='WH002',
        address='456 Test Avenue',
        is_default=False,
        manager=manager_user
    )


@pytest.fixture
def product(db, category, unit):
    """Create a test product."""
    return Product.objects.create(
        name='Test Product',
        name_en='Test Product EN',
        category=category,
        unit=unit,
        cost_price=Decimal('100.00'),
        sale_price=Decimal('150.00'),
        wholesale_price=Decimal('130.00'),
        minimum_price=Decimal('120.00'),
        is_taxable=True,
        tax_rate=Decimal('15.00'),
        track_stock=True,
        minimum_stock=Decimal('10.00'),
        reorder_point=Decimal('20.00')
    )


@pytest.fixture
def product_service(db, category, unit):
    """Create a service product."""
    return Product.objects.create(
        name='Test Service',
        category=category,
        unit=unit,
        product_type=Product.ProductType.SERVICE,
        cost_price=Decimal('50.00'),
        sale_price=Decimal('100.00'),
        track_stock=False
    )


# ============================================================================
# Sales Fixtures
# ============================================================================

@pytest.fixture
def customer(db, salesperson_user):
    """Create a test customer."""
    return Customer.objects.create(
        name='Test Customer',
        name_en='Test Customer EN',
        customer_type=Customer.CustomerType.INDIVIDUAL,
        phone='1234567890',
        email='customer@test.com',
        credit_limit=Decimal('10000.00'),
        payment_terms=30,
        discount_percent=Decimal('5.00'),
        salesperson=salesperson_user
    )


@pytest.fixture
def customer_company(db):
    """Create a company customer."""
    return Customer.objects.create(
        name='Test Company',
        customer_type=Customer.CustomerType.COMPANY,
        tax_number='123456789',
        commercial_register='CR123456',
        credit_limit=Decimal('50000.00'),
        payment_terms=60
    )


# ============================================================================
# Purchases Fixtures
# ============================================================================

@pytest.fixture
def supplier(db):
    """Create a test supplier."""
    return Supplier.objects.create(
        name='Test Supplier',
        name_en='Test Supplier EN',
        phone='9876543210',
        email='supplier@test.com',
        payment_terms=30,
        credit_limit=Decimal('20000.00')
    )


# ============================================================================
# Expenses Fixtures
# ============================================================================

@pytest.fixture
def expense_category(db):
    """Create a test expense category."""
    return ExpenseCategory.objects.create(
        name='Office Supplies',
        description='Office supplies and stationery'
    )


# ============================================================================
# Date Fixtures
# ============================================================================

@pytest.fixture
def today():
    """Return today's date."""
    return date.today()


@pytest.fixture
def yesterday():
    """Return yesterday's date."""
    return date.today() - timedelta(days=1)


@pytest.fixture
def tomorrow():
    """Return tomorrow's date."""
    return date.today() + timedelta(days=1)


@pytest.fixture
def last_week():
    """Return date from last week."""
    return date.today() - timedelta(days=7)


@pytest.fixture
def next_week():
    """Return date for next week."""
    return date.today() + timedelta(days=7)
