"""
Core Models - Base Abstract Models for the Accounting System

These models provide common fields and functionality that are inherited
by other models throughout the application.
"""
from django.db import models
from django.utils import timezone
from django.conf import settings


class TimeStampedModel(models.Model):
    """
    Abstract base model that provides self-updating 
    created_at and updated_at fields.
    """
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاريخ التحديث'
    )

    class Meta:
        abstract = True


class SoftDeleteModel(models.Model):
    """
    Abstract model that provides soft delete functionality.
    Records are marked as deleted instead of being physically removed.
    """
    is_deleted = models.BooleanField(
        default=False,
        verbose_name='محذوف'
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='تاريخ الحذف'
    )
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_deleted',
        verbose_name='حذف بواسطة'
    )

    class Meta:
        abstract = True

    def soft_delete(self, user=None):
        """Mark the record as deleted."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])

    def restore(self):
        """Restore a soft-deleted record."""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])


class ActiveModel(models.Model):
    """
    Abstract model that provides an is_active field
    for enabling/disabling records.
    """
    is_active = models.BooleanField(
        default=True,
        verbose_name='نشط'
    )

    class Meta:
        abstract = True


class AuditModel(TimeStampedModel):
    """
    Abstract model that tracks who created and last modified the record.
    """
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_created',
        verbose_name='أنشئ بواسطة'
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_updated',
        verbose_name='عدّل بواسطة'
    )

    class Meta:
        abstract = True


class BaseModel(AuditModel, SoftDeleteModel, ActiveModel):
    """
    Comprehensive base model combining all common functionality:
    - Timestamps (created_at, updated_at)
    - Audit fields (created_by, updated_by)
    - Soft delete (is_deleted, deleted_at, deleted_by)
    - Active status (is_active)
    """

    class Meta:
        abstract = True
        ordering = ['-created_at']


class AddressModel(models.Model):
    """
    Abstract model for address fields.
    """
    address = models.TextField(
        blank=True,
        null=True,
        verbose_name='العنوان'
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='المدينة'
    )
    region = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='المنطقة'
    )
    postal_code = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='الرمز البريدي'
    )
    country = models.CharField(
        max_length=100,
        default='المملكة العربية السعودية',
        verbose_name='الدولة'
    )

    class Meta:
        abstract = True

    @property
    def full_address(self):
        """Return formatted full address."""
        parts = [self.address, self.city, self.region, self.postal_code, self.country]
        return ', '.join(filter(None, parts))


class ContactModel(models.Model):
    """
    Abstract model for contact information fields.
    """
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='رقم الهاتف'
    )
    mobile = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='رقم الجوال'
    )
    email = models.EmailField(
        blank=True,
        null=True,
        verbose_name='البريد الإلكتروني'
    )
    fax = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='الفاكس'
    )
    website = models.URLField(
        blank=True,
        null=True,
        verbose_name='الموقع الإلكتروني'
    )

    class Meta:
        abstract = True
