"""
Application Configuration
"""
import os
from dataclasses import dataclass, field
from typing import Optional, Dict
from decimal import Decimal


@dataclass
class CurrencyConfig:
    """Currency configuration."""
    code: str = 'SYP'
    name: str = 'الليرة السورية'
    symbol: str = 'ل.س'
    exchange_rate: float = 1.0
    decimal_places: int = 0


@dataclass
class AppConfig:
    """Application configuration settings."""
    
    # API Settings
    API_BASE_URL: str = os.getenv('API_BASE_URL', 'http://localhost:8000/api/v1')
    API_TIMEOUT: int = 30
    
    # Currency Settings (Multi-currency support)
    PRIMARY_CURRENCY: CurrencyConfig = field(default_factory=lambda: CurrencyConfig(
        code='SYP',
        name='الليرة السورية',
        symbol='ل.س',
        exchange_rate=1.0,
        decimal_places=0
    ))
    SECONDARY_CURRENCY: CurrencyConfig = field(default_factory=lambda: CurrencyConfig(
        code='USD',
        name='الدولار الأمريكي',
        symbol='$',
        exchange_rate=15000.0,  # 1 USD = 15000 SYP (user configurable)
        decimal_places=2
    ))
    
    # Tax Settings (Configurable - can be 0 for no tax)
    TAX_RATE: float = 0.0  # No tax by default
    TAX_ENABLED: bool = False  # User configurable
    
    # Company Info
    COMPANY_NAME: str = 'شركتكم'
    COMPANY_NAME_EN: str = 'Your Company'
    COMPANY_ADDRESS: str = ''
    COMPANY_PHONE: str = ''
    COMPANY_TAX_NUMBER: str = ''
    
    # Printer Settings
    DEFAULT_PRINTER: Optional[str] = None
    RECEIPT_PRINTER: Optional[str] = None
    RECEIPT_WIDTH: int = 80  # mm (58 or 80)
    
    # UI Settings
    THEME: str = 'light'  # 'light' or 'dark'
    SIDEBAR_WIDTH: int = 250
    
    # Paths
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    RESOURCES_DIR: str = os.path.join(BASE_DIR, 'src', 'resources')
    
    def format_currency(self, amount: float, currency: str = None) -> str:
        """Format amount with currency symbol."""
        if currency == 'USD' or currency == '$':
            return f"${amount:,.2f}"
        else:
            return f"{amount:,.0f} ل.س"
    
    def convert_to_primary(self, amount: float, from_currency: str = 'USD') -> float:
        """Convert amount to primary currency (SYP)."""
        if from_currency == 'USD':
            return amount * self.SECONDARY_CURRENCY.exchange_rate
        return amount
    
    def convert_to_secondary(self, amount: float) -> float:
        """Convert amount from primary (SYP) to secondary (USD)."""
        if self.SECONDARY_CURRENCY.exchange_rate > 0:
            return amount / self.SECONDARY_CURRENCY.exchange_rate
        return amount
    
    def update_exchange_rate(self, rate: float):
        """Update USD/SYP exchange rate."""
        self.SECONDARY_CURRENCY.exchange_rate = rate
    
    def save_settings(self):
        """Save settings to JSON file for persistence."""
        import json
        settings_file = os.path.join(self.BASE_DIR, 'settings.json')
        settings_data = {
            'API_BASE_URL': self.API_BASE_URL,
            'COMPANY_NAME': self.COMPANY_NAME,
            'COMPANY_NAME_EN': self.COMPANY_NAME_EN,
            'COMPANY_ADDRESS': self.COMPANY_ADDRESS,
            'COMPANY_PHONE': self.COMPANY_PHONE,
            'COMPANY_TAX_NUMBER': self.COMPANY_TAX_NUMBER,
            'TAX_RATE': self.TAX_RATE,
            'TAX_ENABLED': self.TAX_ENABLED,
            'EXCHANGE_RATE': self.SECONDARY_CURRENCY.exchange_rate,
            'DEFAULT_PRINTER': self.DEFAULT_PRINTER,
            'RECEIPT_PRINTER': self.RECEIPT_PRINTER,
            'RECEIPT_WIDTH': self.RECEIPT_WIDTH,
            'THEME': self.THEME,
        }
        try:
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False
    
    def load_settings(self):
        """Load settings from JSON file."""
        import json
        settings_file = os.path.join(self.BASE_DIR, 'settings.json')
        try:
            if os.path.exists(settings_file):
                with open(settings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.API_BASE_URL = data.get('API_BASE_URL', self.API_BASE_URL)
                self.COMPANY_NAME = data.get('COMPANY_NAME', self.COMPANY_NAME)
                self.COMPANY_NAME_EN = data.get('COMPANY_NAME_EN', self.COMPANY_NAME_EN)
                self.COMPANY_ADDRESS = data.get('COMPANY_ADDRESS', self.COMPANY_ADDRESS)
                self.COMPANY_PHONE = data.get('COMPANY_PHONE', self.COMPANY_PHONE)
                self.COMPANY_TAX_NUMBER = data.get('COMPANY_TAX_NUMBER', self.COMPANY_TAX_NUMBER)
                self.TAX_RATE = data.get('TAX_RATE', self.TAX_RATE)
                self.TAX_ENABLED = data.get('TAX_ENABLED', self.TAX_ENABLED)
                self.SECONDARY_CURRENCY.exchange_rate = data.get('EXCHANGE_RATE', self.SECONDARY_CURRENCY.exchange_rate)
                self.DEFAULT_PRINTER = data.get('DEFAULT_PRINTER', self.DEFAULT_PRINTER)
                self.RECEIPT_PRINTER = data.get('RECEIPT_PRINTER', self.RECEIPT_PRINTER)
                self.RECEIPT_WIDTH = data.get('RECEIPT_WIDTH', self.RECEIPT_WIDTH)
                self.THEME = data.get('THEME', self.THEME)
                return True
        except Exception as e:
            print(f"Error loading settings: {e}")
        return False


# Global config instance
config = AppConfig()
# Load saved settings on startup
config.load_settings()


# Constants
class Icons:
    """Icon names/paths."""
    DASHBOARD = 'dashboard'
    PRODUCTS = 'products'
    INVENTORY = 'inventory'
    SALES = 'sales'
    PURCHASES = 'purchases'
    CUSTOMERS = 'customers'
    SUPPLIERS = 'suppliers'
    EXPENSES = 'expenses'
    REPORTS = 'reports'
    SETTINGS = 'settings'
    LOGOUT = 'logout'
    ADD = 'add'
    EDIT = 'edit'
    DELETE = 'delete'
    SEARCH = 'search'
    PRINT = 'print'
    BARCODE = 'barcode'
    SAVE = 'save'
    CANCEL = 'cancel'
    REFRESH = 'refresh'


class Colors:
    """Color palette - Professional, Clear & Vibrant."""
    # Primary - Sophisticated Blue
    PRIMARY = '#2563EB'
    PRIMARY_DARK = '#1D4ED8'
    PRIMARY_LIGHT = '#60A5FA'
    
    # Secondary - Refined Teal
    SECONDARY = '#0D9488'
    SECONDARY_DARK = '#0F766E'
    
    # Accent - Warm Amber
    ACCENT = '#F59E0B'
    
    # Status Colors - Tailwind-style
    SUCCESS = '#10B981'
    WARNING = '#F59E0B'
    DANGER = '#EF4444'
    INFO = '#3B82F6'
    
    # Sidebar Colors - Light
    SIDEBAR_BG_LIGHT = '#F1F5F9'    # Slate 100
    SIDEBAR_TEXT_LIGHT = '#0F172A'  # Slate 900
    SIDEBAR_HOVER_LIGHT = '#E2E8F0' # Slate 200
    
    # Sidebar Colors - Dark
    SIDEBAR_BG_DARK = '#1E293B'     # Slate 800
    SIDEBAR_TEXT_DARK = '#F1F5F9'   # Slate 100
    SIDEBAR_HOVER_DARK = '#334155'  # Slate 700
    
    SIDEBAR_ACTIVE = '#2563EB'      # Blue 600 (Shared active color)
    
    # Light theme - High Contrast & Clean
    LIGHT_BG = '#F8FAFC'           # Slate 50
    LIGHT_CARD = '#FFFFFF'         # Pure White
    LIGHT_BORDER = '#E2E8F0'       # Slate 200
    LIGHT_TEXT = '#0F172A'         # Slate 900
    LIGHT_TEXT_SECONDARY = '#475467'  # Gray 600
    
    # Dark theme - Deep & Readable
    DARK_BG = '#0F172A'            # Slate 900
    DARK_CARD = '#1E293B'          # Slate 800
    DARK_BORDER = '#334155'        # Slate 700
    DARK_TEXT = '#F8FAFC'          # Slate 50
    DARK_TEXT_SECONDARY = '#94A3B8'  # Slate 400
    
    # Table Colors (Light)
    TABLE_HEADER_LIGHT = '#F1F5F9'
    TABLE_ROW_ALT_LIGHT = '#F8FAFC'
    TABLE_HOVER_LIGHT = '#EFF6FF'
    
    # Table Colors (Dark)
    TABLE_HEADER_DARK = '#1E293B'
    TABLE_ROW_ALT_DARK = '#151B2B'
    TABLE_HOVER_DARK = '#26314D'
    
    # Input Colors
    INPUT_BG_LIGHT = '#FFFFFF'
    INPUT_BG_DARK = '#1E293B'
    INPUT_BORDER_LIGHT = '#D1D5DB'
    INPUT_BORDER_DARK = '#334155'
    INPUT_FOCUS = '#2563EB'
    INPUT_PLACEHOLDER = '#94A3B8'


class Fonts:
    """Font settings."""
    FAMILY_AR = 'Segoe UI'
    FAMILY_EN = 'Segoe UI'
    FAMILY_MONO = 'Consolas'
    
    SIZE_H1 = 24
    SIZE_H2 = 20
    SIZE_H3 = 16
    SIZE_BODY = 12
    SIZE_SMALL = 10
