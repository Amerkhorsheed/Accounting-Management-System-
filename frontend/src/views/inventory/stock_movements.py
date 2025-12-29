"""
Stock Movements View

Requirements: 6.1, 6.2, 6.3, 6.4 - Stock Movements View
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QDialog, QComboBox,
    QDateEdit, QFormLayout, QScrollArea
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont, QColor, QBrush

from ...config import Colors, Fonts
from ...widgets.tables import DataTable
from ...widgets.dialogs import MessageDialog
from ...services.api import api, ApiException
from ...utils.error_handler import handle_ui_error


class StockMovementDetailsDialog(QDialog):
    """
    Dialog for displaying stock movement details.
    
    Requirements: 6.3 - Display full movement details including source document reference
    """
    
    def __init__(self, movement: dict, parent=None):
        """
        Initialize the movement details dialog.
        
        Args:
            movement: Full movement data from API
        """
        super().__init__(parent)
        self.movement = movement
        
        self.setWindowTitle("تفاصيل حركة المخزون")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        self.setup_ui()
    
    def setup_ui(self):
        """Initialize dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header with movement type
        header_frame = QFrame()
        movement_type = self.movement.get('movement_type', '')
        type_colors = {
            'in': Colors.SUCCESS,
            'out': Colors.DANGER,
            'adjustment': Colors.WARNING,
            'transfer': Colors.INFO,
            'return': Colors.PRIMARY,
            'damage': Colors.DANGER,
        }
        header_color = type_colors.get(movement_type, Colors.LIGHT_TEXT)
        header_frame.setStyleSheet(f"""
            background-color: {header_color}15;
            border: 2px solid {header_color};
            border-radius: 8px;
            padding: 16px;
        """)
        header_layout = QVBoxLayout(header_frame)
        header_layout.setSpacing(8)
        
        # Movement type icon and display
        type_icons = {
            'in': '📥',
            'out': '📤',
            'adjustment': '⚖️',
            'transfer': '🔄',
            'return': '↩️',
            'damage': '💔',
        }
        type_icon = type_icons.get(movement_type, '📦')
        type_display = self.movement.get('movement_type_display', movement_type)
        
        type_label = QLabel(f"{type_icon} {type_display}")
        type_label.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_H2, QFont.Bold))
        type_label.setStyleSheet(f"color: {header_color};")
        type_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(type_label)
        
        # Quantity
        quantity = float(self.movement.get('quantity', 0))
        quantity_prefix = '+' if movement_type in ['in', 'return'] else '-' if movement_type in ['out', 'damage'] else ''
        quantity_label = QLabel(f"{quantity_prefix}{quantity:,.2f}")
        quantity_label.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_H1, QFont.Bold))
        quantity_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(quantity_label)
        
        layout.addWidget(header_frame)
        
        # Details section
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        details_widget = QWidget()
        details_layout = QFormLayout(details_widget)
        details_layout.setContentsMargins(0, 0, 0, 0)
        details_layout.setSpacing(12)
        details_layout.setLabelAlignment(Qt.AlignRight)
        
        # Product info
        product_name = self.movement.get('product_name', '')
        product_code = self.movement.get('product_code', '')
        product_label = QLabel(f"{product_name} ({product_code})")
        product_label.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_BODY, QFont.Bold))
        details_layout.addRow("المنتج:", product_label)
        
        # Warehouse
        warehouse_name = self.movement.get('warehouse_name', '')
        details_layout.addRow("المستودع:", QLabel(warehouse_name))
        
        # Source type
        source_display = self.movement.get('source_type_display', '')
        details_layout.addRow("مصدر الحركة:", QLabel(source_display))
        
        # Date
        created_at = self.movement.get('created_at', '')
        if created_at:
            # Format date if needed
            date_display = created_at[:10] if len(created_at) >= 10 else created_at
            time_display = created_at[11:19] if len(created_at) >= 19 else ''
            details_layout.addRow("التاريخ:", QLabel(f"{date_display} {time_display}"))
        
        # Balance before/after
        balance_before = float(self.movement.get('balance_before', 0))
        balance_after = float(self.movement.get('balance_after', 0))
        
        balance_frame = QFrame()
        balance_frame.setStyleSheet(f"background-color: {Colors.LIGHT_BG}; border-radius: 4px; padding: 8px;")
        balance_layout = QHBoxLayout(balance_frame)
        balance_layout.setSpacing(16)
        
        before_container = QVBoxLayout()
        before_label = QLabel("الرصيد قبل")
        before_label.setStyleSheet("color: #666;")
        before_container.addWidget(before_label)
        before_value = QLabel(f"{balance_before:,.2f}")
        before_value.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_BODY, QFont.Bold))
        before_container.addWidget(before_value)
        balance_layout.addLayout(before_container)
        
        arrow_label = QLabel("→")
        arrow_label.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_H2))
        balance_layout.addWidget(arrow_label)
        
        after_container = QVBoxLayout()
        after_label = QLabel("الرصيد بعد")
        after_label.setStyleSheet("color: #666;")
        after_container.addWidget(after_label)
        after_value = QLabel(f"{balance_after:,.2f}")
        after_value.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_BODY, QFont.Bold))
        after_value.setStyleSheet(f"color: {header_color};")
        after_container.addWidget(after_value)
        balance_layout.addLayout(after_container)
        
        balance_layout.addStretch()
        details_layout.addRow("الرصيد:", balance_frame)
        
        # Unit cost
        unit_cost = float(self.movement.get('unit_cost', 0))
        if unit_cost > 0:
            details_layout.addRow("تكلفة الوحدة:", QLabel(f"{unit_cost:,.2f} ل.س"))
        
        # Reference section - Requirements: 6.3 - Show source document reference
        reference_number = self.movement.get('reference_number', '')
        reference_type = self.movement.get('reference_type', '')
        reference_id = self.movement.get('reference_id', '')
        
        if reference_number or reference_type:
            ref_frame = QFrame()
            ref_frame.setStyleSheet(f"""
                background-color: {Colors.INFO}10;
                border: 1px solid {Colors.INFO};
                border-radius: 4px;
                padding: 12px;
            """)
            ref_layout = QVBoxLayout(ref_frame)
            ref_layout.setSpacing(4)
            
            ref_title = QLabel("📄 مرجع المستند")
            ref_title.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_BODY, QFont.Bold))
            ref_title.setStyleSheet(f"color: {Colors.INFO};")
            ref_layout.addWidget(ref_title)
            
            if reference_type:
                ref_type_translations = {
                    'Invoice': 'فاتورة مبيعات',
                    'PurchaseOrder': 'أمر شراء',
                    'GoodsReceivedNote': 'سند استلام',
                    'SalesReturn': 'مرتجع مبيعات',
                    'StockAdjustment': 'تسوية مخزون',
                    'StockTransfer': 'تحويل مخزون',
                }
                ref_type_display = ref_type_translations.get(reference_type, reference_type)
                ref_layout.addWidget(QLabel(f"النوع: {ref_type_display}"))
            
            if reference_number:
                ref_layout.addWidget(QLabel(f"الرقم: {reference_number}"))
            
            if reference_id:
                ref_layout.addWidget(QLabel(f"المعرف: {reference_id}"))
            
            details_layout.addRow("", ref_frame)
        
        # Notes
        notes = self.movement.get('notes', '')
        if notes:
            notes_label = QLabel(notes)
            notes_label.setWordWrap(True)
            notes_label.setStyleSheet(f"background-color: {Colors.LIGHT_BG}; padding: 8px; border-radius: 4px;")
            details_layout.addRow("ملاحظات:", notes_label)
        
        # Created by
        created_by = self.movement.get('created_by_name', '')
        if created_by:
            details_layout.addRow("بواسطة:", QLabel(created_by))
        
        scroll.setWidget(details_widget)
        layout.addWidget(scroll)
        
        # Close button
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        close_btn = QPushButton("إغلاق")
        close_btn.setProperty("class", "secondary")
        close_btn.setMinimumHeight(40)
        close_btn.setMinimumWidth(100)
        close_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(close_btn)
        
        layout.addLayout(buttons_layout)


