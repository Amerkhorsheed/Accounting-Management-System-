"""
Script to fix invoice statuses in the database.
Run with: python manage.py shell < fix_invoice_status.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from decimal import Decimal
from apps.sales.models import Invoice

def fix_invoice_statuses():
    """Fix invoices where paid_amount equals total_amount but status is not PAID."""
    
    # Find invoices that are fully paid but marked as partial
    invoices_to_fix = Invoice.objects.filter(
        status=Invoice.Status.PARTIAL
    )
    
    fixed_count = 0
    for invoice in invoices_to_fix:
        # Check if paid_amount >= total_amount (with small tolerance)
        if invoice.paid_amount >= invoice.total_amount - Decimal('0.01'):
            old_status = invoice.status
            invoice.status = Invoice.Status.PAID
            invoice.paid_amount = invoice.total_amount  # Ensure exact match
            invoice.save(update_fields=['status', 'paid_amount'])
            print(f"Fixed Invoice {invoice.invoice_number}: {old_status} -> {invoice.status}")
            print(f"  paid_amount: {invoice.paid_amount}, total_amount: {invoice.total_amount}")
            fixed_count += 1
    
    # Also check CONFIRMED invoices that might be fully paid
    confirmed_invoices = Invoice.objects.filter(
        status=Invoice.Status.CONFIRMED
    )
    
    for invoice in confirmed_invoices:
        if invoice.paid_amount >= invoice.total_amount - Decimal('0.01') and invoice.paid_amount > 0:
            old_status = invoice.status
            invoice.status = Invoice.Status.PAID
            invoice.paid_amount = invoice.total_amount
            invoice.save(update_fields=['status', 'paid_amount'])
            print(f"Fixed Invoice {invoice.invoice_number}: {old_status} -> {invoice.status}")
            fixed_count += 1
    
    print(f"\nTotal invoices fixed: {fixed_count}")

if __name__ == '__main__':
    fix_invoice_statuses()
