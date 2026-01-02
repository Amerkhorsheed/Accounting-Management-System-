"""
Settings Views - System Configuration API
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from decimal import Decimal
from datetime import date, datetime

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .settings_models import SystemSettings, Currency, TaxRate, DailyExchangeRate
from .settings_serializers import (
    SystemSettingsSerializer, CurrencySerializer, 
    TaxRateSerializer, CurrencyConvertSerializer, DailyExchangeRateSerializer
)


class SystemSettingsViewSet(viewsets.ModelViewSet):
    """ViewSet for system settings management."""
    
    queryset = SystemSettings.objects.all()
    serializer_class = SystemSettingsSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def by_key(self, request):
        """Get setting by key."""
        key = request.query_params.get('key')
        if not key:
            return Response({'detail': 'Key parameter is required'}, status=400)
        
        value = SystemSettings.get_setting(key)
        return Response({'key': key, 'value': value})
    
    @action(detail=False, methods=['post'])
    def bulk_update(self, request):
        """Bulk update settings."""
        settings = request.data.get('settings', [])
        
        # Validate input is a list
        if not isinstance(settings, list):
            return Response(
                {'detail': 'يجب أن تكون الإعدادات قائمة', 'code': 'INVALID_INPUT'},
                status=400
            )
        
        # Validate each setting item
        errors = []
        for idx, item in enumerate(settings):
            if not isinstance(item, dict):
                errors.append(f'العنصر {idx}: يجب أن يكون كائن')
                continue
            if 'key' not in item:
                errors.append(f'العنصر {idx}: المفتاح مطلوب')
            elif not isinstance(item['key'], str) or not item['key'].strip():
                errors.append(f'العنصر {idx}: المفتاح يجب أن يكون نص غير فارغ')
            if 'value' not in item:
                errors.append(f'العنصر {idx}: القيمة مطلوبة')
        
        if errors:
            return Response(
                {'detail': 'بيانات غير صالحة', 'errors': errors, 'code': 'VALIDATION_ERROR'},
                status=400
            )
        
        # Process valid settings
        updated_count = 0
        for item in settings:
            SystemSettings.set_setting(
                key=item['key'].strip(),
                value=str(item['value']),
                description=item.get('description', '')
            )
            updated_count += 1
        
        return Response({'status': 'updated', 'count': updated_count})


class CurrencyViewSet(viewsets.ModelViewSet):
    """ViewSet for currency management."""
    
    queryset = Currency.objects.filter(is_active=True)
    serializer_class = CurrencySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def primary(self, request):
        """Get primary currency."""
        currency = Currency.get_primary()
        if currency:
            return Response(CurrencySerializer(currency).data)
        return Response({'detail': 'لا توجد عملة أساسية'}, status=404)
    
    @action(detail=False, methods=['post'])
    def convert(self, request):
        """Convert amount between currencies."""
        serializer = CurrencyConvertSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            result = Currency.convert(
                amount=Decimal(str(serializer.validated_data['amount'])),
                from_currency=serializer.validated_data['from_currency'],
                to_currency=serializer.validated_data['to_currency']
            )
            return Response({
                'amount': serializer.validated_data['amount'],
                'from_currency': serializer.validated_data['from_currency'],
                'to_currency': serializer.validated_data['to_currency'],
                'converted_amount': result
            })
        except Currency.DoesNotExist:
            return Response({'detail': 'العملة غير موجودة'}, status=404)
        except ValueError as e:
            return Response({'detail': str(e), 'code': 'INVALID_EXCHANGE_RATE'}, status=400)
    
    @action(detail=True, methods=['post'])
    def set_primary(self, request, pk=None):
        """Set currency as primary."""
        currency = self.get_object()
        currency.is_primary = True
        currency.save()
        return Response(CurrencySerializer(currency).data)
    
    @action(detail=True, methods=['post'])
    def update_rate(self, request, pk=None):
        """Update exchange rate."""
        currency = self.get_object()
        rate = request.data.get('exchange_rate')
        if rate is not None:
            try:
                rate_decimal = Decimal(str(rate))
                if rate_decimal <= 0:
                    return Response(
                        {'detail': 'سعر الصرف يجب أن يكون أكبر من صفر', 'code': 'INVALID_EXCHANGE_RATE'},
                        status=400
                    )
                currency.exchange_rate = rate_decimal
                currency.save()
            except (ValueError, TypeError):
                return Response(
                    {'detail': 'سعر الصرف غير صالح', 'code': 'INVALID_EXCHANGE_RATE'},
                    status=400
                )
        return Response(CurrencySerializer(currency).data)


class TaxRateViewSet(viewsets.ModelViewSet):
    """ViewSet for tax rate management."""
    
    queryset = TaxRate.objects.filter(is_active=True)
    serializer_class = TaxRateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def default(self, request):
        """Get default tax rate."""
        rate = TaxRate.get_default()
        return Response({
            'rate': rate,
            'is_enabled': TaxRate.is_tax_enabled()
        })
    
    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """Set tax rate as default."""
        tax = self.get_object()
        tax.is_default = True
        tax.save()
        return Response(TaxRateSerializer(tax).data)


class AppContextViewSet(viewsets.ViewSet):
    """Read-only endpoint for frontend bootstrapping context (FX + display currency)."""

    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        rate_date_str = request.query_params.get('rate_date')
        strict_fx = str(request.query_params.get('strict_fx', '')).lower() in {'1', 'true', 'yes'}

        if rate_date_str:
            try:
                rate_date = datetime.strptime(rate_date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {'detail': 'صيغة التاريخ غير صالحة', 'code': 'INVALID_DATE'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            rate_date = date.today()

        primary_currency = Currency.get_primary()
        primary_currency_data = CurrencySerializer(primary_currency).data if primary_currency else None

        fx = DailyExchangeRate.objects.filter(rate_date=rate_date).first()
        if not fx and strict_fx:
            return Response(
                {'detail': 'سعر الصرف لليوم غير موجود', 'code': 'FX_NOT_FOUND', 'rate_date': str(rate_date)},
                status=status.HTTP_404_NOT_FOUND
            )

        fx_data = None
        if fx:
            fx_data = {
                'rate_date': str(fx.rate_date),
                'usd_to_syp_old': str(fx.usd_to_syp_old),
                'usd_to_syp_new': str(fx.usd_to_syp_new),
            }

        return Response({
            'rate_date': str(rate_date),
            'primary_currency': primary_currency_data,
            'daily_fx': fx_data,
        })


class DailyExchangeRateViewSet(viewsets.ModelViewSet):
    """CRUD endpoint for daily USD→SYP exchange rates."""

    queryset = DailyExchangeRate.objects.all()
    serializer_class = DailyExchangeRateSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['rate_date']
    search_fields = ['notes']
    ordering_fields = ['rate_date', 'created_at', 'updated_at']
    ordering = ['-rate_date']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]
