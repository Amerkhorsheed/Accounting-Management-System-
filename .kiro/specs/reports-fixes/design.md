# Design Document: Reports Fixes

## Overview

This design document outlines the implementation of missing and broken features in the Reports module (قائمة التقارير). The implementation will add suppliers report, expenses report, export functionality (Excel/PDF), print capability, and fix the customer statement opening balance calculation.

## Architecture

The reports module follows a layered architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (PySide6)                        │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐│
│  │ Suppliers   │ │ Expenses    │ │ Export Service          ││
│  │ Report View │ │ Report View │ │ (Excel/PDF/Print)       ││
│  └─────────────┘ └─────────────┘ └─────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    API Service Layer                         │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ get_suppliers_report() | get_expenses_report()          ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backend (Django REST)                     │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ SuppliersReportView | ExpensesReportView                ││
│  └─────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────┐│
│  │ ReportService.get_suppliers_report()                    ││
│  │ ReportService.get_expenses_report()                     ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### Backend Components

#### 1. SuppliersReportView (New)

```python
class SuppliersReportView(views.APIView):
    """
    Suppliers report endpoint.
    
    Returns supplier statistics including:
    - Total suppliers count
    - Active suppliers count
    - Total payables
    - Supplier list with purchase totals
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        data = ReportService.get_suppliers_report(start_date, end_date)
        return Response(data)
```

#### 2. ExpensesReportView (New)

```python
class ExpensesReportView(views.APIView):
    """
    Expenses report endpoint.
    
    Returns expense analysis including:
    - Total expenses
    - Breakdown by category
    - Individual expense list
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        category_id = request.query_params.get('category')
        data = ReportService.get_expenses_report(start_date, end_date, category_id)
        return Response(data)
```

#### 3. ReportService Extensions

```python
@staticmethod
def get_suppliers_report(start_date, end_date) -> Dict[str, Any]:
    """
    Generate suppliers report.
    
    Returns:
        Dict with summary, supplier_list
    """
    pass

@staticmethod
def get_expenses_report(start_date, end_date, category_id=None) -> Dict[str, Any]:
    """
    Generate expenses report.
    
    Returns:
        Dict with summary, by_category, expenses_list
    """
    pass
```

### Frontend Components

#### 1. SuppliersReportView (New)

A new view class for displaying supplier statistics and list.

```python
class SuppliersReportView(QWidget):
    """
    Suppliers Report View showing supplier statistics and purchase history.
    
    Displays:
    - Summary cards (total suppliers, active, total payables)
    - Supplier list table with purchase totals
    - Date range filter
    """
    back_requested = Signal()
    
    def __init__(self, parent=None):
        pass
    
    def refresh(self):
        """Load report data from API."""
        pass
```

#### 2. ExpensesReportView (New)

A new view class for displaying expense analysis.

```python
class ExpensesReportView(QWidget):
    """
    Expenses Report View showing expense analysis.
    
    Displays:
    - Summary cards (total expenses)
    - Category breakdown with percentages
    - Expenses list table
    - Date range and category filters
    """
    back_requested = Signal()
    
    def __init__(self, parent=None):
        pass
    
    def refresh(self):
        """Load report data from API."""
        pass
```

#### 3. ExportService (New)

A service class for handling report exports.

```python
class ExportService:
    """
    Service for exporting reports to Excel and PDF formats.
    """
    
    @staticmethod
    def export_to_excel(data: List[Dict], columns: List[str], 
                        filename: str, title: str) -> bool:
        """Export data to Excel file."""
        pass
    
    @staticmethod
    def export_to_pdf(data: List[Dict], columns: List[str],
                      filename: str, title: str, 
                      company_info: Dict = None) -> bool:
        """Export data to PDF file."""
        pass
    
    @staticmethod
    def print_document(html_content: str) -> bool:
        """Print HTML document."""
        pass
```

## Data Models

### Suppliers Report Response

```python
{
    'generated_at': date,
    'period': {
        'start': date,
        'end': date
    },
    'summary': {
        'total_suppliers': int,
        'active_suppliers': int,
        'total_payables': Decimal,
        'total_purchases': Decimal
    },
    'suppliers': [
        {
            'id': int,
            'code': str,
            'name': str,
            'total_purchases': Decimal,
            'total_payments': Decimal,
            'outstanding_balance': Decimal,
            'purchase_order_count': int,
            'last_purchase_date': date
        }
    ]
}
```

