"""
Settings View - Updated with Currency and Tax Configuration

Requirements: 4.1, 4.2 - Error handling for settings save operations
Requirements: 9.1, 9.2, 9.3, 9.4, 9.5 - Unit management settings page
Requirements: 8.1, 8.2, 8.3, 8.4, 8.5 - Category management settings page
Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6 - Warehouse management settings page
Requirements: 11.1, 11.2, 11.3, 11.4, 11.5 - Expense category management settings page
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QGroupBox, QFormLayout, QPushButton,
    QScrollArea, QComboBox, QDoubleSpinBox, QCheckBox,
    QStackedWidget, QFrame, QDateEdit
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont

from ...config import Colors, Fonts, config
from ...widgets.dialogs import MessageDialog
from ...utils.error_handler import handle_ui_error
from ...services.api import api, ApiException
from .units import UnitsManagementView, UnitsView
from .categories import CategoriesView
from .warehouses import WarehousesView, WarehousesManagementView
from .expense_categories import ExpenseCategoriesView
from .backup_restore import BackupRestoreView


class SettingsNavButton(QPushButton):
    """Navigation button for settings sidebar."""
    
    def __init__(self, text: str, icon: str, parent=None):
        super().__init__(parent)
        self.setText(f"{icon}  {text}")
        self.setCheckable(True)
        self.setFixedHeight(44)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            QPushButton {{
                text-align: right;
                padding: 0 16px;
                border: none;
                border-radius: 8px;
                background: transparent;
                color: {Colors.LIGHT_TEXT};
                font-size: 13px;
            }}
            QPushButton:hover {{
                background: {Colors.LIGHT_BORDER};
                color: {Colors.LIGHT_TEXT};
            }}
            QPushButton:checked {{
                background: {Colors.PRIMARY};
                color: white;
            }}
        """)


