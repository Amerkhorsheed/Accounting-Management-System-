"""
Sales Services - Business Logic
"""
from decimal import Decimal
from typing import List, Dict, Any, Optional
from django.db import transaction
from django.db.models import Sum, F
from apps.core.exceptions import ValidationException, InvalidOperationException, InsufficientStockException
from apps.core.decorators import handle_service_error
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
        override_reason: str = None
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
            unit_price = Decimal(str(item.get('unit_price', product.sale_price)))
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
        
        credit_validation_result = None
        
        # Requirement 1.4: Credit limit validation for credit invoices
        if invoice_type == Invoice.InvoiceType.CREDIT and customer_id:
            credit_validation_result = CreditService.validate_credit_limit(
                customer_id, estimated_total
            )
            
            # If credit limit exceeded and no override requested
            if credit_validation_result.status == CreditValidationStatus.ERROR:
                if not override_credit_limit:
                    customer = Customer.objects.get(id=customer_id)
                    raise CreditLimitExceededException(
                        customer.name,
                        credit_validation_result.current_balance,
                        credit_validation_result.credit_limit,
                        estimated_total
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
            
            InvoiceItem.objects.create(
                invoice=invoice,
                product=product,
                product_unit=product_unit,
                quantity=item['quantity'],
                unit_price=item.get('unit_price', product.sale_price),
                cost_price=product.cost_price,
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
                override_amount=invoice.total_amount - credit_validation_result.available_credit,
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
                    skip_invoice_update=True
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
                    skip_invoice_update=True
                )
            else:
                invoice.status = Invoice.Status.CONFIRMED
                invoice.paid_amount = Decimal('0.00')
                
            # Update customer balance for credit invoices
            # Requirements: 1.5
            customer = invoice.customer
            customer.current_balance += (invoice.total_amount - invoice.paid_amount)
            customer.save()
        
        # Explicitly save status and paid_amount
        invoice.save(update_fields=['status', 'paid_amount'])
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
        
        # Create payment record
        payment = Payment.objects.create(
            customer_id=customer_id,
            invoice_id=invoice_id if not allocations and not auto_allocate else None,
            payment_date=payment_date,
            amount=amount,
            payment_method=payment_method,
            reference=reference,
            notes=notes,
            received_by=user,
            created_by=user
        )
        
        # Requirement 2.4: Update customer balance (skip if called from confirm_invoice for credit invoices)
        if not skip_invoice_update:
            customer = Customer.objects.select_for_update().get(id=customer_id)
            customer.current_balance -= amount
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
            
            # Calculate allocation amount (minimum of payment and remaining)
            allocation_amount = min(amount, invoice.remaining_amount)
            
            if allocation_amount > 0:
                # Create allocation record
                PaymentAllocation.objects.create(
                    payment=payment,
                    invoice=invoice,
                    amount=allocation_amount
                )
                
                # Update invoice paid amount
                invoice.paid_amount += allocation_amount
                
                # Requirement 2.2, 2.3: Update invoice status
                if invoice.paid_amount >= invoice.total_amount:
                    invoice.status = Invoice.Status.PAID
                else:
                    invoice.status = Invoice.Status.PARTIAL
                
                invoice.save()
        elif invoice_id and skip_invoice_update:
            # Just create the allocation record without updating invoice
            invoice = Invoice.objects.get(id=invoice_id)
            PaymentAllocation.objects.create(
                payment=payment,
                invoice=invoice,
                amount=amount
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
            
            total_amount += quantity * invoice_item.unit_price
            
            # Add stock back
            if invoice_item.product.track_stock:
                InventoryService.add_stock(
                    product_id=invoice_item.product_id,
                    warehouse_id=invoice.warehouse_id,
                    quantity=quantity,
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
        """Get customer account statement."""
        
        customer = Customer.objects.get(id=customer_id)
        
        # Get invoices
        invoices = Invoice.objects.filter(
            customer_id=customer_id,
            status__in=[Invoice.Status.CONFIRMED, Invoice.Status.PAID, Invoice.Status.PARTIAL]
        )
        
        # Get payments
        payments = Payment.objects.filter(customer_id=customer_id)
        
        # Get returns
        returns = SalesReturn.objects.filter(
            original_invoice__customer_id=customer_id
        )
        
        if start_date:
            invoices = invoices.filter(invoice_date__gte=start_date)
            payments = payments.filter(payment_date__gte=start_date)
            returns = returns.filter(return_date__gte=start_date)
        
        if end_date:
            invoices = invoices.filter(invoice_date__lte=end_date)
            payments = payments.filter(payment_date__lte=end_date)
            returns = returns.filter(return_date__lte=end_date)
        
        # Build transactions list
        transactions = []
        
        for inv in invoices:
            transactions.append({
                'date': inv.invoice_date,
                'type': 'invoice',
                'reference': inv.invoice_number,
                'debit': inv.total_amount,
                'credit': Decimal('0.00'),
                'description': f'فاتورة رقم {inv.invoice_number}'
            })
        
        for payment in payments:
            transactions.append({
                'date': payment.payment_date,
                'type': 'payment',
                'reference': payment.payment_number,
                'debit': Decimal('0.00'),
                'credit': payment.amount,
                'description': f'سند قبض رقم {payment.payment_number}'
            })
        
        for ret in returns:
            transactions.append({
                'date': ret.return_date,
                'type': 'return',
                'reference': ret.return_number,
                'debit': Decimal('0.00'),
                'credit': ret.total_amount,
                'description': f'مرتجع رقم {ret.return_number}'
            })
        
        # Sort by date
        transactions.sort(key=lambda x: x['date'])
        
        # Calculate running balance
        balance = customer.opening_balance
        for t in transactions:
            balance = balance + t['debit'] - t['credit']
            t['balance'] = balance
        
        return {
            'customer': {
                'id': customer.id,
                'name': customer.name,
                'code': customer.code
            },
            'opening_balance': customer.opening_balance,
            'closing_balance': customer.current_balance,
            'total_invoices': sum(t['debit'] for t in transactions),
            'total_payments': sum(t['credit'] for t in transactions if t['type'] == 'payment'),
            'total_returns': sum(t['credit'] for t in transactions if t['type'] == 'return'),
            'transactions': transactions
        }

    @staticmethod
    @handle_service_error
    def get_invoice_profit(invoice_id: int) -> Dict[str, Any]:
        """Calculate profit for an invoice."""
        
        invoice = Invoice.objects.get(id=invoice_id)
        items = invoice.items.all()
        
        total_revenue = sum(item.total for item in items)
        total_cost = sum(item.cost_price * item.quantity for item in items)
        gross_profit = total_revenue - total_cost
        profit_margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else Decimal('0')
        
        return {
            'invoice_number': invoice.invoice_number,
            'total_revenue': total_revenue,
            'total_cost': total_cost,
            'gross_profit': gross_profit,
            'profit_margin': profit_margin,
            'items': [
                {
                    'product': item.product.name,
                    'quantity': item.quantity,
                    'revenue': item.total,
                    'cost': item.cost_price * item.quantity,
                    'profit': item.profit
                }
                for item in items
            ]
        }
