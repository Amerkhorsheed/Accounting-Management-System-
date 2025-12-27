# Implementation Plan: Units Management

## Overview

This implementation plan covers the development of a comprehensive Units Management system for the tobacco accounting application. The implementation follows an incremental approach, starting with backend models and APIs, then frontend components, and finally integration with sales and purchases modules.

## Tasks

- [x] 1. Enhance Unit Model and Create ProductUnit Model
  - [x] 1.1 Update Unit model with name_en field and remove is_base field
    - Add `name_en` CharField to Unit model
    - Remove `is_base` field (moved to ProductUnit)
    - Add unique constraints for name and symbol
    - _Requirements: 1.1, 1.6_

  - [x] 1.2 Create ProductUnit model
    - Create ProductUnit model with product, unit, conversion_factor, is_base_unit, sale_price, cost_price, barcode fields
    - Add CheckConstraint for positive conversion_factor
    - Add unique_together constraint for product and unit
    - Implement convert_to_base and convert_from_base methods
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

  - [x] 1.3 Create database migrations
    - Generate migration for Unit model changes
    - Generate migration for new ProductUnit model
    - _Requirements: 7.4_

  - [ ]* 1.4 Write property test for conversion factor calculations
    - **Property 7: Quantity Conversion Correctness**
    - **Validates: Requirements 2.5**

- [x] 2. Create Unit API and Serializers
  - [x] 2.1 Create Unit serializers
    - Create UnitSerializer with all fields
    - Create UnitCreateSerializer with validation for unique name/symbol
    - _Requirements: 1.1, 1.2, 1.6_

  - [x] 2.2 Create Unit ViewSet
    - Implement list, create, retrieve, update, destroy actions
    - Add validation to prevent deletion of units in use
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

  - [x] 2.3 Add Unit URLs to inventory app
    - Register UnitViewSet in inventory URLs
    - _Requirements: 1.1_

  - [x] 2.4 Write property tests for Unit CRUD
    - **Property 1: Unit CRUD Round-Trip**
    - **Property 2: Unit Name and Symbol Uniqueness**
    - **Property 3: Unit Deletion Protection**
    - **Property 4: Unused Unit Deletion**
    - **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 1.6**

- [x] 3. Create ProductUnit API and Serializers
  - [x] 3.1 Create ProductUnit serializers
    - Create ProductUnitSerializer with all fields and unit details
    - Create ProductUnitCreateSerializer with validation
    - _Requirements: 2.1, 2.2, 2.4_

  - [x] 3.2 Create ProductUnit ViewSet
    - Implement nested routes under products
    - Add validation for base unit requirement
    - Ensure exactly one base unit per product
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.6_

  - [x] 3.3 Update Product serializers to include product_units
    - Add product_units to ProductDetailSerializer
    - Include unit options in product list for sales/purchases
    - _Requirements: 3.1, 4.1_

  - [ ]* 3.4 Write property test for base unit invariant
    - **Property 5: Product Base Unit Invariant**
    - **Property 6: Conversion Factor Positivity**
    - **Validates: Requirements 2.3, 2.6**

- [ ] 4. Checkpoint - Backend Models and APIs
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Extend Sales Module for Unit Selection
  - [x] 5.1 Add product_unit and base_quantity fields to InvoiceItem model
    - Add ForeignKey to ProductUnit (nullable for backward compatibility)
    - Add base_quantity DecimalField
    - Create migration
    - _Requirements: 3.4_

  - [x] 5.2 Update InvoiceItem serializers
    - Add product_unit field to InvoiceItemSerializer
    - Add unit_name, unit_symbol to read serializer
    - Update InvoiceItemCreateSerializer to accept product_unit
    - _Requirements: 3.2, 3.5_

  - [x] 5.3 Update SalesService to calculate base_quantity
    - Calculate base_quantity = quantity * conversion_factor on invoice confirmation
    - Use base_quantity for stock deduction
    - Default to base unit if no product_unit specified
    - _Requirements: 3.4, 3.6_

  - [ ]* 5.4 Write property tests for sales stock deduction
    - **Property 8: Sales Stock Deduction Correctness**
    - **Property 10: Line Total Calculation**
    - **Property 11: Default Unit Fallback**
    - **Validates: Requirements 3.3, 3.4, 3.6**

