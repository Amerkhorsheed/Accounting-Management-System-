"""
Unit tests for SalesReturnDialog.

Requirements: 5.3, 5.7, 5.8 - Sales Return Dialog Validation and Calculation
"""
import pytest
from decimal import Decimal


class TestSalesReturnDialogQuantityValidation:
    """
    Test quantity validation in SalesReturnDialog.
    
    Requirements: 5.3 - Validate that return quantity does not exceed 
    original quantity minus already returned quantity.
    """
    
    def test_quantity_spinner_max_is_available_quantity(self, qapp, sample_invoice):
        """Quantity spinner max should be set to available quantity."""
        from src.views.sales.returns import SalesReturnDialog
        
        dialog = SalesReturnDialog(sample_invoice)
        
        # First item: original=10, returned=0, available=10
        assert dialog.quantity_spinners[0].maximum() == 10.0
        
        # Second item: original=5, returned=2, available=3
        assert dialog.quantity_spinners[1].maximum() == 3.0
        
        dialog.close()
    
    def test_quantity_spinner_min_is_zero(self, qapp, sample_invoice):
        """Quantity spinner minimum should be 0."""
        from src.views.sales.returns import SalesReturnDialog
        
        dialog = SalesReturnDialog(sample_invoice)
        
        for spinner in dialog.quantity_spinners:
            assert spinner.minimum() == 0.0
        
        dialog.close()
    
    def test_quantity_spinner_initial_value_is_zero(self, qapp, sample_invoice):
        """Quantity spinner initial value should be 0."""
        from src.views.sales.returns import SalesReturnDialog
        
        dialog = SalesReturnDialog(sample_invoice)
        
        for spinner in dialog.quantity_spinners:
            assert spinner.value() == 0.0
        
        dialog.close()
    
    def test_validation_fails_when_no_items_selected(self, qapp, sample_invoice):
        """Validation should fail when no return quantities are set."""
        from src.views.sales.returns import SalesReturnDialog
        
        dialog = SalesReturnDialog(sample_invoice)
        
        # Set reason but no quantities
        dialog.reason_input.setPlainText("Test reason for return")
        
        # Validation should fail
        result = dialog.validate()
        assert result is False
        # Error label text should be set (visibility may vary in headless mode)
        assert dialog.error_label.text() != ""
        
        dialog.close()
    
    def test_validation_passes_with_valid_quantity(self, qapp, sample_invoice):
        """Validation should pass when valid quantity and reason are provided."""
        from src.views.sales.returns import SalesReturnDialog
        
        dialog = SalesReturnDialog(sample_invoice)
        
        # Set valid quantity and reason
        dialog.quantity_spinners[0].setValue(5.0)
        dialog.reason_input.setPlainText("Customer returned defective items")
        
        # Validation should pass
        assert dialog.validate() is True
        assert not dialog.error_label.isVisible()
        
        dialog.close()


class TestSalesReturnDialogReasonRequired:
    """
    Test reason field validation in SalesReturnDialog.
    
    Requirements: 5.8 - Reason is required for each return.
    """
    
    def test_validation_fails_without_reason(self, qapp, sample_invoice):
        """Validation should fail when reason is empty."""
        from src.views.sales.returns import SalesReturnDialog
        
        dialog = SalesReturnDialog(sample_invoice)
        
        # Set quantity but no reason
        dialog.quantity_spinners[0].setValue(5.0)
        
        # Validation should fail
        result = dialog.validate()
        assert result is False
        # Error label text should be set
        assert dialog.error_label.text() != ""
        
        dialog.close()
    
    def test_validation_fails_with_whitespace_only_reason(self, qapp, sample_invoice):
        """Validation should fail when reason is only whitespace."""
        from src.views.sales.returns import SalesReturnDialog
        
        dialog = SalesReturnDialog(sample_invoice)
        
        # Set quantity and whitespace-only reason
        dialog.quantity_spinners[0].setValue(5.0)
        dialog.reason_input.setPlainText("   ")
        
        # Validation should fail
        result = dialog.validate()
        assert result is False
        # Error label text should be set
        assert dialog.error_label.text() != ""
        
        dialog.close()
    
    def test_validation_fails_with_short_reason(self, qapp, sample_invoice):
        """Validation should fail when reason is too short (< 5 chars)."""
        from src.views.sales.returns import SalesReturnDialog
        
        dialog = SalesReturnDialog(sample_invoice)
        
        # Set quantity and short reason
        dialog.quantity_spinners[0].setValue(5.0)
        dialog.reason_input.setPlainText("bad")  # Only 3 chars
        
        # Validation should fail
        result = dialog.validate()
        assert result is False
        # Error label text should be set
        assert dialog.error_label.text() != ""
        
        dialog.close()
    
    def test_validation_passes_with_valid_reason(self, qapp, sample_invoice):
        """Validation should pass with valid reason (>= 5 chars)."""
        from src.views.sales.returns import SalesReturnDialog
        
        dialog = SalesReturnDialog(sample_invoice)
        
        # Set quantity and valid reason
        dialog.quantity_spinners[0].setValue(5.0)
        dialog.reason_input.setPlainText("Defective product")
        
        # Validation should pass
        assert dialog.validate() is True
        
        dialog.close()


