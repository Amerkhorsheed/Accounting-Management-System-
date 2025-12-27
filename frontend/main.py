"""
Accounting Management System - PySide6 Application
Entry point for the desktop application.
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QLocale
from PySide6.QtGui import QFont

from src.app import MainApplication


def main():
    """Main entry point for the application."""
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    # Create application
    app = QApplication(sys.argv)
    
    # Set application info
    app.setApplicationName("نظام إدارة المحاسبة")
    app.setApplicationDisplayName("نظام إدارة المحاسبة")
    app.setOrganizationName("ERP Solutions")
    app.setOrganizationDomain("erp-solutions.com")
    
    # Set RTL layout direction
    app.setLayoutDirection(Qt.RightToLeft)
    
    # Set locale to Arabic
    locale = QLocale(QLocale.Arabic)
    QLocale.setDefault(locale)
    
    # Set default font with Arabic support
    font = QFont("Segoe UI", 10)
    font.setStyleHint(QFont.SansSerif)
    app.setFont(font)
    
    # Create and show main window
    main_app = MainApplication()
    main_app.show()
    
    # Run event loop
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
