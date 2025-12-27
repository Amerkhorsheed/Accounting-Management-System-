"""
Card Widgets
"""
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor

from ..config import Colors, Fonts


class Card(QFrame):
    """
    Base card widget with shadow effect.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setProperty("class", "card")
        self.setup_shadow()
        
    def setup_shadow(self):
        """Add shadow effect."""
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 20))  # Softer shadow
        self.setGraphicsEffect(shadow)


class StatCard(Card):
    """
    Statistics card widget for dashboard.
    """
    
    def __init__(self, title: str, value: str, icon: str = "", 
                 color: str = None, change: str = None, parent=None):
        super().__init__(parent)
        self.accent_color = color or Colors.PRIMARY
        self.setup_ui(title, value, icon, change)
        
    def setup_ui(self, title: str, value: str, icon: str, change: str):
        """Initialize card UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        # Top row: icon and change
        top_layout = QHBoxLayout()
        
        # Icon
        if icon:
            icon_label = QLabel(icon)
            icon_label.setFixedSize(48, 48)
            icon_label.setAlignment(Qt.AlignCenter)
            icon_label.setStyleSheet(f"""
                font-size: 24px;
                background: {self.accent_color}15;
                color: {self.accent_color};
                border-radius: 12px;
            """)
            top_layout.addWidget(icon_label)
        
        top_layout.addStretch()
        
        # Change indicator
        if change:
            change_label = QLabel(change)
            is_positive = not change.startswith('-')
            change_color = Colors.SUCCESS if is_positive else Colors.DANGER
            change_label.setStyleSheet(f"""
                color: {change_color};
                font-size: 12px;
                font-weight: bold;
                background: {change_color}15;
                padding: 4px 10px;
                border-radius: 20px;
            """)
            top_layout.addWidget(change_label)
        
        layout.addLayout(top_layout)
        
        # Value
        value_label = QLabel(value)
        value_label.setFont(QFont(Fonts.FAMILY_AR, 22, QFont.Bold))
        value_label.setProperty("class", "stat-value")
        # Direct color for value to ensure visibility if theme property isn't enough
        # But we'll rely on the global QWidget/QLabel style first.
        layout.addWidget(value_label)
        
        # Title
        title_label = QLabel(title)
        title_label.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_BODY, QFont.Medium))
        title_label.setProperty("class", "subtitle")
        layout.addWidget(title_label)
        
    def update_value(self, value: str):
        """Update the displayed value."""
        for child in self.findChildren(QLabel):
            if child.property("class") == "stat-value":
                child.setText(value)
                break


class InfoCard(Card):
    """
    Information card with key-value pairs.
    """
    
    def __init__(self, title: str, data: dict, parent=None):
        super().__init__(parent)
        self.setup_ui(title, data)
        
    def setup_ui(self, title: str, data: dict):
        """Initialize card UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # Title
        title_label = QLabel(title)
        title_label.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_H3, QFont.Bold))
        layout.addWidget(title_label)
        
        # Data rows
        for key, value in data.items():
            row_layout = QHBoxLayout()
            
            key_label = QLabel(key)
            key_label.setProperty("class", "subtitle")
            row_layout.addWidget(key_label)
            
            row_layout.addStretch()
            
            value_label = QLabel(str(value))
            value_label.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_BODY, QFont.Bold))
            row_layout.addWidget(value_label)
            
            layout.addLayout(row_layout)
