# Implementation Plan: Supplier Partial Payments

## Overview

This implementation plan adds partial payment functionality for supplier purchases, following the existing patterns from the sales credit system. The tasks are organized to build incrementally, starting with backend models and services, then API endpoints, and finally frontend components.

## Tasks

- [ ] 1. Update PurchaseOrder Model
  - [ ] 1.1 Add order_type field (cash/credit) to PurchaseOrder model
    - Add OrderType TextChoices class
    - Add order_type field with default 'credit'
    - _Requirements: 1.1, 1.2, 1.3_
  - [ ] 1.2 Add payment_status field to PurchaseOrder model
    - Add PaymentStatus TextChoices class (unpaid, partial, paid)
    - Add payment_status field with default 'unpaid'
    - _Requirements: 2.1, 2.3, 2.4_
  - [ ] 1.3 Create and run database migration
    - Generate migration for new fields
    - Apply migration
    - _Requirements: 1.4_

- [ ] 2. Create SupplierPaymentAllocation Model
  - [ ] 2.1 Create SupplierPaymentAllocation model
    - Add payment ForeignKey to SupplierPayment
    - Add purchase_order ForeignKey to PurchaseOrder
    - Add amount DecimalField
    - Add unique_together constraint
    - _Requirements: 5.2, 5.4_
  - [ ] 2.2 Create and run database migration
    - Generate migration for new model
    - Apply migration
    - _Requirements: 5.2_

- [ ] 3. Implement PayableService
  - [ ] 3.1 Create payable_service.py with core functions
    - Implement update_payment_status function
    - Implement update_supplier_balance function
    - _Requirements: 2.1, 2.3, 2.4, 3.1, 3.2_
  - [ ]* 3.2 Write property test for payment status determination
    - **Property 2: Payment Status Determination**
    - **Validates: Requirements 2.1, 2.3, 2.4**
  - [ ]* 3.3 Write property test for remaining amount calculation
    - **Property 1: Remaining Amount Calculation**
    - **Validates: Requirements 1.4**
  - [ ]* 3.4 Write property test for paid amount constraint
    - **Property 3: Paid Amount Constraint**
    - **Validates: Requirements 2.5**

- [ ] 4. Implement Payment Allocation Logic
  - [ ] 4.1 Implement allocate_payment function in PayableService
    - Support manual allocation with validation
    - Support auto-allocation using FIFO
    - Update order paid_amount and payment_status
    - _Requirements: 5.2, 5.3, 5.4, 5.5_
  - [ ] 4.2 Implement get_supplier_unpaid_orders function
    - Return orders with payment_status in (unpaid, partial)
    - Order by order_date ascending
    - _Requirements: 5.1_
  - [ ]* 4.3 Write property test for allocation amount constraint
    - **Property 9: Allocation Amount Constraint**
    - **Validates: Requirements 5.5**
  - [ ]* 4.4 Write property test for FIFO allocation order
    - **Property 7: FIFO Allocation Order**
    - **Validates: Requirements 5.3**
  - [ ]* 4.5 Write property test for allocation updates order status
    - **Property 8: Allocation Updates Order Status**
    - **Validates: Requirements 5.4**

- [ ] 5. Implement Supplier Balance Management
  - [ ] 5.1 Update PurchaseOrder save/confirm to update supplier balance
    - Increase supplier balance when credit order is confirmed
    - Handle balance updates on order changes
    - _Requirements: 3.1, 3.3_
  - [ ] 5.2 Update SupplierPayment save to update supplier balance
    - Decrease supplier balance when payment is created
    - _Requirements: 3.2, 4.4_
  - [ ]* 5.3 Write property test for supplier balance consistency
    - **Property 4: Supplier Balance Consistency**
    - **Validates: Requirements 3.1, 3.2, 3.3**

- [ ] 6. Checkpoint - Backend Models and Services
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 7. Update Purchase Order Serializers
  - [ ] 7.1 Update PurchaseOrderSerializer with new fields
    - Add order_type field
    - Add payment_status field (read-only)
    - Add paid_amount field
    - Add remaining_amount computed field
    - _Requirements: 1.4, 6.1, 6.2_
  - [ ] 7.2 Create SupplierPaymentAllocationSerializer
    - Serialize allocation with payment and order references
    - _Requirements: 5.2, 6.4_

- [ ] 8. Update Purchase Order Views
  - [ ] 8.1 Update PurchaseOrderViewSet create action
    - Handle order_type and paid_amount on creation
    - Update payment_status based on paid_amount
    - Update supplier balance for credit orders
    - _Requirements: 1.1, 2.1, 2.3, 2.4, 3.1_
  - [ ] 8.2 Add payment_status filter to PurchaseOrderViewSet
    - Support filtering by payment_status
    - _Requirements: 6.3_

- [ ] 9. Implement Supplier Payment Allocation API
  - [ ] 9.1 Create allocate action on SupplierPaymentViewSet
    - Accept allocations list or auto_allocate flag
    - Call PayableService.allocate_payment
    - Return created allocations
    - _Requirements: 5.2, 5.3, 5.4, 5.5_
  - [ ] 9.2 Add unpaid_orders action to SupplierViewSet
    - Return unpaid/partial orders for supplier
    - _Requirements: 5.1_

- [ ] 10. Implement Supplier Statement Report
  - [ ] 10.1 Add get_supplier_statement to ReportService
    - Calculate opening balance from transactions before period
    - Include purchase orders as debits
    - Include payments as credits
    - Calculate running balance for each transaction
    - _Requirements: 7.1, 7.2, 7.3, 7.4_
  - [ ]* 10.2 Write property test for statement balance calculation
    - **Property 10: Statement Balance Calculation**
    - **Validates: Requirements 7.1, 7.2, 7.3**
  - [ ]* 10.3 Write property test for running balance accuracy
    - **Property 11: Running Balance Accuracy**
    - **Validates: Requirements 7.3**

