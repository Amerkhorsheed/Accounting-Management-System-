# Design Document: Units Management

## Overview

This design document describes the architecture and implementation approach for a comprehensive Units Management system in the tobacco accounting application. The system enables products to have multiple units of measure with conversion factors, allowing sales and purchases to be conducted in different units (e.g., selling cigarettes by piece, pack, or carton) while maintaining accurate inventory tracking in base units.

## Architecture

The Units Management system follows the existing application architecture with a Django REST backend and PySide6 frontend. The implementation extends the current `Unit` model and introduces a new `ProductUnit` model to handle product-specific unit configurations with conversion factors and pricing.

```
┌─────────────────────────────────────────────────────────────────┐
│                     FRONTEND (PySide6)                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               │
│  │ Units View  │ │Product Form │ │Invoice Form │               │
│  │ (Settings)  │ │(Unit Config)│ │(Unit Select)│               │
│  └─────────────┘ └─────────────┘ └─────────────┘               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼ HTTP/REST
┌─────────────────────────────────────────────────────────────────┐
│                     BACKEND (Django)                            │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               │
│  │ Unit API    │ │ProductUnit  │ │ Sales API   │               │
│  │ ViewSet     │ │ API ViewSet │ │ (Extended)  │               │
│  └─────────────┘ └─────────────┘ └─────────────┘               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     DATABASE                                     │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               │
│  │    Unit     │ │ ProductUnit │ │InvoiceItem  │               │
│  │   (Enhanced)│ │   (New)     │ │ (Extended)  │               │
│  └─────────────┘ └─────────────┘ └─────────────┘               │
└─────────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### Backend Components

#### 1. Enhanced Unit Model (`backend/apps/inventory/models.py`)

```python
class Unit(BaseModel):
    """Unit of measure for products."""
    name = models.CharField(max_length=50, verbose_name='اسم الوحدة')
    name_en = models.CharField(max_length=50, blank=True, null=True, verbose_name='الاسم بالإنجليزية')
    symbol = models.CharField(max_length=10, verbose_name='الرمز')
    is_active = models.BooleanField(default=True, verbose_name='نشط')
    
    class Meta:
        verbose_name = 'وحدة قياس'
        verbose_name_plural = 'وحدات القياس'
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['name'],
                condition=models.Q(is_deleted=False),
                name='unique_unit_name'
            ),
            models.UniqueConstraint(
                fields=['symbol'],
                condition=models.Q(is_deleted=False),
                name='unique_unit_symbol'
            ),
        ]
```

#### 2. New ProductUnit Model (`backend/apps/inventory/models.py`)

```python
class ProductUnit(BaseModel):
    """Product-specific unit configuration with conversion factor and pricing."""
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='product_units',
        verbose_name='المنتج'
    )
    unit = models.ForeignKey(
        Unit,
        on_delete=models.PROTECT,
        related_name='product_units',
        verbose_name='الوحدة'
    )
    conversion_factor = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        default=Decimal('1.0000'),
        verbose_name='معامل التحويل'
    )
    is_base_unit = models.BooleanField(
        default=False,
        verbose_name='الوحدة الأساسية'
    )
    sale_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='سعر البيع'
    )
    cost_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name='سعر التكلفة'
    )
    barcode = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name='الباركود'
    )
    
    class Meta:
        verbose_name = 'وحدة المنتج'
        verbose_name_plural = 'وحدات المنتج'
        unique_together = ['product', 'unit']
        constraints = [
            models.CheckConstraint(
                check=models.Q(conversion_factor__gt=0),
                name='positive_conversion_factor'
            ),
        ]
    
    def convert_to_base(self, quantity: Decimal) -> Decimal:
        """Convert quantity from this unit to base unit."""
        return quantity * self.conversion_factor
    
    def convert_from_base(self, base_quantity: Decimal) -> Decimal:
        """Convert quantity from base unit to this unit."""
        return base_quantity / self.conversion_factor
```

#### 3. Extended InvoiceItem Model (`backend/apps/sales/models.py`)

```python
class InvoiceItem(BaseModel):
    # ... existing fields ...
    
    # New field for unit tracking
    product_unit = models.ForeignKey(
        'inventory.ProductUnit',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='invoice_items',
        verbose_name='وحدة المنتج'
    )
    base_quantity = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        default=Decimal('0.0000'),
        verbose_name='الكمية بالوحدة الأساسية'
    )
