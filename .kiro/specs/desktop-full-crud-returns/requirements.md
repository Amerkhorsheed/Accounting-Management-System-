# Requirements Document

## Introduction

This document specifies the requirements for bringing the PySide6 desktop application to full feature parity with the Django admin interface. The primary focus areas are:
1. Full CRUD (Create, Read, Update, Delete) operations for all entities
2. Sales Returns functionality with proper stock and profit adjustments
3. Enhanced data management views with filtering, searching, and pagination

## Glossary

- **Desktop_App**: The PySide6-based desktop application for the accounting management system
- **Sales_Return**: A transaction that reverses part or all of a sales invoice, returning products to stock
- **Invoice_Item**: A line item within an invoice representing a product sale
- **Stock_Movement**: A record of inventory changes (in/out/adjustment/return)
- **Customer_Balance**: The current outstanding amount owed by a customer
- **CRUD**: Create, Read, Update, Delete operations
- **Partial_Return**: A return that includes only some items or quantities from an invoice

## Requirements

### Requirement 1: Full CRUD for Customers

**User Story:** As a sales manager, I want to create, view, edit, and delete customers from the desktop app, so that I can manage customer data without using the admin interface.

#### Acceptance Criteria

1. THE Desktop_App SHALL display a customers list with columns: code, name, phone, mobile, balance, credit limit
2. WHEN a user clicks "Add Customer" THEN THE Desktop_App SHALL display a form dialog with all customer fields
3. WHEN a user double-clicks a customer row THEN THE Desktop_App SHALL display an edit form with current data
4. WHEN a user clicks delete on a customer THEN THE Desktop_App SHALL show a confirmation dialog before soft-deleting
5. WHEN a customer has outstanding invoices THEN THE Desktop_App SHALL prevent deletion and show an error message
6. THE Desktop_App SHALL provide search functionality by name, code, phone, or tax number

### Requirement 2: Full CRUD for Products

**User Story:** As an inventory manager, I want to create, view, edit, and delete products from the desktop app, so that I can manage product catalog efficiently.

#### Acceptance Criteria

1. THE Desktop_App SHALL display a products list with columns: code, barcode, name, category, cost price, sale price, stock
2. WHEN a user clicks "Add Product" THEN THE Desktop_App SHALL display a tabbed form with basic info and unit configuration
3. WHEN a user double-clicks a product row THEN THE Desktop_App SHALL display an edit form with current data including product units
4. WHEN a user clicks delete on a product THEN THE Desktop_App SHALL show a confirmation dialog before soft-deleting
5. WHEN a product has stock movements or invoice items THEN THE Desktop_App SHALL prevent deletion and show an error message
6. THE Desktop_App SHALL provide barcode search functionality

### Requirement 3: Full CRUD for Suppliers

**User Story:** As a purchasing manager, I want to create, view, edit, and delete suppliers from the desktop app, so that I can manage supplier relationships.

#### Acceptance Criteria

1. THE Desktop_App SHALL display a suppliers list with columns: code, name, phone, mobile, balance
2. WHEN a user clicks "Add Supplier" THEN THE Desktop_App SHALL display a form dialog with all supplier fields
3. WHEN a user double-clicks a supplier row THEN THE Desktop_App SHALL display an edit form with current data
4. WHEN a user clicks delete on a supplier THEN THE Desktop_App SHALL show a confirmation dialog before soft-deleting
5. WHEN a supplier has purchase orders THEN THE Desktop_App SHALL prevent deletion and show an error message

### Requirement 4: Full CRUD for Invoices

**User Story:** As a sales clerk, I want to view, edit draft invoices, and cancel invoices from the desktop app, so that I can correct mistakes and manage sales.

#### Acceptance Criteria

1. THE Desktop_App SHALL display an invoices list with columns: number, customer, date, total, paid, status
2. WHEN a user double-clicks an invoice row THEN THE Desktop_App SHALL display invoice details with all items
3. WHEN an invoice status is "draft" THEN THE Desktop_App SHALL allow editing invoice items and details
4. WHEN a user clicks cancel on a confirmed invoice THEN THE Desktop_App SHALL show a confirmation dialog and reason input
5. IF an invoice is cancelled THEN THE Desktop_App SHALL reverse stock movements and update customer balance
6. THE Desktop_App SHALL provide filtering by status, date range, and customer

### Requirement 5: Sales Returns Management

**User Story:** As a sales manager, I want to process partial or full returns against invoices, so that I can handle customer refunds and product returns properly.

#### Acceptance Criteria

1. WHEN a user selects a confirmed/paid invoice THEN THE Desktop_App SHALL enable a "Create Return" action
2. WHEN creating a return THEN THE Desktop_App SHALL display original invoice items with returnable quantities
3. THE Desktop_App SHALL validate that return quantity does not exceed original quantity minus already returned quantity
4. WHEN a return is created THEN THE Desktop_App SHALL add returned quantities back to stock
5. WHEN a return is created THEN THE Desktop_App SHALL create a stock movement record with type "return"
6. WHEN a return is created THEN THE Desktop_App SHALL reduce the customer's balance by the return amount
7. THE Desktop_App SHALL calculate return totals including original discounts and taxes proportionally
8. THE Desktop_App SHALL require a reason for each return
9. THE Desktop_App SHALL display a returns list with columns: number, original invoice, date, total, reason

### Requirement 6: Stock Movements View

**User Story:** As an inventory manager, I want to view stock movement history, so that I can track all inventory changes and audit stock levels.

#### Acceptance Criteria

