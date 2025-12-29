# Implementation Plan: POS Improvements

## Overview

This implementation plan covers the improvements to the Point of Sale (نقطة البيع) system including full cash payment, tax-free transactions, and receipt printing functionality.

## Tasks

- [x] 1. Modify POSView for tax-free transactions
  - [x] 1.1 Update `update_totals()` to always display tax as 0.00
    - Modify the tax calculation to always return 0 for POS
    - Update `self.tax_label` to show "0.00 ل.س"
    - _Requirements: 2.1, 2.2_
  - [x] 1.2 Update `create_pos_invoice()` to send tax_rate=0 for all items
    - Remove dependency on `config.TAX_ENABLED` and `config.TAX_RATE`
    - Hardcode `tax_rate: 0` for all items in invoice_data
    - _Requirements: 2.1, 2.3_
  - [ ]* 1.3 Write property test for tax-free POS transactions
    - **Property 2: POS Transactions Are Tax-Free**
    - **Validates: Requirements 2.1, 2.2, 2.3**

- [x] 2. Implement full cash payment functionality
  - [x] 2.1 Update `create_pos_invoice()` for cash payments
    - Set `paid_amount` equal to cart total for cash payments
    - Ensure invoice is marked as fully paid
    - _Requirements: 1.1, 1.2_
  - [x] 2.2 Add `last_completed_invoice` attribute to store invoice data
    - Initialize as `None` in `__init__`
    - Store API response after successful invoice creation
    - _Requirements: 4.1_
  - [ ]* 2.3 Write property test for cash payment creates fully paid invoice
    - **Property 1: Cash Payment Creates Fully Paid Invoice**
    - **Validates: Requirements 1.1, 1.2**
  - [ ]* 2.4 Write property test for cart cleared after payment
    - **Property 3: Cart Cleared After Successful Payment**
    - **Validates: Requirements 1.4**

- [x] 3. Implement print button functionality
  - [x] 3.1 Create `print_receipt()` method in POSView
    - Check if `last_completed_invoice` exists
    - Show warning if no invoice available
    - Call `ReceiptPrinter.print_receipt()` with invoice data
    - Handle print errors gracefully
    - _Requirements: 3.1, 4.2, 4.3, 4.4_
  - [x] 3.2 Connect print button to `print_receipt()` method
    - Add click handler to print button in `setup_ui()`
    - _Requirements: 3.1_
  - [ ]* 3.3 Write property test for last invoice stored for printing
    - **Property 5: Last Invoice Stored for Printing**
    - **Validates: Requirements 4.1**

- [x] 4. Update ReceiptPrinter for POS receipts
  - [x] 4.1 Modify `generate()` to handle tax-free receipts
    - Show tax line as "0.00" when tax_amount is 0
    - Remove "15%" from tax label for POS receipts
    - _Requirements: 2.4_
  - [x] 4.2 Ensure receipt includes all required information
    - Verify company info, invoice details, items, totals are included
    - _Requirements: 3.2, 3.3, 3.4, 3.5, 3.6_
  - [ ]* 4.3 Write property test for receipt contains required information
    - **Property 4: Receipt Contains Required Information**
    - **Validates: Requirements 3.2, 3.3, 3.4, 3.5, 3.6**

- [x] 5. Implement cash drawer integration (optional)
  - [x] 5.1 Call `open_cash_drawer()` after successful cash payment
    - Add call in `create_pos_invoice()` after successful cash sale
    - Wrap in try/except for silent failure
    - _Requirements: 5.1, 5.2_

- [ ] 6. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties
- The implementation uses Python with PyQt6 for the frontend
