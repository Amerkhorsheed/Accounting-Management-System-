"""
Reports Views
"""
from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from datetime import date, datetime

from .services import ReportService
from apps.core.decorators import handle_view_error


class DashboardView(views.APIView):
    """Dashboard summary endpoint."""
    
    permission_classes = [IsAuthenticated]

    @handle_view_error
    def get(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        data = ReportService.get_dashboard_summary(start_date, end_date)
        return Response(data)


class SalesReportView(views.APIView):
    """Sales report endpoint."""
    
    permission_classes = [IsAuthenticated]

    @handle_view_error
    def get(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        group_by = request.query_params.get('group_by', 'day')
        
        if not start_date or not end_date:
            return Response(
                {'detail': 'يجب تحديد تاريخ البداية والنهاية'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        data = ReportService.get_sales_report(start_date, end_date, group_by)
        return Response(data)


class ProfitReportView(views.APIView):
    """Profit/Loss report endpoint."""
    
    permission_classes = [IsAuthenticated]

    @handle_view_error
    def get(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not start_date or not end_date:
            return Response(
                {'detail': 'يجب تحديد تاريخ البداية والنهاية'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        data = ReportService.get_profit_report(start_date, end_date)
        return Response(data)


class InventoryReportView(views.APIView):
    """Inventory report endpoint."""
    
    permission_classes = [IsAuthenticated]

    @handle_view_error
    def get(self, request):
        data = ReportService.get_inventory_report()
        return Response(data)


class CustomerReportView(views.APIView):
    """Customer analysis report endpoint."""
    
    permission_classes = [IsAuthenticated]

    @handle_view_error
    def get(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not start_date or not end_date:
            # Default to current month
            today = date.today()
            start_date = today.replace(day=1)
            end_date = today
        else:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        data = ReportService.get_customer_report(start_date, end_date)
        return Response(data)


class ReceivablesReportView(views.APIView):
    """
    Receivables report endpoint.
    
    Returns total outstanding amount across all customers,
    customers with outstanding balances sorted by amount,
    and invoice counts per customer.
    
    Requirements: 4.1-4.5
    """
    
    permission_classes = [IsAuthenticated]

    @handle_view_error
    def get(self, request):
        # Parse optional filters
        customer_type = request.query_params.get('customer_type')
        salesperson_id = request.query_params.get('salesperson_id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        # Convert dates if provided
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        if salesperson_id:
            salesperson_id = int(salesperson_id)
        
        data = ReportService.get_receivables_report(
            customer_type=customer_type,
            salesperson_id=salesperson_id,
            start_date=start_date,
            end_date=end_date
        )
        return Response(data)


class AgingReportView(views.APIView):
    """
    Aging report endpoint.
    
    Returns outstanding amounts categorized by age:
    current, 1-30 days, 31-60 days, 61-90 days, over 90 days.
    
    Requirements: 5.1-5.5
    """
    
    permission_classes = [IsAuthenticated]

    @handle_view_error
    def get(self, request):
        # Parse optional as_of_date
        as_of_date = request.query_params.get('as_of_date')
        
        if as_of_date:
            as_of_date = datetime.strptime(as_of_date, '%Y-%m-%d').date()
        
        data = ReportService.get_aging_report(as_of_date=as_of_date)
        return Response(data)
