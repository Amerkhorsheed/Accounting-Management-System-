# Requirements Document

## Introduction

This feature improves the UI/UX of the new invoice creation dialog (فاتورة جديدة) in the sales module. The main goal is to make the products table larger and more prominent, with proper scrolling support when adding many products, while keeping other form elements compact and accessible.

## Glossary

- **Invoice_Form_Dialog**: The full-screen dialog for creating new sales invoices
- **Products_Table**: The table widget displaying added products with columns for product name, quantity, price, and total
- **Invoice_Header_Card**: The card containing customer, warehouse, date, and invoice type fields
- **Summary_Card**: The right-side card containing totals, notes, and payment information

## Requirements

### Requirement 1: Maximize Products Table Visibility

**User Story:** As a user, I want the products table to be the largest element on the invoice form, so that I can see all added products clearly without scrolling through a tiny area.

#### Acceptance Criteria

1. THE Invoice_Form_Dialog SHALL allocate at least 60% of the available vertical space to the Products_Table
2. THE Products_Table SHALL have no maximum height constraint that limits its growth
3. WHEN the dialog is resized, THE Products_Table SHALL expand proportionally to fill available space

### Requirement 2: Enable Smooth Scrolling for Products Table

**User Story:** As a user, I want to scroll through the products table smoothly when I add more than 4 products, so that I can see and manage all items in my invoice.

#### Acceptance Criteria

1. WHEN more products are added than can fit in the visible area, THE Products_Table SHALL display a vertical scrollbar
2. THE Products_Table SHALL support smooth pixel-based scrolling
3. WHEN a new product is added, THE Products_Table SHALL automatically scroll to show the newly added item
4. THE Products_Table SHALL maintain a minimum visible height of 300 pixels

### Requirement 3: Compact Invoice Header Section

**User Story:** As a user, I want the invoice header information (customer, warehouse, date) to be compact, so that more space is available for the products table.

#### Acceptance Criteria

1. THE Invoice_Header_Card SHALL use a compact single-row or two-row layout for all header fields
2. THE Invoice_Header_Card SHALL have reduced vertical padding and margins
3. THE Invoice_Header_Card SHALL not exceed 120 pixels in height

### Requirement 4: Compact Product Entry Section

**User Story:** As a user, I want the product entry controls (barcode input, product selector) to be compact, so that more space is available for viewing added products.

#### Acceptance Criteria

1. THE barcode input and product selection controls SHALL be arranged in a single compact row
2. THE product entry section SHALL have reduced vertical spacing
3. THE product entry section SHALL not exceed 80 pixels in height

### Requirement 5: Optimized Summary Card Layout

**User Story:** As a user, I want the summary card on the right side to be compact and well-organized, so that I can see totals and complete the invoice efficiently.

#### Acceptance Criteria

1. THE Summary_Card SHALL use compact spacing between elements
2. THE Summary_Card SHALL display all totals, notes, and payment fields without excessive whitespace
3. THE Summary_Card SHALL have a fixed width that does not exceed 350 pixels
4. WHEN the dialog is resized, THE Summary_Card SHALL maintain its fixed width while the Products_Table expands

### Requirement 6: Improved Visual Hierarchy

**User Story:** As a user, I want the products table to be visually prominent, so that I can focus on adding and reviewing products.

#### Acceptance Criteria

1. THE Products_Table SHALL have a distinct visual border or shadow to emphasize its importance
2. THE Products_Table header row SHALL be visually distinct with a contrasting background color
3. THE Products_Table rows SHALL have alternating colors for better readability
