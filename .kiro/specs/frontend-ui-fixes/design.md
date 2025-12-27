# Design Document: Frontend UI Fixes

## Overview

This design addresses critical UI functionality issues in the PySide6 desktop frontend where buttons for creating invoices and purchase orders are not connected to handlers, and reports are not displaying data. The solution involves connecting button click handlers, implementing form dialogs for data entry, and ensuring proper data loading in report views.

## Architecture

The frontend follows a layered architecture:

```
┌─────────────────────────────────────────────────────────┐
│                    Views Layer                          │
│  (InvoicesView, PurchaseOrdersView, ReportsView)       │
├─────────────────────────────────────────────────────────┤
│                   Widgets Layer                         │
│  (DataTable, FormDialog, MessageDialog)                │
├─────────────────────────────────────────────────────────┤
│                  Services Layer                         │
│  (api.py - REST API client)                            │
├─────────────────────────────────────────────────────────┤
│                   Backend API                           │
│  (Django REST Framework)                               │
└─────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. InvoicesView Enhancements

**Current State**: Button exists but no click handler connected.

**Solution**: Connect `add_btn.clicked` signal to `add_invoice()` method.

```python
# In InvoicesView.setup_ui()
self.table.add_btn.setText("➕ فاتورة جديدة")
self.table.add_btn.clicked.connect(self.add_invoice)  # ADD THIS LINE

# New method to add
def add_invoice(self):
    """Open dialog to create new invoice."""
    dialog = InvoiceFormDialog(parent=self)
    dialog.saved.connect(self.save_invoice)
    dialog.exec()

def save_invoice(self, data: dict):
    """Save invoice via API."""
    result = api.create_invoice(data)
    if result.get('id'):
        api.confirm_invoice(result['id'])
    MessageDialog.success(self, "نجاح", "تم إنشاء الفاتورة بنجاح")
    self.refresh()
```

### 2. InvoiceFormDialog Component

**New Component**: A specialized form dialog for invoice creation.

```python
class InvoiceFormDialog(QDialog):
    """Dialog for creating/editing invoices."""
    saved = Signal(dict)
    
    def __init__(self, data=None, parent=None):
        super().__init__(parent)
        self.data = data or {}
        self.items = []
        self.customers_cache = []
        self.warehouses_cache = []
        self.products_cache = []
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """Build the form UI."""
        # Customer dropdown
        # Invoice type (cash/credit)
        # Warehouse dropdown
        # Items table with add/remove
        # Totals display
        # Save/Cancel buttons
    
    def load_data(self):
        """Load customers, warehouses, products from API."""
        self.customers_cache = api.get_customers().get('results', [])
        self.warehouses_cache = api.get_warehouses().get('results', [])
        self.products_cache = api.get_products().get('results', [])
    
    def validate(self) -> bool:
        """Validate form data."""
        invoice_type = self.type_combo.currentData()
        if invoice_type == 'credit' and not self.customer_combo.currentData():
            MessageDialog.warning(self, "تنبيه", "يجب اختيار العميل للبيع الآجل")
            return False
        if not self.items:
            MessageDialog.warning(self, "تنبيه", "يجب إضافة منتج واحد على الأقل")
            return False
        return True
    
    def save(self):
        """Emit saved signal with form data."""
        if self.validate():
            self.saved.emit(self.get_data())
            self.accept()
```

### 3. PurchaseOrdersView Enhancements

**Current State**: Button exists but no click handler connected.

**Solution**: Connect `add_btn.clicked` signal to `add_purchase_order()` method.

```python
# In PurchaseOrdersView.setup_ui()
self.table.add_btn.setText("➕ أمر شراء جديد")
self.table.add_btn.clicked.connect(self.add_purchase_order)  # ADD THIS LINE

# New method to add
def add_purchase_order(self):
    """Open dialog to create new purchase order."""
    dialog = PurchaseOrderFormDialog(parent=self)
    dialog.saved.connect(self.save_purchase_order)
    dialog.exec()

def save_purchase_order(self, data: dict):
    """Save purchase order via API."""
    api.create_purchase_order(data)
    MessageDialog.success(self, "نجاح", "تم إنشاء أمر الشراء بنجاح")
    self.refresh()
```

### 4. PurchaseOrderFormDialog Component

**New Component**: A specialized form dialog for purchase order creation.

```python
class PurchaseOrderFormDialog(QDialog):
    """Dialog for creating/editing purchase orders."""
    saved = Signal(dict)
    
    def __init__(self, data=None, parent=None):
        super().__init__(parent)
        self.data = data or {}
        self.items = []
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """Build the form UI."""
        # Supplier dropdown
        # Warehouse dropdown
        # Expected delivery date
        # Items table with add/remove
        # Notes field
        # Totals display
        # Save/Cancel buttons
    
    def load_data(self):
        """Load suppliers, warehouses, products from API."""
        self.suppliers_cache = api.get_suppliers().get('results', [])
        self.warehouses_cache = api.get_warehouses().get('results', [])
        self.products_cache = api.get_products().get('results', [])
