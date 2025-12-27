"""
Form Widgets
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit,
    QCheckBox, QFrame, QFormLayout, QDialog, QPushButton,
    QScrollArea, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QFont

from ..config import Colors, Fonts


class FormField(QWidget):
    """
    Form field wrapper with label and validation.
    """
    
    value_changed = Signal(object)
    
    def __init__(self, label: str, field_type: str = 'text', 
                 required: bool = False, options: list = None,
                 placeholder: str = None, parent=None):
        super().__init__(parent)
        self.label_text = label
        self.field_type = field_type
        self.required = required
        self.options = options or []
        self.placeholder = placeholder
        self.input_widget = None
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize field UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 16)
        layout.setSpacing(6)
        
        # Label
        label = QLabel(self.label_text + (" *" if self.required else ""))
        label.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_BODY))
        if self.required:
            label.setStyleSheet(f"color: {Colors.LIGHT_TEXT};")
        layout.addWidget(label)
        
        # Input based on type
        if self.field_type == 'text':
            self.input_widget = QLineEdit()
            if self.placeholder:
                self.input_widget.setPlaceholderText(self.placeholder)
            self.input_widget.textChanged.connect(self._on_change)
            
        elif self.field_type == 'textarea':
            self.input_widget = QTextEdit()
            self.input_widget.setMaximumHeight(100)
            self.input_widget.textChanged.connect(self._on_change)
            
        elif self.field_type == 'number':
            self.input_widget = QDoubleSpinBox()
            self.input_widget.setMaximum(999999999)
            self.input_widget.setDecimals(2)
            self.input_widget.valueChanged.connect(self._on_change)
            
        elif self.field_type == 'integer':
            self.input_widget = QSpinBox()
            self.input_widget.setMaximum(999999999)
            self.input_widget.valueChanged.connect(self._on_change)
            
        elif self.field_type == 'select':
            self.input_widget = QComboBox()
            for opt in self.options:
                if isinstance(opt, dict):
                    self.input_widget.addItem(opt['label'], opt['value'])
                else:
                    self.input_widget.addItem(str(opt), opt)
            self.input_widget.currentIndexChanged.connect(self._on_change)
            
        elif self.field_type == 'date':
            self.input_widget = QDateEdit()
            self.input_widget.setCalendarPopup(True)
            self.input_widget.setDate(QDate.currentDate())
            self.input_widget.dateChanged.connect(self._on_change)
            
        elif self.field_type == 'checkbox':
            self.input_widget = QCheckBox()
            self.input_widget.stateChanged.connect(self._on_change)
            
        elif self.field_type == 'password':
            self.input_widget = QLineEdit()
            self.input_widget.setEchoMode(QLineEdit.Password)
            if self.placeholder:
                self.input_widget.setPlaceholderText(self.placeholder)
            self.input_widget.textChanged.connect(self._on_change)
        
        if self.input_widget:
            layout.addWidget(self.input_widget)
            
        # Error label
        self.error_label = QLabel()
        self.error_label.setStyleSheet(f"color: {Colors.DANGER}; font-size: 11px;")
        self.error_label.hide()
        layout.addWidget(self.error_label)
        
    def _on_change(self, value=None):
        """Handle value change."""
        self.clear_error()
        self.value_changed.emit(self.get_value())
        
    def get_value(self):
        """Get field value."""
        if self.field_type == 'text' or self.field_type == 'password':
            return self.input_widget.text()
        elif self.field_type == 'textarea':
            return self.input_widget.toPlainText()
        elif self.field_type in ['number', 'integer']:
            return self.input_widget.value()
        elif self.field_type == 'select':
            return self.input_widget.currentData()
        elif self.field_type == 'date':
            return self.input_widget.date().toString('yyyy-MM-dd')
        elif self.field_type == 'checkbox':
            return self.input_widget.isChecked()
        return None
        
    def set_value(self, value):
        """Set field value."""
        if self.field_type == 'text' or self.field_type == 'password':
            self.input_widget.setText(str(value) if value else '')
        elif self.field_type == 'textarea':
            self.input_widget.setPlainText(str(value) if value else '')
        elif self.field_type in ['number', 'integer']:
            self.input_widget.setValue(float(value) if value else 0)
        elif self.field_type == 'select':
            index = self.input_widget.findData(value)
            if index >= 0:
                self.input_widget.setCurrentIndex(index)
        elif self.field_type == 'date':
            if value:
                self.input_widget.setDate(QDate.fromString(value, 'yyyy-MM-dd'))
        elif self.field_type == 'checkbox':
            self.input_widget.setChecked(bool(value))
            
    def validate(self) -> bool:
        """Validate field value."""
        value = self.get_value()
        
        if self.required:
            if value is None or value == '' or value == 0:
                self.set_error("هذا الحقل مطلوب")
                return False
                
        self.clear_error()
        return True
        
    def set_error(self, message: str):
        """Show error message."""
        self.error_label.setText(message)
        self.error_label.show()
        if self.input_widget:
            self.input_widget.setProperty("state", "error")
            self.input_widget.style().unpolish(self.input_widget)
            self.input_widget.style().polish(self.input_widget)
            
    def clear_error(self):
        """Clear error message."""
        self.error_label.hide()
        if self.input_widget:
            self.input_widget.setProperty("state", "")
            self.input_widget.style().unpolish(self.input_widget)
            self.input_widget.style().polish(self.input_widget)


class FormDialog(QDialog):
    """
    Dialog for creating/editing records.
    """
    
    saved = Signal(dict)
    
    def __init__(self, title: str, fields: list, data: dict = None, parent=None):
        super().__init__(parent)
        self.fields_config = fields
        self.data = data or {}
        self.field_widgets = {}
        self.setWindowTitle(title)
        self.setMinimumWidth(500)
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Scroll area for fields
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create fields
        for field_config in self.fields_config:
            field = FormField(
                label=field_config['label'],
                field_type=field_config.get('type', 'text'),
                required=field_config.get('required', False),
                options=field_config.get('options', []),
                placeholder=field_config.get('placeholder')
            )
            
            # Set initial value if editing
            key = field_config['key']
            if key in self.data:
                field.set_value(self.data[key])
                
            self.field_widgets[key] = field
            form_layout.addWidget(field)
            
        form_layout.addStretch()
        scroll.setWidget(form_widget)
        layout.addWidget(scroll, 1)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        cancel_btn = QPushButton("إلغاء")
        cancel_btn.setProperty("class", "secondary")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("حفظ")
        save_btn.clicked.connect(self.save)
        buttons_layout.addWidget(save_btn)
        
        layout.addLayout(buttons_layout)
        
    def save(self):
        """Validate and save form data."""
        # Validate all fields
        is_valid = True
        for field in self.field_widgets.values():
            if not field.validate():
                is_valid = False
                
        if not is_valid:
            return
            
        # Collect data
        result = {}
        for key, field in self.field_widgets.items():
            result[key] = field.get_value()
            
        self.saved.emit(result)
        self.accept()
        
    def get_data(self) -> dict:
        """Get form data."""
        result = {}
        for key, field in self.field_widgets.items():
            result[key] = field.get_value()
        return result
