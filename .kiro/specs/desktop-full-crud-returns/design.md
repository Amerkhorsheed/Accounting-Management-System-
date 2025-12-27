# Design Document: Desktop Full CRUD & Sales Returns

## Overview

This design document describes the architecture and implementation approach for bringing the PySide6 desktop application to full feature parity with the Django admin interface. The implementation follows the existing architecture patterns (Service Layer, Repository Pattern, MVC) and extends the current codebase.

The key additions are:
1. Enhanced CRUD operations for all entities with Edit/Delete capabilities
2. Sales Returns module with full stock and financial impact processing
3. Stock Movements view for inventory auditing
4. Enhanced data tables with pagination, sorting, and filtering

## Architecture

### Component Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     DESKTOP APPLICATION                          │
├─────────────────────────────────────────────────────────────────┤
│  Views Layer                                                     │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │ CustomersView│ │ ProductsView │ │ ReturnsView  │            │
│  │ (Full CRUD)  │ │ (Full CRUD)  │ │ (Create/List)│            │
│  └──────────────┘ └──────────────┘ └──────────────┘            │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │SuppliersView │ │ InvoicesView │ │StockMovements│            │
│  │ (Full CRUD)  │ │ (View/Cancel)│ │   View       │            │
│  └──────────────┘ └──────────────┘ └──────────────┘            │
├─────────────────────────────────────────────────────────────────┤
│  Widgets Layer                                                   │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │  DataTable   │ │  FormDialog  │ │ReturnDialog  │            │
│  │ (Enhanced)   │ │  (Reusable)  │ │              │            │
│  └──────────────┘ └──────────────┘ └──────────────┘            │
├─────────────────────────────────────────────────────────────────┤
│  Services Layer (API Client)                                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                      api.py                               │  │
│  │  - CRUD methods for all entities                          │  │
│  │  - Sales returns methods                                  │  │
│  │  - Stock movements methods                                │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼ HTTP/REST
┌─────────────────────────────────────────────────────────────────┐
│                     BACKEND API                                  │
├─────────────────────────────────────────────────────────────────┤
│  ViewSets (DRF)                                                  │
│  - CustomerViewSet (existing, enhanced)                          │
│  - ProductViewSet (existing)                                     │
│  - InvoiceViewSet (existing, add cancel action)                  │
│  - SalesReturnViewSet (existing, add create action)              │
│  - StockMovementViewSet (new)                                    │
├─────────────────────────────────────────────────────────────────┤
│  Services Layer                                                  │
│  - SalesService.create_sales_return() (existing)                 │
│  - SalesService.cancel_invoice() (new)                           │
│  - InventoryService (existing)                                   │
├─────────────────────────────────────────────────────────────────┤
│  Models (existing)                                               │
│  - SalesReturn, SalesReturnItem                                  │
│  - StockMovement                                                 │
│  - Invoice, InvoiceItem                                          │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow for Sales Return

```
User Action: Create Return
        │
        ▼
┌─────────────────┐
│  ReturnDialog   │ ─── Validates quantities, calculates totals
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   API Client    │ ─── POST /api/v1/sales/invoices/{id}/return_items/
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  SalesService   │ ─── create_sales_return()
│                 │     1. Validate invoice status
│                 │     2. Validate return quantities
│                 │     3. Create SalesReturn record
│                 │     4. Create SalesReturnItem records
│                 │     5. Add stock back (InventoryService)
│                 │     6. Update customer balance
│                 │     7. Return created object
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│InventoryService│ ─── add_stock()
│                 │     1. Update Stock.quantity
│                 │     2. Create StockMovement (type=return)
└─────────────────┘
```

## Components and Interfaces

### 1. Enhanced DataTable Widget

The existing DataTable widget will be enhanced with:

```python
class DataTable(QWidget):
    """
    Enhanced data table with full CRUD support.
    
    Signals:
        add_clicked: Emitted when add button clicked
        edit_clicked(row, data): Emitted when edit action triggered
        delete_clicked(row, data): Emitted when delete action triggered
        view_clicked(row, data): Emitted when view action triggered
        row_double_clicked(row, data): Emitted on double-click
        page_changed(page): Emitted when page changes
        sort_changed(column, order): Emitted when sort changes
    """
    
    def __init__(self, columns: List[dict], actions: List[str] = None):
        """
        Args:
            columns: List of column definitions
            actions: List of enabled actions ['view', 'edit', 'delete']
        """
        
    def set_data(self, data: List[dict], total_count: int = None):
        """Set table data with optional total for pagination."""
        
    def set_page(self, page: int, page_size: int):
        """Set current page and page size."""
        
    def get_selected_row(self) -> Optional[dict]:
        """Get currently selected row data."""
```

