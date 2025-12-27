"""
Tests for UserManager.
"""
import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestUserManager:
    """Test suite for UserManager."""
    
    def test_create_user_basic(self):
        """Test basic user creation."""
        user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        assert user.username == 'testuser'
        assert user.check_password('testpass123')
    
    def test_create_user_with_all_fields(self):
        """Test user creation with all fields."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            phone='1234567890',
            role=User.Role.MANAGER
        )
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.first_name == 'Test'
        assert user.last_name == 'User'
        assert user.phone == '1234567890'
        assert user.role == User.Role.MANAGER
    
    def test_create_user_password_hashing(self):
        """Test that password is properly hashed."""
        password = 'testpass123'
        user = User.objects.create_user(
            username='testuser',
            password=password
        )
        assert user.password != password
        assert user.check_password(password)
    
    def test_create_user_without_password(self):
        """Test creating user without password."""
        user = User.objects.create_user(
            username='testuser',
            password=None
        )
        assert not user.has_usable_password()
    
    def test_create_superuser_basic(self):
        """Test basic superuser creation."""
        user = User.objects.create_superuser(
            username='admin',
            password='admin123'
        )
        assert user.is_staff
        assert user.is_superuser
        assert user.is_active
    
    def test_create_superuser_with_email(self):
        """Test superuser creation with email."""
        user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        assert user.email == 'admin@example.com'
    
    def test_create_superuser_defaults(self):
        """Test that superuser has correct default flags."""
        user = User.objects.create_superuser(
            username='admin',
            password='admin123'
        )
        assert user.is_staff is True
        assert user.is_superuser is True
        assert user.is_active is True
    
    def test_create_superuser_is_staff_false_fails(self):
        """Test that creating superuser with is_staff=False fails."""
        with pytest.raises(ValueError, match='Superuser must have is_staff=True'):
            User.objects.create_superuser(
                username='admin',
                password='admin123',
                is_staff=False
            )
    
    def test_create_superuser_is_superuser_false_fails(self):
        """Test that creating superuser with is_superuser=False fails."""
        with pytest.raises(ValueError, match='Superuser must have is_superuser=True'):
            User.objects.create_superuser(
                username='admin',
                password='admin123',
                is_superuser=False
            )
    
    def test_email_normalization(self):
        """Test that email is normalized."""
        user = User.objects.create_user(
            username='testuser',
            email='Test@EXAMPLE.COM',
            password='testpass123'
        )
        assert user.email == 'Test@example.com'
    
    def test_create_user_without_email(self):
        """Test creating user without email."""
        user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        assert user.email is None or user.email == ''
    
    def test_create_user_empty_username_fails(self):
        """Test that creating user with empty username fails."""
        with pytest.raises(ValueError, match='يجب إدخال اسم المستخدم'):
            User.objects.create_user(
                username='',
                password='testpass123'
            )
    
    def test_create_user_none_username_fails(self):
        """Test that creating user with None username fails."""
        with pytest.raises(ValueError, match='يجب إدخال اسم المستخدم'):
            User.objects.create_user(
                username=None,
                password='testpass123'
            )
