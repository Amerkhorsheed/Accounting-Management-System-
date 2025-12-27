"""
Reports Serializers
"""
from rest_framework import serializers
from decimal import Decimal


class ReceivablesCustomerSerializer(serializers.Serializer):
    """Serializer for customer data in receivables report."""
    
    id = serializers.IntegerField()
    code = serializers.CharField()
    name = serializers.CharField()
    customer_type = serializers.CharField()
    current_balance = serializers.DecimalField(max_digits=15, decimal_places=2)
    credit_limit = serializers.DecimalField(max_digits=15, decimal_places=2)
    available_credit = serializers.DecimalField(max_digits=15, decimal_places=2)
    unpaid_invoice_count = serializers.IntegerField()
    partial_invoice_count = serializers.IntegerField()
    total_invoice_count = serializers.IntegerField()
    overdue_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    salesperson = serializers.CharField(allow_null=True)


class ReceivablesSummarySerializer(serializers.Serializer):
    """Serializer for receivables report summary."""
    
    total_outstanding = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_overdue = serializers.DecimalField(max_digits=15, decimal_places=2)
    customer_count = serializers.IntegerField()
    total_unpaid_invoices = serializers.IntegerField()
    total_partial_invoices = serializers.IntegerField()


class ReceivablesFiltersSerializer(serializers.Serializer):
    """Serializer for receivables report filters."""
    
    customer_type = serializers.CharField(allow_null=True)
    salesperson_id = serializers.IntegerField(allow_null=True)
    start_date = serializers.DateField(allow_null=True)
    end_date = serializers.DateField(allow_null=True)


class ReceivablesReportSerializer(serializers.Serializer):
    """Serializer for complete receivables report."""
    
    generated_at = serializers.DateField()
    filters = ReceivablesFiltersSerializer()
    summary = ReceivablesSummarySerializer()
    customers = ReceivablesCustomerSerializer(many=True)


class AgingInvoiceSerializer(serializers.Serializer):
    """Serializer for invoice data in aging report."""
    
    id = serializers.IntegerField()
    invoice_number = serializers.CharField()
    invoice_date = serializers.DateField()
    due_date = serializers.DateField(allow_null=True)
    customer_id = serializers.IntegerField()
    customer_name = serializers.CharField()
    customer_code = serializers.CharField()
    total_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    paid_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    remaining_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    days_overdue = serializers.IntegerField()


class AgingBucketSerializer(serializers.Serializer):
    """Serializer for aging bucket data."""
    
    label = serializers.CharField()
    total = serializers.DecimalField(max_digits=15, decimal_places=2)
    invoice_count = serializers.IntegerField()
    invoices = AgingInvoiceSerializer(many=True)


class AgingSummarySerializer(serializers.Serializer):
    """Serializer for aging report summary."""
    
    total_outstanding = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_current = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_overdue = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_severely_overdue = serializers.DecimalField(max_digits=15, decimal_places=2)


class AgingCustomerBreakdownSerializer(serializers.Serializer):
    """Serializer for customer breakdown in aging report."""
    
    customer_id = serializers.IntegerField()
    customer_name = serializers.CharField()
    customer_code = serializers.CharField()
    current = serializers.DecimalField(max_digits=15, decimal_places=2)
    field_1_30 = serializers.DecimalField(max_digits=15, decimal_places=2, source='1_30')
    field_31_60 = serializers.DecimalField(max_digits=15, decimal_places=2, source='31_60')
    field_61_90 = serializers.DecimalField(max_digits=15, decimal_places=2, source='61_90')
    over_90 = serializers.DecimalField(max_digits=15, decimal_places=2)
    total = serializers.DecimalField(max_digits=15, decimal_places=2)


class AgingBucketsSerializer(serializers.Serializer):
    """Serializer for all aging buckets."""
    
    current = AgingBucketSerializer()
    field_1_30 = AgingBucketSerializer(source='1_30')
    field_31_60 = AgingBucketSerializer(source='31_60')
    field_61_90 = AgingBucketSerializer(source='61_90')
    over_90 = AgingBucketSerializer()


class AgingReportSerializer(serializers.Serializer):
    """Serializer for complete aging report."""
    
    as_of_date = serializers.DateField()
    summary = AgingSummarySerializer()
    buckets = AgingBucketsSerializer()
    customer_breakdown = AgingCustomerBreakdownSerializer(many=True)


class CreditSummarySerializer(serializers.Serializer):
    """Serializer for credit summary on dashboard."""
    
    receivables_total = serializers.DecimalField(max_digits=15, decimal_places=2)
    customers_with_balance = serializers.IntegerField()
    overdue_total = serializers.DecimalField(max_digits=15, decimal_places=2)
