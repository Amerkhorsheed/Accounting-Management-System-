# Requirements Document

## Introduction

This document defines the requirements for a comprehensive Units Management system for a tobacco accounting application. The system must support multiple units of measure for products (e.g., كروز/carton, علبة/pack, حبة/piece for cigarettes; كف/bulk portion, باكيت/packet for shisha tobacco) with conversion factors between units. Users must be able to specify which unit is being used during sales and purchases, with automatic quantity and price calculations based on unit conversions.

## Glossary

- **Unit**: A unit of measure used to quantify products (e.g., piece, pack, carton, kilogram)
- **Base_Unit**: The fundamental unit for a product from which all other units are derived
- **Conversion_Factor**: The multiplier to convert from one unit to another (e.g., 1 carton = 10 packs means conversion factor is 10)
- **Product_Unit**: A relationship between a Product and a Unit, including the conversion factor and unit-specific pricing
- **Unit_Management_System**: The system component responsible for creating, editing, and managing units and their conversions
- **Sales_Module**: The system component handling customer invoices and sales transactions
- **Purchases_Module**: The system component handling supplier orders and purchase transactions
- **Inventory_Module**: The system component managing product stock levels

## Requirements

### Requirement 1: Unit CRUD Operations

**User Story:** As a system administrator, I want to create, view, edit, and delete units of measure, so that I can define all the measurement units needed for my tobacco products.

#### Acceptance Criteria

1. THE Unit_Management_System SHALL allow creating a new unit with name (Arabic), symbol, and optional English name
2. THE Unit_Management_System SHALL display a list of all units with their names, symbols, and status
3. WHEN a user edits a unit, THE Unit_Management_System SHALL update the unit information and reflect changes across all related products
4. WHEN a user attempts to delete a unit that is in use by products, THE Unit_Management_System SHALL prevent deletion and display an error message
5. WHEN a user deletes an unused unit, THE Unit_Management_System SHALL remove the unit from the system
6. THE Unit_Management_System SHALL validate that unit names and symbols are unique

### Requirement 2: Product-Unit Association with Conversion Factors

**User Story:** As a product manager, I want to associate multiple units with a product and define conversion factors, so that I can sell cigarettes by piece, pack, or carton with correct quantity calculations.

#### Acceptance Criteria

1. THE Inventory_Module SHALL allow assigning multiple units to a single product
2. WHEN assigning a unit to a product, THE Inventory_Module SHALL require a conversion factor relative to the base unit
3. THE Inventory_Module SHALL designate one unit as the base unit for each product (conversion factor = 1)
4. WHEN a product has multiple units, THE Inventory_Module SHALL store unit-specific sale price, cost price, and barcode for each unit
5. THE Inventory_Module SHALL calculate derived quantities using conversion factors (e.g., 2 cartons = 20 packs if conversion factor is 10)
6. IF a conversion factor is set to zero or negative, THEN THE Inventory_Module SHALL reject the input and display a validation error

### Requirement 3: Unit Selection in Sales

**User Story:** As a salesperson, I want to select which unit I'm selling when creating an invoice, so that I can sell a كروز (carton) or individual علبة (pack) with correct pricing.

#### Acceptance Criteria

1. WHEN adding a product to an invoice, THE Sales_Module SHALL display all available units for that product
2. WHEN a unit is selected, THE Sales_Module SHALL automatically populate the unit price based on the product-unit configuration
3. THE Sales_Module SHALL calculate the line total based on quantity and selected unit price
4. WHEN the invoice is confirmed, THE Sales_Module SHALL deduct stock in base unit quantities using the conversion factor
5. THE Sales_Module SHALL display the selected unit name/symbol on the invoice and receipt
6. IF no unit is selected, THEN THE Sales_Module SHALL default to the product's base unit

### Requirement 4: Unit Selection in Purchases

**User Story:** As a purchasing manager, I want to specify which unit I'm purchasing when creating a purchase order, so that I can order cartons from suppliers and track costs per unit correctly.

#### Acceptance Criteria

1. WHEN adding a product to a purchase order, THE Purchases_Module SHALL display all available units for that product
2. WHEN a unit is selected, THE Purchases_Module SHALL allow entering the unit cost for that specific unit
3. THE Purchases_Module SHALL calculate the line total based on quantity and unit cost
4. WHEN goods are received, THE Purchases_Module SHALL add stock in base unit quantities using the conversion factor
5. THE Purchases_Module SHALL display the selected unit name/symbol on the purchase order
6. IF no unit is selected, THEN THE Purchases_Module SHALL default to the product's base unit

### Requirement 5: Stock Display and Conversion

**User Story:** As an inventory manager, I want to view stock quantities in different units, so that I can understand inventory levels in terms of cartons, packs, or pieces.

#### Acceptance Criteria

1. THE Inventory_Module SHALL store stock quantities in base unit
2. WHEN displaying stock, THE Inventory_Module SHALL show the quantity in base unit
3. THE Inventory_Module SHALL provide a conversion display showing equivalent quantities in other configured units
4. WHEN stock falls below minimum level, THE Inventory_Module SHALL calculate the threshold using base unit quantities

### Requirement 6: Unit Management Interface

**User Story:** As a system administrator, I want a dedicated interface to manage units, so that I can easily add common tobacco units like كروز, علبة, كف, باكيت.

#### Acceptance Criteria

1. THE Unit_Management_System SHALL provide a settings page for unit management
2. THE Unit_Management_System SHALL display units in a table with columns for name, symbol, English name, and status
3. THE Unit_Management_System SHALL provide add, edit, and delete buttons for unit management
4. WHEN adding a unit, THE Unit_Management_System SHALL show a dialog form with required fields
5. THE Unit_Management_System SHALL support Arabic text input for unit names

### Requirement 7: Data Migration and Defaults

**User Story:** As a system administrator, I want default units pre-configured for tobacco products, so that I can start using the system quickly without manual setup.

#### Acceptance Criteria

1. THE Unit_Management_System SHALL provide default units: قطعة (piece), علبة (pack), كروز (carton), كيلو (kilogram), كف (bulk portion), باكيت (packet)
2. WHEN the system is initialized, THE Unit_Management_System SHALL create these default units if they don't exist
3. THE Unit_Management_System SHALL allow editing or deactivating default units
4. WHEN migrating existing products, THE Inventory_Module SHALL preserve current unit associations

