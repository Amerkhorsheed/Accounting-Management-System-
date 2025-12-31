# Implementation Plan: Invoice Remove Button Enhancement

## Overview

This implementation enhances the existing remove button functionality in the invoice products table by improving its visual styling, hover effects, and user experience. The changes focus on the `update_items_table()` method in `frontend/src/views/sales/__init__.py`.

## Tasks

- [x] 1. Enhance remove button styling and appearance
  - Update the delete button styling with improved hover effects
  - Add danger color constants if not already present
  - Increase button size from 30x30 to 32x32 pixels for better clickability
  - Add Arabic tooltip "حذف المنتج" to the remove button
  - _Requirements: 1.1, 1.2, 1.4, 2.1, 2.2_

- [ ]* 1.1 Write property test for remove button presence
  - **Property 1: Remove Button Presence**
  - **Validates: Requirements 1.1, 1.2**

- [ ]* 1.2 Write property test for remove button size
  - **Property 2: Remove Button Size**
  - **Validates: Requirements 1.4**

- [x] 2. Optimize table column configuration for remove buttons
  - Increase the remove button column width from 40 to 50 pixels
  - Update column header to "حذف" for better clarity
  - Ensure proper column resize mode for the remove button column
  - _Requirements: 2.4_

- [x] 3. Verify and test remove functionality
  - Test the existing remove_item() method works correctly
  - Ensure proper index handling and bounds checking
  - Verify table updates correctly after item removal
  - _Requirements: 3.1, 3.2_

- [ ]* 3.1 Write property test for remove functionality
  - **Property 3: Remove Functionality**
  - **Validates: Requirements 3.1**

- [ ]* 3.2 Write property test for table update after removal
  - **Property 4: Table Update After Removal**
  - **Validates: Requirements 3.2**

- [x] 4. Verify totals recalculation after removal
  - Ensure invoice totals update correctly when items are removed
  - Test that subtotal, tax, and grand total calculations are accurate
  - _Requirements: 3.3_

- [ ]* 4.1 Write property test for totals recalculation
  - **Property 5: Totals Recalculation**
  - **Validates: Requirements 3.3**

- [ ] 5. Test position-independent removal functionality
  - Verify remove buttons work for items in any position (first, middle, last)
  - Test with multiple items to ensure correct item is removed
  - _Requirements: 3.4_

- [ ]* 5.1 Write property test for position-independent removal
  - **Property 6: Position-Independent Removal**
  - **Validates: Requirements 3.4**

- [ ] 6. Checkpoint - Manual verification and testing
  - Test the enhanced remove button styling and hover effects
  - Verify all remove functionality works correctly
  - Test with multiple products to ensure proper behavior
  - Ensure tooltips appear correctly in Arabic

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- All changes are in `frontend/src/views/sales/__init__.py` in the `InvoiceFormDialog` class
- The core remove functionality already exists and works - this enhancement focuses on improving the user experience
- Manual testing is required to verify visual appearance and hover effects
- Property tests validate the functional correctness of the remove operations