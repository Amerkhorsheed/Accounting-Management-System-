# Requirements Document

## Introduction

This document specifies the requirements for fixing and completing the Reports module (قائمة التقارير) in the inventory management system. The reports module currently has several features that are not working or incomplete, including suppliers report, expenses report, and export functionality.

## Glossary

- **Reports_Module**: The system component responsible for generating and displaying business reports and analytics
- **Suppliers_Report**: A report showing supplier statistics, purchase history, and payment status
- **Expenses_Report**: A report showing expense analysis by category, date range, and trends
- **Export_Service**: The service responsible for exporting reports to Excel and PDF formats
- **Customer_Statement**: A report showing customer account transactions and running balance
- **Aging_Report**: A report categorizing receivables by overdue periods
- **Receivables_Report**: A report showing total outstanding customer balances

## Requirements

### Requirement 1: Suppliers Report

**User Story:** As a business owner, I want to view a suppliers report, so that I can analyze supplier performance and payment status.

#### Acceptance Criteria

1. WHEN a user clicks on "تقرير الموردين" THEN THE Reports_Module SHALL display a suppliers report view
2. THE Suppliers_Report SHALL display total suppliers count, active suppliers count, and total payables
3. THE Suppliers_Report SHALL list suppliers sorted by total purchase amount descending
4. WHEN displaying supplier data THEN THE Suppliers_Report SHALL show supplier name, code, total purchases, total payments, and outstanding balance
5. THE Suppliers_Report SHALL support filtering by date range for purchase calculations
6. WHEN a user applies date filters THEN THE Suppliers_Report SHALL recalculate all statistics for the selected period

### Requirement 2: Expenses Report

**User Story:** As a business owner, I want to view an expenses report, so that I can analyze spending patterns and control costs.

#### Acceptance Criteria

1. WHEN a user clicks on "تقرير المصروفات" THEN THE Reports_Module SHALL display an expenses report view
2. THE Expenses_Report SHALL display total expenses amount for the selected period
3. THE Expenses_Report SHALL show expenses breakdown by category with amounts and percentages
4. THE Expenses_Report SHALL list individual expenses with date, category, description, and amount
5. THE Expenses_Report SHALL support filtering by date range
6. THE Expenses_Report SHALL support filtering by expense category
7. WHEN displaying category breakdown THEN THE Expenses_Report SHALL show a visual representation of expense distribution

### Requirement 3: Export to Excel

**User Story:** As a user, I want to export reports to Excel format, so that I can analyze data in spreadsheets and share with others.

#### Acceptance Criteria

1. WHEN a user clicks "Excel" export button on any report THEN THE Export_Service SHALL generate an Excel file
2. THE Export_Service SHALL include all visible data columns in the exported file
3. THE Export_Service SHALL format numbers with proper decimal places and currency symbols
4. THE Export_Service SHALL include report title and generation date in the exported file
5. THE Export_Service SHALL prompt the user to save the file with a default filename based on report type and date
6. IF export fails THEN THE Export_Service SHALL display an error message explaining the failure

### Requirement 4: Export to PDF

**User Story:** As a user, I want to export reports to PDF format, so that I can print or share professional-looking reports.

#### Acceptance Criteria

1. WHEN a user clicks "PDF" export button on any report THEN THE Export_Service SHALL generate a PDF file
2. THE Export_Service SHALL include company header information in the PDF
3. THE Export_Service SHALL format the PDF with proper Arabic text direction (RTL)
4. THE Export_Service SHALL include report title, date range, and generation timestamp
5. THE Export_Service SHALL format tables with proper borders and alignment
6. THE Export_Service SHALL prompt the user to save the file with a default filename
7. IF export fails THEN THE Export_Service SHALL display an error message explaining the failure

### Requirement 5: Print Statement

**User Story:** As a user, I want to print customer statements, so that I can provide physical copies to customers.

#### Acceptance Criteria

1. WHEN a user clicks "طباعة" on customer statement THEN THE Reports_Module SHALL open a print preview dialog
2. THE print preview SHALL display the statement in a print-friendly format
3. THE print preview SHALL include company header, customer details, and transaction table
4. THE print preview SHALL include opening balance, closing balance, and totals
5. WHEN user confirms print THEN THE Reports_Module SHALL send the document to the printer

### Requirement 6: Customer Statement Opening Balance Fix

**User Story:** As a user, I want the customer statement to correctly calculate opening balance when filtering by date range, so that I can see accurate account history.

#### Acceptance Criteria

1. WHEN a date range filter is applied THEN THE Customer_Statement SHALL calculate opening balance as the balance at the start of the period
2. THE opening balance calculation SHALL include all transactions before the start date
3. THE closing balance SHALL equal opening balance plus all debits minus all credits in the period
4. THE running balance after each transaction SHALL be calculated correctly from the opening balance
