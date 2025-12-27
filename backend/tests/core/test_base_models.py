"""
Tests for Core base models.
"""
import pytest
from datetime import datetime
from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.core.models import TimeStampedModel, SoftDeleteModel, ActiveModel, AuditModel, BaseModel
from apps.inventory.models import Category  # Using Category as a concrete BaseModel example

User = get_user_model()


@pytest.mark.django_db
class TestTimeStampedModel:
    """Test suite for TimeStampedModel."""
    
    def test_created_at_auto_set(self):
        """Test that created_at is automatically set."""
        category = Category.objects.create(name='Test Category')
        assert category.created_at is not None
        assert isinstance(category.created_at, datetime)
    
    def test_updated_at_auto_set(self):
        """Test that updated_at is automatically set."""
        category = Category.objects.create(name='Test Category')
        assert category.updated_at is not None
        assert isinstance(category.updated_at, datetime)
    
    def test_updated_at_auto_updates(self):
        """Test that updated_at is automatically updated on save."""
        category = Category.objects.create(name='Test Category')
        original_updated_at = category.updated_at
        
        # Wait a moment and update
        category.name = 'Updated Category'
        category.save()
        
        assert category.updated_at >= original_updated_at
    
    def test_created_at_not_updated(self):
        """Test that created_at doesn't change on update."""
        category = Category.objects.create(name='Test Category')
        original_created_at = category.created_at
        
        category.name = 'Updated Category'
        category.save()
        
        assert category.created_at == original_created_at


@pytest.mark.django_db
class TestSoftDeleteModel:
    """Test suite for SoftDeleteModel."""
    
    def test_is_deleted_default_false(self):
        """Test that is_deleted defaults to False."""
        category = Category.objects.create(name='Test Category')
        assert category.is_deleted is False
    
    def test_soft_delete_method(self, admin_user):
        """Test soft_delete method."""
        category = Category.objects.create(name='Test Category')
        category.soft_delete(user=admin_user)
        
        assert category.is_deleted is True
        assert category.deleted_at is not None
        assert category.deleted_by == admin_user
    
    def test_soft_delete_without_user(self):
        """Test soft_delete without user."""
        category = Category.objects.create(name='Test Category')
        category.soft_delete()
        
        assert category.is_deleted is True
        assert category.deleted_at is not None
        assert category.deleted_by is None
    
    def test_restore_method(self, admin_user):
        """Test restore method."""
        category = Category.objects.create(name='Test Category')
        category.soft_delete(user=admin_user)
        category.restore()
        
        assert category.is_deleted is False
        assert category.deleted_at is None
        assert category.deleted_by is None


@pytest.mark.django_db
class TestActiveModel:
    """Test suite for ActiveModel."""
    
    def test_is_active_default_true(self):
        """Test that is_active defaults to True."""
        category = Category.objects.create(name='Test Category')
        assert category.is_active is True
    
    def test_is_active_can_be_false(self):
        """Test that is_active can be set to False."""
        category = Category.objects.create(name='Test Category', is_active=False)
        assert category.is_active is False


@pytest.mark.django_db
class TestAuditModel:
    """Test suite for AuditModel."""
    
    def test_created_by_can_be_set(self, admin_user):
        """Test that created_by can be set."""
        category = Category.objects.create(
            name='Test Category',
            created_by=admin_user
        )
        assert category.created_by == admin_user
    
    def test_updated_by_can_be_set(self, admin_user, manager_user):
        """Test that updated_by can be set."""
        category = Category.objects.create(
            name='Test Category',
            created_by=admin_user
        )
        category.name = 'Updated'
        category.updated_by = manager_user
        category.save()
        
        assert category.updated_by == manager_user
        assert category.created_by == admin_user


@pytest.mark.django_db
class TestBaseModel:
    """Test suite for BaseModel (combination of all)."""
    
    def test_base_model_has_all_fields(self, admin_user):
        """Test that BaseModel has all combined fields."""
        category = Category.objects.create(
            name='Test Category',
            created_by=admin_user
        )
        
        # TimeStampedModel fields
        assert hasattr(category, 'created_at')
        assert hasattr(category, 'updated_at')
        
        # SoftDeleteModel fields
        assert hasattr(category, 'is_deleted')
        assert hasattr(category, 'deleted_at')
        assert hasattr(category, 'deleted_by')
        
        # ActiveModel fields
        assert hasattr(category, 'is_active')
        
        # AuditModel fields
        assert hasattr(category, 'created_by')
        assert hasattr(category, 'updated_by')
    
    def test_base_model_includes_all_fields(self):
        """Test that BaseModel includes all expected fields."""
        cat = Category.objects.create(name='Test Category')
        
        # BaseModel should include TimeStamped, SoftDelete, Active, and Audit fields
        assert hasattr(cat, 'created_at')
        assert hasattr(cat, 'updated_at')
        assert hasattr(cat, 'is_deleted')
        assert hasattr(cat, 'deleted_at')
        assert hasattr(cat, 'deleted_by')
        assert hasattr(cat, 'is_active')
        assert hasattr(cat, 'created_by')
        assert hasattr(cat, 'updated_by')
