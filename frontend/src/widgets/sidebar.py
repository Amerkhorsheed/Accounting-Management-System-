"""
Sidebar Navigation Widget
"""
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QScrollArea, QWidget, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont, QIcon

from ..config import config, Colors, Fonts


class SidebarButton(QPushButton):
    """Custom sidebar navigation button with active indicator."""
    
    def __init__(self, text: str, icon_symbol: str, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setFixedHeight(48)
        self.setCursor(Qt.PointingHandCursor)
        self.setProperty("class", "sidebar-btn")
        
        # Internal layout for icon and text
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(16, 0, 16, 0)
        self.layout.setSpacing(12)
        
        # Active indicator (hidden by default)
        self.indicator = QFrame()
        self.indicator.setObjectName("sidebar_active_indicator")
        self.indicator.setFixedWidth(4)
        self.indicator.setFixedHeight(24)
        self.indicator.setVisible(False)
        
        self.icon_label = QLabel(icon_symbol)
        self.icon_label.setObjectName("sidebar_icon")
        
        self.text_label = QLabel(text)
        self.text_label.setObjectName("sidebar_text")
        
        self.layout.addWidget(self.icon_label)
        self.layout.addWidget(self.text_label)
        self.layout.addStretch()
        self.layout.addWidget(self.indicator)

    def setChecked(self, checked: bool):
        super().setChecked(checked)
        self.indicator.setVisible(checked)
        # We handle text color changes via QSS instead of hardcoded style sheets
        self.setProperty("active", checked)
        self.style().unpolish(self)
        self.style().polish(self)


class Sidebar(QFrame):
    """
    Sidebar navigation component with premium menu items.
    """
    
    navigation_clicked = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(config.SIDEBAR_WIDTH)
        self.buttons = {}
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize sidebar UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 24)
        layout.setSpacing(4)
        
        # Professional Brand Area
        brand_area = QWidget()
        brand_area.setObjectName("sidebar_brand_area")
        brand_layout = QVBoxLayout(brand_area)
        brand_layout.setContentsMargins(24, 40, 24, 20)
        
        logo_label = QLabel("عامر خورشيد\n0950051261")
        logo_label.setObjectName("sidebar_logo")
        logo_label.setAlignment(Qt.AlignCenter)
        brand_layout.addWidget(logo_label)
        
        tagline = QLabel("نظام الإدارة المتكامل")
        tagline.setObjectName("sidebar_tagline")
        brand_layout.addWidget(tagline)
        
        layout.addWidget(brand_area)
        
        # Navigation items
        nav_items = [
            ('dashboard', 'لوحة التحكم', '📊'),
            ('pos', 'نقطة البيع', '💳'),
            ('invoices', 'الفواتير', '📄'),
            ('customers', 'العملاء', '👥'),
            ('products', 'المنتجات', '📦'),
            ('purchases', 'المشتريات', '🛒'),
            ('suppliers', 'الموردون', '🏭'),
            ('expenses', 'المصروفات', '💸'),
            ('reports', 'التقارير', '📈'),
        ]
        
        # Scroll area for navigation
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        nav_widget = QWidget()
        nav_layout = QVBoxLayout(nav_widget)
        nav_layout.setContentsMargins(8, 0, 8, 0)
        nav_layout.setSpacing(4)
        
        for key, label, icon in nav_items:
            btn = SidebarButton(label, icon)
            btn.clicked.connect(lambda checked, k=key: self.on_nav_click(k))
            nav_layout.addWidget(btn)
            self.buttons[key] = btn
        
        nav_layout.addStretch()
        scroll.setWidget(nav_widget)
        layout.addWidget(scroll, 1)
        
        # Bottom section
        bottom_frame = QFrame()
        bottom_layout = QVBoxLayout(bottom_frame)
        bottom_layout.setContentsMargins(8, 16, 8, 0)
        bottom_layout.setSpacing(4)
        
        # Settings button
        settings_btn = SidebarButton("الإعدادات", "⚙️")
        settings_btn.clicked.connect(lambda: self.on_nav_click('settings'))
        self.buttons['settings'] = settings_btn
        bottom_layout.addWidget(settings_btn)
        
        # Logout button
        logout_btn = SidebarButton("تسجيل الخروج", "🚪")
        logout_btn.setObjectName("sidebar_logout_btn")
        logout_btn.clicked.connect(lambda: self.on_nav_click('logout'))
        bottom_layout.addWidget(logout_btn)
        
        layout.addWidget(bottom_frame)
        
        # Select dashboard by default
        self.buttons['dashboard'].setChecked(True)
        
    def on_nav_click(self, key: str):
        """Handle navigation button click."""
        # Uncheck all buttons
        for btn in self.buttons.values():
            btn.setChecked(False)
        
        # Check clicked button
        if key in self.buttons:
            self.buttons[key].setChecked(True)
        
        # Emit signal
        self.navigation_clicked.emit(key)
