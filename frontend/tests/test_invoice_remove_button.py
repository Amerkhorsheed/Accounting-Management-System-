"""
Unit tests for InvoiceFormDialog remove button functionality.

Requirements: 3.1, 3.2 - Remove functionality and table updates
"""
import pytest
from unittest.mock import patch, MagicMock


class TestInvoiceFormDialogRemoveItem:
    """
    Test remove_item functionality in InvoiceFormDialog.
    
    Requirements: 3.1 - WHEN a user clicks the Remove_Button, THE system SHALL 
    immediately remove the corresponding product from the invoice.
    Requirements: 3.2 - WHEN a product is removed, THE Products_Table SHALL 
    update to show the remaining products.
    """
    
    @pytest.fixture
    def mock_api_responses(self):
        """Mock API responses for dialog initialization."""
        return {
            'customers': [
                {'id': 1, 'name': 'Test Customer', 'credit_limit': 1000}
            ],
            'warehouses': [
                {'id': 1, 'name': 'Main Warehouse'}
            ],
            'products': [
                {'id': 1, 'name': 'Product A', 'price': 100.0, 'is_taxable': False},
                {'id': 2, 'name': 'Product B', 'price': 200.0, 'is_taxable': False},
                {'id': 3, 'name': 'Product C', 'price': 150.0, 'is_taxable': False}
            ]
        }
    
    @pytest.fixture
    def sample_items(self):
        """Sample items for testing."""
        return [
            {
                'product': 1,
                'product_name': 'Product A',
                'unit_name': 'قطعة',
                'quantity': 5,
                'unit_price': 100.0,
                'total': 500.0
            },
            {
                'product': 2,
                'product_name': 'Product B',
                'unit_name': 'كيلو',
                'quantity': 3,
                'unit_price': 200.0,
                'total': 600.0
            },
            {
                'product': 3,
                'product_name': 'Product C',
                'unit_name': 'علبة',
                'quantity': 2,
                'unit_price': 150.0,
                'total': 300.0
            }
        ]
    
    @pytest.fixture
    def invoice_dialog(self, qapp, mock_api_responses):
        """Create InvoiceFormDialog with mocked API calls."""
        with patch('src.views.sales.api') as mock_api:
            # Mock API responses
            mock_api.get_customers.return_value = mock_api_responses['customers']
            mock_api.get_warehouses.return_value = mock_api_responses['warehouses']
            mock_api.get_products.return_value = mock_api_responses['products']
            
            from src.views.sales import InvoiceFormDialog
            dialog = InvoiceFormDialog()
            dialog.products_cache = mock_api_responses['products']
            yield dialog
            dialog.close()
    
    def test_remove_item_decreases_items_count(self, invoice_dialog, sample_items):
        """
        Removing an item should decrease the items list length by one.
        Requirements: 3.1
        """
        # Add items to the dialog
        invoice_dialog.items = sample_items.copy()
        initial_count = len(invoice_dialog.items)
        
        # Remove the first item
        invoice_dialog.remove_item(0)
        
        # Verify count decreased by 1
        assert len(invoice_dialog.items) == initial_count - 1
    
    def test_remove_item_removes_correct_item(self, invoice_dialog, sample_items):
        """
        Removing an item should remove the correct item from the list.
        Requirements: 3.1
        """
        # Add items to the dialog
        invoice_dialog.items = sample_items.copy()
        
        # Get the product name of the item to be removed
        item_to_remove = invoice_dialog.items[1]['product_name']
        
        # Remove the second item (index 1)
        invoice_dialog.remove_item(1)
        
        # Verify the removed item is no longer in the list
        remaining_names = [item['product_name'] for item in invoice_dialog.items]
        assert item_to_remove not in remaining_names
    
    def test_remove_item_updates_table_row_count(self, invoice_dialog, sample_items):
        """
        After removal, table row count should match items list length.
        Requirements: 3.2
        """
        # Add items to the dialog
        invoice_dialog.items = sample_items.copy()
        invoice_dialog.update_items_table()
        
        # Remove an item
        invoice_dialog.remove_item(0)
        
        # Verify table row count matches items list length
        assert invoice_dialog.items_table.rowCount() == len(invoice_dialog.items)
    
    def test_remove_item_with_invalid_negative_index(self, invoice_dialog, sample_items):
        """
        Removing with negative index should not modify the list.
        Requirements: 3.1 - Bounds checking
        """
        # Add items to the dialog
        invoice_dialog.items = sample_items.copy()
        initial_count = len(invoice_dialog.items)
        
        # Try to remove with negative index
        invoice_dialog.remove_item(-1)
        
        # Verify list is unchanged
        assert len(invoice_dialog.items) == initial_count
    
    def test_remove_item_with_out_of_bounds_index(self, invoice_dialog, sample_items):
        """
        Removing with out-of-bounds index should not modify the list.
        Requirements: 3.1 - Bounds checking
        """
        # Add items to the dialog
        invoice_dialog.items = sample_items.copy()
        initial_count = len(invoice_dialog.items)
        
        # Try to remove with out-of-bounds index
        invoice_dialog.remove_item(100)
        
        # Verify list is unchanged
        assert len(invoice_dialog.items) == initial_count
    
    def test_remove_item_from_empty_list(self, invoice_dialog):
        """
        Removing from empty list should not raise an error.
        Requirements: 3.1 - Bounds checking
        """
        # Ensure items list is empty
        invoice_dialog.items = []
        
        # Try to remove from empty list - should not raise
        invoice_dialog.remove_item(0)
        
        # Verify list is still empty
        assert len(invoice_dialog.items) == 0
    
    def test_remove_first_item(self, invoice_dialog, sample_items):
        """
        Removing the first item should work correctly.
        Requirements: 3.1
        """
        # Add items to the dialog
        invoice_dialog.items = sample_items.copy()
        first_item_name = invoice_dialog.items[0]['product_name']
        second_item_name = invoice_dialog.items[1]['product_name']
        
        # Remove first item
        invoice_dialog.remove_item(0)
        
        # Verify first item is removed and second item is now first
        assert invoice_dialog.items[0]['product_name'] == second_item_name
        assert first_item_name not in [item['product_name'] for item in invoice_dialog.items]
    
    def test_remove_last_item(self, invoice_dialog, sample_items):
        """
        Removing the last item should work correctly.
        Requirements: 3.1
        """
        # Add items to the dialog
        invoice_dialog.items = sample_items.copy()
        last_index = len(invoice_dialog.items) - 1
        last_item_name = invoice_dialog.items[last_index]['product_name']
        
        # Remove last item
        invoice_dialog.remove_item(last_index)
        
        # Verify last item is removed
        assert last_item_name not in [item['product_name'] for item in invoice_dialog.items]
        assert len(invoice_dialog.items) == 2
    
    def test_remove_middle_item(self, invoice_dialog, sample_items):
        """
        Removing a middle item should work correctly.
        Requirements: 3.1
        """
        # Add items to the dialog
        invoice_dialog.items = sample_items.copy()
        middle_item_name = invoice_dialog.items[1]['product_name']
        first_item_name = invoice_dialog.items[0]['product_name']
        last_item_name = invoice_dialog.items[2]['product_name']
        
        # Remove middle item
        invoice_dialog.remove_item(1)
        
        # Verify middle item is removed, first and last remain
        remaining_names = [item['product_name'] for item in invoice_dialog.items]
        assert middle_item_name not in remaining_names
        assert first_item_name in remaining_names
        assert last_item_name in remaining_names
    
    def test_remove_all_items_sequentially(self, invoice_dialog, sample_items):
        """
        Removing all items one by one should result in empty list.
        Requirements: 3.1, 3.2
        """
        # Add items to the dialog
        invoice_dialog.items = sample_items.copy()
        
        # Remove all items (always remove first item)
        while invoice_dialog.items:
            invoice_dialog.remove_item(0)
        
        # Verify list is empty
        assert len(invoice_dialog.items) == 0
        assert invoice_dialog.items_table.rowCount() == 0


