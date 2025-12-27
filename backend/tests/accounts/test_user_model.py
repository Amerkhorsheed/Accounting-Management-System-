"""
Tests for User model.
"""
import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    """Test suite for User model."""
    
    def test_create_user_with_username(self):
        """Test creating a user with username."""
        user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        assert user.username == 'testuser'
        assert user.check_password('testpass123')
        assert user.is_active
        assert not user.is_staff
        assert not user.is_superuser
        assert user.role == User.Role.VIEWER
    
    def test_create_user_with_email(self):
        """Test creating a user with email."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        assert user.email == 'test@example.com'
    
    def test_create_user_without_username_fails(self):
        """Test that creating a user without username raises error."""
        with pytest.raises(ValueError, match='يجب إدخال اسم المستخدم'):
            User.objects.create_user(username='', password='testpass123')
    
    def test_create_superuser(self):
        """Test creating a superuser."""
        user = User.objects.create_superuser(
            username='admin',
            password='admin123'
        )
        assert user.is_staff
        assert user.is_superuser
        assert user.is_active
    
    def test_create_superuser_with_wrong_flags_fails(self):
        """Test that creating superuser with is_staff=False fails."""
        with pytest.raises(ValueError, match='Superuser must have is_staff=True'):
            User.objects.create_superuser(
                username='admin',
                password='admin123',
                is_staff=False
            )
    
    def test_user_string_representation(self):
        """Test user string representation."""
        user = User.objects.create_user(
            username='testuser',
            first_name='Test',
            last_name='User'
        )
        assert str(user) == 'Test User'
        
        user_no_name = User.objects.create_user(username='noname')
        assert str(user_no_name) == 'noname'
    
    def test_user_full_name_property(self):
        """Test user full_name property."""
        user = User.objects.create_user(
            username='testuser',
            first_name='John',
            last_name='Doe'
        )
        assert user.full_name == 'John Doe'
        
        user_no_name = User.objects.create_user(username='noname')
        assert user_no_name.full_name == 'noname'
    
    def test_user_has_role(self):
        """Test has_role method."""
        user = User.objects.create_user(
            username='testuser',
            role=User.Role.MANAGER
        )
        assert user.has_role(User.Role.MANAGER)
        assert not user.has_role(User.Role.ADMIN)
    
    def test_user_is_admin(self):
        """Test is_admin method."""
        admin = User.objects.create_user(
            username='admin',
            role=User.Role.ADMIN
        )
        assert admin.is_admin()
        
        superuser = User.objects.create_superuser(
            username='superuser',
            role=User.Role.VIEWER
        )
        assert superuser.is_admin()
        
        manager = User.objects.create_user(
            username='manager',
            role=User.Role.MANAGER
        )
        assert not manager.is_admin()
    
    def test_user_is_manager_or_above(self):
        """Test is_manager_or_above method."""
        admin = User.objects.create_user(
            username='admin',
            role=User.Role.ADMIN
        )
        assert admin.is_manager_or_above()
        
        manager = User.objects.create_user(
            username='manager',
            role=User.Role.MANAGER
        )
        assert manager.is_manager_or_above()
        
        accountant = User.objects.create_user(
            username='accountant',
            role=User.Role.ACCOUNTANT
        )
        assert not accountant.is_manager_or_above()
        
        superuser = User.objects.create_superuser(
            username='superuser',
            role=User.Role.VIEWER
        )
        assert superuser.is_manager_or_above()
    
    def test_user_roles(self):
        """Test all user roles."""
        roles = [
            User.Role.ADMIN,
            User.Role.MANAGER,
            User.Role.ACCOUNTANT,
            User.Role.SALESPERSON,
            User.Role.CASHIER,
            User.Role.WAREHOUSE,
            User.Role.VIEWER
        ]
        
        for role in roles:
            user = User.objects.create_user(
                username=f'user_{role}',
                role=role
            )
            assert user.role == role
    
    def test_user_phone_field(self):
        """Test user phone field."""
        user = User.objects.create_user(
            username='testuser',
            phone='1234567890'
        )
        assert user.phone == '1234567890'
    
    def test_user_avatar_field(self):
        """Test user avatar field."""
        user = User.objects.create_user(username='testuser')
        assert user.avatar.name is None or user.avatar.name == ''
    
    def test_user_timestamps(self):
        """Test user created_at and updated_at timestamps."""
        user = User.objects.create_user(username='testuser')
        assert user.created_at is not None
        assert user.updated_at is not None
        assert user.created_at <= user.updated_at
    
    def test_email_normalization(self):
        """Test email normalization."""
        user = User.objects.create_user(
            username='testuser',
            email='Test@EXAMPLE.COM'
        )
        assert user.email == 'Test@example.com'
