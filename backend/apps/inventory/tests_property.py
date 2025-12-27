import pytest
from hypothesis import given, strategies as st, settings
from decimal import Decimal
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from .models import Unit, Product, ProductUnit, Category
from django.contrib.auth import get_user_model

User = get_user_model()

# Strategies for test data
name_strategy = st.text(
    min_size=1, 
    max_size=50, 
    alphabet=st.characters(blacklist_categories=('Cs',), min_codepoint=0x0020, max_codepoint=0x007E) | st.just(' ')
).map(lambda x: x.strip()).filter(lambda x: len(x) > 0)

symbol_strategy = st.text(
    min_size=1, 
    max_size=10, 
    alphabet=st.characters(blacklist_categories=('Cs',), min_codepoint=0x0020, max_codepoint=0x007E) | st.just(' ')
).map(lambda x: x.strip()).filter(lambda x: len(x) > 0)

# Decimal strategies
quantity_strategy = st.decimals(min_value=Decimal('0.0001'), max_value=Decimal('1000000.0000'), places=4)
factor_strategy = st.decimals(min_value=Decimal('0.0001'), max_value=Decimal('1000.0000'), places=4)

@pytest.fixture
def auth_client():
    """Create authenticated API client for testing."""
    client = APIClient()
    user = User.objects.create_user(
        username='testuser_prop', 
        password='password123', 
        full_name='Test User',
        is_active=True
    )
    client.force_authenticate(user=user)
    return client, user


@pytest.fixture
def setup_data():
    """Setup test data for unit tests."""
    category = Category.objects.create(name='Test Category')
    base_unit = Unit.objects.create(name='Base Unit', symbol='BU')
    return category, base_unit


@pytest.mark.django_db
class TestUnitsProperty:
    """Property-based tests for Unit CRUD operations."""

    @given(q=quantity_strategy, f=factor_strategy)
    @settings(deadline=None, max_examples=50)
    def test_quantity_conversion_correctness(self, setup_data, q, f):
        """
        Property 7: Quantity Conversion Correctness
        
        For any ProductUnit with conversion_factor `f` and any quantity `q`,
        converting `q` units to base units SHALL equal `q * f`, and converting
        `q * f` base units back SHALL equal `q`.
        
        **Validates: Requirements 2.5**
        **Feature: units-management, Property 7: Quantity Conversion Correctness**
        """
        category, base_unit = setup_data
        product = Product.objects.create(
            name=f'Test Product {f}',
            category=category,
            unit=base_unit
        )
        
        other_unit = Unit.objects.create(name=f'Other Unit {f}', symbol=f'OU{f}'[:10])
        product_unit = ProductUnit.objects.create(
            product=product,
            unit=other_unit,
            conversion_factor=f
        )
        
        # Convert to base and back
        base_q = product_unit.convert_to_base(q)
        back_q = product_unit.convert_from_base(base_q)
        
        # Check if we got back the same quantity (allowing for small precision errors)
        assert abs(back_q - q) < Decimal('0.0001')

    @given(name=name_strategy, symbol=symbol_strategy)
    @settings(deadline=None, max_examples=20)
    def test_unit_crud_round_trip(self, auth_client, name, symbol):
        """
        Property 1: Unit CRUD Round-Trip
        
        For any valid unit data (name, symbol, name_en), creating a unit and then
        retrieving it SHALL return the same data that was submitted.
        
        **Validates: Requirements 1.1, 1.2, 1.3**
        **Feature: units-management, Property 1: Unit CRUD Round-Trip**
        """
        client, user = auth_client
        
        # Create
        url = reverse('unit-list')
        data = {'name': name, 'symbol': symbol}
        response = client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED, response.data
        unit_id = response.data['id']
        
        # Retrieve
        detail_url = reverse('unit-detail', args=[unit_id])
        response = client.get(detail_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == name
        assert response.data['symbol'] == symbol
        
        # Update
        new_name = (name[:40] + "_updated")[:50]
        response = client.patch(detail_url, {'name': new_name})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == new_name
        
        # Delete
        response = client.delete(detail_url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify deletion
        assert not Unit.objects.filter(id=unit_id, is_deleted=False).exists()

    @given(name=name_strategy, symbol=symbol_strategy)
    @settings(deadline=None, max_examples=20)
    def test_unit_uniqueness(self, auth_client, name, symbol):
        """
        Property 2: Unit Name and Symbol Uniqueness
        
        For any two units in the system, if both are not deleted, their names
        SHALL be different AND their symbols SHALL be different.
        
        **Validates: Requirements 1.6**
        **Feature: units-management, Property 2: Unit Name and Symbol Uniqueness**
        """
        client, user = auth_client
        
        # Create first unit directly in DB
        Unit.objects.create(name=name, symbol=symbol)
        
        url = reverse('unit-list')
        # Try same name
        response1 = client.post(url, {'name': name, 'symbol': symbol + "_x"})
        assert response1.status_code == status.HTTP_400_BAD_REQUEST
        
        # Try same symbol
        response2 = client.post(url, {'name': name + "_x", 'symbol': symbol})
        assert response2.status_code == status.HTTP_400_BAD_REQUEST

    def test_unit_deletion_protection(self, auth_client, setup_data):
        """
        Property 3: Unit Deletion Protection
        
        For any unit that is associated with at least one ProductUnit, attempting
        to delete that unit SHALL fail with an error.
        
        **Validates: Requirements 1.4**
        **Feature: units-management, Property 3: Unit Deletion Protection**
        """
        client, user = auth_client
        category, base_unit = setup_data
        
        unit = Unit.objects.create(name='Protected Unit', symbol='PROT')
        product = Product.objects.create(
            name='Linked Product',
            category=category,
            unit=base_unit
        )
        
        # Also link via ProductUnit
        ProductUnit.objects.create(
            product=product,
            unit=unit,
            conversion_factor=Decimal('1.0')
        )
        
        url = reverse('unit-detail', args=[unit.id])
        response = client.delete(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'code' in response.data and response.data['code'] == 'UNIT_IN_USE'

    def test_unused_unit_deletion(self, auth_client):
        """
        Property 4: Unused Unit Deletion
        
        For any unit that is not associated with any ProductUnit, deleting that
        unit SHALL succeed and the unit SHALL no longer be retrievable.
        
        **Validates: Requirements 1.5**
        **Feature: units-management, Property 4: Unused Unit Deletion**
        """
        client, user = auth_client
        
        unit = Unit.objects.create(name='Unused Unit', symbol='UNUSD')
        url = reverse('unit-detail', args=[unit.id])
        
        response = client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Unit.objects.filter(id=unit.id, is_deleted=False).exists()
