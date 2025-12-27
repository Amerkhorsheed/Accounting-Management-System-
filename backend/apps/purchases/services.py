"""
Purchases Services - Business Logic
"""
from decimal import Decimal
from typing import List, Dict, Any
from django.db import transaction
from django.utils import timezone
from apps.core.exceptions import ValidationException, InvalidOperationException
from apps.core.decorators import handle_service_error
from apps.inventory.services import InventoryService
from apps.inventory.models import StockMovement
from .models import (
    Supplier, PurchaseOrder, PurchaseOrderItem,
    GoodsReceivedNote, GRNItem, SupplierPayment
)


class PurchaseService:
    """Service class for purchase operations."""

    @staticmethod
    @handle_service_error
    @transaction.atomic
    def create_purchase_order(
        supplier_id: int,
        warehouse_id: int,
        order_date,
        items: List[Dict],
        discount_amount: Decimal = Decimal('0.00'),
        expected_date=None,
        reference: str = None,
        notes: str = None,
        user=None
    ) -> PurchaseOrder:
        """
        Create a new purchase order.
        
        Requirements: 4.4, 4.6
        
        For each item:
        - Accepts optional product_unit_id for unit selection
        - Calculates base_quantity using conversion factor from product_unit
        - If no product_unit specified, defaults to product's base unit
        """
        from apps.inventory.models import ProductUnit
        
        purchase_order = PurchaseOrder.objects.create(
            supplier_id=supplier_id,
            warehouse_id=warehouse_id,
            order_date=order_date,
            expected_date=expected_date,
            discount_amount=discount_amount,
            reference=reference,
            notes=notes,
            status=PurchaseOrder.Status.DRAFT,
            created_by=user
        )
        
        for item in items:
            product_id = item['product_id']
            quantity = Decimal(str(item['quantity']))
            product_unit_id = item.get('product_unit_id')
            product_unit = None
            
            # Get product_unit if specified
            if product_unit_id:
                product_unit = ProductUnit.objects.get(id=product_unit_id)
                base_quantity = product_unit.convert_to_base(quantity)
            else:
                # Default to base unit - find the base unit for this product
                base_unit = ProductUnit.objects.filter(
                    product_id=product_id,
                    is_base_unit=True,
                    is_deleted=False
                ).first()
                
                if base_unit:
                    base_quantity = base_unit.convert_to_base(quantity)
                else:
                    # No ProductUnit configured, use quantity as-is (legacy behavior)
                    base_quantity = quantity
            
            PurchaseOrderItem.objects.create(
                purchase_order=purchase_order,
                product_id=product_id,
                product_unit=product_unit,
                quantity=quantity,
                base_quantity=base_quantity,
                unit_price=item['unit_price'],
                discount_percent=item.get('discount_percent', Decimal('0.00')),
                tax_rate=item.get('tax_rate', Decimal('15.00')),
                notes=item.get('notes'),
                created_by=user
            )
        
        purchase_order.calculate_totals()
        return purchase_order

    @staticmethod
    @handle_service_error
    @transaction.atomic
    def approve_purchase_order(po_id: int, user=None) -> PurchaseOrder:
        """Approve a purchase order."""
        
        purchase_order = PurchaseOrder.objects.get(id=po_id)
        
        if purchase_order.status != PurchaseOrder.Status.DRAFT:
            raise InvalidOperationException(
                'اعتماد أمر الشراء',
                'لا يمكن اعتماد أمر شراء غير مسودة'
            )
        
        purchase_order.status = PurchaseOrder.Status.APPROVED
        purchase_order.approved_by = user
        purchase_order.approved_at = timezone.now()
        purchase_order.save()
        
        return purchase_order

    @staticmethod
    @handle_service_error
    @transaction.atomic
    def receive_goods(
        po_id: int,
        received_date,
        items: List[Dict],
        supplier_invoice_no: str = None,
        notes: str = None,
        user=None
    ) -> GoodsReceivedNote:
        """
        Receive goods against a purchase order.
        
        Requirements: 4.4, 4.6
        
        For each item:
        - Calculates base_quantity using conversion factor from product_unit
        - If no product_unit specified, defaults to product's base unit
        - Uses base_quantity for stock addition
        """
        from apps.inventory.models import ProductUnit
        
        purchase_order = PurchaseOrder.objects.get(id=po_id)
        
        if purchase_order.status not in [
            PurchaseOrder.Status.APPROVED,
            PurchaseOrder.Status.ORDERED,
            PurchaseOrder.Status.PARTIAL
        ]:
            raise InvalidOperationException(
                'استلام البضاعة',
                'لا يمكن استلام بضاعة لأمر شراء غير معتمد'
            )
        
        # Validate items are provided
        if not items:
            raise ValidationException('يجب تحديد بنود للاستلام')
        
        # Create GRN
        grn = GoodsReceivedNote.objects.create(
            purchase_order=purchase_order,
            received_date=received_date,
            supplier_invoice_no=supplier_invoice_no,
            notes=notes,
            received_by=user,
            created_by=user
        )
        
        total_received_value = Decimal('0')
        
        for item_data in items:
            po_item = PurchaseOrderItem.objects.get(id=item_data['po_item_id'])
            quantity = Decimal(str(item_data['quantity']))
            
            # Validate quantity doesn't exceed remaining
            if quantity > po_item.remaining_quantity:
                raise ValidationException(
                    f'الكمية المستلمة ({quantity}) تتجاوز الكمية المتبقية ({po_item.remaining_quantity}) للمنتج {po_item.product.name}'
                )
            
            # Calculate base_quantity based on product_unit or default to base unit
            # Requirements: 4.4, 4.6
            if po_item.product_unit:
                # Use the conversion factor from the specified product_unit
                base_quantity = po_item.product_unit.convert_to_base(quantity)
            else:
                # Default to base unit - find the base unit for this product
                base_unit = ProductUnit.objects.filter(
                    product=po_item.product,
                    is_base_unit=True,
                    is_deleted=False
                ).first()
                
                if base_unit:
                    # Use base unit conversion (should be 1.0)
                    base_quantity = base_unit.convert_to_base(quantity)
                else:
                    # No ProductUnit configured, use quantity as-is (legacy behavior)
                    base_quantity = quantity
            
            # Create GRN item
            GRNItem.objects.create(
                grn=grn,
                po_item=po_item,
                product=po_item.product,
                quantity_received=quantity,
                notes=item_data.get('notes'),
                created_by=user
            )
            
            # Update received quantity on PO item
            po_item.received_quantity += quantity
            po_item.save()
            
            # Calculate value for supplier balance update
            total_received_value += quantity * po_item.unit_price
            
            # Add stock using base_quantity
            InventoryService.add_stock(
                product_id=po_item.product_id,
                warehouse_id=purchase_order.warehouse_id,
                quantity=base_quantity,  # Use base_quantity for stock addition
                unit_cost=po_item.unit_price,
                source_type=StockMovement.SourceType.PURCHASE,
                reference_number=grn.grn_number,
                reference_type='GRN',
                reference_id=grn.id,
                user=user,
                notes=f"استلام من أمر الشراء {purchase_order.order_number}"
            )
        
        # Check if all items are fully received
        all_received = all(
            item.remaining_quantity <= 0 
            for item in purchase_order.items.all()
        )
        
        # Update PO status
        if all_received:
            purchase_order.status = PurchaseOrder.Status.RECEIVED
        else:
            purchase_order.status = PurchaseOrder.Status.PARTIAL
        
        purchase_order.save()
        
        # Update supplier balance (increase what we owe them)
        supplier = purchase_order.supplier
        supplier.current_balance += total_received_value
        supplier.save()
        
        return grn

    @staticmethod
    @handle_service_error
    @transaction.atomic
    def make_supplier_payment(
        supplier_id: int,
        payment_date,
        amount: Decimal,
        payment_method: str,
        purchase_order_id: int = None,
        reference: str = None,
        notes: str = None,
        user=None
    ) -> SupplierPayment:
        """Record a payment to supplier."""
        
        payment = SupplierPayment.objects.create(
            supplier_id=supplier_id,
            purchase_order_id=purchase_order_id,
            payment_date=payment_date,
            amount=amount,
            payment_method=payment_method,
            reference=reference,
            notes=notes,
            created_by=user
        )
        
        # Update supplier balance
        supplier = Supplier.objects.get(id=supplier_id)
        supplier.current_balance -= amount
        supplier.save()
        
        # Update PO paid amount if applicable
        if purchase_order_id:
            purchase_order = PurchaseOrder.objects.get(id=purchase_order_id)
            purchase_order.paid_amount += amount
            purchase_order.save()
        
        return payment

    @staticmethod
    @handle_service_error
    def get_supplier_statement(
        supplier_id: int,
        start_date=None,
        end_date=None
    ) -> Dict[str, Any]:
        """Get supplier account statement."""
        
        supplier = Supplier.objects.get(id=supplier_id)
        
        # Get purchase orders
        orders = PurchaseOrder.objects.filter(
            supplier_id=supplier_id,
            status=PurchaseOrder.Status.RECEIVED
        )
        
        # Get payments
        payments = SupplierPayment.objects.filter(supplier_id=supplier_id)
        
        if start_date:
            orders = orders.filter(order_date__gte=start_date)
            payments = payments.filter(payment_date__gte=start_date)
        
        if end_date:
            orders = orders.filter(order_date__lte=end_date)
            payments = payments.filter(payment_date__lte=end_date)
        
        # Build transactions list
        transactions = []
        
        for order in orders:
            transactions.append({
                'date': order.order_date,
                'type': 'purchase',
                'reference': order.order_number,
                'debit': order.total_amount,
                'credit': Decimal('0.00'),
                'description': f'أمر شراء رقم {order.order_number}'
            })
        
        for payment in payments:
            transactions.append({
                'date': payment.payment_date,
                'type': 'payment',
                'reference': payment.payment_number,
                'debit': Decimal('0.00'),
                'credit': payment.amount,
                'description': f'دفعة رقم {payment.payment_number}'
            })
        
        # Sort by date
        transactions.sort(key=lambda x: x['date'])
        
        # Calculate running balance
        balance = supplier.opening_balance
        for t in transactions:
            balance = balance + t['debit'] - t['credit']
            t['balance'] = balance
        
        return {
            'supplier': {
                'id': supplier.id,
                'name': supplier.name,
                'code': supplier.code
            },
            'opening_balance': supplier.opening_balance,
            'closing_balance': supplier.current_balance,
            'total_purchases': sum(t['debit'] for t in transactions),
            'total_payments': sum(t['credit'] for t in transactions),
            'transactions': transactions
        }
