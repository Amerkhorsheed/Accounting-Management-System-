"""
Core Utilities - Helper Functions and Utilities
"""
import random
import string
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, date
from django.conf import settings


def generate_code(prefix: str, length: int = 8) -> str:
    """
    Generate a unique code with a prefix.
    
    Args:
        prefix: The prefix for the code (e.g., 'INV', 'PO')
        length: Total length of the numeric part
    
    Returns:
        Generated code string
    """
    random_part = ''.join(random.choices(string.digits, k=length))
    return f"{prefix}-{random_part}"


def generate_barcode() -> str:
    """
    Generate a unique 13-digit barcode (EAN-13 format).
    
    Returns:
        13-digit barcode string
    """
    # Generate 12 random digits
    digits = [random.randint(0, 9) for _ in range(12)]
    
    # Calculate check digit (EAN-13 algorithm)
    odd_sum = sum(digits[::2])
    even_sum = sum(digits[1::2])
    check_digit = (10 - (odd_sum + even_sum * 3) % 10) % 10
    
    digits.append(check_digit)
    return ''.join(map(str, digits))


def round_decimal(value: Decimal, places: int = None) -> Decimal:
    """
    Round a decimal value to specified decimal places.
    
    Args:
        value: The decimal value to round
        places: Number of decimal places (defaults to settings)
    
    Returns:
        Rounded Decimal value
    """
    if places is None:
        places = settings.BUSINESS_SETTINGS.get('DECIMAL_PLACES', 2)
    
    quantize_str = Decimal(10) ** -places
    return Decimal(value).quantize(quantize_str, rounding=ROUND_HALF_UP)


def calculate_percentage(amount: Decimal, percentage: Decimal) -> Decimal:
    """
    Calculate percentage of an amount.
    
    Args:
        amount: The base amount
        percentage: The percentage to calculate
    
    Returns:
        Calculated percentage amount
    """
    return round_decimal((Decimal(amount) * Decimal(percentage)) / Decimal(100))


def calculate_vat(amount: Decimal, rate: Decimal = None) -> Decimal:
    """
    Calculate VAT amount.
    
    Args:
        amount: The base amount (excluding VAT)
        rate: VAT rate percentage (defaults to settings)
    
    Returns:
        VAT amount
    """
    if rate is None:
        rate = Decimal(settings.BUSINESS_SETTINGS.get('TAX_RATE', 15))
    return calculate_percentage(amount, rate)


def format_currency(amount: Decimal) -> str:
    """
    Format amount with currency symbol.
    
    Args:
        amount: The amount to format
    
    Returns:
        Formatted currency string
    """
    symbol = settings.BUSINESS_SETTINGS.get('CURRENCY_SYMBOL', 'ر.س')
    formatted = f"{round_decimal(amount):,.2f}"
    return f"{formatted} {symbol}"


def get_date_range(period: str) -> tuple:
    """
    Get start and end dates for a given period.
    
    Args:
        period: 'today', 'week', 'month', 'year'
    
    Returns:
        Tuple of (start_date, end_date)
    """
    today = date.today()
    
    if period == 'today':
        return today, today
    
    elif period == 'week':
        start = today - timedelta(days=today.weekday())
        return start, today
    
    elif period == 'month':
        start = today.replace(day=1)
        return start, today
    
    elif period == 'year':
        start = today.replace(month=1, day=1)
        return start, today
    
    else:
        return today, today


from datetime import timedelta


def arabic_number(number) -> str:
    """
    Convert Western Arabic numerals to Eastern Arabic numerals.
    
    Args:
        number: Number to convert
    
    Returns:
        String with Eastern Arabic numerals
    """
    western = '0123456789'
    eastern = '٠١٢٣٤٥٦٧٨٩'
    trans_table = str.maketrans(western, eastern)
    return str(number).translate(trans_table)


class Singleton:
    """
    Singleton metaclass for implementing singleton pattern.
    """
    _instances = {}
    
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


def get_daily_fx(rate_date: date):
    from apps.core.settings_models import DailyExchangeRate
    from apps.core.exceptions import ValidationException

    fx = DailyExchangeRate.objects.filter(rate_date=rate_date).first()
    if not fx:
        # Fallback to latest available exchange rate
        fx = DailyExchangeRate.objects.order_by('-rate_date').first()
        if not fx:
            raise ValidationException('لا يوجد سعر صرف محدد في النظام', field='fx_rate_date')
    return fx.usd_to_syp_old, fx.usd_to_syp_new


def normalize_fx(usd_to_syp_old: Decimal = None, usd_to_syp_new: Decimal = None):
    from apps.core.exceptions import ValidationException

    if usd_to_syp_old is None and usd_to_syp_new is None:
        raise ValidationException('سعر الصرف غير محدد', field='exchange_rate')

    if usd_to_syp_old is None and usd_to_syp_new is not None:
        if usd_to_syp_new <= 0:
            raise ValidationException('سعر صرف الليرة الجديدة غير صالح', field='usd_to_syp_new_snapshot')
        usd_to_syp_old = usd_to_syp_new * Decimal('100')

    if usd_to_syp_new is None and usd_to_syp_old is not None:
        if usd_to_syp_old <= 0:
            raise ValidationException('سعر صرف الليرة القديمة غير صالح', field='usd_to_syp_old_snapshot')
        usd_to_syp_new = usd_to_syp_old / Decimal('100')

    if usd_to_syp_old is not None and usd_to_syp_old <= 0:
        raise ValidationException('سعر صرف الليرة القديمة غير صالح', field='usd_to_syp_old_snapshot')
    if usd_to_syp_new is not None and usd_to_syp_new <= 0:
        raise ValidationException('سعر صرف الليرة الجديدة غير صالح', field='usd_to_syp_new_snapshot')

    return usd_to_syp_old, usd_to_syp_new


def to_usd(amount: Decimal, currency: str, usd_to_syp_old: Decimal = None, usd_to_syp_new: Decimal = None) -> Decimal:
    if amount is None:
        return Decimal('0.00')

    if currency == 'USD':
        return round_decimal(amount, 2)

    usd_to_syp_old, usd_to_syp_new = normalize_fx(usd_to_syp_old, usd_to_syp_new)

    if currency == 'SYP_OLD':
        return round_decimal(Decimal(amount) / usd_to_syp_old, 2)
    if currency == 'SYP_NEW':
        return round_decimal(Decimal(amount) / usd_to_syp_new, 2)

    from apps.core.exceptions import ValidationException

    raise ValidationException('عملة غير مدعومة', field='transaction_currency')


def from_usd(amount_usd: Decimal, currency: str, usd_to_syp_old: Decimal = None, usd_to_syp_new: Decimal = None) -> Decimal:
    if amount_usd is None:
        return Decimal('0.00')

    if currency == 'USD':
        return round_decimal(amount_usd, 2)

    usd_to_syp_old, usd_to_syp_new = normalize_fx(usd_to_syp_old, usd_to_syp_new)

    if currency == 'SYP_OLD':
        return round_decimal(Decimal(amount_usd) * usd_to_syp_old, 2)
    if currency == 'SYP_NEW':
        return round_decimal(Decimal(amount_usd) * usd_to_syp_new, 2)

    from apps.core.exceptions import ValidationException

    raise ValidationException('عملة غير مدعومة', field='transaction_currency')
