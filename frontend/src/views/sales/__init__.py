"""
Sales Views - Customers, Invoices, POS, and Payment Collection

Requirements: 4.1, 4.2 - Error handling for CRUD operations and form submissions
Requirements: 2.1, 2.5, 2.6, 7.1, 7.3 - Payment collection and allocation
Requirements: 1.1, 1.2, 1.4, 1.6, 6.4, 6.5 - Credit invoice support
Requirements: 3.1, 3.2, 3.3 - Unit selection in sales
Requirements: 5.1, 5.9 - Sales returns management
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QFrame, QGridLayout,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QDoubleSpinBox, QScrollArea, QSplitter,
    QComboBox, QDialog, QTextEdit, QDateEdit,
    QAbstractItemView, QStyledItemDelegate, QAbstractSpinBox
)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QFont
from datetime import datetime, timedelta

from ...config import Colors, Fonts, config
from ...widgets.tables import DataTable
from ...widgets.forms import FormDialog
from ...widgets.dialogs import MessageDialog, ConfirmDialog
from ...widgets.cards import Card
from ...widgets.unit_selector import UnitSelectorComboBox
from ...services.api import api, ApiException
from ...utils.error_handler import handle_ui_error

# Import returns components
from .returns import SalesReturnDialog, SalesReturnsView, InvoiceDetailsDialog

# Import receipt printer
from ...printing.receipt import ReceiptPrinter


class _MoneyQtyDelegate(QStyledItemDelegate):
    def __init__(self, decimals: int = 2, minimum: float = 0.0, maximum: float = 999999999.0, parent=None):
        super().__init__(parent)
        self._decimals = decimals
        self._minimum = minimum
        self._maximum = maximum

    def createEditor(self, parent, option, index):
        editor = QDoubleSpinBox(parent)
        editor.setDecimals(self._decimals)
        editor.setRange(self._minimum, self._maximum)
        editor.setButtonSymbols(QAbstractSpinBox.NoButtons)
        editor.setMinimumHeight(30)
        editor.setAlignment(Qt.AlignCenter)
        editor.setKeyboardTracking(False)
        editor.setStyleSheet(
            f"background-color: {Colors.INPUT_BG_LIGHT}; border: 1px solid {Colors.INPUT_BORDER_LIGHT}; border-radius: 6px; padding: 4px 8px;"
        )
        return editor

    def setEditorData(self, editor, index):
        value = index.data(Qt.UserRole)
        if value is None:
            try:
                value = float(str(index.data(Qt.DisplayRole)).replace(',', '').strip() or 0)
            except Exception:
                value = 0
        editor.setValue(float(value))

    def setModelData(self, editor, model, index):
        value = float(editor.value())
        model.setData(index, value, Qt.UserRole)
        model.setData(index, f"{value:,.2f}", Qt.DisplayRole)


class CustomersView(QWidget):
    """
    Customers management view.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize customers view UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("إدارة العملاء")
        title.setProperty("class", "title")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)
        
        # Customers table
        columns = [
            {'key': 'code', 'label': 'كود العميل', 'type': 'text'},
            {'key': 'name', 'label': 'اسم العميل', 'type': 'text'},
            {'key': 'phone', 'label': 'رقم الهاتف', 'type': 'text'},
            {'key': 'mobile', 'label': 'رقم الجوال', 'type': 'text'},
            {'key': 'current_balance_usd', 'label': 'الرصيد', 'type': 'currency'},
        ]
        
        self.table = DataTable(columns)
        self.table.add_btn.clicked.connect(self.add_customer)
        self.table.action_clicked.connect(self.on_action)
        self.table.row_double_clicked.connect(self.edit_customer)
        
        layout.addWidget(self.table)

    @handle_ui_error
    def refresh(self):
        """Refresh customers data from API."""
        response = api.get_customers()
        if isinstance(response, dict) and 'results' in response:
            customers = response['results']
        else:
            customers = response if isinstance(response, list) else []
        self.table.set_data(customers)
        
    def add_customer(self):
        """Add new customer."""
        fields = [
            {'key': 'name', 'label': 'اسم العميل', 'required': True},
            {'key': 'name_en', 'label': 'الاسم بالإنجليزية'},
            {'key': 'customer_type', 'label': 'نوع العميل', 'type': 'select', 'options': [
                {'value': 'individual', 'label': 'فرد'},
                {'value': 'company', 'label': 'شركة'},
                {'value': 'government', 'label': 'حكومي'},
            ]},
            {'key': 'phone', 'label': 'رقم الهاتف'},
            {'key': 'mobile', 'label': 'رقم الجوال'},
            {'key': 'email', 'label': 'البريد الإلكتروني'},
            {'key': 'address', 'label': 'العنوان', 'type': 'textarea'},
            {'key': 'credit_limit', 'label': 'حد الائتمان', 'type': 'number'},
            {'key': 'tax_number', 'label': 'الرقم الضريبي'},
        ]
        
        dialog = FormDialog("إضافة عميل جديد", fields, parent=self)
        dialog.saved.connect(self.save_customer)
        dialog.exec()
    
    def edit_customer(self, row: int, data: dict):
        """Edit existing customer."""
        fields = [
            {'key': 'name', 'label': 'اسم العميل', 'required': True},
            {'key': 'name_en', 'label': 'الاسم بالإنجليزية'},
            {'key': 'customer_type', 'label': 'نوع العميل', 'type': 'select', 'options': [
                {'value': 'individual', 'label': 'فرد'},
                {'value': 'company', 'label': 'شركة'},
                {'value': 'government', 'label': 'حكومي'},
            ]},
            {'key': 'phone', 'label': 'رقم الهاتف'},
            {'key': 'mobile', 'label': 'رقم الجوال'},
            {'key': 'email', 'label': 'البريد الإلكتروني'},
            {'key': 'address', 'label': 'العنوان', 'type': 'textarea'},
            {'key': 'credit_limit', 'label': 'حد الائتمان', 'type': 'number'},
            {'key': 'tax_number', 'label': 'الرقم الضريبي'},
        ]
        
        dialog = FormDialog("تعديل العميل", fields, data, parent=self)
        dialog.saved.connect(lambda d: self.update_customer(data.get('id'), d))
        dialog.exec()
        
    @handle_ui_error
    def save_customer(self, data: dict):
        """Save customer to API."""
        valid_fields = [
            'name', 'name_en', 'customer_type', 'phone', 'mobile', 'email',
            'address', 'city', 'region', 'postal_code', 'country',
            'credit_limit', 'payment_terms', 'discount_percent',
            'tax_number', 'commercial_register', 'contact_person',
            'opening_balance', 'notes', 'salesperson', 'is_active'
        ]
        create_data = {k: v for k, v in data.items() if k in valid_fields and v is not None and v != ''}
        
        api.create_customer(create_data)
        MessageDialog.success(self, "نجاح", "تم إضافة العميل بنجاح")
        self.refresh()
    
    @handle_ui_error
    def update_customer(self, customer_id: int, data: dict):
        """Update customer via API."""
        editable_fields = [
            'name', 'name_en', 'customer_type', 'phone', 'mobile', 'email',
            'address', 'city', 'region', 'postal_code', 'country',
            'credit_limit', 'payment_terms', 'discount_percent',
            'tax_number', 'commercial_register', 'contact_person',
            'notes', 'salesperson', 'is_active'
        ]
        update_data = {k: v for k, v in data.items() if k in editable_fields and v is not None}
        
        api.update_customer(customer_id, update_data)
        MessageDialog.success(self, "نجاح", "تم تحديث العميل بنجاح")
        self.refresh()
        
    def on_action(self, action: str, row: int, data: dict):
        """Handle table action."""
        if action == 'edit':
            self.edit_customer(row, data)
        elif action == 'delete':
            self.delete_customer(data)
    
    @handle_ui_error
    def delete_customer(self, data: dict):
        """
        Delete customer via API.
        
        Requirements: 1.4, 1.5 - Delete with confirmation and handle deletion protection
        """
        dialog = ConfirmDialog(
            "حذف العميل",
            f"هل أنت متأكد من حذف العميل '{data.get('name')}'؟",
            parent=self
        )
        if dialog.exec():
            try:
                api.delete_customer(data.get('id'))
                MessageDialog.success(self, "نجاح", "تم حذف العميل بنجاح")
                self.refresh()
            except ApiException as e:
                # Handle deletion protection error
                if e.error_code == 'DELETION_PROTECTED' or 'فواتير مستحقة' in str(e):
                    MessageDialog.error(
                        self, 
                        "لا يمكن الحذف", 
                        "لا يمكن حذف هذا العميل لوجود فواتير مستحقة. يرجى تسوية الفواتير أولاً."
                    )
                else:
                    raise


