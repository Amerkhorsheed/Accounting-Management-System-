# Requirements Document

## Introduction

This document specifies the requirements for fixing and completing the backend API of the Accounting Management System. The system is a Django REST Framework backend that provides APIs for inventory management, sales, purchases, expenses, and reporting. The frontend (PySide6 desktop application) is unable to perform CRUD operations due to various issues in the backend including missing endpoints, incorrect URL patterns, authentication issues, and incomplete service implementations.

## Glossary

- **Backend**: The Django REST Framework API server providing data and business logic
- **Frontend**: The PySide6 desktop application consuming the backend APIs
- **CRUD**: Create, Read, Update, Delete operations
- **JWT**: JSON Web Token used for authentication
- **ViewSet**: Django REST Framework class providing CRUD operations for a model
- **Serializer**: Django REST Framework class for data validation and transformation
- **Service**: Business logic layer class handling complex operations

## Requirements

### Requirement 1

**User Story:** As a frontend developer, I want the authentication endpoints to work correctly, so that users can login and access protected resources.

#### Acceptance Criteria

1. WHEN a user sends valid credentials to the login endpoint THEN the Backend SHALL return access and refresh JWT tokens
2. WHEN a user sends a request with a valid access token THEN the Backend SHALL authenticate the request and allow access
3. WHEN a user sends a request to the /auth/users/me/ endpoint THEN the Backend SHALL return the current user's profile data
4. WHEN a user's access token expires THEN the Backend SHALL allow token refresh using the refresh token

### Requirement 2

**User Story:** As a frontend developer, I want the inventory API endpoints to work correctly, so that users can manage products, categories, units, and warehouses.

#### Acceptance Criteria

1. WHEN a user sends a POST request to create a product THEN the Backend SHALL validate the data and create the product with auto-generated code and barcode
2. WHEN a user sends a PATCH request to update a product THEN the Backend SHALL update only the specified fields
3. WHEN a user sends a DELETE request for a product THEN the Backend SHALL soft-delete the product by setting is_deleted to true
4. WHEN a user sends a POST request to search by barcode THEN the Backend SHALL return the matching product or a 404 response
5. WHEN a user requests the category tree THEN the Backend SHALL return categories in a hierarchical structure

### Requirement 3

**User Story:** As a frontend developer, I want the sales API endpoints to work correctly, so that users can manage customers, invoices, and payments.

#### Acceptance Criteria

1. WHEN a user sends a POST request to create a customer THEN the Backend SHALL validate the data and create the customer with auto-generated code
2. WHEN a user sends a POST request to create an invoice with items THEN the Backend SHALL create the invoice and all line items in a single transaction
3. WHEN a user confirms an invoice THEN the Backend SHALL deduct stock and update customer balance appropriately
4. WHEN a user records a payment THEN the Backend SHALL update the invoice paid amount and customer balance
5. WHEN a user requests a customer statement THEN the Backend SHALL return all transactions with running balance

### Requirement 4

**User Story:** As a frontend developer, I want the purchases API endpoints to work correctly, so that users can manage suppliers, purchase orders, and goods receiving.

#### Acceptance Criteria

1. WHEN a user sends a POST request to create a supplier THEN the Backend SHALL validate the data and create the supplier with auto-generated code
2. WHEN a user sends a POST request to create a purchase order with items THEN the Backend SHALL create the order and all line items in a single transaction
3. WHEN a user approves a purchase order THEN the Backend SHALL update the status and record the approver
4. WHEN a user receives goods against a purchase order THEN the Backend SHALL create a GRN, update stock levels, and update PO status

### Requirement 5

**User Story:** As a frontend developer, I want the expenses API endpoints to work correctly, so that users can manage expense categories and expense records.

#### Acceptance Criteria

1. WHEN a user sends a POST request to create an expense category THEN the Backend SHALL validate and create the category
2. WHEN a user sends a POST request to create an expense THEN the Backend SHALL calculate total amount and create the expense with auto-generated number
3. WHEN a user approves an expense THEN the Backend SHALL update the approval status and record the approver
4. WHEN a user requests expense summary THEN the Backend SHALL return totals grouped by category

### Requirement 6

**User Story:** As a frontend developer, I want the reports API endpoints to work correctly, so that users can view dashboard and analytical reports.

#### Acceptance Criteria

1. WHEN a user requests the dashboard THEN the Backend SHALL return sales, purchases, expenses, and profit summaries
2. WHEN a user requests a sales report with date range THEN the Backend SHALL return trend data and top customers/products
3. WHEN a user requests a profit report THEN the Backend SHALL calculate gross and net profit with expense breakdown
4. WHEN a user requests an inventory report THEN the Backend SHALL return stock valuation and low stock items

### Requirement 7

**User Story:** As a frontend developer, I want the core settings API endpoints to work correctly, so that users can manage currencies, tax rates, and system settings.

#### Acceptance Criteria

1. WHEN a user requests the primary currency THEN the Backend SHALL return the currency marked as primary
2. WHEN a user requests currency conversion THEN the Backend SHALL calculate the converted amount using exchange rates
3. WHEN a user requests the default tax rate THEN the Backend SHALL return the tax rate marked as default
4. WHEN a user updates system settings THEN the Backend SHALL persist the key-value pairs

### Requirement 8

**User Story:** As a frontend developer, I want proper error handling and validation, so that the frontend receives meaningful error messages.

#### Acceptance Criteria

1. WHEN a validation error occurs THEN the Backend SHALL return a 400 response with field-specific error messages
2. WHEN a resource is not found THEN the Backend SHALL return a 404 response with a descriptive message
3. WHEN a business rule is violated THEN the Backend SHALL return a 400 response with the violation details
4. WHEN an authentication error occurs THEN the Backend SHALL return a 401 response

### Requirement 9

**User Story:** As a frontend developer, I want the stock management operations to work correctly, so that inventory levels are accurately tracked.

#### Acceptance Criteria

1. WHEN stock is adjusted THEN the Backend SHALL create a stock movement record with before/after balances
2. WHEN stock is deducted for a sale THEN the Backend SHALL verify sufficient quantity before deducting
3. WHEN stock is added from a purchase THEN the Backend SHALL update the stock level and record the movement
4. WHEN low stock products are requested THEN the Backend SHALL return products below minimum stock level
