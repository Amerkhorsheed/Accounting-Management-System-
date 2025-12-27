# Requirements Document

## Introduction

This document specifies the requirements for the Credit Sales and Payments (البيع الآجل والتحصيل) feature. The feature enables businesses to sell on credit (أجل) to customers, track outstanding balances, collect partial or full payments, and generate comprehensive receivables reports. This is essential for real-world business operations where customers don't always pay immediately.

## Glossary

- **Credit_Invoice**: A sales invoice where payment is deferred (فاتورة آجلة)
- **Payment_Receipt**: A document recording customer payment against outstanding balance (سند قبض)
- **Customer_Balance**: The total amount owed by a customer (رصيد العميل)
- **Credit_Limit**: Maximum amount a customer can owe (حد الائتمان)
- **Due_Date**: The date by which payment should be made (تاريخ الاستحقاق)
- **Aging_Report**: Report showing overdue invoices by time periods (تقرير أعمار الديون)
- **Receivables**: Total amounts owed by all customers (المستحقات)
- **Partial_Payment**: Payment of less than the full invoice amount (دفعة جزئية)
- **Full_Payment**: Payment of the complete invoice amount (دفعة كاملة)
- **Account_Statement**: Detailed transaction history for a customer (كشف حساب)

## Requirements

### Requirement 1: Create Credit Invoice

**User Story:** As a salesperson, I want to create a credit invoice (فاتورة آجلة) for a customer, so that I can sell products without immediate payment.

#### Acceptance Criteria

1. WHEN a user selects "آجل" (credit) as payment type THEN THE System SHALL require customer selection before proceeding
2. WHEN creating a credit invoice THEN THE System SHALL calculate and display the due date based on customer payment terms
3. WHEN a credit invoice is confirmed THEN THE System SHALL add the invoice total to the customer's current balance
4. IF the invoice total would exceed the customer's credit limit THEN THE System SHALL display a warning but allow override with confirmation
5. WHEN a credit invoice is created THEN THE System SHALL set the invoice status to "confirmed" and payment status to "unpaid"
6. THE Invoice_Form SHALL display the customer's current balance and available credit before confirmation

### Requirement 2: Collect Customer Payments

**User Story:** As a cashier, I want to collect payments from customers against their outstanding balance, so that I can record partial or full payments.

#### Acceptance Criteria

1. WHEN collecting a payment THEN THE System SHALL allow selecting specific invoices to pay or paying against general balance
2. WHEN a partial payment is made against an invoice THEN THE System SHALL update the invoice paid amount and set status to "partial"
3. WHEN a full payment is made against an invoice THEN THE System SHALL update the invoice paid amount and set status to "paid"
4. WHEN a payment is recorded THEN THE System SHALL reduce the customer's current balance by the payment amount
5. THE Payment_Form SHALL display the customer's current balance and list of unpaid/partial invoices
6. WHEN recording a payment THEN THE System SHALL support multiple payment methods (cash, card, bank transfer, check)
7. THE Payment_Receipt SHALL be printable with payment details, customer info, and remaining balance

### Requirement 3: View Customer Account Statement

**User Story:** As an accountant, I want to view a customer's account statement, so that I can see all transactions and current balance.

#### Acceptance Criteria

1. WHEN viewing a customer statement THEN THE System SHALL display opening balance, all transactions, and closing balance
2. THE Account_Statement SHALL include invoices, payments, and returns with dates and amounts
3. THE Account_Statement SHALL calculate running balance after each transaction
4. WHEN filtering by date range THEN THE System SHALL show only transactions within that period
5. THE Account_Statement SHALL be exportable to PDF and Excel formats
6. THE Account_Statement SHALL display transaction type (invoice/payment/return) clearly

### Requirement 4: Receivables Report

**User Story:** As a business owner, I want to see a report of all outstanding receivables, so that I can track money owed to the business.

#### Acceptance Criteria

1. THE Receivables_Report SHALL display total outstanding amount across all customers
2. THE Receivables_Report SHALL list customers with outstanding balances sorted by amount
3. WHEN viewing the report THEN THE System SHALL show each customer's total balance, credit limit, and available credit
4. THE Receivables_Report SHALL allow filtering by customer type, salesperson, and date range
5. THE Receivables_Report SHALL display count of unpaid and partially paid invoices per customer

### Requirement 5: Aging Report

**User Story:** As a credit manager, I want to see an aging report of overdue invoices, so that I can follow up on late payments.

#### Acceptance Criteria

1. THE Aging_Report SHALL categorize outstanding amounts by age: current, 1-30 days, 31-60 days, 61-90 days, over 90 days
2. WHEN an invoice due date has passed THEN THE System SHALL mark it as overdue in the aging report
3. THE Aging_Report SHALL display total amounts for each aging category
4. THE Aging_Report SHALL allow drilling down to see individual invoices in each category
5. THE Aging_Report SHALL highlight severely overdue amounts (over 60 days) visually

### Requirement 6: Credit Limit Management

**User Story:** As a sales manager, I want to manage customer credit limits, so that I can control credit risk.

#### Acceptance Criteria

1. WHEN editing a customer THEN THE System SHALL allow setting credit limit and payment terms (days)
2. THE Customer_Form SHALL display current balance, credit limit, and available credit
3. WHEN a customer's balance approaches credit limit (80%) THEN THE System SHALL display a warning indicator
4. WHEN a customer exceeds credit limit THEN THE System SHALL block new credit sales unless overridden by manager
5. THE System SHALL log all credit limit overrides with user and reason

### Requirement 7: Payment Allocation

**User Story:** As an accountant, I want to allocate payments to specific invoices, so that I can track which invoices are paid.

#### Acceptance Criteria

1. WHEN recording a payment THEN THE System SHALL allow allocating to one or multiple invoices
2. WHEN payment amount exceeds selected invoice total THEN THE System SHALL allow allocating remainder to other invoices or customer credit
3. THE Payment_Allocation_Form SHALL show invoice number, date, total, paid, and remaining for each unpaid invoice
4. WHEN auto-allocating THEN THE System SHALL apply payment to oldest invoices first (FIFO)
5. THE System SHALL prevent allocating more than the remaining amount on any invoice

### Requirement 8: Dashboard Credit Summary

**User Story:** As a business owner, I want to see credit summary on the dashboard, so that I can monitor receivables at a glance.

#### Acceptance Criteria

1. THE Dashboard SHALL display total receivables amount
2. THE Dashboard SHALL display count of customers with outstanding balance
3. THE Dashboard SHALL display total overdue amount
4. WHEN clicking on receivables summary THEN THE System SHALL navigate to the receivables report
5. THE Dashboard SHALL show receivables trend compared to previous period
