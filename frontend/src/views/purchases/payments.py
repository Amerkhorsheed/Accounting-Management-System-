"""Supplier Payments View - إدارة سندات الصرف للموردين"""

from datetime import datetime
from typing import List, Dict

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QComboBox, QDateEdit,
    QDialog, QGridLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont, QColor

from ...config import Colors, Fonts, config
from ...widgets.tables import DataTable
from ...widgets.cards import Card
from ...widgets.dialogs import MessageDialog
from ...services.api import api, ApiException
from ...services.export import ExportService, ExportError
from ...utils.error_handler import handle_ui_error


class SupplierPaymentsView(QWidget):
    """Dedicated screen for supplier payments list + filters + details."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.suppliers_cache: List[Dict] = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QHBoxLayout()
        title = QLabel("مدفوعات الموردين")
        title.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_H2, QFont.Bold))
        header.addWidget(title)
        header.addStretch()

        export_excel_btn = QPushButton("📊 Excel")
        export_excel_btn.setProperty("class", "secondary")
        export_excel_btn.clicked.connect(self._export_excel)
        header.addWidget(export_excel_btn)

        export_pdf_btn = QPushButton("📄 PDF")
        export_pdf_btn.setProperty("class", "secondary")
        export_pdf_btn.clicked.connect(self._export_pdf)
        header.addWidget(export_pdf_btn)

        layout.addLayout(header)

        filters_frame = QFrame()
        filters_frame.setStyleSheet(
            f"background-color: {Colors.LIGHT_BG}; border-radius: 8px; padding: 12px;"
        )
        filters_layout = QHBoxLayout(filters_frame)
        filters_layout.setSpacing(16)

        filters_layout.addWidget(QLabel("المورد:"))
        self.supplier_filter = QComboBox()
        self.supplier_filter.addItem("الكل", None)
        self.supplier_filter.setMinimumWidth(220)
        self.supplier_filter.setEditable(True)
        self.supplier_filter.setInsertPolicy(QComboBox.NoInsert)
        filters_layout.addWidget(self.supplier_filter)

        filters_layout.addWidget(QLabel("من:"))
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.date_from.setMaximumWidth(140)
        filters_layout.addWidget(self.date_from)

        filters_layout.addWidget(QLabel("إلى:"))
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setMaximumWidth(140)
        filters_layout.addWidget(self.date_to)

        filters_layout.addWidget(QLabel("الطريقة:"))
        self.method_filter = QComboBox()
        self.method_filter.addItem("الكل", "")
        self.method_filter.addItem("نقداً", "cash")
        self.method_filter.addItem("تحويل بنكي", "bank")
        self.method_filter.addItem("شيك", "check")
        self.method_filter.addItem("بطاقة ائتمان", "credit")
        self.method_filter.setMinimumWidth(140)
        filters_layout.addWidget(self.method_filter)

        filters_layout.addWidget(QLabel("العملة:"))
        self.currency_filter = QComboBox()
        self.currency_filter.addItem("الكل", "")
        self.currency_filter.addItem("USD", "USD")
        self.currency_filter.addItem("ل.س قديم", "SYP_OLD")
        self.currency_filter.addItem("ل.س جديد", "SYP_NEW")
        self.currency_filter.setMinimumWidth(130)
        filters_layout.addWidget(self.currency_filter)

        search_btn = QPushButton("🔍 بحث")
        search_btn.setProperty("class", "primary")
        search_btn.clicked.connect(self.apply_filters)
        filters_layout.addWidget(search_btn)

        clear_btn = QPushButton("مسح")
        clear_btn.setProperty("class", "secondary")
        clear_btn.clicked.connect(self.clear_filters)
        filters_layout.addWidget(clear_btn)

        filters_layout.addStretch()
        layout.addWidget(filters_frame)

        columns = [
            {'key': 'payment_number', 'label': 'رقم السند', 'type': 'text'},
            {'key': 'supplier_name', 'label': 'المورد', 'type': 'text', 'sortable': False},
            {'key': 'purchase_order_number', 'label': 'أمر الشراء', 'type': 'text', 'sortable': False},
            {'key': 'payment_date', 'label': 'التاريخ', 'type': 'date'},
            {'key': 'amount', 'label': 'المبلغ', 'type': 'currency'},
            {'key': 'amount_usd', 'label': 'عرض (USD)', 'type': 'currency'},
            {'key': 'transaction_currency', 'label': 'العملة', 'type': 'text'},
            {'key': 'payment_method_display', 'label': 'طريقة الدفع', 'type': 'text', 'sortable': False},
        ]

        self.table = DataTable(columns, actions=['view'])
        self.table.add_btn.setText("➕ سند صرف جديد")
        self.table.action_clicked.connect(self.on_action)
        self.table.row_double_clicked.connect(self.view_payment_details)
        self.table.page_changed.connect(self.on_page_changed)
        self.table.sort_changed.connect(self.on_sort_changed)

        layout.addWidget(self.table)

    @handle_ui_error
    def refresh(self):
        self._load_suppliers()
        params = self._build_params()

        response = api.get_supplier_payments(params)
        if isinstance(response, dict):
            payments = response.get('results', [])
            total = response.get('count', len(payments))
        else:
            payments = response if isinstance(response, list) else []
            total = len(payments)

        self.table.set_data(payments, total)

    def _load_suppliers(self):
        try:
            response = api.get_suppliers()
            if isinstance(response, dict) and 'results' in response:
                self.suppliers_cache = response['results']
            else:
                self.suppliers_cache = response if isinstance(response, list) else []

            current = self.supplier_filter.currentData()
            self.supplier_filter.blockSignals(True)
            self.supplier_filter.clear()
            self.supplier_filter.addItem("الكل", None)
            for s in self.suppliers_cache:
                text = f"{s.get('name', '')} ({s.get('code', '')})"
                self.supplier_filter.addItem(text, s.get('id'))

            if current:
                for i in range(self.supplier_filter.count()):
                    if self.supplier_filter.itemData(i) == current:
                        self.supplier_filter.setCurrentIndex(i)
                        break
            self.supplier_filter.blockSignals(False)
        except ApiException:
            pass

    def _build_params(self) -> dict:
        params = self.table.get_pagination_params()
        params.update(self.table.get_sort_params())

        supplier_id = self.supplier_filter.currentData()
        if supplier_id:
            params['supplier'] = supplier_id

        method = self.method_filter.currentData()
        if method:
            params['payment_method'] = method

        currency = self.currency_filter.currentData()
        if currency:
            params['transaction_currency'] = currency

        params['payment_date__gte'] = self.date_from.date().toString('yyyy-MM-dd')
        params['payment_date__lte'] = self.date_to.date().toString('yyyy-MM-dd')

        return params

    def apply_filters(self):
        self.table.current_page = 1
        self.refresh()

    def clear_filters(self):
        self.supplier_filter.setCurrentIndex(0)
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.date_to.setDate(QDate.currentDate())
        self.method_filter.setCurrentIndex(0)
        self.currency_filter.setCurrentIndex(0)
        self.table.current_page = 1
        self.refresh()

    def on_page_changed(self, page: int, page_size: int):
        self.refresh()

    def on_sort_changed(self, column: str, order: str):
        self.refresh()

    def on_action(self, action: str, row: int, data: dict):
        if action == 'view':
            self.view_payment_details(row, data)
        elif action == 'add':
            self.add_payment()

    def add_payment(self):
        from . import SupplierPaymentDialog

        dialog = SupplierPaymentDialog(order=None, parent=self)
        dialog.saved.connect(self._save_payment)
        dialog.exec()

    @handle_ui_error
    def _save_payment(self, data: dict):
        created = api.create_supplier_payment(data)
        MessageDialog.success(
            self,
            "نجاح",
            f"تم تسجيل سند الصرف بنجاح\nرقم السند: {created.get('payment_number', 'N/A')}"
        )
        self.refresh()

    @handle_ui_error
    def view_payment_details(self, row: int, data: dict):
        payment_id = data.get('id')
        if not payment_id:
            return
        payment = api.get_supplier_payment(payment_id)
        dialog = SupplierPaymentDetailsDialog(payment, parent=self)
        dialog.exec()

    def _export_excel(self):
        rows = self.table.data or []
        if not rows:
            MessageDialog.warning(self, "تنبيه", "لا توجد بيانات للتصدير")
            return

        try:
            columns = [
                ('payment_number', 'رقم السند'),
                ('supplier_name', 'المورد'),
                ('purchase_order_number', 'أمر الشراء'),
                ('payment_date', 'التاريخ'),
                ('amount', 'المبلغ'),
                ('amount_usd', 'عرض (USD)'),
                ('transaction_currency', 'العملة'),
                ('payment_method_display', 'طريقة الدفع'),
                ('reference', 'المرجع'),
                ('created_by_name', 'أنشئ بواسطة'),
            ]

            export_data = []
            total_usd = 0.0
            for p in rows:
                amount_usd = float(p.get('amount_usd', 0) or 0)
                total_usd += amount_usd
                export_data.append({
                    'payment_number': p.get('payment_number', ''),
                    'supplier_name': p.get('supplier_name', ''),
                    'purchase_order_number': p.get('purchase_order_number', '') or '-',
                    'payment_date': p.get('payment_date', ''),
                    'amount': float(p.get('amount', 0) or 0),
                    'amount_usd': float(p.get('amount_usd', 0) or 0),
                    'transaction_currency': p.get('transaction_currency', ''),
                    'payment_method_display': p.get('payment_method_display', ''),
                    'reference': p.get('reference', ''),
                    'created_by_name': p.get('created_by_name', ''),
                })

            filename = f"مدفوعات_الموردين_{datetime.now().strftime('%Y%m%d')}.xlsx"
            summary_data = {
                'الفترة': f"{self.date_from.date().toString('yyyy-MM-dd')} → {self.date_to.date().toString('yyyy-MM-dd')}",
                'عدد السجلات (الصفحة)': str(len(rows)),
                'إجمالي (USD) (الصفحة)': config.format_usd(total_usd),
            }

            ok = ExportService.export_to_excel(
                data=export_data,
                columns=columns,
                filename=filename,
                title="مدفوعات الموردين",
                parent=self,
                summary=summary_data
            )
            if ok:
                MessageDialog.info(self, "نجاح", "تم التصدير بنجاح")
        except ExportError as e:
            MessageDialog.error(self, "خطأ", e.message)
        except Exception as e:
            MessageDialog.error(self, "خطأ", f"فشل التصدير: {str(e)}")

    def _export_pdf(self):
        rows = self.table.data or []
        if not rows:
            MessageDialog.warning(self, "تنبيه", "لا توجد بيانات للتصدير")
            return

        try:
            columns = [
                ('payment_number', 'رقم السند'),
                ('supplier_name', 'المورد'),
                ('purchase_order_number', 'أمر الشراء'),
                ('payment_date', 'التاريخ'),
                ('amount', 'المبلغ'),
                ('amount_usd', 'عرض (USD)'),
                ('transaction_currency', 'العملة'),
                ('payment_method_display', 'طريقة الدفع'),
            ]

            export_data = []
            total_usd = 0.0
            for p in rows:
                amount_usd = float(p.get('amount_usd', 0) or 0)
                total_usd += amount_usd
                export_data.append({
                    'payment_number': p.get('payment_number', ''),
                    'supplier_name': p.get('supplier_name', ''),
                    'purchase_order_number': p.get('purchase_order_number', '') or '-',
                    'payment_date': p.get('payment_date', ''),
                    'amount': float(p.get('amount', 0) or 0),
                    'amount_usd': float(p.get('amount_usd', 0) or 0),
                    'transaction_currency': p.get('transaction_currency', ''),
                    'payment_method_display': p.get('payment_method_display', ''),
                })

            filename = f"مدفوعات_الموردين_{datetime.now().strftime('%Y%m%d')}.pdf"
            summary_data = {
                'الفترة': f"{self.date_from.date().toString('yyyy-MM-dd')} → {self.date_to.date().toString('yyyy-MM-dd')}",
                'عدد السجلات (الصفحة)': str(len(rows)),
                'إجمالي (USD) (الصفحة)': config.format_usd(total_usd),
            }

            start_date = self.date_from.date().toString('yyyy-MM-dd')
            end_date = self.date_to.date().toString('yyyy-MM-dd')

            ok = ExportService.export_to_pdf(
                data=export_data,
                columns=columns,
                filename=filename,
                title="مدفوعات الموردين",
                parent=self,
                summary=summary_data,
                date_range=(start_date, end_date)
            )
            if ok:
                MessageDialog.info(self, "نجاح", "تم التصدير بنجاح")
        except ExportError as e:
            MessageDialog.error(self, "خطأ", e.message)
        except Exception as e:
            MessageDialog.error(self, "خطأ", f"فشل التصدير: {str(e)}")


class SupplierPaymentDetailsDialog(QDialog):
    """Dialog for displaying supplier payment details."""

    def __init__(self, payment: dict, parent=None):
        super().__init__(parent)
        self.payment = payment or {}
        self.setWindowTitle(f"تفاصيل سند الصرف - {self.payment.get('payment_number', '')}")
        self.setMinimumWidth(650)
        self.setMinimumHeight(520)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QHBoxLayout()
        title = QLabel(f"سند صرف رقم: {self.payment.get('payment_number', '')}")
        title.setProperty("class", "title")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        info_card = Card()
        info_layout = QGridLayout(info_card)
        info_layout.setContentsMargins(20, 20, 20, 20)
        info_layout.setSpacing(12)

        info_layout.addWidget(QLabel("المورد:"), 0, 0)
        supplier_label = QLabel(self.payment.get('supplier_name', ''))
        supplier_label.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(supplier_label, 0, 1)

        info_layout.addWidget(QLabel("التاريخ:"), 1, 0)
        info_layout.addWidget(QLabel(str(self.payment.get('payment_date', ''))), 1, 1)

        currency = self.payment.get('transaction_currency') or 'USD'
        amount = float(self.payment.get('amount', 0) or 0)
        amount_usd = float(self.payment.get('amount_usd', 0) or 0)

        info_layout.addWidget(QLabel("المبلغ:"), 2, 0)
        amount_label = QLabel(self._format_amount_by_currency(amount, currency))
        amount_label.setStyleSheet(f"font-weight: bold; color: {Colors.SUCCESS}; font-size: 16px;")
        info_layout.addWidget(amount_label, 2, 1)

        info_layout.addWidget(QLabel("عرض:"), 2, 2)
        amount_usd_label = QLabel(config.format_usd(amount_usd))
        amount_usd_label.setStyleSheet(f"font-weight: bold; color: {Colors.PRIMARY};")
        info_layout.addWidget(amount_usd_label, 2, 3)

        info_layout.addWidget(QLabel("طريقة الدفع:"), 3, 0)
        info_layout.addWidget(QLabel(self.payment.get('payment_method_display', '')), 3, 1)

        po_number = self.payment.get('purchase_order_number')
        if po_number:
            info_layout.addWidget(QLabel("أمر الشراء:"), 4, 0)
            info_layout.addWidget(QLabel(str(po_number)), 4, 1)

        reference = self.payment.get('reference')
        if reference:
            info_layout.addWidget(QLabel("المرجع:"), 5, 0)
            info_layout.addWidget(QLabel(str(reference)), 5, 1)

        created_by = self.payment.get('created_by_name')
        if created_by:
            info_layout.addWidget(QLabel("أنشئ بواسطة:"), 6, 0)
            info_layout.addWidget(QLabel(str(created_by)), 6, 1)

        notes = self.payment.get('notes')
        if notes:
            info_layout.addWidget(QLabel("ملاحظات:"), 7, 0)
            notes_lbl = QLabel(str(notes))
            notes_lbl.setWordWrap(True)
            info_layout.addWidget(notes_lbl, 7, 1, 1, 3)

        layout.addWidget(info_card)
        layout.addStretch()

        btns = QHBoxLayout()
        btns.addStretch()
        close_btn = QPushButton("إغلاق")
        close_btn.setProperty("class", "secondary")
        close_btn.clicked.connect(self.accept)
        btns.addWidget(close_btn)
        layout.addLayout(btns)

    def _format_amount_by_currency(self, amount: float, currency: str) -> str:
        try:
            if currency == 'USD':
                return config.format_usd(float(amount or 0))
            if currency == 'SYP_NEW':
                return f"{float(amount or 0):,.2f} ل.س جديد"
            return f"{float(amount or 0):,.2f} ل.س"
        except Exception:
            return str(amount)
