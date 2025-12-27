"""
Tests for core utility functions.
"""
import pytest
from apps.core.utils import generate_code, generate_barcode


@pytest.mark.django_db
class TestGenerateCode:
    """Test suite for generate_code function."""
    
    def test_generate_code_with_prefix(self):
        """Test generating code with prefix."""
        code = generate_code('PRD')
        assert code.startswith('PRD')
        assert len(code) > 3
    
    def test_generate_code_with_custom_length(self):
        """Test generating code with custom length."""
        code = generate_code('CUS', 5)
        assert code.startswith('CUS-')
        # Code should be prefix + hyphen + 5 digits
        assert len(code) == 9  # 3 (CUS) + 1 (-) + 5 digits
    
    def test_generate_code_uniqueness(self):
        """Test that generated codes are unique."""
        codes = set()
        for _ in range(100):
            code = generate_code('TST')
            codes.add(code)
        
        # All codes should be unique
        assert len(codes) == 100
    
    def test_generate_code_format(self):
        """Test generated code format."""
        code = generate_code('INV')
        # Should be prefix-digits format
        assert code.startswith('INV-')
        assert code[4:].isdigit()  # After 'INV-'


@pytest.mark.django_db
class TestGenerateBarcode:
    """Test suite for generate_barcode function."""
    
    def test_generate_barcode(self):
        """Test generating barcode."""
        barcode = generate_barcode()
        assert barcode is not None
        assert len(barcode) > 0
    
    def test_generate_barcode_uniqueness(self):
        """Test that generated barcodes are unique."""
        barcodes = set()
        for _ in range(100):
            barcode = generate_barcode()
            barcodes.add(barcode)
        
        # All barcodes should be unique
        assert len(barcodes) == 100
    
    def test_generate_barcode_format(self):
        """Test generated barcode format."""
        barcode = generate_barcode()
        # Barcode should be numeric
        assert barcode.isdigit()
