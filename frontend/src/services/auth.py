"""
Authentication Service
"""
from typing import Optional, Dict
from .api import api, ApiException


class AuthService:
    """
    Service for handling authentication and user session.
    """
    
    _current_user: Optional[Dict] = None
    
    @classmethod
    def login(cls, username: str, password: str) -> Dict:
        """
        Login user with credentials.
        Returns user data on success, raises exception on failure.
        """
        try:
            response = api.login(username, password)
            if 'access' in response:
                # Fetch user details
                cls._current_user = api.get_current_user()
                return cls._current_user
            raise AuthException("فشل تسجيل الدخول")
        except ApiException as e:
            raise AuthException(f"خطأ في الاتصال: {str(e)}")
            
    @classmethod
    def logout(cls):
        """Logout current user."""
        cls._current_user = None
        api.logout()
        
    @classmethod
    def get_current_user(cls) -> Optional[Dict]:
        """Get current logged in user."""
        return cls._current_user
        
    @classmethod
    def is_authenticated(cls) -> bool:
        """Check if user is authenticated."""
        return cls._current_user is not None
        
    @classmethod
    def has_permission(cls, permission: str) -> bool:
        """Check if user has specific permission."""
        if not cls._current_user:
            return False
            
        role = cls._current_user.get('role', '')
        
        # Admin has all permissions
        if role == 'admin':
            return True
            
        # Define role permissions
        role_permissions = {
            'manager': ['view', 'create', 'edit', 'delete', 'approve', 'reports'],
            'accountant': ['view', 'create', 'edit', 'reports'],
            'salesperson': ['view', 'create', 'edit'],
            'cashier': ['view', 'create', 'pos'],
            'warehouse': ['view', 'create', 'edit', 'inventory'],
            'viewer': ['view'],
        }
        
        permissions = role_permissions.get(role, [])
        return permission in permissions


class AuthException(Exception):
    """Authentication exception."""
    pass