```

#### 4. Extended PurchaseOrderItem Model (`backend/apps/purchases/models.py`)

```python
class PurchaseOrderItem(BaseModel):
    # ... existing fields ...
    
    # New field for unit tracking
    product_unit = models.ForeignKey(
        'inventory.ProductUnit',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='purchase_items',
        verbose_name='وحدة المنتج'
    )
    base_quantity = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        default=Decimal('0.0000'),
        verbose_name='الكمية بالوحدة الأساسية'
    )
```

### API Endpoints

#### Unit Management API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/inventory/units/` | List all units |
| POST | `/api/v1/inventory/units/` | Create a new unit |
| GET | `/api/v1/inventory/units/{id}/` | Get unit details |
| PUT | `/api/v1/inventory/units/{id}/` | Update a unit |
| DELETE | `/api/v1/inventory/units/{id}/` | Delete a unit |

#### ProductUnit API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/inventory/products/{id}/units/` | List product units |
| POST | `/api/v1/inventory/products/{id}/units/` | Add unit to product |
| PUT | `/api/v1/inventory/products/{id}/units/{unit_id}/` | Update product unit |
| DELETE | `/api/v1/inventory/products/{id}/units/{unit_id}/` | Remove unit from product |

### Frontend Components

#### 1. UnitsManagementView (`frontend/src/views/settings/units.py`)

A settings page component for managing units with:
- Table displaying all units (name, symbol, name_en, status)
- Add button opening a dialog form
- Edit/Delete actions per row
- Search/filter functionality

#### 2. ProductUnitConfigWidget (`frontend/src/widgets/product_units.py`)

A widget embedded in the product form for configuring product units:
- Table of assigned units with conversion factors and prices
- Add unit button with unit selector
- Inline editing of conversion factor, sale price, cost price
- Base unit indicator and selector

#### 3. UnitSelectorComboBox (`frontend/src/widgets/unit_selector.py`)

A reusable combo box for selecting units in sales/purchase forms:
- Displays available units for the selected product
- Shows unit name and price
- Emits signal when unit changes to update price field

## Data Models

### Entity Relationship Diagram

```
┌─────────────┐       ┌─────────────────┐       ┌─────────────┐
│    Unit     │       │   ProductUnit   │       │   Product   │
├─────────────┤       ├─────────────────┤       ├─────────────┤
│ id          │◄──────│ unit_id         │       │ id          │
│ name        │       │ product_id      │──────►│ name        │
│ name_en     │       │ conversion_factor│       │ code        │
│ symbol      │       │ is_base_unit    │       │ ...         │
│ is_active   │       │ sale_price      │       └─────────────┘
└─────────────┘       │ cost_price      │
                      │ barcode         │
                      └─────────────────┘
                              │
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
    ┌─────────────────┐             ┌─────────────────┐
    │  InvoiceItem    │             │PurchaseOrderItem│
    ├─────────────────┤             ├─────────────────┤
    │ product_unit_id │             │ product_unit_id │
    │ quantity        │             │ quantity        │
    │ base_quantity   │             │ base_quantity   │
    │ unit_price      │             │ unit_price      │
    └─────────────────┘             └─────────────────┘
```

### Database Migration Strategy

1. Add `name_en` field to existing `Unit` model
2. Remove `is_base` field from `Unit` model (moved to ProductUnit)
3. Create new `ProductUnit` model
4. Add `product_unit` and `base_quantity` fields to `InvoiceItem`
5. Add `product_unit` and `base_quantity` fields to `PurchaseOrderItem`
6. Create default units via data migration
7. Migrate existing product-unit relationships to ProductUnit

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Unit CRUD Round-Trip

*For any* valid unit data (name, symbol, name_en), creating a unit and then retrieving it SHALL return the same data that was submitted.

**Validates: Requirements 1.1, 1.2, 1.3**

### Property 2: Unit Name and Symbol Uniqueness

*For any* two units in the system, if both are not deleted, their names SHALL be different AND their symbols SHALL be different.

**Validates: Requirements 1.6**

### Property 3: Unit Deletion Protection

*For any* unit that is associated with at least one ProductUnit, attempting to delete that unit SHALL fail with an error.

**Validates: Requirements 1.4**

### Property 4: Unused Unit Deletion

*For any* unit that is not associated with any ProductUnit, deleting that unit SHALL succeed and the unit SHALL no longer be retrievable.

**Validates: Requirements 1.5**

### Property 5: Product Base Unit Invariant

*For any* product that has at least one ProductUnit, exactly one of its ProductUnits SHALL have `is_base_unit = True` and `conversion_factor = 1`.

**Validates: Requirements 2.3**

### Property 6: Conversion Factor Positivity

