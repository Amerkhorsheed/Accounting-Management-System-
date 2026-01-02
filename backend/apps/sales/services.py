"""
Sales Services - Business Logic
"""
from decimal import Decimal
from datetime import datetime
from typing import List, Dict, Any, Optional
from django.db import transaction
from django.db.models import Sum, F
from apps.core.exceptions import ValidationException, InvalidOperationException, InsufficientStockException
from apps.core.decorators import handle_service_error
from apps.core.utils import get_daily_fx, to_usd, from_usd, normalize_fx
from apps.inventory.services import InventoryService
from apps.inventory.models import StockMovement, Product
from .models import Customer, Invoice, InvoiceItem, Payment, SalesReturn, SalesReturnItem, PaymentAllocation, CreditLimitOverride
from .credit_service import CreditService, CreditValidationStatus, CreditLimitExceededException


class SalesService:
    """Service class for sales operations."""

    @staticmethod
    @handle_service_error
    @transaction.atomic
    def create_invoice(
        customer_id: int,
        warehouse_id: int,
        invoice_date,
        items: List[Dict],
        invoice_type: str = 'cash',
        discount_percent: Decimal = Decimal('0.00'),
        discount_amount: Decimal = Decimal('0.00'),
        due_date=None,
        notes: str = None,
        internal_notes: str = None,
        user=None,
        deduct_stock: bool = True,
        override_credit_limit: bool = False,
        override_reason: str = None,
        transaction_currency: str = 'SYP_OLD',
        fx_rate_date=None,
        usd_to_syp_old_snapshot: Decimal = None,
        usd_to_syp_new_snapshot: Decimal = None
    ) -> Invoice:
        """
        Create a new sales invoice.
        
        For credit invoices (invoice_type='credit'):
        - Validates customer credit limit before creation
        - Auto-calculates due_date based on customer payment_terms if not provided
        - Supports override_credit_limit flag to bypass credit limit with reason
        
        Requirements: 1.1, 1.2, 1.4, 1.5, 3.4, 3.6
        
        Args:
            customer_id: The customer's ID
            warehouse_id: The warehouse ID
            invoice_date: Date of the invoice
            items: List of invoice items (can include product_unit_id for unit selection)
            invoice_type: 'cash' or 'credit'
            discount_percent: Invoice-level discount percentage
            discount_amount: Invoice-level discount amount
            due_date: Due date for credit invoices (auto-calculated if not provided)
            notes: Customer-visible notes
            internal_notes: Internal notes
            user: The user creating the invoice
            deduct_stock: Whether to validate stock availability
            override_credit_limit: If True, bypass credit limit check (requires override_reason)
            override_reason: Reason for credit limit override (required if override_credit_limit=True)
            
        Returns:
            The created Invoice
            
        Raises:
            CreditLimitExceededException: If credit limit exceeded and no override
            ValidationException: If credit invoice without customer or invalid override
        """
        from apps.inventory.models import ProductUnit

        needs_fx = transaction_currency != 'USD' or invoice_type == Invoice.InvoiceType.CREDIT
        usd_to_syp_old = None
        usd_to_syp_new = None
        if needs_fx:
            if usd_to_syp_old_snapshot is None and usd_to_syp_new_snapshot is None:
                usd_to_syp_old, usd_to_syp_new = get_daily_fx(fx_rate_date or invoice_date)
            else:
                usd_to_syp_old, usd_to_syp_new = normalize_fx(usd_to_syp_old_snapshot, usd_to_syp_new_snapshot)
        
        # Requirement 1.1: Credit invoices require customer selection
        if invoice_type == Invoice.InvoiceType.CREDIT:
            if not customer_id:
                raise ValidationException(
                    'يجب اختيار عميل للفاتورة الآجلة',
                    field='customer'
                )
        
        # Validate stock availability if deducting
        if deduct_stock:
            for item in items:
                product = Product.objects.get(id=item['product_id'])
                if product.track_stock:
                    # Calculate base_quantity for stock validation
                    quantity = Decimal(str(item['quantity']))
                    product_unit_id = item.get('product_unit_id')
                    
                    if product_unit_id:
                        product_unit = ProductUnit.objects.get(id=product_unit_id)
                        base_quantity = product_unit.convert_to_base(quantity)
                    else:
                        # Default to base unit
                        base_unit = ProductUnit.objects.filter(
                            product=product,
                            is_base_unit=True,
                            is_deleted=False
                        ).first()
                        if base_unit:
                            base_quantity = base_unit.convert_to_base(quantity)
                        else:
                            base_quantity = quantity
                    
                    stock_info = InventoryService.get_product_stock(
                        item['product_id'], warehouse_id
                    )
                    if stock_info['total_available'] < base_quantity:
                        raise InsufficientStockException(
                            product.name,
                            int(base_quantity),
                            int(stock_info['total_available'])
                        )
        
        # Calculate estimated total for credit validation
        estimated_total = Decimal('0.00')
        for item in items:
            product = Product.objects.get(id=item['product_id'])

            if transaction_currency == 'USD':
                if product.sale_price_usd is not None:
                    default_unit_price = product.sale_price_usd
                else:
                    default_unit_price = product.sale_price
            else:
                if product.sale_price_usd is not None and usd_to_syp_old is not None and usd_to_syp_new is not None:
                    default_unit_price = from_usd(
                        product.sale_price_usd,
                        transaction_currency,
                        usd_to_syp_old=usd_to_syp_old,
                        usd_to_syp_new=usd_to_syp_new
                    )
                else:
                    default_unit_price = product.sale_price

            unit_price = Decimal(str(item.get('unit_price', default_unit_price)))
            quantity = Decimal(str(item['quantity']))
            item_discount = Decimal(str(item.get('discount_percent', '0.00')))
            tax_rate = Decimal(str(item.get('tax_rate', product.tax_rate if product.is_taxable else '0.00')))
            
            subtotal = quantity * unit_price
            discount_amt = (subtotal * item_discount) / 100
            taxable = subtotal - discount_amt
            tax_amt = (taxable * tax_rate) / 100
            estimated_total += taxable + tax_amt
        
        # Apply invoice-level discount
        if discount_percent > 0:
            estimated_total -= (estimated_total * discount_percent) / 100
        if discount_amount > 0:
            estimated_total -= discount_amount

        estimated_total_usd = estimated_total
        if transaction_currency != 'USD':
            if usd_to_syp_old is None or usd_to_syp_new is None:
                usd_to_syp_old, usd_to_syp_new = get_daily_fx(fx_rate_date or invoice_date)
            estimated_total_usd = to_usd(
                estimated_total,
                transaction_currency,
                usd_to_syp_old=usd_to_syp_old,
                usd_to_syp_new=usd_to_syp_new
            )
        
        credit_validation_result = None
        
        # Requirement 1.4: Credit limit validation for credit invoices
        if invoice_type == Invoice.InvoiceType.CREDIT and customer_id:
            credit_validation_result = CreditService.validate_credit_limit(
                customer_id, estimated_total_usd, fx_rate_date or invoice_date
            )
            
            # If credit limit exceeded and no override requested
            if credit_validation_result.status == CreditValidationStatus.ERROR:
                if not override_credit_limit:
                    raise CreditLimitExceededException(
                        customer.name,
                        credit_validation_result.current_balance,
                        credit_validation_result.credit_limit,
                        estimated_total_usd
                    )
                
                # Override requested - validate reason is provided
                if not override_reason:
                    raise ValidationException(
                        'يجب تحديد سبب تجاوز حد الائتمان',
                        field='override_reason'
                    )
        
        # Requirement 1.2: Calculate due_date for credit invoices if not provided
        if invoice_type == Invoice.InvoiceType.CREDIT and not due_date and customer_id:
            due_date = CreditService.calculate_due_date(customer_id, invoice_date)
        
        # Create invoice
        invoice = Invoice.objects.create(
            invoice_type=invoice_type,
            customer_id=customer_id,
            warehouse_id=warehouse_id,
            invoice_date=invoice_date,
            due_date=due_date,
            transaction_currency=transaction_currency,
            fx_rate_date=(fx_rate_date or invoice_date) if needs_fx else None,
            usd_to_syp_old_snapshot=usd_to_syp_old if needs_fx else None,
            usd_to_syp_new_snapshot=usd_to_syp_new if needs_fx else None,
            discount_percent=discount_percent,
            discount_amount=discount_amount,
            notes=notes,
            internal_notes=internal_notes,
            status=Invoice.Status.DRAFT,
            created_by=user
        )
        
        # Create items
        for item in items:
            product = Product.objects.get(id=item['product_id'])
            product_unit_id = item.get('product_unit_id')
            product_unit = None
            
            if product_unit_id:
                product_unit = ProductUnit.objects.get(id=product_unit_id)

            if transaction_currency == 'USD':
                if product_unit and product_unit.sale_price_usd is not None:
                    default_unit_price = product_unit.sale_price_usd
                elif product.sale_price_usd is not None:
                    default_unit_price = product.sale_price_usd
                else:
                    default_unit_price = product.sale_price

                if product_unit and product_unit.cost_price_usd is not None:
                    default_cost_price = product_unit.cost_price_usd
                elif product.cost_price_usd is not None:
                    default_cost_price = product.cost_price_usd
                else:
                    default_cost_price = product.cost_price
            else:
                if product_unit and product_unit.sale_price_usd is not None and usd_to_syp_old is not None and usd_to_syp_new is not None:
                    default_unit_price = from_usd(
                        product_unit.sale_price_usd,
                        transaction_currency,
                        usd_to_syp_old=usd_to_syp_old,
                        usd_to_syp_new=usd_to_syp_new
                    )
                elif product.sale_price_usd is not None and usd_to_syp_old is not None and usd_to_syp_new is not None:
                    default_unit_price = from_usd(
                        product.sale_price_usd,
                        transaction_currency,
                        usd_to_syp_old=usd_to_syp_old,
                        usd_to_syp_new=usd_to_syp_new
                    )
                elif product_unit and product_unit.sale_price:
                    default_unit_price = product_unit.sale_price
                else:
                    default_unit_price = product.sale_price

                if product_unit and product_unit.cost_price_usd is not None and usd_to_syp_old is not None and usd_to_syp_new is not None:
                    default_cost_price = from_usd(
                        product_unit.cost_price_usd,
                        transaction_currency,
                        usd_to_syp_old=usd_to_syp_old,
                        usd_to_syp_new=usd_to_syp_new
                    )
                elif product.cost_price_usd is not None and usd_to_syp_old is not None and usd_to_syp_new is not None:
                    default_cost_price = from_usd(
                        product.cost_price_usd,
                        transaction_currency,
                        usd_to_syp_old=usd_to_syp_old,
                        usd_to_syp_new=usd_to_syp_new
                    )
                elif product_unit and product_unit.cost_price:
                    default_cost_price = product_unit.cost_price
                else:
                    default_cost_price = product.cost_price
            
            InvoiceItem.objects.create(
                invoice=invoice,
                product=product,
                product_unit=product_unit,
                quantity=item['quantity'],
                unit_price=item.get('unit_price', default_unit_price),
                cost_price=item.get('cost_price', default_cost_price),
                discount_percent=item.get('discount_percent', Decimal('0.00')),
                tax_rate=item.get('tax_rate', product.tax_rate if product.is_taxable else Decimal('0.00')),
                notes=item.get('notes'),
                created_by=user
            )
        
        invoice.calculate_totals()
        
        # Requirement 6.5: Log credit limit override if applicable
        if (invoice_type == Invoice.InvoiceType.CREDIT and 
            override_credit_limit and 
            credit_validation_result and 
            credit_validation_result.status == CreditValidationStatus.ERROR):
            
            CreditLimitOverride.objects.create(
                customer_id=customer_id,
                invoice=invoice,
                override_amount=invoice.total_amount_usd - credit_validation_result.available_credit,
                reason=override_reason,
                approved_by=user,
                created_by=user
            )
        
        return invoice

    @staticmethod
    @handle_service_error
    @transaction.atomic
    def confirm_invoice(
        invoice_id: int, 
        user=None, 
        paid_amount: Decimal = None, 
        payment_method: str = None
    ) -> Invoice:
        """
        Confirm an invoice, update stock, and handle initial payment.
        
        Requirements: 1.2, 1.5, 3.4, 3.6, 6.1
        
        For each invoice item:
        - Calculates base_quantity using conversion factor from product_unit
        - If no product_unit specified, defaults to product's base unit
        - Uses base_quantity for stock deduction
        """
        from .models import Invoice, Payment
        from apps.inventory.services import InventoryService
        from apps.inventory.models import ProductUnit
        
        invoice = Invoice.objects.select_for_update().get(id=invoice_id)
        
        if invoice.status != Invoice.Status.DRAFT:
            raise InvalidOperationException(
                f"لا يمكن تأكيد فاتورة بحالة {invoice.get_status_display()}"
            )

        invoice.calculate_totals()

        needs_fx = invoice.transaction_currency != 'USD' or invoice.invoice_type == Invoice.InvoiceType.CREDIT
        if needs_fx:
            if invoice.usd_to_syp_old_snapshot is None and invoice.usd_to_syp_new_snapshot is None:
                usd_to_syp_old, usd_to_syp_new = get_daily_fx(invoice.fx_rate_date or invoice.invoice_date)
                invoice.usd_to_syp_old_snapshot = usd_to_syp_old
                invoice.usd_to_syp_new_snapshot = usd_to_syp_new
            else:
                invoice.usd_to_syp_old_snapshot, invoice.usd_to_syp_new_snapshot = normalize_fx(
                    invoice.usd_to_syp_old_snapshot,
                    invoice.usd_to_syp_new_snapshot
                )
            if not invoice.fx_rate_date:
                invoice.fx_rate_date = invoice.invoice_date

        if invoice.transaction_currency == 'USD':
            invoice.total_amount_usd = invoice.total_amount
        else:
            invoice.total_amount_usd = to_usd(
                invoice.total_amount,
                invoice.transaction_currency,
                usd_to_syp_old=invoice.usd_to_syp_old_snapshot,
                usd_to_syp_new=invoice.usd_to_syp_new_snapshot
            )
            
        # Deduct stock for all items
        for item in invoice.items.all():
            # Calculate base_quantity based on product_unit or default to base unit
            # Requirements: 3.4, 3.6
            if item.product_unit:
                # Use the conversion factor from the specified product_unit
                base_quantity = item.product_unit.convert_to_base(item.quantity)
            else:
                # Default to base unit - find the base unit for this product
                base_unit = ProductUnit.objects.filter(
                    product=item.product,
                    is_base_unit=True,
                    is_deleted=False
                ).first()
                
                if base_unit:
                    # Use base unit conversion (should be 1.0)
                    base_quantity = base_unit.convert_to_base(item.quantity)
                else:
                    # No ProductUnit configured, use quantity as-is (legacy behavior)
                    base_quantity = item.quantity
            
            # Update the item's base_quantity
            item.base_quantity = base_quantity
            item.save(update_fields=['base_quantity'])
            
            # Deduct stock using base_quantity
            InventoryService.deduct_stock(
                product_id=item.product_id,
                warehouse_id=invoice.warehouse_id,
                quantity=base_quantity,  # Use base_quantity for stock deduction
                source_type='sale',
                reference_number=invoice.invoice_number,
                reference_type='invoice',
                reference_id=invoice.id,
                user=user
            )
            
        # Handle payment and status
        if invoice.invoice_type == Invoice.InvoiceType.CASH:
            # Cash invoices are fully paid by default if no paid_amount provided
            if paid_amount is not None:
                final_paid = Decimal(str(paid_amount))
            else:
                final_paid = invoice.total_amount
            
            # Use proper decimal comparison with small tolerance
            if final_paid >= invoice.total_amount - Decimal('0.01'):
                invoice.status = Invoice.Status.PAID
                invoice.paid_amount = invoice.total_amount  # Ensure exact match
            else:
                invoice.status = Invoice.Status.PARTIAL
                invoice.paid_amount = final_paid
                
            # Create payment record for cash sales (skip invoice update since we handle it here)
            if invoice.paid_amount > 0:
                SalesService.receive_payment(
                    customer_id=invoice.customer_id,
                    payment_date=invoice.invoice_date,
                    amount=invoice.paid_amount,
                    payment_method=payment_method or 'cash',
                    invoice_id=invoice.id,
                    user=user,
                    notes='الدفع عند إنشاء الفاتورة',
                    skip_invoice_update=True,
                    transaction_currency=invoice.transaction_currency,
                    fx_rate_date=invoice.fx_rate_date,
                    usd_to_syp_old_snapshot=invoice.usd_to_syp_old_snapshot,
                    usd_to_syp_new_snapshot=invoice.usd_to_syp_new_snapshot
                )
        else:
            # Credit invoice
            if paid_amount and paid_amount > 0:
                paid_decimal = Decimal(str(paid_amount))
                # Use proper decimal comparison with small tolerance
                if paid_decimal >= invoice.total_amount - Decimal('0.01'):
                    invoice.status = Invoice.Status.PAID
                    invoice.paid_amount = invoice.total_amount  # Ensure exact match
                else:
                    invoice.status = Invoice.Status.PARTIAL
                    invoice.paid_amount = paid_decimal
                
                # Create payment record (skip invoice update since we handle it here)
                SalesService.receive_payment(
                    customer_id=invoice.customer_id,
                    payment_date=invoice.invoice_date,
                    amount=invoice.paid_amount,
                    payment_method=payment_method or 'cash',
                    invoice_id=invoice.id,
                    user=user,
                    notes='دفعة مقدمة عند إنشاء الفاتورة',
                    skip_invoice_update=True,
                    transaction_currency=invoice.transaction_currency,
                    fx_rate_date=invoice.fx_rate_date,
                    usd_to_syp_old_snapshot=invoice.usd_to_syp_old_snapshot,
                    usd_to_syp_new_snapshot=invoice.usd_to_syp_new_snapshot
                )
            else:
                invoice.status = Invoice.Status.CONFIRMED
                invoice.paid_amount = Decimal('0.00')
                
            # Update customer balance for credit invoices
            # Requirements: 1.5
            customer = invoice.customer
            if invoice.transaction_currency == 'USD':
                invoice.paid_amount_usd = invoice.paid_amount
            else:
                invoice.paid_amount_usd = to_usd(
                    invoice.paid_amount,
                    invoice.transaction_currency,
                    usd_to_syp_old=invoice.usd_to_syp_old_snapshot,
                    usd_to_syp_new=invoice.usd_to_syp_new_snapshot
                )

            remaining_syp_old = invoice.remaining_amount
            if invoice.transaction_currency == 'SYP_NEW':
                remaining_syp_old = invoice.remaining_amount * Decimal('100')
            elif invoice.transaction_currency == 'USD':
                remaining_syp_old = from_usd(
                    invoice.remaining_amount_usd,
                    'SYP_OLD',
                    usd_to_syp_old=invoice.usd_to_syp_old_snapshot,
                    usd_to_syp_new=invoice.usd_to_syp_new_snapshot
                )

            customer.current_balance += remaining_syp_old
            customer.current_balance_usd += invoice.remaining_amount_usd
            customer.save()
        
        if invoice.transaction_currency == 'USD':
            invoice.paid_amount_usd = invoice.paid_amount
        else:
            invoice.paid_amount_usd = to_usd(
                invoice.paid_amount,
                invoice.transaction_currency,
                usd_to_syp_old=invoice.usd_to_syp_old_snapshot,
                usd_to_syp_new=invoice.usd_to_syp_new_snapshot
            )

        invoice.save(
            update_fields=[
                'status',
                'paid_amount',
                'transaction_currency',
                'fx_rate_date',
                'usd_to_syp_old_snapshot',
                'usd_to_syp_new_snapshot',
                'total_amount_usd',
                'paid_amount_usd'
            ]
        )
        return invoice

    @staticmethod
    @handle_service_error
    @transaction.atomic
    def receive_payment(
        customer_id: int,
        payment_date,
        amount: Decimal,
        payment_method: str,
        invoice_id: int = None,
        transaction_currency: str = 'SYP_OLD',
        fx_rate_date=None,
        usd_to_syp_old_snapshot: Decimal = None,
        usd_to_syp_new_snapshot: Decimal = None,
        allocations: Optional[List[Dict[str, Any]]] = None,
        auto_allocate: bool = False,
        reference: str = None,
        notes: str = None,
        user=None,
        skip_invoice_update: bool = False
    ) -> Payment:
        """
        Record a customer payment with optional invoice allocations.
        
        Supports three modes:
        1. Legacy mode: Single invoice_id for backward compatibility
        2. Manual allocation: Provide allocations list with invoice_id and amount
        3. Auto allocation (FIFO): Set auto_allocate=True to apply to oldest invoices
        
        Requirements: 2.1, 2.2, 2.3, 2.4
        
        Args:
            customer_id: The customer's ID
            payment_date: Date of the payment
            amount: Payment amount
            payment_method: Payment method (cash, card, bank, check, credit)
            invoice_id: Single invoice ID (legacy mode, for backward compatibility)
            allocations: List of dicts with 'invoice_id' and 'amount' keys
            auto_allocate: If True, uses FIFO strategy (oldest invoices first)
            reference: Payment reference number
            notes: Payment notes
            user: The user recording the payment
            skip_invoice_update: If True, skip updating invoice paid_amount and status (used when called from confirm_invoice)
            
        Returns:
            The created Payment
            
        Raises:
            ValidationException: If allocation amounts exceed payment or invoice remaining
        """

        if usd_to_syp_old_snapshot is None and usd_to_syp_new_snapshot is None:
            if transaction_currency != 'USD' or (transaction_currency == 'USD' and not skip_invoice_update):
                usd_to_syp_old_snapshot, usd_to_syp_new_snapshot = get_daily_fx(fx_rate_date or payment_date)
        elif transaction_currency != 'USD' or (transaction_currency == 'USD' and not skip_invoice_update):
            usd_to_syp_old_snapshot, usd_to_syp_new_snapshot = normalize_fx(
                usd_to_syp_old_snapshot,
                usd_to_syp_new_snapshot
            )

        amount_usd = amount
        if transaction_currency != 'USD':
            amount_usd = to_usd(
                amount,
                transaction_currency,
                usd_to_syp_old=usd_to_syp_old_snapshot,
                usd_to_syp_new=usd_to_syp_new_snapshot
            )

        # Create payment record
        payment = Payment.objects.create(
            customer_id=customer_id,
            invoice_id=invoice_id if not allocations and not auto_allocate else None,
            payment_date=payment_date,
            transaction_currency=transaction_currency,
            fx_rate_date=fx_rate_date or payment_date,
            usd_to_syp_old_snapshot=usd_to_syp_old_snapshot,
            usd_to_syp_new_snapshot=usd_to_syp_new_snapshot,
            amount=amount,
            amount_usd=amount_usd,
            payment_method=payment_method,
            reference=reference,
            notes=notes,
            received_by=user,
            created_by=user
        )
        
        # Requirement 2.4: Update customer balance (skip if called from confirm_invoice for credit invoices)
        if not skip_invoice_update:
            customer = Customer.objects.select_for_update().get(id=customer_id)

            amount_syp_old = amount
            if transaction_currency == 'SYP_NEW':
                amount_syp_old = amount * Decimal('100')
            elif transaction_currency == 'USD':
                amount_syp_old = from_usd(
                    amount_usd,
                    'SYP_OLD',
                    usd_to_syp_old=payment.usd_to_syp_old_snapshot,
                    usd_to_syp_new=payment.usd_to_syp_new_snapshot
                )

            customer.current_balance -= amount_syp_old
            customer.current_balance_usd -= amount_usd
            customer.save()
        
        # Handle allocations
        if allocations or auto_allocate:
            # Use CreditService for allocation
            CreditService.allocate_payment(
                payment_id=payment.id,
                allocations=allocations,
                auto_allocate=auto_allocate
            )
        elif invoice_id and not skip_invoice_update:
            # Legacy mode: allocate to single invoice
            invoice = Invoice.objects.select_for_update().get(id=invoice_id)

            if invoice.total_amount_usd == 0 and invoice.transaction_currency != 'USD':
                if not invoice.fx_rate_date:
                    invoice.fx_rate_date = invoice.invoice_date
                if not invoice.usd_to_syp_old_snapshot or not invoice.usd_to_syp_new_snapshot:
                    usd_to_syp_old, usd_to_syp_new = get_daily_fx(invoice.fx_rate_date)
                    invoice.usd_to_syp_old_snapshot = usd_to_syp_old
                    invoice.usd_to_syp_new_snapshot = usd_to_syp_new
                invoice.total_amount_usd = to_usd(
                    invoice.total_amount,
                    invoice.transaction_currency,
                    usd_to_syp_old=invoice.usd_to_syp_old_snapshot,
                    usd_to_syp_new=invoice.usd_to_syp_new_snapshot
                )

            if invoice.transaction_currency == 'USD' and invoice.total_amount_usd == 0:
                invoice.total_amount_usd = invoice.total_amount

            allocation_amount_usd = min(amount_usd, invoice.remaining_amount_usd)
            allocation_amount = from_usd(
                allocation_amount_usd,
                invoice.transaction_currency,
                usd_to_syp_old=invoice.usd_to_syp_old_snapshot,
                usd_to_syp_new=invoice.usd_to_syp_new_snapshot
            )
            
            if allocation_amount > 0:
                # Create allocation record
                PaymentAllocation.objects.create(
                    payment=payment,
                    invoice=invoice,
                    amount=allocation_amount,
                    amount_usd=allocation_amount_usd
                )
                
                invoice.paid_amount_usd += allocation_amount_usd
                invoice.paid_amount = from_usd(
                    invoice.paid_amount_usd,
                    invoice.transaction_currency,
                    usd_to_syp_old=invoice.usd_to_syp_old_snapshot,
                    usd_to_syp_new=invoice.usd_to_syp_new_snapshot
                )
                
                # Requirement 2.2, 2.3: Update invoice status
                if invoice.paid_amount_usd >= invoice.total_amount_usd - Decimal('0.01'):
                    invoice.status = Invoice.Status.PAID
                else:
                    invoice.status = Invoice.Status.PARTIAL
                
                invoice.save(update_fields=['paid_amount', 'paid_amount_usd', 'status', 'fx_rate_date', 'usd_to_syp_old_snapshot', 'usd_to_syp_new_snapshot', 'total_amount_usd'])
        elif invoice_id and skip_invoice_update:
            # Just create the allocation record without updating invoice
            invoice = Invoice.objects.get(id=invoice_id)
            if invoice.transaction_currency != 'USD' and (not invoice.usd_to_syp_old_snapshot or not invoice.usd_to_syp_new_snapshot):
                usd_to_syp_old, usd_to_syp_new = get_daily_fx(invoice.invoice_date)
                invoice.fx_rate_date = invoice.invoice_date
                invoice.usd_to_syp_old_snapshot = usd_to_syp_old
                invoice.usd_to_syp_new_snapshot = usd_to_syp_new
                invoice.total_amount_usd = to_usd(
                    invoice.total_amount,
                    invoice.transaction_currency,
                    usd_to_syp_old=invoice.usd_to_syp_old_snapshot,
                    usd_to_syp_new=invoice.usd_to_syp_new_snapshot
                )
                invoice.save(update_fields=['fx_rate_date', 'usd_to_syp_old_snapshot', 'usd_to_syp_new_snapshot', 'total_amount_usd'])

            alloc_usd = amount_usd
            if invoice.transaction_currency != 'USD':
                alloc_usd = to_usd(
                    amount,
                    invoice.transaction_currency,
                    usd_to_syp_old=invoice.usd_to_syp_old_snapshot,
                    usd_to_syp_new=invoice.usd_to_syp_new_snapshot
                )
            PaymentAllocation.objects.create(
                payment=payment,
                invoice=invoice,
                amount=amount,
                amount_usd=alloc_usd
            )
        
        return payment

    @staticmethod
    @handle_service_error
    @transaction.atomic
    def create_sales_return(
        invoice_id: int,
        return_date,
        items: List[Dict],
        reason: str,
        notes: str = None,
        user=None
    ) -> SalesReturn:
        """Create a sales return."""
        from apps.inventory.models import ProductUnit
        
        invoice = Invoice.objects.get(id=invoice_id)
        
        if invoice.status not in [Invoice.Status.CONFIRMED, Invoice.Status.PAID, Invoice.Status.PARTIAL]:
            raise InvalidOperationException(
                'إنشاء مرتجع',
                'لا يمكن إنشاء مرتجع لفاتورة غير مؤكدة'
            )
        
        # Create return
        sales_return = SalesReturn.objects.create(
            original_invoice=invoice,
            return_date=return_date,
            reason=reason,
            notes=notes,
            created_by=user
        )
        
        total_amount = Decimal('0.00')
        
        for item_data in items:
            invoice_item = InvoiceItem.objects.get(id=item_data['invoice_item_id'])
            quantity = Decimal(str(item_data['quantity']))
            
            # Create return item
            SalesReturnItem.objects.create(
                sales_return=sales_return,
                invoice_item=invoice_item,
                product=invoice_item.product,
                quantity=quantity,
                unit_price=invoice_item.unit_price,
                reason=item_data.get('reason'),
                created_by=user
            )

            # Calculate line total proportionally with original discount/tax
            unit_price = Decimal(str(invoice_item.unit_price or '0'))
            discount_percent = Decimal(str(invoice_item.discount_percent or '0'))
            tax_rate = Decimal(str(invoice_item.tax_rate or '0'))

            line_subtotal = quantity * unit_price
            line_discount = (line_subtotal * discount_percent) / Decimal('100')
            line_taxable = line_subtotal - line_discount
            line_tax = (line_taxable * tax_rate) / Decimal('100')
            line_total = line_taxable + line_tax

            total_amount += line_total
            
            # Add stock back
            if invoice_item.product.track_stock:
                if invoice_item.product_unit:
                    base_quantity = invoice_item.product_unit.convert_to_base(quantity)
                else:
                    base_unit = ProductUnit.objects.filter(
                        product=invoice_item.product,
                        is_base_unit=True,
                        is_deleted=False
                    ).first()
                    if base_unit:
                        base_quantity = base_unit.convert_to_base(quantity)
                    else:
                        base_quantity = quantity

                InventoryService.add_stock(
                    product_id=invoice_item.product_id,
                    warehouse_id=invoice.warehouse_id,
                    quantity=base_quantity,
                    unit_cost=invoice_item.cost_price,
                    source_type=StockMovement.SourceType.RETURN,
                    reference_number=sales_return.return_number,
                    reference_type='SalesReturn',
                    reference_id=sales_return.id,
                    user=user,
                    notes=f"مرتجع مبيعات - الفاتورة رقم {invoice.invoice_number}"
                )
        
        sales_return.total_amount = total_amount
        sales_return.save()
        
        # Adjust customer balance
        customer = invoice.customer
        customer.current_balance -= total_amount
        customer.save()
        
        return sales_return

    @staticmethod
    @handle_service_error
    def get_customer_statement(
        customer_id: int,
        start_date=None,
        end_date=None
    ) -> Dict[str, Any]:
        """
        Get customer account statement with correct opening balance calculation.
        
        Requirements: 6.1, 6.2, 6.3, 6.4
        
        When a date range filter is applied:
        - Opening balance = customer.opening_balance + all transactions before start_date
        - Closing balance = opening_balance + total_debit - total_credit
        - Running balance is calculated correctly from the opening balance
        
        Args:
            customer_id: The customer's ID
            start_date: Optional start date for filtering (inclusive)
            end_date: Optional end date for filtering (inclusive)
            
        Returns:
            Dict with customer info, opening_balance, closing_balance, totals, and transactions
        """
        
        if start_date and isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date and isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

        customer = Customer.objects.get(id=customer_id)
        
        # Get ALL invoices (for opening balance calculation)
        all_invoices = Invoice.objects.filter(
            customer_id=customer_id,
            status__in=[Invoice.Status.CONFIRMED, Invoice.Status.PAID, Invoice.Status.PARTIAL]
        ).order_by('invoice_date', 'id')
        
        # Get ALL payments (for opening balance calculation)
        all_payments = Payment.objects.filter(customer_id=customer_id).order_by('payment_date', 'id')
        
        # Get ALL returns (for opening balance calculation)
        all_returns = SalesReturn.objects.filter(
            original_invoice__customer_id=customer_id
        ).order_by('return_date', 'id')
        
        # Build complete transactions list
        all_transactions = []
        
        for inv in all_invoices:
            all_transactions.append({
                'date': inv.invoice_date,
                'type': 'invoice',
                'reference': inv.invoice_number,
                'debit': inv.total_amount,
                'debit_usd': inv.total_amount_usd,
                'credit': Decimal('0.00'),
                'credit_usd': Decimal('0.00'),
                'transaction_currency': inv.transaction_currency,
                'description': f'فاتورة رقم {inv.invoice_number}',
                'sort_key': (inv.invoice_date, 0, inv.id)  # invoices first within same date
            })
        
        for payment in all_payments:
            all_transactions.append({
                'date': payment.payment_date,
                'type': 'payment',
                'reference': payment.payment_number,
                'debit': Decimal('0.00'),
                'debit_usd': Decimal('0.00'),
                'credit': payment.amount,
                'credit_usd': payment.amount_usd,
                'transaction_currency': payment.transaction_currency,
                'description': f'سند قبض رقم {payment.payment_number}',
                'sort_key': (payment.payment_date, 1, payment.id)  # payments after invoices
            })
        
        for ret in all_returns:
            all_transactions.append({
                'date': ret.return_date,
                'type': 'return',
                'reference': ret.return_number,
                'debit': Decimal('0.00'),
                'debit_usd': Decimal('0.00'),
                'credit': ret.total_amount,
                'credit_usd': ret.total_amount_usd,
                'transaction_currency': ret.transaction_currency,
                'description': f'مرتجع رقم {ret.return_number}',
                'sort_key': (ret.return_date, 2, ret.id)  # returns after payments
            })
        
        # Sort all transactions by date, then type priority, then id
        all_transactions.sort(key=lambda x: x['sort_key'])
        
        # Requirement 6.1, 6.2: Calculate opening balance
        # Opening balance = customer.opening_balance + all transactions before start_date
        opening_balance = customer.opening_balance
        opening_balance_usd = customer.opening_balance_usd
        
        if start_date:
            # Add all transactions before start_date to opening balance
            for txn in all_transactions:
                if txn['date'] < start_date:
                    opening_balance += txn['debit'] - txn['credit']
                    opening_balance_usd += txn.get('debit_usd', Decimal('0.00')) - txn.get('credit_usd', Decimal('0.00'))
        
        # Filter transactions by date range for display
        filtered_transactions = []
        for txn in all_transactions:
            include = True
            if start_date and txn['date'] < start_date:
                include = False
            if end_date and txn['date'] > end_date:
                include = False
            if include:
                # Remove sort_key before adding to result
                filtered_txn = {k: v for k, v in txn.items() if k != 'sort_key'}
                filtered_transactions.append(filtered_txn)
        
        # Calculate running balance for each transaction
        # Requirement 6.4: Running balance starts from opening_balance
        running_balance = opening_balance
        running_balance_usd = opening_balance_usd
        total_debit = Decimal('0.00')
        total_credit = Decimal('0.00')
        total_debit_usd = Decimal('0.00')
        total_credit_usd = Decimal('0.00')
        
        for t in filtered_transactions:
            running_balance = running_balance + t['debit'] - t['credit']
            t['balance'] = running_balance
            total_debit += t['debit']
            total_credit += t['credit']

            debit_usd = t.get('debit_usd', Decimal('0.00'))
            credit_usd = t.get('credit_usd', Decimal('0.00'))
            running_balance_usd = running_balance_usd + debit_usd - credit_usd
            t['balance_usd'] = running_balance_usd
            total_debit_usd += debit_usd
            total_credit_usd += credit_usd
        
        # Requirement 6.3: Closing balance = opening_balance + total_debit - total_credit
        closing_balance = opening_balance + total_debit - total_credit
        closing_balance_usd = opening_balance_usd + total_debit_usd - total_credit_usd
        
        return {
            'customer': {
                'id': customer.id,
                'name': customer.name,
                'code': customer.code
            },
            'period': {
                'start': start_date,
                'end': end_date
            },
            'opening_balance': opening_balance,
            'opening_balance_usd': opening_balance_usd,
            'closing_balance': closing_balance,
            'closing_balance_usd': closing_balance_usd,
            'total_debit': total_debit,
            'total_debit_usd': total_debit_usd,
            'total_credit': total_credit,
            'total_credit_usd': total_credit_usd,
            'total_invoices': sum(t['debit'] for t in filtered_transactions),
            'total_invoices_usd': sum(t.get('debit_usd', Decimal('0.00')) for t in filtered_transactions),
            'total_payments': sum(t['credit'] for t in filtered_transactions if t['type'] == 'payment'),
            'total_payments_usd': sum(t.get('credit_usd', Decimal('0.00')) for t in filtered_transactions if t['type'] == 'payment'),
            'total_returns': sum(t['credit'] for t in filtered_transactions if t['type'] == 'return'),
            'total_returns_usd': sum(t.get('credit_usd', Decimal('0.00')) for t in filtered_transactions if t['type'] == 'return'),
            'transactions': filtered_transactions
        }

    @staticmethod
    @handle_service_error
    def get_invoice_profit(invoice_id: int) -> Dict[str, Any]:
        """Calculate profit for an invoice."""
        
        invoice = Invoice.objects.get(id=invoice_id)
        items = invoice.items.all()

        usd_to_syp_old = invoice.usd_to_syp_old_snapshot
        usd_to_syp_new = invoice.usd_to_syp_new_snapshot
        if invoice.transaction_currency != 'USD' and (not usd_to_syp_old or not usd_to_syp_new):
            try:
                usd_to_syp_old, usd_to_syp_new = get_daily_fx(invoice.fx_rate_date or invoice.invoice_date)
            except Exception:
                usd_to_syp_old, usd_to_syp_new = None, None

        returned = SalesReturnItem.objects.filter(
            invoice_item__invoice=invoice
        ).values('invoice_item_id').annotate(qty=Sum('quantity'))
        returned_by_item = {r['invoice_item_id']: (r['qty'] or Decimal('0')) for r in returned}

        total_revenue = Decimal('0.00')
        total_cost = Decimal('0.00')
        total_revenue_usd = Decimal('0.00')
        total_cost_usd = Decimal('0.00')

        for item in items:
            returned_qty = returned_by_item.get(item.id, Decimal('0.00'))
            net_qty = item.quantity - returned_qty
            if net_qty < 0:
                net_qty = Decimal('0.00')

            if item.quantity and item.quantity > 0:
                revenue = item.total * (net_qty / item.quantity)
            else:
                revenue = Decimal('0.00')

            cost = item.cost_price * net_qty
            total_revenue += revenue
            total_cost += cost

            if invoice.transaction_currency == 'USD':
                revenue_usd = revenue
            elif usd_to_syp_old and usd_to_syp_new:
                revenue_usd = to_usd(
                    revenue,
                    invoice.transaction_currency,
                    usd_to_syp_old=usd_to_syp_old,
                    usd_to_syp_new=usd_to_syp_new
                )
            else:
                revenue_usd = revenue

            total_revenue_usd += revenue_usd
            if invoice.transaction_currency == 'USD':
                cost_usd = cost
            elif usd_to_syp_old and usd_to_syp_new:
                cost_usd = to_usd(
                    cost,
                    invoice.transaction_currency,
                    usd_to_syp_old=usd_to_syp_old,
                    usd_to_syp_new=usd_to_syp_new
                )
            else:
                cost_usd = cost

            total_cost_usd += cost_usd

        gross_profit = total_revenue - total_cost
        gross_profit_usd = total_revenue_usd - total_cost_usd
        profit_margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else Decimal('0')
        profit_margin_usd = (gross_profit_usd / total_revenue_usd * 100) if total_revenue_usd > 0 else Decimal('0')
        
        return {
            'invoice_number': invoice.invoice_number,
            'total_revenue': total_revenue,
            'total_cost': total_cost,
            'gross_profit': gross_profit,
            'profit_margin': profit_margin,
            'total_revenue_usd': total_revenue_usd,
            'total_cost_usd': total_cost_usd,
            'gross_profit_usd': gross_profit_usd,
            'profit_margin_usd': profit_margin_usd,
            'items': [
                {
                    'product': item.product.name,
                    'quantity': item.quantity,
                    'returned_quantity': returned_by_item.get(item.id, Decimal('0.00')),
                    'revenue': item.total,
                    'cost': item.cost_price * item.quantity,
                    'profit': item.profit
                }
                for item in items
            ]
        }

    @staticmethod
    @handle_service_error
    @transaction.atomic
    def cancel_invoice(
        invoice_id: int,
        reason: str,
        user=None
    ) -> Invoice:
        """
        Cancel an invoice and reverse all effects.
        
        This method:
        1. Validates invoice can be cancelled (must be confirmed, paid, or partial)
        2. Reverses stock movements (adds stock back)
        3. Reverses customer balance changes
        4. Updates invoice status to cancelled
        
        Requirements: 4.4, 4.5
        - Property 9: Invoice Cancellation Reversal
        
        Args:
            invoice_id: Invoice to cancel
            reason: Reason for cancellation
            user: User performing cancellation
            
        Returns:
            Updated Invoice
            
        Raises:
            InvalidOperationException: If invoice cannot be cancelled
            ValidationException: If reason is not provided
        """
        from apps.inventory.models import ProductUnit
        
        if not reason or not reason.strip():
            raise ValidationException(
                'يجب تحديد سبب الإلغاء',
                field='reason'
            )
        
        invoice = Invoice.objects.select_for_update().get(id=invoice_id)
        
        # Validate invoice status - can only cancel confirmed, paid, or partial invoices
        allowed_statuses = [Invoice.Status.CONFIRMED, Invoice.Status.PAID, Invoice.Status.PARTIAL]
        if invoice.status not in allowed_statuses:
            raise InvalidOperationException(
                'إلغاء الفاتورة',
                f'لا يمكن إلغاء فاتورة بحالة {invoice.get_status_display()}. يمكن إلغاء الفواتير المؤكدة أو المدفوعة فقط.'
            )
        
        # Reverse stock movements - add stock back for all items
        for item in invoice.items.all():
            if item.product.track_stock:
                # Calculate base_quantity based on product_unit or default to base unit
                if item.product_unit:
                    base_quantity = item.product_unit.convert_to_base(item.quantity)
                else:
                    base_unit = ProductUnit.objects.filter(
                        product=item.product,
                        is_base_unit=True,
                        is_deleted=False
                    ).first()
                    
                    if base_unit:
                        base_quantity = base_unit.convert_to_base(item.quantity)
                    else:
                        base_quantity = item.quantity
                
                # Add stock back using InventoryService
                InventoryService.add_stock(
                    product_id=item.product_id,
                    warehouse_id=invoice.warehouse_id,
                    quantity=base_quantity,
                    unit_cost=item.cost_price,
                    source_type=StockMovement.SourceType.ADJUSTMENT,
                    reference_number=invoice.invoice_number,
                    reference_type='invoice_cancellation',
                    reference_id=invoice.id,
                    user=user,
                    notes=f'إلغاء فاتورة رقم {invoice.invoice_number} - السبب: {reason}'
                )
        
        # Reverse customer balance changes
        # For credit invoices, the customer balance was increased by (total - paid)
        # We need to decrease it by the same amount
        if invoice.invoice_type == Invoice.InvoiceType.CREDIT:
            customer = invoice.customer
            if invoice.total_amount_usd == 0 and invoice.total_amount:
                if invoice.transaction_currency == 'USD':
                    invoice.total_amount_usd = invoice.total_amount
                elif invoice.usd_to_syp_old_snapshot and invoice.usd_to_syp_new_snapshot:
                    invoice.total_amount_usd = to_usd(
                        invoice.total_amount,
                        invoice.transaction_currency,
                        usd_to_syp_old=invoice.usd_to_syp_old_snapshot,
                        usd_to_syp_new=invoice.usd_to_syp_new_snapshot
                    )

            if invoice.paid_amount_usd == 0 and invoice.paid_amount:
                if invoice.transaction_currency == 'USD':
                    invoice.paid_amount_usd = invoice.paid_amount
                elif invoice.usd_to_syp_old_snapshot and invoice.usd_to_syp_new_snapshot:
                    invoice.paid_amount_usd = to_usd(
                        invoice.paid_amount,
                        invoice.transaction_currency,
                        usd_to_syp_old=invoice.usd_to_syp_old_snapshot,
                        usd_to_syp_new=invoice.usd_to_syp_new_snapshot
                    )

            unpaid_amount_usd = invoice.remaining_amount_usd

            unpaid_amount_syp_old = invoice.remaining_amount
            if invoice.transaction_currency == 'SYP_NEW':
                unpaid_amount_syp_old = invoice.remaining_amount * Decimal('100')
            elif invoice.transaction_currency == 'USD':
                if invoice.usd_to_syp_old_snapshot and invoice.usd_to_syp_new_snapshot:
                    unpaid_amount_syp_old = from_usd(
                        unpaid_amount_usd,
                        'SYP_OLD',
                        usd_to_syp_old=invoice.usd_to_syp_old_snapshot,
                        usd_to_syp_new=invoice.usd_to_syp_new_snapshot
                    )

            customer.current_balance -= unpaid_amount_syp_old
            customer.current_balance_usd -= unpaid_amount_usd
            customer.save(update_fields=['current_balance', 'current_balance_usd'])
        
        # Update invoice status to cancelled
        invoice.status = Invoice.Status.CANCELLED
        invoice.internal_notes = f"{invoice.internal_notes or ''}\n\nتم الإلغاء بواسطة: {user.full_name if user else 'النظام'}\nالسبب: {reason}".strip()
        invoice.save(update_fields=['status', 'internal_notes'])
        
        return invoice
