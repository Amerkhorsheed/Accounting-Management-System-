"""
Credit Service - Business Logic for Credit Sales and Payments
"""
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from enum import Enum
from typing import List, Dict, Any, Optional

from django.db import transaction
from django.db.models import Sum, F

from apps.core.decorators import handle_service_error
from apps.core.exceptions import ValidationException, InvalidOperationException


class CreditValidationStatus(Enum):
    """Status codes for credit validation results."""
    OK = 'ok'
    WARNING = 'warning'
    ERROR = 'error'


@dataclass
class CreditValidationResult:
    """
    Result of credit limit validation.
    
    Attributes:
        status: OK, WARNING, or ERROR
        can_proceed: Whether the transaction can proceed
        requires_override: Whether manager override is required
        message: Human-readable message (Arabic)
        current_balance: Customer's current balance
        credit_limit: Customer's credit limit
        requested_amount: Amount being requested
        new_balance: Balance after transaction if approved
        available_credit: Remaining credit available
    """
    status: CreditValidationStatus
    can_proceed: bool
    requires_override: bool
    message: str
    current_balance: Decimal
    credit_limit: Decimal
    requested_amount: Decimal
    new_balance: Decimal
    available_credit: Decimal


class CreditLimitExceededException(ValidationException):
    """Raised when credit limit would be exceeded."""
    
    def __init__(self, customer_name: str, current_balance: Decimal, 
                 credit_limit: Decimal, requested_amount: Decimal):
        self.customer_name = customer_name
        self.current_balance = current_balance
        self.credit_limit = credit_limit
        self.requested_amount = requested_amount
        message = (
            f'تجاوز حد الائتمان للعميل {customer_name}. '
            f'الرصيد الحالي: {current_balance}, '
            f'حد الائتمان: {credit_limit}, '
            f'المبلغ المطلوب: {requested_amount}'
        )
        super().__init__(message, field='credit_limit')


class AllocationExceedsRemainingException(ValidationException):
    """Raised when allocation exceeds invoice remaining amount."""
    
    def __init__(self, invoice_number: str, remaining: Decimal, requested: Decimal):
        self.invoice_number = invoice_number
        self.remaining = remaining
        self.requested = requested
        message = (
            f'مبلغ التخصيص ({requested}) يتجاوز المتبقي ({remaining}) '
            f'للفاتورة {invoice_number}'
        )
        super().__init__(message, field='allocation_amount')