class TestSalesReturnDialogTotalCalculation:
    """
    Test return total calculation in SalesReturnDialog.
    
    Requirements: 5.7 - Calculate return totals including original 
    discounts and taxes proportionally.
    """
    
    def test_line_total_calculation_no_discount_no_tax(self, qapp, sample_invoice):
        """Line total should be quantity * unit_price when no discount/tax."""
        from src.views.sales.returns import SalesReturnDialog
        
        dialog = SalesReturnDialog(sample_invoice)
        
        # First item: unit_price=100, discount=0%, tax=0%
        dialog.quantity_spinners[0].setValue(3.0)
        
        # Expected: 3 * 100 = 300
        line_total_text = dialog.items_table.item(0, 6).text()
        assert '300' in line_total_text.replace(',', '')
        
        dialog.close()
    
    def test_line_total_calculation_with_discount_and_tax(self, qapp, sample_invoice):
        """Line total should apply discount then tax correctly."""
        from src.views.sales.returns import SalesReturnDialog
        
        dialog = SalesReturnDialog(sample_invoice)
        
        # Second item: unit_price=100, discount=10%, tax=5%
        # For quantity=2: subtotal=200, discount=20, taxable=180, tax=9, total=189
        dialog.quantity_spinners[1].setValue(2.0)
        
        line_total_text = dialog.items_table.item(1, 6).text()
        # Should be 189.00
        assert '189' in line_total_text.replace(',', '')
        
        dialog.close()
    
    def test_grand_total_calculation(self, qapp, sample_invoice):
        """Grand total should sum all line totals correctly."""
        from src.views.sales.returns import SalesReturnDialog
        
        dialog = SalesReturnDialog(sample_invoice)
        
        # Set quantities for both items
        dialog.quantity_spinners[0].setValue(2.0)  # 2 * 100 = 200
        dialog.quantity_spinners[1].setValue(1.0)  # 1 * 100 * 0.9 * 1.05 = 94.5
        
        # Expected total: 200 + 94.5 = 294.5
        total_text = dialog.return_total_label.text()
        assert '294' in total_text.replace(',', '')
        
        dialog.close()
    
    def test_total_updates_when_quantity_changes(self, qapp, sample_invoice):
        """Total should update when quantity spinner value changes."""
        from src.views.sales.returns import SalesReturnDialog
        
        dialog = SalesReturnDialog(sample_invoice)
        
        # Initial total should be 0
        initial_total = dialog.return_total_label.text()
        assert '0' in initial_total
        
        # Set quantity
        dialog.quantity_spinners[0].setValue(5.0)
        
        # Total should update
        updated_total = dialog.return_total_label.text()
        assert '500' in updated_total.replace(',', '')
        
        dialog.close()
    
    def test_subtotal_and_tax_displayed_separately(self, qapp, invoice_with_discount_and_tax):
        """Subtotal and tax should be displayed separately."""
        from src.views.sales.returns import SalesReturnDialog
        
        dialog = SalesReturnDialog(invoice_with_discount_and_tax)
        
        # Return 5 items: 5 * 100 = 500, discount 10% = 450, tax 15% = 67.5
        # Total = 517.5
        dialog.quantity_spinners[0].setValue(5.0)
        
        subtotal_text = dialog.return_subtotal_label.text()
        tax_text = dialog.return_tax_label.text()
        total_text = dialog.return_total_label.text()
        
        # Subtotal should be 450 (after discount, before tax)
        assert '450' in subtotal_text.replace(',', '')
        
        # Tax should be 67.5
        assert '67' in tax_text.replace(',', '')
        
        # Total should be 517.5
        assert '517' in total_text.replace(',', '')
        
        dialog.close()


class TestSalesReturnDialogGetReturnData:
    """Test get_return_data method returns correct structure."""
    
    def test_return_data_structure(self, qapp, sample_invoice):
        """get_return_data should return correct structure."""
        from src.views.sales.returns import SalesReturnDialog
        
        dialog = SalesReturnDialog(sample_invoice)
        
        # Set up return
        dialog.quantity_spinners[0].setValue(3.0)
        dialog.reason_input.setPlainText("Test return reason")
        dialog.notes_input.setPlainText("Additional notes")
        
        data = dialog.get_return_data()
        
        # Check structure
        assert 'return_date' in data
        assert 'reason' in data
        assert 'notes' in data
        assert 'items' in data
        
        # Check values
        assert data['reason'] == "Test return reason"
        assert data['notes'] == "Additional notes"
        assert len(data['items']) == 1  # Only one item has quantity > 0
        
        # Check item structure
        item = data['items'][0]
        assert item['invoice_item_id'] == 1
        assert item['quantity'] == '3.0'
        assert item['reason'] == "Test return reason"
        
        dialog.close()
    
    def test_return_data_excludes_zero_quantity_items(self, qapp, sample_invoice):
        """get_return_data should exclude items with zero quantity."""
        from src.views.sales.returns import SalesReturnDialog
        
        dialog = SalesReturnDialog(sample_invoice)
        
        # Only set quantity for first item
        dialog.quantity_spinners[0].setValue(2.0)
        dialog.quantity_spinners[1].setValue(0.0)
        dialog.reason_input.setPlainText("Test reason")
        
        data = dialog.get_return_data()
        
        # Should only have one item
        assert len(data['items']) == 1
        assert data['items'][0]['invoice_item_id'] == 1
        
        dialog.close()
