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
from apps.core.utils import get_daily_fx, to_usd, from_usd


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
    def validate_credit_limit(
        customer_id: int,
        amount: Decimal,
        fx_rate_date: Optional[date] = None
    ) -> CreditValidationResult:
        """
        Validate if customer can take additional credit.
        
        Returns validation result with warning/error status based on:
        - OK: New balance is below 80% of credit limit
        - WARNING: New balance is between 80% and 100% of credit limit
        - ERROR: New balance would exceed credit limit
        
        Requirements: 1.4, 6.3, 6.4
        """
        from .models import Customer
        from apps.core.utils import get_daily_fx, to_usd
        
        customer = Customer.objects.get(id=customer_id)
        
        requested_amount_usd = Decimal(str(amount or 0))

        current_balance_usd = customer.current_balance_usd

        credit_limit = customer.credit_limit
        credit_limit_usd = Decimal('0.00')
        if credit_limit and credit_limit > 0:
            fx_old, fx_new = get_daily_fx(fx_rate_date or date.today())
            credit_limit_usd = to_usd(
                credit_limit,
                'SYP_OLD',
                usd_to_syp_old=fx_old,
                usd_to_syp_new=fx_new
            )

        new_balance_usd = current_balance_usd + requested_amount_usd
        available_credit_usd = credit_limit_usd - current_balance_usd
        
        # If no credit limit set (0 or negative), allow unlimited credit
        if credit_limit_usd <= 0:
            return CreditValidationResult(
                status=CreditValidationStatus.OK,
                can_proceed=True,
                requires_override=False,
                message='لا يوجد حد ائتمان محدد للعميل',
                current_balance=current_balance_usd,
                credit_limit=credit_limit_usd,
                requested_amount=requested_amount_usd,
                new_balance=new_balance_usd,
                available_credit=Decimal('999999999.99')  # Effectively unlimited
            )
        
        warning_threshold_amount = credit_limit_usd * CreditService.WARNING_THRESHOLD
        
        # Check if new balance would exceed credit limit
        if new_balance_usd > credit_limit_usd:
            return CreditValidationResult(
                status=CreditValidationStatus.ERROR,
                can_proceed=False,
                requires_override=True,
                message=(
                    f'تجاوز حد الائتمان! '
                    f'الرصيد الحالي: {current_balance_usd}, '
                    f'حد الائتمان: {credit_limit_usd}, '
                    f'المبلغ المطلوب: {requested_amount_usd}, '
                    f'الرصيد الجديد: {new_balance_usd}'
                ),
                current_balance=current_balance_usd,
                credit_limit=credit_limit_usd,
                requested_amount=requested_amount_usd,
                new_balance=new_balance_usd,
                available_credit=available_credit_usd
            )
        
        # Check if new balance would reach warning threshold (80%)
        if new_balance_usd >= warning_threshold_amount:
            return CreditValidationResult(
                status=CreditValidationStatus.WARNING,
                can_proceed=True,
                requires_override=False,
                message=(
                    f'تحذير: الرصيد يقترب من حد الائتمان! '
                    f'الرصيد الجديد: {new_balance_usd} من أصل {credit_limit_usd}'
                ),
                current_balance=current_balance_usd,
                credit_limit=credit_limit_usd,
                requested_amount=requested_amount_usd,
                new_balance=new_balance_usd,
                available_credit=available_credit_usd
            )
        
        # All good - below warning threshold
        return CreditValidationResult(
            status=CreditValidationStatus.OK,
            can_proceed=True,
            requires_override=False,
            message='الرصيد ضمن الحد المسموح',
            current_balance=current_balance_usd,
            credit_limit=credit_limit_usd,
            requested_amount=requested_amount_usd,
            new_balance=new_balance_usd,
            available_credit=available_credit_usd
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

        if payment.amount_usd == 0 and payment.amount and payment.transaction_currency:
            if not payment.usd_to_syp_old_snapshot or not payment.usd_to_syp_new_snapshot:
                usd_to_syp_old, usd_to_syp_new = get_daily_fx(payment.fx_rate_date or payment.payment_date)
                payment.usd_to_syp_old_snapshot = usd_to_syp_old
                payment.usd_to_syp_new_snapshot = usd_to_syp_new

            payment.amount_usd = payment.amount
            if payment.transaction_currency != 'USD':
                payment.amount_usd = to_usd(
                    payment.amount,
                    payment.transaction_currency,
                    usd_to_syp_old=payment.usd_to_syp_old_snapshot,
                    usd_to_syp_new=payment.usd_to_syp_new_snapshot
                )
            payment.save(update_fields=['fx_rate_date', 'usd_to_syp_old_snapshot', 'usd_to_syp_new_snapshot', 'amount_usd'])
        
        # Calculate already allocated amount for this payment
        existing_allocations_usd = PaymentAllocation.objects.filter(
            payment=payment
        ).aggregate(total=Sum('amount_usd'))['total'] or Decimal('0.00')
        
        remaining_payment_usd = payment.amount_usd - existing_allocations_usd
        
        if remaining_payment_usd <= 0:
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
            
            amount_to_allocate_usd = remaining_payment_usd
            
            for invoice in unpaid_invoices:
                if amount_to_allocate_usd <= 0:
                    break

                if invoice.total_amount_usd == 0 and invoice.total_amount:
                    if invoice.transaction_currency == 'USD':
                        invoice.total_amount_usd = invoice.total_amount
                    else:
                        if not invoice.usd_to_syp_old_snapshot or not invoice.usd_to_syp_new_snapshot:
                            usd_to_syp_old, usd_to_syp_new = get_daily_fx(invoice.fx_rate_date or invoice.invoice_date)
                            invoice.fx_rate_date = invoice.fx_rate_date or invoice.invoice_date
                            invoice.usd_to_syp_old_snapshot = usd_to_syp_old
                            invoice.usd_to_syp_new_snapshot = usd_to_syp_new
                        invoice.total_amount_usd = to_usd(
                            invoice.total_amount,
                            invoice.transaction_currency,
                            usd_to_syp_old=invoice.usd_to_syp_old_snapshot,
                            usd_to_syp_new=invoice.usd_to_syp_new_snapshot
                        )

                    if invoice.paid_amount_usd == 0 and invoice.paid_amount:
                        if invoice.transaction_currency == 'USD':
                            invoice.paid_amount_usd = invoice.paid_amount
                        else:
                            invoice.paid_amount_usd = to_usd(
                                invoice.paid_amount,
                                invoice.transaction_currency,
                                usd_to_syp_old=invoice.usd_to_syp_old_snapshot,
                                usd_to_syp_new=invoice.usd_to_syp_new_snapshot
                            )

                    invoice.save(update_fields=['fx_rate_date', 'usd_to_syp_old_snapshot', 'usd_to_syp_new_snapshot', 'total_amount_usd', 'paid_amount_usd'])
                
                invoice_remaining_usd = invoice.remaining_amount_usd
                if invoice_remaining_usd <= 0:
                    continue
                
                # Allocate the minimum of remaining payment and invoice remaining
                allocation_amount_usd = min(amount_to_allocate_usd, invoice_remaining_usd)
                allocation_amount = from_usd(
                    allocation_amount_usd,
                    invoice.transaction_currency,
                    usd_to_syp_old=invoice.usd_to_syp_old_snapshot,
                    usd_to_syp_new=invoice.usd_to_syp_new_snapshot
                )
                
                # Check if allocation already exists for this payment-invoice pair
                existing = PaymentAllocation.objects.filter(
                    payment=payment,
                    invoice=invoice
                ).first()
                
                if existing:
                    # Update existing allocation
                    if existing.amount_usd == 0 and existing.amount:
                        existing.amount_usd = to_usd(
                            existing.amount,
                            invoice.transaction_currency,
                            usd_to_syp_old=invoice.usd_to_syp_old_snapshot,
                            usd_to_syp_new=invoice.usd_to_syp_new_snapshot
                        )
                    existing.amount_usd += allocation_amount_usd
                    existing.amount = from_usd(
                        existing.amount_usd,
                        invoice.transaction_currency,
                        usd_to_syp_old=invoice.usd_to_syp_old_snapshot,
                        usd_to_syp_new=invoice.usd_to_syp_new_snapshot
                    )
                    existing.save(update_fields=['amount', 'amount_usd'])
                    created_allocations.append(existing)
                else:
                    # Create new allocation
                    allocation = PaymentAllocation.objects.create(
                        payment=payment,
                        invoice=invoice,
                        amount=allocation_amount,
                        amount_usd=allocation_amount_usd
                    )
                    created_allocations.append(allocation)
                
                # Update invoice paid amount and status
                invoice.paid_amount_usd += allocation_amount_usd
                invoice.paid_amount = from_usd(
                    invoice.paid_amount_usd,
                    invoice.transaction_currency,
                    usd_to_syp_old=invoice.usd_to_syp_old_snapshot,
                    usd_to_syp_new=invoice.usd_to_syp_new_snapshot
                )

                if invoice.paid_amount_usd >= invoice.total_amount_usd - Decimal('0.01'):
                    invoice.status = Invoice.Status.PAID
                else:
                    invoice.status = Invoice.Status.PARTIAL
                invoice.save(update_fields=['paid_amount', 'paid_amount_usd', 'status'])
                
                amount_to_allocate_usd -= allocation_amount_usd
        
        else:
            # Manual allocation
            if not allocations:
                raise ValidationException(
                    'يجب تحديد الفواتير للتخصيص أو استخدام التخصيص التلقائي',
                    field='allocations'
                )
            
            total_allocation_usd = Decimal('0.00')

            for alloc in allocations:
                invoice_id = alloc['invoice_id']
                amount = alloc.get('amount')
                amount_usd = alloc.get('amount_usd')

                if amount_usd is not None:
                    amount_usd = Decimal(str(amount_usd))
                    if amount_usd <= 0:
                        continue
                else:
                    if amount is None:
                        continue
                    amount = Decimal(str(amount))
                    if amount <= 0:
                        continue

                invoice = Invoice.objects.get(id=invoice_id)

                if invoice.transaction_currency != 'USD' and (not invoice.usd_to_syp_old_snapshot or not invoice.usd_to_syp_new_snapshot):
                    usd_to_syp_old, usd_to_syp_new = get_daily_fx(invoice.fx_rate_date or invoice.invoice_date)
                    invoice.fx_rate_date = invoice.fx_rate_date or invoice.invoice_date
                    invoice.usd_to_syp_old_snapshot = usd_to_syp_old
                    invoice.usd_to_syp_new_snapshot = usd_to_syp_new
                    invoice.save(update_fields=['fx_rate_date', 'usd_to_syp_old_snapshot', 'usd_to_syp_new_snapshot'])

                alloc_usd = amount_usd
                if alloc_usd is None:
                    alloc_usd = amount
                    if invoice.transaction_currency != 'USD':
                        alloc_usd = to_usd(
                            amount,
                            invoice.transaction_currency,
                            usd_to_syp_old=invoice.usd_to_syp_old_snapshot,
                            usd_to_syp_new=invoice.usd_to_syp_new_snapshot
                        )
                total_allocation_usd += alloc_usd

            if total_allocation_usd > remaining_payment_usd + Decimal('0.01'):
                raise ValidationException(
                    f'إجمالي التخصيصات ({total_allocation_usd}) يتجاوز المبلغ المتبقي ({remaining_payment_usd})',
                    field='amount'
                )
            
            for alloc in allocations:
                invoice_id = alloc['invoice_id']
                amount = alloc.get('amount')
                amount_usd = alloc.get('amount_usd')

                if amount_usd is not None:
                    amount_usd = Decimal(str(amount_usd))
                    if amount_usd <= 0:
                        continue
                else:
                    if amount is None:
                        continue
                    amount = Decimal(str(amount))
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
                if invoice.total_amount_usd == 0 and invoice.total_amount:
                    if invoice.transaction_currency == 'USD':
                        invoice.total_amount_usd = invoice.total_amount
                    else:
                        if not invoice.usd_to_syp_old_snapshot or not invoice.usd_to_syp_new_snapshot:
                            usd_to_syp_old, usd_to_syp_new = get_daily_fx(invoice.fx_rate_date or invoice.invoice_date)
                            invoice.fx_rate_date = invoice.fx_rate_date or invoice.invoice_date
                            invoice.usd_to_syp_old_snapshot = usd_to_syp_old
                            invoice.usd_to_syp_new_snapshot = usd_to_syp_new
                        invoice.total_amount_usd = to_usd(
                            invoice.total_amount,
                            invoice.transaction_currency,
                            usd_to_syp_old=invoice.usd_to_syp_old_snapshot,
                            usd_to_syp_new=invoice.usd_to_syp_new_snapshot
                        )

                    if invoice.paid_amount_usd == 0 and invoice.paid_amount:
                        if invoice.transaction_currency == 'USD':
                            invoice.paid_amount_usd = invoice.paid_amount
                        else:
                            invoice.paid_amount_usd = to_usd(
                                invoice.paid_amount,
                                invoice.transaction_currency,
                                usd_to_syp_old=invoice.usd_to_syp_old_snapshot,
                                usd_to_syp_new=invoice.usd_to_syp_new_snapshot
                            )

                    invoice.save(update_fields=['fx_rate_date', 'usd_to_syp_old_snapshot', 'usd_to_syp_new_snapshot', 'total_amount_usd', 'paid_amount_usd'])

                invoice_remaining_usd = invoice.remaining_amount_usd

                alloc_usd = amount_usd
                if alloc_usd is None:
                    alloc_usd = amount
                    if invoice.transaction_currency != 'USD':
                        alloc_usd = to_usd(
                            amount,
                            invoice.transaction_currency,
                            usd_to_syp_old=invoice.usd_to_syp_old_snapshot,
                            usd_to_syp_new=invoice.usd_to_syp_new_snapshot
                        )

                if alloc_usd > invoice_remaining_usd + Decimal('0.01'):
                    requested_amount = from_usd(
                        alloc_usd,
                        invoice.transaction_currency,
                        usd_to_syp_old=invoice.usd_to_syp_old_snapshot,
                        usd_to_syp_new=invoice.usd_to_syp_new_snapshot
                    )
                    raise AllocationExceedsRemainingException(
                        invoice.invoice_number,
                        invoice.remaining_amount,
                        requested_amount
                    )
                
                # Check if allocation already exists
                existing = PaymentAllocation.objects.filter(
                    payment=payment,
                    invoice=invoice
                ).first()

                amount_usd = alloc_usd
                amount = from_usd(
                    amount_usd,
                    invoice.transaction_currency,
                    usd_to_syp_old=invoice.usd_to_syp_old_snapshot,
                    usd_to_syp_new=invoice.usd_to_syp_new_snapshot
                )
                
                if existing:
                    # Validate combined allocation doesn't exceed remaining
                    if existing.amount_usd == 0 and existing.amount:
                        existing.amount_usd = to_usd(
                            existing.amount,
                            invoice.transaction_currency,
                            usd_to_syp_old=invoice.usd_to_syp_old_snapshot,
                            usd_to_syp_new=invoice.usd_to_syp_new_snapshot
                        )
                    existing.amount_usd += amount_usd
                    existing.amount = from_usd(
                        existing.amount_usd,
                        invoice.transaction_currency,
                        usd_to_syp_old=invoice.usd_to_syp_old_snapshot,
                        usd_to_syp_new=invoice.usd_to_syp_new_snapshot
                    )
                    existing.save(update_fields=['amount', 'amount_usd'])
                    created_allocations.append(existing)
                else:
                    allocation = PaymentAllocation.objects.create(
                        payment=payment,
                        invoice=invoice,
                        amount=amount,
                        amount_usd=amount_usd
                    )
                    created_allocations.append(allocation)
                
                # Update invoice paid amount and status
                invoice.paid_amount_usd += amount_usd
                invoice.paid_amount = from_usd(
                    invoice.paid_amount_usd,
                    invoice.transaction_currency,
                    usd_to_syp_old=invoice.usd_to_syp_old_snapshot,
                    usd_to_syp_new=invoice.usd_to_syp_new_snapshot
                )

                if invoice.paid_amount_usd >= invoice.total_amount_usd - Decimal('0.01'):
                    invoice.status = Invoice.Status.PAID
                else:
                    invoice.status = Invoice.Status.PARTIAL
                invoice.save(update_fields=['paid_amount', 'paid_amount_usd', 'status'])
        
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
        
        results = []
        for inv in invoices:
            if inv.total_amount_usd == 0 and inv.total_amount:
                if inv.transaction_currency == 'USD':
                    inv.total_amount_usd = inv.total_amount
                    inv.paid_amount_usd = inv.paid_amount
                else:
                    if not inv.usd_to_syp_old_snapshot or not inv.usd_to_syp_new_snapshot:
                        usd_to_syp_old, usd_to_syp_new = get_daily_fx(inv.fx_rate_date or inv.invoice_date)
                        inv.fx_rate_date = inv.fx_rate_date or inv.invoice_date
                        inv.usd_to_syp_old_snapshot = usd_to_syp_old
                        inv.usd_to_syp_new_snapshot = usd_to_syp_new
                    inv.total_amount_usd = to_usd(
                        inv.total_amount,
                        inv.transaction_currency,
                        usd_to_syp_old=inv.usd_to_syp_old_snapshot,
                        usd_to_syp_new=inv.usd_to_syp_new_snapshot
                    )
                    inv.paid_amount_usd = to_usd(
                        inv.paid_amount,
                        inv.transaction_currency,
                        usd_to_syp_old=inv.usd_to_syp_old_snapshot,
                        usd_to_syp_new=inv.usd_to_syp_new_snapshot
                    )
                inv.save(update_fields=['fx_rate_date', 'usd_to_syp_old_snapshot', 'usd_to_syp_new_snapshot', 'total_amount_usd', 'paid_amount_usd'])

            results.append(
                {
                    'id': inv.id,
                    'invoice_number': inv.invoice_number,
                    'invoice_date': inv.invoice_date,
                    'due_date': inv.due_date,
                    'transaction_currency': inv.transaction_currency,
                    'fx_rate_date': inv.fx_rate_date,
                    'usd_to_syp_old_snapshot': inv.usd_to_syp_old_snapshot,
                    'usd_to_syp_new_snapshot': inv.usd_to_syp_new_snapshot,
                    'total_amount': inv.total_amount,
                    'paid_amount': inv.paid_amount,
                    'remaining_amount': inv.remaining_amount,
                    'total_amount_usd': inv.total_amount_usd,
                    'paid_amount_usd': inv.paid_amount_usd,
                    'remaining_amount_usd': inv.remaining_amount_usd,
                    'status': inv.status,
                    'is_overdue': inv.due_date and inv.due_date < date.today()
                }
            )
        return results