class InvoicesView(QWidget):
    """
    Invoices management view.
    
    Requirements: 1.1, 1.2, 1.3, 1.4 - Invoice creation and management
    Requirements: 4.2 - Display full invoice with items on double-click
    Requirements: 4.4 - Cancel action for confirmed invoices
    Requirements: 4.6 - Filtering by status, date range, and customer
    Requirements: 5.1 - Create Return action for confirmed/paid invoices
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.customers_cache = []
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize invoices view UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("الفواتير")
        title.setProperty("class", "title")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)
        
        # Requirements: 4.6 - Filters section
        filters_frame = QFrame()
        filters_frame.setStyleSheet(f"background-color: {Colors.LIGHT_BG}; border-radius: 8px; padding: 12px;")
        filters_layout = QHBoxLayout(filters_frame)
        filters_layout.setSpacing(16)
        
        # Status filter dropdown
        filters_layout.addWidget(QLabel("الحالة:"))
        self.status_filter = QComboBox()
        self.status_filter.addItem("الكل", "")
        self.status_filter.addItem("مسودة", "draft")
        self.status_filter.addItem("مؤكدة", "confirmed")
        self.status_filter.addItem("مدفوعة", "paid")
        self.status_filter.addItem("مدفوعة جزئياً", "partial")
        self.status_filter.addItem("ملغاة", "cancelled")
        self.status_filter.setMinimumWidth(120)
        filters_layout.addWidget(self.status_filter)
        
        # Date range filter
        filters_layout.addWidget(QLabel("من:"))
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.date_from.setMaximumWidth(130)
        filters_layout.addWidget(self.date_from)
        
        filters_layout.addWidget(QLabel("إلى:"))
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setMaximumWidth(130)
        filters_layout.addWidget(self.date_to)
        
        # Customer filter
        filters_layout.addWidget(QLabel("العميل:"))
        self.customer_filter = QComboBox()
        self.customer_filter.addItem("الكل", "")
        self.customer_filter.setMinimumWidth(180)
        self.customer_filter.setEditable(True)
        self.customer_filter.setInsertPolicy(QComboBox.NoInsert)
        filters_layout.addWidget(self.customer_filter)
        
        # Apply filter button
        filter_btn = QPushButton("🔍 بحث")
        filter_btn.setProperty("class", "primary")
        filter_btn.clicked.connect(self.apply_filters)
        filters_layout.addWidget(filter_btn)
        
        # Clear filters button
        clear_btn = QPushButton("مسح")
        clear_btn.setProperty("class", "secondary")
        clear_btn.clicked.connect(self.clear_filters)
        filters_layout.addWidget(clear_btn)
        
        filters_layout.addStretch()
        layout.addWidget(filters_frame)
        
        # Invoices table with view and return actions
        columns = [
            {'key': 'invoice_number', 'label': 'رقم الفاتورة', 'type': 'text'},
            {'key': 'customer_name', 'label': 'العميل', 'type': 'text'},
            {'key': 'invoice_date', 'label': 'التاريخ', 'type': 'date'},
            {'key': 'total_amount_usd', 'label': 'المبلغ', 'type': 'currency'},
            {'key': 'remaining_amount_usd', 'label': 'المتبقي', 'type': 'currency'},
            {'key': 'transaction_currency_display', 'label': 'العملة', 'type': 'text'},
            {'key': 'status_display', 'label': 'الحالة', 'type': 'text'},
        ]
        
        # Requirements: 5.1 - Add return action for invoices
        self.table = DataTable(columns, actions=['view'])
        self.table.add_btn.setText("➕ فاتورة جديدة")
        # Requirements: 1.1 - Connect add button to open form dialog
        self.table.add_btn.clicked.connect(self.add_invoice)
        self.table.action_clicked.connect(self.on_action)
        self.table.row_double_clicked.connect(self.view_invoice_details)
        self.table.page_changed.connect(self.on_page_changed)
        self.table.sort_changed.connect(self.on_sort_changed)
        
        layout.addWidget(self.table)
    
    def add_invoice(self):
        """
        Open dialog to create new invoice.
        
        Requirements: 1.1 - WHEN a user clicks the "فاتورة جديدة" button 
        THEN THE InvoicesView SHALL display a form dialog for entering invoice details
        """
        dialog = InvoiceFormDialog(parent=self)
        dialog.saved.connect(self.save_invoice)
        dialog.print_requested.connect(self.save_and_print_invoice)
        dialog.exec()
    
    @handle_ui_error
    def save_invoice(self, data: dict):
        """
        Save invoice via API.
        
        Requirements: 1.2 - WHEN a user submits valid invoice data 
        THEN THE InvoicesView SHALL send the data to the API and create the invoice
        Requirements: 1.3 - WHEN an invoice is successfully created 
        THEN THE InvoicesView SHALL refresh the invoices list and show a success message
        Requirements: 1.4 - IF an error occurs during invoice creation 
        THEN THE InvoicesView SHALL display an error message to the user
        """
        try:
            result = api.create_invoice(data)
            MessageDialog.success(self, "نجاح", "تم إنشاء الفاتورة بنجاح")
            self.refresh()
        except ApiException as e:
            MessageDialog.error(self, "خطأ", str(e))

    @handle_ui_error
    def save_and_print_invoice(self, data: dict):
        try:
            result = api.create_invoice(data)
            MessageDialog.success(self, "نجاح", "تم إنشاء الفاتورة بنجاح")
            self.refresh()

            try:
                printer = ReceiptPrinter()
                print_result = printer.print_receipt(result)
                if print_result is True:
                    MessageDialog.success(self, "نجاح", "تم إرسال الفاتورة للطباعة")
                elif isinstance(print_result, str):
                    MessageDialog.info(self, "معلومات", f"تم حفظ الفاتورة في ملف: {print_result}")
            except Exception as e:
                MessageDialog.error(self, "خطأ في الطباعة", f"فشل في طباعة الفاتورة: {str(e)}")
        except ApiException as e:
            MessageDialog.error(self, "خطأ", str(e))
        
    @handle_ui_error
    def refresh(self):
        """Refresh invoices data from API."""
        # Load customers for filter dropdown
        self._load_customers()
        
        # Build params from filters
        params = self._build_params()
        
        response = api.get_invoices(params)
        if isinstance(response, dict):
            invoices = response.get('results', [])
            total = response.get('count', len(invoices))
        else:
            invoices = response if isinstance(response, list) else []
            total = len(invoices)
        
        for inv in invoices:
            cur = inv.get('transaction_currency')
            if cur == 'USD':
                inv['transaction_currency_display'] = 'USD'
            elif cur == 'SYP_NEW':
                inv['transaction_currency_display'] = 'ل.س جديد'
            elif cur == 'SYP_OLD':
                inv['transaction_currency_display'] = 'ل.س قديم'
            else:
                inv['transaction_currency_display'] = str(cur or '')

        self.table.set_data(invoices, total)
    
    def _load_customers(self):
        """Load customers for filter dropdown."""
        try:
            response = api.get_customers()
            if isinstance(response, dict) and 'results' in response:
                self.customers_cache = response['results']
            else:
                self.customers_cache = response if isinstance(response, list) else []
            
            # Update customer filter combo (preserve current selection)
            current_customer = self.customer_filter.currentData()
            self.customer_filter.clear()
            self.customer_filter.addItem("الكل", "")
            for customer in self.customers_cache:
                display_text = f"{customer.get('name', '')} ({customer.get('code', '')})"
                self.customer_filter.addItem(display_text, customer.get('id'))
            
            # Restore selection if possible
            if current_customer:
                for i in range(self.customer_filter.count()):
                    if self.customer_filter.itemData(i) == current_customer:
                        self.customer_filter.setCurrentIndex(i)
                        break
        except ApiException:
            pass  # Silently fail - customers will just not be loaded
    
    def _build_params(self) -> dict:
        """Build API parameters from filters."""
        params = self.table.get_pagination_params()
        params.update(self.table.get_sort_params())
        
        # Status filter
        status = self.status_filter.currentData()
        if status:
            params['status'] = status
        
        # Date range
        date_from = self.date_from.date().toString('yyyy-MM-dd')
        date_to = self.date_to.date().toString('yyyy-MM-dd')
        params['invoice_date__gte'] = date_from
        params['invoice_date__lte'] = date_to
        
        # Customer filter
        customer_id = self.customer_filter.currentData()
        if customer_id:
            params['customer'] = customer_id
        
        return params
    
    def apply_filters(self):
        """Apply filters and refresh."""
        self.table.current_page = 1
        self.refresh()
    
    def clear_filters(self):
        """Clear all filters."""
        self.status_filter.setCurrentIndex(0)
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.date_to.setDate(QDate.currentDate())
        self.customer_filter.setCurrentIndex(0)
        self.table.current_page = 1
        self.refresh()
    
    def on_page_changed(self, page: int, page_size: int):
        """Handle page change."""
        self.refresh()
    
    def on_sort_changed(self, column: str, order: str):
        """Handle sort change."""
        self.refresh()
    
    def on_action(self, action: str, row: int, data: dict):
        """Handle table action."""
        if action == 'view':
            self.view_invoice_details(row, data)
        elif action == 'return':
            self.create_return(row, data)
    
    @handle_ui_error
    def view_invoice_details(self, row: int, data: dict):
        """
        View invoice details.
        
        Requirements: 4.2 - Display full invoice with items on double-click
        """
        invoice_id = data.get('id')
        if invoice_id:
            try:
                invoice = api.get_invoice(invoice_id)
                # Show invoice details dialog with return and cancel options
                dialog = InvoiceDetailsDialog(invoice, parent=self)
                dialog.return_requested.connect(self.create_return_from_invoice)
                dialog.cancel_requested.connect(self.cancel_invoice_from_dialog)
                dialog.exec()
            except ApiException as e:
                MessageDialog.error(self, "خطأ", f"فشل في تحميل تفاصيل الفاتورة: {str(e)}")
    
    @handle_ui_error
    def create_return(self, row: int, data: dict):
        """
        Create a sales return for an invoice.
        
        Requirements: 5.1 - WHEN a user selects a confirmed/paid invoice 
        THEN THE Desktop_App SHALL enable a "Create Return" action
        """
        invoice_id = data.get('id')
        status = data.get('status', '')
        
        # Requirements: 5.1 - Only allow returns for confirmed/paid/partial invoices
        if status not in ['confirmed', 'paid', 'partial']:
            MessageDialog.warning(
                self, 
                "غير مسموح", 
                "لا يمكن إنشاء مرتجع إلا للفواتير المؤكدة أو المدفوعة"
            )
            return
        
        try:
            # Get full invoice details with items
            invoice = api.get_invoice(invoice_id)
            self._open_return_dialog(invoice)
        except ApiException as e:
            MessageDialog.error(self, "خطأ", f"فشل في تحميل بيانات الفاتورة: {str(e)}")
    
    def create_return_from_invoice(self, invoice: dict):
        """Create return from invoice details dialog."""
        invoice_id = invoice.get('id') if isinstance(invoice, dict) else None
        if invoice_id:
            try:
                invoice = api.get_invoice(invoice_id)
            except ApiException:
                pass
        self._open_return_dialog(invoice)
    
    def _open_return_dialog(self, invoice: dict):
        """Open the sales return dialog."""
        from .returns import SalesReturnDialog
        
        dialog = SalesReturnDialog(invoice, parent=self)
        dialog.saved.connect(lambda data: self._save_return(invoice.get('id'), data))
        dialog.exec()
    
    @handle_ui_error
    def _save_return(self, invoice_id: int, data: dict):
        """
        Save the sales return via API.
        
        Requirements: 5.1 - Call API and refresh on success
        """
        try:
            result = api.create_sales_return(invoice_id, data)
            MessageDialog.success(
                self, 
                "نجاح", 
                f"تم إنشاء المرتجع رقم {result.get('return_number', '')} بنجاح"
            )
            self.refresh()
        except ApiException as e:
            MessageDialog.error(self, "خطأ", f"فشل في إنشاء المرتجع: {str(e)}")
    
    def cancel_invoice_from_dialog(self, invoice: dict):
        """
        Handle cancel request from invoice details dialog.
        
        Requirements: 4.4 - Cancel action for confirmed invoices
        """
        self._show_cancel_dialog(invoice)
    
    def _show_cancel_dialog(self, invoice: dict):
        """
        Show cancel confirmation dialog with reason input.
        
        Requirements: 4.4 - Show confirmation with reason input
        """
        dialog = InvoiceCancelDialog(invoice, parent=self)
        dialog.confirmed.connect(lambda reason: self._cancel_invoice(invoice.get('id'), reason))
        dialog.exec()
    
    @handle_ui_error
    def _cancel_invoice(self, invoice_id: int, reason: str):
        """
        Cancel invoice via API.
        
        Requirements: 4.4, 4.5 - Call cancel API and refresh
        """
        try:
            result = api.cancel_invoice(invoice_id, reason)
            MessageDialog.success(
                self, 
                "نجاح", 
                f"تم إلغاء الفاتورة بنجاح"
            )
            self.refresh()
        except ApiException as e:
            MessageDialog.error(self, "خطأ", f"فشل في إلغاء الفاتورة: {str(e)}")


class InvoiceCancelDialog(QDialog):
    """
    Dialog for confirming invoice cancellation with reason input.
    
    Requirements: 4.4 - Show confirmation with reason input
    """
    
    confirmed = Signal(str)  # Emits the cancellation reason
    
    def __init__(self, invoice: dict, parent=None):
        super().__init__(parent)
        self.invoice = invoice
        
        self.setWindowTitle("إلغاء الفاتورة")
        self.setMinimumWidth(450)
        self.setup_ui()
    
    def setup_ui(self):
        """Initialize dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Warning icon and title
        header = QHBoxLayout()
        icon = QLabel("⚠️")
        icon.setFont(QFont(Fonts.FAMILY_AR, 36))
        header.addWidget(icon)
        
        title = QLabel("تأكيد إلغاء الفاتورة")
        title.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_H2, QFont.Bold))
        title.setStyleSheet(f"color: {Colors.WARNING};")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)
        
        # Invoice info
        info_frame = QFrame()
        info_frame.setStyleSheet(f"background-color: {Colors.LIGHT_BG}; border-radius: 8px; padding: 12px;")
        info_layout = QVBoxLayout(info_frame)
        info_layout.setSpacing(8)
        
        info_layout.addWidget(QLabel(f"رقم الفاتورة: {self.invoice.get('invoice_number', '')}"))
        info_layout.addWidget(QLabel(f"العميل: {self.invoice.get('customer_name', '')}"))
        total = float(self.invoice.get('total_amount_usd', self.invoice.get('total_amount', 0)) or 0)
        info_layout.addWidget(QLabel(f"المبلغ: {config.format_usd(total)}"))
        
        layout.addWidget(info_frame)
        
        # Warning message
        warning_label = QLabel(
            "⚠️ سيتم إلغاء الفاتورة وإرجاع المخزون وتعديل رصيد العميل.\n"
            "هذه العملية لا يمكن التراجع عنها."
        )
        warning_label.setStyleSheet(f"color: {Colors.DANGER}; font-weight: bold;")
        warning_label.setWordWrap(True)
        layout.addWidget(warning_label)
        
        # Reason input
        reason_label = QLabel("سبب الإلغاء (مطلوب):")
        reason_label.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_BODY))
        layout.addWidget(reason_label)
        
        self.reason_input = QTextEdit()
        self.reason_input.setPlaceholderText("أدخل سبب إلغاء الفاتورة...")
        self.reason_input.setMaximumHeight(100)
        layout.addWidget(self.reason_input)
        
        # Error label
        self.error_label = QLabel()
        self.error_label.setStyleSheet(f"color: {Colors.DANGER};")
        self.error_label.setVisible(False)
        layout.addWidget(self.error_label)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        cancel_btn = QPushButton("تراجع")
        cancel_btn.setProperty("class", "secondary")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        confirm_btn = QPushButton("تأكيد الإلغاء")
        confirm_btn.setProperty("class", "danger")
        confirm_btn.clicked.connect(self.confirm)
        buttons_layout.addWidget(confirm_btn)
        
        layout.addLayout(buttons_layout)
    
    def confirm(self):
        """Validate and confirm cancellation."""
        reason = self.reason_input.toPlainText().strip()
        
        if not reason:
            self.error_label.setText("يجب إدخال سبب الإلغاء")
            self.error_label.setVisible(True)
            return
        
        if len(reason) < 5:
            self.error_label.setText("سبب الإلغاء قصير جداً (5 أحرف على الأقل)")
            self.error_label.setVisible(True)
            return
        
        self.confirmed.emit(reason)
        self.accept()


