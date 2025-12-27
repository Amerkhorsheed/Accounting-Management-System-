"""
Theme Manager - QSS Stylesheets
"""
from ..config import Colors, Fonts


class ThemeManager:
    """Manages application themes and stylesheets."""
    
    def get_stylesheet(self, theme: str = 'light') -> str:
        """Get the complete stylesheet for the theme."""
        if theme == 'dark':
            return self._dark_theme()
        return self._light_theme()
    
    def _light_theme(self) -> str:
        """Generate light theme stylesheet."""
        return f"""
            /* Base Widget Styles */
            QWidget {{
                background-color: {Colors.LIGHT_BG};
                color: {Colors.LIGHT_TEXT};
                font-family: "{Fonts.FAMILY_AR}";
                font-size: {Fonts.SIZE_BODY}px;
            }}
            
            /* Top Level & Specific Containers */
            QMainWindow, QDialog, QMessageBox, QMenu, QFrame.card {{
                background-color: {Colors.LIGHT_CARD};
            }}
            
            /* Scroll Areas */
            QScrollArea, QScrollArea > QWidget, QScrollArea > QWidget > QWidget {{
                background-color: {Colors.LIGHT_BG};
                border: none;
            }}
            
            /* Transparent Elements */
            QLabel, QCheckBox, QRadioButton, QGroupBox::title, QFrame#header, QToolButton {{
                background-color: transparent;
            }}
            
            QLabel.title {{
                font-size: 28px;
                font-weight: bold;
                color: {Colors.LIGHT_TEXT};
                margin-bottom: 4px;
            }}
            
            QLabel.subtitle {{
                font-size: 14px;
                color: {Colors.LIGHT_TEXT_SECONDARY};
                margin-bottom: 8px;
            }}
            
            QLabel.h2 {{
                font-size: 20px;
                font-weight: bold;
                color: {Colors.LIGHT_TEXT};
            }}
            
            /* Group Boxes */
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {Colors.LIGHT_BORDER};
                border-radius: 16px;
                margin-top: 25px;
                padding-top: 25px;
                background-color: {Colors.LIGHT_CARD};
            }}
            
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top right;
                padding: 0 10px;
                color: {Colors.PRIMARY};
                background-color: transparent;
            }}
            
            /* Buttons */
            QPushButton {{
                background-color: {Colors.PRIMARY};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 500;
                min-height: 40px;
            }}
            
            QPushButton:hover {{
                background-color: {Colors.PRIMARY_DARK};
            }}
            
            QPushButton:pressed {{
                background-color: {Colors.PRIMARY_LIGHT};
            }}
            
            QPushButton:disabled {{
                background-color: {Colors.LIGHT_BORDER};
                color: {Colors.LIGHT_TEXT_SECONDARY};
            }}
            
            QPushButton.secondary {{
                background-color: transparent;
                color: {Colors.PRIMARY};
                border: 2px solid {Colors.PRIMARY};
            }}
            
            QPushButton.secondary:hover {{
                background-color: {Colors.PRIMARY}10;
            }}
            
            QPushButton.danger {{
                background-color: {Colors.DANGER};
            }}
            
            QPushButton.success {{
                background-color: {Colors.SUCCESS};
            }}
            
            QPushButton[style="large"] {{
                font-size: 18px;
                font-weight: bold;
            }}
            
            QPushButton.icon-btn {{
                background: transparent;
                border: none;
                padding: 8px;
                border-radius: 6px;
                color: {Colors.LIGHT_TEXT};
            }}
            
            QPushButton.icon-btn:hover {{
                background: {Colors.LIGHT_BORDER}80;
            }}
            
            /* Sidebar Buttons */
            QPushButton.sidebar-btn {{
                background: transparent;
                border: none;
                border-radius: 10px;
                padding: 4px;
                text-align: right;
                margin: 2px 8px;
            }}
            
            QPushButton.sidebar-btn:hover {{
                background: {Colors.SIDEBAR_HOVER_LIGHT};
            }}
            
            QPushButton.sidebar-btn:checked {{
                background: {Colors.SIDEBAR_ACTIVE};
            }}
            
            QLabel#sidebar_icon {{
                font-size: 18px;
                background: transparent;
                color: {Colors.SIDEBAR_TEXT_LIGHT};
            }}
            
            QLabel#sidebar_text {{
                font-weight: 500;
                background: transparent;
                color: {Colors.SIDEBAR_TEXT_LIGHT};
            }}
            
            QPushButton.sidebar-btn:checked > QLabel {{
                color: white;
                font-weight: bold;
            }}
            
            QFrame#sidebar_active_indicator {{
                background-color: white;
                border-radius: 2px;
            }}
            
            /* Professional Sidebar Brand Area */
            QWidget#sidebar_brand_area {{
                background-color: {Colors.SIDEBAR_BG_LIGHT};
                margin-bottom: 20px;
                border-bottom: 1px solid {Colors.SIDEBAR_HOVER_LIGHT};
            }}
            
            QLabel#sidebar_logo {{
                font-size: 22px;
                font-weight: 900;
                color: {Colors.PRIMARY};
                padding: 10px;
                letter-spacing: 1px;
            }}
            
            /* Modern Header Elements */
            QLineEdit#header_search {{
                background-color: {Colors.LIGHT_BG};
                border: 1px solid {Colors.LIGHT_BORDER};
                border-radius: 18px;
                padding: 6px 18px;
                font-size: 13px;
                color: {Colors.LIGHT_TEXT};
                min-height: 36px;
            }}
            
            QLineEdit#header_search:focus {{
                border-color: {Colors.PRIMARY};
                background-color: white;
            }}
            
            QWidget#header_user_module {{
                background-color: {Colors.LIGHT_BG};
                border-radius: 18px;
                padding: 2px 8px;
                border: 1px solid {Colors.LIGHT_BORDER};
            }}
            
            QLabel#header_user_name {{
                font-weight: 600;
                color: {Colors.LIGHT_TEXT};
                font-size: 13px;
            }}
            
            /* Input Widgets */
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QTextEdit {{
                background-color: {Colors.INPUT_BG_LIGHT};
                border: 1px solid {Colors.INPUT_BORDER_LIGHT};
                border-radius: 8px;
                padding: 10px 15px;
                min-height: 40px;
                color: {Colors.LIGHT_TEXT};
                selection-background-color: {Colors.PRIMARY};
            }}
            
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus, QTextEdit:focus {{
                border: 2px solid {Colors.INPUT_FOCUS};
                background-color: white;
            }}
            
            QComboBox::drop-down {{
                border: none;
                width: 30px;
            }}
            
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {Colors.LIGHT_TEXT_SECONDARY};
                margin-right: 10px;
            }}
            
            QLineEdit[state="error"] {{
                border-color: {Colors.DANGER};
                background-color: {Colors.DANGER}10;
            }}
            
            /* Table Widget */
            QTableWidget, QTableView {{
                background-color: {Colors.LIGHT_CARD};
                border: 1px solid {Colors.LIGHT_BORDER};
                border-radius: 8px;
                gridline-color: {Colors.LIGHT_BORDER};
                alternate-background-color: {Colors.TABLE_ROW_ALT_LIGHT};
            }}
            
            QHeaderView::section {{
                background-color: {Colors.TABLE_HEADER_LIGHT};
                color: {Colors.LIGHT_TEXT};
                padding: 12px;
                border: none;
                border-bottom: 2px solid {Colors.LIGHT_BORDER};
                font-weight: bold;
            }}
            
            QTableWidget::item:selected {{
                background-color: {Colors.PRIMARY}20;
                color: {Colors.PRIMARY};
            }}
            
            /* Progress Bar */
            QProgressBar {{
                background-color: {Colors.LIGHT_BORDER};
                border: none;
                border-radius: 4px;
                height: 8px;
                text-align: center;
            }}
            
            QProgressBar::chunk {{
                background-color: {Colors.PRIMARY};
                border-radius: 4px;
            }}
            
            /* Scroll Bar */
            QScrollBar:vertical {{
                background: transparent;
                width: 8px;
                margin: 0;
            }}
            
            QScrollBar::handle:vertical {{
                background: {Colors.LIGHT_BORDER};
                border-radius: 4px;
                min-height: 20px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background: {Colors.LIGHT_TEXT_SECONDARY}40;
            }}
            
            /* Cards */
            QFrame.card {{
                background-color: {Colors.LIGHT_CARD};
                border: 1px solid {Colors.LIGHT_BORDER};
                border-radius: 16px;
            }}
            
            QFrame#sidebar {{
                background-color: {Colors.SIDEBAR_BG_LIGHT};
                border: none;
            }}
            
            QFrame#header {{
                background-color: white;
                border-bottom: 1px solid {Colors.LIGHT_BORDER};
            }}
        """
    
    def _dark_theme(self) -> str:
        """Generate dark theme stylesheet."""
        return f"""
            /* Base Widget Styles */
            QWidget {{
                background-color: {Colors.DARK_BG};
                color: {Colors.DARK_TEXT};
                font-family: "{Fonts.FAMILY_AR}";
                font-size: {Fonts.SIZE_BODY}px;
            }}
            
            /* Top Level & Specific Containers */
            QMainWindow, QDialog, QMessageBox, QMenu, QFrame.card {{
                background-color: {Colors.DARK_CARD};
            }}
            
            /* Scroll Areas */
            QScrollArea, QScrollArea > QWidget, QScrollArea > QWidget > QWidget {{
                background-color: {Colors.DARK_BG};
                border: none;
            }}
            
            /* Transparent Elements */
            QLabel, QCheckBox, QRadioButton, QGroupBox::title, QFrame#header, QToolButton {{
                background-color: transparent;
            }}
            
            QLabel.title {{
                font-size: 28px;
                font-weight: bold;
                color: {Colors.DARK_TEXT};
                margin-bottom: 4px;
            }}
            
            QLabel.subtitle {{
                font-size: 14px;
                color: {Colors.DARK_TEXT_SECONDARY};
                margin-bottom: 8px;
            }}
            
            QLabel.h2 {{
                font-size: 20px;
                font-weight: bold;
                color: {Colors.DARK_TEXT};
            }}
            
            /* Group Boxes */
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {Colors.DARK_BORDER};
                border-radius: 16px;
                margin-top: 25px;
                padding-top: 25px;
                background-color: {Colors.DARK_CARD};
            }}
            
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top right;
                padding: 0 10px;
                color: {Colors.PRIMARY_LIGHT};
                background-color: transparent;
            }}
            
            /* Buttons */
            QPushButton {{
                background-color: {Colors.PRIMARY};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 500;
                min-height: 40px;
            }}
            
            QPushButton:hover {{
                background-color: {Colors.PRIMARY_LIGHT};
            }}
            
            QPushButton.secondary {{
                background-color: transparent;
                color: {Colors.PRIMARY_LIGHT};
                border: 2px solid {Colors.PRIMARY};
            }}
            
            QPushButton.danger {{
                background-color: {Colors.DANGER};
            }}
            
            QPushButton.success {{
                background-color: {Colors.SUCCESS};
            }}
            
            QPushButton[style="large"] {{
                font-size: 18px;
                font-weight: bold;
            }}
            
            QPushButton.icon-btn {{
                background: transparent;
                border: none;
                padding: 8px;
                border-radius: 6px;
                color: {Colors.DARK_TEXT};
            }}
            
            QPushButton.icon-btn:hover {{
                background: {Colors.DARK_BORDER}80;
            }}
            
            /* Sidebar Buttons */
            QPushButton.sidebar-btn {{
                background: transparent;
                border: none;
                border-radius: 10px;
                padding: 4px;
                text-align: right;
                margin: 2px 8px;
            }}
            
            QPushButton.sidebar-btn:hover {{
                background: {Colors.SIDEBAR_HOVER_DARK};
            }}
            
            QPushButton.sidebar-btn:checked {{
                background: {Colors.SIDEBAR_ACTIVE};
            }}
            
            QLabel#sidebar_icon {{
                font-size: 18px;
                background: transparent;
                color: {Colors.SIDEBAR_TEXT_DARK};
            }}
            
            QLabel#sidebar_text {{
                font-weight: 500;
                background: transparent;
                color: {Colors.SIDEBAR_TEXT_DARK};
            }}
            
            QPushButton.sidebar-btn:checked > QLabel {{
                color: white;
                font-weight: bold;
            }}
            
            QFrame#sidebar_active_indicator {{
                background-color: white;
                border-radius: 2px;
            }}
            
            /* Professional Sidebar Brand Area */
            QWidget#sidebar_brand_area {{
                background-color: {Colors.SIDEBAR_BG_DARK};
                margin-bottom: 20px;
                border-bottom: 1px solid {Colors.SIDEBAR_HOVER_DARK};
            }}
            
            QLabel#sidebar_logo {{
                font-size: 22px;
                font-weight: 900;
                color: white;
                padding: 10px;
                letter-spacing: 1px;
            }}
            
            QLabel#sidebar_tagline {{
                color: {Colors.SIDEBAR_TEXT_DARK}80;
                font-size: 11px;
                margin-right: 10px;
            }}

            QPushButton#sidebar_logout_btn > QLabel#sidebar_text {{
                color: #F87171;
            }}
            
            /* Modern Header Elements */
            QLineEdit#header_search {{
                background-color: {Colors.DARK_BG};
                border: 1px solid {Colors.DARK_BORDER};
                border-radius: 18px;
                padding: 6px 18px;
                font-size: 13px;
                color: {Colors.DARK_TEXT};
                min-height: 36px;
            }}
            
            QLineEdit#header_search:focus {{
                border-color: {Colors.PRIMARY};
                background-color: {Colors.DARK_CARD};
            }}
            
            QWidget#header_user_module {{
                background-color: {Colors.DARK_BG};
                border-radius: 18px;
                padding: 2px 8px;
                border: 1px solid {Colors.DARK_BORDER};
            }}
            
            QLabel#header_user_name {{
                font-weight: 600;
                color: {Colors.DARK_TEXT};
                font-size: 13px;
            }}
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QTextEdit {{
                background-color: {Colors.INPUT_BG_DARK};
                border: 1px solid {Colors.INPUT_BORDER_DARK};
                border-radius: 8px;
                padding: 10px 15px;
                min-height: 40px;
                color: {Colors.DARK_TEXT};
                selection-background-color: {Colors.PRIMARY};
            }}
            
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus, QTextEdit:focus {{
                border: 2px solid {Colors.PRIMARY};
            }}
            
            QComboBox::drop-down {{
                border: none;
                width: 30px;
            }}
            
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid {Colors.DARK_TEXT_SECONDARY};
                margin-right: 10px;
            }}
            
            QLineEdit[state="error"] {{
                border-color: {Colors.DANGER};
                background-color: {Colors.DANGER}20;
            }}
            
            /* Table Widget */
            QTableWidget, QTableView {{
                background-color: {Colors.DARK_CARD};
                border: 1px solid {Colors.DARK_BORDER};
                border-radius: 8px;
                gridline-color: {Colors.DARK_BORDER};
                alternate-background-color: {Colors.TABLE_ROW_ALT_DARK};
            }}
            
            QHeaderView::section {{
                background-color: {Colors.TABLE_HEADER_DARK};
                color: {Colors.DARK_TEXT};
                padding: 12px;
                border: none;
                border-bottom: 2px solid {Colors.DARK_BORDER};
                font-weight: bold;
            }}
            
            QTableWidget::item:selected {{
                background-color: {Colors.PRIMARY}40;
                color: white;
            }}
            
            /* Progress Bar */
            QProgressBar {{
                background-color: {Colors.DARK_BORDER};
                border: none;
                border-radius: 4px;
                height: 8px;
                text-align: center;
            }}
            
            QProgressBar::chunk {{
                background-color: {Colors.PRIMARY};
                border-radius: 4px;
            }}
            
            /* Scroll Bar */
            QScrollBar:vertical {{
                background: transparent;
                width: 8px;
                margin: 0;
            }}
            
            QScrollBar::handle:vertical {{
                background: {Colors.DARK_BORDER};
                border-radius: 4px;
                min-height: 20px;
            }}
            
            /* Cards */
            QFrame.card {{
                background-color: {Colors.DARK_CARD};
                border: 1px solid {Colors.DARK_BORDER};
                border-radius: 16px;
            }}
            
            QFrame#sidebar {{
                background-color: {Colors.SIDEBAR_BG_LIGHT};
                border: none;
            }}
            
            QFrame#header {{
                background-color: {Colors.DARK_CARD};
                border-bottom: 1px solid {Colors.DARK_BORDER};
            }}
        """
