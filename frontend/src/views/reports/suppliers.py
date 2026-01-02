"""Suppliers Report View - تقرير الموردين - Professional Modern Design"""

from datetime import datetime
from typing import Dict, List

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QDateEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QFrame, QGridLayout,
    QScrollArea, QGraphicsDropShadowEffect, QProgressBar
)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QFont, QBrush, QColor

from ...config import Colors, Fonts, config
from ...widgets.cards import Card
from ...widgets.dialogs import MessageDialog
from ...services.api import api, ApiException
from ...services.export import ExportService, ExportError
from ...utils.error_handler import handle_ui_error


class SupplierMetricCard(QFrame):
    """Modern metric card for supplier data."""
    
    def __init__(self, title: str, value: str, icon: str, color: str,
                 subtitle: str = "", parent=None):
        super().__init__(parent)
        self.accent_color = color
        self.setObjectName("supplier_metric_card")
        self.setup_ui(title, value, icon, subtitle)
        self._apply_style()
        
    def setup_ui(self, title: str, value: str, icon: str, subtitle: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(8)
        
        top = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setFixedSize(44, 44)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet(f"""
            font-size: 22px;
            background: {self.accent_color}18;
            color: {self.accent_color};
            border-radius: 12px;
            border: 1px solid {self.accent_color}30;
        """)
        top.addWidget(icon_label)
        top.addStretch()
        layout.addLayout(top)
        
        self.value_label = QLabel(value)
        self.value_label.setFont(QFont(Fonts.FAMILY_AR, 26, QFont.Bold))
        self.value_label.setStyleSheet(f"color: {self.accent_color}; background: transparent;")
        layout.addWidget(self.value_label)
        
        title_label = QLabel(title)
        title_label.setFont(QFont(Fonts.FAMILY_AR, 12, QFont.Medium))
        title_label.setStyleSheet(f"color: {Colors.LIGHT_TEXT_SECONDARY}; background: transparent;")
        layout.addWidget(title_label)
        
        if subtitle:
            sub_label = QLabel(subtitle)
            sub_label.setFont(QFont(Fonts.FAMILY_AR, 10))
            sub_label.setStyleSheet(f"color: {Colors.LIGHT_TEXT_SECONDARY}80; background: transparent;")
            layout.addWidget(sub_label)
    
    def _apply_style(self):
        self.setStyleSheet(f"""
            QFrame#supplier_metric_card {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {Colors.LIGHT_CARD}, stop:1 {self.accent_color}08);
                border: 1px solid {Colors.LIGHT_BORDER};
                border-radius: 16px;
                border-left: 4px solid {self.accent_color};
            }}
        """)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 15))
        self.setGraphicsEffect(shadow)
        
    def update_value(self, value: str):
        self.value_label.setText(value)


class SectionHeader(QFrame):
    def __init__(self, title: str, icon: str = "", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 12)
        if icon:
            icon_lbl = QLabel(icon)
            icon_lbl.setFont(QFont(Fonts.FAMILY_AR, 16))
            icon_lbl.setStyleSheet("background: transparent;")
            layout.addWidget(icon_lbl)
        title_lbl = QLabel(title)
        title_lbl.setFont(QFont(Fonts.FAMILY_AR, 16, QFont.Bold))
        title_lbl.setStyleSheet(f"color: {Colors.LIGHT_TEXT}; background: transparent;")
        layout.addWidget(title_lbl)
        layout.addStretch()
        self.setStyleSheet("background: transparent;")