### Expenses Report Response

```python
{
    'generated_at': date,
    'period': {
        'start': date,
        'end': date
    },
    'summary': {
        'total_expenses': Decimal,
        'expense_count': int,
        'average_expense': Decimal
    },
    'by_category': [
        {
            'category_id': int,
            'category_name': str,
            'total': Decimal,
            'percentage': float,
            'count': int
        }
    ],
    'expenses': [
        {
            'id': int,
            'date': date,
            'category': str,
            'description': str,
            'amount': Decimal,
            'reference': str
        }
    ]
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Suppliers Report Data Completeness and Consistency

*For any* suppliers report response, the sum of all individual supplier outstanding_balance values SHALL equal the total_payables in the summary, and each supplier record SHALL contain all required fields (id, code, name, total_purchases, total_payments, outstanding_balance).

**Validates: Requirements 1.2, 1.4**

### Property 2: Suppliers Report Sorting

*For any* suppliers report, the suppliers list SHALL be sorted by total_purchases in descending order.

**Validates: Requirements 1.3**

### Property 3: Expenses Report Category Percentages

*For any* expenses report with at least one expense, the sum of all category percentages SHALL equal 100% (within 0.01 tolerance).

**Validates: Requirements 2.3**

### Property 4: Expenses Report Total Consistency

*For any* expenses report, the sum of all individual expense amounts in the expenses list SHALL equal the total_expenses in the summary.

**Validates: Requirements 2.2, 2.4**

### Property 5: Customer Statement Opening Balance Calculation

*For any* customer statement with a date range filter, the opening_balance SHALL equal the customer's opening_balance plus the sum of all debits minus credits from transactions before the start_date.

**Validates: Requirements 6.1, 6.2**

### Property 6: Customer Statement Balance Equation

*For any* customer statement, the closing_balance SHALL equal opening_balance plus total_debit minus total_credit.

**Validates: Requirements 6.3**

### Property 7: Customer Statement Running Balance Sequence

*For any* customer statement, each transaction's balance SHALL equal the previous transaction's balance plus the current debit minus the current credit (with the first transaction starting from opening_balance).

**Validates: Requirements 6.4**

## Error Handling

### Export Errors

| Error Condition | User Message | Recovery Action |
|----------------|--------------|-----------------|
| No data to export | "لا توجد بيانات للتصدير" | Show info dialog |
| File write permission denied | "لا يمكن حفظ الملف. تحقق من الصلاحيات" | Suggest different location |
| PDF generation failed | "فشل إنشاء ملف PDF" | Log error, show retry option |
| Excel library not available | "مكتبة Excel غير متوفرة" | Suggest installation |

### Report Loading Errors

| Error Condition | User Message | Recovery Action |
|----------------|--------------|-----------------|
| Network timeout | "انتهت مهلة الاتصال" | Show retry button |
| Server error | "خطأ في الخادم" | Log error, show retry |
| Invalid date range | "نطاق التاريخ غير صالح" | Highlight date fields |

## Testing Strategy

### Unit Tests

- Test ReportService.get_suppliers_report() with various date ranges
- Test ReportService.get_expenses_report() with category filters
- Test ExportService.export_to_excel() with sample data
- Test ExportService.export_to_pdf() with RTL text
- Test customer statement opening balance calculation

### Property-Based Tests

- Property 1: Suppliers report total consistency
- Property 2: Expenses report category percentages sum to 100%
- Property 3: Expenses report total consistency
- Property 4: Customer statement balance consistency

### Integration Tests

- Test full flow from UI click to file download for exports
- Test report navigation and back button functionality
- Test date filter application and data refresh

## Dependencies

### Python Packages (Frontend)

- `openpyxl` - Excel file generation
- `reportlab` - PDF generation
- `arabic-reshaper` - Arabic text shaping for PDF
- `python-bidi` - Bidirectional text support

### Existing Dependencies

- PySide6 - UI framework
- requests - HTTP client
- Django REST Framework - Backend API