- [x] 6. Extend Purchases Module for Unit Selection
  - [x] 6.1 Add product_unit and base_quantity fields to PurchaseOrderItem model
    - Add ForeignKey to ProductUnit (nullable for backward compatibility)
    - Add base_quantity DecimalField
    - Create migration
    - _Requirements: 4.4_

  - [x] 6.2 Update PurchaseOrderItem serializers
    - Add product_unit field to PurchaseOrderItemSerializer
    - Add unit_name, unit_symbol to read serializer
    - Update PurchaseOrderItemCreateSerializer to accept product_unit
    - _Requirements: 4.2, 4.5_

  - [x] 6.3 Update PurchaseService to calculate base_quantity
    - Calculate base_quantity = quantity * conversion_factor on goods receipt
    - Use base_quantity for stock addition
    - Default to base unit if no product_unit specified
    - _Requirements: 4.4, 4.6_

  - [ ]* 6.4 Write property tests for purchase stock addition
    - **Property 9: Purchase Stock Addition Correctness**
    - **Validates: Requirements 4.4**

- [ ] 7. Checkpoint - Backend Integration Complete
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Create Default Units Data Migration
  - [x] 8.1 Create data migration for default units
    - Create default units: قطعة (piece), علبة (pack), كروز (carton), كيلو (kilogram), كف (bulk portion), باكيت (packet)
    - Set appropriate symbols for each unit
    - _Requirements: 7.1, 7.2_

  - [x] 8.2 Create migration to convert existing product units
    - For each existing product, create a ProductUnit with the current unit as base
    - Preserve existing unit associations
    - _Requirements: 7.4_

- [x] 9. Create Frontend Units Management View
  - [x] 9.1 Create UnitsManagementView in settings
    - Create `frontend/src/views/settings/units.py`
    - Implement table with columns: name, symbol, name_en, is_active
    - Add search/filter functionality
    - _Requirements: 6.1, 6.2_

  - [x] 9.2 Create Unit dialog form
    - Create add/edit dialog with fields: name, name_en, symbol
    - Add validation for required fields
    - Support Arabic text input
    - _Requirements: 6.3, 6.4, 6.5_

  - [x] 9.3 Implement Unit CRUD operations in frontend
    - Connect to Unit API endpoints
    - Handle create, update, delete operations
    - Show confirmation dialog before delete
    - Display error messages from API
    - _Requirements: 1.1, 1.3, 1.4, 1.5_

  - [x] 9.4 Add Units to Settings navigation
    - Add "وحدات القياس" menu item in settings sidebar
    - Wire up navigation to UnitsManagementView
    - _Requirements: 6.1_

- [x] 10. Create ProductUnit Configuration Widget
  - [x] 10.1 Create ProductUnitConfigWidget
    - Create `frontend/src/widgets/product_units.py`
    - Implement table showing assigned units with conversion factors and prices
    - Add base unit indicator
    - _Requirements: 2.1, 2.3, 2.4_

  - [x] 10.2 Implement add/edit unit assignment
    - Create dialog for adding unit to product
    - Include fields: unit selector, conversion_factor, sale_price, cost_price, barcode
    - Validate conversion_factor > 0
    - _Requirements: 2.2, 2.4, 2.6_

  - [x] 10.3 Integrate ProductUnitConfigWidget into Product form
    - Add widget to product create/edit dialog
    - Load existing product units on edit
    - Save product units with product
    - _Requirements: 2.1_

- [x] 11. Create Unit Selector for Sales and Purchases
  - [x] 11.1 Create UnitSelectorComboBox widget
    - Create `frontend/src/widgets/unit_selector.py`
    - Display available units for selected product
    - Show unit name and price in dropdown
    - Emit signal when unit changes
    - _Requirements: 3.1, 4.1_

  - [x] 11.2 Integrate unit selector into Invoice form
    - Add unit selector column to invoice items table
    - Auto-populate price when unit is selected
    - Update line total calculation
    - _Requirements: 3.1, 3.2, 3.3_

  - [x] 11.3 Integrate unit selector into Purchase Order form
    - Add unit selector column to PO items table
    - Allow entering unit-specific cost
    - Update line total calculation
    - _Requirements: 4.1, 4.2, 4.3_

- [x] 12. Update Stock Display with Unit Conversions
  - [x] 12.1 Update stock display to show conversions
    - Show stock in base unit
    - Add tooltip or expandable section showing equivalent quantities in other units
    - _Requirements: 5.1, 5.2, 5.3_

  - [x] 12.2 Update low stock alerts to use base unit
    - Ensure minimum_stock comparison uses base unit quantities
    - _Requirements: 5.4_

  - [ ]* 12.3 Write property test for stock display conversion
    - **Property 13: Stock Display Conversion**
    - **Validates: Requirements 5.3**

- [ ] 13. Final Checkpoint - Full Integration
  - Ensure all tests pass, ask the user if questions arise.
  - Verify end-to-end flow: create unit → assign to product → use in sale → verify stock deduction

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- Backend implementation should be completed before frontend to ensure API stability
