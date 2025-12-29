"""
Pytest configuration for frontend tests.
"""
import pytest
import sys
import os

# Add frontend to path for imports (so 'src' is a package)
frontend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if frontend_dir not in sys.path:
    sys.path.insert(0, frontend_dir)

# Configure Qt for headless testing
os.environ['QT_QPA_PLATFORM'] = 'offscreen'


@pytest.fixture(scope='session')
def qapp():
    """Create QApplication for tests."""
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def sample_invoice():
    """Sample invoice data for testing."""
    return {
        'id': 1,
        'invoice_number': 'INV-001',
        'customer_name': 'Test Customer',
        'invoice_date': '2025-01-15',
        'total_amount': '1500.00',
        'status': 'confirmed',
        'items': [
            {
                'id': 1,
                'product_name': 'Product A',
                'unit_name': 'قطعة',
                'quantity': 10,
                'unit_price': 100.0,
                'discount_percent': 0,
                'tax_rate': 0,
                'returned_quantity': 0,
                'total': 1000.0
            },
            {
                'id': 2,
                'product_name': 'Product B',
                'unit_name': 'كيلو',
                'quantity': 5,
                'unit_price': 100.0,
                'discount_percent': 10,
                'tax_rate': 5,
                'returned_quantity': 2,
                'total': 472.5
            }
        ]
    }


@pytest.fixture
def invoice_with_discount_and_tax():
    """Invoice with discount and tax for total calculation tests."""
    return {
        'id': 2,
        'invoice_number': 'INV-002',
        'customer_name': 'Test Customer 2',
        'invoice_date': '2025-01-20',
        'total_amount': '1050.00',
        'status': 'paid',
        'items': [
            {
                'id': 10,
                'product_name': 'Taxed Product',
                'unit_name': 'unit',
                'quantity': 10,
                'unit_price': 100.0,
                'discount_percent': 10,  # 10% discount
                'tax_rate': 15,  # 15% tax
                'returned_quantity': 0,
                'total': 1035.0  # (10*100 - 10%) * 1.15 = 900 * 1.15 = 1035
            }
        ]
    }
