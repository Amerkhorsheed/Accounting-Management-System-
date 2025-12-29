"""
Expenses Report View - تقرير المصروفات

This module provides the UI for viewing the expenses report showing
expense analysis by category, date range, and trends.

Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6
"""
from typing import List, Dict
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QDateEdit, QComboBox, QAbstractItemView, QProgressBar,
    QGridLayout, QFrame
)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QFont, QColor

from ...config import Colors, Fonts
from ...widgets.cards import Card, StatCard
from ...widgets.dialogs import MessageDialog
from ...services.api import api, ApiException
from ...services.export import ExportService, ExportError
from ...utils.error_handler import handle_ui_error


class ExpensesReportView(QWidget):
    """
    Expenses Report View showing expense analysis.
    
    Displays:
    - Summary cards (total expenses, expense count, average expense)
    - Category breakdown with percentages and visual bars
    - Expenses list table with all details
    - Date range and category filters
    
    Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6
    """
    
    back_requested = Signal()  # Emitted when back button is clicked
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.report_data: Dict = {}
        self.expenses_list: List[Dict] = []
        self.categories: List[Dict] = []
        self.setup_ui()
    
    def go_back(self):
        """Navigate back to main reports view."""
        self.back_requested.emit()

    def setup_ui(self):
        """Initialize the expenses report UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header with back button and title
        # Requirements: 2.1 - Display expenses report view
        header = QHBoxLayout()
        
        # Back button
        back_btn = QPushButton("→ رجوع")
        back_btn.setProperty("class", "secondary")
        back_btn.clicked.connect(self.go_back)
        header.addWidget(back_btn)
        
        title = QLabel("تقرير المصروفات")
        title.setProperty("class", "title")
        header.addWidget(title)
        header.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton("🔄 تحديث")
        refresh_btn.setProperty("class", "secondary")
        refresh_btn.clicked.connect(self.refresh)
        header.addWidget(refresh_btn)
        
        # Export buttons (placeholders for future implementation)
        export_excel_btn = QPushButton("📊 Excel")
        export_excel_btn.setProperty("class", "secondary")
        export_excel_btn.clicked.connect(self._export_excel)
        header.addWidget(export_excel_btn)
        
        export_pdf_btn = QPushButton("📄 PDF")
        export_pdf_btn.setProperty("class", "secondary")
        export_pdf_btn.clicked.connect(self._export_pdf)
        header.addWidget(export_pdf_btn)
        
        layout.addLayout(header)
        
        # Date range and category filter section
        # Requirements: 2.5, 2.6 - Support filtering by date range and category
        filters_frame = Card()
        filters_layout = QHBoxLayout(filters_frame)
        filters_layout.setContentsMargins(16, 12, 16, 12)
        filters_layout.setSpacing(16)
        
        # Date range filter
        filters_layout.addWidget(QLabel("من:"))
        self.from_date = QDateEdit()
        self.from_date.setCalendarPopup(True)
        self.from_date.setDate(QDate.currentDate().addMonths(-1))
        filters_layout.addWidget(self.from_date)
        
        filters_layout.addWidget(QLabel("إلى:"))
        self.to_date = QDateEdit()
        self.to_date.setCalendarPopup(True)
        self.to_date.setDate(QDate.currentDate())
        filters_layout.addWidget(self.to_date)
        
        # Category filter
        # Requirements: 2.6 - Support filtering by expense category
        filters_layout.addWidget(QLabel("الفئة:"))
        self.category_combo = QComboBox()
        self.category_combo.addItem("جميع الفئات", None)
        self.category_combo.setMinimumWidth(150)
        filters_layout.addWidget(self.category_combo)
        
        # Apply filter button
        apply_btn = QPushButton("تطبيق")
        apply_btn.clicked.connect(self._apply_filters)
        filters_layout.addWidget(apply_btn)
        
        filters_layout.addStretch()
        
        layout.addWidget(filters_frame)
        
        # Summary cards section
        # Requirements: 2.2 - Display total expenses amount
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)
        
        # Total expenses card
        self.total_expenses_card = StatCard(
            title="إجمالي المصروفات",
            value="0.00 ل.س",
            icon="💸",
            color=Colors.DANGER
        )
        cards_layout.addWidget(self.total_expenses_card)
        
        # Expense count card
        self.expense_count_card = StatCard(
            title="عدد المصروفات",
            value="0",
            icon="📋",
            color=Colors.INFO
        )
        cards_layout.addWidget(self.expense_count_card)
        
        # Average expense card
        self.average_expense_card = StatCard(
            title="متوسط المصروف",
            value="0.00 ل.س",
            icon="📊",
            color=Colors.WARNING
        )
        cards_layout.addWidget(self.average_expense_card)
        
        layout.addLayout(cards_layout)
        
        # Category breakdown section
        # Requirements: 2.3 - Show expenses breakdown by category with percentages
        self.category_card = Card()
        category_layout = QVBoxLayout(self.category_card)
        category_layout.setContentsMargins(16, 16, 16, 16)
        category_layout.setSpacing(12)
        
        category_header = QHBoxLayout()
        category_title = QLabel("توزيع المصروفات حسب الفئة")
        category_title.setProperty("class", "h2")
        category_header.addWidget(category_title)
        category_header.addStretch()
        category_layout.addLayout(category_header)
        
        # Container for category breakdown items
        self.category_breakdown_layout = QVBoxLayout()
        self.category_breakdown_layout.setSpacing(8)
        category_layout.addLayout(self.category_breakdown_layout)
        
        layout.addWidget(self.category_card)

        # Expenses table section
        # Requirements: 2.4 - List individual expenses with date, category, description, amount
        table_card = Card()
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(16, 16, 16, 16)
        table_layout.setSpacing(12)
        
        table_header = QHBoxLayout()
        table_title = QLabel("قائمة المصروفات")
        table_title.setProperty("class", "h2")
        table_header.addWidget(table_title)
        table_header.addStretch()
        table_layout.addLayout(table_header)
        
        # Expenses table
        # Requirements: 2.4 - Show date, category, description, amount
        self.expenses_table = QTableWidget()
        self.expenses_table.setColumnCount(5)
        self.expenses_table.setHorizontalHeaderLabels([
            'التاريخ',
            'الفئة',
            'الوصف',
            'المبلغ',
            'المرجع'
        ])
        self.expenses_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.expenses_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.expenses_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.expenses_table.verticalHeader().setVisible(False)
        self.expenses_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.expenses_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.expenses_table.setAlternatingRowColors(True)
        
        table_layout.addWidget(self.expenses_table)
        
        layout.addWidget(table_card, 1)
    
    def _load_categories(self):
        """Load expense categories for the filter dropdown."""
        try:
            self.categories = api.get_expense_categories()
            
            # Clear and repopulate category combo
            self.category_combo.clear()
            self.category_combo.addItem("جميع الفئات", None)
            
            for category in self.categories:
                self.category_combo.addItem(
                    category.get('name', ''),
                    category.get('id')
                )
        except Exception:
            # If categories fail to load, just keep the default "All" option
            pass
    
    @handle_ui_error
    def refresh(self):
        """Refresh the expenses report data from API."""
        self._load_categories()
        self._load_report()
    
    @handle_ui_error
    def _apply_filters(self):
        """Apply filters and reload the report."""
        self._load_report()
    
    def _load_report(self):
        """
        Load expenses report data from API.
        
        Requirements: 2.5, 2.6 - Support date range and category filtering
        """
        # Build filter parameters
        start_date = self.from_date.date().toString('yyyy-MM-dd')
        end_date = self.to_date.date().toString('yyyy-MM-dd')
        category_id = self.category_combo.currentData()
        
        # Fetch report data
        self.report_data = api.get_expenses_report(
            start_date=start_date,
            end_date=end_date,
            category_id=category_id
        )
        
        # Update summary cards
        self._update_summary_cards()
        
        # Update category breakdown
        self._update_category_breakdown()
        
        # Update expenses table
        self._update_expenses_table()
    
    def _update_summary_cards(self):
        """
        Update the summary cards with report data.
        
        Requirements: 2.2 - Display total expenses amount
        """
        summary = self.report_data.get('summary', {})
        total_expenses = float(summary.get('total_expenses', 0))
        expense_count = int(summary.get('expense_count', 0))
        average_expense = float(summary.get('average_expense', 0))
        
        self.total_expenses_card.update_value(f"{total_expenses:,.2f} ل.س")
        self.expense_count_card.update_value(str(expense_count))
        self.average_expense_card.update_value(f"{average_expense:,.2f} ل.س")

    def _update_category_breakdown(self):
        """
        Update the category breakdown section with visual representation.
        
        Requirements: 2.3 - Show expenses breakdown by category with amounts and percentages
        Requirements: 2.7 - Show visual representation of expense distribution
        """
        # Clear existing breakdown items
        while self.category_breakdown_layout.count():
            item = self.category_breakdown_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        by_category = self.report_data.get('by_category', [])
        
        if not by_category:
            no_data_label = QLabel("لا توجد بيانات للعرض")
            no_data_label.setAlignment(Qt.AlignCenter)
            no_data_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY}; padding: 20px;")
            self.category_breakdown_layout.addWidget(no_data_label)
            return
        
        # Define colors for categories
        category_colors = [
            Colors.PRIMARY,
            Colors.SUCCESS,
            Colors.WARNING,
            Colors.DANGER,
            Colors.INFO,
            Colors.SECONDARY,
            "#9C27B0",  # Purple
            "#00BCD4",  # Cyan
            "#FF9800",  # Orange
            "#795548",  # Brown
        ]
        
        for i, category in enumerate(by_category):
            category_name = category.get('category_name', 'غير مصنف')
            total = float(category.get('total', 0))
            percentage = float(category.get('percentage', 0))
            count = int(category.get('count', 0))
            color = category_colors[i % len(category_colors)]
            
            # Create category row widget
            row_widget = QFrame()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 4, 0, 4)
            row_layout.setSpacing(12)
            
            # Category name
            name_label = QLabel(category_name)
            name_label.setMinimumWidth(120)
            name_label.setStyleSheet(f"font-weight: bold;")
            row_layout.addWidget(name_label)
            
            # Progress bar for visual representation
            progress_bar = QProgressBar()
            progress_bar.setMinimum(0)
            progress_bar.setMaximum(100)
            progress_bar.setValue(int(percentage))
            progress_bar.setTextVisible(False)
            progress_bar.setMinimumHeight(20)
            progress_bar.setStyleSheet(f"""
                QProgressBar {{
                    border: none;
                    border-radius: 4px;
                    background-color: {Colors.BACKGROUND};
                }}
                QProgressBar::chunk {{
                    background-color: {color};
                    border-radius: 4px;
                }}
            """)
            row_layout.addWidget(progress_bar, 1)
            
            # Percentage label
            percentage_label = QLabel(f"{percentage:.1f}%")
            percentage_label.setMinimumWidth(50)
            percentage_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            row_layout.addWidget(percentage_label)
            
            # Amount label
            amount_label = QLabel(f"{total:,.2f} ل.س")
            amount_label.setMinimumWidth(100)
            amount_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            amount_label.setStyleSheet(f"color: {color}; font-weight: bold;")
            row_layout.addWidget(amount_label)
            
            # Count label
            count_label = QLabel(f"({count})")
            count_label.setMinimumWidth(40)
            count_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            count_label.setStyleSheet(f"color: {Colors.TEXT_SECONDARY};")
            row_layout.addWidget(count_label)
            
            self.category_breakdown_layout.addWidget(row_widget)
    
    def _update_expenses_table(self):
        """
        Update the expenses table with report data.
        
        Requirements: 2.4 - List individual expenses with date, category, description, amount
        """
        expenses = self.report_data.get('expenses', [])
        self.expenses_list = expenses
        
        self.expenses_table.setRowCount(len(expenses))
        
        for row, expense in enumerate(expenses):
            # Date
            date_str = expense.get('date', '')
            date_item = QTableWidgetItem(str(date_str))
            date_item.setData(Qt.UserRole, expense)
            date_item.setTextAlignment(Qt.AlignCenter)
            self.expenses_table.setItem(row, 0, date_item)
            
            # Category
            category_name = expense.get('category', 'غير مصنف')
            self.expenses_table.setItem(row, 1, QTableWidgetItem(str(category_name)))
            
            # Description
            description = expense.get('description', '')
            self.expenses_table.setItem(row, 2, QTableWidgetItem(str(description)))
            
            # Amount
            amount = float(expense.get('amount', 0))
            amount_item = QTableWidgetItem(f"{amount:,.2f}")
            amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            amount_item.setForeground(QColor(Colors.DANGER))
            self.expenses_table.setItem(row, 3, amount_item)
            
            # Reference
            reference = expense.get('reference', '')
            ref_item = QTableWidgetItem(str(reference) if reference else '-')
            ref_item.setTextAlignment(Qt.AlignCenter)
            self.expenses_table.setItem(row, 4, ref_item)
    
    def _export_excel(self):
        """
        Export report to Excel.
        
        Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6
        """
        if not self.expenses_list:
            MessageDialog.warning(self, "تنبيه", "لا توجد بيانات للتصدير")
            return
        
        try:
            # Define columns for export
            columns = [
                ('date', 'التاريخ'),
                ('category', 'الفئة'),
                ('description', 'الوصف'),
                ('amount', 'المبلغ'),
                ('reference', 'المرجع')
            ]
            
            # Prepare data
            export_data = []
            for expense in self.expenses_list:
                export_data.append({
                    'date': expense.get('date', ''),
                    'category': expense.get('category', 'غير مصنف'),
                    'description': expense.get('description', ''),
                    'amount': float(expense.get('amount', 0)),
                    'reference': expense.get('reference', '') or '-'
                })
            
            # Generate filename with date
            filename = f"تقرير_المصروفات_{datetime.now().strftime('%Y%m%d')}.xlsx"
            
            # Prepare summary data
            summary = self.report_data.get('summary', {})
            by_category = self.report_data.get('by_category', [])
            
            summary_data = {
                'إجمالي المصروفات': f"{float(summary.get('total_expenses', 0)):,.2f} ل.س",
                'عدد المصروفات': str(summary.get('expense_count', 0)),
                'متوسط المصروف': f"{float(summary.get('average_expense', 0)):,.2f} ل.س"
            }
            
            # Add category breakdown to summary
            for cat in by_category:
                cat_name = cat.get('category_name', 'غير مصنف')
                cat_total = float(cat.get('total', 0))
                cat_percent = float(cat.get('percentage', 0))
                summary_data[f'{cat_name}'] = f"{cat_total:,.2f} ل.س ({cat_percent:.1f}%)"
            
            # Export to Excel
            success = ExportService.export_to_excel(
                data=export_data,
                columns=columns,
                filename=filename,
                title="تقرير المصروفات",
                parent=self,
                summary=summary_data
            )
            
            if success:
                MessageDialog.info(self, "نجاح", "تم تصدير التقرير بنجاح")
                
        except ExportError as e:
            MessageDialog.error(self, "خطأ", e.message)
        except Exception as e:
            MessageDialog.error(self, "خطأ", f"فشل تصدير التقرير: {str(e)}")
    
    def _export_pdf(self):
        """
        Export report to PDF.
        
        Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7
        """
        if not self.expenses_list:
            MessageDialog.warning(self, "تنبيه", "لا توجد بيانات للتصدير")
            return
        
        try:
            # Define columns for export
            columns = [
                ('date', 'التاريخ'),
                ('category', 'الفئة'),
                ('description', 'الوصف'),
                ('amount', 'المبلغ'),
                ('reference', 'المرجع')
            ]
            
            # Prepare data
            export_data = []
            for expense in self.expenses_list:
                export_data.append({
                    'date': expense.get('date', ''),
                    'category': expense.get('category', 'غير مصنف'),
                    'description': expense.get('description', ''),
                    'amount': float(expense.get('amount', 0)),
                    'reference': expense.get('reference', '') or '-'
                })
            
            # Generate filename with date
            filename = f"تقرير_المصروفات_{datetime.now().strftime('%Y%m%d')}.pdf"
            
            # Prepare summary data
            summary = self.report_data.get('summary', {})
            by_category = self.report_data.get('by_category', [])
            
            summary_data = {
                'إجمالي المصروفات': f"{float(summary.get('total_expenses', 0)):,.2f} ل.س",
                'عدد المصروفات': str(summary.get('expense_count', 0)),
                'متوسط المصروف': f"{float(summary.get('average_expense', 0)):,.2f} ل.س"
            }
            
            # Add category breakdown to summary
            for cat in by_category:
                cat_name = cat.get('category_name', 'غير مصنف')
                cat_total = float(cat.get('total', 0))
                cat_percent = float(cat.get('percentage', 0))
                summary_data[f'{cat_name}'] = f"{cat_total:,.2f} ل.س ({cat_percent:.1f}%)"
            
            # Get date range
            start_date = self.from_date.date().toString('yyyy-MM-dd')
            end_date = self.to_date.date().toString('yyyy-MM-dd')
            
            # Export to PDF
            success = ExportService.export_to_pdf(
                data=export_data,
                columns=columns,
                filename=filename,
                title="تقرير المصروفات",
                parent=self,
                summary=summary_data,
                date_range=(start_date, end_date)
            )
            
            if success:
                MessageDialog.info(self, "نجاح", "تم تصدير التقرير بنجاح")
                
        except ExportError as e:
            MessageDialog.error(self, "خطأ", e.message)
        except Exception as e:
            MessageDialog.error(self, "خطأ", f"فشل تصدير التقرير: {str(e)}")