class GeneralSettingsWidget(QWidget):
    """General settings widget (company, currency, tax, printer, system)."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(24)
        
        title = QLabel("الإعدادات العامة")
        title.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_H2, QFont.Bold))
        layout.addWidget(title)
        
        # Company Settings
        company_group = QGroupBox("معلومات الشركة")
        company_layout = QFormLayout(company_group)
        
        self.company_name = QLineEdit(config.COMPANY_NAME)
        company_layout.addRow("اسم الشركة:", self.company_name)
        
        self.company_name_en = QLineEdit(config.COMPANY_NAME_EN)
        company_layout.addRow("الاسم بالإنجليزية:", self.company_name_en)
        
        self.company_address = QLineEdit(config.COMPANY_ADDRESS)
        company_layout.addRow("العنوان:", self.company_address)
        
        self.company_phone = QLineEdit(config.COMPANY_PHONE)
        company_layout.addRow("الهاتف:", self.company_phone)
        
        self.tax_number = QLineEdit(config.COMPANY_TAX_NUMBER)
        company_layout.addRow("الرقم الضريبي:", self.tax_number)
        
        layout.addWidget(company_group)
        
        # Currency Settings
        currency_group = QGroupBox("إعدادات العملة")
        currency_layout = QFormLayout(currency_group)
        
        self.primary_currency = QComboBox()
        self.primary_currency.addItems([
            'ل.س - الليرة السورية',
            '$ - الدولار الأمريكي',
            'ر.س - الريال السعودي',
            'د.ل - الدينار الليبي',
        ])
        currency_layout.addRow("العملة الأساسية:", self.primary_currency)
        
        self.secondary_currency = QComboBox()
        self.secondary_currency.addItems([
            '$ - الدولار الأمريكي',
            'ل.س - الليرة السورية',
            '€ - اليورو',
        ])
        currency_layout.addRow("العملة الثانوية:", self.secondary_currency)

        self.display_currency = QComboBox()
        self.display_currency.addItem('USD - الدولار الأمريكي', 'USD')
        self.display_currency.addItem('ل.س جديدة', 'SYP_NEW')
        self.display_currency.addItem('ل.س قديمة', 'SYP_OLD')
        current_display = config.DISPLAY_CURRENCY or 'USD'
        display_idx = self.display_currency.findData(current_display)
        if display_idx >= 0:
            self.display_currency.setCurrentIndex(display_idx)
        currency_layout.addRow("عملة العرض:", self.display_currency)
        
        exchange_row = QHBoxLayout()
        self.exchange_rate = QDoubleSpinBox()
        self.exchange_rate.setRange(0, 1000000)
        self.exchange_rate.setDecimals(2)
        self.exchange_rate.setValue(config.SECONDARY_CURRENCY.exchange_rate)
        self.exchange_rate.setPrefix("1 $ = ")
        self.exchange_rate.setSuffix(" ل.س")
        exchange_row.addWidget(self.exchange_rate)
        
        update_rate_btn = QPushButton("تحديث")
        update_rate_btn.setStyleSheet(f"background: {Colors.PRIMARY}; color: white; border-radius: 4px; padding: 5px 15px;")
        update_rate_btn.clicked.connect(self.update_exchange_rate)
        exchange_row.addWidget(update_rate_btn)
        exchange_row.addStretch()
        
        currency_layout.addRow("سعر الصرف:", exchange_row)
        
        self.show_dual_currency = QCheckBox("عرض السعر بالعملتين")
        self.show_dual_currency.setChecked(True)
        currency_layout.addRow("", self.show_dual_currency)

        self._fx_syncing = False
        self._daily_fx_id = None

        fx_group = QGroupBox("سعر الصرف اليومي")
        fx_layout = QFormLayout(fx_group)

        self.fx_rate_date = QDateEdit()
        self.fx_rate_date.setCalendarPopup(True)
        self.fx_rate_date.setDisplayFormat('yyyy-MM-dd')
        self.fx_rate_date.setDate(QDate.currentDate())
        self.fx_rate_date.dateChanged.connect(self.load_daily_fx)
        fx_layout.addRow("تاريخ سعر الصرف:", self.fx_rate_date)

        self.usd_to_syp_new = QDoubleSpinBox()
        self.usd_to_syp_new.setRange(0, 999999999999)
        self.usd_to_syp_new.setDecimals(6)
        self.usd_to_syp_new.setPrefix("1 $ = ")
        self.usd_to_syp_new.setSuffix(" ل.س جديدة")
        self.usd_to_syp_new.valueChanged.connect(self._on_fx_new_changed)
        fx_layout.addRow("سعر الدولار (الجديدة):", self.usd_to_syp_new)

        self.usd_to_syp_old = QDoubleSpinBox()
        self.usd_to_syp_old.setRange(0, 99999999999999)
        self.usd_to_syp_old.setDecimals(6)
        self.usd_to_syp_old.setPrefix("1 $ = ")
        self.usd_to_syp_old.setSuffix(" ل.س قديمة")
        self.usd_to_syp_old.valueChanged.connect(self._on_fx_old_changed)
        fx_layout.addRow("سعر الدولار (القديمة):", self.usd_to_syp_old)

        fx_btn_row = QHBoxLayout()
        fx_btn_row.addStretch()
        self.save_fx_btn = QPushButton("حفظ سعر الصرف")
        self.save_fx_btn.setStyleSheet(f"background: {Colors.PRIMARY}; color: white; border-radius: 4px; padding: 5px 15px;")
        self.save_fx_btn.clicked.connect(self.save_daily_fx)
        fx_btn_row.addWidget(self.save_fx_btn)
        fx_layout.addRow("", fx_btn_row)
        
        layout.addWidget(currency_group)
        layout.addWidget(fx_group)
        
        # Tax Settings
        tax_group = QGroupBox("إعدادات الضريبة")
        tax_layout = QFormLayout(tax_group)
        
        self.tax_enabled = QCheckBox("تفعيل الضريبة")
        self.tax_enabled.setChecked(config.TAX_ENABLED)
        self.tax_enabled.toggled.connect(self.on_tax_toggle)
        tax_layout.addRow("", self.tax_enabled)
        
        self.tax_rate = QDoubleSpinBox()
        self.tax_rate.setRange(0, 100)
        self.tax_rate.setDecimals(2)
        self.tax_rate.setValue(config.TAX_RATE)
        self.tax_rate.setSuffix(" %")
        self.tax_rate.setEnabled(config.TAX_ENABLED)
        tax_layout.addRow("نسبة الضريبة:", self.tax_rate)
        
        self.tax_name = QLineEdit("ضريبة القيمة المضافة")
        self.tax_name.setEnabled(config.TAX_ENABLED)
        tax_layout.addRow("اسم الضريبة:", self.tax_name)
        
        layout.addWidget(tax_group)
        
        # Printer Settings
        printer_group = QGroupBox("إعدادات الطباعة")
        printer_layout = QFormLayout(printer_group)
        
        self.default_printer = QComboBox()
        self.default_printer.addItem("الطابعة الافتراضية")
        printer_layout.addRow("طابعة A4:", self.default_printer)
        
        self.receipt_printer = QComboBox()
        self.receipt_printer.addItem("الطابعة الافتراضية")
        printer_layout.addRow("طابعة الإيصالات:", self.receipt_printer)
        
        self.receipt_width = QComboBox()
        self.receipt_width.addItems(['58mm', '80mm'])
        self.receipt_width.setCurrentText(f"{config.RECEIPT_WIDTH}mm")
        printer_layout.addRow("عرض الإيصال:", self.receipt_width)
        
        layout.addWidget(printer_group)
        
        # System Settings
        system_group = QGroupBox("إعدادات النظام")
        system_layout = QFormLayout(system_group)
        
        self.theme = QComboBox()
        self.theme.addItems(['فاتح', 'داكن'])
        system_layout.addRow("المظهر:", self.theme)
        
        self.api_url = QLineEdit(config.API_BASE_URL)
        system_layout.addRow("رابط الخادم:", self.api_url)
        
        layout.addWidget(system_group)
        
        # Save button
        save_layout = QHBoxLayout()
        save_layout.addStretch()
        
        save_btn = QPushButton("حفظ الإعدادات")
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Colors.PRIMARY};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 32px;
                font-size: 14px;
                font-weight: bold;
            }}
        """)
        save_btn.clicked.connect(self.save_settings)
        save_layout.addWidget(save_btn)
        
        layout.addLayout(save_layout)
        layout.addStretch()
        
        scroll.setWidget(content)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)
        
    def on_tax_toggle(self, enabled: bool):
        """Handle tax enabled toggle."""
        self.tax_rate.setEnabled(enabled)
        self.tax_name.setEnabled(enabled)
        
    @handle_ui_error
    def update_exchange_rate(self):
        """Update exchange rate in config."""
        rate = self.exchange_rate.value()
        config.update_exchange_rate(rate)
        MessageDialog.success(self, "نجاح", f"تم تحديث سعر الصرف: 1$ = {rate:,.2f} ل.س")

    def _on_fx_new_changed(self, value: float):
        if self._fx_syncing:
            return
        self._fx_syncing = True
        try:
            self.usd_to_syp_old.setValue(value * 100.0)
            config.update_exchange_rate(value)
            self.exchange_rate.setValue(value)
        finally:
            self._fx_syncing = False

    def _on_fx_old_changed(self, value: float):
        if self._fx_syncing:
            return
        self._fx_syncing = True
        try:
            new_value = value / 100.0 if value else 0.0
            self.usd_to_syp_new.setValue(new_value)
            config.update_exchange_rate(new_value)
            self.exchange_rate.setValue(new_value)
        finally:
            self._fx_syncing = False

    @handle_ui_error
    def load_daily_fx(self, qdate=None):
        try:
            rate_date = self.fx_rate_date.date().toString('yyyy-MM-dd')
            resp = api.get_daily_exchange_rates({'rate_date': rate_date})
            if isinstance(resp, dict) and 'results' in resp:
                results = resp.get('results') or []
            else:
                results = resp if isinstance(resp, list) else []

            fx = results[0] if results else None
            self._daily_fx_id = fx.get('id') if fx else None

            if fx:
                old = float(fx.get('usd_to_syp_old') or 0)
                new = float(fx.get('usd_to_syp_new') or 0)
                self._fx_syncing = True
                try:
                    self.usd_to_syp_old.setValue(old)
                    self.usd_to_syp_new.setValue(new)
                    config.update_exchange_rate(new)
                    self.exchange_rate.setValue(new)
                finally:
                    self._fx_syncing = False
            else:
                self._daily_fx_id = None
        except ApiException as e:
            MessageDialog.warning(self, "تنبيه", f"تعذر تحميل سعر الصرف: {str(e)}")

    @handle_ui_error
    def save_daily_fx(self):
        rate_date = self.fx_rate_date.date().toString('yyyy-MM-dd')
        payload = {
            'rate_date': rate_date,
            'usd_to_syp_old': f"{self.usd_to_syp_old.value():.6f}",
            'usd_to_syp_new': f"{self.usd_to_syp_new.value():.6f}",
        }
        try:
            if self._daily_fx_id:
                api.update_daily_exchange_rate(self._daily_fx_id, payload)
            else:
                created = api.create_daily_exchange_rate(payload)
                self._daily_fx_id = created.get('id') if isinstance(created, dict) else None

            config.update_exchange_rate(self.usd_to_syp_new.value())
            self.exchange_rate.setValue(self.usd_to_syp_new.value())
            MessageDialog.success(self, "نجاح", "تم حفظ سعر الصرف اليومي")
        except ApiException as e:
            MessageDialog.error(self, "خطأ", f"فشل حفظ سعر الصرف: {str(e)}")
    
    @handle_ui_error
    def save_settings(self):
        """Save all settings."""
        config.COMPANY_NAME = self.company_name.text()
        config.COMPANY_NAME_EN = self.company_name_en.text()
        config.COMPANY_ADDRESS = self.company_address.text()
        config.COMPANY_PHONE = self.company_phone.text()
        config.COMPANY_TAX_NUMBER = self.tax_number.text()
        
        config.TAX_ENABLED = self.tax_enabled.isChecked()
        config.TAX_RATE = self.tax_rate.value()
        
        config.update_exchange_rate(self.exchange_rate.value())

        config.DISPLAY_CURRENCY = self.display_currency.currentData() or 'USD'
        
        config.API_BASE_URL = self.api_url.text()
        
        receipt_width_text = self.receipt_width.currentText()
        config.RECEIPT_WIDTH = int(receipt_width_text.replace('mm', ''))
        
        if config.save_settings():
            MessageDialog.success(self, "نجاح", "تم حفظ الإعدادات بنجاح")
        else:
            MessageDialog.warning(self, "تحذير", "تم تطبيق الإعدادات ولكن فشل الحفظ للملف")
        
    def refresh(self):
        """Refresh settings - reload from config."""
        self.company_name.setText(config.COMPANY_NAME)
        self.company_name_en.setText(config.COMPANY_NAME_EN)
        self.company_address.setText(config.COMPANY_ADDRESS)
        self.company_phone.setText(config.COMPANY_PHONE)
        self.tax_number.setText(config.COMPANY_TAX_NUMBER)
        self.tax_enabled.setChecked(config.TAX_ENABLED)
        self.tax_rate.setValue(config.TAX_RATE)
        self.exchange_rate.setValue(config.SECONDARY_CURRENCY.exchange_rate)
        display_idx = self.display_currency.findData(config.DISPLAY_CURRENCY or 'USD')
        if display_idx >= 0:
            self.display_currency.setCurrentIndex(display_idx)
        self.load_daily_fx()



