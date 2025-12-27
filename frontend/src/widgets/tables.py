"""
Data Table Widget
"""
from PySide6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QFrame, QMenu, QToolTip
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QAction

from ..config import Colors, Fonts


class DataTable(QFrame):
    """
    Enhanced data table with search, pagination, and actions.
    """
    
    row_selected = Signal(int, dict)
    row_double_clicked = Signal(int, dict)
    action_clicked = Signal(str, int, dict)
    
    def __init__(self, columns: list, parent=None):
        super().__init__(parent)
        self.columns = columns
        self.data = []
        self.current_page = 1
        self.page_size = 20
        self.total_items = 0
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize table UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 بحث في الجدول...")
        self.search_input.setFixedWidth(250)
        self.search_input.textChanged.connect(self.on_search)
        toolbar.addWidget(self.search_input)
        
        toolbar.addStretch()
        
        # Actions
        self.add_btn = QPushButton("➕ إضافة جديد")
        self.add_btn.clicked.connect(self.on_add_clicked)  # Assuming method exists or will be connected
        toolbar.addWidget(self.add_btn)
        
        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.setProperty("class", "icon-btn")
        self.refresh_btn.setFixedSize(40, 40)
        toolbar.addWidget(self.refresh_btn)
        
        layout.addLayout(toolbar)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.columns) + 1)
        
        # Set headers
        headers = [col['label'] for col in self.columns] + ['إجراءات']
        self.table.setHorizontalHeaderLabels(headers)
        
        # Config table
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        
        # Enable mouse tracking for tooltips
        self.table.setMouseTracking(True)
        self.table.cellEntered.connect(self.on_cell_entered)
        
        # Header style
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setDefaultAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        # Connect signals
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        self.table.itemDoubleClicked.connect(self.on_double_click)
        
        layout.addWidget(self.table)
        
        # Pagination
        pagination = QHBoxLayout()
        
        self.prev_btn = QPushButton("السابق")
        self.prev_btn.setProperty("class", "secondary")
        self.prev_btn.setMinimumHeight(40)
        self.prev_btn.clicked.connect(self.prev_page)
        pagination.addWidget(self.prev_btn)
        
        self.page_label = QLabel("صفحة 1 من 1")
        self.page_label.setProperty("class", "subtitle")
        self.page_label.setStyleSheet("padding: 0 16px; font-weight: 600;")
        pagination.addWidget(self.page_label)
        
        self.next_btn = QPushButton("التالي")
        self.next_btn.setProperty("class", "secondary")
        self.next_btn.setMinimumHeight(40)
        self.next_btn.clicked.connect(self.next_page)
        pagination.addWidget(self.next_btn)
        
        pagination.addStretch()
        
        self.total_label = QLabel("إجمالي: 0 سجل")
        self.total_label.setProperty("class", "subtitle")
        pagination.addWidget(self.total_label)
        
        layout.addLayout(pagination)

    def on_add_clicked(self):
        """Handle add button click."""
        # Emit action signal for parent view to handle
        self.action_clicked.emit('add', -1, {})
        
    def set_data(self, data: list, total: int = None):
        """Set table data."""
        self.data = data
        self.total_items = total or len(data)
        self.refresh_table()
        
    def refresh_table(self):
        """Refresh table display."""
        self.table.setRowCount(len(self.data))
        
        for row, item in enumerate(self.data):
            for col, column in enumerate(self.columns):
                key = column['key']
                value = item.get(key, '')
                
                # Format value
                if column.get('type') == 'currency':
                    value = f"{float(value):,.2f}"
                elif column.get('type') == 'date':
                    pass  # Format date if needed
                elif column.get('type') == 'stock':
                    # Format stock with unit info
                    value = self._format_stock_value(item, value)
                    
                cell = QTableWidgetItem(str(value))
                cell.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                
                # Store tooltip data for stock columns
                if column.get('type') == 'stock':
                    tooltip = self._build_stock_tooltip(item)
                    if tooltip:
                        cell.setToolTip(tooltip)
                    
                    # Highlight low stock items with red background
                    # Requirements: 5.4 - Low stock alerts
                    if item.get('is_low_stock', False):
                        from PySide6.QtGui import QBrush, QColor
                        cell.setBackground(QBrush(QColor(255, 200, 200)))  # Light red
                        cell.setForeground(QBrush(QColor(180, 0, 0)))  # Dark red text
                
                self.table.setItem(row, col, cell)
            
            # Actions column
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 4, 4, 4)
            actions_layout.setSpacing(4)
            
            edit_btn = QPushButton("✏️")
            edit_btn.setFixedSize(30, 30)
            edit_btn.setStyleSheet("border: none; background: transparent;")
            edit_btn.clicked.connect(lambda _, r=row: self.on_action('edit', r))
            actions_layout.addWidget(edit_btn)
            
            delete_btn = QPushButton("🗑️")
            delete_btn.setFixedSize(30, 30)
            delete_btn.setStyleSheet("border: none; background: transparent;")
            delete_btn.clicked.connect(lambda _, r=row: self.on_action('delete', r))
            actions_layout.addWidget(delete_btn)
            
            self.table.setCellWidget(row, len(self.columns), actions_widget)
        
        # Update pagination
        total_pages = max(1, (self.total_items + self.page_size - 1) // self.page_size)
        self.page_label.setText(f"صفحة {self.current_page} من {total_pages}")
        self.total_label.setText(f"إجمالي: {self.total_items} سجل")
        
        self.prev_btn.setEnabled(self.current_page > 1)
        self.next_btn.setEnabled(self.current_page < total_pages)

    def _format_stock_value(self, item: dict, value) -> str:
        """
        Format stock value with base unit info.
        
        Requirements: 5.1, 5.2
        """
        base_unit_info = item.get('base_unit_info')
        if base_unit_info:
            unit_symbol = base_unit_info.get('unit_symbol', '')
            return f"{float(value):,.2f} {unit_symbol}"
        return f"{float(value):,.2f}"

    def _build_stock_tooltip(self, item: dict) -> str:
        """
        Build tooltip showing stock conversions to other units.
        
        Requirements: 5.3 - Show equivalent quantities in other units
        """
        stock_conversions = item.get('stock_conversions', [])
        base_unit_info = item.get('base_unit_info')
        total_stock = item.get('total_stock', 0)
        is_low_stock = item.get('is_low_stock', False)
        minimum_stock = item.get('minimum_stock', 0)
        
        lines = []
        
        # Low stock warning
        if is_low_stock:
            lines.append("⚠️ تحذير: المخزون منخفض!")
            lines.append(f"الحد الأدنى: {float(minimum_stock):,.2f}")
            lines.append("")
        
        # Header with base unit
        if base_unit_info:
            base_name = base_unit_info.get('unit_name', '')
            lines.append(f"المخزون بالوحدة الأساسية ({base_name}): {float(total_stock):,.2f}")
        
        # Add conversions if available
        if stock_conversions:
            lines.append("")
            lines.append("المعادل بالوحدات الأخرى:")
            for conv in stock_conversions:
                unit_name = conv.get('unit_name', '')
                unit_symbol = conv.get('unit_symbol', '')
                quantity = conv.get('quantity', '0')
                conversion_factor = conv.get('conversion_factor', '1')
                lines.append(f"  • {unit_name} ({unit_symbol}): {float(quantity):,.2f}")
                lines.append(f"    (معامل التحويل: {conversion_factor})")
        
        return "\n".join(lines) if lines else ""

    def on_cell_entered(self, row: int, col: int):
        """Handle cell hover for tooltip display."""
        item = self.table.item(row, col)
        if item and item.toolTip():
            # Tooltip is already set on the item
            pass
        
    def on_search(self, text: str):
        """Filter table by search text."""
        # Client-side filtering: show/hide rows based on search text
        search_lower = text.lower().strip()
        for row in range(self.table.rowCount()):
            row_visible = False
            if not search_lower:
                row_visible = True
            else:
                for col in range(self.table.columnCount() - 1):  # Exclude actions column
                    item = self.table.item(row, col)
                    if item and search_lower in item.text().lower():
                        row_visible = True
                        break
            self.table.setRowHidden(row, not row_visible)
        
    def on_selection_changed(self):
        """Handle row selection."""
        rows = self.table.selectionModel().selectedRows()
        if rows:
            row = rows[0].row()
            if row < len(self.data):
                self.row_selected.emit(row, self.data[row])
                
    def on_double_click(self, item):
        """Handle row double-click."""
        row = item.row()
        if row < len(self.data):
            self.row_double_clicked.emit(row, self.data[row])
            
    def on_action(self, action: str, row: int):
        """Handle action button click."""
        if row < len(self.data):
            self.action_clicked.emit(action, row, self.data[row])
            
    def prev_page(self):
        """Go to previous page."""
        if self.current_page > 1:
            self.current_page -= 1
            # Emit signal to load data
            
    def next_page(self):
        """Go to next page."""
        total_pages = (self.total_items + self.page_size - 1) // self.page_size
        if self.current_page < total_pages:
            self.current_page += 1
            # Emit signal to load data
            
    def get_selected_row(self):
        """Get currently selected row data."""
        rows = self.table.selectionModel().selectedRows()
        if rows:
            row = rows[0].row()
            if row < len(self.data):
                return self.data[row]
        return None
