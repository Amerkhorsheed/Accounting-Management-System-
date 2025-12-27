"""
Tests for Unit model.
"""
import pytest
from django.db import IntegrityError
from apps.inventory.models import Unit, Product, ProductUnit


@pytest.mark.django_db
class TestUnitModel:
    """Test suite for Unit model."""
    
    def test_create_unit(self):
        """Test creating a unit."""
        unit = Unit.objects.create(
            name='Kilogram',
            name_en='Kilogram',
            symbol='KG'
        )
        assert unit.name == 'Kilogram'
        assert unit.name_en == 'Kilogram'
        assert unit.symbol == 'KG'
    
    def test_unit_string_representation(self):
        """Test unit string representation."""
        unit = Unit.objects.create(name='Kilogram', symbol='KG')
        assert str(unit) == 'Kilogram (KG)'
    
    def test_unit_name_unique_constraint(self):
        """Test that unit name must be unique."""
        Unit.objects.create(name='Kilogram', symbol='KG')
        
        with pytest.raises(IntegrityError):
            Unit.objects.create(name='Kilogram', symbol='KG2')
    
    def test_unit_symbol_unique_constraint(self):
        """Test that unit symbol must be unique."""
        Unit.objects.create(name='Kilogram', symbol='KG')
        
        with pytest.raises(IntegrityError):
            Unit.objects.create(name='Kilogram2', symbol='KG')
    
    def test_unit_soft_delete_allows_duplicate_name(self):
        """Test that soft deleted units don't block new units with same name."""
        unit = Unit.objects.create(name='Kilogram', symbol='KG')
        unit.soft_delete()
        
        # Should be able to create new unit with same name after soft delete
        new_unit = Unit.objects.create(name='Kilogram', symbol='KG2')
        assert new_unit.name == 'Kilogram'
    
    def test_unit_ordering(self):
        """Test unit ordering by name."""
        unit_c = Unit.objects.create(name='C Unit', symbol='C')
        unit_a = Unit.objects.create(name='A Unit', symbol='A')
        unit_b = Unit.objects.create(name='B Unit', symbol='B')
        
        units = list(Unit.objects.all())
        assert units[0] == unit_a
        assert units[1] == unit_b
        assert units[2] == unit_c
    
    def test_unit_is_active(self):
        """Test unit is_active field."""
        unit = Unit.objects.create(name='Kilogram', symbol='KG', is_active=True)
        assert unit.is_active is True
    
    def test_unit_timestamps(self):
        """Test unit timestamps."""
        unit = Unit.objects.create(name='Kilogram', symbol='KG')
        assert unit.created_at is not None
        assert unit.updated_at is not None
