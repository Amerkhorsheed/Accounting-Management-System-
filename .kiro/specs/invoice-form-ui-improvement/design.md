# Design Document: Invoice Form UI Improvement

## Overview

This design improves the invoice creation dialog (InvoiceFormDialog) to maximize the products table visibility and enable smooth scrolling when adding many products. The layout will be restructured to prioritize the products table while keeping header and summary sections compact.

## Architecture

The improved dialog maintains the existing two-column layout but with optimized space allocation:

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Header: Invoice Type Selector (compact)                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────┐  ┌──────────────────┐ │
│  │ Invoice Header Card (compact ~100px)        │  │                  │ │
│  │ [Customer ▼] [Warehouse ▼] [Date] [Due]     │  │  Summary Card    │ │
│  └─────────────────────────────────────────────┘  │  (fixed 320px)   │ │
│                                                    │                  │ │
│  ┌─────────────────────────────────────────────┐  │  - Subtotal      │ │
│  │ Product Entry (compact ~60px)               │  │  - Tax           │ │
│  │ [🔍 Barcode...] [Product ▼] [Qty] [+Add]    │  │  - Total         │ │
│  └─────────────────────────────────────────────┘  │                  │ │
│                                                    │  - Notes         │ │
│  ┌─────────────────────────────────────────────┐  │  - Paid Amount   │ │
│  │                                             │  │  - Remaining     │ │
│  │           Products Table                    │  │                  │ │
│  │         (expandable, scrollable)            │  │  [Save Button]   │ │
│  │                                             │  │  [Cancel]        │ │
│  │  Product    | Qty | Price | Total | ❌      │  │                  │ │
│  │  ─────────────────────────────────────────  │  └──────────────────┘ │
│  │  Item 1     | 2   | 100   | 200   | ❌      │                       │
│  │  Item 2     | 1   | 50    | 50    | ❌      │                       │
│  │  Item 3     | 3   | 75    | 225   | ❌      │                       │
│  │  ...        |     |       |       |         │                       │
│  │  (scrollable when more items)               │                       │
│  │                                             │                       │
│  └─────────────────────────────────────────────┘                       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### Modified Components

#### 1. InvoiceFormDialog.setup_ui()

The main UI setup method will be restructured with the following changes:

**Layout Changes:**
- Remove `setMaximumHeight(400)` constraint from items_table
- Set items_table minimum height to 300px
- Use stretch factors to prioritize table expansion
- Reduce margins and spacing in header and entry sections

**Header Card Modifications:**
- Reduce card padding from 20px to 12px
- Use single-row grid layout for all fields
- Set maximum height of 100px

**Product Entry Modifications:**
- Combine barcode and manual selection into single row
- Remove separator label
- Reduce spacing to 8px
- Set maximum height of 70px

**Items Table Modifications:**
- Remove maximum height constraint
- Add stretch factor of 1 to allow expansion
- Enable auto-scroll to last row on item add
- Ensure vertical scrollbar is always visible when needed

**Summary Card Modifications:**
- Set fixed width of 320px
- Reduce internal spacing
- Use compact layout for totals

### Interface Changes

No API or data model changes required - this is purely a UI/UX improvement.

## Data Models

No changes to data models required.

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

This feature is primarily UI/UX focused. The acceptance criteria relate to visual layout and user interaction, which are not amenable to property-based testing. The testable aspects are:

**Analysis of Acceptance Criteria:**

1.1 - 60% vertical space allocation: This is a visual/layout requirement, not testable via property
1.2 - No max height constraint: This is a code structure requirement, verifiable by code review
1.3 - Proportional expansion on resize: UI behavior, not property-testable

2.1 - Scrollbar display: UI behavior, not property-testable
2.2 - Smooth scrolling: UI behavior, not property-testable
2.3 - Auto-scroll to new item: UI behavior, could be tested as example
2.4 - Minimum height 300px: Code structure requirement, verifiable by code review

3.1-3.3 - Compact header layout: Visual requirements, not property-testable

4.1-4.3 - Compact entry section: Visual requirements, not property-testable

5.1-5.4 - Summary card layout: Visual requirements, not property-testable

6.1-6.3 - Visual hierarchy: Visual requirements, not property-testable

**Conclusion:** No testable properties identified. All requirements relate to visual layout and UI behavior that must be verified through manual testing or visual inspection.

## Error Handling

No new error handling required. The existing error handling for API calls and form validation remains unchanged.

## Testing Strategy

### Manual Testing

Since this is a UI/UX improvement, testing will be primarily manual:

1. **Visual Inspection:**
   - Verify products table occupies majority of vertical space
   - Verify header section is compact
   - Verify summary card has fixed width

2. **Functional Testing:**
   - Add 10+ products and verify scrolling works smoothly
   - Verify new products are visible (auto-scroll)
   - Resize dialog and verify table expands proportionally

3. **Regression Testing:**
   - Verify all existing functionality still works (add product, remove product, save invoice)
   - Verify totals calculate correctly
   - Verify customer/warehouse selection works

### Unit Tests

No new unit tests required as this is purely a layout change with no logic modifications.
