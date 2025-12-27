# Implementation Plan: Credit Sales and Payments (البيع الآجل والتحصيل)

## Overview

This implementation plan breaks down the Credit Sales and Payments feature into discrete coding tasks. The implementation follows a bottom-up approach: database models first, then services, then API endpoints, and finally frontend components.

## Tasks

- [x] 1. Create new database models and migrations
  - [x] 1.1 Create PaymentAllocation model
    - Add PaymentAllocation model to backend/apps/sales/models.py
    - Fields: payment (FK), invoice (FK), amount (Decimal)
    - Add unique_together constraint for payment and invoice
    - _Requirements: 7.1, 7.5_

  - [x] 1.2 Create CreditLimitOverride model
    - Add CreditLimitOverride model to backend/apps/sales/models.py
    - Fields: customer (FK), invoice (FK nullable), override_amount, reason, approved_by
    - _Requirements: 6.5_

  - [x] 1.3 Add computed properties to Customer model
    - Add credit_warning_threshold property (returns True if balance >= 80% of limit)
    - Add is_over_credit_limit property (returns True if balance >= limit)
    - _Requirements: 6.3, 6.4_

  - [x] 1.4 Generate and apply migrations
    - Run makemigrations for sales app
    - Apply migrations
    - _Requirements: 1.1-1.6, 7.1-7.5_

- [x] 2. Implement CreditService backend logic
  - [x] 2.1 Create CreditService class with credit validation
    - Create backend/apps/sales/credit_service.py
    - Implement validate_credit_limit method
    - Return CreditValidationResult with warning/error status
    - _Requirements: 1.4, 6.3, 6.4_

  - [ ]* 2.2 Write property test for credit limit validation
    - **Property 4: Credit Limit Warning**
    - **Property 11: Credit Warning Threshold**
    - **Property 12: Credit Limit Blocking**
    - **Validates: Requirements 1.4, 6.3, 6.4**

  - [x] 2.3 Implement due date calculation
    - Add calculate_due_date method to CreditService
    - Calculate based on customer payment_terms
    - _Requirements: 1.2_

  - [ ]* 2.4 Write property test for due date calculation
    - **Property 2: Due Date Calculation**
    - **Validates: Requirements 1.2**

  - [x] 2.5 Implement payment allocation logic
    - Add allocate_payment method to CreditService
    - Support manual allocation to specific invoices
    - Implement FIFO auto-allocation strategy
    - Validate allocation amounts don't exceed remaining
    - _Requirements: 7.1, 7.2, 7.4, 7.5_

  - [ ]* 2.6 Write property tests for payment allocation
    - **Property 14: FIFO Payment Allocation**
    - **Property 15: Allocation Amount Constraint**
    - **Validates: Requirements 7.4, 7.5**

- [ ] 3. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Enhance SalesService for credit invoices
  - [x] 4.1 Update create_invoice for credit validation
    - Add credit limit check before creating credit invoice
    - Calculate and set due_date for credit invoices
    - Support override flag for credit limit bypass
    - _Requirements: 1.1, 1.2, 1.4, 1.5_

  - [x] 4.2 Update confirm_invoice for balance updates
    - Ensure credit invoice confirmation updates customer balance
    - Set correct initial status for credit invoices
    - _Requirements: 1.3, 1.5_

  - [ ]* 4.3 Write property test for credit invoice balance update
    - **Property 3: Credit Invoice Balance Update**
    - **Validates: Requirements 1.3**

  - [x] 4.4 Update receive_payment for allocation support
    - Modify receive_payment to accept allocations list
    - Create PaymentAllocation records
    - Update invoice paid_amount and status correctly
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [ ]* 4.5 Write property tests for payment processing
    - **Property 5: Payment Status Consistency**
    - **Property 6: Payment Balance Update**
    - **Validates: Requirements 2.2, 2.3, 2.4**

- [x] 5. Implement report services
  - [x] 5.1 Implement get_customer_statement enhancement
    - Ensure statement includes opening_balance, transactions, closing_balance
    - Calculate running balance for each transaction
    - Support date range filtering
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.6_

  - [ ]* 5.2 Write property tests for customer statement
    - **Property 7: Statement Structure and Running Balance**
    - **Property 8: Statement Date Filtering**
    - **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.6**

  - [x] 5.3 Implement get_receivables_report in ReportService
    - Add method to backend/apps/reports/services.py
    - Calculate total outstanding across customers
    - List customers sorted by balance descending
    - Include unpaid/partial invoice counts
    - Support filters (customer_type, salesperson)
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

  - [ ]* 5.4 Write property test for receivables report
    - **Property 9: Receivables Report Structure**
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.5**

  - [x] 5.5 Implement get_aging_report in ReportService
    - Add method to backend/apps/reports/services.py
    - Categorize by age buckets: current, 1-30, 31-60, 61-90, >90 days
    - Calculate totals per category
    - Include invoice details per category
    - _Requirements: 5.1, 5.2, 5.3_

  - [ ]* 5.6 Write property test for aging report
    - **Property 10: Aging Report Categorization**
    - **Validates: Requirements 5.1, 5.2, 5.3**

