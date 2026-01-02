"""
Unit Selector Widget for Sales and Purchases

Requirements: 3.1, 4.1 - Unit selection in sales and purchases
"""
from PySide6.QtWidgets import QComboBox, QWidget, QHBoxLayout, QLabel
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont
from decimal import Decimal
from typing import Optional, List, Dict, Any

from ..config import Colors, Fonts


class UnitSelectorComboBox(QComboBox):
    """
    A combo box for selecting product units in sales and purchases.
    
    Displays available units for a selected product with unit name and price.
    Emits signal when unit changes to update price field.
    
    Requirements: 3.1, 4.1 - Display available units for selected product
    """
    
    # Signal emitted when unit selection changes
    # Emits: (product_unit_id, unit_name, unit_symbol, sale_price, cost_price, conversion_factor)
    unit_changed = Signal(int, str, str, float, float, float)
    
    def __init__(self, parent=None, price_type: str = 'sale'):
        """
        Initialize the unit selector.
        
        Args:
            parent: Parent widget
            price_type: 'sale' for sales forms, 'cost' for purchase forms
        """
        super().__init__(parent)
        self.price_type = price_type
        self.product_units: List[Dict[str, Any]] = []
        self.current_product_id: Optional[int] = None
        
        # Setup UI
        self.setPlaceholderText("الوحدة")
        self.setMinimumWidth(120)
        self.setMinimumHeight(32)
        
        # Connect signal
        self.currentIndexChanged.connect(self._on_selection_changed)
        
        # Style
        self.setStyleSheet(f"""
            QComboBox {{
                padding: 4px 8px;
                border: 1px solid {Colors.LIGHT_BORDER};
                border-radius: 4px;
                background-color: white;
                font-size: 12px;
            }}
            QComboBox:hover {{
                border-color: {Colors.PRIMARY};
            }}
            QComboBox:focus {{
                border-color: {Colors.PRIMARY};
                border-width: 2px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid {Colors.LIGHT_TEXT};
                margin-right: 5px;
            }}
            QComboBox QAbstractItemView {{
                border: 1px solid {Colors.LIGHT_BORDER};
                border-radius: 4px;
                background-color: white;
                selection-background-color: {Colors.PRIMARY}20;
                selection-color: {Colors.PRIMARY};
            }}
        """)
    
    def set_product_units(self, product_units: List[Dict[str, Any]], product_id: int = None):
        """
        Set available units for a product.
        
        Args:
            product_units: List of product unit dictionaries from API
            product_id: Optional product ID for tracking
        """
        self.blockSignals(True)
        self.clear()
        self.product_units = product_units or []
        self.current_product_id = product_id
        
        if not self.product_units:
            self.addItem("لا توجد وحدات", None)
            self.setEnabled(False)
            self.blockSignals(False)
            return
        
        self.setEnabled(True)
        
        # Add units to combo box
        for pu in self.product_units:
            unit_name = pu.get('unit_name', '')
            unit_symbol = pu.get('unit_symbol', '')
            is_base = pu.get('is_base_unit', False)
            
            # Get price based on type
            if self.price_type == 'sale':
                price = pu.get('sale_price_usd', None)
                if price is None:
                    price = pu.get('sale_price', 0)
                price = float(price or 0)
            else:
                price = pu.get('cost_price_usd', None)
                if price is None:
                    price = pu.get('cost_price', 0)
                price = float(price or 0)
            
            # Format display text
            base_indicator = " ⭐" if is_base else ""
            display_text = f"{unit_name} ({unit_symbol}) - {price:,.2f}{base_indicator}"
            
            # Store product_unit id as data
            pu_id = pu.get('id')
            self.addItem(display_text, pu_id)
        
        # Select base unit by default
        self._select_base_unit()
        
        self.blockSignals(False)
    
    def _select_base_unit(self):
        """Select the base unit by default."""
        for i, pu in enumerate(self.product_units):
            if pu.get('is_base_unit', False):
                self.setCurrentIndex(i)
                return
        # If no base unit found, select first
        if self.count() > 0:
            self.setCurrentIndex(0)
    
    def _on_selection_changed(self, index: int):
        """Handle selection change and emit signal."""
        if index < 0 or index >= len(self.product_units):
            return
        
        pu = self.product_units[index]
        pu_id = pu.get('id', 0)
        unit_name = pu.get('unit_name', '')
        unit_symbol = pu.get('unit_symbol', '')
        sale_price = pu.get('sale_price_usd', None)
        if sale_price is None:
            sale_price = pu.get('sale_price', 0)
        sale_price = float(sale_price or 0)

        cost_price = pu.get('cost_price_usd', None)
        if cost_price is None:
            cost_price = pu.get('cost_price', 0)
        cost_price = float(cost_price or 0)
        conversion_factor = float(pu.get('conversion_factor', 1))
        
        self.unit_changed.emit(
            pu_id, unit_name, unit_symbol, 
            sale_price, cost_price, conversion_factor
        )
    
    def get_selected_unit(self) -> Optional[Dict[str, Any]]:
        """
        Get the currently selected product unit.
        
        Returns:
            Dictionary with product unit data or None if nothing selected
        """
        index = self.currentIndex()
        if index < 0 or index >= len(self.product_units):
            return None
        return self.product_units[index]
    
    def get_selected_unit_id(self) -> Optional[int]:
        """Get the ID of the currently selected product unit."""
        return self.currentData()
    
    def get_selected_price(self) -> float:
        """Get the price of the currently selected unit based on price_type."""
        pu = self.get_selected_unit()
        if not pu:
            return 0.0
        
        if self.price_type == 'sale':
            price = pu.get('sale_price_usd', None)
            if price is None:
                price = pu.get('sale_price', 0)
            return float(price or 0)
        else:
            price = pu.get('cost_price_usd', None)
            if price is None:
                price = pu.get('cost_price', 0)
            return float(price or 0)
    
    def get_conversion_factor(self) -> float:
        """Get the conversion factor of the currently selected unit."""
        pu = self.get_selected_unit()
        if not pu:
            return 1.0
        return float(pu.get('conversion_factor', 1))
    
    def clear_units(self):
        """Clear all units from the selector."""
        self.blockSignals(True)
        self.clear()
        self.product_units = []
        self.current_product_id = None
        self.setEnabled(False)
        self.blockSignals(False)
    
    def select_unit_by_id(self, product_unit_id: int) -> bool:
        """
        Select a unit by its product_unit ID.
        
        Args:
            product_unit_id: The ID of the product unit to select
            
        Returns:
            True if unit was found and selected, False otherwise
        """
        for i, pu in enumerate(self.product_units):
            if pu.get('id') == product_unit_id:
                self.setCurrentIndex(i)
                return True
        return False