### 2. Sales Return Dialog

```python
class SalesReturnDialog(QDialog):
    """
    Dialog for creating sales returns.
    
    Displays original invoice items and allows selecting
    quantities to return with reasons.
    """
    
    saved = Signal(dict)  # Emits return data
    
    def __init__(self, invoice: dict, parent=None):
        """
        Args:
            invoice: Invoice data with items
        """
        
    def get_return_data(self) -> dict:
        """
        Get return data for API submission.
        
        Returns:
            {
                'return_date': date,
                'reason': str,
                'notes': str,
                'items': [
                    {
                        'invoice_item_id': int,
                        'quantity': Decimal,
                        'reason': str
                    }
                ]
            }
        """
```

### 3. API Client Extensions

```python
class APIClient:
    """Extended API client with new methods."""
    
    # Sales Returns
    def create_sales_return(self, invoice_id: int, data: dict) -> dict:
        """Create a sales return for an invoice."""
        return self.post(f'sales/invoices/{invoice_id}/return_items/', data)
    
    def get_sales_returns(self, params: dict = None) -> dict:
        """Get list of sales returns."""
        return self.get('sales/returns/', params)
    
    def get_sales_return(self, return_id: int) -> dict:
        """Get sales return details."""
        return self.get(f'sales/returns/{return_id}/')
    
    # Stock Movements
    def get_stock_movements(self, params: dict = None) -> dict:
        """Get stock movements with filters."""
        return self.get('inventory/movements/', params)
    
    # Invoice Actions
    def cancel_invoice(self, invoice_id: int, reason: str) -> dict:
        """Cancel an invoice."""
        return self.post(f'sales/invoices/{invoice_id}/cancel/', {'reason': reason})
    
    # Categories
    def get_categories(self, params: dict = None) -> dict:
        return self.get('inventory/categories/', params)
    
    def create_category(self, data: dict) -> dict:
        return self.post('inventory/categories/', data)
    
    def update_category(self, category_id: int, data: dict) -> dict:
        return self.patch(f'inventory/categories/{category_id}/', data)
    
    def delete_category(self, category_id: int) -> None:
        return self.delete(f'inventory/categories/{category_id}/')
    
    # Units
    def get_units(self, params: dict = None) -> dict:
        return self.get('inventory/units/', params)
    
    def create_unit(self, data: dict) -> dict:
        return self.post('inventory/units/', data)
    
    def update_unit(self, unit_id: int, data: dict) -> dict:
        return self.patch(f'inventory/units/{unit_id}/', data)
    
    def delete_unit(self, unit_id: int) -> None:
        return self.delete(f'inventory/units/{unit_id}/')
    
    # Warehouses
    def get_warehouses(self, params: dict = None) -> dict:
        return self.get('inventory/warehouses/', params)
    
    def create_warehouse(self, data: dict) -> dict:
        return self.post('inventory/warehouses/', data)
    
    def update_warehouse(self, warehouse_id: int, data: dict) -> dict:
        return self.patch(f'inventory/warehouses/{warehouse_id}/', data)
    
    def delete_warehouse(self, warehouse_id: int) -> None:
        return self.delete(f'inventory/warehouses/{warehouse_id}/')
    
    # Expense Categories
    def get_expense_categories(self, params: dict = None) -> dict:
        return self.get('expenses/categories/', params)
    
    def create_expense_category(self, data: dict) -> dict:
        return self.post('expenses/categories/', data)
    
    def update_expense_category(self, category_id: int, data: dict) -> dict:
        return self.patch(f'expenses/categories/{category_id}/', data)
    
    def delete_expense_category(self, category_id: int) -> None:
        return self.delete(f'expenses/categories/{category_id}/')
```

### 4. Backend Service Extensions

```python
# backend/apps/sales/services.py

class SalesService:
    @staticmethod
    @transaction.atomic
    def cancel_invoice(
        invoice_id: int,
        reason: str,
        user=None
    ) -> Invoice:
        """
        Cancel an invoice and reverse all effects.
        
        1. Validate invoice can be cancelled
        2. Reverse stock movements (add stock back)
        3. Reverse customer balance changes
        4. Reverse any payments (create credit)
        5. Update invoice status to cancelled
        
        Args:
            invoice_id: Invoice to cancel
            reason: Reason for cancellation
            user: User performing cancellation
            
        Returns:
            Updated Invoice
            
        Raises:
            InvalidOperationException: If invoice cannot be cancelled
        """
```