1. THE Desktop_App SHALL display a stock movements list with columns: date, product, warehouse, type, quantity, balance before, balance after, reference
2. THE Desktop_App SHALL provide filtering by product, warehouse, movement type, and date range
3. WHEN a user clicks on a movement THEN THE Desktop_App SHALL display full details including source document reference
4. THE Desktop_App SHALL color-code movements by type (green for in, red for out, yellow for adjustment)

### Requirement 7: Full CRUD for Expenses

**User Story:** As an accountant, I want to create, view, edit, and delete expenses from the desktop app, so that I can track all business expenses.

#### Acceptance Criteria

1. THE Desktop_App SHALL display an expenses list with columns: number, category, description, date, amount
2. WHEN a user clicks "Add Expense" THEN THE Desktop_App SHALL display a form with category, date, amount, payee, description
3. WHEN a user double-clicks an expense row THEN THE Desktop_App SHALL display an edit form with current data
4. WHEN a user clicks delete on an expense THEN THE Desktop_App SHALL show a confirmation dialog before soft-deleting
5. THE Desktop_App SHALL provide filtering by category and date range

### Requirement 8: Full CRUD for Categories

**User Story:** As an inventory manager, I want to manage product categories from the desktop app, so that I can organize products hierarchically.

#### Acceptance Criteria

1. THE Desktop_App SHALL display a categories list with columns: name, parent category, product count
2. WHEN a user clicks "Add Category" THEN THE Desktop_App SHALL display a form with name, parent, description
3. WHEN a user double-clicks a category row THEN THE Desktop_App SHALL display an edit form with current data
4. WHEN a user clicks delete on a category THEN THE Desktop_App SHALL show a confirmation dialog
5. WHEN a category has products THEN THE Desktop_App SHALL prevent deletion and show an error message

### Requirement 9: Full CRUD for Units

**User Story:** As an administrator, I want to manage units of measure from the desktop app, so that I can define measurement units for products.

#### Acceptance Criteria

1. THE Desktop_App SHALL display a units list with columns: name, symbol, product count
2. WHEN a user clicks "Add Unit" THEN THE Desktop_App SHALL display a form with name, name_en, symbol
3. WHEN a user double-clicks a unit row THEN THE Desktop_App SHALL display an edit form with current data
4. WHEN a user clicks delete on a unit THEN THE Desktop_App SHALL show a confirmation dialog
5. WHEN a unit is used by products THEN THE Desktop_App SHALL prevent deletion and show an error message

### Requirement 10: Full CRUD for Warehouses

**User Story:** As an inventory manager, I want to manage warehouses from the desktop app, so that I can configure storage locations.

#### Acceptance Criteria

1. THE Desktop_App SHALL display a warehouses list with columns: code, name, address, is default
2. WHEN a user clicks "Add Warehouse" THEN THE Desktop_App SHALL display a form with code, name, address, is_default
3. WHEN a user double-clicks a warehouse row THEN THE Desktop_App SHALL display an edit form with current data
4. WHEN a user clicks delete on a warehouse THEN THE Desktop_App SHALL show a confirmation dialog
5. WHEN a warehouse has stock THEN THE Desktop_App SHALL prevent deletion and show an error message
6. WHEN setting a warehouse as default THEN THE Desktop_App SHALL unset any previous default warehouse

### Requirement 11: Full CRUD for Expense Categories

**User Story:** As an accountant, I want to manage expense categories from the desktop app, so that I can organize expenses by type.

#### Acceptance Criteria

1. THE Desktop_App SHALL display an expense categories list with columns: name, parent, expense count
2. WHEN a user clicks "Add Category" THEN THE Desktop_App SHALL display a form with name, parent, description
3. WHEN a user double-clicks a category row THEN THE Desktop_App SHALL display an edit form with current data
4. WHEN a user clicks delete on a category THEN THE Desktop_App SHALL show a confirmation dialog
5. WHEN a category has expenses THEN THE Desktop_App SHALL prevent deletion and show an error message

### Requirement 12: Purchase Orders Full Management

**User Story:** As a purchasing manager, I want to view, edit, and manage purchase order status from the desktop app, so that I can track procurement.

#### Acceptance Criteria

1. THE Desktop_App SHALL display purchase orders list with columns: number, supplier, date, total, status
2. WHEN a user double-clicks a purchase order THEN THE Desktop_App SHALL display full details with items
3. WHEN a purchase order status is "draft" THEN THE Desktop_App SHALL allow editing items and details
4. THE Desktop_App SHALL provide actions to change status: approve, mark as ordered, receive goods
5. WHEN receiving goods THEN THE Desktop_App SHALL update stock levels and create stock movements
6. THE Desktop_App SHALL provide filtering by status, supplier, and date range

### Requirement 13: Payments Management

**User Story:** As an accountant, I want to view and manage customer payments from the desktop app, so that I can track receivables.

#### Acceptance Criteria

1. THE Desktop_App SHALL display a payments list with columns: number, customer, date, amount, method, invoice
2. WHEN a user clicks "Add Payment" THEN THE Desktop_App SHALL display a form with customer, amount, method, invoice allocation
3. WHEN a user double-clicks a payment row THEN THE Desktop_App SHALL display payment details with allocations
4. THE Desktop_App SHALL support allocating one payment to multiple invoices
5. THE Desktop_App SHALL provide filtering by customer, date range, and payment method

### Requirement 14: Data Tables Enhancement

**User Story:** As a user, I want consistent data table functionality across all views, so that I can efficiently work with large datasets.

#### Acceptance Criteria

1. THE Desktop_App SHALL provide pagination for all data tables with configurable page size
2. THE Desktop_App SHALL provide column sorting by clicking column headers
3. THE Desktop_App SHALL provide a search box that filters across visible columns
4. THE Desktop_App SHALL display row count and current page information
5. THE Desktop_App SHALL remember user's preferred page size per view