- [ ] 11. Implement Accounts Payable Report
  - [ ] 11.1 Add get_payables_report to ReportService
    - Calculate total outstanding across suppliers
    - List suppliers with balances sorted by amount
    - Include unpaid/partial order counts
    - Support filtering
    - _Requirements: 8.1, 8.2, 8.3, 8.4_
  - [ ]* 11.2 Write property test for payables report total
    - **Property 12: Payables Report Total**
    - **Validates: Requirements 8.1**
  - [ ]* 11.3 Write property test for payables report sorting
    - **Property 13: Payables Report Sorting**
    - **Validates: Requirements 8.2**

- [ ] 12. Implement Supplier Aging Report
  - [ ] 12.1 Add get_supplier_aging_report to ReportService
    - Categorize by age buckets (current, 1-30, 31-60, 61-90, >90)
    - Calculate totals per bucket
    - Include order details per bucket
    - _Requirements: 9.1, 9.2, 9.3, 9.4_
  - [ ]* 12.2 Write property test for aging bucket categorization
    - **Property 14: Aging Bucket Categorization**
    - **Validates: Requirements 9.1**
  - [ ]* 12.3 Write property test for aging bucket totals
    - **Property 15: Aging Bucket Totals**
    - **Validates: Requirements 9.2**

- [ ] 13. Add Report API Endpoints
  - [ ] 13.1 Add supplier statement endpoint
    - GET /api/v1/purchases/suppliers/{id}/statement/
    - Support date range query params
    - _Requirements: 7.1, 7.4_
  - [ ] 13.2 Add payables report endpoint
    - GET /api/v1/reports/payables/
    - Support supplier and date filters
    - _Requirements: 8.1, 8.4_
  - [ ] 13.3 Add aging report endpoint
    - GET /api/v1/reports/payables/aging/
    - Support as_of_date param
    - _Requirements: 9.1_

- [ ] 14. Checkpoint - Backend API Complete
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 15. Update Purchase Order Form Dialog
  - [ ] 15.1 Add order type selection to PurchaseOrderFormDialog
    - Add order_type combo box (cash/credit)
    - Show/hide payment section based on type
    - _Requirements: 1.1, 1.2, 1.3_
  - [ ] 15.2 Add paid amount section to form
    - Add paid_amount spin box
    - Add "full payment" button
    - Connect full payment button to set paid_amount = total
    - _Requirements: 2.2_
  - [ ] 15.3 Update form save to include payment data
    - Include order_type and paid_amount in save data
    - _Requirements: 1.4, 2.1_

- [ ] 16. Update Purchase Order List and Details
  - [ ] 16.1 Add payment columns to purchase order table
    - Add payment_status column with status badge
    - Add paid_amount and remaining_amount columns
    - _Requirements: 6.1, 6.2_
  - [ ] 16.2 Add payment status filter to list view
    - Add payment_status filter dropdown
    - _Requirements: 6.3_
  - [ ] 16.3 Update PurchaseOrderDetailsDialog with payment info
    - Show payment history section
    - Show payment allocations
    - _Requirements: 6.4_

- [ ] 17. Create Supplier Payment Dialog
  - [ ] 17.1 Create SupplierPaymentDialog class
    - Supplier selection (or pre-selected)
    - Payment amount and method inputs
    - Payment date picker
    - Notes field
    - _Requirements: 4.1, 4.3_
  - [ ] 17.2 Add unpaid orders table with allocation
    - Display unpaid/partial orders for supplier
    - Add allocation amount input per order
    - Calculate total allocation
    - _Requirements: 5.1, 5.2_
  - [ ] 17.3 Add auto-allocate button
    - Implement FIFO auto-allocation in UI
    - _Requirements: 5.3_
  - [ ] 17.4 Connect dialog to API
    - Save payment via API
    - Submit allocations
    - Refresh parent view on success
    - _Requirements: 4.4, 5.4_

- [ ] 18. Add Supplier Payment to Suppliers View
  - [ ] 18.1 Add "سند صرف" button to suppliers table actions
    - Open SupplierPaymentDialog for selected supplier
    - _Requirements: 4.1_
  - [ ] 18.2 Add supplier payments list view
    - Show payment history for supplier
    - _Requirements: 4.2_

- [ ] 19. Implement Reports UI
  - [ ] 19.1 Add supplier statement report view
    - Supplier selection
    - Date range filter
    - Statement table with running balance
    - Export buttons
    - _Requirements: 7.1, 7.4, 7.5_
  - [ ] 19.2 Add accounts payable report view
    - Summary cards (total, overdue, supplier count)
    - Suppliers table with balances
    - Filter controls
    - _Requirements: 8.1, 8.2, 8.3, 8.4_
  - [ ] 19.3 Add supplier aging report view
    - Age bucket summary cards
    - Detailed table per bucket
    - _Requirements: 9.1, 9.2, 9.3_

- [ ] 20. Update Dashboard
  - [ ] 20.1 Add accounts payable summary card
    - Total payables amount
    - Suppliers with balance count
    - Overdue amount highlight
    - _Requirements: 10.1, 10.2, 10.3_

- [ ] 21. Final Checkpoint
  - Ensure all tests pass, ask the user if questions arise.
  - Verify all requirements are implemented
  - Test end-to-end payment flow

## Notes

- Tasks marked with `*` are optional property-based tests that can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