## Data Models

### Existing Models Used

The implementation uses existing models without modification:

1. **SalesReturn** - Header for return transaction
2. **SalesReturnItem** - Line items for return
3. **StockMovement** - Inventory movement records
4. **Invoice/InvoiceItem** - Original sale records
5. **Customer** - Customer with balance tracking

### Return Calculation Logic

```python
def calculate_return_item_total(invoice_item, return_quantity):
    """
    Calculate return amount for an item.
    
    Applies original discount and tax rates proportionally.
    """
    unit_price = invoice_item.unit_price
    discount_percent = invoice_item.discount_percent
    tax_rate = invoice_item.tax_rate
    
    subtotal = return_quantity * unit_price
    discount = (subtotal * discount_percent) / 100
    taxable = subtotal - discount
    tax = (taxable * tax_rate) / 100
    
    return taxable + tax
```

## Error Handling

### Frontend Error Handling

All API calls use the existing `@handle_ui_error` decorator which:
1. Catches `ApiException` and displays error message
2. Catches network errors and displays connection error
3. Logs errors for debugging

### Backend Error Handling

The backend uses custom exceptions:
- `ValidationException` - Invalid input data
- `InvalidOperationException` - Operation not allowed in current state
- `InsufficientStockException` - Not enough stock
- `NotFoundException` - Resource not found

### Validation Rules

1. **Return Quantity Validation**:
   - Return quantity must be > 0
   - Return quantity must not exceed (original quantity - already returned quantity)

2. **Invoice Status Validation**:
   - Returns only allowed for: confirmed, paid, partial
   - Cancellation only allowed for: draft, confirmed

3. **Delete Validation**:
   - Customers with invoices cannot be deleted
   - Products with stock movements cannot be deleted
   - Categories with products cannot be deleted
   - Units used by products cannot be deleted
   - Warehouses with stock cannot be deleted



## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Entity Deletion Protection

*For any* entity (Customer, Product, Supplier, Category, Unit, Warehouse, ExpenseCategory) that has dependent records, attempting to delete it SHALL result in a rejection with an appropriate error message, and the entity SHALL remain unchanged in the database.

**Validates: Requirements 1.5, 2.5, 3.5, 8.5, 9.5, 10.5, 11.5**

### Property 2: Draft Document Editability

*For any* document (Invoice, PurchaseOrder) with status "draft", editing operations SHALL be allowed. *For any* document with status other than "draft", editing operations SHALL be rejected.

**Validates: Requirements 4.3, 12.3**

### Property 3: Return Quantity Validation

*For any* sales return attempt, the return quantity for each item SHALL NOT exceed (original_quantity - already_returned_quantity). If this constraint is violated, the return SHALL be rejected.

**Validates: Requirements 5.3**

### Property 4: Return Stock Restoration

*For any* successfully created sales return, the stock quantity for each returned product SHALL increase by exactly the returned quantity (in base units).

**Validates: Requirements 5.4**

### Property 5: Return Stock Movement Creation

*For any* successfully created sales return, a StockMovement record with movement_type="return" SHALL be created for each returned item, with quantity matching the returned quantity.

**Validates: Requirements 5.5**

### Property 6: Return Customer Balance Adjustment

*For any* successfully created sales return with total amount T, the customer's current_balance SHALL decrease by exactly T.

**Validates: Requirements 5.6**

### Property 7: Return Total Calculation

*For any* return item with quantity Q from an invoice item with unit_price P, discount_percent D, and tax_rate T, the return item total SHALL equal: ((Q * P) - ((Q * P) * D / 100)) * (1 + T / 100).

**Validates: Requirements 5.7**

### Property 8: Return Reason Required

*For any* sales return creation attempt without a reason, the operation SHALL be rejected with a validation error.

**Validates: Requirements 5.8**

### Property 9: Invoice Cancellation Reversal

*For any* successfully cancelled invoice, the stock quantities for all items SHALL be restored to their pre-sale levels, and the customer's current_balance SHALL decrease by the invoice total.

**Validates: Requirements 4.5**

### Property 10: Goods Receipt Stock Update

