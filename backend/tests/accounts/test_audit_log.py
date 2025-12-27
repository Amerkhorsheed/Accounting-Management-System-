"""
Tests for AuditLog model.
"""
import pytest
from django.contrib.auth import get_user_model
from apps.accounts.models import AuditLog

User = get_user_model()


@pytest.mark.django_db
class TestAuditLogModel:
    """Test suite for AuditLog model."""
    
    @pytest.fixture(autouse=True)
    def setup_data(self):
        """Setup test data."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_create_audit_log(self):
        """Test creating an audit log entry."""
        log = AuditLog.objects.create(
            user=self.user,
            action=AuditLog.Action.CREATE,
            model_name='Product',
            object_id='123',
            object_repr='Test Product'
        )
        assert log.user == self.user
        assert log.action == AuditLog.Action.CREATE
        assert log.model_name == 'Product'
        assert log.object_id == '123'
        assert log.object_repr == 'Test Product'
    
    def test_audit_log_all_actions(self):
        """Test all audit log actions."""
        actions = [
            AuditLog.Action.CREATE,
            AuditLog.Action.UPDATE,
            AuditLog.Action.DELETE,
            AuditLog.Action.LOGIN,
            AuditLog.Action.LOGOUT,
            AuditLog.Action.VIEW,
            AuditLog.Action.PRINT,
            AuditLog.Action.EXPORT
        ]
        
        for action in actions:
            log = AuditLog.objects.create(
                user=self.user,
                action=action,
                model_name='TestModel'
            )
            assert log.action == action
    
    def test_audit_log_with_changes(self):
        """Test audit log with changes JSON field."""
        changes = {
            'name': {'old': 'Old Name', 'new': 'New Name'},
            'price': {'old': 100, 'new': 150}
        }
        log = AuditLog.objects.create(
            user=self.user,
            action=AuditLog.Action.UPDATE,
            model_name='Product',
            changes=changes
        )
        assert log.changes == changes
        assert log.changes['name']['old'] == 'Old Name'
        assert log.changes['price']['new'] == 150
    
    def test_audit_log_with_ip_address(self):
        """Test audit log with IP address."""
        log = AuditLog.objects.create(
            user=self.user,
            action=AuditLog.Action.LOGIN,
            model_name='User',
            ip_address='192.168.1.1'
        )
        assert log.ip_address == '192.168.1.1'
    
    def test_audit_log_with_ipv6_address(self):
        """Test audit log with IPv6 address."""
        log = AuditLog.objects.create(
            user=self.user,
            action=AuditLog.Action.LOGIN,
            model_name='User',
            ip_address='2001:0db8:85a3:0000:0000:8a2e:0370:7334'
        )
        assert log.ip_address == '2001:0db8:85a3:0000:0000:8a2e:0370:7334'
    
    def test_audit_log_without_user(self):
        """Test audit log without user (system action)."""
        log = AuditLog.objects.create(
            user=None,
            action=AuditLog.Action.CREATE,
            model_name='Product'
        )
        assert log.user is None
    
    def test_audit_log_string_representation(self):
        """Test audit log string representation."""
        log = AuditLog.objects.create(
            user=self.user,
            action=AuditLog.Action.UPDATE,
            model_name='Product'
        )
        expected = f"{self.user} - {log.action} - Product"
        assert str(log) == expected
    
    def test_audit_log_timestamps(self):
        """Test audit log timestamps."""
        log = AuditLog.objects.create(
            user=self.user,
            action=AuditLog.Action.CREATE,
            model_name='Product'
        )
        assert log.created_at is not None
        assert log.updated_at is not None
    
    def test_audit_log_ordering(self):
        """Test audit log ordering (newest first)."""
        import time
        log1 = AuditLog.objects.create(
            user=self.user,
            action=AuditLog.Action.CREATE,
            model_name='Product1'
        )
        time.sleep(0.01)  # Ensure different timestamps
        log2 = AuditLog.objects.create(
            user=self.user,
            action=AuditLog.Action.CREATE,
            model_name='Product2'
        )
        
        logs = list(AuditLog.objects.all())
        assert logs[0] == log2
        assert logs[1] == log1
    
    def test_audit_log_optional_fields(self):
        """Test audit log with optional fields empty."""
        log = AuditLog.objects.create(
            user=self.user,
            action=AuditLog.Action.VIEW,
            model_name='Product'
        )
        assert log.object_id is None or log.object_id == ''
        assert log.object_repr is None or log.object_repr == ''
        assert log.changes is None
        assert log.ip_address is None
