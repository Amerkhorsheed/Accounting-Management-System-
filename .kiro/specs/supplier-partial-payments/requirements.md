# Requirements Document

## Introduction

This feature adds comprehensive partial payment functionality for supplier purchases, mirroring the existing credit sales payment system. When creating a purchase order, users can make full or partial payments to suppliers. The system will track payment status, supplier balances, and provide detailed reports for accounts payable management.

## Glossary

- **Supplier**: A vendor from whom goods are purchased
- **Purchase_Order**: An order placed with a supplier for goods
- **Supplier_Payment**: A payment made to a supplier (سند صرف)
- **Payment_Allocation**: The assignment of a payment amount to specific purchase orders
- **Supplier_Balance**: The current amount owed to a supplier (الرصيد الحالي)
- **Accounts_Payable**: Total amounts owed to all suppliers
- **Payment_Status**: The payment state of a purchase order (draft, confirmed, paid, partial)

## Requirements

### Requirement 1: Purchase Order Payment Types

**User Story:** As a user, I want to specify payment type when creating a purchase order, so that I can track whether it's a cash or credit purchase.

#### Acceptance Criteria

1. WHEN a user creates a new purchase order, THE Purchase_Order_Form SHALL display payment type options (cash/credit)
2. WHEN cash payment type is selected, THE Purchase_Order_Form SHALL display a paid amount field with a "full payment" button
3. WHEN credit payment type is selected, THE Purchase_Order_Form SHALL allow zero or partial payment entry
4. THE Purchase_Order SHALL store the paid_amount and calculate remaining_amount automatically

### Requirement 2: Partial Payment Entry

**User Story:** As a user, I want to enter partial payments when creating a purchase order, so that I can record the actual amount paid to the supplier.

#### Acceptance Criteria

1. WHEN a user enters a paid amount less than total, THE System SHALL set the purchase order status to 'partial'
2. WHEN a user clicks the "full payment" button, THE System SHALL set paid_amount equal to total_amount
3. WHEN paid_amount equals total_amount, THE System SHALL set the purchase order status to 'paid'
4. WHEN paid_amount is zero for a credit purchase, THE System SHALL set the status to 'confirmed'
5. THE System SHALL validate that paid_amount does not exceed total_amount

### Requirement 3: Supplier Balance Management

**User Story:** As a user, I want the system to automatically update supplier balances, so that I can track how much I owe each supplier.

#### Acceptance Criteria

1. WHEN a credit purchase order is confirmed, THE System SHALL increase the supplier's current_balance by the remaining_amount
2. WHEN a payment is made to a supplier, THE System SHALL decrease the supplier's current_balance by the payment amount
3. THE Supplier model SHALL track current_balance accurately across all transactions
4. WHEN viewing a supplier, THE System SHALL display the current outstanding balance

### Requirement 4: Supplier Payment Recording

**User Story:** As a user, I want to record payments to suppliers separately from purchase orders, so that I can pay off outstanding balances.

#### Acceptance Criteria

1. WHEN a user creates a supplier payment, THE System SHALL allow selecting the supplier and entering payment details
2. WHEN a supplier payment is created, THE System SHALL generate a unique payment number (سند صرف)
3. THE Supplier_Payment SHALL support multiple payment methods (cash, bank transfer, check, credit card)
4. WHEN a payment is saved, THE System SHALL update the supplier's current_balance

### Requirement 5: Payment Allocation to Purchase Orders

**User Story:** As a user, I want to allocate payments to specific purchase orders, so that I can track which orders have been paid.

#### Acceptance Criteria

1. WHEN creating a supplier payment, THE System SHALL display unpaid/partial purchase orders for the supplier
2. THE System SHALL allow manual allocation of payment amounts to specific purchase orders
3. THE System SHALL support auto-allocation using FIFO (oldest orders first)
4. WHEN a payment is allocated to a purchase order, THE System SHALL update the order's paid_amount and status
5. IF allocation amount exceeds order remaining amount, THEN THE System SHALL reject the allocation with an error

### Requirement 6: Purchase Order Payment Status

**User Story:** As a user, I want to see the payment status of purchase orders, so that I can identify which orders need payment.

#### Acceptance Criteria

1. THE Purchase_Order_List SHALL display payment status (draft, confirmed, partial, paid, cancelled)
2. THE Purchase_Order_List SHALL display paid_amount and remaining_amount columns
3. WHEN filtering purchase orders, THE System SHALL support filtering by payment status
4. THE Purchase_Order_Details SHALL show payment history and allocations

### Requirement 7: Supplier Statement Report

**User Story:** As a user, I want to generate supplier account statements, so that I can review transaction history with each supplier.

#### Acceptance Criteria

1. THE System SHALL generate supplier statements showing opening balance, transactions, and closing balance
2. THE Statement SHALL include purchase orders (debits) and payments (credits)
3. THE Statement SHALL calculate running balance for each transaction
4. THE Statement SHALL support date range filtering
5. THE Statement SHALL be exportable to PDF/Excel

### Requirement 8: Accounts Payable Report

**User Story:** As a user, I want to view an accounts payable report, so that I can see total amounts owed to all suppliers.

#### Acceptance Criteria

1. THE Report SHALL display total outstanding amount across all suppliers
2. THE Report SHALL list suppliers with outstanding balances sorted by amount
3. THE Report SHALL show unpaid and partial purchase order counts per supplier
4. THE Report SHALL support filtering by supplier and date range

### Requirement 9: Supplier Aging Report

**User Story:** As a user, I want to see an aging report for supplier payables, so that I can prioritize payments.

#### Acceptance Criteria

1. THE Report SHALL categorize payables by age buckets (current, 1-30, 31-60, 61-90, >90 days)
2. THE Report SHALL calculate totals per aging category
3. THE Report SHALL include purchase order details per category
4. THE Report SHALL use expected_date or order_date for aging calculation

### Requirement 10: Dashboard Integration

**User Story:** As a user, I want to see accounts payable summary on the dashboard, so that I can monitor supplier obligations.

#### Acceptance Criteria

1. THE Dashboard SHALL display total accounts payable amount
2. THE Dashboard SHALL show count of suppliers with outstanding balances
3. THE Dashboard SHALL highlight overdue payables amount
