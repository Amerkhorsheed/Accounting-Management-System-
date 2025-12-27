"""
Header Widget
"""
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QWidget
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from ..config import Colors, Fonts


class Header(QFrame):
    """
    Header component with title, search, and actions.
    """
    
    search_requested = Signal(str)
    theme_toggled = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("header")
        self.setFixedHeight(70)
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize header UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 0, 24, 0)
        layout.setSpacing(16)
        
        # Add subtle shadow for depth
        from PySide6.QtWidgets import QGraphicsDropShadowEffect
        from PySide6.QtGui import QColor
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 20))
        self.setGraphicsEffect(shadow)
        
        # Title area
        self.title_label = QLabel("لوحة التحكم")
        self.title_label.setProperty("class", "h2")
        self.title_label.setFixedWidth(200)
        layout.addWidget(self.title_label)
        
        layout.addStretch()
        
        # Search box - Professional Pill Shape
        self.search_input = QLineEdit()
        self.search_input.setObjectName("header_search")
        self.search_input.setPlaceholderText("🔍 بحث في النظام...")
        self.search_input.setFixedWidth(400)
        self.search_input.returnPressed.connect(self.on_search)
        layout.addWidget(self.search_input)
        
        layout.addStretch()
        
        # Theme toggle
        self.theme_btn = QPushButton("🌙")
        self.theme_btn.setProperty("class", "icon-btn")
        self.theme_btn.setFixedSize(40, 40)
        self.theme_btn.clicked.connect(self.on_theme_toggle)
        layout.addWidget(self.theme_btn)
        
        # Professional User Module
        user_module = QWidget()
        user_module.setObjectName("header_user_module")
        user_layout = QHBoxLayout(user_module)
        user_layout.setContentsMargins(4, 4, 16, 4)
        user_layout.setSpacing(10)
        
        user_avatar = QLabel("👤")
        user_avatar.setStyleSheet("""
            background-color: #E2E8F0;
            border-radius: 14px;
            padding: 4px;
            font-size: 16px;
        """)
        user_avatar.setFixedSize(28, 28)
        user_avatar.setAlignment(Qt.AlignCenter)
        user_layout.addWidget(user_avatar)
        
        self.user_name_label = QLabel("المستخدم")
        self.user_name_label.setObjectName("header_user_name")
        user_layout.addWidget(self.user_name_label)
        
        layout.addWidget(user_module)
        
    def set_title(self, title: str):
        """Set the header title."""
        self.title_label.setText(title)
    
    def set_user(self, user: dict):
        """Set the current user info in header."""
        if user:
            name = user.get('full_name') or user.get('username', 'المستخدم')
            self.user_name_label.setText(name)
        
    def on_search(self):
        """Handle search input."""
        query = self.search_input.text().strip()
        if query:
            self.search_requested.emit(query)
            
    def on_theme_toggle(self):
        """Toggle theme."""
        # Toggle icon
        current = self.theme_btn.text()
        self.theme_btn.setText("☀️" if current == "🌙" else "🌙")
        self.theme_toggled.emit()
