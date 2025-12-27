"""
Invoice Printer - A4 Invoice Generation and Printing
"""
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT
from typing import Dict, List
import os
import tempfile

from ..config import config


class InvoicePrinter:
    """
    A4 Invoice PDF generator.
    """
    
    def __init__(self):
        self.width, self.height = A4
        self.margin = 1.5 * cm
        self._setup_fonts()
        
    def _setup_fonts(self):
        """Setup Arabic fonts."""
        # Use system Arabic font
        try:
            pdfmetrics.registerFont(TTFont('Arabic', 'C:/Windows/Fonts/arial.ttf'))
        except:
            pass
            
    def _get_styles(self):
        """Get paragraph styles."""
        styles = getSampleStyleSheet()
        
        styles.add(ParagraphStyle(
            name='ArabicTitle',
            fontName='Arabic',
            fontSize=18,
            alignment=TA_RIGHT,
            leading=22
        ))
        
        styles.add(ParagraphStyle(
            name='ArabicNormal',
            fontName='Arabic',
            fontSize=10,
            alignment=TA_RIGHT,
            leading=14
        ))
        
        styles.add(ParagraphStyle(
            name='ArabicBold',
            fontName='Arabic',
            fontSize=12,
            alignment=TA_RIGHT,
            leading=16
        ))
        
        return styles
        
    def generate(self, invoice_data: Dict) -> str:
        """
        Generate A4 invoice PDF.
        Returns path to generated PDF file.
        """
        # Create temp file
        fd, filepath = tempfile.mkstemp(suffix='.pdf')
        os.close(fd)
        
        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=self.margin,
            leftMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=self.margin
        )
        
        styles = self._get_styles()
        elements = []
        
        # Header - Company info
        company_info = [
            [config.COMPANY_NAME],
            [config.COMPANY_ADDRESS],
            [f"هاتف: {config.COMPANY_PHONE}"],
            [f"الرقم الضريبي: {config.COMPANY_TAX_NUMBER}"],
        ]
        
        company_table = Table(company_info, colWidths=[self.width - 2 * self.margin])
        company_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Arabic'),
            ('FONTSIZE', (0, 0), (0, 0), 16),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
        ]))
        elements.append(company_table)
        elements.append(Spacer(1, 1 * cm))
        
        # Invoice title and number
        title_data = [
            ['فاتورة ضريبية', f"رقم: {invoice_data.get('invoice_number', '')}"],
            [f"التاريخ: {invoice_data.get('invoice_date', '')}", ''],
        ]
        
        title_table = Table(title_data, colWidths=[9 * cm, 9 * cm])
        title_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Arabic'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        elements.append(title_table)
        elements.append(Spacer(1, 0.5 * cm))
        
        # Customer info
        customer = invoice_data.get('customer', {})
        customer_data = [
            ['معلومات العميل', ''],
            [f"الاسم: {customer.get('name', '')}", f"الكود: {customer.get('code', '')}"],
            [f"الهاتف: {customer.get('phone', '')}", f"الرقم الضريبي: {customer.get('tax_number', '')}"],
        ]
        
        customer_table = Table(customer_data, colWidths=[9 * cm, 9 * cm])
        customer_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Arabic'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTSIZE', (0, 0), (0, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.grey),
            ('INNERGRID', (0, 1), (-1, -1), 0.25, colors.lightgrey),
        ]))
        elements.append(customer_table)
        elements.append(Spacer(1, 0.5 * cm))
        
        # Items table
        items = invoice_data.get('items', [])
        table_data = [
            ['#', 'المنتج', 'الكمية', 'السعر', 'الخصم', 'الضريبة', 'الإجمالي']
        ]
        
        for i, item in enumerate(items, 1):
            table_data.append([
                str(i),
                item.get('product_name', ''),
                str(item.get('quantity', 0)),
                f"{float(item.get('unit_price', 0)):,.2f}",
                f"{float(item.get('discount_amount', 0)):,.2f}",
                f"{float(item.get('tax_amount', 0)):,.2f}",
                f"{float(item.get('total', 0)):,.2f}",
            ])
        
        col_widths = [0.8*cm, 6*cm, 2*cm, 2.5*cm, 2*cm, 2*cm, 2.5*cm]
        items_table = Table(table_data, colWidths=col_widths)
        items_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Arabic'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.145, 0.388, 0.922)),  # Primary color
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.grey),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.lightgrey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.Color(0.97, 0.98, 0.99)]),
        ]))
        elements.append(items_table)
        elements.append(Spacer(1, 0.5 * cm))
        
        # Totals
        totals_data = [
            [f"{float(invoice_data.get('subtotal', 0)):,.2f}", 'المجموع الفرعي'],
            [f"{float(invoice_data.get('discount_amount', 0)):,.2f}", 'الخصم'],
            [f"{float(invoice_data.get('tax_amount', 0)):,.2f}", 'ضريبة القيمة المضافة (15%)'],
            [f"{float(invoice_data.get('total_amount', 0)):,.2f}", 'الإجمالي'],
        ]
        
        totals_table = Table(totals_data, colWidths=[3.5*cm, 4*cm])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Arabic'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTSIZE', (0, -1), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BACKGROUND', (0, -1), (-1, -1), colors.Color(0.145, 0.388, 0.922)),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        
        # Right align totals table
        totals_wrapper = Table([[totals_table, '']], colWidths=[7.5*cm, 10*cm])
        elements.append(totals_wrapper)
        elements.append(Spacer(1, 1 * cm))
        
        # Notes
        if invoice_data.get('notes'):
            notes = Paragraph(f"ملاحظات: {invoice_data['notes']}", styles['ArabicNormal'])
            elements.append(notes)
            elements.append(Spacer(1, 0.5 * cm))
        
        # Footer
        footer_text = "شكراً لتعاملكم معنا"
        footer = Paragraph(footer_text, styles['ArabicNormal'])
        elements.append(footer)
        
        # Build PDF
        doc.build(elements)
        
        return filepath
        
    def print_invoice(self, invoice_data: Dict, printer_name: str = None):
        """
        Generate and print invoice.
        """
        filepath = self.generate(invoice_data)
        
        try:
            # Windows printing
            import win32api
            import win32print
            
            if printer_name:
                win32print.SetDefaultPrinter(printer_name)
                
            win32api.ShellExecute(0, "print", filepath, None, ".", 0)
            
        except ImportError:
            # Fallback - open PDF with default viewer
            import webbrowser
            webbrowser.open(filepath)
            
        return filepath
