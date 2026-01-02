"""
Data Table Widget

Enhanced data table with search, pagination, sorting, and CRUD actions.

Requirements: 14.1, 14.2, 14.3, 14.4, 14.5 - Data Tables Enhancement
Requirements: 1.3, 1.4, 2.3, 2.4, 3.3, 3.4 - Edit and delete actions
"""
from PySide6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QFrame, QMenu, QToolTip, QComboBox, QSpinBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QAction, QBrush, QColor

from ..config import Colors, Fonts, config


class DataTable(QFrame):
    """
    Enhanced data table with search, pagination, sorting, and actions.
    
    Signals:
        row_selected(row, data): Emitted when a row is selected
        row_double_clicked(row, data): Emitted on double-click
        action_clicked(action, row, data): Emitted when any action button clicked
        edit_clicked(row, data): Emitted when edit action triggered
        delete_clicked(row, data): Emitted when delete action triggered
        view_clicked(row, data): Emitted when view action triggered
        page_changed(page, page_size): Emitted when page changes
        sort_changed(column_key, order): Emitted when sort changes ('asc' or 'desc')
    
    Requirements: 14.1, 14.4 - Pagination support
    Requirements: 14.2 - Column sorting
    Requirements: 1.3, 1.4, 2.3, 2.4, 3.3, 3.4 - Edit and delete actions
    """
    
    row_selected = Signal(int, dict)
    row_double_clicked = Signal(int, dict)
    action_clicked = Signal(str, int, dict)
    edit_clicked = Signal(int, dict)
    delete_clicked = Signal(int, dict)
    view_clicked = Signal(int, dict)
    page_changed = Signal(int, int)  # (page, page_size)
    sort_changed = Signal(str, str)  # (column_key, order: 'asc' or 'desc')
    
    def __init__(self, columns: list, actions: list = None, parent=None):
        """
        Initialize DataTable.
        
        Args:
            columns: List of column definitions with keys:
                - key: Data key for the column
                - label: Display label
                - type: Optional type ('text', 'currency', 'date', 'stock')
                - sortable: Optional bool, default True
            actions: List of enabled actions ['view', 'edit', 'delete']
                    If None, defaults to ['edit', 'delete']
            parent: Parent widget
        """
        super().__init__(parent)
        self.columns = columns
        self.actions = actions if actions is not None else ['edit', 'delete']
        self.data = []
        self.current_page = 1
        self.page_size = 20
        self.total_items = 0
        self.sort_column = None
        self.sort_order = None  # 'asc' or 'desc'
        self._page_sizes = [10, 20, 50, 100]
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
        self.add_btn.clicked.connect(self.on_add_clicked)
        toolbar.addWidget(self.add_btn)
        
        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.setProperty("class", "icon-btn")
        self.refresh_btn.setFixedSize(40, 40)
        toolbar.addWidget(self.refresh_btn)
        
        layout.addLayout(toolbar)
        
        # Table
        self.table = QTableWidget()
        
        # Determine if we need actions column
        has_actions = len(self.actions) > 0
        col_count = len(self.columns) + (1 if has_actions else 0)
        self.table.setColumnCount(col_count)
        
        # Set headers
        headers = [col['label'] for col in self.columns]
        if has_actions:
            headers.append('إجراءات')
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
        
        # Header style and sorting
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setDefaultAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        # Enable sorting on header click
        # Requirements: 14.2 - Column sorting by clicking column headers
        header.sectionClicked.connect(self.on_header_clicked)
        header.setSortIndicatorShown(True)
        
        # Connect signals
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        self.table.itemDoubleClicked.connect(self.on_double_click)
        
        layout.addWidget(self.table)
        
        # Pagination
        # Requirements: 14.1, 14.4 - Pagination with configurable page size
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
        
        # Page size selector
        # Requirements: 14.4 - Configurable page size
        page_size_label = QLabel("عدد السجلات:")
        page_size_label.setProperty("class", "subtitle")
        pagination.addWidget(page_size_label)
        
        self.page_size_combo = QComboBox()
        self.page_size_combo.setFixedWidth(80)
        for size in self._page_sizes:
            self.page_size_combo.addItem(str(size), size)
        # Set default to 20
        default_idx = self._page_sizes.index(20) if 20 in self._page_sizes else 0
        self.page_size_combo.setCurrentIndex(default_idx)
        self.page_size_combo.currentIndexChanged.connect(self.on_page_size_changed)
        pagination.addWidget(self.page_size_combo)
        
        pagination.addSpacing(16)
        
        self.total_label = QLabel("إجمالي: 0 سجل")
        self.total_label.setProperty("class", "subtitle")
        pagination.addWidget(self.total_label)
        
        layout.addLayout(pagination)

    def on_add_clicked(self):
        """Handle add button click."""
        self.action_clicked.emit('add', -1, {})
        
    def set_data(self, data: list, total: int = None):
        """
        Set table data.
        
        Args:
            data: List of row data dictionaries
            total: Total count for pagination (if different from len(data))
        """
        self.data = data
        self.total_items = total if total is not None else len(data)
        self.refresh_table()
    
    def set_page(self, page: int, page_size: int = None):
        """
        Set current page and optionally page size.
        
        Args:
            page: Page number (1-based)
            page_size: Optional page size
        """
        self.current_page = page
        if page_size is not None:
            self.page_size = page_size
            # Update combo box without triggering signal
            idx = self._page_sizes.index(page_size) if page_size in self._page_sizes else -1
            if idx >= 0:
                self.page_size_combo.blockSignals(True)
                self.page_size_combo.setCurrentIndex(idx)
                self.page_size_combo.blockSignals(False)
        self._update_pagination_ui()
        
    def refresh_table(self):
        """Refresh table display."""
        self.table.setRowCount(len(self.data))
        
        for row, item in enumerate(self.data):
            for col, column in enumerate(self.columns):
                key = column['key']
                value = item.get(key, '')
                
                # Format value
                if column.get('type') == 'currency':
                    try:
                        if isinstance(key, str) and key.endswith('_usd'):
                            value = config.format_usd(float(value or 0))
                        else:
                            value = f"{float(value):,.2f}"
                    except (ValueError, TypeError):
                        value = str(value)
                elif column.get('type') == 'date':
                    pass  # Format date if needed
                elif column.get('type') == 'stock':
                    value = self._format_stock_value(item, value)
                    
                cell = QTableWidgetItem(str(value))
                cell.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                
                # Store tooltip data for stock columns
                if column.get('type') == 'stock':
                    tooltip = self._build_stock_tooltip(item)
                    if tooltip:
                        cell.setToolTip(tooltip)
                    
                    # Highlight low stock items with red background
                    if item.get('is_low_stock', False):
                        cell.setBackground(QBrush(QColor(255, 200, 200)))
                        cell.setForeground(QBrush(QColor(180, 0, 0)))
                
                self.table.setItem(row, col, cell)
            
            # Actions column
            if len(self.actions) > 0:
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(4, 4, 4, 4)
                actions_layout.setSpacing(4)
                
                # Requirements: 1.3, 1.4, 2.3, 2.4, 3.3, 3.4 - Edit and delete actions
                if 'view' in self.actions:
                    view_btn = QPushButton("👁️")
                    view_btn.setFixedSize(30, 30)
                    view_btn.setStyleSheet("border: none; background: transparent;")
                    view_btn.setToolTip("عرض")
                    view_btn.clicked.connect(lambda _, r=row: self.on_action('view', r))
                    actions_layout.addWidget(view_btn)
                
                if 'edit' in self.actions:
                    edit_btn = QPushButton("✏️")
                    edit_btn.setFixedSize(30, 30)
                    edit_btn.setStyleSheet("border: none; background: transparent;")
                    edit_btn.setToolTip("تعديل")
                    edit_btn.clicked.connect(lambda _, r=row: self.on_action('edit', r))
                    actions_layout.addWidget(edit_btn)
                
                if 'delete' in self.actions:
                    delete_btn = QPushButton("🗑️")
                    delete_btn.setFixedSize(30, 30)
                    delete_btn.setStyleSheet("border: none; background: transparent;")
                    delete_btn.setToolTip("حذف")
                    delete_btn.clicked.connect(lambda _, r=row: self.on_action('delete', r))
                    actions_layout.addWidget(delete_btn)
                
                self.table.setCellWidget(row, len(self.columns), actions_widget)
        
        # Update pagination UI
        self._update_pagination_ui()
        
        # Update sort indicator if sorting is active
        self._update_sort_indicator()

    def _update_pagination_ui(self):
        """Update pagination controls."""
        # Requirements: 14.4 - Display row count and current page information
        total_pages = max(1, (self.total_items + self.page_size - 1) // self.page_size)
        self.page_label.setText(f"صفحة {self.current_page} من {total_pages}")
        self.total_label.setText(f"إجمالي: {self.total_items} سجل")
        
        self.prev_btn.setEnabled(self.current_page > 1)
        self.next_btn.setEnabled(self.current_page < total_pages)

    def _update_sort_indicator(self):
        """Update sort indicator on header."""
        header = self.table.horizontalHeader()
        if self.sort_column is not None:
            # Find column index
            col_idx = None
            for idx, col in enumerate(self.columns):
                if col['key'] == self.sort_column:
                    col_idx = idx
                    break
            
            if col_idx is not None:
                order = Qt.AscendingOrder if self.sort_order == 'asc' else Qt.DescendingOrder
                header.setSortIndicator(col_idx, order)
        else:
            # Clear sort indicator
            header.setSortIndicator(-1, Qt.AscendingOrder)

    def _format_stock_value(self, item: dict, value) -> str:
        """Format stock value with base unit info."""
        base_unit_info = item.get('base_unit_info')
        if base_unit_info:
            unit_symbol = base_unit_info.get('unit_symbol', '')
            try:
                return f"{float(value):,.2f} {unit_symbol}"
            except (ValueError, TypeError):
                return str(value)
        try:
            return f"{float(value):,.2f}"
        except (ValueError, TypeError):
            return str(value)

    def _build_stock_tooltip(self, item: dict) -> str:
        """Build tooltip showing stock conversions to other units."""
        stock_conversions = item.get('stock_conversions', [])
        base_unit_info = item.get('base_unit_info')
        total_stock = item.get('total_stock', 0)
        is_low_stock = item.get('is_low_stock', False)
        minimum_stock = item.get('minimum_stock', 0)
        
        lines = []
        
        # Low stock warning
        if is_low_stock:
            lines.append("⚠️ تحذير: المخزون منخفض!")
            try:
                lines.append(f"الحد الأدنى: {float(minimum_stock):,.2f}")
            except (ValueError, TypeError):
                pass
            lines.append("")
        
        # Header with base unit
        if base_unit_info:
            base_name = base_unit_info.get('unit_name', '')
            try:
                lines.append(f"المخزون بالوحدة الأساسية ({base_name}): {float(total_stock):,.2f}")
            except (ValueError, TypeError):
                pass
        
        # Add conversions if available
        if stock_conversions:
            lines.append("")
            lines.append("المعادل بالوحدات الأخرى:")
            for conv in stock_conversions:
                unit_name = conv.get('unit_name', '')
                unit_symbol = conv.get('unit_symbol', '')
                quantity = conv.get('quantity', '0')
                conversion_factor = conv.get('conversion_factor', '1')
                try:
                    lines.append(f"  • {unit_name} ({unit_symbol}): {float(quantity):,.2f}")
                    lines.append(f"    (معامل التحويل: {conversion_factor})")
                except (ValueError, TypeError):
                    pass
        
        return "\n".join(lines) if lines else ""

    def on_cell_entered(self, row: int, col: int):
        """Handle cell hover for tooltip display."""
        item = self.table.item(row, col)
        if item and item.toolTip():
            pass
        
    def on_search(self, text: str):
        """
        Filter table by search text.
        
        Requirements: 14.3 - Search box that filters across visible columns
        """
        search_lower = text.lower().strip()
        for row in range(self.table.rowCount()):
            row_visible = False
            if not search_lower:
                row_visible = True
            else:
                for col in range(len(self.columns)):  # Exclude actions column
                    item = self.table.item(row, col)
                    if item and search_lower in item.text().lower():
                        row_visible = True
                        break
            self.table.setRowHidden(row, not row_visible)
    
    def on_header_clicked(self, logical_index: int):
        """
        Handle header click for sorting.
        
        Requirements: 14.2 - Column sorting by clicking column headers
        """
        # Don't sort actions column
        if logical_index >= len(self.columns):
            return
        
        column = self.columns[logical_index]
        
        # Check if column is sortable (default True)
        if not column.get('sortable', True):
            return
        
        column_key = column['key']
        
        # Toggle sort order
        if self.sort_column == column_key:
            # Toggle between asc -> desc -> none
            if self.sort_order == 'asc':
                self.sort_order = 'desc'
            elif self.sort_order == 'desc':
                self.sort_column = None
                self.sort_order = None
            else:
                self.sort_order = 'asc'
        else:
            # New column, start with ascending
            self.sort_column = column_key
            self.sort_order = 'asc'
        
        # Update sort indicator
        self._update_sort_indicator()
        
        # Emit signal for parent to handle server-side sorting
        if self.sort_column and self.sort_order:
            self.sort_changed.emit(self.sort_column, self.sort_order)
        else:
            # Emit empty to indicate no sorting
            self.sort_changed.emit('', '')
                
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
        """
        Handle action button click.
        
        Requirements: 1.3, 1.4, 2.3, 2.4, 3.3, 3.4 - Edit and delete actions
        """
        if row < len(self.data):
            data = self.data[row]
            # Emit generic action signal
            self.action_clicked.emit(action, row, data)
            
            # Also emit specific signals for edit/delete/view
            if action == 'edit':
                self.edit_clicked.emit(row, data)
            elif action == 'delete':
                self.delete_clicked.emit(row, data)
            elif action == 'view':
                self.view_clicked.emit(row, data)
            
    def prev_page(self):
        """
        Go to previous page.
        
        Requirements: 14.1 - Pagination navigation
        """
        if self.current_page > 1:
            self.current_page -= 1
            self._update_pagination_ui()
            self.page_changed.emit(self.current_page, self.page_size)
            
    def next_page(self):
        """
        Go to next page.
        
        Requirements: 14.1 - Pagination navigation
        """
        total_pages = (self.total_items + self.page_size - 1) // self.page_size
        if self.current_page < total_pages:
            self.current_page += 1
            self._update_pagination_ui()
            self.page_changed.emit(self.current_page, self.page_size)
    
    def on_page_size_changed(self, index: int):
        """
        Handle page size change.
        
        Requirements: 14.4 - Configurable page size
        """
        new_size = self.page_size_combo.currentData()
        if new_size and new_size != self.page_size:
            self.page_size = new_size
            # Reset to page 1 when page size changes
            self.current_page = 1
            self._update_pagination_ui()
            self.page_changed.emit(self.current_page, self.page_size)
            
    def get_selected_row(self):
        """Get currently selected row data."""
        rows = self.table.selectionModel().selectedRows()
        if rows:
            row = rows[0].row()
            if row < len(self.data):
                return self.data[row]
        return None
    
    def get_sort_params(self) -> dict:
        """
        Get current sort parameters for API calls.
        
        Returns:
            dict with 'ordering' key if sorting is active, empty dict otherwise
        """
        if self.sort_column and self.sort_order:
            prefix = '-' if self.sort_order == 'desc' else ''
            return {'ordering': f'{prefix}{self.sort_column}'}
        return {}
    
    def get_pagination_params(self) -> dict:
        """
        Get current pagination parameters for API calls.
        
        Returns:
            dict with 'page' and 'page_size' keys
        """
        return {
            'page': self.current_page,
            'page_size': self.page_size
        }
    
    def set_sort(self, column_key: str, order: str):
        """
        Set sort column and order programmatically.
        
        Args:
            column_key: Column key to sort by
            order: 'asc' or 'desc'
        """
        self.sort_column = column_key if column_key else None
        self.sort_order = order if order in ('asc', 'desc') else None
        self._update_sort_indicator()
    
    def clear_sort(self):
        """Clear current sorting."""
        self.sort_column = None
        self.sort_order = None
        self._update_sort_indicator()
