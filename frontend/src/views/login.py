from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFrame, QMessageBox,
    QWidget, QSpacerItem, QSizePolicy, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal, QSize, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QPixmap, QColor, QPalette, QBrush

from ..config import Colors, Fonts
from ..services.auth import AuthService, AuthException


class LoginDialog(QDialog):
    """
    Super Modern Login dialog for user authentication.
    Tailored for a premium tobacco store experience.
    """
    
    login_successful = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("تسجيل الدخول - عامر خورشيد")
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setup_ui()
        self.showMaximized()
        
    def setup_ui(self):
        """Initialize the modern full-screen login UI."""
        # Main container layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Background Layer
        self.bg_label = QLabel(self)
        bg_pixmap = QPixmap("C:/Users/ahmad/.gemini/antigravity/brain/af9e977c-0547-446d-b618-cafc16f1d5d6/premium_tobacco_background_1766568155865.png")
        self.bg_label.setPixmap(bg_pixmap)
        self.bg_label.setScaledContents(True)
        self.bg_label.resize(self.size())
        
        # Overlay for darkening/blur effect
        self.overlay = QFrame(self)
        self.overlay.setStyleSheet("background-color: rgba(18, 18, 18, 160);")
        self.overlay.resize(self.size())
        
        # Foreground Content Layout
        content_wrapper = QWidget(self)
        content_layout = QHBoxLayout(content_wrapper)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        # Center the login card
        content_layout.addStretch()
        
        # Login Card (Glassmorphism)
        self.login_card = QFrame()
        self.login_card.setFixedWidth(450)
        self.login_card.setObjectName("login_card")
        self.login_card.setStyleSheet(f"""
            #login_card {{
                background-color: rgba(25, 25, 25, 220);
                border: 1px solid rgba(193, 149, 82, 80);
                border-radius: 24px;
            }}
        """)
        
        # Shadow effect for the card
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 10)
        self.login_card.setGraphicsEffect(shadow)
        
        card_layout = QVBoxLayout(self.login_card)
        card_layout.setContentsMargins(50, 60, 50, 60)
        card_layout.setSpacing(15)
        
        # Branding
        title_label = QLabel("عامر خورشيد")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(f"""
            color: #C19552;
            font-size: 36px;
            font-weight: bold;
            font-family: '{Fonts.FAMILY_AR}';
            background: transparent;
        """)
        card_layout.addWidget(title_label)
        
        tagline = QLabel("عالم من الفخامة والتميز") # A world of luxury and excellence
        tagline.setAlignment(Qt.AlignCenter)
        tagline.setStyleSheet(f"""
            color: rgba(255, 255, 255, 180);
            font-size: 16px;
            background: transparent;
        """)
        card_layout.addWidget(tagline)
        
        card_layout.addSpacing(30)
        
        # Inputs Styling
        input_style = f"""
            QLineEdit {{
                background-color: rgba(255, 255, 255, 15);
                border: 1px solid rgba(255, 255, 255, 30);
                border-radius: 12px;
                padding: 15px;
                color: white;
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border: 1px solid #C19552;
                background-color: rgba(255, 255, 255, 25);
            }}
        """
        
        # Username Field
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("اسم المستخدم")
        self.username_input.setStyleSheet(input_style)
        card_layout.addWidget(self.username_input)
        
        # Password Field
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("كلمة المرور")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet(input_style)
        self.password_input.returnPressed.connect(self.do_login)
        card_layout.addWidget(self.password_input)
        
        # Error Area
        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: #FF5252; font-size: 12px; background: transparent;")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.hide()
        card_layout.addWidget(self.error_label)
        
        card_layout.addSpacing(10)
        
        # Login Button
        self.login_btn = QPushButton("دخول النظام") # Enter System
        self.login_btn.setCursor(Qt.PointingHandCursor)
        self.login_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #C19552, stop:1 #E0B36E);
                color: #121212;
                border: none;
                border-radius: 12px;
                padding: 16px;
                font-size: 18px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #D4A764, stop:1 #F0C480);
            }}
            QPushButton:pressed {{
                background: #B08641;
            }}
        """)
        self.login_btn.clicked.connect(self.do_login)
        card_layout.addWidget(self.login_btn)
        
        # Close Button (Top Left of Card or Screen)
        self.close_btn = QPushButton("✕", self)
        self.close_btn.setFixedSize(40, 40)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: rgba(255, 255, 255, 100);
                font-size: 20px;
                border-radius: 20px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 20);
                color: white;
            }
        """)
        self.close_btn.clicked.connect(self.reject)
        
        content_layout.addWidget(self.login_card)
        content_layout.addStretch()
        
        self.main_layout.addWidget(content_wrapper)

    def resizeEvent(self, event):
        """Ensure background and overlay follow window size."""
        self.bg_label.resize(self.size())
        self.overlay.resize(self.size())
        self.close_btn.move(self.width() - 50, 10)
        super().resizeEvent(event)

    def do_login(self):
        """Handle login attempt with high-end transition feel."""
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        if not username or not password:
            self.show_error("يرجى إدخال البيانات المطلوبة") # Please enter required data
            return
            
        self.login_btn.setEnabled(False)
        self.login_btn.setText("جاري التحقق...") # Verifying...
        self.error_label.hide()
        
        try:
            user = AuthService.login(username, password)
            self.login_successful.emit(user)
            self.accept()
            
        except AuthException as e:
            self.show_error("خطأ في اسم المستخدم أو كلمة المرور")
            
        finally:
            self.login_btn.setEnabled(True)
            self.login_btn.setText("دخول النظام")
            
    def show_error(self, message: str):
        """Show error message with subtle animation."""
        self.error_label.setText(message)
        self.error_label.show()
