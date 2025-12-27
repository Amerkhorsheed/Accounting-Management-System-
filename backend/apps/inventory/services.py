"""
Inventory Services - Business Logic Layer
"""
from decimal import Decimal
from typing import List, Optional, Dict, Any
from django.db import transaction
from django.db.models import Sum, F, Q
from apps.core.exceptions import (
    InsufficientStockException, 
    NotFoundException, 
    ValidationException
)
from apps.core.decorators import handle_service_error
from .models import Product, Stock, StockMovement, Warehouse, Category


class InventoryService:
    """
    Service class for inventory management operations.
    Implements business logic for stock operations.
    """

    @staticmethod
    @handle_service_error
    def get_product_by_barcode(barcode: str) -> Optional[Product]:
        """
        Find a product by its barcode.
        
        Args:
            barcode: The barcode to search for
            
        Returns:
            Product instance or None
        """
        try:
            return Product.objects.select_related('category', 'unit').get(
                barcode=barcode, 
                is_active=True, 
                is_deleted=False
            )
        except Product.DoesNotExist:
            return None

    @staticmethod
    @handle_service_error
    def get_product_stock(product_id: int, warehouse_id: int = None) -> Dict[str, Any]:
        """
        Get stock information for a product.
        
        Args:
            product_id: Product ID
            warehouse_id: Optional warehouse ID for specific warehouse
            
        Returns:
            Dictionary with stock information
        """
        stocks = Stock.objects.filter(product_id=product_id)
        
        if warehouse_id:
            stocks = stocks.filter(warehouse_id=warehouse_id)
        
        stocks = stocks.select_related('warehouse')
        
        total_quantity = Decimal('0')
        total_reserved = Decimal('0')
        by_warehouse = []
        
        for stock in stocks:
            total_quantity += stock.quantity
            total_reserved += stock.reserved_quantity
            by_warehouse.append({
                'warehouse_id': stock.warehouse_id,
                'warehouse_name': stock.warehouse.name,
                'quantity': stock.quantity,
                'reserved': stock.reserved_quantity,
                'available': stock.available_quantity
            })
        
        return {
            'product_id': product_id,
            'total_quantity': total_quantity,
            'total_reserved': total_reserved,
            'total_available': total_quantity - total_reserved,
            'by_warehouse': by_warehouse
        }

    @staticmethod
    @handle_service_error
    @transaction.atomic
    def adjust_stock(
        product_id: int,
        warehouse_id: int,
        quantity: Decimal,
        adjustment_type: str,
        reason: str,
        user=None,
        notes: str = None
    ) -> Stock:
        """
        Adjust stock level for a product in a warehouse.
        
        Args:
            product_id: Product ID
            warehouse_id: Warehouse ID
            quantity: Quantity to adjust
            adjustment_type: 'add', 'subtract', or 'set'
            reason: Reason for adjustment
            user: User performing the adjustment
            notes: Optional notes
            
        Returns:
            Updated Stock instance
        """
        # Get or create stock record
        stock, created = Stock.objects.get_or_create(
            product_id=product_id,
            warehouse_id=warehouse_id,
            defaults={'quantity': Decimal('0')}
        )
        
        balance_before = stock.quantity
        
        # Calculate new quantity
        if adjustment_type == 'add':
            stock.quantity += quantity
            movement_type = StockMovement.MovementType.IN
        elif adjustment_type == 'subtract':
            if stock.quantity < quantity:
                product = Product.objects.get(id=product_id)
                raise InsufficientStockException(
                    product.name, 
                    int(quantity), 
                    int(stock.quantity)
                )
            stock.quantity -= quantity
            movement_type = StockMovement.MovementType.OUT
        elif adjustment_type == 'set':
            stock.quantity = quantity
            movement_type = StockMovement.MovementType.ADJUSTMENT
        else:
            raise ValidationException(f'نوع التعديل غير صالح: {adjustment_type}')
        
        stock.save()
        
        # Create movement record
        StockMovement.objects.create(
            product_id=product_id,
            warehouse_id=warehouse_id,
            movement_type=movement_type,
            source_type=StockMovement.SourceType.ADJUSTMENT,
            quantity=quantity,
            balance_before=balance_before,
            balance_after=stock.quantity,
            notes=f"{reason}\n{notes}" if notes else reason,
            created_by=user
        )
        
        return stock

    @staticmethod
    @handle_service_error
    @transaction.atomic
    def add_stock(
        product_id: int,
        warehouse_id: int,
        quantity: Decimal,
        unit_cost: Decimal,
        source_type: str,
        reference_number: str = None,
        reference_type: str = None,
        reference_id: int = None,
        user=None,
        notes: str = None
    ) -> Stock:
        """
        Add stock from purchase or other source.
        
        Args:
            product_id: Product ID
            warehouse_id: Warehouse ID
            quantity: Quantity to add
            unit_cost: Cost per unit
            source_type: Source of stock (purchase, return, etc.)
            reference_number: Reference document number
            reference_type: Type of reference document
            reference_id: ID of reference document
            user: User performing the operation
            notes: Optional notes
            
        Returns:
            Updated Stock instance
        """
        stock, created = Stock.objects.get_or_create(
            product_id=product_id,
            warehouse_id=warehouse_id,
            defaults={'quantity': Decimal('0')}
        )
        
        balance_before = stock.quantity
        stock.quantity += quantity
        stock.save()
        
        # Create movement record
        StockMovement.objects.create(
            product_id=product_id,
            warehouse_id=warehouse_id,
            movement_type=StockMovement.MovementType.IN,
            source_type=source_type,
            quantity=quantity,
            unit_cost=unit_cost,
            reference_number=reference_number,
            reference_type=reference_type,
            reference_id=reference_id,
            balance_before=balance_before,
            balance_after=stock.quantity,
            notes=notes,
            created_by=user
        )
        
        return stock

    @staticmethod
    @handle_service_error
    @transaction.atomic
    def deduct_stock(
        product_id: int,
        warehouse_id: int,
        quantity: Decimal,
        source_type: str,
        reference_number: str = None,
        reference_type: str = None,
        reference_id: int = None,
        user=None,
        notes: str = None
    ) -> Stock:
        """
        Deduct stock for sale or other purpose.
        
        Args:
            product_id: Product ID
            warehouse_id: Warehouse ID
            quantity: Quantity to deduct
            source_type: Source of deduction (sale, damage, etc.)
            reference_number: Reference document number
            reference_type: Type of reference document
            reference_id: ID of reference document
            user: User performing the operation
            notes: Optional notes
            
        Returns:
            Updated Stock instance
            
        Raises:
            InsufficientStockException: If stock is insufficient
        """
        try:
            stock = Stock.objects.get(
                product_id=product_id, 
                warehouse_id=warehouse_id
            )
        except Stock.DoesNotExist:
            product = Product.objects.get(id=product_id)
            raise InsufficientStockException(product.name, int(quantity), 0)
        
        if stock.available_quantity < quantity:
            product = Product.objects.get(id=product_id)
            raise InsufficientStockException(
                product.name, 
                int(quantity), 
                int(stock.available_quantity)
            )
        
        balance_before = stock.quantity
        stock.quantity -= quantity
        stock.save()
        
        # Create movement record
        StockMovement.objects.create(
            product_id=product_id,
            warehouse_id=warehouse_id,
            movement_type=StockMovement.MovementType.OUT,
            source_type=source_type,
            quantity=quantity,
            reference_number=reference_number,
            reference_type=reference_type,
            reference_id=reference_id,
            balance_before=balance_before,
            balance_after=stock.quantity,
            notes=notes,
            created_by=user
        )
        
        return stock

    @staticmethod
    @handle_service_error
    def get_low_stock_products(warehouse_id: int = None) -> List[Dict[str, Any]]:
        """
        Get products with stock below minimum level.
        
        Args:
            warehouse_id: Optional warehouse filter
            
        Returns:
            List of products with low stock
        """
        stocks = Stock.objects.select_related('product', 'warehouse').filter(
            quantity__lte=F('product__minimum_stock'),
            product__is_active=True,
            product__is_deleted=False,
            product__track_stock=True
        )
        
        if warehouse_id:
            stocks = stocks.filter(warehouse_id=warehouse_id)
        
        return [
            {
                'product_id': s.product_id,
                'product_code': s.product.code,
                'product_name': s.product.name,
                'warehouse_id': s.warehouse_id,
                'warehouse_name': s.warehouse.name,
                'current_stock': s.quantity,
                'minimum_stock': s.product.minimum_stock,
                'reorder_point': s.product.reorder_point
            }
            for s in stocks
        ]

    @staticmethod
    @handle_service_error
    def get_stock_valuation(warehouse_id: int = None, method: str = 'average') -> Dict[str, Any]:
        """
        Calculate total stock valuation.
        
        Args:
            warehouse_id: Optional warehouse filter
            method: Valuation method ('average', 'fifo', 'lifo')
            
        Returns:
            Dictionary with valuation information
        """
        stocks = Stock.objects.select_related('product').filter(
            product__is_active=True,
            product__is_deleted=False
        )
        
        if warehouse_id:
            stocks = stocks.filter(warehouse_id=warehouse_id)
        
        total_value = Decimal('0')
        items = []
        
        for stock in stocks:
            # Using average cost (cost_price) for simplicity
            # FIFO/LIFO would require tracking lot-level costs
            item_value = stock.quantity * stock.product.cost_price
            total_value += item_value
            
            items.append({
                'product_id': stock.product_id,
                'product_name': stock.product.name,
                'quantity': stock.quantity,
                'unit_cost': stock.product.cost_price,
                'total_value': item_value
            })
        
        return {
            'total_value': total_value,
            'item_count': len(items),
            'method': method,
            'items': items
        }

    @staticmethod
    @handle_service_error
    def reserve_stock(product_id: int, warehouse_id: int, quantity: Decimal) -> bool:
        """
        Reserve stock for a pending order.
        
        Args:
            product_id: Product ID
            warehouse_id: Warehouse ID
            quantity: Quantity to reserve
            
        Returns:
            True if reservation successful
            
        Raises:
            InsufficientStockException: If not enough available stock
        """
        try:
            stock = Stock.objects.get(
                product_id=product_id, 
                warehouse_id=warehouse_id
            )
        except Stock.DoesNotExist:
            product = Product.objects.get(id=product_id)
            raise InsufficientStockException(product.name, int(quantity), 0)
        
        if stock.available_quantity < quantity:
            product = Product.objects.get(id=product_id)
            raise InsufficientStockException(
                product.name, 
                int(quantity), 
                int(stock.available_quantity)
            )
        
        stock.reserved_quantity += quantity
        stock.save()
        return True

    @staticmethod
    @handle_service_error
    def release_reserved_stock(product_id: int, warehouse_id: int, quantity: Decimal) -> bool:
        """
        Release previously reserved stock.
        
        Args:
            product_id: Product ID
            warehouse_id: Warehouse ID
            quantity: Quantity to release
            
        Returns:
            True if release successful
        """
        try:
            stock = Stock.objects.get(
                product_id=product_id, 
                warehouse_id=warehouse_id
            )
            stock.reserved_quantity = max(
                Decimal('0'), 
                stock.reserved_quantity - quantity
            )
            stock.save()
            return True
        except Stock.DoesNotExist:
            return False
