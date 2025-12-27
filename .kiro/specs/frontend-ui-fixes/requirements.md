# Requirements Document

## Introduction

This document specifies the requirements for fixing critical UI functionality issues in the PySide6 desktop frontend application. Users are unable to create new invoices, view reports, or create purchase orders due to missing button click handlers and incomplete UI implementations.

## Glossary

- **Frontend**: The PySide6 desktop application providing the user interface
- **InvoicesView**: The view component for managing sales invoices (الفواتير)
- **PurchaseOrdersView**: The view component for managing purchase orders (أوامر الشراء)
- **ReportsView**: The view component for displaying business reports (التقارير)
- **DataTable**: A reusable table widget with add/edit/delete actions
- **FormDialog**: A reusable dialog for data entry forms
- **API**: The backend REST API service layer

## Requirements

### Requirement 1: Invoice Creation

**User Story:** As a sales user, I want to click the "فاتورة جديدة" button to create a new invoice, so that I can record sales transactions.

#### Acceptance Criteria

1. WHEN a user clicks the "فاتورة جديدة" button THEN THE InvoicesView SHALL display a form dialog for entering invoice details
2. WHEN a user submits valid invoice data THEN THE InvoicesView SHALL send the data to the API and create the invoice
3. WHEN an invoice is successfully created THEN THE InvoicesView SHALL refresh the invoices list and show a success message
4. IF an error occurs during invoice creation THEN THE InvoicesView SHALL display an error message to the user

### Requirement 2: Invoice Form Fields

**User Story:** As a sales user, I want the invoice form to include all necessary fields, so that I can enter complete invoice information.

#### Acceptance Criteria

1. THE Invoice_Form SHALL include a customer selection dropdown populated from the API
2. THE Invoice_Form SHALL include an invoice type selection (cash/credit)
3. THE Invoice_Form SHALL include a warehouse selection dropdown
4. THE Invoice_Form SHALL include an items section for adding products with quantity and price
5. WHEN invoice type is "credit" THEN THE Invoice_Form SHALL require customer selection

### Requirement 3: Purchase Order Creation

**User Story:** As a purchasing user, I want to click the "أمر شراء جديد" button to create a new purchase order, so that I can order products from suppliers.

#### Acceptance Criteria

1. WHEN a user clicks the "أمر شراء جديد" button THEN THE PurchaseOrdersView SHALL display a form dialog for entering order details
2. WHEN a user submits valid order data THEN THE PurchaseOrdersView SHALL send the data to the API and create the order
3. WHEN an order is successfully created THEN THE PurchaseOrdersView SHALL refresh the orders list and show a success message
4. IF an error occurs during order creation THEN THE PurchaseOrdersView SHALL display an error message to the user

### Requirement 4: Purchase Order Form Fields

**User Story:** As a purchasing user, I want the purchase order form to include all necessary fields, so that I can enter complete order information.

#### Acceptance Criteria

1. THE PurchaseOrder_Form SHALL include a supplier selection dropdown populated from the API
2. THE PurchaseOrder_Form SHALL include a warehouse selection dropdown
3. THE PurchaseOrder_Form SHALL include an items section for adding products with quantity and price
4. THE PurchaseOrder_Form SHALL include an expected delivery date field
5. THE PurchaseOrder_Form SHALL include a notes field for additional information

### Requirement 5: Reports Data Loading

**User Story:** As a manager, I want to view reports with actual data, so that I can analyze business performance.

#### Acceptance Criteria

1. WHEN a user navigates to the reports section THEN THE ReportsView SHALL load available report types
2. WHEN a user selects a report type THEN THE ReportsView SHALL fetch data from the API and display it
3. WHEN report data is loading THEN THE ReportsView SHALL show a loading indicator
4. IF no data is available THEN THE ReportsView SHALL display an appropriate empty state message
5. IF an error occurs during data loading THEN THE ReportsView SHALL display an error message

### Requirement 6: Receivables Report

**User Story:** As a finance user, I want to view the receivables report, so that I can track customer outstanding balances.

#### Acceptance Criteria

1. WHEN a user opens the receivables report THEN THE System SHALL display a list of customers with outstanding balances
2. THE Receivables_Report SHALL show customer name, balance, credit limit, and overdue amount
3. THE Receivables_Report SHALL show summary totals at the top
4. THE Receivables_Report SHALL support filtering by customer type

### Requirement 7: Aging Report

**User Story:** As a finance user, I want to view the aging report, so that I can see overdue invoices categorized by age.

#### Acceptance Criteria

1. WHEN a user opens the aging report THEN THE System SHALL display invoices grouped by aging buckets
2. THE Aging_Report SHALL show buckets: current, 1-30 days, 31-60 days, 61-90 days, over 90 days
3. THE Aging_Report SHALL show totals for each aging bucket
4. THE Aging_Report SHALL show customer breakdown with amounts per bucket