*For any* ProductUnit, the conversion_factor SHALL be greater than zero. Attempts to create or update a ProductUnit with conversion_factor <= 0 SHALL be rejected.

**Validates: Requirements 2.6**

### Property 7: Quantity Conversion Correctness

*For any* ProductUnit with conversion_factor `f` and any quantity `q`, converting `q` units to base units SHALL equal `q * f`, and converting `q * f` base units back SHALL equal `q`.

**Validates: Requirements 2.5**

### Property 8: Sales Stock Deduction Correctness

*For any* confirmed invoice item with quantity `q` and ProductUnit with conversion_factor `f`, the stock deduction in base units SHALL equal `q * f`.

**Validates: Requirements 3.4**

### Property 9: Purchase Stock Addition Correctness

*For any* received purchase order item with quantity `q` and ProductUnit with conversion_factor `f`, the stock addition in base units SHALL equal `q * f`.

**Validates: Requirements 4.4**

### Property 10: Line Total Calculation

*For any* invoice item or purchase order item with quantity `q` and unit_price `p`, the line subtotal SHALL equal `q * p`.

**Validates: Requirements 3.3, 4.3**

### Property 11: Default Unit Fallback

*For any* invoice item or purchase order item where no ProductUnit is specified, the system SHALL use the product's base unit and its associated price.

**Validates: Requirements 3.6, 4.6**

### Property 12: Arabic Text Preservation

*For any* unit created with Arabic characters in the name field, retrieving that unit SHALL return the exact same Arabic text.

**Validates: Requirements 6.5**

### Property 13: Stock Display Conversion

*For any* product with stock quantity `s` (in base units) and a ProductUnit with conversion_factor `f`, the displayed quantity in that unit SHALL equal `s / f`.

**Validates: Requirements 5.3**

## Error Handling

### Backend Error Handling

| Error Condition | HTTP Status | Error Code | Message |
|-----------------|-------------|------------|---------|
| Unit name already exists | 400 | `DUPLICATE_UNIT_NAME` | اسم الوحدة موجود مسبقاً |
| Unit symbol already exists | 400 | `DUPLICATE_UNIT_SYMBOL` | رمز الوحدة موجود مسبقاً |
| Unit in use, cannot delete | 400 | `UNIT_IN_USE` | لا يمكن حذف الوحدة لأنها مستخدمة في منتجات |
| Invalid conversion factor | 400 | `INVALID_CONVERSION_FACTOR` | معامل التحويل يجب أن يكون أكبر من صفر |
| Product already has this unit | 400 | `DUPLICATE_PRODUCT_UNIT` | هذه الوحدة مضافة للمنتج مسبقاً |
| Cannot remove base unit | 400 | `CANNOT_REMOVE_BASE_UNIT` | لا يمكن حذف الوحدة الأساسية |
| Unit not found | 404 | `UNIT_NOT_FOUND` | الوحدة غير موجودة |
| ProductUnit not found | 404 | `PRODUCT_UNIT_NOT_FOUND` | وحدة المنتج غير موجودة |

### Frontend Error Handling

- Display validation errors inline in forms
- Show toast notifications for API errors
- Confirm before deleting units
- Prevent form submission with invalid data

## Testing Strategy

### Unit Tests

Unit tests will cover:
- Unit model validation (name, symbol uniqueness)
- ProductUnit model validation (conversion factor > 0)
- Conversion calculations (to_base, from_base methods)
- API endpoint responses and error codes
- Serializer validation

### Property-Based Tests

Property-based tests will use the `hypothesis` library for Python to verify:
- Conversion factor calculations are mathematically correct
- Stock adjustments match expected base unit quantities
- Round-trip data integrity for unit CRUD operations
- Uniqueness constraints are enforced

**Test Configuration:**
- Minimum 100 iterations per property test
- Each test tagged with: **Feature: units-management, Property {number}: {property_text}**

### Integration Tests

Integration tests will verify:
- End-to-end invoice creation with unit selection
- End-to-end purchase order with unit selection
- Stock level updates after sales/purchases
- Default unit migration

### Test Files

| Test File | Coverage |
|-----------|----------|
| `backend/apps/inventory/tests/test_units.py` | Unit model and API tests |
| `backend/apps/inventory/tests/test_product_units.py` | ProductUnit model and API tests |
| `backend/apps/inventory/tests/test_unit_properties.py` | Property-based tests for conversions |
| `backend/apps/sales/tests/test_invoice_units.py` | Invoice unit selection tests |
| `backend/apps/purchases/tests/test_po_units.py` | Purchase order unit selection tests |

