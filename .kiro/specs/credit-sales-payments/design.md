# Design Document: Credit Sales and Payments (البيع الآجل والتحصيل)

## Overview

This design document describes the implementation of the Credit Sales and Payments feature for the inventory management system. The feature enables businesses to sell on credit (آجل), track customer balances, collect partial or full payments, and generate comprehensive receivables and aging reports.

The implementation extends the existing sales module with enhanced credit management capabilities while maintaining backward compatibility with cash sales.

## Architecture

The feature follows the existing Django REST Framework architecture with:
- **Backend**: Django models, serializers, views, and services
- **Frontend**: PySide6 Qt widgets with API integration
- **Database**: PostgreSQL with existing schema extensions

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (PySide6)                        │
├─────────────────────────────────────────────────────────────────┤
│  CreditInvoiceForm  │  PaymentCollectionView  │  ReportsView    │
│  CustomerStatement  │  ReceivablesReport      │  AgingReport    │
└─────────────────────────────────────────────────────────────────┘
                              │ HTTP/REST
┌─────────────────────────────────────────────────────────────────┐
│                     Backend (Django REST)                        │
├─────────────────────────────────────────────────────────────────┤
│  InvoiceViewSet     │  PaymentViewSet         │  ReportViews    │
│  CustomerViewSet    │  CreditService          │  ReportService  │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                     Database (PostgreSQL)                        │
├─────────────────────────────────────────────────────────────────┤
│  Invoice  │  Payment  │  PaymentAllocation  │  Customer         │
│  CreditLimitOverride (new)                                      │
└─────────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### Backend Components

#### 1. CreditService (New Service Class)

```python
class CreditService:
    """Service for credit-related business logic."""
    
    @staticmethod
    def validate_credit_limit(customer_id: int, amount: Decimal) -> CreditValidationResult:
        """
        Validate if customer can take additional credit.
        Returns validation result with warning/error status.
        """
        pass
    
    @staticmethod
    def calculate_due_date(customer_id: int, invoice_date: date) -> date:
        """Calculate due date based on customer payment terms."""
        pass
    
    @staticmethod
    def allocate_payment(
        payment_id: int,
        allocations: List[Dict[str, Any]],
        auto_allocate: bool = False
    ) -> List[PaymentAllocation]:
        """
        Allocate payment to invoices.
        If auto_allocate=True, uses FIFO strategy.
        """
        pass
    
    @staticmethod
    def get_receivables_report(
        filters: Dict[str, Any] = None
    ) -> ReceivablesReportData:
        """Generate receivables report with customer balances."""
        pass
    
    @staticmethod
    def get_aging_report(as_of_date: date = None) -> AgingReportData:
        """Generate aging report categorized by overdue periods."""
        pass
```

#### 2. Enhanced PaymentViewSet

```python
class PaymentViewSet(viewsets.ModelViewSet):
    """Enhanced payment management with allocation support."""
    
    @action(detail=False, methods=['get'])
    def customer_unpaid_invoices(self, request):
        """Get list of unpaid/partial invoices for a customer."""
        pass
    
    @action(detail=True, methods=['post'])
    def allocate(self, request, pk=None):
        """Allocate payment to specific invoices."""
        pass
    
    @action(detail=False, methods=['post'])
    def collect_with_allocation(self, request):
        """Create payment with invoice allocations in one transaction."""
        pass
```

#### 3. Report Views

```python
class ReceivablesReportView(views.APIView):
    """Receivables report endpoint."""
    
    def get(self, request):
        """Get receivables report with filters."""
        pass

class AgingReportView(views.APIView):
    """Aging report endpoint."""
    
    def get(self, request):
        """Get aging report as of specified date."""
        pass
```

### Frontend Components

#### 1. CreditInvoiceForm

Enhanced invoice creation form with:
- Customer selection (required for credit)
- Credit limit display and validation
- Due date auto-calculation
- Override confirmation dialog

#### 2. PaymentCollectionView

New view for collecting payments:
- Customer selection with balance display
- Unpaid invoices list with checkboxes
- Payment amount input
- Allocation preview
- Payment method selection

#### 3. CustomerStatementView

