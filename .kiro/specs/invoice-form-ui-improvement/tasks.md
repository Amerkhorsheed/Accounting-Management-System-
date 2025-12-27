# Implementation Plan: Invoice Form UI Improvement

## Overview

This implementation restructures the InvoiceFormDialog layout to maximize the products table visibility and enable smooth scrolling. The changes are focused on the `setup_ui()` method in `frontend/src/views/sales/__init__.py`.

## Tasks

- [x] 1. Restructure the Invoice Header Card for compact layout
  - Reduce card padding from 20px to 12px
  - Arrange all fields (customer, warehouse, date, due date) in a single row
  - Set maximum height constraint of 100px on the header card
  - _Requirements: 3.1, 3.2, 3.3_

- [x] 2. Compact the Product Entry Section
  - Combine barcode input and manual product selection into a single row
  - Remove the "أو اختر من القائمة" separator label
  - Reduce spacing between elements to 8px
  - Set maximum height constraint of 70px on the entry section
  - _Requirements: 4.1, 4.2, 4.3_

- [x] 3. Optimize the Products Table for expansion and scrolling
  - Remove the `setMaximumHeight(400)` constraint from items_table
  - Set minimum height to 300px
  - Add stretch factor to allow table to expand and fill available space
  - Ensure vertical scrollbar policy is set to show when needed
  - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 2.4_

- [x] 4. Implement auto-scroll to newly added products
  - Modify `update_items_table()` method to scroll to the last row after adding items
  - Use `scrollToItem()` or `scrollToBottom()` to ensure new items are visible
  - _Requirements: 2.3_

- [x] 5. Optimize the Summary Card layout
  - Set fixed width of 320px on the summary card
  - Reduce internal spacing and padding
  - Adjust the content layout ratio (left column 7:1 right column → 8:1)
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [x] 6. Enhance visual styling of the Products Table
  - Add distinct border or shadow to emphasize the table
  - Ensure header row has contrasting background
  - Verify alternating row colors are applied
  - _Requirements: 6.1, 6.2, 6.3_

- [x] 7. Checkpoint - Manual verification
  - Test adding 10+ products and verify scrolling works
  - Verify layout looks correct at different window sizes
  - Ensure all existing functionality still works (save, cancel, totals calculation)

## Notes

- All changes are in `frontend/src/views/sales/__init__.py` in the `InvoiceFormDialog` class
- This is a UI-only change with no backend modifications
- Manual testing is required to verify visual appearance
