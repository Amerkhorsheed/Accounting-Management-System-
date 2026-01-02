"""Backup & Restore View - النسخ الاحتياطي والاستعادة - Professional Modern Design"""

from pathlib import Path
from datetime import datetime
from functools import partial

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QCheckBox, QFileDialog, QFrame,
    QGridLayout, QScrollArea, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QGraphicsDropShadowEffect,
    QProgressBar, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor, QBrush

from ...config import Colors, Fonts
from ...widgets.dialogs import MessageDialog, ConfirmDialog
from ...services.api import api, ApiException
from ...utils.error_handler import handle_ui_error


class BackupActionCard(QFrame):
    """Modern action card for backup/restore operations."""
    
    clicked = Signal()
    
    def __init__(self, title: str, description: str, icon: str, color: str, 
                 button_text: str, is_danger: bool = False, parent=None):
        super().__init__(parent)
        self.accent_color = color
        self.is_danger = is_danger
        self.setObjectName("action_card")
        self.setup_ui(title, description, icon, button_text)
        self._apply_style()
        
    def setup_ui(self, title: str, description: str, icon: str, button_text: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Icon
        icon_label = QLabel(icon)
        icon_label.setFixedSize(64, 64)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet(f"""
            font-size: 32px;
            background: {self.accent_color}15;
            color: {self.accent_color};
            border-radius: 16px;
            border: 2px solid {self.accent_color}30;
        """)
        layout.addWidget(icon_label, alignment=Qt.AlignCenter)
        
        # Title
        title_label = QLabel(title)
        title_label.setFont(QFont(Fonts.FAMILY_AR, 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(f"color: {Colors.LIGHT_TEXT}; background: transparent;")
        layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel(description)
        desc_label.setFont(QFont(Fonts.FAMILY_AR, 11))
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(f"color: {Colors.LIGHT_TEXT_SECONDARY}; background: transparent;")
        layout.addWidget(desc_label)
        
        layout.addStretch()
        
        # Action button
        self.action_btn = QPushButton(button_text)
        self.action_btn.setCursor(Qt.PointingHandCursor)
        self.action_btn.setMinimumHeight(44)
        btn_color = Colors.DANGER if self.is_danger else self.accent_color
        self.action_btn.setStyleSheet(f"""
            QPushButton {{
                background: {btn_color};
                color: white;
                border: none;
                border-radius: 10px;
                padding: 12px 24px;
                font-weight: 600;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background: {btn_color}dd;
            }}
            QPushButton:pressed {{
                background: {btn_color}bb;
            }}
        """)
        self.action_btn.clicked.connect(self.clicked.emit)
        layout.addWidget(self.action_btn)
    
    def _apply_style(self):
        self.setStyleSheet(f"""
            QFrame#action_card {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {Colors.LIGHT_CARD}, stop:1 {self.accent_color}05);
                border: 1px solid {Colors.LIGHT_BORDER};
                border-radius: 20px;
                border-top: 4px solid {self.accent_color};
            }}
        """)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setXOffset(0)
        shadow.setYOffset(6)
        shadow.setColor(QColor(0, 0, 0, 12))
        self.setGraphicsEffect(shadow)


class BackupStatCard(QFrame):
    """Statistics card for backup info."""
    
    def __init__(self, title: str, value: str, icon: str, color: str, parent=None):
        super().__init__(parent)
        self.accent_color = color
        self.setObjectName("stat_card")
        self.setup_ui(title, value, icon)
        self._apply_style()
        
    def setup_ui(self, title: str, value: str, icon: str):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)
        
        # Icon
        icon_label = QLabel(icon)
        icon_label.setFixedSize(48, 48)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet(f"""
            font-size: 24px;
            background: {self.accent_color}15;
            color: {self.accent_color};
            border-radius: 12px;
        """)
        layout.addWidget(icon_label)
        
        # Text section
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        
        self.value_label = QLabel(value)
        self.value_label.setFont(QFont(Fonts.FAMILY_AR, 20, QFont.Bold))
        self.value_label.setStyleSheet(f"color: {self.accent_color}; background: transparent;")
        text_layout.addWidget(self.value_label)
        
        title_label = QLabel(title)
        title_label.setFont(QFont(Fonts.FAMILY_AR, 11))
        title_label.setStyleSheet(f"color: {Colors.LIGHT_TEXT_SECONDARY}; background: transparent;")
        text_layout.addWidget(title_label)
        
        layout.addLayout(text_layout)
        layout.addStretch()
    
    def _apply_style(self):
        self.setStyleSheet(f"""
            QFrame#stat_card {{
                background: {Colors.LIGHT_CARD};
                border: 1px solid {Colors.LIGHT_BORDER};
                border-radius: 14px;
                border-left: 4px solid {self.accent_color};
            }}
        """)
        
    def update_value(self, value: str):
        self.value_label.setText(value)


class SectionHeader(QFrame):
    """Section header with icon and title."""
    
    def __init__(self, title: str, icon: str = "", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 12, 0, 12)
        
        if icon:
            icon_lbl = QLabel(icon)
            icon_lbl.setFont(QFont(Fonts.FAMILY_AR, 18))
            icon_lbl.setStyleSheet("background: transparent;")
            layout.addWidget(icon_lbl)
        
        title_lbl = QLabel(title)
        title_lbl.setFont(QFont(Fonts.FAMILY_AR, 16, QFont.Bold))
        title_lbl.setStyleSheet(f"color: {Colors.LIGHT_TEXT}; background: transparent;")
        layout.addWidget(title_lbl)
        layout.addStretch()
        
        self.setStyleSheet("background: transparent;")


class BackupRestoreView(QWidget):
    """Professional Backup & Restore view with modern UI/UX."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._backups = []
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(24)

        # ═══════════════════════════════════════════════════════════
        # HEADER SECTION
        # ═══════════════════════════════════════════════════════════
        header_card = QFrame()
        header_card.setObjectName("header_card")
        header_card.setStyleSheet(f"""
            QFrame#header_card {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Colors.PRIMARY}, stop:1 #6366f1);
                border-radius: 20px;
            }}
        """)
        header_layout = QVBoxLayout(header_card)
        header_layout.setContentsMargins(32, 28, 32, 28)
        header_layout.setSpacing(12)
        
        # Title row
        title_row = QHBoxLayout()
        
        title_icon = QLabel("💾")
        title_icon.setFont(QFont(Fonts.FAMILY_AR, 32))
        title_icon.setStyleSheet("background: transparent;")
        title_row.addWidget(title_icon)
        
        title_text = QVBoxLayout()
        title_text.setSpacing(4)
        
        title = QLabel("النسخ الاحتياطي والاستعادة")
        title.setFont(QFont(Fonts.FAMILY_AR, 24, QFont.Bold))
        title.setStyleSheet("color: white; background: transparent;")
        title_text.addWidget(title)
        
        subtitle = QLabel("حماية بياناتك واستعادتها بسهولة وأمان")
        subtitle.setFont(QFont(Fonts.FAMILY_AR, 13))
        subtitle.setStyleSheet("color: rgba(255,255,255,0.85); background: transparent;")
        title_text.addWidget(subtitle)
        
        title_row.addLayout(title_text)
        title_row.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton("🔄 تحديث")
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255,255,255,0.2);
                color: white;
                border: 1px solid rgba(255,255,255,0.3);
                border-radius: 10px;
                padding: 12px 24px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background: rgba(255,255,255,0.3);
            }}
        """)
        refresh_btn.clicked.connect(self.load_backups)
        title_row.addWidget(refresh_btn)
        
        header_layout.addLayout(title_row)
        
        # Description
        desc = QLabel(
            "قم بإنشاء نسخة احتياطية من بيانات النظام لحمايتها من الفقدان. "
            "يمكنك استعادة البيانات في أي وقت من النسخ المحفوظة."
        )
        desc.setFont(QFont(Fonts.FAMILY_AR, 12))
        desc.setWordWrap(True)
        desc.setStyleSheet("color: rgba(255,255,255,0.75); background: transparent;")
        header_layout.addWidget(desc)
        
        layout.addWidget(header_card)

        # ═══════════════════════════════════════════════════════════
        # STATISTICS SECTION
        # ═══════════════════════════════════════════════════════════
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(16)
        
        self.total_backups_card = BackupStatCard("إجمالي النسخ", "0", "📦", Colors.PRIMARY)
        stats_layout.addWidget(self.total_backups_card)
        
        self.last_backup_card = BackupStatCard("آخر نسخة", "-", "🕐", Colors.SUCCESS)
        stats_layout.addWidget(self.last_backup_card)
        
        self.total_size_card = BackupStatCard("الحجم الكلي", "0 MB", "💿", Colors.INFO)
        stats_layout.addWidget(self.total_size_card)
        
        layout.addLayout(stats_layout)

        # ═══════════════════════════════════════════════════════════
        # ACTION CARDS SECTION
        # ═══════════════════════════════════════════════════════════
        layout.addWidget(SectionHeader("العمليات الرئيسية", "⚡"))
        
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(20)
        
        # Create Backup Card
        self.create_backup_card = BackupActionCard(
            title="إنشاء نسخة احتياطية",
            description="إنشاء نسخة احتياطية جديدة من قاعدة البيانات وجميع البيانات المهمة",
            icon="📤",
            color=Colors.SUCCESS,
            button_text="🔒 إنشاء نسخة جديدة"
        )
        self.create_backup_card.clicked.connect(self._show_create_backup_dialog)
        actions_layout.addWidget(self.create_backup_card)
        
        # Restore Card
        self.restore_card = BackupActionCard(
            title="استعادة من ملف",
            description="استعادة البيانات من نسخة احتياطية محفوظة على جهازك",
            icon="📥",
            color=Colors.DANGER,
            button_text="⚠️ استعادة البيانات",
            is_danger=True
        )
        self.restore_card.clicked.connect(self._show_restore_dialog)
        actions_layout.addWidget(self.restore_card)
        
        layout.addLayout(actions_layout)

        # ═══════════════════════════════════════════════════════════
        # BACKUPS TABLE SECTION
        # ═══════════════════════════════════════════════════════════
        layout.addWidget(SectionHeader("النسخ الاحتياطية المتوفرة", "📋"))
        
        table_card = QFrame()
        table_card.setObjectName("table_card")
        table_card.setStyleSheet(f"""
            QFrame#table_card {{
                background: {Colors.LIGHT_CARD};
                border: 1px solid {Colors.LIGHT_BORDER};
                border-radius: 16px;
            }}
        """)
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(20, 20, 20, 20)
        table_layout.setSpacing(16)
        
        # Table header with info
        table_header = QHBoxLayout()
        
        info_label = QLabel("💡 انقر على أي نسخة لتحميلها أو حذفها")
        info_label.setFont(QFont(Fonts.FAMILY_AR, 11))
        info_label.setStyleSheet(f"""
            color: {Colors.LIGHT_TEXT_SECONDARY};
            background: {Colors.INFO}10;
            padding: 10px 16px;
            border-radius: 8px;
            border-left: 3px solid {Colors.INFO};
        """)
        table_header.addWidget(info_label)
        table_header.addStretch()
        
        table_layout.addLayout(table_header)
        
        # Backups table
        self.backups_table = QTableWidget()
        self.backups_table.setColumnCount(5)
        self.backups_table.setHorizontalHeaderLabels([
            'اسم الملف', 'تاريخ الإنشاء', 'الحجم', 'تحميل', 'حذف'
        ])
        self.backups_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.backups_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.backups_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.backups_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.backups_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        self.backups_table.setColumnWidth(3, 100)
        self.backups_table.setColumnWidth(4, 100)
        self.backups_table.verticalHeader().setVisible(False)
        self.backups_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.backups_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.backups_table.setAlternatingRowColors(True)
        self.backups_table.setMinimumHeight(300)
        self._style_table()
        
        table_layout.addWidget(self.backups_table)
        layout.addWidget(table_card)
        
        # Add stretch
        layout.addStretch()
        
        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    def _style_table(self):
        """Apply modern styling to table."""
        self.backups_table.setStyleSheet(f"""
            QTableWidget {{
                background: {Colors.LIGHT_CARD};
                border: 1px solid {Colors.LIGHT_BORDER};
                border-radius: 12px;
                gridline-color: {Colors.LIGHT_BORDER};
            }}
            QTableWidget::item {{
                padding: 12px 16px;
                border-bottom: 1px solid {Colors.LIGHT_BORDER}50;
            }}
            QTableWidget::item:selected {{
                background: {Colors.PRIMARY}15;
                color: {Colors.PRIMARY};
            }}
            QHeaderView::section {{
                background: {Colors.LIGHT_BG};
                color: {Colors.LIGHT_TEXT};
                padding: 14px;
                border: none;
                border-bottom: 2px solid {Colors.PRIMARY};
                font-weight: bold;
                font-size: 12px;
            }}
        """)

    def _show_create_backup_dialog(self):
        """Show create backup options dialog."""
        # Create options dialog
        dialog = QFrame(self)
        dialog.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        dialog.setObjectName("options_dialog")
        dialog.setStyleSheet(f"""
            QFrame#options_dialog {{
                background: {Colors.LIGHT_CARD};
                border: 1px solid {Colors.LIGHT_BORDER};
                border-radius: 16px;
            }}
        """)
        
        # For now, directly create backup with confirmation
        include_media = False  # Default to not include media for faster backup
        
        if not MessageDialog.confirm(
            self,
            "إنشاء نسخة احتياطية",
            "سيتم إنشاء نسخة احتياطية جديدة من قاعدة البيانات.\n\n"
            "هل تريد المتابعة؟"
        ):
            return
        
        self.create_backup(include_media)

    def _show_restore_dialog(self):
        """Show restore options and file picker."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "اختيار ملف النسخة الاحتياطية",
            str(Path.home()),
            "Backup Files (*.amsbackup *.zip);;All Files (*.*)"
        )
        if not file_path:
            return

        dialog = ConfirmDialog(
            "⚠️ تأكيد الاستعادة",
            "تحذير هام:\n\n"
            "• ستؤدي الاستعادة إلى استبدال جميع البيانات الحالية\n"
            "• لا يمكن التراجع عن هذه العملية\n"
            "• يُنصح بإنشاء نسخة احتياطية قبل الاستعادة\n\n"
            f"الملف المحدد:\n{Path(file_path).name}\n\n"
            "هل أنت متأكد من المتابعة؟",
            confirm_text="تأكيد الاستعادة",
            cancel_text="إلغاء",
            danger=True,
            parent=self
        )
        if dialog.exec() != ConfirmDialog.Accepted:
            return

        self.restore_from_file(file_path)

    def _normalize_backups(self, resp):
        if isinstance(resp, dict) and 'results' in resp:
            return resp.get('results') or []
        if isinstance(resp, list):
            return resp
        return []

    @handle_ui_error
    def load_backups(self):
        """Load and display available backups."""
        resp = api.list_backups()
        self._backups = self._normalize_backups(resp)
        
        total_size = 0
        for item in self._backups:
            try:
                size = int(item.get('size') or 0)
                total_size += size
                item['size_display'] = f"{size/1024.0/1024.0:.2f} MB" if size else "-"
            except Exception:
                item['size_display'] = str(item.get('size') or '-')
        
        # Update statistics
        self.total_backups_card.update_value(str(len(self._backups)))
        self.total_size_card.update_value(f"{total_size/1024.0/1024.0:.2f} MB")
        
        if self._backups:
            last_backup = self._backups[0]
            last_date = last_backup.get('created_at', '-')
            if last_date and last_date != '-':
                try:
                    dt = datetime.fromisoformat(last_date.replace('Z', '+00:00'))
                    last_date = dt.strftime('%Y-%m-%d')
                except:
                    pass
            self.last_backup_card.update_value(last_date)
        else:
            self.last_backup_card.update_value("-")
        
        # Update table
        self._update_table()

    def _update_table(self):
        """Update the backups table."""
        self.backups_table.setRowCount(len(self._backups))
        
        for row, backup in enumerate(self._backups):
            # Filename
            filename = backup.get('filename', '')
            filename_item = QTableWidgetItem(f"📄 {filename}")
            filename_item.setFont(QFont(Fonts.FAMILY_AR, 11, QFont.Medium))
            self.backups_table.setItem(row, 0, filename_item)
            
            # Created date
            created_at = backup.get('created_at', '-')
            if created_at and created_at != '-':
                try:
                    dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    created_at = dt.strftime('%Y-%m-%d %H:%M')
                except:
                    pass
            date_item = QTableWidgetItem(created_at)
            date_item.setTextAlignment(Qt.AlignCenter)
            date_item.setForeground(QBrush(QColor(Colors.LIGHT_TEXT_SECONDARY)))
            self.backups_table.setItem(row, 1, date_item)
            
            # Size
            size_item = QTableWidgetItem(backup.get('size_display', '-'))
            size_item.setTextAlignment(Qt.AlignCenter)
            size_item.setForeground(QBrush(QColor(Colors.INFO)))
            self.backups_table.setItem(row, 2, size_item)
            
            # Download button - direct without container
            download_btn = QPushButton("📥 تحميل")
            download_btn.setCursor(Qt.PointingHandCursor)
            download_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {Colors.SUCCESS};
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 12px;
                    font-size: 11px;
                    margin: 4px;
                }}
                QPushButton:hover {{
                    background: {Colors.SUCCESS}dd;
                }}
            """)
            download_btn.clicked.connect(partial(self._download_backup, row))
            self.backups_table.setCellWidget(row, 3, download_btn)
            
            # Delete button - direct without container
            delete_btn = QPushButton("🗑️ حذف")
            delete_btn.setCursor(Qt.PointingHandCursor)
            delete_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {Colors.DANGER};
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 12px;
                    font-size: 11px;
                    margin: 4px;
                }}
                QPushButton:hover {{
                    background: {Colors.DANGER}dd;
                }}
            """)
            delete_btn.clicked.connect(partial(self._delete_backup, row))
            self.backups_table.setCellWidget(row, 4, delete_btn)
        
        # Show empty state if no backups
        if not self._backups:
            self.backups_table.setRowCount(1)
            empty_item = QTableWidgetItem("لا توجد نسخ احتياطية متوفرة")
            empty_item.setTextAlignment(Qt.AlignCenter)
            empty_item.setForeground(QBrush(QColor(Colors.LIGHT_TEXT_SECONDARY)))
            empty_item.setFont(QFont(Fonts.FAMILY_AR, 12))
            self.backups_table.setItem(0, 0, empty_item)
            self.backups_table.setSpan(0, 0, 1, 5)

    @handle_ui_error
    def create_backup(self, include_media: bool = False):
        """Create a new backup."""
        try:
            api.create_backup(include_media=include_media)
            MessageDialog.success(self, "نجاح ✅", "تم إنشاء النسخة الاحتياطية بنجاح")
            self.load_backups()
        except ApiException as e:
            MessageDialog.error(self, "خطأ", str(e))

    @handle_ui_error
    def _download_backup(self, row: int):
        """Download a backup file."""
        if row < 0 or row >= len(self._backups):
            MessageDialog.warning(self, "تنبيه", "لم يتم العثور على النسخة الاحتياطية")
            return
            
        backup = self._backups[row]
        filename = backup.get('filename')
        if not filename:
            MessageDialog.warning(self, "تنبيه", "اسم الملف غير موجود")
            return

        suggested = str(Path.home() / 'Downloads' / filename)
        dest_path, _ = QFileDialog.getSaveFileName(
            self,
            "حفظ النسخة الاحتياطية",
            suggested,
            "Backup Files (*.amsbackup *.zip);;All Files (*.*)"
        )
        if not dest_path:
            return

        try:
            api.download_backup_to_file(filename, dest_path)
            MessageDialog.success(self, "نجاح ✅", f"تم حفظ النسخة الاحتياطية في:\n{dest_path}")
        except Exception as e:
            MessageDialog.error(self, "خطأ", f"فشل تحميل النسخة الاحتياطية:\n{str(e)}")

    @handle_ui_error
    def _delete_backup(self, row: int):
        """Delete a backup file."""
        if row < 0 or row >= len(self._backups):
            MessageDialog.warning(self, "تنبيه", "لم يتم العثور على النسخة الاحتياطية")
            return
            
        backup = self._backups[row]
        filename = backup.get('filename')
        if not filename:
            MessageDialog.warning(self, "تنبيه", "اسم الملف غير موجود")
            return

        dialog = ConfirmDialog(
            "حذف النسخة الاحتياطية",
            f"هل تريد حذف النسخة الاحتياطية التالية؟\n\n📄 {filename}\n\n"
            "لا يمكن التراجع عن هذه العملية.",
            confirm_text="حذف",
            cancel_text="إلغاء",
            danger=True,
            parent=self
        )
        if dialog.exec() != ConfirmDialog.Accepted:
            return

        try:
            api.delete_backup(filename)
            MessageDialog.success(self, "نجاح ✅", "تم حذف النسخة الاحتياطية")
            self.load_backups()
        except Exception as e:
            MessageDialog.error(self, "خطأ", f"فشل حذف النسخة الاحتياطية:\n{str(e)}")

    @handle_ui_error
    def restore_from_file(self, file_path: str):
        """Restore from a backup file."""
        restore_media = True
        replace_media = False

        api.restore_backup_from_file(
            file_path=file_path,
            restore_media=restore_media,
            replace_media=replace_media,
        )
        MessageDialog.success(
            self,
            "نجاح ✅",
            "تمت الاستعادة بنجاح!\n\n"
            "يُفضل إعادة تشغيل التطبيق لضمان تحديث جميع البيانات."
        )
        self.load_backups()

    def refresh(self):
        """Refresh the view."""
        self.load_backups()
