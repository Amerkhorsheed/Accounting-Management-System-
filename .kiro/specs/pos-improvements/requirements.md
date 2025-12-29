# Requirements Document

## Introduction

This document specifies the requirements for improving the Point of Sale (نقطة البيع) functionality in the inventory management system. The improvements focus on enabling full cash payment (الدفع نقداً), disabling tax for all POS transactions, and ensuring the print functionality works correctly for receipts.

## Glossary

- **POS_System**: The Point of Sale interface used for quick retail transactions
- **Receipt_Printer**: The thermal printer component responsible for printing transaction receipts
- **Cash_Payment**: A payment method where the full invoice amount is paid immediately in cash
- **Tax_Rate**: The percentage applied to calculate tax on transactions (to be disabled for POS)
- **Invoice**: A document recording a sales transaction with items, quantities, and amounts

## Requirements

### Requirement 1: Full Cash Payment (الدفع نقداً)

**User Story:** As a cashier, I want to process full cash payments in POS, so that I can complete sales transactions quickly and accurately.

#### Acceptance Criteria

1. WHEN a user clicks the "نقداً" (cash) button in POS, THE POS_System SHALL create an invoice with payment_method set to 'cash' and paid_amount equal to the total amount
2. WHEN a cash payment is processed, THE POS_System SHALL mark the invoice as fully paid immediately
3. WHEN a cash payment is successful, THE POS_System SHALL display a success message with the invoice number
4. WHEN a cash payment is successful, THE POS_System SHALL clear the cart and reset the POS view for the next transaction

### Requirement 2: Tax-Free POS Transactions

**User Story:** As a store owner, I want all POS transactions to be tax-free, so that I can offer simplified pricing to walk-in customers.

#### Acceptance Criteria

1. THE POS_System SHALL set tax_rate to 0 for all items in POS transactions regardless of global tax settings
2. THE POS_System SHALL display tax amount as 0.00 in the totals section
3. WHEN creating an invoice from POS, THE POS_System SHALL send tax_rate=0 for each item to the backend API
4. THE Receipt_Printer SHALL not display tax line or display it as 0.00 for POS receipts

### Requirement 3: Receipt Printing Functionality

**User Story:** As a cashier, I want to print receipts after completing a sale, so that I can provide customers with proof of purchase.

#### Acceptance Criteria

1. WHEN a user clicks the "طباعة" (print) button after a successful sale, THE POS_System SHALL print a receipt with the last completed invoice details
2. WHEN printing a receipt, THE Receipt_Printer SHALL include company information (name, address, phone, tax number if configured)
3. WHEN printing a receipt, THE Receipt_Printer SHALL include invoice number, date, and time
4. WHEN printing a receipt, THE Receipt_Printer SHALL include all items with product name, quantity, unit price, and line total
5. WHEN printing a receipt, THE Receipt_Printer SHALL include subtotal, discount (if any), and total amount
6. WHEN printing a receipt, THE Receipt_Printer SHALL include payment method (نقداً/بطاقة/آجل)
7. IF the thermal printer is not available, THEN THE Receipt_Printer SHALL fall back to opening the receipt as a text file
8. WHEN a cash sale is completed, THE POS_System SHALL automatically trigger receipt printing (optional auto-print)

### Requirement 4: Print Button Integration

**User Story:** As a cashier, I want the print button to work correctly in POS, so that I can print receipts on demand.

#### Acceptance Criteria

1. THE POS_System SHALL store the last completed invoice data for printing
2. WHEN the print button is clicked and no invoice has been completed, THE POS_System SHALL display a warning message "لا توجد فاتورة للطباعة"
3. WHEN the print button is clicked after a successful sale, THE POS_System SHALL call the Receipt_Printer with the stored invoice data
4. IF printing fails, THEN THE POS_System SHALL display an error message with the failure reason

### Requirement 5: Cash Drawer Integration (Optional)

**User Story:** As a cashier, I want the cash drawer to open automatically after a cash sale, so that I can quickly handle cash transactions.

#### Acceptance Criteria

1. WHEN a cash payment is completed successfully, THE POS_System SHALL send the open command to the cash drawer
2. IF the cash drawer command fails, THEN THE POS_System SHALL continue without error (silent failure)
