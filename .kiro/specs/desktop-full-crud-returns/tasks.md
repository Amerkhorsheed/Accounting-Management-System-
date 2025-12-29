# Implementation Plan: Desktop Full CRUD & Sales Returns

## Overview

This implementation plan brings the PySide6 desktop application to full feature parity with Django admin. The approach is incremental: backend API extensions first, then frontend views, with testing integrated throughout.

## Tasks

- [x] 1. Backend API Extensions
  - [x] 1.1 Add StockMovement ViewSet and serializers
    - Create `StockMovementSerializer` in `backend/apps/inventory/serializers.py`
    - Create `StockMovementViewSet` in `backend/apps/inventory/views.py`
    - Add URL routes in `backend/apps/inventory/urls.py`
    - _Requirements: 6.1, 6.2, 6.3_

  - [x] 1.2 Add cancel_invoice action to InvoiceViewSet
    - Add `cancel_invoice` method to `SalesService` in `backend/apps/sales/services.py`
    - Add `cancel` action to `InvoiceViewSet` in `backend/apps/sales/views.py`
    - _Requirements: 4.4, 4.5_

  - [x] 1.3 Enhance SalesReturnViewSet with create action
    - Update `SalesReturnViewSet` to support POST for creating returns
    - Add `SalesReturnCreateSerializer` in `backend/apps/sales/serializers.py`
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8_

  - [x] 1.4 Write property tests for sales return service
    - **Property 3: Return Quantity Validation**
    - **Property 4: Return Stock Restoration**
    - **Property 5: Return Stock Movement Creation**
    - **Property 6: Return Customer Balance Adjustment**
    - **Validates: Requirements 5.3, 5.4, 5.5, 5.6**

  - [x]* 1.5 Write property test for invoice cancellation
    - **Property 9: Invoice Cancellation Reversal**
    - **Validates: Requirements 4.5**

- [ ] 2. Checkpoint - Backend API Complete
  - Ensure all backend tests pass, ask the user if questions arise.

- [x] 3. Frontend API Client Extensions
  - [x] 3.1 Add stock movements API methods
    - Add `get_stock_movements(params)` method to `api.py`
    - _Requirements: 6.1, 6.2_

  - [x] 3.2 Add sales returns API methods
    - Add `create_sales_return(invoice_id, data)` method
    - Add `get_sales_returns(params)` method
    - Add `get_sales_return(return_id)` method
    - _Requirements: 5.1, 5.9_

  - [x] 3.3 Add invoice cancel API method
    - Add `cancel_invoice(invoice_id, reason)` method
    - _Requirements: 4.4_

  - [x] 3.4 Add CRUD methods for Categories, Units, Warehouses, ExpenseCategories
    - Add create/update/delete methods for each entity
    - _Requirements: 8.2, 8.3, 8.4, 9.2, 9.3, 9.4, 10.2, 10.3, 10.4, 11.2, 11.3, 11.4_

- [x] 4. Enhanced DataTable Widget
  - [x] 4.1 Add pagination support to DataTable
    - Add page navigation controls
    - Add page size selector
    - Emit `page_changed` signal
    - _Requirements: 14.1, 14.4_

  - [x] 4.2 Add column sorting to DataTable
    - Add click handler on column headers
    - Emit `sort_changed` signal
    - Display sort indicator
    - _Requirements: 14.2_

  - [x] 4.3 Add edit and delete actions to DataTable
    - Add action buttons column
    - Emit `edit_clicked` and `delete_clicked` signals
    - _Requirements: 1.3, 1.4, 2.3, 2.4, 3.3, 3.4_

