"""
Tests for Category model.
"""
import pytest
from apps.inventory.models import Category


@pytest.mark.django_db
class TestCategoryModel:
    """Test suite for Category model."""
    
    def test_create_category(self):
        """Test creating a category."""
        category = Category.objects.create(
            name='Electronics',
            name_en='Electronics',
            description='Electronic items'
        )
        assert category.name == 'Electronics'
        assert category.name_en == 'Electronics'
        assert category.description == 'Electronic items'
    
    def test_category_string_representation(self):
        """Test category string representation."""
        category = Category.objects.create(name='Electronics')
        assert str(category) == 'Electronics'
    
    def test_category_parent_child_relationship(self):
        """Test hierarchical category structure."""
        parent = Category.objects.create(name='Electronics')
        child = Category.objects.create(
            name='Laptops',
            parent=parent
        )
        assert child.parent == parent
        assert child in parent.children.all()
    
    def test_category_full_path_no_parent(self):
        """Test full_path for category without parent."""
        category = Category.objects.create(name='Electronics')
        assert category.full_path == 'Electronics'
    
    def test_category_full_path_with_parent(self):
        """Test full_path for category with parent."""
        parent = Category.objects.create(name='Electronics')
        child = Category.objects.create(name='Laptops', parent=parent)
        assert child.full_path == 'Electronics > Laptops'
    
    def test_category_full_path_multiple_levels(self):
        """Test full_path for multi-level hierarchy."""
        grandparent = Category.objects.create(name='Products')
        parent = Category.objects.create(name='Electronics', parent=grandparent)
        child = Category.objects.create(name='Laptops', parent=parent)
        assert child.full_path == 'Products > Electronics > Laptops'
    
    def test_category_sort_order(self):
        """Test category ordering by sort_order."""
        cat1 = Category.objects.create(name='Category 1', sort_order=2)
        cat2 = Category.objects.create(name='Category 2', sort_order=1)
        cat3 = Category.objects.create(name='Category 3', sort_order=3)
        
        categories = list(Category.objects.all())
        assert categories[0] == cat2
        assert categories[1] == cat1
        assert categories[2] == cat3
    
    def test_category_sort_order_default(self):
        """Test category default sort_order."""
        category = Category.objects.create(name='Test')
        assert category.sort_order == 0
    
    def test_category_image_field(self):
        """Test category image field."""
        category = Category.objects.create(name='Electronics')
        assert category.image.name is None or category.image.name == ''
    
    def test_category_soft_delete(self, admin_user):
        """Test category soft delete."""
        category = Category.objects.create(name='Electronics')
        category.soft_delete(user=admin_user)
        
        assert category.is_deleted is True
        assert category.deleted_by == admin_user
    
    def test_category_is_active(self):
        """Test category is_active field."""
        category = Category.objects.create(name='Electronics', is_active=True)
        assert category.is_active is True
        
        category.is_active = False
        category.save()
        assert category.is_active is False