class SettingsView(QWidget):
    """
    Application settings view with sidebar navigation.
    
    Requirements: 6.1 - Settings page for unit management
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.nav_buttons = {}
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize settings view UI with sidebar navigation."""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Settings sidebar navigation
        sidebar = QFrame()
        sidebar.setFixedWidth(200)
        sidebar.setStyleSheet(f"""
            QFrame {{
                background: {Colors.LIGHT_CARD};
                border-right: 1px solid {Colors.LIGHT_BORDER};
            }}
        """)
        
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 24, 12, 24)
        sidebar_layout.setSpacing(8)
        
        # Sidebar title
        sidebar_title = QLabel("الإعدادات")
        sidebar_title.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_H3, QFont.Bold))
        sidebar_title.setStyleSheet("padding: 0 8px 16px 8px;")
        sidebar_layout.addWidget(sidebar_title)
        
        # Navigation items
        nav_items = [
            ('general', 'الإعدادات العامة', '⚙️'),
            ('units', 'وحدات القياس', '📏'),
            ('categories', 'الفئات', '📁'),
            ('warehouses', 'المستودعات', '🏭'),
            ('expense_categories', 'فئات المصروفات', '💰'),
            ('backup_restore', 'النسخ الاحتياطي والاستعادة', '💾'),
        ]
        
        for key, label, icon in nav_items:
            btn = SettingsNavButton(label, icon)
            btn.clicked.connect(lambda checked, k=key: self.on_nav_click(k))
            sidebar_layout.addWidget(btn)
            self.nav_buttons[key] = btn
        
        sidebar_layout.addStretch()
        main_layout.addWidget(sidebar)
        
        # Content area with stacked widget
        self.stack = QStackedWidget()
        
        # General settings widget
        self.general_settings = GeneralSettingsWidget()
        self.stack.addWidget(self.general_settings)
        
        # Units management widget
        self.units_view = UnitsManagementView()
        self.stack.addWidget(self.units_view)
        
        # Categories management widget
        self.categories_view = CategoriesView()
        self.stack.addWidget(self.categories_view)
        
        # Warehouses management widget
        self.warehouses_view = WarehousesView()
        self.stack.addWidget(self.warehouses_view)
        
        # Expense categories management widget
        self.expense_categories_view = ExpenseCategoriesView()
        self.stack.addWidget(self.expense_categories_view)

        self.backup_restore_view = BackupRestoreView()
        self.stack.addWidget(self.backup_restore_view)
        
        # Content wrapper with padding
        content_wrapper = QWidget()
        content_layout = QVBoxLayout(content_wrapper)
        content_layout.setContentsMargins(24, 24, 24, 24)
        content_layout.addWidget(self.stack)
        
        main_layout.addWidget(content_wrapper, 1)
        
        # Select general settings by default
        self.nav_buttons['general'].setChecked(True)
        
    def on_nav_click(self, key: str):
        """Handle settings navigation click."""
        # Uncheck all buttons
        for btn in self.nav_buttons.values():
            btn.setChecked(False)
        
        # Check clicked button
        if key in self.nav_buttons:
            self.nav_buttons[key].setChecked(True)
        
        # Switch view
        if key == 'general':
            self.stack.setCurrentWidget(self.general_settings)
        elif key == 'units':
            self.stack.setCurrentWidget(self.units_view)
            self.units_view.refresh()
        elif key == 'categories':
            self.stack.setCurrentWidget(self.categories_view)
            self.categories_view.refresh()
        elif key == 'warehouses':
            self.stack.setCurrentWidget(self.warehouses_view)
            self.warehouses_view.refresh()
        elif key == 'expense_categories':
            self.stack.setCurrentWidget(self.expense_categories_view)
            self.expense_categories_view.refresh()
        elif key == 'backup_restore':
            self.stack.setCurrentWidget(self.backup_restore_view)
            self.backup_restore_view.load_backups()
            
    def refresh(self):
        """Refresh current settings view."""
        current_widget = self.stack.currentWidget()
        if hasattr(current_widget, 'refresh'):
            current_widget.refresh()
