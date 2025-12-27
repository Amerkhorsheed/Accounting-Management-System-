"""
Local Development Settings
Override these values for your local environment.
"""
from .base import *

# Debug mode
DEBUG = True

# Database Configuration - SQL Server with Windows Authentication
DATABASES = {
    'default': {
        'ENGINE': 'mssql',
        'NAME': 'Accounting',              # Database name
        'HOST': 'AMER',                     # Server name
        # Windows Authentication - no USER/PASSWORD needed
        'OPTIONS': {
            'driver': 'ODBC Driver 17 for SQL Server',
            'extra_params': 'TrustServerCertificate=yes;Trusted_Connection=yes',
        },
    }
}

# Business Settings - Defaults (configurable from app settings)
BUSINESS_SETTINGS = {
    'PRIMARY_CURRENCY': 'SYP',      # ل.س Syrian Pound
    'SECONDARY_CURRENCY': 'USD',     # $ Dollar
    'EXCHANGE_RATE': 15000.0,        # 1 USD = 15000 SYP (user configurable)
    'TAX_RATE': 0.0,                 # No tax by default (0-100, user configurable)
    'TAX_ENABLED': False,            # Tax disabled by default
    'INVOICE_PREFIX': 'INV',
    'PURCHASE_ORDER_PREFIX': 'PO',
    'DECIMAL_PLACES': 2,
}

# Company Information (configurable from app settings)
COMPANY_INFO = {
    'NAME': 'شركتكم',
    'NAME_EN': 'Your Company',
    'ADDRESS': '',
    'PHONE': '',
    'TAX_NUMBER': '',
}

# CORS - Allow all for development
CORS_ALLOW_ALL_ORIGINS = True
