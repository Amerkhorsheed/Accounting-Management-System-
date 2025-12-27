"""
Receipt Printer - Thermal Receipt Printing (58mm/80mm)
"""
from typing import Dict, List
from datetime import datetime
from ..config import config


class ReceiptPrinter:
    """
    Thermal receipt printer for 58mm and 80mm printers.
    """
    
    def __init__(self, width: int = 80):
        """
        Initialize receipt printer.
        width: 58 or 80 (mm)
        """
        self.width = width
        self.char_width = 48 if width == 80 else 32
        
    def _center(self, text: str) -> str:
        """Center text."""
        return text.center(self.char_width)
        
    def _right(self, text: str) -> str:
        """Right align text."""
        return text.rjust(self.char_width)
        
    def _line(self, char: str = '-') -> str:
        """Create horizontal line."""
        return char * self.char_width
        
    def _row(self, left: str, right: str) -> str:
        """Create two-column row."""
        available = self.char_width - len(right) - 1
        left = left[:available]
        return f"{left}{' ' * (self.char_width - len(left) - len(right))}{right}"
        
    def generate(self, invoice_data: Dict) -> str:
        """
        Generate receipt text.
        Returns formatted receipt string.
        """
        lines = []
        
        # Header
        lines.append(self._center(config.COMPANY_NAME))
        if config.COMPANY_ADDRESS:
            lines.append(self._center(config.COMPANY_ADDRESS[:self.char_width]))
        if config.COMPANY_PHONE:
            lines.append(self._center(f"هاتف: {config.COMPANY_PHONE}"))
        if config.COMPANY_TAX_NUMBER:
            lines.append(self._center(f"الرقم الضريبي: {config.COMPANY_TAX_NUMBER}"))
            
        lines.append(self._line('='))
        
        # Invoice info
        lines.append(self._center("فاتورة ضريبية مبسطة"))
        lines.append(self._line())
        
        lines.append(self._row("رقم الفاتورة:", invoice_data.get('invoice_number', '')))
        lines.append(self._row("التاريخ:", invoice_data.get('invoice_date', '')))
        lines.append(self._row("الوقت:", datetime.now().strftime('%H:%M:%S')))
        
        # Customer if available
        customer = invoice_data.get('customer', {})
        if customer.get('name'):
            lines.append(self._row("العميل:", customer['name'][:20]))
            
        lines.append(self._line())
        
        # Items
        lines.append(self._center("--- البنود ---"))
        
        for item in invoice_data.get('items', []):
            name = item.get('product_name', '')[:self.char_width - 10]
            qty = item.get('quantity', 0)
            price = float(item.get('unit_price', 0))
            total = float(item.get('total', 0))
            
            lines.append(name)
            lines.append(self._row(f"  {qty} x {price:,.2f}", f"{total:,.2f}"))
            
        lines.append(self._line())
        
        # Totals
        lines.append(self._row("المجموع الفرعي:", f"{float(invoice_data.get('subtotal', 0)):,.2f}"))
        
        discount = float(invoice_data.get('discount_amount', 0))
        if discount > 0:
            lines.append(self._row("الخصم:", f"-{discount:,.2f}"))
            
        lines.append(self._row("الضريبة (15%):", f"{float(invoice_data.get('tax_amount', 0)):,.2f}"))
        lines.append(self._line())
        
        lines.append(self._row("الإجمالي:", f"{float(invoice_data.get('total_amount', 0)):,.2f} {config.CURRENCY_SYMBOL}"))
        
        lines.append(self._line('='))
        
        # Payment info
        payment_method = invoice_data.get('payment_method', 'cash')
        payment_labels = {
            'cash': 'نقداً',
            'card': 'بطاقة',
            'credit': 'آجل',
            'bank': 'تحويل'
        }
        lines.append(self._row("طريقة الدفع:", payment_labels.get(payment_method, payment_method)))
        
        if payment_method == 'cash':
            paid = float(invoice_data.get('amount_paid', 0))
            change = paid - float(invoice_data.get('total_amount', 0))
            if paid > 0:
                lines.append(self._row("المدفوع:", f"{paid:,.2f}"))
                if change > 0:
                    lines.append(self._row("الباقي:", f"{change:,.2f}"))
                    
        lines.append(self._line())
        
        # Footer
        lines.append(self._center("شكراً لتعاملكم معنا"))
        lines.append(self._center("نتمنى لكم يوماً سعيداً"))
        lines.append("")
        lines.append("")
        lines.append("")  # Feed for cutting
        
        return '\n'.join(lines)
        
    def print_receipt(self, invoice_data: Dict, printer_name: str = None):
        """
        Print receipt to thermal printer.
        """
        content = self.generate(invoice_data)
        
        try:
            import win32print
            import win32ui
            
            # Get printer
            if not printer_name:
                printer_name = config.RECEIPT_PRINTER or win32print.GetDefaultPrinter()
                
            # Open printer
            hprinter = win32print.OpenPrinter(printer_name)
            
            try:
                # Start document
                job = win32print.StartDocPrinter(hprinter, 1, ("Receipt", None, "RAW"))
                win32print.StartPagePrinter(hprinter)
                
                # Write data
                win32print.WritePrinter(hprinter, content.encode('utf-8'))
                
                # End document
                win32print.EndPagePrinter(hprinter)
                win32print.EndDocPrinter(hprinter)
                
            finally:
                win32print.ClosePrinter(hprinter)
                
        except ImportError:
            # Fallback - save to file
            import tempfile
            fd, filepath = tempfile.mkstemp(suffix='.txt')
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            import webbrowser
            webbrowser.open(filepath)
            return filepath
            
        return True
        
    def open_cash_drawer(self, printer_name: str = None):
        """
        Send command to open cash drawer.
        Standard ESC/POS command for cash drawer.
        """
        try:
            import win32print
            
            if not printer_name:
                printer_name = config.RECEIPT_PRINTER or win32print.GetDefaultPrinter()
                
            # ESC/POS cash drawer command
            # DLE DC4 n m t - Generates pulse on pin 2 or 5
            cash_drawer_cmd = bytes([0x1B, 0x70, 0x00, 0x19, 0xFA])
            
            hprinter = win32print.OpenPrinter(printer_name)
            try:
                job = win32print.StartDocPrinter(hprinter, 1, ("CashDrawer", None, "RAW"))
                win32print.StartPagePrinter(hprinter)
                win32print.WritePrinter(hprinter, cash_drawer_cmd)
                win32print.EndPagePrinter(hprinter)
                win32print.EndDocPrinter(hprinter)
            finally:
                win32print.ClosePrinter(hprinter)
                
            return True
            
        except:
            return False
