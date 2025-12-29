"""
Receipt Printer - Thermal Receipt Printing (58mm/80mm)
Supports Arabic text by rendering as image for XPrinter XP-Q838L
"""
from typing import Dict, Optional
from datetime import datetime
from io import BytesIO
from ..config import config


class ReceiptPrinter:
    """
    Thermal receipt printer for 80mm printers.
    Renders Arabic text as images for proper display.
    """
    
    def __init__(self, width: int = None):
        self.width = width or getattr(config, 'RECEIPT_WIDTH', 80) or 80
        # Pixel width for 80mm printer (203 DPI, ~72mm printable)
        self.pixel_width = 576 if self.width == 80 else 384
        self.char_width = 48 if self.width == 80 else 32
        
    def _format_price(self, amount) -> str:
        try:
            value = float(amount or 0)
            decimals = getattr(getattr(config, 'PRIMARY_CURRENCY', None), 'decimal_places', 0) or 0
            if decimals <= 0:
                return f"{int(round(value)):,}"
            return f"{value:,.{decimals}f}"
        except:
            return "0"
    
    def _format_qty(self, qty) -> str:
        try:
            q = float(qty)
            return str(int(q)) if q == int(q) else f"{q:.1f}"
        except:
            return "1"

    def _reshape_arabic(self, text: str) -> str:
        """Reshape Arabic text for proper display."""
        if not text:
            return ""
        try:
            s = str(text)

            try:
                import arabic_reshaper
                s = arabic_reshaper.reshape(s)
            except Exception:
                pass

            try:
                from bidi.algorithm import get_display
                return get_display(s)
            except Exception:
                return s[::-1]
        except Exception:
            return str(text)

    def _contains_arabic(self, text: str) -> bool:
        if not text:
            return False
        for ch in text:
            o = ord(ch)
            if (
                (0x0600 <= o <= 0x06FF)
                or (0x0750 <= o <= 0x077F)
                or (0x08A0 <= o <= 0x08FF)
                or (0xFB50 <= o <= 0xFDFF)
                or (0xFE70 <= o <= 0xFEFF)
            ):
                return True
        return False

    def _shape_text(self, text: str) -> str:
        text = "" if text is None else str(text)
        if self._contains_arabic(text):
            return self._reshape_arabic(text)
        return text

    def _get_currency_symbol(self) -> str:
        sym = getattr(getattr(config, 'PRIMARY_CURRENCY', None), 'symbol', None)
        return (sym or "").strip()

    def _load_fonts(self):
        try:
            from PIL import ImageFont
        except ImportError:
            return None, None, None
        
        # Tahoma is usually the safest for Arabic on Windows
        font_paths = [
            "C:/Windows/Fonts/tahoma.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/segoeui.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
        
        # Compact sizes for thermal
        size_normal = 20 if self.width == 80 else 18
        size_bold = 24 if self.width == 80 else 20
        size_small = 18 if self.width == 80 else 16
        
        for path in font_paths:
            try:
                normal = ImageFont.truetype(path, size_normal)
                bold = ImageFont.truetype(path, size_bold)
                small = ImageFont.truetype(path, size_small)
                return normal, bold, small
            except:
                continue
        
        normal = ImageFont.load_default()
        return normal, normal, normal

    def _text_width(self, draw, text: str, font) -> int:
        bbox = draw.textbbox((0, 0), text, font=font)
        return int(bbox[2] - bbox[0])

    def _wrap_text(self, draw, text: str, font, max_width: int):
        text = (text or "").strip()
        if not text:
            return [""]
        
        # If it already fits, avoid extra work
        if self._text_width(draw, text, font) <= max_width:
            return [text]
        
        words = text.split(" ")
        lines = []
        current = ""
        
        for w in words:
            candidate = w if not current else f"{current} {w}"
            if self._text_width(draw, candidate, font) <= max_width:
                current = candidate
                continue
            
            if current:
                lines.append(current)
            current = w
        
        if current:
            lines.append(current)
        
        return lines

    def _image_has_ink(self, img) -> bool:
        try:
            g = img.convert('L')
            hist = g.histogram()
            if not hist or len(hist) < 256:
                return True

            total = int(g.size[0]) * int(g.size[1])
            black = int(sum(hist[:16]))

            min_black = max(80, total // 5000)  # ~0.02% or 80 pixels
            return black >= min_black
        except Exception:
            return True

    def _escpos_bitmap_has_ink(self, data: bytes) -> bool:
        try:
            if not data:
                return False

            marker = b'\x1D\x76\x30\x00'
            i = 0
            while True:
                j = data.find(marker, i)
                if j < 0:
                    break
                if j + 8 > len(data):
                    break

                width_bytes = int(data[j + 4]) | (int(data[j + 5]) << 8)
                height = int(data[j + 6]) | (int(data[j + 7]) << 8)

                start = j + 8
                end = start + (width_bytes * height)
                if end > len(data):
                    break

                bmp = data[start:end]
                if any(bmp):
                    return True

                i = end

            return False
        except Exception:
            return True

    def _create_receipt_image_qt(self, invoice_data: Dict):
        try:
            from PySide6.QtGui import QTextDocument
            from PySide6.QtCore import QByteArray, QBuffer, QIODevice
        except Exception:
            return None

        try:
            from PIL import Image
        except Exception:
            return None

        width = self.pixel_width
        padding = 8
        avail = width - (padding * 2)

        company = (config.COMPANY_NAME or config.COMPANY_NAME_EN or "STORE").strip()
        phone = str(config.COMPANY_PHONE or "").strip()

        inv_num = str(invoice_data.get('invoice_number', '') or "")
        inv_date = str(invoice_data.get('invoice_date', '') or "")
        info = f"{inv_date}   #{inv_num}".strip()

        currency = self._get_currency_symbol()
        total_amount = self._format_price(invoice_data.get('total_amount', 0))
        total_text = f"{total_amount} {currency}".strip()

        items_html = ""
        items = invoice_data.get('items', []) or []
        for item in items:
            name = str(item.get('product_name', '') or item.get('name', '') or "Item")
            unit = str(item.get('unit_name', '') or item.get('unit_symbol', '') or "").strip()
            qty = self._format_qty(item.get('quantity', 1))
            price = self._format_price(item.get('unit_price', 0))
            line_total = self._format_price(item.get('total', 0))

            def esc(s: str) -> str:
                return (
                    ("" if s is None else str(s))
                    .replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                )

            name_html = esc(name)
            qty_disp = qty
            price_disp = price
            if unit:
                qty_disp = f"{qty} {unit}"
                price_disp = f"{price}/{unit}"

            items_html += (
                "<tr>"
                f"<td class='item'>{name_html}</td>"
                f"<td class='num'>{esc(qty_disp)}</td>"
                f"<td class='num'>{esc(price_disp)}</td>"
                f"<td class='num'>{esc(line_total)}</td>"
                "</tr>"
            )

        html = f"""
        <!DOCTYPE html>
        <html dir="rtl" lang="ar">
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: Tahoma, Arial, 'Segoe UI', sans-serif;
                    direction: rtl;
                    margin: 0;
                    padding: 0;
                    color: #000;
                    font-size: 15pt;
                }}
                .center {{ text-align: center; }}
                .company {{ font-size: 22pt; font-weight: 700; }}
                .small {{ font-size: 13pt; }}
                hr {{ border: 0; border-top: 1px solid #000; margin: 6px 0; }}
                table {{ width: 100%; border-collapse: collapse; table-layout: fixed; }}
                th {{ font-weight: 700; font-size: 13pt; padding: 5px 8px; border-bottom: 1px solid #000; }}
                td {{ font-size: 13pt; padding: 5px 8px; vertical-align: top; }}
                th:nth-child(1), td:nth-child(1) {{ width: 44%; }}
                th:nth-child(2), td:nth-child(2) {{ width: 18%; }}
                th:nth-child(3), td:nth-child(3) {{ width: 19%; }}
                th:nth-child(4), td:nth-child(4) {{ width: 19%; }}
                td.item {{ text-align: right; }}
                td.num {{ text-align: right; direction: ltr; white-space: nowrap; }}
                .total-row td {{ font-weight: 700; font-size: 15pt; padding-top: 10px; }}
            </style>
        </head>
        <body>
            <div class="center company">{company}</div>
            {f'<div class="center small">{phone}</div>' if phone else ''}
            <hr />
            <div class="center" style="font-weight:700;">فاتورة</div>
            {f'<div class="center small">{info}</div>' if info else ''}
            <hr />
            <table>
                <thead>
                    <tr>
                        <th style="text-align:right;">الصنف</th>
                        <th style="text-align:right; direction:ltr;">كمية</th>
                        <th style="text-align:right; direction:ltr;">سعر</th>
                        <th style="text-align:right; direction:ltr;">إجمالي</th>
                    </tr>
                </thead>
                <tbody>
                    {items_html}
                </tbody>
            </table>
            <hr />
            <table>
                <tr class="total-row">
                    <td class="item">الإجمالي</td>
                    <td class="num" colspan="3">{total_text}</td>
                </tr>
            </table>
            <hr />
            <div class="center small">شكراً لتعاملكم معنا</div>
        </body>
        </html>
        """

        doc = QTextDocument()
        doc.setHtml(html)
        doc.setTextWidth(avail)
        doc.adjustSize()

        size = doc.size().toSize()
        if size.width() <= 0 or size.height() <= 0:
            return None

        try:
            from PySide6.QtGui import QImage, QPainter
        except Exception:
            return None

        img_w = int(width)
        img_h = int(size.height() + (padding * 2))
        if img_h < 120:
            img_h = 120

        qimg = QImage(img_w, img_h, QImage.Format_ARGB32)
        qimg.fill(0xFFFFFFFF)

        painter = QPainter(qimg)
        try:
            painter.setRenderHint(QPainter.Antialiasing, False)
            painter.setRenderHint(QPainter.TextAntialiasing, False)
            painter.translate(padding, padding)
            doc.drawContents(painter)
        finally:
            painter.end()

        ba = QByteArray()
        buf = QBuffer(ba)
        buf.open(QIODevice.WriteOnly)
        qimg.save(buf, "PNG")
        buf.close()

        pil = Image.open(BytesIO(bytes(ba))).convert('L')
        pil = pil.point(lambda p: 0 if p < 200 else 255, mode='1')
        if not self._image_has_ink(pil):
            return None
        return pil

    def _create_receipt_image(self, invoice_data: Dict) -> bytes:
        """Create receipt as image for Arabic support."""
        try:
            from PIL import Image, ImageDraw
        except ImportError:
            return None
        
        width = self.pixel_width
        padding = 8
        gap = 14 if self.width == 80 else 12
        
        font, font_bold, font_small = self._load_fonts()
        if not font:
            return None
        
        measure_img = Image.new('L', (width, 10), color=255)
        measure = ImageDraw.Draw(measure_img)
        
        avail = width - (padding * 2)
        qty_w = 95 if self.width == 80 else 70
        price_w = 130 if self.width == 80 else 105
        total_w = 130 if self.width == 80 else 110
        item_w = max(120, avail - (qty_w + price_w + total_w + (gap * 3)))
        
        x_right = width - padding
        item_right = x_right
        qty_right = item_right - gap - item_w
        price_right = qty_right - gap - qty_w
        total_right = price_right - gap - total_w
        
        ops = []
        y = padding
        
        company = (config.COMPANY_NAME or config.COMPANY_NAME_EN or "STORE").strip()
        if company:
            ops.append(("center", (self._shape_text(company), font_bold)))
            y += 34
        
        if config.COMPANY_PHONE:
            ops.append(("center", (str(config.COMPANY_PHONE), font_small)))
            y += 26
        
        ops.append(("hline", None))
        y += 12
        
        ops.append(("center", (self._shape_text("فاتورة"), font)))
        y += 28
        
        inv_num = str(invoice_data.get('invoice_number', '') or "")
        inv_date = str(invoice_data.get('invoice_date', '') or "")
        info = f"{inv_date}   #{inv_num}".strip()
        if info:
            ops.append(("center", (info, font_small)))
            y += 26
        
        ops.append(("hline", None))
        y += 12
        
        # Table header: Item | Qty | Price | Total
        ops.append(("table_header", (
            self._shape_text("الصنف"),
            self._shape_text("كمية"),
            self._shape_text("سعر"),
            self._shape_text("إجمالي"),
        )))
        y += 30
        ops.append(("hline", None))
        y += 12

        items = invoice_data.get('items', []) or []
        for item in items:
            name = str(item.get('product_name', '') or item.get('name', '') or "Item")
            unit = str(item.get('unit_name', '') or item.get('unit_symbol', '') or "").strip()
            qty = self._format_qty(item.get('quantity', 1))
            price = self._format_price(item.get('unit_price', 0))
            total = self._format_price(item.get('total', 0))

            qty_disp = f"{qty} {unit}" if unit else qty
            price_disp = f"{price}/{unit}" if unit else price

            shaped_name = self._shape_text(name)
            name_lines = self._wrap_text(measure, shaped_name, font_small, item_w)
            if not name_lines:
                name_lines = [""]

            first = True
            for ln in name_lines:
                if first:
                    ops.append(("item_row", (ln, qty_disp, price_disp, total)))
                    y += 26
                    first = False
                else:
                    ops.append(("item_name_only", (ln,)))
                    y += 24
        
        ops.append(("hline", None))
        y += 14
        
        # Total (only essential field)
        currency = self._get_currency_symbol()
        total_amount = self._format_price(invoice_data.get('total_amount', 0))
        total_text = f"{total_amount} {currency}".strip()
        ops.append(("total_row", (self._shape_text("الإجمالي"), total_text)))
        y += 34
        
        ops.append(("hline", None))
        y += 12
        
        ops.append(("center", (self._shape_text("شكراً لتعاملكم معنا"), font_small)))
        y += 28
        y += 18
        
        height = max(int(y + padding), 120)
        
        img = Image.new('L', (width, height), color=255)
        draw = ImageDraw.Draw(img)
        
        y = padding
        for op, payload in ops:
            if op == "center":
                text, fnt = payload
                bbox = draw.textbbox((0, 0), text, font=fnt)
                tw = bbox[2] - bbox[0]
                draw.text(((width - tw) // 2, y), text, font=fnt, fill=0)
                y += 34 if fnt == font_bold else 26
            elif op == "hline":
                draw.line((padding, y, width - padding, y), fill=0, width=1)
                y += 10
            elif op == "table_header":
                hi, hq, hp, ht = payload
                tw = self._text_width(draw, ht, font_small)
                draw.text((total_right - tw, y), ht, font=font_small, fill=0)
                tw = self._text_width(draw, hp, font_small)
                draw.text((price_right - tw, y), hp, font=font_small, fill=0)
                tw = self._text_width(draw, hq, font_small)
                draw.text((qty_right - tw, y), hq, font=font_small, fill=0)
                tw = self._text_width(draw, hi, font_small)
                draw.text((item_right - tw, y), hi, font=font_small, fill=0)
                y += 28
            elif op == "item_row":
                ln, qty, price, total = payload
                s = str(total)
                tw = self._text_width(draw, s, font_small)
                draw.text((total_right - tw, y), s, font=font_small, fill=0)
                s = str(price)
                tw = self._text_width(draw, s, font_small)
                draw.text((price_right - tw, y), s, font=font_small, fill=0)
                s = str(qty)
                tw = self._text_width(draw, s, font_small)
                draw.text((qty_right - tw, y), s, font=font_small, fill=0)
                tw = self._text_width(draw, ln, font_small)
                draw.text((item_right - tw, y), ln, font=font_small, fill=0)
                y += 26
            elif op == "item_name_only":
                (ln,) = payload
                tw = self._text_width(draw, ln, font=font_small)
                draw.text((item_right - tw, y), ln, font=font_small, fill=0)
                y += 24
            elif op == "total_row":
                lbl, value = payload
                tw = self._text_width(draw, value, font_bold)
                draw.text((total_right - tw, y), value, font=font_bold, fill=0)
                tw = self._text_width(draw, lbl, font_bold)
                draw.text((item_right - tw, y), lbl, font=font_bold, fill=0)
                y += 34
        
        # Convert to pure black/white with threshold (better thermal output)
        img = img.point(lambda p: 0 if p < 180 else 255, mode='1')
        return img

    def _image_to_escpos(self, img) -> bytes:
        """Convert PIL image to ESC/POS raster format."""
        img = img.convert('L')
        width, height = img.size
        width_bytes = (width + 7) // 8

        output = bytearray()
        output.extend(b'\x1B\x40')
        output.extend(b'\x1B\x61\x01')

        pixels = img.load()
        xL = width_bytes & 0xFF
        xH = (width_bytes >> 8) & 0xFF

        chunk_h = 240
        y0 = 0
        while y0 < height:
            h = min(chunk_h, height - y0)
            yL = h & 0xFF
            yH = (h >> 8) & 0xFF

            output.extend(b'\x1D\x76\x30\x00')
            output.append(xL)
            output.append(xH)
            output.append(yL)
            output.append(yH)

            for y in range(y0, y0 + h):
                for xb in range(width_bytes):
                    b = 0
                    for bit in range(8):
                        x = xb * 8 + bit
                        if x < width and int(pixels[x, y]) < 200:
                            b |= (1 << (7 - bit))
                    output.append(b)

            output.extend(b'\x0A')
            y0 += h

        output.extend(b'\x1B\x64\x04')
        output.extend(b'\x1D\x56\x01')
        return bytes(output)

    def generate_text(self, invoice_data: Dict) -> str:
        """Generate plain text receipt (fallback)."""
        lines = []
        
        lines.append("")
        company = config.COMPANY_NAME or "STORE"
        lines.append(company.center(self.char_width))
        
        if config.COMPANY_PHONE:
            lines.append(f"Tel: {config.COMPANY_PHONE}".center(self.char_width))
        
        lines.append("=" * self.char_width)
        lines.append("SALES RECEIPT".center(self.char_width))
        lines.append("=" * self.char_width)
        
        inv_num = invoice_data.get('invoice_number', '')
        inv_date = invoice_data.get('invoice_date', '')
        
        lines.append(f"Invoice: {inv_num}")
        lines.append(f"Date: {inv_date}")
        
        cust_name = invoice_data.get('customer_name') or ''
        if not cust_name:
            cust = invoice_data.get('customer', {})
            if isinstance(cust, dict):
                cust_name = cust.get('name', '')
        if cust_name:
            lines.append(f"Customer: {cust_name[:20]}")
        
        lines.append("-" * self.char_width)
        
        items = invoice_data.get('items', [])
        for item in items:
            unit = str(item.get('unit_name', '') or item.get('unit_symbol', '') or "").strip()
            name = item.get('product_name', 'Product')
            if unit:
                name = f"{name} ({unit})"
            name = name[:25]
            qty = self._format_qty(item.get('quantity', 1))
            total = self._format_price(item.get('total', 0))
            lines.append(f"{name}")
            lines.append(f"  {qty} x ... = {total}")
        
        lines.append("-" * self.char_width)
        
        total_amount = self._format_price(invoice_data.get('total_amount', 0))
        lines.append(f"TOTAL: {total_amount} SYP")
        
        lines.append("=" * self.char_width)
        lines.append("Thank you!".center(self.char_width))
        lines.append("")
        lines.append("")
        
        return '\n'.join(lines)
        
    def print_receipt(self, invoice_data: Dict, printer_name: str = None):
        """Print receipt to thermal printer."""
        
        # Try image-based printing first (for Arabic support)
        try:
            img = self._create_receipt_image_qt(invoice_data)
            if img and not self._image_has_ink(img):
                img = None
            if img:
                data = self._image_to_escpos(img)
                return self._send_to_printer(data, printer_name)

            img = self._create_receipt_image(invoice_data)
            if img and not self._image_has_ink(img):
                img = None
            if img:
                data = self._image_to_escpos(img)
                return self._send_to_printer(data, printer_name)
        except Exception as e:
            print(f"Image print failed: {e}")
        
        # Fallback to text
        content = self.generate_text(invoice_data)
        data = b'\x1B\x40' + content.encode('ascii', errors='replace') + b'\x1D\x56\x01'
        return self._send_to_printer(data, printer_name)
    
    def _send_to_printer(self, data: bytes, printer_name: str = None):
        """Send data to printer."""
        try:
            import win32print
            
            if not printer_name:
                printer_name = config.RECEIPT_PRINTER or win32print.GetDefaultPrinter()
            
            hprinter = win32print.OpenPrinter(printer_name)
            try:
                win32print.StartDocPrinter(hprinter, 1, ("Receipt", None, "RAW"))
                win32print.StartPagePrinter(hprinter)

                total = len(data or b"")
                pos = 0
                while pos < total:
                    chunk = data[pos:pos + 8192]
                    written = win32print.WritePrinter(hprinter, chunk)
                    if written is None:
                        written = 0
                    if written <= 0:
                        raise RuntimeError("Failed to write to printer")
                    pos += written

                win32print.EndPagePrinter(hprinter)
                win32print.EndDocPrinter(hprinter)
            finally:
                win32print.ClosePrinter(hprinter)
            
            return True
            
        except ImportError:
            return self._save_to_file(data)
        except Exception as e:
            print(f"Print error: {e}")
            return self._save_to_file(data)
    
    def _save_to_file(self, data) -> str:
        """Save receipt to file."""
        import tempfile
        import webbrowser
        import os
        
        # If data is bytes, convert to text for file
        if isinstance(data, bytes):
            content = data.decode('ascii', errors='replace')
        else:
            content = str(data)
        
        fd, filepath = tempfile.mkstemp(suffix='.txt', prefix='receipt_')
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write(content)
            webbrowser.open(filepath)
            return filepath
        except:
            return None
    
    def open_cash_drawer(self, printer_name: str = None) -> bool:
        """Open cash drawer."""
        try:
            import win32print
            
            if not printer_name:
                printer_name = config.RECEIPT_PRINTER or win32print.GetDefaultPrinter()
            
            cmd = b'\x1B\x70\x00\x19\xFA'
            
            hprinter = win32print.OpenPrinter(printer_name)
            try:
                win32print.StartDocPrinter(hprinter, 1, ("Drawer", None, "RAW"))
                win32print.StartPagePrinter(hprinter)
                win32print.WritePrinter(hprinter, cmd)
                win32print.EndPagePrinter(hprinter)
                win32print.EndDocPrinter(hprinter)
            finally:
                win32print.ClosePrinter(hprinter)
            return True
        except:
            return False
