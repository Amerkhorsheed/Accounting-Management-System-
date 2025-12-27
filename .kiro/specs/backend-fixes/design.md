# Design Document: Backend Fixes

## Overview

This design document outlines the fixes and improvements needed for the Accounting Management System backend to ensure all API endpoints work correctly with the PySide6 frontend. The backend is built with Django REST Framework and uses SQL Server as the database.

The main issues identified are:
1. Authentication endpoint URL mismatch between frontend and backend
2. Missing or incorrect serializer configurations
3. Incomplete service layer implementations
4. Missing error handling middleware
5. Soft delete not properly implemented in ViewSets

## Architecture

The backend follows a layered architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                      API Layer (Views)                       │
│  ViewSets handle HTTP requests and delegate to services      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Service Layer                             │
│  Business logic, transactions, and complex operations        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Data Layer (Models)                       │
│  Django ORM models with soft delete and audit fields         │
└─────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. Authentication Component

**Current Issues:**
- Frontend calls `/auth/token/` but backend has `/auth/login/`
- Missing `/auth/users/me/` endpoint implementation

**Fix:**
- Update `accounts/urls.py` to use correct JWT token endpoints
- Ensure `UserViewSet.me()` action returns proper user data

**Interface:**
```python
# POST /api/v1/auth/login/
Request: {"username": str, "password": str}
Response: {"access": str, "refresh": str}

# POST /api/v1/auth/refresh/
Request: {"refresh": str}
Response: {"access": str}

# GET /api/v1/auth/users/me/
Response: UserSerializer data
```

### 2. Inventory Component

**Current Issues:**
- `by_barcode` action uses GET but frontend sends POST
- Product creation may fail if unit is not provided

**Fix:**
- Update `by_barcode` to accept POST requests
- Add proper validation in `ProductCreateSerializer`

**Interface:**
```python
# POST /api/v1/inventory/products/by_barcode/
Request: {"barcode": str}
Response: ProductDetailSerializer data or 404

# POST /api/v1/inventory/products/
Request: ProductCreateSerializer data
Response: ProductDetailSerializer data
```

### 3. Sales Component

**Current Issues:**
- Invoice creation serializer doesn't properly handle nested items
- Payment creation bypasses service layer

**Fix:**
- Fix `InvoiceCreateSerializer` to properly create items
- Route payment creation through `SalesService`

**Interface:**
```python
# POST /api/v1/sales/invoices/
Request: {
    "invoice_type": str,
    "customer": int,
    "warehouse": int,
    "invoice_date": str,
    "items": [{"product": int, "quantity": decimal, "unit_price": decimal, ...}]
}
Response: InvoiceDetailSerializer data
```

### 4. Purchases Component

**Current Issues:**
- Purchase order item serializer has incorrect field handling
- GRN creation doesn't properly update PO item received quantities

**Fix:**
- Fix `PurchaseOrderCreateSerializer` nested item creation
- Ensure `PurchaseService.receive_goods()` updates all related records

### 5. Expenses Component

**Current Issues:**
- Expense summary action has incorrect import (models imported at end of file)

**Fix:**
- Move import to top of file
- Ensure proper aggregation in summary endpoint

### 6. Core Settings Component

**Current Issues:**
- Currency conversion may fail with division by zero
- Settings bulk update doesn't validate input

**Fix:**
- Add validation for exchange rates
- Add input validation for bulk settings update

## Data Models

The existing data models are well-designed. Key relationships:

```
Product ──┬── Category (FK)
          └── Unit (FK)

Stock ────┬── Product (FK)
          └── Warehouse (FK)

Invoice ──┬── Customer (FK)
          ├── Warehouse (FK)
          └── InvoiceItem[] ── Product (FK)

PurchaseOrder ──┬── Supplier (FK)
                ├── Warehouse (FK)
                └── PurchaseOrderItem[] ── Product (FK)
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Authentication Token Validity
*For any* valid user credentials, logging in SHALL return both access and refresh tokens that can be used for subsequent authenticated requests.
**Validates: Requirements 1.1, 1.2**

### Property 2: Token Refresh Consistency
*For any* valid refresh token, the refresh endpoint SHALL return a new valid access token.
**Validates: Requirements 1.4**

### Property 3: Product Auto-Generation
*For any* product created without explicit code or barcode, the Backend SHALL generate unique values for both fields.
**Validates: Requirements 2.1**

### Property 4: Partial Update Isolation
*For any* PATCH request to update a product, only the fields included in the request SHALL be modified; all other fields SHALL remain unchanged.
**Validates: Requirements 2.2**

### Property 5: Soft Delete Preservation
*For any* deleted product, the record SHALL remain in the database with is_deleted=True and SHALL NOT appear in normal list queries.
**Validates: Requirements 2.3**

### Property 6: Barcode Search Correctness
*For any* barcode search, the Backend SHALL return the exact product matching that barcode or a 404 if no match exists.
**Validates: Requirements 2.4**

### Property 7: Category Tree Structure
*For any* category with children, the tree endpoint SHALL return the category with all its descendants in a nested structure.
**Validates: Requirements 2.5**

### Property 8: Customer Code Auto-Generation
*For any* customer created without explicit code, the Backend SHALL generate a unique code with the CUS prefix.
**Validates: Requirements 3.1**

### Property 9: Invoice Transaction Atomicity
*For any* invoice creation with items, either all items SHALL be created successfully or none SHALL be created (atomic transaction).
**Validates: Requirements 3.2**

### Property 10: Invoice Confirmation Stock Deduction
*For any* confirmed invoice, the stock levels for all items SHALL decrease by the exact quantities specified in the invoice.
**Validates: Requirements 3.3**

### Property 11: Payment Balance Update
*For any* payment recorded, the customer's current_balance SHALL decrease by the payment amount, and if linked to an invoice, the invoice's paid_amount SHALL increase by the same amount.
**Validates: Requirements 3.4**

### Property 12: Statement Running Balance
*For any* customer statement, the running balance after each transaction SHALL equal the previous balance plus debits minus credits.
**Validates: Requirements 3.5**

### Property 13: Supplier Code Auto-Generation
*For any* supplier created without explicit code, the Backend SHALL generate a unique code with the SUP prefix.
**Validates: Requirements 4.1**

### Property 14: Purchase Order Transaction Atomicity
*For any* purchase order creation with items, either all items SHALL be created successfully or none SHALL be created.
**Validates: Requirements 4.2**

### Property 15: Goods Receiving Stock Addition
*For any* goods received, the stock levels SHALL increase by the exact quantities received, and a stock movement record SHALL be created.
**Validates: Requirements 4.4**

### Property 16: Expense Total Calculation
*For any* expense created, the total_amount SHALL equal amount plus tax_amount.
**Validates: Requirements 5.2**

### Property 17: Profit Calculation Correctness
*For any* profit report, gross_profit SHALL equal total revenue minus cost of goods sold, and net_profit SHALL equal gross_profit minus total expenses.
**Validates: Requirements 6.3**

### Property 18: Currency Conversion Formula
*For any* currency conversion, the converted amount SHALL equal (amount × from_currency_rate) ÷ to_currency_rate.
**Validates: Requirements 7.2**

### Property 19: Validation Error Response Format
*For any* validation error, the response SHALL have status 400 and include field-specific error messages.
**Validates: Requirements 8.1**

### Property 20: Stock Movement Balance Tracking
*For any* stock adjustment, the movement record SHALL have balance_before equal to the stock level before adjustment and balance_after equal to the stock level after adjustment.
**Validates: Requirements 9.1**

### Property 21: Insufficient Stock Prevention
*For any* stock deduction request where requested quantity exceeds available quantity, the Backend SHALL raise an InsufficientStockException and NOT modify the stock level.
**Validates: Requirements 9.2**

### Property 22: Low Stock Detection
*For any* product where current stock is less than or equal to minimum_stock, the product SHALL appear in low stock queries.
**Validates: Requirements 9.4**

## Error Handling

All exceptions should be caught and converted to appropriate HTTP responses:

| Exception Type | HTTP Status | Response Format |
|---------------|-------------|-----------------|
| ValidationException | 400 | `{"detail": message, "field": field_name}` |
| InsufficientStockException | 400 | `{"detail": message, "code": "INSUFFICIENT_STOCK"}` |
| NotFoundException | 404 | `{"detail": message}` |
| InvalidOperationException | 400 | `{"detail": message, "code": "INVALID_OPERATION"}` |
| PermissionDeniedException | 403 | `{"detail": message}` |

Add a custom exception handler in Django REST Framework settings:

```python
REST_FRAMEWORK = {
    'EXCEPTION_HANDLER': 'apps.core.exceptions.custom_exception_handler',
}
```

## Testing Strategy

### Dual Testing Approach

The testing strategy employs both unit tests and property-based tests:

1. **Unit Tests**: Verify specific examples and edge cases
2. **Property-Based Tests**: Verify universal properties across all valid inputs

### Property-Based Testing Framework

Use **Hypothesis** for Python property-based testing:

```python
from hypothesis import given, strategies as st
```

### Test Categories

1. **Authentication Tests**
   - Login with valid/invalid credentials
   - Token refresh flow
   - Protected endpoint access

2. **CRUD Operation Tests**
   - Create with auto-generated fields
   - Partial updates
   - Soft delete behavior
   - List filtering

3. **Business Logic Tests**
   - Invoice confirmation and stock deduction
   - Payment processing and balance updates
   - Goods receiving and stock addition

4. **Calculation Tests**
   - Invoice totals
   - Profit calculations
   - Currency conversions

### Test Configuration

Each property-based test should run a minimum of 100 iterations to ensure adequate coverage.

Property tests must be tagged with the format:
`**Feature: backend-fixes, Property {number}: {property_text}**`
