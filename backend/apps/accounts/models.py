"""
Accounts Models - User Management and Authentication
"""
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from apps.core.models import TimeStampedModel


class UserManager(BaseUserManager):
    """Custom manager for User model."""
    
    def create_user(self, username, email=None, password=None, **extra_fields):
        """Create and save a regular user."""
        if not username:
            raise ValueError('يجب إدخال اسم المستخدم')
        
        email = self.normalize_email(email) if email else None
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        """Create and save a superuser."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(username, email, password, **extra_fields)


class User(AbstractUser, TimeStampedModel):
    """
    Custom User model for the accounting system.
    Extends Django's AbstractUser with additional fields.
    """
    
    class Role(models.TextChoices):
        ADMIN = 'admin', 'مدير النظام'
        MANAGER = 'manager', 'مدير'
        ACCOUNTANT = 'accountant', 'محاسب'
        SALESPERSON = 'salesperson', 'مندوب مبيعات'
        CASHIER = 'cashier', 'كاشير'
        WAREHOUSE = 'warehouse', 'أمين مستودع'
        VIEWER = 'viewer', 'مشاهد فقط'

    email = models.EmailField(
        blank=True,
        null=True,
        verbose_name='البريد الإلكتروني'
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='رقم الهاتف'
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.VIEWER,
        verbose_name='الدور'
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        verbose_name='الصورة الشخصية'
    )
    
    objects = UserManager()

    class Meta:
        verbose_name = 'مستخدم'
        verbose_name_plural = 'المستخدمون'
        ordering = ['-date_joined']

    def __str__(self):
        return self.get_full_name() or self.username

    @property
    def full_name(self):
        return self.get_full_name() or self.username

    def has_role(self, role: str) -> bool:
        """Check if user has a specific role."""
        return self.role == role

    def is_admin(self) -> bool:
        """Check if user is admin."""
        return self.role == self.Role.ADMIN or self.is_superuser

    def is_manager_or_above(self) -> bool:
        """Check if user is manager or admin."""
        return self.role in [self.Role.ADMIN, self.Role.MANAGER] or self.is_superuser


class AuditLog(TimeStampedModel):
    """
    Audit log for tracking user actions.
    """
    
    class Action(models.TextChoices):
        CREATE = 'create', 'إنشاء'
        UPDATE = 'update', 'تعديل'
        DELETE = 'delete', 'حذف'
        LOGIN = 'login', 'تسجيل دخول'
        LOGOUT = 'logout', 'تسجيل خروج'
        VIEW = 'view', 'عرض'
        PRINT = 'print', 'طباعة'
        EXPORT = 'export', 'تصدير'

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs',
        verbose_name='المستخدم'
    )
    action = models.CharField(
        max_length=20,
        choices=Action.choices,
        verbose_name='الإجراء'
    )
    model_name = models.CharField(
        max_length=100,
        verbose_name='اسم الجدول'
    )
    object_id = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='معرف السجل'
    )
    object_repr = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='وصف السجل'
    )
    changes = models.JSONField(
        blank=True,
        null=True,
        verbose_name='التغييرات'
    )
    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
        verbose_name='عنوان IP'
    )

    class Meta:
        verbose_name = 'سجل المراجعة'
        verbose_name_plural = 'سجلات المراجعة'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} - {self.action} - {self.model_name}"