class StockMovementsView(QWidget):
    """
    Stock Movements list view.
    
    Displays movements list with DataTable, color-coded by type,
    and filtering by product, warehouse, type, and date range.
    
    Requirements: 6.1, 6.2, 6.4 - Stock Movements View
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.products = []
        self.warehouses = []
        self.setup_ui()
    
    def setup_ui(self):
        """Initialize the view UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("حركات المخزون")
        title.setProperty("class", "title")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)
        
        # Filters section
        # Requirements: 6.2 - Provide filtering by product, warehouse, movement type, and date range
        filters_frame = QFrame()
        filters_frame.setStyleSheet(f"background-color: {Colors.LIGHT_BG}; border-radius: 8px; padding: 12px;")
        filters_layout = QHBoxLayout(filters_frame)
        filters_layout.setSpacing(12)
        
        # Product filter
        filters_layout.addWidget(QLabel("المنتج:"))
        self.product_filter = QComboBox()
        self.product_filter.setMinimumWidth(150)
        self.product_filter.addItem("الكل", None)
        filters_layout.addWidget(self.product_filter)
        
        # Warehouse filter
        filters_layout.addWidget(QLabel("المستودع:"))
        self.warehouse_filter = QComboBox()
        self.warehouse_filter.setMinimumWidth(120)
        self.warehouse_filter.addItem("الكل", None)
        filters_layout.addWidget(self.warehouse_filter)
        
        # Movement type filter
        filters_layout.addWidget(QLabel("نوع الحركة:"))
        self.type_filter = QComboBox()
        self.type_filter.setMinimumWidth(100)
        self.type_filter.addItem("الكل", None)
        self.type_filter.addItem("📥 وارد", "in")
        self.type_filter.addItem("📤 صادر", "out")
        self.type_filter.addItem("⚖️ تسوية", "adjustment")
        self.type_filter.addItem("🔄 تحويل", "transfer")
        self.type_filter.addItem("↩️ مرتجع", "return")
        self.type_filter.addItem("💔 تالف", "damage")
        filters_layout.addWidget(self.type_filter)
        
        # Date range filter
        filters_layout.addWidget(QLabel("من:"))
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.date_from.setMaximumWidth(130)
        filters_layout.addWidget(self.date_from)
        
        filters_layout.addWidget(QLabel("إلى:"))
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setMaximumWidth(130)
        filters_layout.addWidget(self.date_to)
        
        # Apply filter button
        filter_btn = QPushButton("🔍 بحث")
        filter_btn.setProperty("class", "primary")
        filter_btn.clicked.connect(self.apply_filters)
        filters_layout.addWidget(filter_btn)
        
        # Clear filters button
        clear_btn = QPushButton("مسح")
        clear_btn.setProperty("class", "secondary")
        clear_btn.clicked.connect(self.clear_filters)
        filters_layout.addWidget(clear_btn)
        
        filters_layout.addStretch()
        layout.addWidget(filters_frame)
        
        # Legend for color coding
        # Requirements: 6.4 - Color-code movements by type
        legend_frame = QFrame()
        legend_frame.setStyleSheet("padding: 4px;")
        legend_layout = QHBoxLayout(legend_frame)
        legend_layout.setSpacing(16)
        
        legend_label = QLabel("دليل الألوان:")
        legend_label.setStyleSheet("font-weight: bold;")
        legend_layout.addWidget(legend_label)
        
        # In (green)
        in_indicator = QLabel("● وارد/مرتجع")
        in_indicator.setStyleSheet(f"color: {Colors.SUCCESS};")
        legend_layout.addWidget(in_indicator)
        
        # Out (red)
        out_indicator = QLabel("● صادر/تالف")
        out_indicator.setStyleSheet(f"color: {Colors.DANGER};")
        legend_layout.addWidget(out_indicator)
        
        # Adjustment (yellow/warning)
        adj_indicator = QLabel("● تسوية")
        adj_indicator.setStyleSheet(f"color: {Colors.WARNING};")
        legend_layout.addWidget(adj_indicator)
        
        # Transfer (blue)
        transfer_indicator = QLabel("● تحويل")
        transfer_indicator.setStyleSheet(f"color: {Colors.INFO};")
        legend_layout.addWidget(transfer_indicator)
        
        legend_layout.addStretch()
        layout.addWidget(legend_frame)
        
        # Movements table
        # Requirements: 6.1 - Display stock movements list with columns
        columns = [
            {'key': 'created_at', 'label': 'التاريخ', 'type': 'text'},
            {'key': 'product_name', 'label': 'المنتج', 'type': 'text'},
            {'key': 'warehouse_name', 'label': 'المستودع', 'type': 'text'},
            {'key': 'movement_type_display', 'label': 'نوع الحركة', 'type': 'text'},
            {'key': 'quantity', 'label': 'الكمية', 'type': 'currency'},
            {'key': 'balance_before', 'label': 'الرصيد قبل', 'type': 'currency'},
            {'key': 'balance_after', 'label': 'الرصيد بعد', 'type': 'currency'},
            {'key': 'reference_number', 'label': 'المرجع', 'type': 'text'},
        ]
        
        self.table = DataTable(columns, actions=['view'])
        self.table.add_btn.setVisible(False)  # Movements are created by other operations
        self.table.action_clicked.connect(self.on_action)
        self.table.row_double_clicked.connect(self.view_movement)
        self.table.page_changed.connect(self.on_page_changed)
        self.table.sort_changed.connect(self.on_sort_changed)
        
        layout.addWidget(self.table)
    
    @handle_ui_error
    def refresh(self):
        """Refresh movements data from API."""
        # Load filter options first
        self.load_filter_options()
        
        # Load movements
        params = self._build_params()
        response = api.get_stock_movements(params)
        
        if isinstance(response, dict):
            movements = response.get('results', [])
            total = response.get('count', len(movements))
        else:
            movements = response if isinstance(response, list) else []
            total = len(movements)
        
        # Format dates and apply color coding
        for movement in movements:
            # Format date for display
            created_at = movement.get('created_at', '')
            if created_at and len(created_at) >= 10:
                movement['created_at'] = created_at[:10]
            
            # Add color indicator based on movement type
            movement_type = movement.get('movement_type', '')
            movement['_row_color'] = self._get_movement_color(movement_type)
        
        self.table.set_data(movements, total)
        
        # Apply row colors after setting data
        self._apply_row_colors(movements)
    
    def _get_movement_color(self, movement_type: str) -> str:
        """
        Get color for movement type.
        
        Requirements: 6.4 - Color-code movements by type
        (green for in, red for out, yellow for adjustment)
        """
        colors = {
            'in': Colors.SUCCESS,
            'out': Colors.DANGER,
            'adjustment': Colors.WARNING,
            'transfer': Colors.INFO,
            'return': Colors.SUCCESS,  # Returns add stock back
            'damage': Colors.DANGER,
        }
        return colors.get(movement_type, Colors.LIGHT_TEXT)
    
    def _apply_row_colors(self, movements: list):
        """Apply color coding to table rows based on movement type."""
        for row, movement in enumerate(movements):
            movement_type = movement.get('movement_type', '')
            color = self._get_movement_color(movement_type)
            
            # Apply color to the movement type column (index 3)
            type_item = self.table.table.item(row, 3)
            if type_item:
                type_item.setForeground(QBrush(QColor(color)))
            
            # Also color the quantity column (index 4)
            qty_item = self.table.table.item(row, 4)
            if qty_item:
                qty_item.setForeground(QBrush(QColor(color)))
    
    @handle_ui_error
    def load_filter_options(self):
        """Load products and warehouses for filter dropdowns."""
        # Load products
        if not self.products:
            try:
                response = api.get_products({'page_size': 1000})
                if isinstance(response, dict) and 'results' in response:
                    self.products = response['results']
                else:
                    self.products = response if isinstance(response, list) else []
                
                # Update product filter
                self.product_filter.clear()
                self.product_filter.addItem("الكل", None)
                for product in self.products:
                    display = f"{product.get('code', '')} - {product.get('name', '')}"
                    self.product_filter.addItem(display, product.get('id'))
            except Exception:
                pass
        
        # Load warehouses
        if not self.warehouses:
            try:
                response = api.get_warehouses()
                if isinstance(response, dict) and 'results' in response:
                    self.warehouses = response['results']
                else:
                    self.warehouses = response if isinstance(response, list) else []
                
                # Update warehouse filter
                self.warehouse_filter.clear()
                self.warehouse_filter.addItem("الكل", None)
                for warehouse in self.warehouses:
                    self.warehouse_filter.addItem(warehouse.get('name', ''), warehouse.get('id'))
            except Exception:
                pass
    
    def _build_params(self) -> dict:
        """Build API parameters from filters."""
        params = self.table.get_pagination_params()
        params.update(self.table.get_sort_params())
        
        # Product filter
        product_id = self.product_filter.currentData()
        if product_id:
            params['product'] = product_id
        
        # Warehouse filter
        warehouse_id = self.warehouse_filter.currentData()
        if warehouse_id:
            params['warehouse'] = warehouse_id
        
        # Movement type filter
        movement_type = self.type_filter.currentData()
        if movement_type:
            params['movement_type'] = movement_type
        
        # Date range
        date_from = self.date_from.date().toString('yyyy-MM-dd')
        date_to = self.date_to.date().toString('yyyy-MM-dd')
        params['date_from'] = date_from
        params['date_to'] = date_to
        
        return params
    
    def apply_filters(self):
        """Apply filters and refresh."""
        self.table.current_page = 1
        self.refresh()
    
    def clear_filters(self):
        """Clear all filters."""
        self.product_filter.setCurrentIndex(0)
        self.warehouse_filter.setCurrentIndex(0)
        self.type_filter.setCurrentIndex(0)
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.date_to.setDate(QDate.currentDate())
        self.table.current_page = 1
        self.refresh()
    
    def on_page_changed(self, page: int, page_size: int):
        """Handle page change."""
        self.refresh()
    
    def on_sort_changed(self, column: str, order: str):
        """Handle sort change."""
        self.refresh()
    
    def on_action(self, action: str, row: int, data: dict):
        """Handle table action."""
        if action == 'view':
            self.view_movement(row, data)
    
    @handle_ui_error
    def view_movement(self, row: int, data: dict):
        """
        View movement details.
        
        Requirements: 6.3 - Display full details including source document reference
        """
        movement_id = data.get('id')
        if not movement_id:
            return
        
        try:
            # Fetch full movement details from API
            movement_data = api.get_stock_movement(movement_id)
            
            # Show details dialog
            dialog = StockMovementDetailsDialog(movement_data, parent=self)
            dialog.exec()
            
        except ApiException as e:
            MessageDialog.error(self, "خطأ", f"فشل في تحميل تفاصيل الحركة: {str(e)}")