```

### 5. Reports View Data Loading

**Current State**: Report views exist but may not be loading data properly.

**Solution**: Ensure `refresh()` method is called on view activation and data is properly displayed.

```python
# In ReportsView or specific report views
def refresh(self):
    """Load report data from API."""
    try:
        self.show_loading()
        data = api.get_receivables_report()  # or appropriate report endpoint
        if data and data.get('customers'):
            self.display_data(data)
        else:
            self.show_empty_state("لا توجد بيانات للعرض")
    except ApiException as e:
        self.show_error(str(e))
    finally:
        self.hide_loading()
```

## Data Models

### Invoice Form Data Structure

```python
{
    'customer': int,           # Customer ID (required for credit)
    'warehouse': int,          # Warehouse ID (required)
    'invoice_type': str,       # 'cash' or 'credit'
    'invoice_date': str,       # YYYY-MM-DD format
    'due_date': str,           # YYYY-MM-DD format (for credit)
    'notes': str,              # Optional notes
    'items': [
        {
            'product': int,    # Product ID
            'quantity': float, # Quantity
            'unit_price': float # Unit price
        }
    ]
}
```

### Purchase Order Form Data Structure

```python
{
    'supplier': int,           # Supplier ID (required)
    'warehouse': int,          # Warehouse ID (required)
    'order_date': str,         # YYYY-MM-DD format
    'expected_date': str,      # Expected delivery date
    'notes': str,              # Optional notes
    'items': [
        {
            'product': int,    # Product ID
            'quantity': float, # Quantity
            'unit_price': float # Unit price
        }
    ]
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Invoice Data Submission Correctness

*For any* valid invoice form data with at least one item, submitting the form SHALL result in an API call with all required fields (customer for credit, warehouse, items) correctly populated.

**Validates: Requirements 1.2, 2.1, 2.2, 2.3, 2.4**

### Property 2: Credit Invoice Customer Requirement

*For any* invoice with type "credit", the form validation SHALL reject submission if no customer is selected, and accept submission if a customer is selected.

**Validates: Requirements 2.5**

### Property 3: Purchase Order Data Submission Correctness

*For any* valid purchase order form data with at least one item, submitting the form SHALL result in an API call with all required fields (supplier, warehouse, items) correctly populated.

**Validates: Requirements 3.2, 4.1, 4.2, 4.3**

### Property 4: Report Data Fetch on Selection

*For any* report type selection, the system SHALL fetch data from the corresponding API endpoint and display results or an appropriate empty/error state.

**Validates: Requirements 5.2, 5.4, 5.5**

### Property 5: Receivables Report Field Completeness

*For any* customer displayed in the receivables report, the display SHALL include customer name, current balance, credit limit, and overdue amount.

**Validates: Requirements 6.2**

### Property 6: Receivables Filtering Correctness

*For any* customer type filter applied to the receivables report, all displayed customers SHALL match the selected customer type.

**Validates: Requirements 6.4**

### Property 7: Aging Bucket Totals Correctness

*For any* aging bucket in the aging report, the displayed total SHALL equal the sum of all invoice remaining amounts in that bucket.

**Validates: Requirements 7.3**

## Error Handling

### Form Validation Errors

- Display inline validation messages for required fields
- Show warning dialogs for business rule violations (e.g., credit without customer)
- Prevent form submission until validation passes

### API Errors

- Catch `ApiException` in all API calls
- Display user-friendly error messages via `MessageDialog.error()`
- Log detailed errors for debugging

### Data Loading Errors

- Show loading indicators during API calls
- Display empty state messages when no data available
- Show error messages when API calls fail

## Testing Strategy

### Unit Tests

Unit tests will verify specific examples and edge cases:

1. **Button Connection Tests**: Verify buttons are connected to handlers
2. **Form Validation Tests**: Test validation logic with specific inputs
3. **Empty State Tests**: Verify empty state messages appear correctly
4. **Error Handling Tests**: Verify error messages display on API failures

### Property-Based Tests

Property-based tests will use the `hypothesis` library to verify universal properties:

1. **Invoice Submission Property**: Generate random valid invoice data, verify API call correctness
2. **Credit Validation Property**: Generate invoices with/without customers, verify validation
3. **Purchase Order Submission Property**: Generate random valid PO data, verify API call correctness
4. **Report Display Property**: Generate report data, verify all required fields displayed

**Test Configuration**:
- Minimum 100 iterations per property test
- Use `hypothesis` library for Python property-based testing
- Tag format: **Feature: frontend-ui-fixes, Property {number}: {property_text}**