class CreditService:
    """Service for credit-related business logic."""
    
    WARNING_THRESHOLD = Decimal('0.8')  # 80% of credit limit
    
    @staticmethod
    def validate_credit_limit(customer_id: int, amount: Decimal) -> CreditValidationResult:
        """
        Validate if customer can take additional credit.
        
        Returns validation result with warning/error status based on:
        - OK: New balance is below 80% of credit limit
        - WARNING: New balance is between 80% and 100% of credit limit
        - ERROR: New balance would exceed credit limit
        
        Requirements: 1.4, 6.3, 6.4
        """
        from .models import Customer
        
        customer = Customer.objects.get(id=customer_id)
        
        current_balance = customer.current_balance
        credit_limit = customer.credit_limit
        new_balance = current_balance + amount
        available_credit = credit_limit - current_balance
        
        # If no credit limit set (0 or negative), allow unlimited credit
        if credit_limit <= 0:
            return CreditValidationResult(
                status=CreditValidationStatus.OK,
                can_proceed=True,
                requires_override=False,
                message='لا يوجد حد ائتمان محدد للعميل',
                current_balance=current_balance,
                credit_limit=credit_limit,
                requested_amount=amount,
                new_balance=new_balance,
                available_credit=Decimal('999999999.99')  # Effectively unlimited
            )
        
        warning_threshold_amount = credit_limit * CreditService.WARNING_THRESHOLD
        
        # Check if new balance would exceed credit limit
        if new_balance > credit_limit:
            return CreditValidationResult(
                status=CreditValidationStatus.ERROR,
                can_proceed=False,
                requires_override=True,
                message=(
                    f'تجاوز حد الائتمان! '
                    f'الرصيد الحالي: {current_balance}, '
                    f'حد الائتمان: {credit_limit}, '
                    f'المبلغ المطلوب: {amount}, '
                    f'الرصيد الجديد: {new_balance}'
                ),
                current_balance=current_balance,
                credit_limit=credit_limit,
                requested_amount=amount,
                new_balance=new_balance,
                available_credit=available_credit
            )
        
        # Check if new balance would reach warning threshold (80%)
        if new_balance >= warning_threshold_amount:
            return CreditValidationResult(
                status=CreditValidationStatus.WARNING,
                can_proceed=True,
                requires_override=False,
                message=(
                    f'تحذير: الرصيد يقترب من حد الائتمان! '
                    f'الرصيد الجديد: {new_balance} من أصل {credit_limit}'
                ),
                current_balance=current_balance,
                credit_limit=credit_limit,
                requested_amount=amount,
                new_balance=new_balance,
                available_credit=available_credit
            )
        
        # All good - below warning threshold
        return CreditValidationResult(
            status=CreditValidationStatus.OK,
            can_proceed=True,
            requires_override=False,
            message='الرصيد ضمن الحد المسموح',
            current_balance=current_balance,
            credit_limit=credit_limit,
            requested_amount=amount,
            new_balance=new_balance,
            available_credit=available_credit
        )


    @staticmethod
    def calculate_due_date(customer_id: int, invoice_date: date) -> date:
        """
        Calculate due date based on customer payment terms.
        
        The due date is calculated as: invoice_date + payment_terms (days)
        
        Requirements: 1.2
        
        Args:
            customer_id: The customer's ID
            invoice_date: The date of the invoice
            
        Returns:
            The calculated due date
        """
        from .models import Customer
        
        customer = Customer.objects.get(id=customer_id)
        payment_terms_days = customer.payment_terms or 0
        
        return invoice_date + timedelta(days=payment_terms_days)

    @staticmethod
    @handle_service_error
    @transaction.atomic
    def allocate_payment(
        payment_id: int,
        allocations: Optional[List[Dict[str, Any]]] = None,
        auto_allocate: bool = False
    ) -> List['PaymentAllocation']:
        """
        Allocate payment to invoices.
        
        Supports two modes:
        1. Manual allocation: Provide specific allocations list
        2. Auto allocation (FIFO): Set auto_allocate=True to apply payment to oldest invoices first
        
        Requirements: 7.1, 7.2, 7.4, 7.5
        
        Args:
            payment_id: The payment to allocate
            allocations: List of dicts with 'invoice_id' and 'amount' keys
            auto_allocate: If True, uses FIFO strategy (oldest invoices first)
            
        Returns:
            List of created PaymentAllocation records
            
        Raises:
            AllocationExceedsRemainingException: If allocation exceeds invoice remaining
            ValidationException: If total allocations exceed payment amount
        """
        from .models import Payment, Invoice, PaymentAllocation
        
        payment = Payment.objects.select_for_update().get(id=payment_id)
        customer = payment.customer
        
        # Calculate already allocated amount for this payment
        existing_allocations = PaymentAllocation.objects.filter(
            payment=payment
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        remaining_payment = payment.amount - existing_allocations
        
        if remaining_payment <= 0:
            raise ValidationException(
                'لا يوجد مبلغ متبقي للتخصيص من هذه الدفعة',
                field='amount'
            )
        
        created_allocations = []
        
        if auto_allocate:
            # FIFO: Get unpaid/partial invoices ordered by date (oldest first)
            unpaid_invoices = Invoice.objects.filter(
                customer=customer,
                invoice_type=Invoice.InvoiceType.CREDIT,
                status__in=[Invoice.Status.CONFIRMED, Invoice.Status.PARTIAL]
            ).order_by('invoice_date', 'id').select_for_update()
            
            amount_to_allocate = remaining_payment
            
            for invoice in unpaid_invoices:
                if amount_to_allocate <= 0:
                    break
                
                invoice_remaining = invoice.remaining_amount
                if invoice_remaining <= 0:
                    continue
                
                # Allocate the minimum of remaining payment and invoice remaining
                allocation_amount = min(amount_to_allocate, invoice_remaining)
                
                # Check if allocation already exists for this payment-invoice pair
                existing = PaymentAllocation.objects.filter(
                    payment=payment,
                    invoice=invoice
                ).first()
                
                if existing:
                    # Update existing allocation
                    existing.amount += allocation_amount
                    existing.save()
                    created_allocations.append(existing)
                else:
                    # Create new allocation
                    allocation = PaymentAllocation.objects.create(
                        payment=payment,
                        invoice=invoice,
                        amount=allocation_amount
                    )
                    created_allocations.append(allocation)
                
                # Update invoice paid amount and status
                invoice.paid_amount += allocation_amount
                if invoice.paid_amount >= invoice.total_amount:
                    invoice.status = Invoice.Status.PAID
                else:
                    invoice.status = Invoice.Status.PARTIAL
                invoice.save()
                
                amount_to_allocate -= allocation_amount
        
        else:
            # Manual allocation
            if not allocations:
                raise ValidationException(
                    'يجب تحديد الفواتير للتخصيص أو استخدام التخصيص التلقائي',
                    field='allocations'
                )
            
            total_allocation = sum(Decimal(str(a['amount'])) for a in allocations)
            
            if total_allocation > remaining_payment:
                raise ValidationException(
                    f'إجمالي التخصيصات ({total_allocation}) يتجاوز المبلغ المتبقي ({remaining_payment})',
                    field='amount'
                )
            
            for alloc in allocations:
                invoice_id = alloc['invoice_id']
                amount = Decimal(str(alloc['amount']))
                
                if amount <= 0:
                    continue
                
                invoice = Invoice.objects.select_for_update().get(id=invoice_id)
                
                # Validate invoice belongs to same customer
                if invoice.customer_id != customer.id:
                    raise ValidationException(
                        f'الفاتورة {invoice.invoice_number} لا تخص هذا العميل',
                        field='invoice_id'
                    )
                
                # Validate invoice is a credit invoice
                if invoice.invoice_type != Invoice.InvoiceType.CREDIT:
                    raise ValidationException(
                        f'الفاتورة {invoice.invoice_number} ليست فاتورة آجلة',
                        field='invoice_id'
                    )
                
                # Validate allocation doesn't exceed remaining
                invoice_remaining = invoice.remaining_amount
                if amount > invoice_remaining:
                    raise AllocationExceedsRemainingException(
                        invoice.invoice_number,
                        invoice_remaining,
                        amount
                    )
                
                # Check if allocation already exists
                existing = PaymentAllocation.objects.filter(
                    payment=payment,
                    invoice=invoice
                ).first()
                
                if existing:
                    # Validate combined allocation doesn't exceed remaining
                    new_total = existing.amount + amount
                    if new_total > invoice_remaining + existing.amount:
                        raise AllocationExceedsRemainingException(
                            invoice.invoice_number,
                            invoice_remaining + existing.amount,
                            new_total
                        )
                    existing.amount = new_total
                    existing.save()
                    created_allocations.append(existing)
                else:
                    allocation = PaymentAllocation.objects.create(
                        payment=payment,
                        invoice=invoice,
                        amount=amount
                    )
                    created_allocations.append(allocation)
                
                # Update invoice paid amount and status
                invoice.paid_amount += amount
                if invoice.paid_amount >= invoice.total_amount:
                    invoice.status = Invoice.Status.PAID
                else:
                    invoice.status = Invoice.Status.PARTIAL
                invoice.save()
        
        return created_allocations

    @staticmethod
    def get_customer_unpaid_invoices(customer_id: int) -> List[Dict[str, Any]]:
        """
        Get list of unpaid/partial invoices for a customer.
        
        Returns invoices ordered by date (oldest first) for FIFO display.
        
        Args:
            customer_id: The customer's ID
            
        Returns:
            List of invoice dicts with id, number, date, total, paid, remaining
        """
        from .models import Invoice
        
        invoices = Invoice.objects.filter(
            customer_id=customer_id,
            invoice_type=Invoice.InvoiceType.CREDIT,
            status__in=[Invoice.Status.CONFIRMED, Invoice.Status.PARTIAL]
        ).order_by('invoice_date', 'id')
        
        return [
            {
                'id': inv.id,
                'invoice_number': inv.invoice_number,
                'invoice_date': inv.invoice_date,
                'due_date': inv.due_date,
                'total_amount': inv.total_amount,
                'paid_amount': inv.paid_amount,
                'remaining_amount': inv.remaining_amount,
                'status': inv.status,
                'is_overdue': inv.due_date and inv.due_date < date.today()
            }
            for inv in invoices
        ]
