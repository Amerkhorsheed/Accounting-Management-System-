"""
Settings Serializers
"""
from decimal import Decimal
from rest_framework import serializers
from .settings_models import SystemSettings, Currency, TaxRate, DailyExchangeRate


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


class DailyExchangeRateSerializer(serializers.ModelSerializer):
    """Serializer for DailyExchangeRate."""

    class Meta:
        model = DailyExchangeRate
        fields = ['id', 'rate_date', 'usd_to_syp_old', 'usd_to_syp_new', 'notes', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'usd_to_syp_old': {'required': False},
            'usd_to_syp_new': {'required': False},
        }

    def validate(self, attrs):
        old = attrs.get('usd_to_syp_old')
        new = attrs.get('usd_to_syp_new')

        if self.instance is None and old is None and new is None:
            raise serializers.ValidationError({'exchange_rate': 'سعر الصرف غير محدد'})

        if old is not None and old <= 0:
            raise serializers.ValidationError({'usd_to_syp_old': 'سعر صرف الليرة القديمة غير صالح'})
        if new is not None and new <= 0:
            raise serializers.ValidationError({'usd_to_syp_new': 'سعر صرف الليرة الجديدة غير صالح'})

        if old is None and new is not None:
            attrs['usd_to_syp_old'] = new * Decimal('100')
        if new is None and old is not None:
            attrs['usd_to_syp_new'] = old / Decimal('100')

        return attrs


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