class UnitSelectorWidget(QWidget):
    """
    A widget containing a unit selector with optional label.
    
    Provides a more complete unit selection experience with label.
    """
    
    unit_changed = Signal(int, str, str, float, float, float)
    
    def __init__(self, label: str = "الوحدة", price_type: str = 'sale', parent=None):
        """
        Initialize the unit selector widget.
        
        Args:
            label: Label text to display
            price_type: 'sale' for sales forms, 'cost' for purchase forms
            parent: Parent widget
        """
        super().__init__(parent)
        self.setup_ui(label, price_type)
    
    def setup_ui(self, label: str, price_type: str):
        """Initialize the widget UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Label
        self.label = QLabel(label)
        self.label.setFont(QFont(Fonts.FAMILY_AR, Fonts.SIZE_BODY))
        layout.addWidget(self.label)
        
        # Unit selector
        self.selector = UnitSelectorComboBox(price_type=price_type)
        self.selector.unit_changed.connect(self.unit_changed.emit)
        layout.addWidget(self.selector, 1)
    
    def set_product_units(self, product_units: List[Dict[str, Any]], product_id: int = None):
        """Set available units for a product."""
        self.selector.set_product_units(product_units, product_id)
    
    def get_selected_unit(self) -> Optional[Dict[str, Any]]:
        """Get the currently selected product unit."""
        return self.selector.get_selected_unit()
    
    def get_selected_unit_id(self) -> Optional[int]:
        """Get the ID of the currently selected product unit."""
        return self.selector.get_selected_unit_id()
    
    def get_selected_price(self) -> float:
        """Get the price of the currently selected unit."""
        return self.selector.get_selected_price()
    
    def get_conversion_factor(self) -> float:
        """Get the conversion factor of the currently selected unit."""
        return self.selector.get_conversion_factor()
    
    def clear_units(self):
        """Clear all units from the selector."""
        self.selector.clear_units()
    
    def select_unit_by_id(self, product_unit_id: int) -> bool:
        """Select a unit by its product_unit ID."""
        return self.selector.select_unit_by_id(product_unit_id)
