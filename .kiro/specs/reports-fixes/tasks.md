# Implementation Plan: Reports Fixes

## Overview

This implementation plan covers fixing and completing the Reports module features including suppliers report, expenses report, export functionality (Excel/PDF), print capability, and customer statement opening balance fix.

## Tasks

- [x] 1. Backend: Add Suppliers Report Endpoint
  - [x] 1.1 Add get_suppliers_report method to ReportService
    - Calculate total suppliers, active suppliers, total payables
    - Build supplier list with purchase totals and outstanding balances
    - Support date range filtering
    - _Requirements: 1.2, 1.3, 1.4, 1.5, 1.6_
  - [ ]* 1.2 Write property test for suppliers report data consistency
    - **Property 1: Suppliers Report Data Completeness and Consistency**
    - **Validates: Requirements 1.2, 1.4**
  - [ ]* 1.3 Write property test for suppliers report sorting
    - **Property 2: Suppliers Report Sorting**
    - **Validates: Requirements 1.3**
  - [x] 1.4 Add SuppliersReportView to backend views
    - Create API endpoint at /reports/suppliers/
    - Parse date range query parameters
    - _Requirements: 1.1_
  - [x] 1.5 Register suppliers report URL
    - Add URL pattern to reports/urls.py
    - _Requirements: 1.1_

- [x] 2. Backend: Add Expenses Report Endpoint
  - [x] 2.1 Add get_expenses_report method to ReportService
    - Calculate total expenses and average
    - Build category breakdown with percentages
    - Build expenses list with all details
    - Support date range and category filtering
    - _Requirements: 2.2, 2.3, 2.4, 2.5, 2.6_
  - [ ]* 2.2 Write property test for expenses report category percentages
    - **Property 3: Expenses Report Category Percentages**
    - **Validates: Requirements 2.3**
  - [ ]* 2.3 Write property test for expenses report total consistency
    - **Property 4: Expenses Report Total Consistency**
    - **Validates: Requirements 2.2, 2.4**
  - [x] 2.4 Add ExpensesReportView to backend views
    - Create API endpoint at /reports/expenses/
    - Parse date range and category query parameters
    - _Requirements: 2.1_
  - [x] 2.5 Register expenses report URL
    - Add URL pattern to reports/urls.py
    - _Requirements: 2.1_

- [x] 3. Backend: Fix Customer Statement Opening Balance
  - [x] 3.1 Update SalesService.get_customer_statement method
    - Calculate opening balance including transactions before start_date
    - Ensure closing balance equals opening + debits - credits
    - _Requirements: 6.1, 6.2, 6.3, 6.4_
  - [x] 3.2 Write property test for customer statement opening balance
    - **Property 5: Customer Statement Opening Balance Calculation**
    - **Validates: Requirements 6.1, 6.2**
    and make the test only for those 
  - [ ]* 3.3 Write property test for customer statement balance equation
    - **Property 6: Customer Statement Balance Equation**
    - **Validates: Requirements 6.3**
    and make the test only for those 
  - [ ]* 3.4 Write property test for customer statement running balance
    - **Property 7: Customer Statement Running Balance Sequence**
    - **Validates: Requirements 6.4**
    and make the test only for those 

- [ ] 4. Checkpoint - Backend Tests
  - Ensure all backend tests pass, ask the user if questions arise.

- [x] 5. Frontend: Add API Methods for New Reports
  - [x] 5.1 Add get_suppliers_report method to ApiService
    - Accept date range parameters
    - Return suppliers report data
    - _Requirements: 1.1_
  - [x] 5.2 Add get_expenses_report method to ApiService
    - Accept date range and category parameters
    - Return expenses report data
    - _Requirements: 2.1_

- [x] 6. Frontend: Create Suppliers Report View
  - [x] 6.1 Create SuppliersReportView class
    - Add back button and header
    - Add date range filter controls
    - Add summary cards (total suppliers, active, payables)
    - Add suppliers table with columns
    - _Requirements: 1.1, 1.2, 1.4_
  - [x] 6.2 Implement data loading and refresh
    - Call API with date filters
    - Update summary cards
    - Populate suppliers table
    - _Requirements: 1.5, 1.6_
  - [x] 6.3 Register view in ReportsView
    - Add to stack widget
    - Connect navigation signals
    - Update show_report method
    - _Requirements: 1.1_

- [x] 7. Frontend: Create Expenses Report View
  - [x] 7.1 Create ExpensesReportView class
    - Add back button and header
    - Add date range and category filter controls
    - Add summary cards (total expenses)
    - Add category breakdown section
    - Add expenses table
    - _Requirements: 2.1, 2.2, 2.3, 2.4_
  - [x] 7.2 Implement data loading and refresh
    - Call API with filters
    - Update summary cards
    - Update category breakdown
    - Populate expenses table
    - _Requirements: 2.5, 2.6_
  - [x] 7.3 Register view in ReportsView
    - Add to stack widget
    - Connect navigation signals
    - Update show_report method
    - _Requirements: 2.1_

- [x] 8. Frontend: Create Export Service
  - [x] 8.1 Create ExportService class with Excel export
    - Use openpyxl for Excel generation
    - Format headers and data columns
    - Add report title and date
    - Handle file save dialog
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_
  - [x] 8.2 Add PDF export to ExportService
    - Use reportlab for PDF generation
    - Add company header
    - Format tables with RTL support
    - Add report metadata
    - Handle file save dialog
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_
  - [x] 8.3 Add print functionality to ExportService
    - Generate print-friendly HTML
    - Open print preview dialog
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_
  - [x] 8.4 Add error handling for export operations
    - Handle file permission errors
    - Handle library errors
    - Display user-friendly error messages
    - _Requirements: 3.6, 4.7_

- [x] 9. Frontend: Integrate Export Service with Reports
  - [x] 9.1 Add export buttons to ReceivablesReportView
    - Connect Excel button to export service
    - Connect PDF button to export service
    - _Requirements: 3.1, 4.1_
  - [x] 9.2 Add export buttons to AgingReportView
    - Connect Excel button to export service
    - Connect PDF button to export service
    - _Requirements: 3.1, 4.1_
  - [x] 9.3 Add export buttons to CustomerStatementView
    - Connect Excel button to export service
    - Connect PDF button to export service
    - Connect print button to print service
    - _Requirements: 3.1, 4.1, 5.1_
  - [x] 9.4 Add export buttons to SuppliersReportView
    - Connect Excel button to export service
    - Connect PDF button to export service
    - _Requirements: 3.1, 4.1_
  - [x] 9.5 Add export buttons to ExpensesReportView
    - Connect Excel button to export service
    - Connect PDF button to export service
    - _Requirements: 3.1, 4.1_

- [ ] 10. Final Checkpoint
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Export functionality requires openpyxl and reportlab packages