Enhanced statement view:
- Date range filter
- Transaction list with running balance
- Export buttons (PDF/Excel)
- Print functionality

#### 4. ReceivablesReportView

New report view:
- Summary cards (total, overdue, customer count)
- Customer list with balances
- Filters (customer type, salesperson)
- Drill-down to customer statement

#### 5. AgingReportView

New report view:
- Aging buckets visualization
- Customer breakdown by bucket
- Invoice drill-down
- Visual highlighting for severe overdue

## Data Models

### New Model: PaymentAllocation

```python
class PaymentAllocation(BaseModel):
    """
    Tracks allocation of payments to specific invoices.
    Enables partial payments across multiple invoices.
    """
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name='allocations'
    )
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.PROTECT,
        related_name='payment_allocations'
    )
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2
    )
    
    class Meta:
        unique_together = ['payment', 'invoice']
```

### New Model: CreditLimitOverride

```python
class CreditLimitOverride(BaseModel):
    """
    Audit log for credit limit override decisions.
    """
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='credit_overrides'
    )
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.SET_NULL,
        null=True,
        related_name='credit_overrides'
    )
    override_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2
    )
    reason = models.TextField()
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
```

### Enhanced Existing Models

#### Customer (additions)

```python
# Add computed property
@property
def credit_warning_threshold(self) -> bool:
    """Returns True if balance >= 80% of credit limit."""
    if self.credit_limit <= 0:
        return False
    return self.current_balance >= (self.credit_limit * Decimal('0.8'))

@property
def is_over_credit_limit(self) -> bool:
    """Returns True if balance >= credit limit."""
    if self.credit_limit <= 0:
        return False
    return self.current_balance >= self.credit_limit
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Credit Invoice Requires Customer

*For any* invoice with invoice_type='credit', the customer field must be non-null and valid.

**Validates: Requirements 1.1**

### Property 2: Due Date Calculation

*For any* credit invoice with a customer having payment_terms=N days, the due_date should equal invoice_date + N days.

**Validates: Requirements 1.2**

### Property 3: Credit Invoice Balance Update

*For any* credit invoice that is confirmed, the customer's current_balance should increase by exactly the invoice's total_amount.

**Validates: Requirements 1.3**

### Property 4: Credit Limit Warning

*For any* credit invoice where (customer.current_balance + invoice.total_amount) > customer.credit_limit, the system should return a warning indicator.

**Validates: Requirements 1.4**

### Property 5: Payment Status Consistency

*For any* invoice with payments, if paid_amount < total_amount then status='partial', and if paid_amount >= total_amount then status='paid'.

**Validates: Requirements 2.2, 2.3**

### Property 6: Payment Balance Update

*For any* payment of amount A recorded for a customer, the customer's current_balance should decrease by exactly A.

**Validates: Requirements 2.4**

### Property 7: Statement Structure and Running Balance

*For any* customer statement, it should contain opening_balance, a list of transactions (each with type, date, debit, credit, and balance), and closing_balance. The running balance after each transaction should equal previous_balance + debit - credit.

**Validates: Requirements 3.1, 3.2, 3.3, 3.6**

### Property 8: Statement Date Filtering

*For any* customer statement filtered by date range [start, end], all transactions in the result should have dates within that range (inclusive).

**Validates: Requirements 3.4**

### Property 9: Receivables Report Structure

*For any* receivables report, the total_outstanding should equal the sum of all customer balances where balance > 0, and customers should be sorted by balance descending.

**Validates: Requirements 4.1, 4.2, 4.3, 4.5**

### Property 10: Aging Report Categorization

*For any* aging report, each unpaid invoice should appear in exactly one age category based on days_overdue = today - due_date: current (<=0), 1-30, 31-60, 61-90, or >90 days. The total for each category should equal the sum of remaining amounts of invoices in that category.

**Validates: Requirements 5.1, 5.2, 5.3**

### Property 11: Credit Warning Threshold

*For any* customer where current_balance >= 0.8 * credit_limit and credit_limit > 0, the credit_warning_threshold property should return True.

**Validates: Requirements 6.3**

### Property 12: Credit Limit Blocking

*For any* customer where current_balance >= credit_limit and credit_limit > 0, attempting to create a new credit invoice without override should fail with a credit limit error.

**Validates: Requirements 6.4**

### Property 13: Payment Excess Handling

*For any* payment where amount > sum of selected invoice remaining amounts, the excess should be applicable to other invoices or remain as customer credit.

**Validates: Requirements 7.2**

### Property 14: FIFO Payment Allocation

*For any* auto-allocated payment, invoices should be paid in order of invoice_date ascending (oldest first).

**Validates: Requirements 7.4**

### Property 15: Allocation Amount Constraint

*For any* payment allocation, the allocated_amount for each invoice should be <= invoice.remaining_amount.

**Validates: Requirements 7.5**

## Error Handling

### Credit Limit Errors

```python
class CreditLimitExceededException(ValidationException):
    """Raised when credit limit would be exceeded."""
    
    def __init__(self, customer_name: str, current_balance: Decimal, 
                 credit_limit: Decimal, requested_amount: Decimal):
        self.customer_name = customer_name
        self.current_balance = current_balance
        self.credit_limit = credit_limit
        self.requested_amount = requested_amount
        super().__init__(
            field='credit_limit',
            message=f'تجاوز حد الائتمان للعميل {customer_name}. '
                    f'الرصيد الحالي: {current_balance}, '
                    f'حد الائتمان: {credit_limit}, '
                    f'المبلغ المطلوب: {requested_amount}'
        )
