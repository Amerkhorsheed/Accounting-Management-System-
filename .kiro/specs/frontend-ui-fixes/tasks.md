# Implementation Plan: Frontend UI Fixes

## Overview

This plan addresses critical UI functionality issues where buttons for creating invoices and purchase orders are not connected to handlers, and reports are not displaying data properly.

## Tasks

- [x] 1. Fix InvoicesView button handler
  - [x] 1.1 Connect add button click handler in InvoicesView
    - Add `self.table.add_btn.clicked.connect(self.add_invoice)` in setup_ui()
    - Implement `add_invoice()` method to open form dialog
    - Implement `save_invoice()` method to call API and refresh
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

  - [x] 1.2 Create InvoiceFormDialog class
    - Create dialog with customer dropdown, invoice type, warehouse, items table
    - Implement `load_data()` to fetch customers, warehouses, products
    - Implement `validate()` with credit invoice customer requirement
    - Implement `save()` to emit data and close dialog
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [ ]* 1.3 Write property test for credit invoice validation
    - **Property 2: Credit Invoice Customer Requirement**
    - **Validates: Requirements 2.5**

- [x] 2. Fix PurchaseOrdersView button handler
  - [x] 2.1 Connect add button click handler in PurchaseOrdersView
    - Add `self.table.add_btn.clicked.connect(self.add_purchase_order)` in setup_ui()
    - Implement `add_purchase_order()` method to open form dialog
    - Implement `save_purchase_order()` method to call API and refresh
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

  - [x] 2.2 Create PurchaseOrderFormDialog class
    - Create dialog with supplier dropdown, warehouse, expected date, items table, notes
    - Implement `load_data()` to fetch suppliers, warehouses, products
    - Implement `validate()` for required fields
    - Implement `save()` to emit data and close dialog
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

  - [ ]* 2.3 Write property test for purchase order submission
    - **Property 3: Purchase Order Data Submission Correctness**
    - **Validates: Requirements 3.2, 4.1, 4.2, 4.3**

- [ ] 3. Checkpoint - Ensure invoice and purchase order forms work
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 4. Fix Reports data loading
  - [ ] 4.1 Fix ReceivablesReportView data loading
    - Ensure `refresh()` calls `api.get_receivables_report()`
    - Handle empty data with appropriate message
    - Handle API errors with error message
    - Display customer data in table with all required fields
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 6.1, 6.2, 6.3_

  - [ ] 4.2 Fix AgingReportView data loading
    - Ensure `refresh()` calls `api.get_aging_report()`
    - Display aging buckets with totals
    - Display customer breakdown
    - Handle empty/error states
    - _Requirements: 7.1, 7.2, 7.3, 7.4_

  - [ ] 4.3 Add filtering support to ReceivablesReportView
    - Add customer type filter dropdown
    - Update API call with filter parameters
    - Refresh data when filter changes
    - _Requirements: 6.4_

  - [ ]* 4.4 Write property test for receivables filtering
    - **Property 6: Receivables Filtering Correctness**
    - **Validates: Requirements 6.4**

- [ ] 5. Final Checkpoint - Ensure all functionality works
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- The implementation uses existing widgets (DataTable, FormDialog, MessageDialog)
- Property tests use the `hypothesis` library for Python
