# Design Document: Purchase Order Form UI Improvement

## Overview

This design document describes the UI improvements for the PurchaseOrderFormDialog to maximize the products table visibility and enable smooth scrolling. The changes mirror the improvements made to the InvoiceFormDialog, adapting them for the purchase order context.

## Architecture

The changes are localized to the `PurchaseOrderFormDialog` class in `frontend/src/views/purchases/__init__.py`. No new classes or modules are required.

### Current Structure
```
PurchaseOrderFormDialog
├── Header Section (title)
├── Content Layout (horizontal)
│   ├── Left Column
│   │   ├── Info Card (supplier, warehouse, dates)
│   │   └── Items Card (product entry + table)
│   └── Right Column
│       └── Summary Card (totals, notes, buttons)
└── Error Label
```

### Target Structure
```
PurchaseOrderFormDialog
├── Header Section (compact title)
├── Content Layout (horizontal)
│   ├── Left Column (stretch factor: 7)
│   │   ├── Info Card (compact, max 100px)
│   │   ├── Entry Section (compact, max 70px)
│   │   └── Items Table (expandable, min 300px, stretch)
│   └── Right Column (stretch factor: 1)
│       └── Summary Card (fixed 320px width)
└── Error Label
```

## Components and Interfaces

### Modified Components

#### 1. Info Card (Header)
- Reduce `setContentsMargins` from (20, 20, 20, 20) to (12, 12, 12, 12)
- Reduce grid spacing from 15 to 10
- Set `setMaximumHeight(100)`

#### 2. Entry Section
- Extract from items_card into separate compact section
- Set spacing to 8px
- Set `setMaximumHeight(70)`

#### 3. Items Table
- Remove any `setMaximumHeight` constraint
- Set `setMinimumHeight(300)`
- Add stretch factor to layout
- Configure scroll policy: `setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)`
- Add styling for emphasis (border/shadow)

#### 4. Summary Card
- Set `setFixedWidth(320)`
- Reduce internal spacing
- Adjust layout ratio to 8:1 (left:right columns)

### Method Modifications

#### `setup_ui()` Changes
```python
# Info card compact layout
info_card_layout.setContentsMargins(12, 12, 12, 12)
info_card.setMaximumHeight(100)

# Entry section compact
entry_layout.setSpacing(8)
entry_widget.setMaximumHeight(70)

# Items table expansion
self.items_table.setMinimumHeight(300)
# Remove setMaximumHeight if present
items_card_layout.addWidget(self.items_table, 1)  # stretch factor

# Summary card fixed width
summary_card.setFixedWidth(320)
```

#### `update_items_table()` Changes
```python
def update_items_table(self):
    # ... existing code ...
    
    # Auto-scroll to last item
    if self.items:
        last_row = len(self.items) - 1
        self.items_table.scrollToItem(
            self.items_table.item(last_row, 0),
            QAbstractItemView.EnsureVisible
        )
```

## Data Models

No data model changes required. This is a UI-only modification.

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Auto-scroll on Item Addition

*For any* purchase order form with items, when a new product is added, the items table should scroll to make the newly added item visible.

**Validates: Requirements 2.3**

## Error Handling

No new error handling required. Existing error handling in the form remains unchanged:
- Validation errors displayed via MessageDialog
- API errors caught and displayed to user
- Form state preserved on validation failure

## Testing Strategy

### Unit Tests
- Verify UI configuration values (padding, spacing, heights)
- Verify scroll policy settings
- Verify layout stretch factors

### Manual Testing
- Add 10+ products and verify scrolling works
- Resize dialog and verify table expands/contracts
- Verify all existing functionality (save, cancel, totals)
- Compare visual appearance with InvoiceFormDialog

### Property-Based Testing
Due to the UI-focused nature of this feature, property-based testing is limited. The main testable property is:
- Auto-scroll behavior: For any sequence of product additions, the last added item should be visible

Testing framework: pytest with PySide6 test utilities