- [ ] 6. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Create API endpoints
  - [x] 7.1 Add payment allocation endpoints
    - Add customer_unpaid_invoices action to PaymentViewSet
    - Add allocate action to PaymentViewSet
    - Add collect_with_allocation action for combined operation
    - _Requirements: 2.1, 7.1, 7.3_

  - [x] 7.2 Add receivables report endpoint
    - Create ReceivablesReportView in backend/apps/reports/views.py
    - Add URL route
    - _Requirements: 4.1-4.5_

  - [x] 7.3 Add aging report endpoint
    - Create AgingReportView in backend/apps/reports/views.py
    - Add URL route
    - _Requirements: 5.1-5.5_

  - [x] 7.4 Update dashboard endpoint for credit summary
    - Add receivables_total, customers_with_balance, overdue_total to dashboard
    - _Requirements: 8.1, 8.2, 8.3_

  - [x] 7.5 Add serializers for new models and reports
    - Create PaymentAllocationSerializer
    - Create ReceivablesReportSerializer
    - Create AgingReportSerializer
    - _Requirements: 4.1-4.5, 5.1-5.5, 7.1-7.5_

- [x] 8. Update API service in frontend
  - [x] 8.1 Add payment collection API methods
    - Add get_customer_unpaid_invoices method
    - Add collect_payment_with_allocation method
    - _Requirements: 2.1, 7.1_

  - [x] 8.2 Add report API methods
    - Add get_receivables_report method
    - Add get_aging_report method
    - _Requirements: 4.1-4.5, 5.1-5.5_

- [x] 9. Implement frontend payment collection view
  - [x] 9.1 Create PaymentCollectionView widget
    - Create frontend/src/views/sales/payment_collection.py
    - Customer selection dropdown with balance display
    - Unpaid invoices table with checkboxes
    - Payment amount input
    - Payment method selection
    - _Requirements: 2.1, 2.5, 2.6_

  - [x] 9.2 Implement payment allocation UI
    - Show allocation preview as user selects invoices
    - Auto-calculate allocation amounts
    - Support partial allocation input
    - _Requirements: 7.1, 7.3_

  - [x] 9.3 Integrate payment submission
    - Call API to create payment with allocations
    - Show success/error messages
    - Refresh customer balance display
    - _Requirements: 2.2, 2.3, 2.4_

- [x] 10. Enhance invoice creation for credit sales
  - [x] 10.1 Update POSView for credit invoice support
    - Add customer selection requirement for credit
    - Display customer balance and available credit
    - Show credit limit warning when applicable
    - _Requirements: 1.1, 1.6_

  - [x] 10.2 Implement credit limit override dialog
    - Create confirmation dialog for credit limit override
    - Capture override reason
    - _Requirements: 1.4, 6.4, 6.5_

  - [x] 10.3 Auto-calculate due date
    - Set due_date based on customer payment_terms
    - Display due date in invoice form
    - _Requirements: 1.2_

- [ ] 11. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 12. Implement frontend reports
  - [x] 12.1 Create ReceivablesReportView widget
    - Create frontend/src/views/reports/receivables.py
    - Summary cards (total, overdue, customer count)
    - Customer list table with balances
    - Filter controls
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

  - [x] 12.2 Create AgingReportView widget
    - Create frontend/src/views/reports/aging.py
    - Aging buckets visualization (cards or chart)
    - Customer breakdown table
    - Visual highlighting for severe overdue
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

  - [x] 12.3 Enhance CustomerStatementView
    - Add date range filter
    - Display running balance column
    - Add export buttons (PDF/Excel placeholders)
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

  - [x] 12.4 Update ReportsView to include new reports
    - Add receivables report card
    - Add aging report card
    - Wire up navigation
    - _Requirements: 4.1-4.5, 5.1-5.5_

- [x] 13. Update dashboard with credit summary
  - [x] 13.1 Add receivables summary cards to dashboard
    - Display total receivables
    - Display customers with balance count
    - Display overdue amount
    - _Requirements: 8.1, 8.2, 8.3_

  - [x] 13.2 Add click navigation to receivables report
    - Navigate to receivables report on card click
    - _Requirements: 8.4_

- [ ] 14. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
  - Verify all requirements are implemented
  - Test end-to-end credit sale and payment flow

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- The implementation uses Python with Django REST Framework (backend) and PySide6 (frontend)
- Property-based testing uses the `hypothesis` library
