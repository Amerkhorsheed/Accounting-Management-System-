import pytest
from datetime import date
from rest_framework import status

from apps.core.settings_models import Currency, DailyExchangeRate


@pytest.mark.django_db
class TestAppContextApi:
    def test_requires_authentication(self, api_client):
        response = api_client.get('/api/v1/core/app-context/')
        assert response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)

    def test_returns_primary_currency_and_daily_fx(self, admin_client):
        Currency.objects.create(code='USD', name='US Dollar', name_en='US Dollar', symbol='$', is_primary=True, is_active=True)
        DailyExchangeRate.objects.create(rate_date=date.today(), usd_to_syp_old='1500000', usd_to_syp_new='15000')

        response = admin_client.get('/api/v1/core/app-context/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data.get('primary_currency') is not None
        assert response.data['primary_currency']['code'] == 'USD'
        assert response.data.get('daily_fx') is not None
        assert response.data['daily_fx']['rate_date'] == str(date.today())

    def test_strict_fx_returns_404_when_missing(self, admin_client):
        Currency.objects.create(code='USD', name='US Dollar', name_en='US Dollar', symbol='$', is_primary=True, is_active=True)

        response = admin_client.get('/api/v1/core/app-context/?strict_fx=true')
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data.get('code') == 'FX_NOT_FOUND'

    def test_invalid_date_returns_400(self, admin_client):
        response = admin_client.get('/api/v1/core/app-context/?rate_date=2025-99-99')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data.get('code') == 'INVALID_DATE'


@pytest.mark.django_db
class TestDailyExchangeRatesApi:
    def test_list_requires_authentication(self, api_client):
        response = api_client.get('/api/v1/core/daily-exchange-rates/')
        assert response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)

    def test_list_authenticated(self, manager_client):
        DailyExchangeRate.objects.create(rate_date=date.today(), usd_to_syp_old='1500000', usd_to_syp_new='15000')
        response = manager_client.get('/api/v1/core/daily-exchange-rates/')
        assert response.status_code == status.HTTP_200_OK

    def test_create_requires_admin(self, manager_client):
        payload = {
            'rate_date': str(date.today()),
            'usd_to_syp_old': '1500000',
            'usd_to_syp_new': '15000',
        }
        response = manager_client.post('/api/v1/core/daily-exchange-rates/', payload, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_admin_allows_and_derives_old_from_new(self, admin_client):
        payload = {
            'rate_date': str(date.today()),
            'usd_to_syp_new': '15000',
        }
        response = admin_client.post('/api/v1/core/daily-exchange-rates/', payload, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data.get('usd_to_syp_old') is not None
        assert response.data.get('usd_to_syp_new') == '15000.000000'

    def test_create_validation_missing_rates(self, admin_client):
        payload = {
            'rate_date': str(date.today()),
        }
        response = admin_client.post('/api/v1/core/daily-exchange-rates/', payload, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'exchange_rate' in response.data

    def test_rate_date_uniqueness(self, admin_client):
        payload = {
            'rate_date': str(date.today()),
            'usd_to_syp_old': '1500000',
            'usd_to_syp_new': '15000',
        }
        response1 = admin_client.post('/api/v1/core/daily-exchange-rates/', payload, format='json')
        assert response1.status_code == status.HTTP_201_CREATED

        response2 = admin_client.post('/api/v1/core/daily-exchange-rates/', payload, format='json')
        assert response2.status_code == status.HTTP_400_BAD_REQUEST
        assert 'rate_date' in response2.data

    def test_filter_by_rate_date(self, manager_client):
        DailyExchangeRate.objects.create(rate_date=date.today(), usd_to_syp_old='1500000', usd_to_syp_new='15000')
        DailyExchangeRate.objects.create(rate_date=date(2025, 1, 1), usd_to_syp_old='1400000', usd_to_syp_new='14000')

        response = manager_client.get(f'/api/v1/core/daily-exchange-rates/?rate_date={date.today()}')
        assert response.status_code == status.HTTP_200_OK

    def test_update_requires_admin(self, admin_client, manager_client):
        fx = DailyExchangeRate.objects.create(rate_date=date.today(), usd_to_syp_old='1500000', usd_to_syp_new='15000')

        response_forbidden = manager_client.patch(
            f'/api/v1/core/daily-exchange-rates/{fx.id}/',
            {'usd_to_syp_new': '16000'},
            format='json'
        )
        assert response_forbidden.status_code == status.HTTP_403_FORBIDDEN

        response_ok = admin_client.patch(
            f'/api/v1/core/daily-exchange-rates/{fx.id}/',
            {'usd_to_syp_new': '16000'},
            format='json'
        )
        assert response_ok.status_code == status.HTTP_200_OK

    def test_delete_requires_admin(self, admin_client, manager_client):
        fx = DailyExchangeRate.objects.create(rate_date=date.today(), usd_to_syp_old='1500000', usd_to_syp_new='15000')

        response_forbidden = manager_client.delete(f'/api/v1/core/daily-exchange-rates/{fx.id}/')
        assert response_forbidden.status_code == status.HTTP_403_FORBIDDEN

        response_ok = admin_client.delete(f'/api/v1/core/daily-exchange-rates/{fx.id}/')
        assert response_ok.status_code == status.HTTP_204_NO_CONTENT