*For any* goods receipt (GRN) creation, the stock quantity for each received product SHALL increase by exactly the received quantity (in base units), and a StockMovement record with movement_type="in" SHALL be created.

**Validates: Requirements 12.5**

### Property 11: Single Default Warehouse

*For any* warehouse set as default, there SHALL be exactly one warehouse with is_default=True in the system at any time.

**Validates: Requirements 10.6**

### Property 12: Payment Allocation Consistency

*For any* payment with allocations, the sum of all allocation amounts SHALL NOT exceed the payment amount, and each allocation amount SHALL NOT exceed the invoice's remaining amount.

**Validates: Requirements 13.4**

## Testing Strategy

### Dual Testing Approach

This implementation uses both unit tests and property-based tests:

1. **Unit Tests**: Verify specific examples, edge cases, and UI interactions
2. **Property-Based Tests**: Verify universal properties across randomly generated inputs

### Property-Based Testing Framework

- **Framework**: Hypothesis (Python)
- **Minimum Iterations**: 100 per property test
- **Tag Format**: `Feature: desktop-full-crud-returns, Property {number}: {property_text}`

### Test Categories

#### Backend Service Tests (Property-Based)

```python
# tests/sales/test_returns_properties.py

from hypothesis import given, strategies as st
from decimal import Decimal

class TestSalesReturnProperties:
    """
    Property-based tests for sales return functionality.
    """
    
    @given(
        original_qty=st.decimals(min_value=1, max_value=1000),
        returned_qty=st.decimals(min_value=0, max_value=500)
    )
    def test_return_quantity_validation(self, original_qty, returned_qty):
        """
        Feature: desktop-full-crud-returns, Property 3: Return Quantity Validation
        
        For any return attempt, quantity must not exceed available.
        """
        # Test implementation
        
    @given(
        return_qty=st.decimals(min_value=1, max_value=100),
        initial_stock=st.decimals(min_value=0, max_value=1000)
    )
    def test_return_stock_restoration(self, return_qty, initial_stock):
        """
        Feature: desktop-full-crud-returns, Property 4: Return Stock Restoration
        
        For any return, stock increases by returned quantity.
        """
        # Test implementation
```

#### Backend Model Tests (Unit)

```python
# tests/sales/test_returns_unit.py

class TestSalesReturnUnit:
    """Unit tests for sales return edge cases."""
    
    def test_return_with_zero_quantity_rejected(self):
        """Return with zero quantity should be rejected."""
        
    def test_return_for_draft_invoice_rejected(self):
        """Return for draft invoice should be rejected."""
        
    def test_return_creates_movement_record(self):
        """Return should create stock movement with correct type."""
```

#### Frontend Tests (Unit)

```python
# tests/frontend/test_return_dialog.py

class TestSalesReturnDialog:
    """Unit tests for return dialog UI."""
    
    def test_dialog_shows_invoice_items(self):
        """Dialog should display all invoice items."""
        
    def test_quantity_spinner_max_is_available(self):
        """Quantity spinner max should be available quantity."""
        
    def test_reason_field_required(self):
        """Reason field should be required for submission."""
```

### Test Data Generation

For property-based tests, use Hypothesis strategies:

```python
# tests/strategies.py

from hypothesis import strategies as st

# Generate valid invoice items
invoice_item_strategy = st.fixed_dictionaries({
    'product_id': st.integers(min_value=1),
    'quantity': st.decimals(min_value=Decimal('0.01'), max_value=Decimal('1000')),
    'unit_price': st.decimals(min_value=Decimal('0.01'), max_value=Decimal('10000')),
    'discount_percent': st.decimals(min_value=Decimal('0'), max_value=Decimal('100')),
    'tax_rate': st.decimals(min_value=Decimal('0'), max_value=Decimal('50')),
})

# Generate valid return items
return_item_strategy = st.fixed_dictionaries({
    'invoice_item_id': st.integers(min_value=1),
    'quantity': st.decimals(min_value=Decimal('0.01'), max_value=Decimal('100')),
    'reason': st.text(min_size=1, max_size=255),
})
```

### Integration Test Scenarios

1. **Full Return Flow**: Create invoice → Confirm → Create full return → Verify stock restored
2. **Partial Return Flow**: Create invoice → Confirm → Create partial return → Verify partial stock restored
3. **Multiple Returns**: Create invoice → Multiple partial returns → Verify cumulative limits
4. **Cancellation Flow**: Create invoice → Confirm → Cancel → Verify full reversal