class POSView(QWidget):
    """
    Point of Sale view for quick sales.
    
    Requirements: 1.1, 1.6 - Credit invoice support with customer selection
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cart_items = []
        self.products_cache = []
        self.customers_cache = []
        self.selected_customer = None
        self.default_warehouse = None
        self.last_completed_invoice = None  # Requirements: 4.1 - Store last invoice for printing
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize POS view UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Left side: Products search and grid
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(16)
        
        # Search bar
        search_layout = QHBoxLayout()
        
        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("🔍 البحث بالباركود أو اسم المنتج...")
        self.barcode_input.returnPressed.connect(self.search_product)
        search_layout.addWidget(self.barcode_input)
        
        left_layout.addLayout(search_layout)
        
        # Products grid (placeholder)
        products_scroll = QScrollArea()
        products_scroll.setWidgetResizable(True)
        products_scroll.setStyleSheet("border: none;")
        
        products_widget = QWidget()
        self.products_grid = QGridLayout(products_widget)
        self.products_grid.setSpacing(12)
        
        products_scroll.setWidget(products_widget)
        left_layout.addWidget(products_scroll)
        
        layout.addWidget(left_panel, 2)
        
        # Right side: Cart and checkout
        right_panel = Card()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(20, 20, 20, 20)
        right_layout.setSpacing(16)
        
        # Cart header
        cart_header = QHBoxLayout()
        cart_title = QLabel("🛒 سلة المشتريات")
        cart_title.setProperty("class", "h2")
        cart_header.addWidget(cart_title)
        
        clear_btn = QPushButton("مسح")
        clear_btn.setStyleSheet(f"color: {Colors.DANGER}; background: transparent; border: none; font-weight: bold;")
        clear_btn.clicked.connect(self.clear_cart)
        cart_header.addWidget(clear_btn)
        
        right_layout.addLayout(cart_header)
        
        # Customer selection section (for credit sales)
        # Requirements: 1.1, 1.6 - Customer selection for credit invoices
        customer_frame = QFrame()
        customer_frame.setStyleSheet(f"background-color: {Colors.LIGHT_BG}; border-radius: 8px; padding: 8px;")
        customer_layout = QVBoxLayout(customer_frame)
        customer_layout.setContentsMargins(12, 12, 12, 12)
        customer_layout.setSpacing(8)
        
        customer_header = QHBoxLayout()
        customer_label = QLabel("👤 العميل:")
        customer_label.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_BODY))
        customer_header.addWidget(customer_label)
        customer_header.addStretch()
        customer_layout.addLayout(customer_header)
        
        self.customer_combo = QComboBox()
        self.customer_combo.setPlaceholderText("اختر العميل...")
        self.customer_combo.currentIndexChanged.connect(self.on_customer_changed)
        customer_layout.addWidget(self.customer_combo)
        
        # Customer credit info display
        # Requirements: 1.6 - Display customer balance and available credit
        self.customer_info_frame = QFrame()
        self.customer_info_frame.setVisible(False)
        customer_info_layout = QVBoxLayout(self.customer_info_frame)
        customer_info_layout.setContentsMargins(0, 8, 0, 0)
        customer_info_layout.setSpacing(4)
        
        # Current balance row
        balance_row = QHBoxLayout()
        balance_row.addWidget(QLabel("الرصيد الحالي:"))
        self.balance_label = QLabel(config.format_usd(0))
        self.balance_label.setStyleSheet(f"font-weight: bold;")
        balance_row.addWidget(self.balance_label)
        balance_row.addStretch()
        customer_info_layout.addLayout(balance_row)
        
        # Credit limit row
        limit_row = QHBoxLayout()
        limit_row.addWidget(QLabel("حد الائتمان:"))
        self.credit_limit_label = QLabel(config.format_usd(0))
        self.credit_limit_label.setStyleSheet(f"font-weight: bold;")
        limit_row.addWidget(self.credit_limit_label)
        limit_row.addStretch()
        customer_info_layout.addLayout(limit_row)
        
        # Available credit row
        available_row = QHBoxLayout()
        available_row.addWidget(QLabel("الائتمان المتاح:"))
        self.available_credit_label = QLabel(config.format_usd(0))
        self.available_credit_label.setStyleSheet(f"font-weight: bold; color: {Colors.SUCCESS};")
        available_row.addWidget(self.available_credit_label)
        available_row.addStretch()
        customer_info_layout.addLayout(available_row)
        
        # Credit warning label
        self.credit_warning_label = QLabel()
        self.credit_warning_label.setStyleSheet(f"color: {Colors.WARNING}; font-weight: bold;")
        self.credit_warning_label.setVisible(False)
        customer_info_layout.addWidget(self.credit_warning_label)
        
        customer_layout.addWidget(self.customer_info_frame)
        
        # Due date display (for credit sales)
        # Requirements: 1.2 - Display due date based on payment terms
        self.due_date_frame = QFrame()
        self.due_date_frame.setVisible(False)
        due_date_layout = QHBoxLayout(self.due_date_frame)
        due_date_layout.setContentsMargins(0, 8, 0, 0)
        due_date_layout.addWidget(QLabel("📅 تاريخ الاستحقاق:"))
        self.due_date_label = QLabel("")
        self.due_date_label.setStyleSheet(f"font-weight: bold; color: {Colors.PRIMARY};")
        due_date_layout.addWidget(self.due_date_label)
        due_date_layout.addStretch()
        customer_layout.addWidget(self.due_date_frame)
        
        right_layout.addWidget(customer_frame)
        
        # Cart items table
        self.cart_table = QTableWidget()
        self.cart_table.setColumnCount(4)
        self.cart_table.setHorizontalHeaderLabels(['المنتج', 'الكمية', 'السعر', 'الإجمالي'])
        self.cart_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.cart_table.verticalHeader().setVisible(False)
        self.cart_table.setSelectionBehavior(QTableWidget.SelectRows)
        right_layout.addWidget(self.cart_table)
        
        # Totals
        totals_frame = QFrame()
        totals_layout = QVBoxLayout(totals_frame)
        totals_layout.setSpacing(8)
        
        # Subtotal
        subtotal_row = QHBoxLayout()
        subtotal_row.addWidget(QLabel("المجموع الفرعي:"))
        self.subtotal_label = QLabel(config.format_usd(0))
        self.subtotal_label.setProperty("class", "subtitle")
        subtotal_row.addWidget(self.subtotal_label)
        totals_layout.addLayout(subtotal_row)
        
        # Tax
        tax_row = QHBoxLayout()
        tax_row.addWidget(QLabel("الضريبة:"))
        self.tax_label = QLabel(config.format_usd(0))
        self.tax_label.setProperty("class", "subtitle")
        tax_row.addWidget(self.tax_label)
        totals_layout.addLayout(tax_row)
        
        # Total
        total_row = QHBoxLayout()
        total_lbl = QLabel("الإجمالي:")
        total_lbl.setProperty("class", "h2")
        total_row.addWidget(total_lbl)
        self.total_label = QLabel(config.format_usd(0))
        self.total_label.setProperty("class", "title")
        self.total_label.setStyleSheet(f"color: {Colors.PRIMARY};")
        total_row.addWidget(self.total_label)
        totals_layout.addLayout(total_row)
        
        right_layout.addWidget(totals_frame)
        
        # Action buttons
        actions_layout = QGridLayout()
        actions_layout.setSpacing(8)
        
        cash_btn = QPushButton("💵 نقداً")
        cash_btn.setProperty("class", "success")
        cash_btn.setMinimumHeight(60)
        cash_btn.setProperty("style", "large")
        cash_btn.clicked.connect(lambda: self.checkout('cash'))
        actions_layout.addWidget(cash_btn, 0, 0)
        
        card_btn = QPushButton("💳 بطاقة")
        card_btn.setProperty("class", "primary")
        card_btn.setMinimumHeight(60)
        card_btn.setProperty("style", "large")
        card_btn.clicked.connect(lambda: self.checkout('card'))
        actions_layout.addWidget(card_btn, 0, 1)
        
        credit_btn = QPushButton("📝 آجل")
        credit_btn.setProperty("class", "secondary")
        credit_btn.setMinimumHeight(60)
        credit_btn.setProperty("style", "large")
        credit_btn.clicked.connect(lambda: self.checkout('credit'))
        actions_layout.addWidget(credit_btn, 1, 0)
        
        print_btn = QPushButton("🖨️ طباعة")
        print_btn.setProperty("class", "secondary")
        print_btn.setMinimumHeight(60)
        print_btn.setProperty("style", "large")
        print_btn.clicked.connect(self.print_receipt)  # Requirements: 3.1 - Connect print button
        actions_layout.addWidget(print_btn, 1, 1)
        
        right_layout.addLayout(actions_layout)
        
        layout.addWidget(right_panel, 1)

    def on_customer_changed(self, index: int):
        """
        Handle customer selection change.
        
        Requirements: 1.6 - Display customer balance and available credit
        Requirements: 1.2 - Calculate and display due date
        """
        if index <= 0:  # No customer selected (placeholder)
            self.selected_customer = None
            self.customer_info_frame.setVisible(False)
            self.due_date_frame.setVisible(False)
            self.credit_warning_label.setVisible(False)
            return
        
        customer_id = self.customer_combo.currentData()
        if not customer_id:
            return
        
        # Find customer in cache
        self.selected_customer = None
        for customer in self.customers_cache:
            if customer.get('id') == customer_id:
                self.selected_customer = customer
                break
        
        if not self.selected_customer:
            return
        
        # Update customer info display (USD base)
        current_balance_usd = float(self.selected_customer.get('current_balance_usd', self.selected_customer.get('current_balance', 0)) or 0)
        credit_limit_usd = float(self.selected_customer.get('credit_limit_usd', self.selected_customer.get('credit_limit', 0)) or 0)
        available_credit_usd = float(self.selected_customer.get('available_credit_usd', (credit_limit_usd - current_balance_usd)) or 0)
        
        self.balance_label.setText(config.format_usd(current_balance_usd))
        self.credit_limit_label.setText(config.format_usd(credit_limit_usd) if credit_limit_usd > 0 else "غير محدد")
        
        if credit_limit_usd > 0:
            self.available_credit_label.setText(config.format_usd(available_credit_usd))
            # Color based on available credit
            if available_credit_usd <= 0:
                self.available_credit_label.setStyleSheet(f"font-weight: bold; color: {Colors.DANGER};")
            elif current_balance_usd >= credit_limit_usd * 0.8:
                self.available_credit_label.setStyleSheet(f"font-weight: bold; color: {Colors.WARNING};")
            else:
                self.available_credit_label.setStyleSheet(f"font-weight: bold; color: {Colors.SUCCESS};")
        else:
            self.available_credit_label.setText("غير محدد")
            self.available_credit_label.setStyleSheet(f"font-weight: bold; color: {Colors.SUCCESS};")
        
        # Show credit warning if applicable
        # Requirements: 1.6 - Show credit limit warning when applicable
        if credit_limit_usd > 0 and current_balance_usd >= credit_limit_usd * 0.8:
            if current_balance_usd >= credit_limit_usd:
                self.credit_warning_label.setText("⚠️ تم تجاوز حد الائتمان!")
                self.credit_warning_label.setStyleSheet(f"color: {Colors.DANGER}; font-weight: bold;")
            else:
                self.credit_warning_label.setText("⚠️ الرصيد يقترب من حد الائتمان")
                self.credit_warning_label.setStyleSheet(f"color: {Colors.WARNING}; font-weight: bold;")
            self.credit_warning_label.setVisible(True)
        else:
            self.credit_warning_label.setVisible(False)
        
        # Calculate and display due date
        # Requirements: 1.2 - Auto-calculate due date based on payment terms
        payment_terms = self.selected_customer.get('payment_terms', 0)
        if payment_terms > 0:
            due_date = datetime.now().date() + timedelta(days=payment_terms)
            self.due_date_label.setText(due_date.strftime('%Y-%m-%d'))
            self.due_date_frame.setVisible(True)
        else:
            self.due_date_frame.setVisible(False)
        
        self.customer_info_frame.setVisible(True)
        
    @handle_ui_error
    def search_product(self):
        """Search product by barcode or name."""
        query = self.barcode_input.text().strip()
        if query:
            # Try barcode search first
            try:
                product = api.get_product_by_barcode(query)
                if product:
                    self.add_to_cart_product(product)
                    self.barcode_input.clear()
                    return
            except ApiException:
                pass  # Fall through to name search
            
            # If barcode not found, search by name
            response = api.get_products({'search': query})
            if isinstance(response, dict) and 'results' in response:
                products = response['results']
            else:
                products = response if isinstance(response, list) else []
            
            if products:
                self.add_to_cart_product(products[0])
                self.barcode_input.clear()
            else:
                MessageDialog.warning(self, "تنبيه", "المنتج غير موجود")
    
    def add_to_cart_product(self, product: dict):
        """Add product to cart."""
        # Check if product already in cart
        for item in self.cart_items:
            if item['product_id'] == product['id']:
                item['quantity'] += 1
                item['total'] = item['quantity'] * item['unit_price']
                self.update_cart_display()
                return
        
        # Add new item
        unit_price = float(product.get('sale_price_usd', product.get('sale_price', 0)) or 0)
        self.cart_items.append({
            'product_id': product['id'],
            'product_name': product['name'],
            'quantity': 1,
            'unit_price': unit_price,
            'total': unit_price,
        })
        self.update_cart_display()
        
    def add_to_cart(self, product_idx: int):
        """Add product to cart by index."""
        if product_idx < len(self.products_cache):
            self.add_to_cart_product(self.products_cache[product_idx])
        
    def clear_cart(self):
        """Clear cart."""
        self.cart_items = []
        self.cart_table.setRowCount(0)
        self.update_totals()
    
    def update_cart_display(self):
        """Update cart table display."""
        self.cart_table.setRowCount(len(self.cart_items))
        for i, item in enumerate(self.cart_items):
            self.cart_table.setItem(i, 0, QTableWidgetItem(item['product_name']))
            self.cart_table.setItem(i, 1, QTableWidgetItem(str(item['quantity'])))
            self.cart_table.setItem(i, 2, QTableWidgetItem(config.format_usd(float(item.get('unit_price', 0) or 0))))
            self.cart_table.setItem(i, 3, QTableWidgetItem(config.format_usd(float(item.get('total', 0) or 0))))
        self.update_totals()
        
    def update_totals(self):
        """
        Update cart totals.
        
        Requirements: 2.1, 2.2 - POS transactions are always tax-free
        Tax is always 0 for POS regardless of global tax settings.
        """
        subtotal = sum(item.get('total', 0) for item in self.cart_items)
        # Requirements: 2.1, 2.2 - Always display tax as 0.00 for POS
        tax = 0
        total = subtotal + tax
        
        self.subtotal_label.setText(config.format_usd(float(subtotal or 0)))
        self.tax_label.setText(config.format_usd(0))  # Always show 0.00 for POS
        self.total_label.setText(config.format_usd(float(total or 0)))
    
    def get_cart_total(self) -> float:
        """Get current cart total."""
        return sum(item.get('total', 0) for item in self.cart_items)

    def checkout(self, payment_method: str):
        """
        Process checkout.
        
        Requirements: 1.1 - Require customer selection for credit invoices
        Requirements: 1.4, 6.4 - Credit limit validation with override option
        """
        if not self.cart_items:
            MessageDialog.warning(self, "تنبيه", "السلة فارغة")
            return
        
        # For credit sales, customer selection is required
        # Requirements: 1.1 - WHEN a user selects "آجل" (credit) as payment type 
        # THEN THE System SHALL require customer selection before proceeding
        if payment_method == 'credit':
            if not self.selected_customer:
                MessageDialog.warning(
                    self, 
                    "تنبيه", 
                    "يجب اختيار العميل للبيع الآجل"
                )
                return
            
            # Validate credit limit
            # Requirements: 1.4, 6.4 - Credit limit validation
            cart_total_usd = float(self.get_cart_total() or 0)
            current_balance_usd = float(self.selected_customer.get('current_balance_usd', self.selected_customer.get('current_balance', 0)) or 0)
            credit_limit_usd = float(self.selected_customer.get('credit_limit_usd', self.selected_customer.get('credit_limit', 0)) or 0)
            
            if credit_limit_usd > 0:
                new_balance_usd = current_balance_usd + cart_total_usd
                
                if new_balance_usd > credit_limit_usd:
                    # Show credit limit override dialog
                    # Requirements: 1.4, 6.4, 6.5 - Override with confirmation
                    dialog = CreditLimitOverrideDialog(
                        customer_name=self.selected_customer.get('name', ''),
                        current_balance=current_balance_usd,
                        credit_limit=credit_limit_usd,
                        requested_amount=cart_total_usd,
                        parent=self
                    )
                    if dialog.exec() == QDialog.Accepted:
                        override_reason = dialog.get_reason()
                        self._create_credit_invoice(override_reason)
                    return
                elif new_balance_usd >= credit_limit_usd * 0.8:
                    # Show warning but allow to proceed
                    if not MessageDialog.confirm(
                        self,
                        "تحذير حد الائتمان",
                        f"الرصيد الجديد ({config.format_usd(new_balance_usd)}) يقترب من حد الائتمان ({config.format_usd(credit_limit_usd)}).\n"
                        "هل تريد المتابعة؟"
                    ):
                        return
            
            self.create_pos_invoice('credit')
        else:
            # For cash/card sales
            self.create_pos_invoice('cash')
    
    def create_pos_invoice(self, payment_method: str, override_reason: str = None):
        """
        Create and confirm invoice via API.
        
        Requirements: 1.2, 1.5, 7.1
        Requirements: 2.1, 2.3 - POS transactions are always tax-free
        """
        # Ensure we have a warehouse
        if not self.default_warehouse:
            MessageDialog.error(self, "خطأ", "لم يتم تحديد المستودع الافتراضي")
            return
        
        # Prepare invoice data
        cart_total = self.get_cart_total()
        invoice_date = datetime.now().date()
        
        invoice_data = {
            'warehouse': self.default_warehouse.get('id'),
            'invoice_type': payment_method,
            'invoice_date': invoice_date.strftime('%Y-%m-%d'),
            'transaction_currency': 'USD',
            'items': [
                {
                    'product': item['product_id'],
                    'quantity': item['quantity'],
                    'unit_price': item['unit_price'],
                    'tax_rate': 0  # Requirements: 2.1, 2.3 - Always 0 for POS transactions
                }
                for item in self.cart_items
            ],
            'confirm': True,
            'paid_amount': float(cart_total) if payment_method == 'cash' else 0,
            'payment_method': 'cash' # Initial payment method
        }
        
        # Customer handling
        if self.selected_customer:
            invoice_data['customer'] = self.selected_customer.get('id')
            if payment_method == 'credit':
                payment_terms = self.selected_customer.get('payment_terms', 0)
                due_date = invoice_date + timedelta(days=payment_terms)
                invoice_data['due_date'] = due_date.strftime('%Y-%m-%d')
        else:
            # For cash sales without customer selection, use default walking customer
            # The API will handle assigning a default customer if none provided
            invoice_data['customer'] = None

        if override_reason:
            invoice_data['override_credit_limit'] = True
            invoice_data['override_reason'] = override_reason
        
        try:
            # Create and confirm invoice in one go
            result = api.create_invoice(invoice_data)
            
            # Requirements: 4.1 - Store last completed invoice for printing
            self.last_completed_invoice = result
            
            # Requirements: 5.1, 5.2 - Open cash drawer for cash payments (silent failure)
            if payment_method == 'cash':
                try:
                    printer = ReceiptPrinter()
                    printer.open_cash_drawer()
                except Exception:
                    # Requirements: 5.2 - Silent failure if cash drawer command fails
                    pass
            
            MessageDialog.success(
                self, 
                "نجاح", 
                f"تم إنشاء الفاتورة رقم {result.get('invoice_number', '')} بنجاح"
            )
            
            # Clear cart and refresh
            self.clear_cart()
            self.refresh()
            
        except ApiException as e:
            MessageDialog.error(self, "خطأ", str(e))
    
    def print_receipt(self):
        """
        Print receipt for the last completed invoice.
        
        Requirements: 3.1 - Print receipt when user clicks print button
        Requirements: 4.1 - Use stored last_completed_invoice data
        Requirements: 4.2 - Show warning if no invoice available
        Requirements: 4.3 - Call ReceiptPrinter with invoice data
        Requirements: 4.4 - Handle print errors gracefully
        """
        # Requirements: 4.2 - Check if last_completed_invoice exists
        if not self.last_completed_invoice:
            MessageDialog.warning(self, "تنبيه", "لا توجد فاتورة للطباعة")
            return
        
        try:
            # Requirements: 4.3 - Call ReceiptPrinter with invoice data
            printer = ReceiptPrinter()
            result = printer.print_receipt(self.last_completed_invoice)
            
            if result is True:
                MessageDialog.success(self, "نجاح", "تم إرسال الفاتورة للطباعة")
            elif isinstance(result, str):
                # Fallback to file - result is the filepath
                MessageDialog.info(self, "معلومات", f"تم حفظ الفاتورة في ملف: {result}")
        except Exception as e:
            # Requirements: 4.4 - Handle print errors gracefully
            MessageDialog.error(self, "خطأ في الطباعة", f"فشل في طباعة الفاتورة: {str(e)}")
    

    @handle_ui_error
    def refresh(self):
        # Load default warehouse
        try:
            self.default_warehouse = api.get_default_warehouse()
        except ApiException:
            self.default_warehouse = None
        
        # Load products
        response = api.get_products()
        if isinstance(response, dict) and 'results' in response:
            self.products_cache = response['results']
        else:
            self.products_cache = response if isinstance(response, list) else []
        
        # Load customers for credit sales
        customers_response = api.get_customers()
        if isinstance(customers_response, dict) and 'results' in customers_response:
            self.customers_cache = customers_response['results']
        else:
            self.customers_cache = customers_response if isinstance(customers_response, list) else []
        
        # Update customer combo
        self.customer_combo.clear()
        self.customer_combo.addItem("اختر العميل...", None)
        for customer in self.customers_cache:
            display_text = f"{customer.get('name', '')} ({customer.get('code', '')})"
            self.customer_combo.addItem(display_text, customer.get('id'))
        
        # Reset customer selection
        self.selected_customer = None
        self.customer_info_frame.setVisible(False)
        self.due_date_frame.setVisible(False)
        
        # Update products grid
        # Clear existing buttons
        while self.products_grid.count():
            item = self.products_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add product buttons
        for i, product in enumerate(self.products_cache[:12]):  # Show first 12
            btn = QPushButton(f"{product['name']}\n{config.format_usd(float(product.get('sale_price_usd', product.get('sale_price', 0)) or 0))}")
            btn.setFixedSize(120, 80)
            btn.clicked.connect(lambda _, idx=i: self.add_to_cart(idx))
            self.products_grid.addWidget(btn, i // 4, i % 4)


class CreditLimitOverrideDialog(QDialog):
    """
    Dialog for credit limit override confirmation.
    
    Requirements: 1.4, 6.4, 6.5 - Credit limit override with reason capture
    """
    
    def __init__(
        self, 
        customer_name: str,
        current_balance: float,
        credit_limit: float,
        requested_amount: float,
        parent=None
    ):
        super().__init__(parent)
        self.customer_name = customer_name
        self.current_balance = current_balance
        self.credit_limit = credit_limit
        self.requested_amount = requested_amount
        self.new_balance = current_balance + requested_amount
        self.override_reason = ""
        
        self.setWindowTitle("تجاوز حد الائتمان")
        self.setMinimumWidth(450)
        self.setup_ui()
    
    def setup_ui(self):
        """Initialize dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Warning icon and title
        header = QHBoxLayout()
        icon = QLabel("⚠️")
        icon.setFont(QFont(Fonts.FAMILY_AR, 36))
        header.addWidget(icon)
        
        title = QLabel("تجاوز حد الائتمان")
        title.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_H2, QFont.Bold))
        title.setStyleSheet(f"color: {Colors.WARNING};")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)
        
        # Customer info
        info_frame = QFrame()
        info_frame.setStyleSheet(f"background-color: {Colors.LIGHT_BG}; border-radius: 8px; padding: 12px;")
        info_layout = QVBoxLayout(info_frame)
        info_layout.setSpacing(8)
        
        info_layout.addWidget(QLabel(f"العميل: {self.customer_name}"))
        info_layout.addWidget(QLabel(f"الرصيد الحالي: {config.format_usd(self.current_balance)}"))
        info_layout.addWidget(QLabel(f"حد الائتمان: {config.format_usd(self.credit_limit)}"))
        info_layout.addWidget(QLabel(f"المبلغ المطلوب: {config.format_usd(self.requested_amount)}"))
        
        new_balance_label = QLabel(f"الرصيد الجديد: {config.format_usd(self.new_balance)}")
        new_balance_label.setStyleSheet(f"color: {Colors.DANGER}; font-weight: bold;")
        info_layout.addWidget(new_balance_label)
        
        excess = self.new_balance - self.credit_limit
        excess_label = QLabel(f"مبلغ التجاوز: {config.format_usd(excess)}")
        excess_label.setStyleSheet(f"color: {Colors.DANGER}; font-weight: bold;")
        info_layout.addWidget(excess_label)
        
        layout.addWidget(info_frame)
        
        # Reason input
        # Requirements: 6.5 - Capture override reason
        reason_label = QLabel("سبب التجاوز (مطلوب):")
        reason_label.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_BODY))
        layout.addWidget(reason_label)
        
        self.reason_input = QTextEdit()
        self.reason_input.setPlaceholderText("أدخل سبب تجاوز حد الائتمان...")
        self.reason_input.setMaximumHeight(100)
        layout.addWidget(self.reason_input)
        
        # Error label
        self.error_label = QLabel()
        self.error_label.setStyleSheet(f"color: {Colors.DANGER};")
        self.error_label.setVisible(False)
        layout.addWidget(self.error_label)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        cancel_btn = QPushButton("إلغاء")
        cancel_btn.setProperty("class", "secondary")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        confirm_btn = QPushButton("تأكيد التجاوز")
        confirm_btn.setProperty("class", "danger")
        confirm_btn.clicked.connect(self.confirm)
        buttons_layout.addWidget(confirm_btn)
        
        layout.addLayout(buttons_layout)
    
    def confirm(self):
        """Validate and confirm override."""
        reason = self.reason_input.toPlainText().strip()
        
        if not reason:
            self.error_label.setText("يجب إدخال سبب التجاوز")
            self.error_label.setVisible(True)
            return
        
        if len(reason) < 10:
            self.error_label.setText("سبب التجاوز قصير جداً (10 أحرف على الأقل)")
            self.error_label.setVisible(True)
            return
        
        self.override_reason = reason
        self.accept()
    
    def get_reason(self) -> str:
        """Get the override reason."""
        return self.override_reason


