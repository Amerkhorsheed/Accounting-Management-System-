"""
Settings Serializers
"""
from rest_framework import serializers
from .settings_models import SystemSettings, Currency, TaxRate


class SystemSettingsSerializer(serializers.ModelSerializer):
    """Serializer for SystemSettings."""
    
    class Meta:
        model = SystemSettings
        fields = ['id', 'key', 'value', 'description', 'updated_at']
        read_only_fields = ['id', 'updated_at']


class CurrencySerializer(serializers.ModelSerializer):
    """Serializer for Currency."""
    
    class Meta:
        model = Currency
        fields = [
            'id', 'code', 'name', 'name_en', 'symbol',
            'exchange_rate', 'is_primary', 'is_active', 'decimal_places'
        ]
        read_only_fields = ['id']
    
    def validate_exchange_rate(self, value):
        """Validate that exchange rate is positive and non-zero."""
        if value <= 0:
            raise serializers.ValidationError('سعر الصرف يجب أن يكون أكبر من صفر')
        return value


class TaxRateSerializer(serializers.ModelSerializer):
    """Serializer for TaxRate."""
    
    class Meta:
        model = TaxRate
        fields = [
            'id', 'name', 'code', 'rate', 
            'is_active', 'is_default', 'description'
        ]
        read_only_fields = ['id']


class CurrencyConvertSerializer(serializers.Serializer):
    """Serializer for currency conversion."""
    
    amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    from_currency = serializers.CharField(max_length=10)
    to_currency = serializers.CharField(max_length=10)