class TestInvoiceFormDialogTotalsRecalculation:
    """
    Test totals recalculation after item removal in InvoiceFormDialog.
    
    Requirements: 3.3 - WHEN a product is removed, THE invoice totals SHALL 
    recalculate automatically.
    """
    
    @pytest.fixture
    def mock_api_responses(self):
        """Mock API responses for dialog initialization."""
        return {
            'customers': [
                {'id': 1, 'name': 'Test Customer', 'credit_limit': 1000}
            ],
            'warehouses': [
                {'id': 1, 'name': 'Main Warehouse'}
            ],
            'products': [
                {'id': 1, 'name': 'Product A', 'sale_price': 100.0, 'is_taxable': False},
                {'id': 2, 'name': 'Product B', 'sale_price': 200.0, 'is_taxable': True, 'tax_rate': 15},
                {'id': 3, 'name': 'Product C', 'sale_price': 150.0, 'is_taxable': False}
            ]
        }
    
    @pytest.fixture
    def sample_items_with_totals(self):
        """Sample items with calculated totals for testing."""
        return [
            {
                'product': 1,
                'product_name': 'Product A',
                'unit_name': 'قطعة',
                'quantity': 5,
                'unit_price': 100.0,
                'total': 500.0  # 5 * 100
            },
            {
                'product': 2,
                'product_name': 'Product B',
                'unit_name': 'كيلو',
                'quantity': 3,
                'unit_price': 200.0,
                'total': 600.0  # 3 * 200
            },
            {
                'product': 3,
                'product_name': 'Product C',
                'unit_name': 'علبة',
                'quantity': 2,
                'unit_price': 150.0,
                'total': 300.0  # 2 * 150
            }
        ]
    
    @pytest.fixture
    def invoice_dialog(self, qapp, mock_api_responses):
        """Create InvoiceFormDialog with mocked API calls."""
        with patch('src.views.sales.api') as mock_api:
            # Mock API responses
            mock_api.get_customers.return_value = mock_api_responses['customers']
            mock_api.get_warehouses.return_value = mock_api_responses['warehouses']
            mock_api.get_products.return_value = mock_api_responses['products']
            
            from src.views.sales import InvoiceFormDialog
            dialog = InvoiceFormDialog()
            dialog.products_cache = mock_api_responses['products']
            yield dialog
            dialog.close()
    
    def test_subtotal_recalculates_after_removal(self, invoice_dialog, sample_items_with_totals):
        """
        Subtotal should recalculate correctly after item removal.
        Requirements: 3.3
        """
        # Add items to the dialog
        invoice_dialog.items = sample_items_with_totals.copy()
        invoice_dialog.update_items_table()
        
        # Initial subtotal: 500 + 600 + 300 = 1400
        initial_subtotal = sum(item['total'] for item in invoice_dialog.items)
        assert initial_subtotal == 1400.0
        
        # Remove first item (total: 500)
        invoice_dialog.remove_item(0)
        
        # New subtotal should be 600 + 300 = 900
        new_subtotal = sum(item['total'] for item in invoice_dialog.items)
        assert new_subtotal == 900.0
        
        # Verify the displayed subtotal matches
        displayed_subtotal = invoice_dialog.subtotal_value.text()
        assert "900" in displayed_subtotal.replace(",", "")
    
    def test_grand_total_recalculates_after_removal(self, invoice_dialog, sample_items_with_totals):
        """
        Grand total should recalculate correctly after item removal.
        Requirements: 3.3
        """
        # Add items to the dialog
        invoice_dialog.items = sample_items_with_totals.copy()
        invoice_dialog.update_items_table()
        
        # Remove the second item (Product B with tax)
        invoice_dialog.remove_item(1)
        
        # Remaining items: Product A (500) + Product C (300) = 800
        # No tax since remaining products are not taxable
        expected_subtotal = 800.0
        
        # Verify subtotal
        actual_subtotal = sum(item['total'] for item in invoice_dialog.items)
        assert actual_subtotal == expected_subtotal
    
    def test_totals_zero_after_all_items_removed(self, invoice_dialog, sample_items_with_totals):
        """
        Totals should be zero after all items are removed.
        Requirements: 3.3
        """
        # Add items to the dialog
        invoice_dialog.items = sample_items_with_totals.copy()
        invoice_dialog.update_items_table()
        
        # Remove all items
        while invoice_dialog.items:
            invoice_dialog.remove_item(0)
        
        # Verify totals are zero
        subtotal, tax, grand_total = invoice_dialog._calculate_totals()
        assert subtotal == 0.0
        assert tax == 0.0
        assert grand_total == 0.0
        
        # Verify displayed values show zero
        assert "0" in invoice_dialog.subtotal_value.text()
        assert "0" in invoice_dialog.total_value.text()
    
    def test_calculate_totals_returns_correct_values(self, invoice_dialog, sample_items_with_totals, mock_api_responses):
        """
        _calculate_totals should return correct subtotal, tax, and grand_total.
        Requirements: 3.3
        """
        # Add items to the dialog
        invoice_dialog.items = sample_items_with_totals.copy()
        
        # Calculate totals
        subtotal, tax, grand_total = invoice_dialog._calculate_totals()
        
        # Expected subtotal: 500 + 600 + 300 = 1400
        assert subtotal == 1400.0
        
        # Expected tax: Only Product B is taxable (600 * 0.15 = 90)
        assert tax == 90.0
        
        # Expected grand total: 1400 + 90 = 1490
        assert grand_total == 1490.0
    
    def test_totals_update_after_removing_taxable_item(self, invoice_dialog, sample_items_with_totals, mock_api_responses):
        """
        Tax should recalculate correctly after removing a taxable item.
        Requirements: 3.3
        """
        # Add items to the dialog
        invoice_dialog.items = sample_items_with_totals.copy()
        invoice_dialog.update_items_table()
        
        # Initial tax from Product B (taxable): 600 * 0.15 = 90
        initial_subtotal, initial_tax, initial_grand = invoice_dialog._calculate_totals()
        assert initial_tax == 90.0
        
        # Remove Product B (index 1, the taxable item)
        invoice_dialog.remove_item(1)
        
        # After removal, no taxable items remain
        new_subtotal, new_tax, new_grand = invoice_dialog._calculate_totals()
        assert new_tax == 0.0
        assert new_subtotal == 800.0  # 500 + 300
        assert new_grand == 800.0  # No tax
    
    def test_remaining_amount_updates_after_removal(self, invoice_dialog, sample_items_with_totals):
        """
        Remaining amount calculation should work correctly after item removal.
        Requirements: 3.3
        """
        # Add items to the dialog
        invoice_dialog.items = sample_items_with_totals.copy()
        invoice_dialog.update_items_table()
        
        # Get initial totals
        initial_subtotal, initial_tax, initial_grand = invoice_dialog._calculate_totals()
        
        # Remove first item (500)
        invoice_dialog.remove_item(0)
        
        # Get new totals after removal
        new_subtotal, new_tax, new_grand = invoice_dialog._calculate_totals()
        
        # Verify totals decreased after removal
        assert new_grand < initial_grand
        
        # Verify the remaining amount calculation is consistent
        # The remaining amount should be grand_total - paid_amount (capped at 0)
        paid = invoice_dialog.paid_amount_spin.value()
        calculated_remaining = max(0, new_grand - paid)
        
        # The remaining value label should reflect the calculated remaining
        remaining_text = invoice_dialog.remaining_value.text()
        # Extract numeric value from text (format: "X,XXX.XX ل.س")
        remaining_numeric = float(remaining_text.replace(",", "").replace("ل.س", "").strip())
        
        assert abs(remaining_numeric - calculated_remaining) < 0.01  # Allow small floating point tolerance
