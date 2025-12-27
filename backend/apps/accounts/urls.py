"""
Accounts URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import UserViewSet, AuditLogViewSet

router = DefaultRouter()
router.register('users', UserViewSet)
router.register('audit-logs', AuditLogViewSet)

urlpatterns = [
    path('', include(router.urls)),
    # JWT token endpoints - matching frontend expectations
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
