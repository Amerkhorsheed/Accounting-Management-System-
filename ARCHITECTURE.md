# نظام إدارة المحاسبة - وثيقة الهيكلة
# Accounting Management System - Architecture Document

---

## 📐 System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     PRESENTATION LAYER                          │
│                   (PySide6 Desktop App)                         │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │
│  │  Dashboard  │ │  Inventory  │ │    Sales    │ │  Reports  │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      SERVICE LAYER                               │
│                   (API Client Services)                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │
│  │ AuthService │ │ StockService│ │ SalesService│ │ReportSvc  │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼ HTTP/REST
┌─────────────────────────────────────────────────────────────────┐
│                       API LAYER                                  │
│                (Django REST Framework)                           │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │
│  │   /auth/*   │ │ /inventory/*│ │  /sales/*   │ │ /reports/*│ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BUSINESS LAYER                                │
│                  (Django Services)                               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │
│  │InventorySvc │ │ PurchaseSvc │ │  SalesSvc   │ │ ReportSvc │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DATA LAYER                                  │
│                   (Django ORM + SQL Server)                      │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │
│  │   Models    │ │ Repositories│ │  Managers   │ │ QuerySets │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DATABASE                                    │
│                    (SQL Server)                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Technology Stack

| Layer | Technology | Version |
|-------|------------|---------|
| Frontend | PySide6 | 6.6+ |
| Backend | Django | 5.0+ |
| API | Django REST Framework | 3.14+ |
| Database | SQL Server | 2019+ |
| DB Driver | pyodbc / mssql-django | Latest |
| Barcode | python-barcode | 0.15+ |
| PDF | ReportLab | 4.0+ |
| Printing | PyQt Printing / win32print | Latest |

---

## 📁 Directory Structure

```
c:\ERP\
├── ARCHITECTURE.md          # This file
├── TODO.md                  # Feature roadmap
├── README.md                # Project documentation
│
├── backend/                 # Django Backend
│   ├── manage.py
│   ├── requirements.txt
│   ├── config/              # Django configuration
│   │   ├── __init__.py
│   │   ├── settings/
│   │   │   ├── __init__.py
│   │   │   ├── base.py      # Base settings
│   │   │   ├── development.py
│   │   │   └── production.py
│   │   ├── urls.py          # Root URL config
│   │   └── wsgi.py
│   │
│   ├── apps/                # Django applications
│   │   ├── __init__.py
│   │   ├── core/            # Shared utilities
│   │   │   ├── __init__.py
│   │   │   ├── models.py    # Base models
│   │   │   ├── mixins.py    # Model mixins
│   │   │   ├── exceptions.py
│   │   │   └── utils.py
│   │   │
│   │   ├── accounts/        # User management
│   │   │   ├── __init__.py
│   │   │   ├── models.py    # User, Role, Permission
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   ├── services.py
│   │   │   └── urls.py
│   │   │
│   │   ├── inventory/       # Stock management
│   │   │   ├── __init__.py
│   │   │   ├── models.py    # Product, Category, Stock
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   ├── services.py
│   │   │   └── urls.py
│   │   │
│   │   ├── purchases/       # Purchase management
│   │   │   ├── __init__.py
│   │   │   ├── models.py    # Supplier, PO, GRN
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   ├── services.py
│   │   │   └── urls.py
│   │   │
│   │   ├── sales/           # Sales management
│   │   │   ├── __init__.py
│   │   │   ├── models.py    # Customer, Invoice, Payment
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   ├── services.py
│   │   │   └── urls.py
│   │   │
│   │   ├── expenses/        # Expense tracking
│   │   │   ├── __init__.py
│   │   │   ├── models.py
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   ├── services.py
│   │   │   └── urls.py
│   │   │
│   │   └── reports/         # Reporting module
│   │       ├── __init__.py
│   │       ├── services.py  # Report generation
│   │       ├── views.py
│   │       └── urls.py
│   │
│   └── api/                 # API configuration
│       ├── __init__.py
│       └── v1/
│           ├── __init__.py
│           └── urls.py      # API v1 routes
│
├── frontend/                # PySide6 Frontend
│   ├── main.py              # Application entry point
│   ├── requirements.txt
│   │
│   ├── src/
│   │   ├── __init__.py
│   │   ├── app.py           # Main application class
│   │   │
│   │   ├── config/          # Configuration
│   │   │   ├── __init__.py
│   │   │   ├── settings.py  # App settings
│   │   │   └── constants.py # Constants
│   │   │
│   │   ├── services/        # API client services
│   │   │   ├── __init__.py
│   │   │   ├── base.py      # Base API client
│   │   │   ├── auth.py      # Auth service
│   │   │   ├── inventory.py # Inventory API
│   │   │   ├── sales.py     # Sales API
│   │   │   ├── purchases.py # Purchases API
│   │   │   └── reports.py   # Reports API
│   │   │
│   │   ├── models/          # Data models (dataclasses)
│   │   │   ├── __init__.py
│   │   │   ├── product.py
│   │   │   ├── customer.py
│   │   │   ├── invoice.py
│   │   │   └── ...
│   │   │
│   │   ├── views/           # UI screens
│   │   │   ├── __init__.py
│   │   │   ├── main_window.py
│   │   │   ├── dashboard/
│   │   │   │   ├── __init__.py
│   │   │   │   └── dashboard_view.py
│   │   │   ├── inventory/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── products_view.py
│   │   │   │   ├── categories_view.py
│   │   │   │   └── stock_view.py
│   │   │   ├── sales/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── pos_view.py
│   │   │   │   ├── invoices_view.py
│   │   │   │   └── customers_view.py
│   │   │   ├── purchases/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── orders_view.py
│   │   │   │   └── suppliers_view.py
│   │   │   ├── expenses/
│   │   │   │   ├── __init__.py
│   │   │   │   └── expenses_view.py
│   │   │   ├── reports/
│   │   │   │   ├── __init__.py
│   │   │   │   └── reports_view.py
│   │   │   └── settings/
│   │   │       ├── __init__.py
│   │   │       └── settings_view.py
│   │   │
│   │   ├── widgets/         # Reusable UI components
│   │   │   ├── __init__.py
│   │   │   ├── sidebar.py
│   │   │   ├── header.py
│   │   │   ├── cards.py
│   │   │   ├── tables.py
│   │   │   ├── forms.py
│   │   │   ├── dialogs.py
│   │   │   ├── charts.py
│   │   │   └── barcode.py
│   │   │
│   │   ├── styles/          # QSS stylesheets
│   │   │   ├── __init__.py
│   │   │   ├── theme.py     # Theme manager
│   │   │   ├── light.qss
│   │   │   └── dark.qss
│   │   │
│   │   ├── resources/       # Static resources
│   │   │   ├── icons/
│   │   │   ├── images/
│   │   │   └── fonts/
│   │   │
│   │   ├── printing/        # Printing utilities
│   │   │   ├── __init__.py
│   │   │   ├── invoice_printer.py
│   │   │   ├── receipt_printer.py
│   │   │   └── templates/
│   │   │
│   │   └── utils/           # Utilities
│   │       ├── __init__.py
│   │       ├── validators.py
│   │       ├── formatters.py
│   │       └── helpers.py
│   │
│   └── tests/               # Frontend tests
│
└── common/                  # Shared resources
    ├── types/               # Shared type definitions
    └── docs/                # Documentation
```

---

## 🔧 Design Patterns

### 1. Repository Pattern (Backend)
Abstracts data access logic from business logic.

```python
# backend/apps/inventory/repositories.py
class ProductRepository:
    def get_by_id(self, id: int) -> Product
    def get_by_barcode(self, barcode: str) -> Product
    def get_all(self, filters: dict) -> QuerySet
    def create(self, data: dict) -> Product
    def update(self, id: int, data: dict) -> Product
    def delete(self, id: int) -> bool
```

### 2. Service Layer Pattern (Backend)
Encapsulates business logic in service classes.

```python
# backend/apps/inventory/services.py
class InventoryService:
    def __init__(self, repository: ProductRepository):
        self.repository = repository
    
    def adjust_stock(self, product_id: int, quantity: int, reason: str)
    def check_low_stock(self) -> List[Product]
    def calculate_valuation(self, method: str) -> Decimal
```

### 3. MVC/MVP Pattern (Frontend)
Separates UI concerns in PySide6.

```python
# View: Handles UI rendering
# Model: Data representation
# Presenter/Controller: Handles logic between View and Model
```

### 4. Singleton Pattern
Used for services and configuration.

```python
# frontend/src/services/base.py
class APIClient:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
```

### 5. Observer Pattern
For real-time UI updates using Qt signals.

```python
# PySide6 Signals for reactive updates
class InventoryModel(QObject):
    stock_updated = Signal(int, int)  # product_id, new_quantity
```

---

## 🔒 SOLID Principles Application

### Single Responsibility (S)
- Each module handles one domain (inventory, sales, etc.)
- Services contain business logic only
- Views handle UI only

### Open/Closed (O)
- Base classes for extension
- Plugin architecture for reports
- Configurable templates

### Liskov Substitution (L)
- Consistent interfaces across modules
- Base serializers extended properly

### Interface Segregation (I)
- Focused API endpoints
- Specific service interfaces

### Dependency Inversion (D)
- Services depend on abstractions
- Dependency injection used

---

## 🗄️ Database Schema (Key Tables)

```sql
-- Core Tables
Users, Roles, Permissions, AuditLog

-- Inventory
Categories, Products, ProductUnits, Warehouses, Stock, StockMovements

-- Purchases  
Suppliers, PurchaseOrders, PurchaseOrderItems, GoodsReceivedNotes

-- Sales
Customers, Invoices, InvoiceItems, Payments, Returns

-- Expenses
ExpenseCategories, Expenses

-- Settings
CompanySettings, TaxRates, PaymentMethods
```

---

## 🔌 API Endpoints Structure

```
/api/v1/
├── auth/
│   ├── login/
│   ├── logout/
│   └── refresh/
│
├── inventory/
│   ├── products/
│   ├── categories/
│   ├── stock/
│   └── movements/
│
├── purchases/
│   ├── suppliers/
│   ├── orders/
│   └── receiving/
│
├── sales/
│   ├── customers/
│   ├── invoices/
│   ├── payments/
│   └── returns/
│
├── expenses/
│   ├── categories/
│   └── expenses/
│
└── reports/
    ├── profit/
    ├── inventory/
    ├── sales/
    └── expenses/
```

---

## 🎨 UI Component Hierarchy

```
MainWindow
├── Sidebar (Navigation)
│   ├── Logo
│   ├── Menu Items
│   └── User Profile
│
├── Header
│   ├── Search
│   ├── Notifications
│   └── Quick Actions
│
└── Content Area
    ├── Dashboard
    │   ├── Stats Cards
    │   ├── Charts
    │   └── Recent Activity
    │
    ├── Data Views
    │   ├── Toolbar (Add, Filter, Search)
    │   ├── Table/List
    │   └── Pagination
    │
    └── Forms
        ├── Form Fields
        ├── Validation Messages
        └── Action Buttons
```

---

## 🔄 Data Flow

```
User Action → View → Service → API Client → Backend API
                                                 ↓
                                           Business Service
                                                 ↓
                                            Repository
                                                 ↓
                                             Database
                                                 ↓
                                            Response
                                                 ↓
User ← View Updates ← Model Update ← Service ← API Response
```

---

## 📝 Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Files | snake_case | `product_service.py` |
| Classes | PascalCase | `ProductService` |
| Functions | snake_case | `get_by_id()` |
| Constants | UPPER_SNAKE | `MAX_PAGE_SIZE` |
| DB Tables | PascalCase | `Products` |
| API Routes | kebab-case | `/api/v1/products` |

---

## 🔐 Security Measures

1. **Authentication**: JWT tokens with refresh
2. **Authorization**: Role-based access control
3. **Input Validation**: Server-side validation
4. **SQL Injection**: Parameterized queries (ORM)
5. **XSS Prevention**: Output encoding
6. **CORS**: Configured for desktop app
7. **Audit Logging**: All critical actions logged

---

## 📊 Performance Considerations

1. **Database**: Proper indexing on frequently queried fields
2. **Pagination**: All list endpoints paginated
3. **Caching**: Redis for frequently accessed data
4. **Lazy Loading**: UI components loaded on demand
5. **Batch Operations**: Bulk inserts/updates supported

---

*Last Updated: 2025-12-22*
*Version: 1.0.0*