class SuppliersReportView(QWidget):
    """Professional Suppliers report view with modern UI/UX."""
    
    back_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.report_data: Dict = {}
        self.suppliers_list: List[Dict] = []
        self.setup_ui()
    
    def go_back(self):
        self.back_requested.emit()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(20)

        # Header
        header_card = QFrame()
        header_card.setObjectName("header_card")
        header_card.setStyleSheet(f"""
            QFrame#header_card {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Colors.SECONDARY}, stop:1 #14B8A6);
                border-radius: 16px;
            }}
        """)
        header_layout = QHBoxLayout(header_card)
        header_layout.setContentsMargins(24, 20, 24, 20)
        
        back_btn = QPushButton("→ رجوع")
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255,255,255,0.2);
                color: white;
                border: 1px solid rgba(255,255,255,0.3);
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: 500;
            }}
            QPushButton:hover {{ background: rgba(255,255,255,0.3); }}
        """)
        back_btn.clicked.connect(self.go_back)
        header_layout.addWidget(back_btn)
        
        title_section = QVBoxLayout()
        title_section.setSpacing(4)
        title = QLabel("🏭 تقرير الموردين")
        title.setFont(QFont(Fonts.FAMILY_AR, 22, QFont.Bold))
        title.setStyleSheet("color: white; background: transparent;")
        title_section.addWidget(title)
        
        subtitle = QLabel("تحليل شامل لبيانات الموردين والمشتريات والمستحقات")
        subtitle.setFont(QFont(Fonts.FAMILY_AR, 12))
        subtitle.setStyleSheet("color: rgba(255,255,255,0.85); background: transparent;")
        title_section.addWidget(subtitle)
        header_layout.addLayout(title_section)
        header_layout.addStretch()
        
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(10)
        
        refresh_btn = QPushButton("🔄 تحديث")
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255,255,255,0.15);
                color: white;
                border: 1px solid rgba(255,255,255,0.25);
                border-radius: 8px;
                padding: 10px 18px;
            }}
            QPushButton:hover {{ background: rgba(255,255,255,0.25); }}
        """)
        refresh_btn.clicked.connect(self.refresh)
        actions_layout.addWidget(refresh_btn)
        
        export_excel_btn = QPushButton("📊 Excel")
        export_excel_btn.setCursor(Qt.PointingHandCursor)
        export_excel_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Colors.SUCCESS};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 18px;
            }}
            QPushButton:hover {{ background: {Colors.SUCCESS}dd; }}
        """)
        export_excel_btn.clicked.connect(self._export_excel)
        actions_layout.addWidget(export_excel_btn)
        
        export_pdf_btn = QPushButton("📄 PDF")
        export_pdf_btn.setCursor(Qt.PointingHandCursor)
        export_pdf_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Colors.DANGER};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 18px;
            }}
            QPushButton:hover {{ background: {Colors.DANGER}dd; }}
        """)
        export_pdf_btn.clicked.connect(self._export_pdf)
        actions_layout.addWidget(export_pdf_btn)
        
        header_layout.addLayout(actions_layout)
        layout.addWidget(header_card)

        # Filters
        filters_card = QFrame()
        filters_card.setObjectName("filters_card")
        filters_card.setStyleSheet(f"""
            QFrame#filters_card {{
                background: {Colors.LIGHT_CARD};
                border: 1px solid {Colors.LIGHT_BORDER};
                border-radius: 12px;
            }}
        """)
        filters_layout = QHBoxLayout(filters_card)
        filters_layout.setContentsMargins(20, 16, 20, 16)
        filters_layout.setSpacing(16)
        
        date_icon = QLabel("📅")
        date_icon.setFont(QFont(Fonts.FAMILY_AR, 16))
        date_icon.setStyleSheet("background: transparent;")
        filters_layout.addWidget(date_icon)
        
        from_label = QLabel("من:")
        from_label.setFont(QFont(Fonts.FAMILY_AR, 12, QFont.Medium))
        from_label.setStyleSheet(f"color: {Colors.LIGHT_TEXT_SECONDARY}; background: transparent;")
        filters_layout.addWidget(from_label)
        
        self.from_date = QDateEdit()
        self.from_date.setCalendarPopup(True)
        self.from_date.setDate(QDate.currentDate().addMonths(-3))
        self.from_date.setMinimumWidth(140)
        filters_layout.addWidget(self.from_date)
        
        to_label = QLabel("إلى:")
        to_label.setFont(QFont(Fonts.FAMILY_AR, 12, QFont.Medium))
        to_label.setStyleSheet(f"color: {Colors.LIGHT_TEXT_SECONDARY}; background: transparent;")
        filters_layout.addWidget(to_label)
        
        self.to_date = QDateEdit()
        self.to_date.setCalendarPopup(True)
        self.to_date.setDate(QDate.currentDate())
        self.to_date.setMinimumWidth(140)
        filters_layout.addWidget(self.to_date)
        
        apply_btn = QPushButton("🔍 عرض التقرير")
        apply_btn.setCursor(Qt.PointingHandCursor)
        apply_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Colors.SECONDARY};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 24px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background: {Colors.SECONDARY_DARK}; }}
        """)
        apply_btn.clicked.connect(self.refresh)
        filters_layout.addWidget(apply_btn)
        filters_layout.addStretch()
        
        layout.addWidget(filters_card)

        # Metrics
        layout.addWidget(SectionHeader("📊 ملخص الموردين", ""))
        
        metrics_grid = QGridLayout()
        metrics_grid.setSpacing(16)
        
        self.total_suppliers_card = SupplierMetricCard(
            "إجمالي الموردين", "0", "🏭", Colors.SECONDARY, "Total Suppliers"
        )
        metrics_grid.addWidget(self.total_suppliers_card, 0, 0)
        
        self.active_suppliers_card = SupplierMetricCard(
            "الموردين النشطين", "0", "✅", Colors.SUCCESS, "Active Suppliers"
        )
        metrics_grid.addWidget(self.active_suppliers_card, 0, 1)
        
        self.total_purchases_card = SupplierMetricCard(
            "إجمالي المشتريات", config.format_usd(0), "📦", Colors.INFO, "Total Purchases"
        )
        metrics_grid.addWidget(self.total_purchases_card, 0, 2)
        
        self.total_payables_card = SupplierMetricCard(
            "إجمالي المستحقات", config.format_usd(0), "💰", Colors.WARNING, "Total Payables"
        )
        metrics_grid.addWidget(self.total_payables_card, 0, 3)
        
        layout.addLayout(metrics_grid)

        # Suppliers Table
        layout.addWidget(SectionHeader("🏆 أفضل الموردين", ""))
        
        suppliers_card = QFrame()
        suppliers_card.setObjectName("suppliers_card")
        suppliers_card.setStyleSheet(f"""
            QFrame#suppliers_card {{
                background: {Colors.LIGHT_CARD};
                border: 1px solid {Colors.LIGHT_BORDER};
                border-radius: 12px;
            }}
        """)
        suppliers_layout = QVBoxLayout(suppliers_card)
        suppliers_layout.setContentsMargins(20, 16, 20, 16)
        suppliers_layout.setSpacing(12)
        
        note = QLabel("💡 أفضل الموردين حسب إجمالي المشتريات خلال الفترة المحددة")
        note.setFont(QFont(Fonts.FAMILY_AR, 10))
        note.setStyleSheet(f"""
            color: {Colors.LIGHT_TEXT_SECONDARY};
            background: {Colors.SECONDARY}15;
            padding: 8px 12px;
            border-radius: 6px;
            border-left: 3px solid {Colors.SECONDARY};
        """)
        suppliers_layout.addWidget(note)
        
        self.suppliers_table = QTableWidget()
        self.suppliers_table.setColumnCount(7)
        self.suppliers_table.setHorizontalHeaderLabels([
            'الترتيب', 'الكود', 'اسم المورد', 'عدد الطلبات',
            'إجمالي المشتريات', 'الرصيد المستحق', 'الحالة'
        ])
        self.suppliers_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.suppliers_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.suppliers_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        for i in range(3, 7):
            self.suppliers_table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)
        self.suppliers_table.verticalHeader().setVisible(False)
        self.suppliers_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.suppliers_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.suppliers_table.setAlternatingRowColors(True)
        self.suppliers_table.setMinimumHeight(400)
        self._style_table(self.suppliers_table)
        suppliers_layout.addWidget(self.suppliers_table)
        
        layout.addWidget(suppliers_card, 1)
        layout.addStretch()
        
        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    def _style_table(self, table: QTableWidget):
        table.setStyleSheet(f"""
            QTableWidget {{
                background: {Colors.LIGHT_CARD};
                border: 1px solid {Colors.LIGHT_BORDER};
                border-radius: 8px;
                gridline-color: {Colors.LIGHT_BORDER};
            }}
            QTableWidget::item {{
                padding: 10px 12px;
                border-bottom: 1px solid {Colors.LIGHT_BORDER}50;
            }}
            QTableWidget::item:selected {{
                background: {Colors.SECONDARY}15;
                color: {Colors.SECONDARY};
            }}
            QHeaderView::section {{
                background: {Colors.LIGHT_BG};
                color: {Colors.LIGHT_TEXT};
                padding: 12px;
                border: none;
                border-bottom: 2px solid {Colors.SECONDARY};
                font-weight: bold;
                font-size: 12px;
            }}
        """)

    @handle_ui_error
    def refresh(self):
        start_date = self.from_date.date().toString('yyyy-MM-dd')
        end_date = self.to_date.date().toString('yyyy-MM-dd')
        self.report_data = api.get_suppliers_report(start_date, end_date) or {}
        self._update_ui()

    def _update_ui(self):
        data = self.report_data or {}
        summary = data.get('summary', {})

        total_suppliers = int(summary.get('total_suppliers', 0) or 0)
        active_suppliers = int(summary.get('active_suppliers', 0) or 0)
        total_purchases = float(summary.get('total_purchases_usd', summary.get('total_purchases', 0)) or 0)
        total_payables = float(summary.get('total_payables_usd', summary.get('total_payables', 0)) or 0)

        self.total_suppliers_card.update_value(f"{total_suppliers:,}")
        self.active_suppliers_card.update_value(f"{active_suppliers:,}")
        self.total_purchases_card.update_value(config.format_usd(total_purchases))
        self.total_payables_card.update_value(config.format_usd(total_payables))

        self._update_suppliers_table(data)

    def _update_suppliers_table(self, data: Dict):
        suppliers = data.get('top_suppliers', [])
        self.suppliers_list = suppliers
        self.suppliers_table.setRowCount(len(suppliers))
        
        max_total = max([float(s.get('purchases_total_usd', s.get('purchases_total', 0)) or 0) 
                        for s in suppliers], default=1)
        
        for r, sup in enumerate(suppliers):
            code = sup.get('code', '') or '-'
            name = sup.get('name', '') or 'غير محدد'
            orders_count = int(sup.get('orders_count', 0) or 0)
            purchases_total = float(sup.get('purchases_total_usd', sup.get('purchases_total', 0)) or 0)
            balance = float(sup.get('balance_usd', sup.get('balance', 0)) or 0)
            
            rank = r + 1
            if rank == 1:
                rank_text = "🥇 1"
            elif rank == 2:
                rank_text = "🥈 2"
            elif rank == 3:
                rank_text = "🥉 3"
            else:
                rank_text = f"   {rank}"
            
            rank_item = QTableWidgetItem(rank_text)
            rank_item.setTextAlignment(Qt.AlignCenter)
            rank_item.setFont(QFont(Fonts.FAMILY_AR, 12, QFont.Bold))
            self.suppliers_table.setItem(r, 0, rank_item)
            
            code_item = QTableWidgetItem(str(code))
            code_item.setTextAlignment(Qt.AlignCenter)
            code_item.setForeground(QBrush(QColor(Colors.LIGHT_TEXT_SECONDARY)))
            self.suppliers_table.setItem(r, 1, code_item)
            
            name_item = QTableWidgetItem(str(name))
            name_item.setFont(QFont(Fonts.FAMILY_AR, 11, QFont.Medium))
            self.suppliers_table.setItem(r, 2, name_item)
            
            count_item = QTableWidgetItem(f"{orders_count:,}")
            count_item.setTextAlignment(Qt.AlignCenter)
            count_item.setForeground(QBrush(QColor(Colors.INFO)))
            self.suppliers_table.setItem(r, 3, count_item)
            
            total_item = QTableWidgetItem(config.format_usd(purchases_total))
            total_item.setTextAlignment(Qt.AlignCenter)
            total_item.setFont(QFont(Fonts.FAMILY_AR, 11, QFont.Bold))
            total_item.setForeground(QBrush(QColor(Colors.SUCCESS)))
            self.suppliers_table.setItem(r, 4, total_item)
            
            balance_item = QTableWidgetItem(config.format_usd(balance))
            balance_item.setTextAlignment(Qt.AlignCenter)
            balance_item.setFont(QFont(Fonts.FAMILY_AR, 11, QFont.Bold))
            if balance > 0:
                balance_item.setForeground(QBrush(QColor(Colors.DANGER)))
            else:
                balance_item.setForeground(QBrush(QColor(Colors.SUCCESS)))
            self.suppliers_table.setItem(r, 5, balance_item)
            
            pct = (purchases_total / max_total * 100) if max_total > 0 else 0
            if pct >= 30:
                status = "⭐ رئيسي"
            elif pct >= 15:
                status = "🔵 مميز"
            elif orders_count > 0:
                status = "🟢 نشط"
            else:
                status = "⚪ غير نشط"
            status_item = QTableWidgetItem(status)
            status_item.setTextAlignment(Qt.AlignCenter)
            self.suppliers_table.setItem(r, 6, status_item)

    def _export_excel(self):
        if not self.suppliers_list:
            MessageDialog.warning(self, "تنبيه", "لا توجد بيانات للتصدير")
            return
        try:
            start_date = self.from_date.date().toString('yyyy-MM-dd')
            end_date = self.to_date.date().toString('yyyy-MM-dd')
            summary = self.report_data.get('summary', {})
            
            summary_data = {
                'الفترة': f"{start_date} → {end_date}",
                'إجمالي الموردين': summary.get('total_suppliers', 0),
                'الموردين النشطين': summary.get('active_suppliers', 0),
                'إجمالي المشتريات': config.format_usd(float(summary.get('total_purchases_usd', 0) or 0)),
                'إجمالي المستحقات': config.format_usd(float(summary.get('total_payables_usd', 0) or 0)),
            }
            
            rows = [{'rank': i+1, 'code': s.get('code',''), 'name': s.get('name',''),
                    'orders_count': s.get('orders_count',0),
                    'purchases_total': float(s.get('purchases_total_usd', s.get('purchases_total',0)) or 0),
                    'balance': float(s.get('balance_usd', s.get('balance',0)) or 0)}
                   for i, s in enumerate(self.suppliers_list)]
            
            columns = [('rank','الترتيب'),('code','الكود'),('name','اسم المورد'),
                      ('orders_count','عدد الطلبات'),('purchases_total','إجمالي المشتريات'),('balance','الرصيد')]
            
            filename = f"تقرير_الموردين_{datetime.now().strftime('%Y%m%d')}.xlsx"
            if ExportService.export_to_excel(data=rows, columns=columns, filename=filename,
                                            title="تقرير الموردين", parent=self, summary=summary_data):
                MessageDialog.info(self, "نجاح", "تم التصدير بنجاح ✅")
        except ExportError as e:
            MessageDialog.error(self, "خطأ", e.message)
        except Exception as e:
            MessageDialog.error(self, "خطأ", f"فشل التصدير: {str(e)}")

    def _export_pdf(self):
        if not self.suppliers_list:
            MessageDialog.warning(self, "تنبيه", "لا توجد بيانات للتصدير")
            return
        try:
            start_date = self.from_date.date().toString('yyyy-MM-dd')
            end_date = self.to_date.date().toString('yyyy-MM-dd')
            summary = self.report_data.get('summary', {})
            
            summary_data = {
                'الفترة': f"{start_date} → {end_date}",
                'إجمالي الموردين': summary.get('total_suppliers', 0),
                'الموردين النشطين': summary.get('active_suppliers', 0),
                'إجمالي المشتريات': config.format_usd(float(summary.get('total_purchases_usd', 0) or 0)),
                'إجمالي المستحقات': config.format_usd(float(summary.get('total_payables_usd', 0) or 0)),
            }
            
            rows = [{'rank': i+1, 'code': s.get('code',''), 'name': s.get('name',''),
                    'orders_count': s.get('orders_count',0),
                    'purchases_total': float(s.get('purchases_total_usd', s.get('purchases_total',0)) or 0),
                    'balance': float(s.get('balance_usd', s.get('balance',0)) or 0)}
                   for i, s in enumerate(self.suppliers_list)]
            
            columns = [('rank','الترتيب'),('code','الكود'),('name','اسم المورد'),
                      ('orders_count','عدد الطلبات'),('purchases_total','إجمالي المشتريات'),('balance','الرصيد')]
            
            filename = f"تقرير_الموردين_{datetime.now().strftime('%Y%m%d')}.pdf"
            if ExportService.export_to_pdf(data=rows, columns=columns, filename=filename,
                                          title="تقرير الموردين", parent=self, summary=summary_data,
                                          date_range=(start_date, end_date)):
                MessageDialog.info(self, "نجاح", "تم التصدير بنجاح ✅")
        except ExportError as e:
            MessageDialog.error(self, "خطأ", e.message)
        except Exception as e:
            MessageDialog.error(self, "خطأ", f"فشل التصدير: {str(e)}")