class InvoiceFormDialog(QDialog):
    """
    Full-screen dialog for creating invoices with modern UI/UX.
    """
    
    saved = Signal(dict)
    print_requested = Signal(dict)
    
    def __init__(self, data=None, parent=None):
        super().__init__(parent)
        self.data = data or {}
        self.items = []
        self._updating_items_table = False
        self._fx_syncing = False
        self.transaction_currency = 'USD'
        self.customers_cache = []
        self.warehouses_cache = []
        self.products_cache = []
        
        self.setWindowTitle("فاتورة مبيعات جديدة")
        # Make it full screen / maximized
        self.setWindowState(Qt.WindowMaximized)
        self.setMinimumSize(1200, 800)
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """Build the redesigned form UI with two columns and cards."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # Header Section
        header_layout = QHBoxLayout()
        title_label = QLabel("إنشاء فاتورة جديدة")
        title_label.setProperty("class", "title")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Quick Actions in header
        self.invoice_type_label = QLabel("نوع الفاتورة:")
        header_layout.addWidget(self.invoice_type_label)
        self.type_combo = QComboBox()
        self.type_combo.addItem("نقدي", "cash")
        self.type_combo.addItem("آجل", "credit")
        self.type_combo.setMinimumWidth(120)
        self.type_combo.currentIndexChanged.connect(self.on_type_changed)
        header_layout.addWidget(self.type_combo)

        self.currency_label = QLabel("العملة:")
        header_layout.addWidget(self.currency_label)
        self.currency_combo = QComboBox()
        self.currency_combo.addItem("USD", "USD")
        self.currency_combo.addItem("الليرة القديمة", "SYP_OLD")
        self.currency_combo.addItem("الليرة الجديدة", "SYP_NEW")
        self.currency_combo.setMinimumWidth(140)
        self.currency_combo.currentIndexChanged.connect(self.on_currency_changed)
        header_layout.addWidget(self.currency_combo)

        self.print_btn = QPushButton("🖨️ طباعة")
        self.print_btn.setProperty("class", "secondary")
        self.print_btn.setMinimumHeight(34)
        self.print_btn.setMinimumWidth(110)
        self.print_btn.clicked.connect(self.request_print)
        header_layout.addWidget(self.print_btn)
        
        main_layout.addLayout(header_layout)

        # Main Content Area: Split into two columns
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)

        # Left Column: Invoice Details and Items
        left_column = QVBoxLayout()
        left_column.setSpacing(20)

        # 1. Invoice Header Info Card (compact layout - Requirements: 3.1, 3.2, 3.3)
        info_card = Card()
        info_card.setMaximumHeight(100)  # Requirement 3.3: max height 100px
        info_card_layout = QVBoxLayout(info_card)
        info_card_layout.setContentsMargins(12, 12, 12, 12)  # Reduced from 20px to 12px
        info_card_layout.setSpacing(8)

        # Single row layout for all fields (Requirement 3.1: compact single-row layout)
        fields_layout = QHBoxLayout()
        fields_layout.setSpacing(12)

        # Customer
        customer_container = QVBoxLayout()
        customer_container.setSpacing(2)
        customer_label = QLabel("العميل *")
        customer_label.setStyleSheet("font-size: 11px;")
        customer_container.addWidget(customer_label)
        self.customer_combo = QComboBox()
        self.customer_combo.setPlaceholderText("اختر العميل...")
        self.customer_combo.setMinimumWidth(180)
        customer_container.addWidget(self.customer_combo)
        fields_layout.addLayout(customer_container)

        # Warehouse
        warehouse_container = QVBoxLayout()
        warehouse_container.setSpacing(2)
        warehouse_label = QLabel("المستودع *")
        warehouse_label.setStyleSheet("font-size: 11px;")
        warehouse_container.addWidget(warehouse_label)
        self.warehouse_combo = QComboBox()
        self.warehouse_combo.setPlaceholderText("اختر المستودع...")
        self.warehouse_combo.setMinimumWidth(150)
        warehouse_container.addWidget(self.warehouse_combo)
        fields_layout.addLayout(warehouse_container)

        # Date
        date_container = QVBoxLayout()
        date_container.setSpacing(2)
        date_label = QLabel("التاريخ *")
        date_label.setStyleSheet("font-size: 11px;")
        date_container.addWidget(date_label)
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setMinimumWidth(120)
        self.date_edit.dateChanged.connect(self.load_fx_for_date)
        date_container.addWidget(self.date_edit)
        fields_layout.addLayout(date_container)

        # Due Date (Initially Hidden)
        self.due_date_container = QWidget()
        due_date_layout = QVBoxLayout(self.due_date_container)
        due_date_layout.setContentsMargins(0, 0, 0, 0)
        due_date_layout.setSpacing(2)
        self.due_date_label = QLabel("الاستحقاق")
        self.due_date_label.setStyleSheet("font-size: 11px;")
        due_date_layout.addWidget(self.due_date_label)
        self.due_date_edit = QDateEdit()
        self.due_date_edit.setCalendarPopup(True)
        self.due_date_edit.setDate(QDate.currentDate().addDays(30))
        self.due_date_edit.setMinimumWidth(120)
        due_date_layout.addWidget(self.due_date_edit)
        fields_layout.addWidget(self.due_date_container)
        
        self.due_date_container.setVisible(False)

        fields_layout.addStretch()
        info_card_layout.addLayout(fields_layout)
        left_column.addWidget(info_card)

        # 2. Items Section Card
        items_card = Card()
        items_card_layout = QVBoxLayout(items_card)
        items_card_layout.setContentsMargins(16, 16, 16, 16)
        items_card_layout.setSpacing(12)

        items_title = QLabel("📦 منتجات الفاتورة")
        items_title.setProperty("class", "h2")
        items_card_layout.addWidget(items_title)

        # Product Entry Section (compact single row - Requirements: 4.1, 4.2, 4.3)
        entry_container = QWidget()
        entry_container.setMaximumHeight(70)  # Requirement 4.3: max height 70px
        entry_container_layout = QVBoxLayout(entry_container)
        entry_container_layout.setContentsMargins(0, 0, 0, 0)
        entry_container_layout.setSpacing(8)  # Requirement 4.2: reduced spacing to 8px

        # Combined single row for barcode and manual selection (Requirement 4.1)
        entry_layout = QHBoxLayout()
        entry_layout.setSpacing(8)  # Requirement 4.2: reduced spacing to 8px

        # Barcode input (compact)
        barcode_label = QLabel("🔍")
        barcode_label.setFont(QFont(Fonts.FAMILY_AR, 14))
        entry_layout.addWidget(barcode_label)
        
        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("باركود...")
        self.barcode_input.setMinimumHeight(36)
        self.barcode_input.setMaximumWidth(150)
        self.barcode_input.setStyleSheet(f"""
            QLineEdit {{
                font-size: 13px;
                padding: 6px 10px;
                border: 2px solid {Colors.PRIMARY};
                border-radius: 6px;
                background-color: {Colors.LIGHT_BG};
            }}
            QLineEdit:focus {{
                border-color: {Colors.SUCCESS};
                background-color: white;
            }}
        """)
        self.barcode_input.returnPressed.connect(self.search_by_barcode)
        entry_layout.addWidget(self.barcode_input)

        # Product combo (manual selection)
        self.product_combo = QComboBox()
        self.product_combo.setPlaceholderText("اختر المنتج...")
        self.product_combo.setMinimumWidth(200)
        self.product_combo.setEditable(True)
        self.product_combo.setInsertPolicy(QComboBox.NoInsert)
        entry_layout.addWidget(self.product_combo, 2)

        # Unit selector - Requirements: 3.1 - Display available units for selected product
        self.unit_selector = UnitSelectorComboBox(price_type='sale')
        self.unit_selector.setMinimumWidth(150)
        self.unit_selector.unit_changed.connect(self.on_unit_changed)
        entry_layout.addWidget(self.unit_selector, 2)

        # Quantity
        self.quantity_spin = QDoubleSpinBox()
        self.quantity_spin.setRange(0.01, 999999)
        self.quantity_spin.setValue(1)
        self.quantity_spin.setPrefix("الكمية: ")
        self.quantity_spin.setMinimumHeight(34)
        entry_layout.addWidget(self.quantity_spin, 1)

        # Price
        self.price_spin = QDoubleSpinBox()
        self.price_spin.setRange(0, 999999999)
        self.price_spin.setPrefix("السعر: ")
        self.price_spin.setMinimumHeight(34)
        entry_layout.addWidget(self.price_spin, 1)

        # Add button
        add_btn = QPushButton("➕ إضافة")
        add_btn.setProperty("class", "primary")
        add_btn.clicked.connect(self.add_item)
        entry_layout.addWidget(add_btn, 1)

        entry_container_layout.addLayout(entry_layout)
        items_card_layout.addWidget(entry_container)

        # Items Table with scroll area (Requirements: 6.1, 6.2, 6.3 - Visual styling)
        # Requirements: 3.1, 3.2 - Add unit column for unit selection display
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(6)
        self.items_table.setHorizontalHeaderLabels(['المنتج', 'الوحدة', 'الكمية', 'السعر', 'الإجمالي', 'حذف'])
        header = self.items_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        header.setSectionResizeMode(5, QHeaderView.Fixed)  # Remove button column - fixed width
        self.items_table.setColumnWidth(2, 120)
        self.items_table.setColumnWidth(3, 140)
        self.items_table.setColumnWidth(4, 140)
        self.items_table.setColumnWidth(5, 50)  # Remove button column width - Requirements: 2.4
        self.items_table.verticalHeader().setVisible(False)
        self.items_table.verticalHeader().setDefaultSectionSize(34)
        self.items_table.setAlternatingRowColors(True)  # Requirement 6.3: Alternating row colors
        self.items_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.items_table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)
        self.items_table.setShowGrid(False)
        self.items_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.items_table.setItemDelegateForColumn(2, _MoneyQtyDelegate(decimals=2, minimum=0.01, maximum=999999, parent=self.items_table))
        self.items_table.setItemDelegateForColumn(3, _MoneyQtyDelegate(decimals=2, minimum=0.0, maximum=999999999, parent=self.items_table))
        self.items_table.itemChanged.connect(self.on_items_table_item_changed)
        # Requirements 6.1, 6.2, 6.3: Enhanced visual styling with distinct border, contrasting header, and alternating rows
        self.items_table.setStyleSheet(f"""
            QTableWidget {{
                border: 1px solid {Colors.LIGHT_BORDER};
                border-radius: 8px;
                background-color: white;
                gridline-color: transparent;
                outline: none;
            }}
            QTableWidget::item {{
                padding: 6px 10px;
                border-bottom: 1px solid {Colors.LIGHT_BORDER};
            }}
            QTableWidget::item:alternate {{
                background-color: {Colors.TABLE_ROW_ALT_LIGHT};
            }}
            QTableWidget::item:hover {{
                background-color: {Colors.TABLE_HOVER_LIGHT};
            }}
            QTableWidget::item:selected {{
                background-color: {Colors.PRIMARY}20;
                color: {Colors.PRIMARY};
            }}
            QHeaderView::section {{
                background-color: {Colors.TABLE_HEADER_LIGHT};
                color: {Colors.LIGHT_TEXT};
                padding: 10px 8px;
                border: none;
                border-bottom: 1px solid {Colors.LIGHT_BORDER};
                font-weight: 700;
                font-size: 12px;
            }}
            QScrollBar:vertical {{
                background: {Colors.LIGHT_BG};
                width: 8px;
                border-radius: 5px;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: {Colors.PRIMARY_LIGHT};
                border-radius: 5px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {Colors.PRIMARY};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
        """)
        self.items_table.setMinimumHeight(220)
        self.items_table.setMaximumHeight(360)
        # Enable vertical scrolling with scrollbar visible when needed
        self.items_table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.items_table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.items_table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        items_card_layout.addWidget(self.items_table, 1)  # Stretch factor of 1 allows expansion

        left_column.addWidget(items_card, 1) # Give items card more priority
        content_layout.addLayout(left_column, 8) # Requirement 5.4: Increased from 7 to 8 for better ratio

        # Right Column: Summary and Notes
        right_column = QVBoxLayout()
        right_column.setSpacing(12)  # Reduced from 20px

        # 3. Summary Card (Requirements: 5.1, 5.2, 5.3, 5.4)
        summary_card = Card()
        summary_card.setFixedWidth(320)  # Requirement 5.3: fixed width 320px
        summary_card_layout = QVBoxLayout(summary_card)
        summary_card_layout.setContentsMargins(16, 16, 16, 16)  # Reduced from 20px to 16px
        summary_card_layout.setSpacing(12)  # Reduced from 20px to 12px

        summary_title = QLabel("💰 ملخص الفاتورة")
        summary_title.setProperty("class", "h2")
        summary_card_layout.addWidget(summary_title)

        # Totals Display (Requirements: 5.1, 5.2 - compact spacing)
        totals_layout = QVBoxLayout()
        totals_layout.setSpacing(8)  # Reduced from 12px to 8px

        def add_total_row(label, value_attr, is_grand=False):
            row = QHBoxLayout()
            lbl = QLabel(label)
            if is_grand:
                lbl.setFont(QFont(Fonts.FAMILY_AR, 16, QFont.Bold))
            else:
                lbl.setProperty("class", "subtitle")
            
            val = QLabel(config.format_usd(0))
            if is_grand:
                val.setFont(QFont(Fonts.FAMILY_AR, 20, QFont.Bold))
                val.setStyleSheet(f"color: {Colors.PRIMARY};")
            else:
                val.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_H3, QFont.Bold))
            
            setattr(self, value_attr, val)
            row.addWidget(lbl)
            row.addStretch()
            row.addWidget(val)
            totals_layout.addLayout(row)

        add_total_row("إجمالي المنتجات:", "subtotal_value")
        add_total_row("الضريبة (0%):", "tax_value")

        discount_row = QHBoxLayout()
        discount_label = QLabel("الخصم:")
        discount_label.setProperty("class", "subtitle")
        discount_row.addWidget(discount_label)
        discount_row.addStretch()

        self.discount_type_combo = QComboBox()
        self.discount_type_combo.addItem("%", "percent")
        self.discount_type_combo.addItem("$", "amount")
        self.discount_type_combo.setFixedWidth(70)
        discount_row.addWidget(self.discount_type_combo)

        self.discount_spin = QDoubleSpinBox()
        self.discount_spin.setDecimals(2)
        self.discount_spin.setRange(0, 100)
        self.discount_spin.setSuffix(" %")
        self.discount_spin.setFixedWidth(120)
        discount_row.addWidget(self.discount_spin)

        totals_layout.addLayout(discount_row)
        
        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet(f"background-color: {Colors.LIGHT_BORDER};")
        totals_layout.addWidget(line)
        
        add_total_row("الإجمالي الكلي:", "total_value", is_grand=True)

        summary_card_layout.addLayout(totals_layout)
        
        # Notes Section (compact)
        notes_label = QLabel("📝 ملاحظات")
        notes_label.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_BODY, QFont.Bold))
        summary_card_layout.addWidget(notes_label)
        
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("أدخل أي ملاحظات إضافية هنا...")
        self.notes_edit.setMinimumHeight(50)  # Reduced from 60px
        self.notes_edit.setMaximumHeight(70)  # Reduced from 80px
        self.notes_edit.setStyleSheet(f"background-color: {Colors.LIGHT_BG}; border: 1px solid {Colors.LIGHT_BORDER}; border-radius: 8px;")
        summary_card_layout.addWidget(self.notes_edit)
        
        # Paid Amount Section (for partial payments - compact)
        paid_label = QLabel("💰 المبلغ المدفوع")
        paid_label.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_BODY, QFont.Bold))
        summary_card_layout.addWidget(paid_label)

        fx_row = QHBoxLayout()
        fx_row.setSpacing(6)
        fx_row.addWidget(QLabel("FX:"))
        self.usd_to_syp_new_snapshot = QDoubleSpinBox()
        self.usd_to_syp_new_snapshot.setRange(0, 999999999999)
        self.usd_to_syp_new_snapshot.setDecimals(6)
        self.usd_to_syp_new_snapshot.setPrefix("1$=")
        self.usd_to_syp_new_snapshot.setSuffix(" جديد")
        self.usd_to_syp_new_snapshot.valueChanged.connect(self.on_fx_new_changed)
        fx_row.addWidget(self.usd_to_syp_new_snapshot, 1)
        self.usd_to_syp_old_snapshot = QDoubleSpinBox()
        self.usd_to_syp_old_snapshot.setRange(0, 99999999999999)
        self.usd_to_syp_old_snapshot.setDecimals(6)
        self.usd_to_syp_old_snapshot.setPrefix("1$=")
        self.usd_to_syp_old_snapshot.setSuffix(" قديم")
        self.usd_to_syp_old_snapshot.valueChanged.connect(self.on_fx_old_changed)
        fx_row.addWidget(self.usd_to_syp_old_snapshot, 1)
        summary_card_layout.addLayout(fx_row)

        payable_row = QHBoxLayout()
        payable_label = QLabel("مستحق الدفع:")
        payable_label.setProperty("class", "subtitle")
        payable_row.addWidget(payable_label)
        payable_row.addStretch()
        self.payable_value = QLabel("0.00")
        self.payable_value.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_H3, QFont.Bold))
        payable_row.addWidget(self.payable_value)
        summary_card_layout.addLayout(payable_row)
        
        # Payment amount row with full payment button
        paid_row = QHBoxLayout()
        paid_row.setSpacing(6)  # Reduced from 8px
        
        self.paid_amount_spin = QDoubleSpinBox()
        self.paid_amount_spin.setRange(0, 999999999)
        self.paid_amount_spin.setDecimals(2)
        self.paid_amount_spin.setSuffix(" $")
        self.paid_amount_spin.setStyleSheet(f"font-size: 14px; padding: 6px; border: 2px solid {Colors.PRIMARY}; border-radius: 6px;")  # Reduced font and padding
        paid_row.addWidget(self.paid_amount_spin, 2)
        
        # Full payment button
        self.full_payment_btn = QPushButton("دفع كامل")
        self.full_payment_btn.setProperty("class", "primary")
        self.full_payment_btn.setMinimumHeight(36)  # Reduced from 40px
        self.full_payment_btn.clicked.connect(self.set_full_payment)
        paid_row.addWidget(self.full_payment_btn, 1)
        
        summary_card_layout.addLayout(paid_row)
        
        # Remaining amount display
        remaining_row = QHBoxLayout()
        remaining_label = QLabel("المتبقي:")
        remaining_label.setProperty("class", "subtitle")
        remaining_row.addWidget(remaining_label)
        remaining_row.addStretch()
        self.remaining_value = QLabel(self._format_transaction_amount(0))
        self.remaining_value.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_H3, QFont.Bold))
        self.remaining_value.setStyleSheet(f"color: {Colors.WARNING};")
        remaining_row.addWidget(self.remaining_value)
        summary_card_layout.addLayout(remaining_row)
        
        # Connect paid amount change to update remaining
        self.paid_amount_spin.valueChanged.connect(self.update_remaining_amount)

        self.discount_type_combo.currentIndexChanged.connect(self.on_discount_type_changed)
        self.discount_spin.valueChanged.connect(lambda _: self._refresh_summary_totals())
        
        summary_card_layout.addStretch()
        
        # Action buttons (compact)
        save_btn = QPushButton("✅ حفظ وإصدار الفاتورة")
        save_btn.setProperty("class", "success")
        save_btn.setMinimumHeight(44)  # Reduced from 50px
        save_btn.setFont(QFont(Fonts.FAMILY_AR, 13, QFont.Bold))  # Reduced from 14
        save_btn.clicked.connect(self.save)
        summary_card_layout.addWidget(save_btn)

        cancel_btn = QPushButton("إلغاء")
        cancel_btn.setProperty("class", "secondary")
        cancel_btn.setMinimumHeight(36)  # Added explicit height
        cancel_btn.clicked.connect(self.reject)
        summary_card_layout.addWidget(cancel_btn)

        right_column.addWidget(summary_card)
        
        # Error Label
        self.error_label = QLabel()
        self.error_label.setStyleSheet(f"color: {Colors.DANGER}; font-weight: bold;")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setVisible(False)
        right_column.addWidget(self.error_label)

        content_layout.addLayout(right_column, 1)
        main_layout.addLayout(content_layout)

        self.on_currency_changed(self.currency_combo.currentIndex())
    
    def load_data(self):
        """Load customers, warehouses, products from API."""
        try:
            # Load customers
            # Requirements: 2.1 - Customer selection dropdown populated from the API
            customers_response = api.get_customers()
            if isinstance(customers_response, dict) and 'results' in customers_response:
                self.customers_cache = customers_response['results']
            else:
                self.customers_cache = customers_response if isinstance(customers_response, list) else []
            
            self.customer_combo.clear()
            self.customer_combo.addItem("اختر العميل...", None)
            for customer in self.customers_cache:
                display_text = f"{customer.get('name', '')} ({customer.get('code', '')})"
                self.customer_combo.addItem(display_text, customer.get('id'))
            
            # Load warehouses
            warehouses_response = api.get_warehouses()
            if isinstance(warehouses_response, dict) and 'results' in warehouses_response:
                self.warehouses_cache = warehouses_response['results']
            else:
                self.warehouses_cache = warehouses_response if isinstance(warehouses_response, list) else []
            
            self.warehouse_combo.clear()
            self.warehouse_combo.addItem("اختر المستودع...", None)
            for warehouse in self.warehouses_cache:
                self.warehouse_combo.addItem(warehouse.get('name', ''), warehouse.get('id'))
            
            # Select default warehouse if available
            for i, warehouse in enumerate(self.warehouses_cache):
                if warehouse.get('is_default'):
                    self.warehouse_combo.setCurrentIndex(i + 1)  # +1 for placeholder
                    break
            
            # Load products
            products_response = api.get_products()
            if isinstance(products_response, dict) and 'results' in products_response:
                self.products_cache = products_response['results']
            else:
                self.products_cache = products_response if isinstance(products_response, list) else []
            
            self.product_combo.clear()
            self.product_combo.addItem("اختر المنتج...", None)
            for product in self.products_cache:
                display_text = f"{product.get('name', '')} - ${float(product.get('sale_price_usd', product.get('sale_price', 0)) or 0):,.2f}"
                self.product_combo.addItem(display_text, product.get('id'))
            
            # Update price when product is selected
            self.product_combo.currentIndexChanged.connect(self.on_product_changed)
            
        except ApiException as e:
            MessageDialog.error(self, "خطأ", f"فشل في تحميل البيانات: {str(e)}")
    
    def on_type_changed(self, index: int):
        """Handle invoice type change."""
        invoice_type = self.type_combo.currentData()
        
        if invoice_type == 'cash':
            self.due_date_container.setVisible(False)
            # For cash, default paid amount to total
            self.set_full_payment()
        else:
            self.due_date_container.setVisible(True)
            self.paid_amount_spin.setValue(0)
            self.update_remaining_amount()
    
    def _calculate_totals(self):
        """Calculate subtotal, tax, and grand total."""
        subtotal = sum(item.get('total', 0) for item in self.items)
        # Calculate tax based on products' tax rates
        tax = 0
        for item in self.items:
            product_id = item.get('product')
            # Find product to get tax rate
            for product in self.products_cache:
                if product.get('id') == product_id:
                    if product.get('is_taxable', False):
                        tax_rate = float(product.get('tax_rate', 15)) / 100
                        tax += item.get('total', 0) * tax_rate
                    break

        discount_amount = 0.0
        if hasattr(self, 'discount_type_combo') and hasattr(self, 'discount_spin'):
            mode = self.discount_type_combo.currentData()
            value = float(self.discount_spin.value())
            if mode == 'percent':
                discount_amount = (subtotal * value) / 100.0
            else:
                discount_amount = value

        if discount_amount < 0:
            discount_amount = 0.0
        if discount_amount > subtotal:
            discount_amount = subtotal

        grand_total = (subtotal - discount_amount) + tax
        return subtotal, tax, grand_total

    def _refresh_summary_totals(self):
        subtotal, tax, grand_total = self._calculate_totals()
        self.subtotal_value.setText(config.format_usd(subtotal))
        self.tax_value.setText(config.format_usd(tax))
        self.total_value.setText(config.format_usd(grand_total))
        payable = self._usd_to_transaction_amount(grand_total)
        self.payable_value.setText(self._format_transaction_amount(payable))
        self._update_cash_paid_amount()
        self.update_remaining_amount()

    def on_discount_type_changed(self, index: int):
        mode = self.discount_type_combo.currentData()
        if mode == 'amount':
            self.discount_spin.setRange(0, 999999999)
            self.discount_spin.setSuffix(" $")
        else:
            self.discount_spin.setRange(0, 100)
            self.discount_spin.setSuffix(" %")
        self._refresh_summary_totals()
    
    def set_full_payment(self):
        """Set paid amount to full invoice total (including tax)."""
        subtotal, tax, grand_total = self._calculate_totals()
        self.paid_amount_spin.setValue(self._usd_to_transaction_amount(grand_total))
        self.update_remaining_amount()
    
    def update_remaining_amount(self):
        """Update the remaining amount display."""
        subtotal, tax, grand_total = self._calculate_totals()
        paid = self.paid_amount_spin.value()
        payable = self._usd_to_transaction_amount(grand_total)
        remaining = max(0, payable - paid)
        self.remaining_value.setText(self._format_transaction_amount(remaining))
        
        # Color code based on remaining
        if remaining <= 0.01:  # Small tolerance for floating point
            self.remaining_value.setStyleSheet(f"color: {Colors.SUCCESS}; font-weight: bold;")
        else:
            self.remaining_value.setStyleSheet(f"color: {Colors.WARNING}; font-weight: bold;")
    
    def _update_cash_paid_amount(self):
        """Update paid amount spinbox for cash sales."""
        if self.type_combo.currentData() == 'cash':
            self.set_full_payment()
        
    def on_product_changed(self, index: int):
        """Update price and unit selector when product is selected."""
        product_id = self.product_combo.currentData()
        if product_id:
            for product in self.products_cache:
                if product.get('id') == product_id:
                    # Update price with base sale price
                    self.price_spin.setValue(float(product.get('sale_price_usd', product.get('sale_price', 0)) or 0))
                    
                    # Update unit selector with product units
                    # Requirements: 3.1 - Display available units for selected product
                    product_units = product.get('product_units', [])
                    self.unit_selector.set_product_units(product_units, product_id)
                    break
        else:
            # Clear unit selector when no product selected
            self.unit_selector.clear_units()
    
    def on_unit_changed(self, pu_id: int, unit_name: str, unit_symbol: str, 
                        sale_price: float, cost_price: float, conversion_factor: float):
        """
        Handle unit selection change - auto-populate price.
        
        Requirements: 3.2 - Auto-populate price when unit is selected
        """
        if sale_price > 0:
            self.price_spin.setValue(sale_price)
    
    def search_by_barcode(self):
        """Search and add product by barcode or code."""
        query = self.barcode_input.text().strip()
        if not query:
            return
        
        product_found = None
        
        # First try to find by barcode in cache
        for product in self.products_cache:
            if product.get('barcode') == query or product.get('code') == query:
                product_found = product
                break
        
        # If not found in cache, try API
        if not product_found:
            try:
                product_found = api.get_product_by_barcode(query)
            except ApiException:
                pass
        
        if product_found:
            # Add product directly with quantity 1
            self.add_product_to_items(product_found, quantity=1)
            self.barcode_input.clear()
            self.barcode_input.setFocus()  # Keep focus for next scan
        else:
            # Show brief error and clear
            MessageDialog.warning(self, "غير موجود", f"المنتج '{query}' غير موجود")
            self.barcode_input.selectAll()
    
    def add_product_to_items(self, product: dict, quantity: float = 1):
        """Add a product to items list."""
        product_id = product.get('id')
        product_name = product.get('name', '')
        unit_price = float(product.get('sale_price_usd', product.get('sale_price', 0)) or 0)
        
        # Get product units for unit selection
        product_units = product.get('product_units', [])
        
        # Find base unit or first unit
        selected_unit = None
        unit_name = ''
        unit_symbol = ''
        product_unit_id = None
        
        if product_units:
            # Find base unit
            for pu in product_units:
                if pu.get('is_base_unit', False):
                    selected_unit = pu
                    break
            # If no base unit, use first unit
            if not selected_unit and product_units:
                selected_unit = product_units[0]
            
            if selected_unit:
                unit_name = selected_unit.get('unit_name', '')
                unit_symbol = selected_unit.get('unit_symbol', '')
                product_unit_id = selected_unit.get('id')
                # Use unit-specific price if available
                unit_sale_price = float(selected_unit.get('sale_price_usd', selected_unit.get('sale_price', 0)) or 0)
                if unit_sale_price > 0:
                    unit_price = unit_sale_price
        
        # Check if product already in list - increment quantity
        for item in self.items:
            if item['product'] == product_id and item.get('product_unit') == product_unit_id:
                item['quantity'] += quantity
                item['total'] = item['quantity'] * item['unit_price']
                self.update_items_table()
                return
        
        # Add new item
        self.items.append({
            'product': product_id,
            'product_name': product_name,
            'product_unit': product_unit_id,
            'unit_name': unit_name,
            'unit_symbol': unit_symbol,
            'quantity': quantity,
            'unit_price': unit_price,
            'total': quantity * unit_price
        })
        
        self.update_items_table()
    
    def add_item(self):
        """Add item to the items list."""
        product_id = self.product_combo.currentData()
        if not product_id:
            MessageDialog.warning(self, "تنبيه", "يرجى اختيار منتج")
            return
        
        quantity = self.quantity_spin.value()
        unit_price = self.price_spin.value()
        
        if quantity <= 0:
            MessageDialog.warning(self, "تنبيه", "يرجى إدخال كمية صحيحة")
            return
        
        # Get product name
        product_name = ""
        for product in self.products_cache:
            if product.get('id') == product_id:
                product_name = product.get('name', '')
                break
        
        # Get selected unit information
        # Requirements: 3.1, 3.2 - Unit selection in sales
        selected_unit = self.unit_selector.get_selected_unit()
        product_unit_id = None
        unit_name = ''
        unit_symbol = ''
        
        if selected_unit:
            product_unit_id = selected_unit.get('id')
            unit_name = selected_unit.get('unit_name', '')
            unit_symbol = selected_unit.get('unit_symbol', '')
        
        # Check if product with same unit already in list
        for item in self.items:
            if item['product'] == product_id and item.get('product_unit') == product_unit_id:
                item['quantity'] += quantity
                item['total'] = item['quantity'] * item['unit_price']
                self.update_items_table()
                # Reset inputs
                self.product_combo.setCurrentIndex(0)
                self.quantity_spin.setValue(1)
                self.price_spin.setValue(0)
                self.unit_selector.clear_units()
                return
        
        # Add new item
        self.items.append({
            'product': product_id,
            'product_name': product_name,
            'product_unit': product_unit_id,
            'unit_name': unit_name,
            'unit_symbol': unit_symbol,
            'quantity': quantity,
            'unit_price': unit_price,
            'total': quantity * unit_price
        })
        
        self.update_items_table()
        
        # Reset inputs
        self.product_combo.setCurrentIndex(0)
        self.quantity_spin.setValue(1)
        self.price_spin.setValue(0)
        self.unit_selector.clear_units()
    
    def update_items_table(self):
        """Update items table display."""
        self._updating_items_table = True
        self.items_table.blockSignals(True)
        self.items_table.setRowCount(len(self.items))
        
        for i, item in enumerate(self.items):
            # Product name
            product_item = QTableWidgetItem(item['product_name'])
            product_item.setFlags(product_item.flags() & ~Qt.ItemIsEditable)
            self.items_table.setItem(i, 0, product_item)
            
            # Unit name - Requirements: 3.5 - Display selected unit name/symbol
            unit_display = item.get('unit_name', '') or item.get('unit_symbol', '') or '-'
            unit_item = QTableWidgetItem(unit_display)
            unit_item.setFlags(unit_item.flags() & ~Qt.ItemIsEditable)
            unit_item.setTextAlignment(Qt.AlignCenter)
            self.items_table.setItem(i, 1, unit_item)
            
            # Quantity
            qty_val = float(item.get('quantity', 0))
            qty_item = QTableWidgetItem(f"{qty_val:,.2f}")
            qty_item.setData(Qt.UserRole, qty_val)
            qty_item.setTextAlignment(Qt.AlignCenter)
            qty_item.setFlags(qty_item.flags() | Qt.ItemIsEditable)
            self.items_table.setItem(i, 2, qty_item)
            
            # Price
            price_val = float(item.get('unit_price', 0))
            price_item = QTableWidgetItem(f"{price_val:,.2f}")
            price_item.setData(Qt.UserRole, price_val)
            price_item.setTextAlignment(Qt.AlignCenter)
            price_item.setFlags(price_item.flags() | Qt.ItemIsEditable)
            self.items_table.setItem(i, 3, price_item)
            
            # Total - Requirements: 3.3 - Calculate line total
            total_item = QTableWidgetItem(f"{float(item.get('total', 0)):,.2f}")
            total_item.setTextAlignment(Qt.AlignCenter)
            total_item.setFlags(total_item.flags() & ~Qt.ItemIsEditable)
            self.items_table.setItem(i, 4, total_item)
            
            # Delete button - Enhanced styling with hover effects
            delete_btn = QPushButton("🗑️")
            delete_btn.setFixedSize(32, 32)  # Slightly larger for better clickability
            delete_btn.setToolTip("حذف المنتج")  # Arabic tooltip
            delete_btn.setStyleSheet(f"""
                QPushButton {{
                    border: none;
                    background: transparent;
                    border-radius: 16px;
                    font-size: 14px;
                    color: {Colors.DANGER};
                }}
                QPushButton:hover {{
                    background-color: {Colors.DANGER}15;
                    border: 1px solid {Colors.DANGER}30;
                }}
                QPushButton:pressed {{
                    background-color: {Colors.DANGER}25;
                }}
            """)
            delete_btn.clicked.connect(lambda _, idx=i: self.remove_item(idx))
            self.items_table.setCellWidget(i, 5, delete_btn)
        
        self.items_table.blockSignals(False)
        self._updating_items_table = False
        
        # Update summary with tax calculation
        self._refresh_summary_totals()
        
        # Scroll to show the last added item
        if self.items:
            self.items_table.scrollToBottom()

    def on_items_table_item_changed(self, changed: QTableWidgetItem):
        if self._updating_items_table:
            return
        if changed is None:
            return
        row = changed.row()
        col = changed.column()
        if not (0 <= row < len(self.items)):
            return
        if col not in (2, 3):
            return

        try:
            numeric = changed.data(Qt.UserRole)
            if numeric is None:
                numeric = float(str(changed.text()).replace(',', '').strip() or 0)
            numeric = float(numeric)
        except Exception:
            numeric = 0.0

        if col == 2:
            if numeric <= 0:
                numeric = 0.01
            self.items[row]['quantity'] = numeric
        elif col == 3:
            if numeric < 0:
                numeric = 0.0
            self.items[row]['unit_price'] = numeric

        self.items[row]['total'] = float(self.items[row].get('quantity', 0)) * float(self.items[row].get('unit_price', 0))

        self._updating_items_table = True
        self.items_table.blockSignals(True)
        if col == 2:
            changed.setData(Qt.UserRole, float(self.items[row]['quantity']))
            changed.setText(f"{float(self.items[row]['quantity']):,.2f}")
        elif col == 3:
            changed.setData(Qt.UserRole, float(self.items[row]['unit_price']))
            changed.setText(f"{float(self.items[row]['unit_price']):,.2f}")

        total_cell = self.items_table.item(row, 4)
        if total_cell is None:
            total_cell = QTableWidgetItem()
            total_cell.setTextAlignment(Qt.AlignCenter)
            total_cell.setFlags(total_cell.flags() & ~Qt.ItemIsEditable)
            self.items_table.setItem(row, 4, total_cell)
        total_cell.setText(f"{float(self.items[row]['total']):,.2f}")
        self.items_table.blockSignals(False)
        self._updating_items_table = False

        self._refresh_summary_totals()
    
    def remove_item(self, index: int):
        """Remove item from the list."""
        if 0 <= index < len(self.items):
            self.items.pop(index)
            self.update_items_table()
    
    def validate(self) -> bool:
        """
        Validate form data.
        
        Customer is required for all invoices (backend requirement).
        Requirements: 2.5 - Credit invoices especially require customer selection.
        """
        self.error_label.setVisible(False)
        
        invoice_type = self.type_combo.currentData()
        customer_id = self.customer_combo.currentData()
        warehouse_id = self.warehouse_combo.currentData()
        
        # Validate customer - required for all invoices
        if not customer_id:
            MessageDialog.warning(self, "تنبيه", "يجب اختيار العميل")
            return False
        
        # Validate warehouse
        if not warehouse_id:
            self.error_label.setText("يجب اختيار المستودع")
            self.error_label.setVisible(True)
            return False
        
        # Validate items
        if not self.items:
            MessageDialog.warning(self, "تنبيه", "يجب إضافة منتج واحد على الأقل")
            return False

        currency = self.currency_combo.currentData() or 'USD'
        if currency != 'USD':
            fx_old = float(self.usd_to_syp_old_snapshot.value() or 0)
            fx_new = float(self.usd_to_syp_new_snapshot.value() or 0)
            if fx_old <= 0 or fx_new <= 0:
                MessageDialog.warning(self, "تنبيه", "يرجى إدخال سعر الصرف")
                return False
        
        return True
    
    def get_data(self) -> dict:
        """Get form data as dictionary."""
        # Determine tax rate based on global settings
        # If TAX_ENABLED is False, send tax_rate=0 to override product defaults
        global_tax_rate = config.TAX_RATE if config.TAX_ENABLED else 0

        invoice_date = self.date_edit.date().toString('yyyy-MM-dd')
        transaction_currency = self.currency_combo.currentData() or 'USD'
        fx_old = float(self.usd_to_syp_old_snapshot.value() or 0)
        fx_new = float(self.usd_to_syp_new_snapshot.value() or 0)

        data = {
            'invoice_type': self.type_combo.currentData(),
            'warehouse': self.warehouse_combo.currentData(),
            'invoice_date': invoice_date,
            'transaction_currency': transaction_currency,
            'fx_rate_date': invoice_date,
            'usd_to_syp_old_snapshot': fx_old if fx_old > 0 else None,
            'usd_to_syp_new_snapshot': fx_new if fx_new > 0 else None,
            'items': [
                {
                    'product': item['product'],
                    'product_unit': item.get('product_unit'),  # Include product_unit for unit tracking
                    'quantity': item['quantity'],
                    'unit_price': self._usd_to_transaction_amount(float(item['unit_price'])),
                    'tax_rate': global_tax_rate  # Respect global tax settings
                }
                for item in self.items
            ],
            'paid_amount': float(self.paid_amount_spin.value()),
            'payment_method': 'cash', # Default to cash for the initial payment
            'confirm': True # Atomic confirmation
        }

        mode = self.discount_type_combo.currentData() if hasattr(self, 'discount_type_combo') else 'percent'
        discount_val = float(self.discount_spin.value()) if hasattr(self, 'discount_spin') else 0.0
        if mode == 'amount':
            data['discount_percent'] = 0
            data['discount_amount'] = self._usd_to_transaction_amount(discount_val)
        else:
            data['discount_percent'] = discount_val
            data['discount_amount'] = 0
        
        customer_id = self.customer_combo.currentData()
        if customer_id:
            data['customer'] = customer_id
        
        if self.type_combo.currentData() == 'credit':
            data['due_date'] = self.due_date_edit.date().toString('yyyy-MM-dd')
        
        notes = self.notes_edit.toPlainText().strip()
        if notes:
            data['notes'] = notes
        
        return data

    def _usd_to_transaction_amount(self, amount_usd: float) -> float:
        currency = self.currency_combo.currentData() or 'USD'
        if currency == 'USD':
            return float(amount_usd or 0)
        if currency == 'SYP_NEW':
            rate = float(self.usd_to_syp_new_snapshot.value() or 0)
            return float(amount_usd or 0) * rate if rate > 0 else 0.0
        if currency == 'SYP_OLD':
            rate = float(self.usd_to_syp_old_snapshot.value() or 0)
            return float(amount_usd or 0) * rate if rate > 0 else 0.0
        return float(amount_usd or 0)

    def _format_transaction_amount(self, amount: float) -> str:
        currency = self.currency_combo.currentData() or 'USD'
        if currency == 'USD':
            return f"${float(amount or 0):,.2f}"
        if currency == 'SYP_NEW':
            return f"{float(amount or 0):,.2f} ل.س جديدة"
        return f"{float(amount or 0):,.2f} ل.س"

    def on_currency_changed(self, index: int):
        self.transaction_currency = self.currency_combo.currentData() or 'USD'
        if self.transaction_currency == 'USD':
            self.paid_amount_spin.setSuffix(" $")
        elif self.transaction_currency == 'SYP_NEW':
            self.paid_amount_spin.setSuffix(" ل.س جديدة")
        else:
            self.paid_amount_spin.setSuffix(" ل.س")
        self.usd_to_syp_new_snapshot.setEnabled(self.transaction_currency != 'USD')
        self.usd_to_syp_old_snapshot.setEnabled(self.transaction_currency != 'USD')
        self.load_fx_for_date()
        self._refresh_summary_totals()

    def on_fx_new_changed(self, value: float):
        if self._fx_syncing:
            return
        self._fx_syncing = True
        try:
            self.usd_to_syp_old_snapshot.setValue(value * 100.0)
        finally:
            self._fx_syncing = False
        self._refresh_summary_totals()

    def on_fx_old_changed(self, value: float):
        if self._fx_syncing:
            return
        self._fx_syncing = True
        try:
            self.usd_to_syp_new_snapshot.setValue(value / 100.0 if value else 0.0)
        finally:
            self._fx_syncing = False
        self._refresh_summary_totals()

    def load_fx_for_date(self, qdate=None):
        if (self.currency_combo.currentData() or 'USD') == 'USD':
            return
        try:
            rate_date = self.date_edit.date().toString('yyyy-MM-dd')
            ctx = api.get_app_context(rate_date=rate_date, strict_fx=False)
            fx = ctx.get('daily_fx') if isinstance(ctx, dict) else None
            if fx:
                self._fx_syncing = True
                try:
                    self.usd_to_syp_old_snapshot.setValue(float(fx.get('usd_to_syp_old') or 0))
                    self.usd_to_syp_new_snapshot.setValue(float(fx.get('usd_to_syp_new') or 0))
                finally:
                    self._fx_syncing = False
        except ApiException:
            pass
    
    def save(self):
        """Emit saved signal with form data."""
        if self.validate():
            self.saved.emit(self.get_data())
            self.accept()

    def request_print(self):
        if self.validate():
            self.print_requested.emit(self.get_data())
            self.accept()


# Import PaymentCollectionView from separate module
from .payment_collection import PaymentCollectionView

# Import PaymentsView from separate module
from .payments import PaymentsView, PaymentCreateDialog, PaymentDetailsDialog

__all__ = [
    'CustomersView', 'InvoicesView', 'POSView', 'PaymentCollectionView', 
    'CreditLimitOverrideDialog', 'InvoiceFormDialog',
    'SalesReturnDialog', 'SalesReturnsView', 'InvoiceDetailsDialog',
    'PaymentsView', 'PaymentCreateDialog', 'PaymentDetailsDialog'
]
