# Requirements Document

## Introduction

تحسين واجهة نموذج أمر الشراء (PurchaseOrderFormDialog) لتعظيم مساحة جدول المنتجات وتمكين التمرير السلس، مع تحسين التخطيط العام للنموذج ليكون أكثر كفاءة واحترافية.

## Glossary

- **PurchaseOrderFormDialog**: نافذة الحوار المستخدمة لإنشاء أوامر الشراء الجديدة
- **Items_Table**: جدول المنتجات الذي يعرض المنتجات المضافة لأمر الشراء
- **Header_Card**: بطاقة معلومات أمر الشراء (المورد، المستودع، التواريخ)
- **Entry_Section**: قسم إدخال المنتجات (اختيار المنتج، الكمية، السعر)
- **Summary_Card**: بطاقة ملخص أمر الشراء (الإجماليات والملاحظات)

## Requirements

### Requirement 1: Products Table Expansion

**User Story:** As a user, I want the products table to take maximum available space, so that I can see more products without excessive scrolling.

#### Acceptance Criteria

1. THE Items_Table SHALL expand to fill all available vertical space in the dialog
2. THE Items_Table SHALL have a minimum height of 300 pixels
3. WHEN the dialog is resized, THE Items_Table SHALL grow or shrink proportionally

### Requirement 2: Smooth Scrolling

**User Story:** As a user, I want smooth scrolling in the products table, so that I can navigate through many products easily.

#### Acceptance Criteria

1. THE Items_Table SHALL display a vertical scrollbar when content exceeds visible area
2. WHEN scrolling, THE Items_Table SHALL scroll smoothly without lag
3. WHEN a new product is added, THE Items_Table SHALL auto-scroll to show the newly added item
4. THE Items_Table SHALL maintain scroll position when items are modified

### Requirement 3: Compact Header Layout

**User Story:** As a user, I want a compact header section, so that more space is available for the products table.

#### Acceptance Criteria

1. THE Header_Card SHALL have reduced padding of 12 pixels instead of 20 pixels
2. THE Header_Card SHALL arrange all fields (supplier, warehouse, order date, expected date) efficiently
3. THE Header_Card SHALL have a maximum height constraint of 100 pixels

### Requirement 4: Compact Product Entry Section

**User Story:** As a user, I want a compact product entry section, so that more space is available for viewing products.

#### Acceptance Criteria

1. THE Entry_Section SHALL combine product selection, quantity, and price in a single compact row
2. THE Entry_Section SHALL have reduced spacing of 8 pixels between elements
3. THE Entry_Section SHALL have a maximum height constraint of 70 pixels

### Requirement 5: Optimized Summary Card

**User Story:** As a user, I want an optimized summary card, so that I can see totals clearly without wasting space.

#### Acceptance Criteria

1. THE Summary_Card SHALL have a fixed width of 320 pixels
2. THE Summary_Card SHALL have reduced internal spacing and padding
3. THE Summary_Card SHALL display totals prominently
4. THE Summary_Card SHALL position action buttons (save, cancel) at the bottom

### Requirement 6: Enhanced Visual Styling

**User Story:** As a user, I want clear visual distinction for the products table, so that it stands out as the main focus area.

#### Acceptance Criteria

1. THE Items_Table SHALL have a distinct border or shadow to emphasize it
2. THE Items_Table header row SHALL have a contrasting background color
3. THE Items_Table SHALL display alternating row colors for better readability