```

### Allocation Errors

```python
class AllocationExceedsRemainingException(ValidationException):
    """Raised when allocation exceeds invoice remaining amount."""
    
    def __init__(self, invoice_number: str, remaining: Decimal, requested: Decimal):
        super().__init__(
            field='allocation_amount',
            message=f'مبلغ التخصيص ({requested}) يتجاوز المتبقي ({remaining}) '
                    f'للفاتورة {invoice_number}'
        )
```

### Error Response Format

All errors follow the existing API error format:
```json
{
    "code": "CREDIT_LIMIT_EXCEEDED",
    "message": "تجاوز حد الائتمان للعميل",
    "detail": {
        "customer_name": "أحمد محمد",
        "current_balance": 5000.00,
        "credit_limit": 5000.00,
        "requested_amount": 1500.00
    }
}
```

## Testing Strategy

### Unit Tests

Unit tests will cover:
- Credit limit validation logic
- Due date calculation
- Balance update calculations
- Aging category determination
- FIFO allocation ordering

### Property-Based Tests

Property-based tests using `hypothesis` library will verify:
- All 15 correctness properties defined above
- Each test runs minimum 100 iterations
- Tests tagged with property reference

**Test Configuration:**
```python
from hypothesis import given, strategies as st, settings

@settings(max_examples=100)
@given(
    balance=st.decimals(min_value=0, max_value=100000, places=2),
    credit_limit=st.decimals(min_value=0, max_value=100000, places=2)
)
def test_credit_warning_threshold(balance, credit_limit):
    """
    Feature: credit-sales-payments, Property 11: Credit Warning Threshold
    Validates: Requirements 6.3
    """
    # Test implementation
    pass
```

### Integration Tests

Integration tests will verify:
- End-to-end credit invoice creation flow
- Payment collection with allocation
- Report generation accuracy
- Customer statement correctness

### Test Data Generators

```python
# Generators for property-based testing
def customer_generator():
    """Generate valid customer with credit settings."""
    return st.fixed_dictionaries({
        'name': st.text(min_size=1, max_size=100),
        'credit_limit': st.decimals(min_value=0, max_value=100000, places=2),
        'payment_terms': st.integers(min_value=0, max_value=90),
        'current_balance': st.decimals(min_value=0, max_value=100000, places=2)
    })

def invoice_generator(customer_balance, credit_limit):
    """Generate valid invoice respecting credit constraints."""
    max_amount = max(0, credit_limit - customer_balance)
    return st.fixed_dictionaries({
        'invoice_type': st.sampled_from(['cash', 'credit']),
        'total_amount': st.decimals(min_value=1, max_value=max_amount or 10000, places=2)
    })
```