- [x] 5. Sales Returns View
  - [x] 5.1 Create SalesReturnDialog widget
    - Display original invoice items with quantities
    - Add quantity spinners with max validation
    - Add reason text field (required)
    - Calculate and display return totals
    - _Requirements: 5.2, 5.3, 5.7, 5.8_

  - [x] 5.2 Create SalesReturnsView
    - Display returns list with DataTable
    - Add filtering by date range and invoice
    - _Requirements: 5.9_

  - [x] 5.3 Add "Create Return" action to InvoicesView
    - Add return button for confirmed/paid invoices
    - Open SalesReturnDialog on click
    - Call API and refresh on success
    - _Requirements: 5.1_

  - [x] 5.4 Write unit tests for SalesReturnDialog
    - Test quantity validation
    - Test reason required
    - Test total calculation
    - _Requirements: 5.3, 5.7, 5.8_

- [ ] 6. Checkpoint - Sales Returns Complete
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Stock Movements View
  - [x] 7.1 Create StockMovementsView
    - Display movements list with DataTable
    - Color-code by movement type
    - Add filtering by product, warehouse, type, date range
    - _Requirements: 6.1, 6.2, 6.4_

  - [x] 7.2 Add movement details dialog
    - Display full movement details on click
    - Show source document reference
    - _Requirements: 6.3_

- [x] 8. Enhanced Customers View
  - [x] 8.1 Add edit functionality to CustomersView
    - Handle double-click to open edit dialog
    - Pre-populate form with current data
    - Call update API on save
    - _Requirements: 1.3_

  - [x] 8.2 Add delete functionality to CustomersView
    - Add delete action to table
    - Show confirmation dialog
    - Handle deletion protection error
    - _Requirements: 1.4, 1.5_

  - [x] 8.3 Write property test for customer deletion protection
    - **Property 1: Entity Deletion Protection (Customer)**
    - **Validates: Requirements 1.5**

- [x] 9. Enhanced Products View
  - [x] 9.1 Verify edit functionality in ProductsView
    - Ensure double-click opens edit dialog with product units
    - Ensure update API is called correctly
    - _Requirements: 2.3_

  - [x] 9.2 Add delete functionality to ProductsView
    - Add delete action to table
    - Show confirmation dialog
    - Handle deletion protection error
    - _Requirements: 2.4, 2.5_

- [x] 10. Enhanced Suppliers View
  - [x] 10.1 Verify edit functionality in SuppliersView
    - Ensure double-click opens edit dialog
    - Ensure update API is called correctly
    - _Requirements: 3.3_

  - [x] 10.2 Add delete functionality to SuppliersView
    - Add delete action to table
    - Show confirmation dialog
    - Handle deletion protection error
    - _Requirements: 3.4, 3.5_

- [x] 11. Enhanced Invoices View
  - [x] 11.1 Add invoice details dialog
    - Display full invoice with items on double-click
    - Show customer, dates, totals, items
    - _Requirements: 4.2_

  - [x] 11.2 Add cancel action for invoices
    - Add cancel button for confirmed invoices
    - Show confirmation with reason input
    - Call cancel API and refresh
    - _Requirements: 4.4_

  - [x] 11.3 Add filtering to InvoicesView
    - Add status filter dropdown
    - Add date range filter
    - Add customer filter
    - _Requirements: 4.6_

- [ ] 12. Checkpoint - Core Views Complete
  - Ensure all tests pass, ask the user if questions arise.

- [x] 13. Categories Management View
  - [x] 13.1 Create CategoriesView
    - Display categories list with DataTable
    - Show name, parent, product count columns
    - _Requirements: 8.1_

  - [x] 13.2 Add CRUD operations to CategoriesView
    - Add create dialog with name, parent, description
    - Add edit on double-click
    - Add delete with protection check
    - _Requirements: 8.2, 8.3, 8.4, 8.5_

- [x] 14. Units Management View
  - [x] 14.1 Create UnitsView
    - Display units list with DataTable
    - Show name, symbol, product count columns
    - _Requirements: 9.1_

  - [x] 14.2 Add CRUD operations to UnitsView
    - Add create dialog with name, name_en, symbol
    - Add edit on double-click
    - Add delete with protection check
    - _Requirements: 9.2, 9.3, 9.4, 9.5_

