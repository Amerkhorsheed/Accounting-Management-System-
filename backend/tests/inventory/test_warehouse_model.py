"""
Tests for Warehouse model.
"""
import pytest
from apps.inventory.models import Warehouse
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestWarehouseModel:
    """Test suite for Warehouse model."""
    
    def test_create_warehouse(self, admin_user):
        """Test creating a warehouse."""
        warehouse = Warehouse.objects.create(
            name='Main Warehouse',
            code='WH001',
            manager=admin_user
        )
        assert warehouse.name == 'Main Warehouse'
        assert warehouse.code == 'WH001'
        assert warehouse.manager == admin_user
    
    def test_warehouse_string_representation(self, admin_user):
        """Test warehouse string representation."""
        warehouse = Warehouse.objects.create(
            name='Main Warehouse',
            code='WH001',
            manager=admin_user
        )
        assert str(warehouse) == 'Main Warehouse'
    
    def test_warehouse_default_flag(self, admin_user):
        """Test warehouse is_default flag."""
        warehouse = Warehouse.objects.create(
            name='Main Warehouse',
            code='WH001',
            is_default=True,
            manager=admin_user
        )
        assert warehouse.is_default is True
    
    def test_warehouse_only_one_default(self, admin_user, manager_user):
        """Test that only one warehouse can be default."""
        warehouse1 = Warehouse.objects.create(
            name='Warehouse 1',
            code='WH001',
            is_default=True,
            manager=admin_user
        )
        assert warehouse1.is_default is True
        
        warehouse2 = Warehouse.objects.create(
            name='Warehouse 2',
            code='WH002',
            is_default=True,
            manager=manager_user
        )
        
        # Refresh warehouse1 from database
        warehouse1.refresh_from_db()
        
        # warehouse1 should no longer be default
        assert warehouse1.is_default is False
        assert warehouse2.is_default is True
    
    def test_warehouse_address(self, admin_user):
        """Test warehouse address field."""
        warehouse = Warehouse.objects.create(
            name='Main Warehouse',
            code='WH001',
            address='123 Warehouse Street, Industrial Area',
            manager=admin_user
        )
        assert warehouse.address == '123 Warehouse Street, Industrial Area'
    
    def test_warehouse_code_unique(self, admin_user):
        """Test warehouse code uniqueness."""
        Warehouse.objects.create(
            name='Warehouse 1',
            code='WH001',
            manager=admin_user
        )
        
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            Warehouse.objects.create(
                name='Warehouse 2',
                code='WH001',
                manager=admin_user
            )
