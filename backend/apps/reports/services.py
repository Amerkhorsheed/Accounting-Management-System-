"""
Reports Services - Business Intelligence and Analytics
"""
from decimal import Decimal
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from django.db.models import Sum, Count, Avg, F, Q, DecimalField, ExpressionWrapper
from django.db.models.functions import TruncDate, TruncMonth
from datetime import date, timedelta

from apps.sales.models import Invoice, InvoiceItem, Customer, Payment, SalesReturn
from apps.purchases.models import PurchaseOrder, Supplier
from apps.expenses.models import Expense
from apps.inventory.models import Product, Stock, StockMovement
from apps.core.decorators import handle_service_error


@dataclass
class StatementTransaction:
    """Represents a single transaction in a customer statement."""
    date: date
    type: str  # 'invoice', 'payment', 'return', 'opening'
    reference: str
    description: str
    debit: Decimal
    credit: Decimal
    balance: Decimal


@dataclass
class CustomerStatementData:
    """Complete customer statement data."""
    customer_id: int
    customer_name: str
    customer_code: str
    period_start: Optional[date]
    period_end: Optional[date]
    opening_balance: Decimal
    transactions: List[StatementTransaction]
    closing_balance: Decimal
    total_debit: Decimal
    total_credit: Decimal


class ReportService:
    """Service class for generating reports."""

    @staticmethod
    @handle_service_error
    def get_dashboard_summary(start_date: date = None, end_date: date = None) -> Dict[str, Any]:
        """Get dashboard summary statistics."""
        
        if not start_date:
            start_date = date.today().replace(day=1)
        if not end_date:
            end_date = date.today()
        
        # Sales
        sales = Invoice.objects.filter(
            status__in=[Invoice.Status.CONFIRMED, Invoice.Status.PAID, Invoice.Status.PARTIAL],
            invoice_date__gte=start_date,
            invoice_date__lte=end_date
        ).aggregate(
            total=Sum('total_amount'),
            count=Count('id')
        )
        
        # Purchases
        purchases = PurchaseOrder.objects.filter(
            status__in=[PurchaseOrder.Status.RECEIVED, PurchaseOrder.Status.PARTIAL],
            order_date__gte=start_date,
            order_date__lte=end_date
        ).aggregate(
            total=Sum('total_amount'),
            count=Count('id')
        )
        
        # Expenses
        expenses = Expense.objects.filter(
            is_approved=True,
            expense_date__gte=start_date,
            expense_date__lte=end_date
        ).aggregate(total=Sum('total_amount'))
        
        # Gross Profit from sales
        invoice_items = InvoiceItem.objects.filter(
            invoice__status__in=[Invoice.Status.CONFIRMED, Invoice.Status.PAID, Invoice.Status.PARTIAL],
            invoice__invoice_date__gte=start_date,
            invoice__invoice_date__lte=end_date
        )
        
        revenue = sum(item.total for item in invoice_items)
        cost = sum(item.cost_price * item.quantity for item in invoice_items)
        gross_profit = revenue - cost
        
        # Net profit (gross - expenses)
        expenses_total = expenses['total'] or Decimal('0')
        net_profit = gross_profit - expenses_total
        
        # Counts
        product_count = Product.objects.filter(is_active=True, is_deleted=False).count()
        customer_count = Customer.objects.filter(is_active=True, is_deleted=False).count()
        supplier_count = Supplier.objects.filter(is_active=True, is_deleted=False).count()
        
        # Low stock
        low_stock_count = Stock.objects.filter(
            quantity__lte=F('product__minimum_stock'),
            product__is_active=True,
            product__track_stock=True
        ).count()
        
        # Credit summary (Requirements: 8.1, 8.2, 8.3)
        # Total receivables - sum of all customer balances > 0
        receivables_total = Customer.objects.filter(
            is_active=True,
            is_deleted=False,
            current_balance__gt=0
        ).aggregate(total=Sum('current_balance'))['total'] or Decimal('0')
        
        # Customers with outstanding balance
        customers_with_balance = Customer.objects.filter(
            is_active=True,
            is_deleted=False,
            current_balance__gt=0
        ).count()
        
        # Total overdue amount - sum of remaining amounts on overdue invoices
        today = date.today()
        overdue_invoices = Invoice.objects.filter(
            invoice_type=Invoice.InvoiceType.CREDIT,
            status__in=[Invoice.Status.CONFIRMED, Invoice.Status.PARTIAL],
            due_date__lt=today
        )
        overdue_total = sum(inv.remaining_amount for inv in overdue_invoices)
        
        return {
            'period': {
                'start': start_date,
                'end': end_date
            },
            'sales': {
                'total': sales['total'] or Decimal('0'),
                'count': sales['count'] or 0
            },
            'purchases': {
                'total': purchases['total'] or Decimal('0'),
                'count': purchases['count'] or 0
            },
            'expenses': {
                'total': expenses_total
            },
            'profit': {
                'gross': gross_profit,
                'net': net_profit,
                'margin': (gross_profit / revenue * 100) if revenue > 0 else Decimal('0')
            },
            'counts': {
                'products': product_count,
                'customers': customer_count,
                'suppliers': supplier_count,
                'low_stock': low_stock_count
            },
            'credit': {
                'receivables_total': receivables_total,
                'customers_with_balance': customers_with_balance,
                'overdue_total': overdue_total
            },
            'top_products': list(InvoiceItem.objects.filter(
                invoice__status__in=[Invoice.Status.CONFIRMED, Invoice.Status.PAID, Invoice.Status.PARTIAL],
                invoice__invoice_date__gte=start_date,
                invoice__invoice_date__lte=end_date
            ).values('product__name').annotate(
                total_quantity=Sum('quantity'),
                total_value=Sum(ExpressionWrapper(F('quantity') * F('unit_price'), output_field=DecimalField()))
            ).order_by('-total_value')[:5]),
            'recent_activity': list(Invoice.objects.select_related('customer').order_by('-created_at')[:5].values(
                'id', 'invoice_number', 'customer__name', 'total_amount', 'created_at', 'status'
            ))
        }

    @staticmethod
    @handle_service_error
    def get_sales_report(start_date: date, end_date: date, group_by: str = 'day') -> Dict[str, Any]:
        """Get sales report with trend data."""
        
        invoices = Invoice.objects.filter(
            status__in=[Invoice.Status.CONFIRMED, Invoice.Status.PAID, Invoice.Status.PARTIAL],
            invoice_date__gte=start_date,
            invoice_date__lte=end_date
        )
        
        # Aggregate by period
        # Note: invoice_date is already a DateField, so we use it directly for day grouping
        # to avoid SQL Server compatibility issues with TruncDate on date fields
        if group_by == 'month':
            trend_data = invoices.annotate(
                period=TruncMonth('invoice_date')
            ).values('period').annotate(
                total=Sum('total_amount'),
                count=Count('id')
            ).order_by('period')
            trend = list(trend_data)
        else:
            # Group by invoice_date directly since it's already a DateField
            trend_data = invoices.values(
                'invoice_date'
            ).annotate(
                total=Sum('total_amount'),
                count=Count('id')
            ).order_by('invoice_date')
            # Normalize field name to 'period' for consistent API response
            trend = [
                {'period': item['invoice_date'], 'total': item['total'], 'count': item['count']}
                for item in trend_data
            ]
        
        # Top customers
        top_customers = Invoice.objects.filter(
            status__in=[Invoice.Status.CONFIRMED, Invoice.Status.PAID, Invoice.Status.PARTIAL],
            invoice_date__gte=start_date,
            invoice_date__lte=end_date
        ).values('customer__name').annotate(
            total=Sum('total_amount'),
            count=Count('id')
        ).order_by('-total')[:10]
        
        # Top products
        top_products = InvoiceItem.objects.filter(
            invoice__status__in=[Invoice.Status.CONFIRMED, Invoice.Status.PAID, Invoice.Status.PARTIAL],
            invoice__invoice_date__gte=start_date,
            invoice__invoice_date__lte=end_date
        ).values('product__name').annotate(
            total_quantity=Sum('quantity'),
            total_value=Sum(ExpressionWrapper(F('quantity') * F('unit_price'), output_field=DecimalField()))
        ).order_by('-total_value')[:10]
        
        # Summary
        summary = invoices.aggregate(
            total=Sum('total_amount'),
            count=Count('id'),
            avg=Avg('total_amount')
        )
        
        return {
            'period': {'start': start_date, 'end': end_date},
            'summary': {
                'total': summary['total'] or Decimal('0'),
                'count': summary['count'] or 0,
                'average': summary['avg'] or Decimal('0')
            },
            'trend': trend,
            'top_customers': list(top_customers),
            'top_products': list(top_products)
        }

    @staticmethod
    @handle_service_error
    def get_profit_report(start_date: date, end_date: date) -> Dict[str, Any]:
        """Get profit/loss report."""
        
        # Revenue from sales
        items = InvoiceItem.objects.filter(
            invoice__status__in=[Invoice.Status.CONFIRMED, Invoice.Status.PAID, Invoice.Status.PARTIAL],
            invoice__invoice_date__gte=start_date,
            invoice__invoice_date__lte=end_date
        )
        
        revenue = Decimal('0')
        cost_of_goods = Decimal('0')
        
        for item in items:
            revenue += item.total
            cost_of_goods += item.cost_price * item.quantity
        
        gross_profit = revenue - cost_of_goods
        
        # Expenses
        expenses_data = Expense.objects.filter(
            is_approved=True,
            expense_date__gte=start_date,
            expense_date__lte=end_date
        ).values('category__name').annotate(
            total=Sum('total_amount')
        ).order_by('-total')
        
        total_expenses = sum(e['total'] for e in expenses_data)
        
        # Net profit
        net_profit = gross_profit - total_expenses
        
        # By product category
        profit_by_category = InvoiceItem.objects.filter(
            invoice__status__in=[Invoice.Status.CONFIRMED, Invoice.Status.PAID, Invoice.Status.PARTIAL],
            invoice__invoice_date__gte=start_date,
            invoice__invoice_date__lte=end_date
        ).values('product__category__name').annotate(
            revenue=Sum(ExpressionWrapper(F('quantity') * F('unit_price'), output_field=DecimalField())),
            cost=Sum(ExpressionWrapper(F('quantity') * F('cost_price'), output_field=DecimalField()))
        ).order_by('-revenue')
        
        categories = []
        for cat in profit_by_category:
            profit = (cat['revenue'] or Decimal('0')) - (cat['cost'] or Decimal('0'))
            categories.append({
                'category': cat['product__category__name'] or 'بدون فئة',
                'revenue': cat['revenue'] or Decimal('0'),
                'cost': cat['cost'] or Decimal('0'),
                'profit': profit
            })
        
        return {
            'period': {'start': start_date, 'end': end_date},
            'revenue': revenue,
            'cost_of_goods': cost_of_goods,
            'gross_profit': gross_profit,
            'gross_margin': (gross_profit / revenue * 100) if revenue > 0 else Decimal('0'),
            'expenses': {
                'total': total_expenses,
                'by_category': list(expenses_data)
            },
            'net_profit': net_profit,
            'net_margin': (net_profit / revenue * 100) if revenue > 0 else Decimal('0'),
            'profit_by_category': categories
        }

    @staticmethod
    @handle_service_error
    def get_inventory_report() -> Dict[str, Any]:
        """Get inventory status report."""
        
        # Stock valuation
        stocks = Stock.objects.select_related('product', 'warehouse').filter(
            product__is_active=True,
            product__is_deleted=False
        )
        
        total_value = Decimal('0')
        items = []
        low_stock_items = []
        
        for stock in stocks:
            value = stock.quantity * stock.product.cost_price
            total_value += value
            
            item_data = {
                'product_id': stock.product_id,
                'product_code': stock.product.code,
                'product_name': stock.product.name,
                'warehouse': stock.warehouse.name,
                'quantity': stock.quantity,
                'unit_cost': stock.product.cost_price,
                'value': value
            }
            
            items.append(item_data)
            
            if stock.is_low_stock:
                low_stock_items.append({
                    **item_data,
                    'minimum': stock.product.minimum_stock,
                    'shortage': stock.product.minimum_stock - stock.quantity
                })
        
        # By category
        by_category = Product.objects.filter(
            is_active=True, is_deleted=False
        ).values('category__name').annotate(
            count=Count('id')
        ).order_by('-count')
        
        return {
            'total_value': total_value,
            'item_count': len(items),
            'low_stock_count': len(low_stock_items),
            'by_category': list(by_category),
            'low_stock_items': low_stock_items[:20]
        }

    @staticmethod
    @handle_service_error
    def get_customer_report(start_date: date, end_date: date) -> Dict[str, Any]:
        """Get customer analysis report."""
        
        customers = Customer.objects.filter(is_active=True, is_deleted=False).annotate(
            invoices_count=Count(
                'invoices',
                filter=Q(
                    invoices__status__in=[Invoice.Status.CONFIRMED, Invoice.Status.PAID, Invoice.Status.PARTIAL],
                    invoices__invoice_date__gte=start_date,
                    invoices__invoice_date__lte=end_date
                )
            ),
            invoices_total=Sum(
                'invoices__total_amount',
                filter=Q(
                    invoices__status__in=[Invoice.Status.CONFIRMED, Invoice.Status.PAID, Invoice.Status.PARTIAL],
                    invoices__invoice_date__gte=start_date,
                    invoices__invoice_date__lte=end_date
                )
            )
        ).order_by('-invoices_total')
        
        top_customers = [
            {
                'id': c.id,
                'code': c.code,
                'name': c.name,
                'invoices_count': c.invoices_count or 0,
                'invoices_total': c.invoices_total or Decimal('0'),
                'balance': c.current_balance
            }
            for c in customers[:20]
        ]
        
        # Summary
        total_customers = customers.count()
        active_customers = sum(1 for c in customers if c.invoices_count > 0)
        total_receivables = sum(c.current_balance for c in customers if c.current_balance > 0)
        
        return {
            'period': {'start': start_date, 'end': end_date},
            'summary': {
                'total_customers': total_customers,
                'active_customers': active_customers,
                'total_receivables': total_receivables
            },
            'top_customers': top_customers
        }

    @staticmethod
    @handle_service_error
    def get_customer_statement(
        customer_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> CustomerStatementData:
        """
        Get customer account statement with opening balance, transactions, and closing balance.
        
        Calculates running balance for each transaction.
        Supports date range filtering.
        
        Requirements: 3.1, 3.2, 3.3, 3.4, 3.6
        
        Args:
            customer_id: The customer's ID
            start_date: Optional start date for filtering (inclusive)
            end_date: Optional end date for filtering (inclusive)
            
        Returns:
            CustomerStatementData with opening_balance, transactions, closing_balance
        """
        customer = Customer.objects.get(id=customer_id)
        
        # Build list of all transactions (invoices, payments, returns)
        all_transactions = []
        
        # Get credit invoices (confirmed, paid, partial)
        invoice_filter = Q(
            customer_id=customer_id,
            invoice_type=Invoice.InvoiceType.CREDIT,
            status__in=[Invoice.Status.CONFIRMED, Invoice.Status.PAID, Invoice.Status.PARTIAL]
        )
        invoices = Invoice.objects.filter(invoice_filter).order_by('invoice_date', 'id')
        
        for inv in invoices:
            all_transactions.append({
                'date': inv.invoice_date,
                'type': 'invoice',
                'reference': inv.invoice_number,
                'description': f'فاتورة مبيعات - {inv.invoice_number}',
                'debit': inv.total_amount,
                'credit': Decimal('0.00'),
                'sort_key': (inv.invoice_date, 0, inv.id)  # invoices first within same date
            })
        
        # Get payments
        payments = Payment.objects.filter(customer_id=customer_id).order_by('payment_date', 'id')
        
        for pmt in payments:
            all_transactions.append({
                'date': pmt.payment_date,
                'type': 'payment',
                'reference': pmt.payment_number,
                'description': f'سند قبض - {pmt.payment_number}',
                'debit': Decimal('0.00'),
                'credit': pmt.amount,
                'sort_key': (pmt.payment_date, 1, pmt.id)  # payments after invoices within same date
            })
        
        # Get sales returns (reduce customer balance)
        returns = SalesReturn.objects.filter(
            original_invoice__customer_id=customer_id
        ).order_by('return_date', 'id')
        
        for ret in returns:
            all_transactions.append({
                'date': ret.return_date,
                'type': 'return',
                'reference': ret.return_number,
                'description': f'مرتجع مبيعات - {ret.return_number}',
                'debit': Decimal('0.00'),
                'credit': ret.total_amount,
                'sort_key': (ret.return_date, 2, ret.id)  # returns after payments within same date
            })
        
        # Sort all transactions by date, then type priority, then id
        all_transactions.sort(key=lambda x: x['sort_key'])
        
        # Calculate opening balance
        # Opening balance = customer.opening_balance + all transactions before start_date
        opening_balance = customer.opening_balance
        
        if start_date:
            # Calculate balance from transactions before start_date
            for txn in all_transactions:
                if txn['date'] < start_date:
                    opening_balance += txn['debit'] - txn['credit']
        
        # Filter transactions by date range
        filtered_transactions = []
        for txn in all_transactions:
            include = True
            if start_date and txn['date'] < start_date:
                include = False
            if end_date and txn['date'] > end_date:
                include = False
            if include:
                filtered_transactions.append(txn)
        
        # Calculate running balance for each transaction
        running_balance = opening_balance
        statement_transactions = []
        total_debit = Decimal('0.00')
        total_credit = Decimal('0.00')
        
        for txn in filtered_transactions:
            running_balance += txn['debit'] - txn['credit']
            total_debit += txn['debit']
            total_credit += txn['credit']
            
            statement_transactions.append(StatementTransaction(
                date=txn['date'],
                type=txn['type'],
                reference=txn['reference'],
                description=txn['description'],
                debit=txn['debit'],
                credit=txn['credit'],
                balance=running_balance
            ))
        
        closing_balance = running_balance
        
        return CustomerStatementData(
            customer_id=customer.id,
            customer_name=customer.name,
            customer_code=customer.code,
            period_start=start_date,
            period_end=end_date,
            opening_balance=opening_balance,
            transactions=statement_transactions,
            closing_balance=closing_balance,
            total_debit=total_debit,
            total_credit=total_credit
        )

    @staticmethod
    @handle_service_error
    def get_receivables_report(
        customer_type: Optional[str] = None,
        salesperson_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Generate receivables report with customer balances.
        
        Calculates total outstanding across customers.
        Lists customers sorted by balance descending.
        Includes unpaid/partial invoice counts.
        Supports filters (customer_type, salesperson).
        
        Requirements: 4.1, 4.2, 4.3, 4.4, 4.5
        
        Args:
            customer_type: Optional filter by customer type ('individual', 'company', 'government')
            salesperson_id: Optional filter by salesperson
            start_date: Optional filter for invoices created after this date
            end_date: Optional filter for invoices created before this date
            
        Returns:
            Dict with total_outstanding, customers list, and summary
        """
        # Build customer filter
        customer_filter = Q(is_active=True, is_deleted=False, current_balance__gt=0)
        
        if customer_type:
            customer_filter &= Q(customer_type=customer_type)
        
        if salesperson_id:
            customer_filter &= Q(salesperson_id=salesperson_id)
        
        # Get customers with outstanding balance
        customers = Customer.objects.filter(customer_filter).order_by('-current_balance')
        
        # Build invoice filter for counting
        invoice_base_filter = Q(
            invoice_type=Invoice.InvoiceType.CREDIT,
            status__in=[Invoice.Status.CONFIRMED, Invoice.Status.PARTIAL]
        )
        
        if start_date:
            invoice_base_filter &= Q(invoice_date__gte=start_date)
        if end_date:
            invoice_base_filter &= Q(invoice_date__lte=end_date)
        
        # Build customer list with invoice counts
        customer_list = []
        total_outstanding = Decimal('0.00')
        total_overdue = Decimal('0.00')
        today = date.today()
        
        for cust in customers:
            # Count unpaid and partial invoices for this customer
            cust_invoice_filter = invoice_base_filter & Q(customer=cust)
            
            unpaid_count = Invoice.objects.filter(
                cust_invoice_filter & Q(status=Invoice.Status.CONFIRMED)
            ).count()
            
            partial_count = Invoice.objects.filter(
                cust_invoice_filter & Q(status=Invoice.Status.PARTIAL)
            ).count()
            
            # Calculate overdue amount for this customer
            overdue_invoices = Invoice.objects.filter(
                cust_invoice_filter & Q(due_date__lt=today)
            )
            customer_overdue = sum(
                inv.remaining_amount for inv in overdue_invoices
            )
            
            customer_list.append({
                'id': cust.id,
                'code': cust.code,
                'name': cust.name,
                'customer_type': cust.customer_type,
                'current_balance': cust.current_balance,
                'credit_limit': cust.credit_limit,
                'available_credit': cust.available_credit,
                'unpaid_invoice_count': unpaid_count,
                'partial_invoice_count': partial_count,
                'total_invoice_count': unpaid_count + partial_count,
                'overdue_amount': customer_overdue,
                'salesperson': cust.salesperson.get_full_name() if cust.salesperson else None
            })
            
            total_outstanding += cust.current_balance
            total_overdue += customer_overdue
        
        return {
            'generated_at': date.today(),
            'filters': {
                'customer_type': customer_type,
                'salesperson_id': salesperson_id,
                'start_date': start_date,
                'end_date': end_date
            },
            'summary': {
                'total_outstanding': total_outstanding,
                'total_overdue': total_overdue,
                'customer_count': len(customer_list),
                'total_unpaid_invoices': sum(c['unpaid_invoice_count'] for c in customer_list),
                'total_partial_invoices': sum(c['partial_invoice_count'] for c in customer_list)
            },
            'customers': customer_list
        }

    @staticmethod
    @handle_service_error
    def get_aging_report(as_of_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Generate aging report categorized by overdue periods.
        
        Categorizes by age buckets: current, 1-30, 31-60, 61-90, >90 days.
        Calculates totals per category.
        Includes invoice details per category.
        
        Requirements: 5.1, 5.2, 5.3
        
        Args:
            as_of_date: The date to calculate aging from (defaults to today)
            
        Returns:
            Dict with aging buckets, totals, and invoice details
        """
        if as_of_date is None:
            as_of_date = date.today()
        
        # Get all unpaid/partial credit invoices
        invoices = Invoice.objects.filter(
            invoice_type=Invoice.InvoiceType.CREDIT,
            status__in=[Invoice.Status.CONFIRMED, Invoice.Status.PARTIAL]
        ).select_related('customer').order_by('due_date', 'invoice_date')
        
        # Initialize aging buckets
        buckets = {
            'current': {
                'label': 'جاري (غير مستحق)',
                'min_days': None,
                'max_days': 0,
                'total': Decimal('0.00'),
                'invoice_count': 0,
                'invoices': []
            },
            '1_30': {
                'label': '1-30 يوم',
                'min_days': 1,
                'max_days': 30,
                'total': Decimal('0.00'),
                'invoice_count': 0,
                'invoices': []
            },
            '31_60': {
                'label': '31-60 يوم',
                'min_days': 31,
                'max_days': 60,
                'total': Decimal('0.00'),
                'invoice_count': 0,
                'invoices': []
            },
            '61_90': {
                'label': '61-90 يوم',
                'min_days': 61,
                'max_days': 90,
                'total': Decimal('0.00'),
                'invoice_count': 0,
                'invoices': []
            },
            'over_90': {
                'label': 'أكثر من 90 يوم',
                'min_days': 91,
                'max_days': None,
                'total': Decimal('0.00'),
                'invoice_count': 0,
                'invoices': []
            }
        }
        
        total_outstanding = Decimal('0.00')
        
        for inv in invoices:
            remaining = inv.remaining_amount
            if remaining <= 0:
                continue
            
            # Calculate days overdue
            # If no due_date, use invoice_date as reference
            reference_date = inv.due_date or inv.invoice_date
            days_overdue = (as_of_date - reference_date).days
            
            # Determine bucket
            if days_overdue <= 0:
                bucket_key = 'current'
            elif days_overdue <= 30:
                bucket_key = '1_30'
            elif days_overdue <= 60:
                bucket_key = '31_60'
            elif days_overdue <= 90:
                bucket_key = '61_90'
            else:
                bucket_key = 'over_90'
            
            invoice_data = {
                'id': inv.id,
                'invoice_number': inv.invoice_number,
                'invoice_date': inv.invoice_date,
                'due_date': inv.due_date,
                'customer_id': inv.customer.id,
                'customer_name': inv.customer.name,
                'customer_code': inv.customer.code,
                'total_amount': inv.total_amount,
                'paid_amount': inv.paid_amount,
                'remaining_amount': remaining,
                'days_overdue': max(0, days_overdue)
            }
            
            buckets[bucket_key]['invoices'].append(invoice_data)
            buckets[bucket_key]['total'] += remaining
            buckets[bucket_key]['invoice_count'] += 1
            total_outstanding += remaining
        
        # Build summary by customer
        customer_summary = {}
        for bucket_key, bucket_data in buckets.items():
            for inv in bucket_data['invoices']:
                cust_id = inv['customer_id']
                if cust_id not in customer_summary:
                    customer_summary[cust_id] = {
                        'customer_id': cust_id,
                        'customer_name': inv['customer_name'],
                        'customer_code': inv['customer_code'],
                        'current': Decimal('0.00'),
                        '1_30': Decimal('0.00'),
                        '31_60': Decimal('0.00'),
                        '61_90': Decimal('0.00'),
                        'over_90': Decimal('0.00'),
                        'total': Decimal('0.00')
                    }
                customer_summary[cust_id][bucket_key] += inv['remaining_amount']
                customer_summary[cust_id]['total'] += inv['remaining_amount']
        
        # Sort customer summary by total descending
        customer_breakdown = sorted(
            customer_summary.values(),
            key=lambda x: x['total'],
            reverse=True
        )
        
        return {
            'as_of_date': as_of_date,
            'summary': {
                'total_outstanding': total_outstanding,
                'total_current': buckets['current']['total'],
                'total_overdue': total_outstanding - buckets['current']['total'],
                'total_severely_overdue': buckets['61_90']['total'] + buckets['over_90']['total']
            },
            'buckets': {
                key: {
                    'label': data['label'],
                    'total': data['total'],
                    'invoice_count': data['invoice_count'],
                    'invoices': data['invoices']
                }
                for key, data in buckets.items()
            },
            'customer_breakdown': customer_breakdown
        }

    @staticmethod
    @handle_service_error
    def get_suppliers_report(
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Generate suppliers report with purchase statistics and payment status.
        
        Calculates total suppliers, active suppliers, total payables.
        Lists suppliers sorted by total purchase amount descending.
        Includes purchase totals and outstanding balances.
        Supports date range filtering for purchase calculations.
        
        Requirements: 1.2, 1.3, 1.4, 1.5, 1.6
        
        Args:
            start_date: Optional start date for filtering purchases (inclusive)
            end_date: Optional end date for filtering purchases (inclusive)
            
        Returns:
            Dict with generated_at, period, summary, and suppliers list
        """
        from apps.purchases.models import Supplier, PurchaseOrder, SupplierPayment
        
        # Get all active suppliers
        suppliers = Supplier.objects.filter(is_active=True, is_deleted=False)
        
        # Build purchase order filter for date range
        po_filter = Q(
            status__in=[PurchaseOrder.Status.RECEIVED, PurchaseOrder.Status.PARTIAL, 
                       PurchaseOrder.Status.APPROVED, PurchaseOrder.Status.ORDERED]
        )
        
        if start_date:
            po_filter &= Q(order_date__gte=start_date)
        if end_date:
            po_filter &= Q(order_date__lte=end_date)
        
        # Build payment filter for date range
        payment_filter = Q()
        if start_date:
            payment_filter &= Q(payment_date__gte=start_date)
        if end_date:
            payment_filter &= Q(payment_date__lte=end_date)
        
        # Build supplier list with purchase totals
        supplier_list = []
        total_payables = Decimal('0.00')
        total_purchases = Decimal('0.00')
        active_suppliers = 0
        
        for supplier in suppliers:
            # Get purchase orders for this supplier within date range
            supplier_po_filter = po_filter & Q(supplier=supplier)
            purchase_orders = PurchaseOrder.objects.filter(supplier_po_filter)
            
            # Calculate total purchases
            supplier_total_purchases = purchase_orders.aggregate(
                total=Sum('total_amount')
            )['total'] or Decimal('0.00')
            
            # Get purchase order count
            po_count = purchase_orders.count()
            
            # Get last purchase date
            last_po = purchase_orders.order_by('-order_date').first()
            last_purchase_date = last_po.order_date if last_po else None
            
            # Get payments for this supplier within date range
            supplier_payment_filter = payment_filter & Q(supplier=supplier)
            if payment_filter:
                payments = SupplierPayment.objects.filter(supplier_payment_filter)
            else:
                payments = SupplierPayment.objects.filter(supplier=supplier)
            
            supplier_total_payments = payments.aggregate(
                total=Sum('amount')
            )['total'] or Decimal('0.00')
            
            # Outstanding balance is the supplier's current_balance (from model)
            # This represents the actual outstanding amount owed to the supplier
            outstanding_balance = supplier.current_balance
            
            # Track if supplier is active (has purchases in period)
            if po_count > 0:
                active_suppliers += 1
            
            supplier_list.append({
                'id': supplier.id,
                'code': supplier.code,
                'name': supplier.name,
                'total_purchases': supplier_total_purchases,
                'total_payments': supplier_total_payments,
                'outstanding_balance': outstanding_balance,
                'purchase_order_count': po_count,
                'last_purchase_date': last_purchase_date
            })
            
            total_purchases += supplier_total_purchases
            # Sum outstanding balances for total payables
            if outstanding_balance > 0:
                total_payables += outstanding_balance
        
        # Sort suppliers by total_purchases descending (Requirement 1.3)
        supplier_list.sort(key=lambda x: x['total_purchases'], reverse=True)
        
        return {
            'generated_at': date.today(),
            'period': {
                'start': start_date,
                'end': end_date
            },
            'summary': {
                'total_suppliers': len(supplier_list),
                'active_suppliers': active_suppliers,
                'total_payables': total_payables,
                'total_purchases': total_purchases
            },
            'suppliers': supplier_list
        }

    @staticmethod
    @handle_service_error
    def get_expenses_report(
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        category_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate expenses report with category breakdown and expense details.
        
        Calculates total expenses and average expense amount.
        Builds category breakdown with amounts and percentages.
        Lists individual expenses with all details.
        Supports date range and category filtering.
        
        Requirements: 2.2, 2.3, 2.4, 2.5, 2.6
        
        Args:
            start_date: Optional start date for filtering expenses (inclusive)
            end_date: Optional end date for filtering expenses (inclusive)
            category_id: Optional category ID to filter expenses
            
        Returns:
            Dict with generated_at, period, summary, by_category, and expenses list
        """
        from apps.expenses.models import Expense, ExpenseCategory
        
        # Build expense filter
        expense_filter = Q(is_approved=True)
        
        if start_date:
            expense_filter &= Q(expense_date__gte=start_date)
        if end_date:
            expense_filter &= Q(expense_date__lte=end_date)
        if category_id:
            expense_filter &= Q(category_id=category_id)
        
        # Get filtered expenses
        expenses = Expense.objects.filter(expense_filter).select_related('category').order_by('-expense_date', '-id')
        
        # Calculate summary statistics
        expense_count = expenses.count()
        total_expenses = expenses.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        average_expense = total_expenses / expense_count if expense_count > 0 else Decimal('0.00')
        
        # Build category breakdown
        category_totals = expenses.values(
            'category_id', 'category__name'
        ).annotate(
            total=Sum('total_amount'),
            count=Count('id')
        ).order_by('-total')
        
        by_category = []
        for cat in category_totals:
            percentage = (cat['total'] / total_expenses * 100) if total_expenses > 0 else Decimal('0.00')
            by_category.append({
                'category_id': cat['category_id'],
                'category_name': cat['category__name'] or 'بدون فئة',
                'total': cat['total'],
                'percentage': float(round(percentage, 2)),
                'count': cat['count']
            })
        
        # Build expenses list
        expenses_list = []
        for exp in expenses:
            expenses_list.append({
                'id': exp.id,
                'expense_number': exp.expense_number,
                'date': exp.expense_date,
                'category_id': exp.category_id,
                'category': exp.category.name if exp.category else 'بدون فئة',
                'description': exp.description,
                'amount': exp.amount,
                'tax_amount': exp.tax_amount,
                'total_amount': exp.total_amount,
                'payment_method': exp.payment_method,
                'payee': exp.payee,
                'reference': exp.reference
            })
        
        return {
            'generated_at': date.today(),
            'period': {
                'start': start_date,
                'end': end_date
            },
            'summary': {
                'total_expenses': total_expenses,
                'expense_count': expense_count,
                'average_expense': average_expense
            },
            'by_category': by_category,
            'expenses': expenses_list
        }