- [x] 15. Warehouses Management View
  - [x] 15.1 Create WarehousesView
    - Display warehouses list with DataTable
    - Show code, name, address, is_default columns
    - _Requirements: 10.1_

  - [x] 15.2 Add CRUD operations to WarehousesView
    - Add create dialog with code, name, address, is_default
    - Add edit on double-click
    - Add delete with protection check
    - _Requirements: 10.2, 10.3, 10.4, 10.5_

  - [ ]* 15.3 Write property test for single default warehouse
    - **Property 11: Single Default Warehouse**
    - **Validates: Requirements 10.6**

- [x] 16. Enhanced Expenses View
  - [x] 16.1 Add edit functionality to ExpensesView
    - Handle double-click to open edit dialog
    - Pre-populate form with current data
    - _Requirements: 7.3_

  - [x] 16.2 Add delete functionality to ExpensesView
    - Add delete action to table
    - Show confirmation dialog
    - _Requirements: 7.4_

  - [x] 16.3 Add filtering to ExpensesView
    - Add category filter dropdown
    - Add date range filter
    - _Requirements: 7.5_

- [x] 17. Expense Categories Management View
  - [x] 17.1 Create ExpenseCategoriesView
    - Display expense categories list with DataTable
    - Show name, parent, expense count columns
    - _Requirements: 11.1_

  - [x] 17.2 Add CRUD operations to ExpenseCategoriesView
    - Add create dialog with name, parent, description
    - Add edit on double-click
    - Add delete with protection check
    - _Requirements: 11.2, 11.3, 11.4, 11.5_

- [x] 18. Enhanced Purchase Orders View
  - [x] 18.1 Add purchase order details dialog
    - Display full PO with items on double-click
    - Show supplier, dates, totals, items
    - _Requirements: 12.2_

  - [x] 18.2 Add status actions to PurchaseOrdersView
    - Add approve, mark ordered, receive goods actions
    - Update status via API
    - _Requirements: 12.4_

  - [x] 18.3 Add filtering to PurchaseOrdersView
    - Add status filter dropdown
    - Add supplier filter
    - Add date range filter
    - _Requirements: 12.6_

  - [ ]* 18.4 Write property test for goods receipt stock update
    - **Property 10: Goods Receipt Stock Update**
    - **Validates: Requirements 12.5**

- [x] 19. Enhanced Payments View
  - [x] 19.1 Create PaymentsView
    - Display payments list with DataTable
    - Show number, customer, date, amount, method columns
    - _Requirements: 13.1_

  - [x] 19.2 Add payment creation with allocation
    - Create payment form with customer, amount, method
    - Add invoice allocation section
    - Support multiple invoice allocation
    - _Requirements: 13.2, 13.4_

  - [x] 19.3 Add payment details dialog
    - Display payment details on double-click
    - Show allocations list
    - _Requirements: 13.3_

  - [x] 19.4 Add filtering to PaymentsView
    - Add customer filter
    - Add date range filter
    - Add payment method filter
    - _Requirements: 13.5_

  - [ ]* 19.5 Write property test for payment allocation consistency
    - **Property 12: Payment Allocation Consistency**
    - **Validates: Requirements 13.4**

- [x] 20. Navigation Integration
  - [x] 20.1 Add new views to sidebar navigation
    - Add Stock Movements under Inventory
    - Add Sales Returns under Sales
    - Add Categories, Units, Warehouses under Settings
    - Add Expense Categories under Settings
    - Add Payments under Sales

  - [x] 20.2 Update main window to include new views
    - Register all new views in view stack
    - Connect navigation signals

- [ ] 21. Final Checkpoint
  - Ensure all tests pass, ask the user if questions arise.
  - Verify all views are accessible from navigation
  - Test complete workflows end-to-end

## Notes

- Tasks marked with `*` are optional property-based tests
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Backend tasks should be completed before corresponding frontend tasks
