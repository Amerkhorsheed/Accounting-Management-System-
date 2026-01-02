"""
API Service - HTTP Client for Backend Communication

This module provides the HTTP client for communicating with the Django backend.
All API methods are wrapped with @handle_api_error decorator for consistent
error handling and conversion of network errors to typed exceptions.

Requirements: 3.1, 3.2, 5.1, 5.2
"""
import logging
import requests
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple
from ..config import config
from ..utils.error_handler import handle_api_error
from ..utils.exceptions import ConnectionException, TimeoutException

# Configure logger for API service
logger = logging.getLogger(__name__)


class ApiException(Exception):
    """
    API exception class with enhanced error details.
    
    Attributes:
        message: Human-readable error message
        status_code: HTTP status code (if available)
        error_code: Machine-readable error code from backend
        field_errors: Dictionary of field-specific validation errors
        detail: Additional error details
    """
    
    def __init__(
        self,
        message: str,
        status_code: int = None,
        error_code: str = None,
        field_errors: Dict[str, List[str]] = None,
        detail: str = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or 'API_ERROR'
        self.field_errors = field_errors or {}
        self.detail = detail
        super().__init__(self.message)
    
    def __str__(self) -> str:
        return self.message
    
    def get_field_error(self, field: str) -> Optional[str]:
        """Get error message for a specific field."""
        errors = self.field_errors.get(field, [])
        return errors[0] if errors else None
    
    def has_field_errors(self) -> bool:
        """Check if there are field-specific errors."""
        return bool(self.field_errors)


class ApiService:
    """
    HTTP client for communicating with the Django backend.
    Implements singleton pattern.
    """
    
    _instance = None
    _access_token: Optional[str] = None
    _refresh_token: Optional[str] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        self.base_url = config.API_BASE_URL
        self.timeout = config.API_TIMEOUT
        
    def set_tokens(self, access: str, refresh: str):
        """Set authentication tokens."""
        self._access_token = access
        self._refresh_token = refresh
        
    def clear_tokens(self):
        """Clear authentication tokens."""
        self._access_token = None
        self._refresh_token = None
        
    def _headers(self) -> Dict[str, str]:
        """Get request headers."""
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        if self._access_token:
            headers['Authorization'] = f'Bearer {self._access_token}'
        return headers
        
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """
        Make HTTP request with comprehensive error handling.
        
        Converts network errors to typed exceptions and parses error responses
        to extract field-specific validation errors and business rule violations.
        
        Requirements: 3.1, 3.2, 5.1, 5.2
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            response = requests.request(
                method,
                url,
                headers=self._headers(),
                timeout=self.timeout,
                **kwargs
            )
            
            # Handle token refresh
            if response.status_code == 401 and self._refresh_token:
                if self._refresh_access_token():
                    response = requests.request(
                        method,
                        url,
                        headers=self._headers(),
                        timeout=self.timeout,
                        **kwargs
                    )
            
            # Check for errors and parse response
            if not response.ok:
                self._handle_error_response(response)
            
            return response.json() if response.content else {}
            
        except requests.exceptions.Timeout as e:
            logger.exception(f"Request timeout for {method} {endpoint}")
            raise TimeoutException("انتهت مهلة الاتصال بالخادم. يرجى المحاولة مرة أخرى.")
            
        except requests.exceptions.ConnectionError as e:
            logger.exception(f"Connection error for {method} {endpoint}")
            raise ConnectionException("فشل الاتصال بالخادم. يرجى التحقق من اتصال الشبكة.")
            
        except requests.exceptions.RequestException as e:
            logger.exception(f"Request error for {method} {endpoint}")
            raise ConnectionException(f"فشل في الاتصال بالخادم: {str(e)}")
    
    def _handle_error_response(self, response: requests.Response) -> None:
        """
        Parse error response and raise appropriate ApiException.
        
        Extracts field-specific validation errors and business rule violation
        details from the response body.
        
        Requirements: 5.1, 5.2
        """
        status_code = response.status_code
        error_code = None
        field_errors = {}
        detail = None
        user_message = self._get_status_message(status_code)
        
        try:
            error_data = response.json()
            
            if isinstance(error_data, dict):
                # Extract error code if present
                error_code = error_data.get('code', error_data.get('error_code'))
                
                # Extract detail message
                detail = error_data.get('detail', error_data.get('message'))
                
                # Parse field-specific validation errors
                field_errors = self._extract_field_errors(error_data)
                
                # Build user-friendly message
                if field_errors:
                    # Format field errors for display
                    error_parts = []
                    for field, messages in field_errors.items():
                        field_name = self._translate_field_name(field)
                        error_parts.append(f"{field_name}: {', '.join(messages)}")
                    user_message = '\n'.join(error_parts)
                elif detail:
                    user_message = f"{user_message}: {detail}"
                    
            elif isinstance(error_data, str):
                detail = error_data
                user_message = f"{user_message}: {error_data}"
                
        except Exception:
            # If JSON parsing fails, use response text
            detail = response.text[:200] if response.text else response.reason
            if detail:
                user_message = f"{user_message}: {detail}"
        
        logger.warning(
            f"API error response: {status_code}",
            extra={
                'status_code': status_code,
                'error_code': error_code,
                'detail': detail,
                'field_errors': field_errors,
            }
        )
        
        raise ApiException(
            message=user_message,
            status_code=status_code,
            error_code=error_code,
            field_errors=field_errors,
            detail=detail
        )
    
    def _extract_field_errors(self, error_data: Dict) -> Dict[str, List[str]]:
        """
        Extract field-specific validation errors from DRF error response.
        
        DRF returns validation errors in format:
        {"field_name": ["error1", "error2"], "other_field": ["error"]}
        
        Requirement 5.1: WHEN a validation error occurs THEN the Error_Handler 
        SHALL display which field has the error and why
        """
        field_errors = {}
        
        # Skip known non-field keys (including business exception metadata)
        non_field_keys = {
            'detail', 'code', 'error_code', 'message', 'non_field_errors',
            # InsufficientStockException metadata
            'product_name', 'requested', 'available',
            # Other business exception metadata
            'model', 'identifier', 'reason', 'operation',
        }
        
        for key, value in error_data.items():
            if key in non_field_keys:
                # Handle non_field_errors specially
                if key == 'non_field_errors' and isinstance(value, list):
                    field_errors['general'] = [str(v) for v in value]
                continue
                
            # Convert value to list of strings
            if isinstance(value, list):
                field_errors[key] = [str(v) for v in value]
            elif isinstance(value, str):
                field_errors[key] = [value]
            elif isinstance(value, dict):
                # Nested errors (e.g., for nested serializers)
                nested_errors = self._extract_field_errors(value)
                for nested_key, nested_value in nested_errors.items():
                    field_errors[f"{key}.{nested_key}"] = nested_value
        
        return field_errors
    
    def _translate_field_name(self, field: str) -> str:
        """
        Translate field names to Arabic for user display.
        
        Requirement 5.1: Display which field has the error
        """
        translations = {
            'name': 'الاسم',
            'code': 'الكود',
            'barcode': 'الباركود',
            'price': 'السعر',
            'cost_price': 'سعر التكلفة',
            'sale_price': 'سعر البيع',
            'quantity': 'الكمية',
            'stock': 'المخزون',
            'stock_quantity': 'كمية المخزون',
            'min_stock': 'الحد الأدنى للمخزون',
            'description': 'الوصف',
            'category': 'الفئة',
            'supplier': 'المورد',
            'customer': 'العميل',
            'phone': 'الهاتف',
            'email': 'البريد الإلكتروني',
            'address': 'العنوان',
            'date': 'التاريخ',
            'due_date': 'تاريخ الاستحقاق',
            'amount': 'المبلغ',
            'total': 'الإجمالي',
            'subtotal': 'المجموع الفرعي',
            'discount': 'الخصم',
            'tax': 'الضريبة',
            'notes': 'الملاحظات',
            'status': 'الحالة',
            'items': 'العناصر',
            'product': 'المنتج',
            'unit': 'الوحدة',
            'username': 'اسم المستخدم',
            'password': 'كلمة المرور',
            'general': 'خطأ عام',
            'non_field_errors': 'خطأ عام',
            'detail': 'التفاصيل',
        }
        return translations.get(field, field)
    
    def _get_status_message(self, status_code: int) -> str:
        """
        Get user-friendly message for HTTP status code.
        
        Requirement 5.2: WHEN a business rule violation occurs THEN the Error_Handler 
        SHALL explain the rule that was violated
        """
        messages = {
            400: 'خطأ في البيانات المدخلة',
            401: 'يرجى تسجيل الدخول مرة أخرى',
            403: 'ليس لديك صلاحية لهذه العملية',
            404: 'العنصر المطلوب غير موجود',
            409: 'تعارض في البيانات',
            422: 'خطأ في التحقق من البيانات',
            500: 'خطأ في الخادم',
            502: 'خطأ في الاتصال بالخادم',
            503: 'الخادم غير متاح حالياً',
        }
        return messages.get(status_code, 'حدث خطأ غير متوقع')
            
    def _refresh_access_token(self) -> bool:
        """Refresh the access token."""
        try:
            response = requests.post(
                f"{self.base_url}/auth/token/refresh/",
                json={'refresh': self._refresh_token},
                timeout=self.timeout
            )
            if response.status_code == 200:
                data = response.json()
                self._access_token = data.get('access')
                return True
        except:
            pass
        return False
    
    # Generic CRUD methods with error handling
    @handle_api_error
    def get(self, endpoint: str, params: Dict = None) -> Dict:
        """
        GET request with error handling.
        
        Converts network errors to typed exceptions.
        Requirements: 3.1, 3.2
        """
        return self._request('GET', endpoint, params=params)
    
    @handle_api_error
    def post(self, endpoint: str, data: Dict) -> Dict:
        """
        POST request with error handling.
        
        Converts network errors to typed exceptions.
        Requirements: 3.1, 3.2
        """
        return self._request('POST', endpoint, json=data)
    
    @handle_api_error
    def put(self, endpoint: str, data: Dict) -> Dict:
        """
        PUT request with error handling.
        
        Converts network errors to typed exceptions.
        Requirements: 3.1, 3.2
        """
        return self._request('PUT', endpoint, json=data)
    
    @handle_api_error
    def patch(self, endpoint: str, data: Dict) -> Dict:
        """
        PATCH request with error handling.
        
        Converts network errors to typed exceptions.
        Requirements: 3.1, 3.2
        """
        return self._request('PATCH', endpoint, json=data)
    
    @handle_api_error
    def delete(self, endpoint: str) -> Dict:
        """
        DELETE request with error handling.
        
        Converts network errors to typed exceptions.
        Requirements: 3.1, 3.2
        """
        return self._request('DELETE', endpoint)
    
    # Auth endpoints
    def login(self, username: str, password: str) -> Dict:
        """Login and get tokens."""
        response = self.post('auth/token/', {
            'username': username,
            'password': password
        })
        if 'access' in response:
            self.set_tokens(response['access'], response.get('refresh', ''))
        return response
        
    def logout(self):
        """Logout and clear tokens."""
        self.clear_tokens()
        
    def get_current_user(self) -> Dict:
        """Get current user info."""
        return self.get('auth/users/me/')

    def get_app_context(self, rate_date: Optional[str] = None, strict_fx: bool = False) -> Dict:
        params = {}
        if rate_date:
            params['rate_date'] = rate_date
        if strict_fx:
            params['strict_fx'] = 'true'
        return self.get('core/app-context/', params or None)

    def get_daily_exchange_rates(self, params: Dict = None) -> Dict:
        return self.get('core/daily-exchange-rates/', params)

    def get_daily_exchange_rate(self, id: int) -> Dict:
        return self.get(f'core/daily-exchange-rates/{id}/')

    def create_daily_exchange_rate(self, data: Dict) -> Dict:
        return self.post('core/daily-exchange-rates/', data)

    def update_daily_exchange_rate(self, id: int, data: Dict) -> Dict:
        return self.patch(f'core/daily-exchange-rates/{id}/', data)

    def delete_daily_exchange_rate(self, id: int) -> Dict:
        return self.delete(f'core/daily-exchange-rates/{id}/')

    # Backups endpoints
    def list_backups(self) -> Dict:
        return self.get('core/backups/')

    def create_backup(self, include_media: bool = False) -> Dict:
        return self.post('core/backups/', {'include_media': include_media})

    def delete_backup(self, filename: str) -> Dict:
        return self.delete(f'core/backups/{filename}/')

    @handle_api_error
    def download_backup_to_file(self, filename: str, dest_path: str) -> Dict:
        base = str(self.base_url).rstrip('/')
        url = f"{base}/core/backups/{filename}/download/"
        headers = self._headers().copy()
        headers.pop('Content-Type', None)
        headers['Accept'] = '*/*'

        response = requests.get(url, headers=headers, timeout=self.timeout, stream=True)

        if response.status_code == 401 and self._refresh_token:
            if self._refresh_access_token():
                headers = self._headers().copy()
                headers.pop('Content-Type', None)
                headers['Accept'] = '*/*'
                response = requests.get(url, headers=headers, timeout=self.timeout, stream=True)

        if not response.ok:
            self._handle_error_response(response)

        try:
            with open(dest_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)
        finally:
            try:
                response.close()
            except Exception:
                pass

        return {}

    @handle_api_error
    def restore_backup_from_file(
        self,
        file_path: str,
        restore_media: bool = True,
        replace_media: bool = False,
    ) -> Dict:
        base = str(self.base_url).rstrip('/')
        url = f"{base}/core/backups/restore/"

        def do_request():
            headers = self._headers().copy()
            headers.pop('Content-Type', None)
            headers['Accept'] = 'application/json'

            with open(file_path, 'rb') as f:
                files = {
                    'file': (Path(file_path).name, f, 'application/octet-stream')
                }
                data = {
                    'confirm': 'RESTORE',
                    'restore_media': 'true' if restore_media else 'false',
                    'replace_media': 'true' if replace_media else 'false',
                }
                return requests.post(url, headers=headers, timeout=self.timeout, files=files, data=data)

        response = do_request()

        if response.status_code == 401 and self._refresh_token:
            if self._refresh_access_token():
                response = do_request()

        if not response.ok:
            self._handle_error_response(response)

        return response.json() if response.content else {}
    
    # Products endpoints
    def get_products(self, params: Dict = None) -> Dict:
        return self.get('inventory/products/', params)
        
    def get_product(self, id: int) -> Dict:
        return self.get(f'inventory/products/{id}/')
        
    def get_product_by_barcode(self, barcode: str) -> Dict:
        return self.get('inventory/products/by_barcode/', {'barcode': barcode})
        
    def create_product(self, data: Dict) -> Dict:
        return self.post('inventory/products/', data)
        
    def update_product(self, id: int, data: Dict) -> Dict:
        return self.patch(f'inventory/products/{id}/', data)
        
    def delete_product(self, id: int) -> Dict:
        return self.delete(f'inventory/products/{id}/')
    
    # Categories endpoints
    def get_categories(self) -> List[Dict]:
        return self.get('inventory/categories/')
        
    def get_category_tree(self) -> List[Dict]:
        return self.get('inventory/categories/tree/')
    
    # Warehouses endpoints
    def get_warehouses(self, params: Dict = None) -> List[Dict]:
        return self.get('inventory/warehouses/', params)
    
    def get_default_warehouse(self) -> Dict:
        """Get the default warehouse."""
        warehouses = self.get('inventory/warehouses/', {'is_default': True})
        if isinstance(warehouses, dict) and 'results' in warehouses:
            warehouses = warehouses['results']
        if warehouses and len(warehouses) > 0:
            return warehouses[0]
        # Fallback: get first warehouse if no default
        all_warehouses = self.get('inventory/warehouses/')
        if isinstance(all_warehouses, dict) and 'results' in all_warehouses:
            all_warehouses = all_warehouses['results']
        if all_warehouses and len(all_warehouses) > 0:
            return all_warehouses[0]
        return None
    
    # Customers endpoints
    def get_customers(self, params: Dict = None) -> Dict:
        return self.get('sales/customers/', params)
        
    def get_customer(self, id: int) -> Dict:
        return self.get(f'sales/customers/{id}/')
        
    def create_customer(self, data: Dict) -> Dict:
        return self.post('sales/customers/', data)
        
    def update_customer(self, id: int, data: Dict) -> Dict:
        return self.patch(f'sales/customers/{id}/', data)
        
    def get_customer_statement(self, id: int, start_date: str = None, end_date: str = None) -> Dict:
        params = {}
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        return self.get(f'sales/customers/{id}/statement/', params)
    
    # Payment Collection endpoints (Credit Sales)
    def get_customer_unpaid_invoices(self, customer_id: int) -> List[Dict]:
        """
        Get list of unpaid/partial invoices for a customer.
        
        Returns list of invoices with id, number, date, total, paid, remaining.
        Requirements: 2.1, 7.1
        """
        return self.get('sales/payments/customer_unpaid_invoices/', {'customer_id': customer_id})
    
    def collect_payment_with_allocation(self, data: Dict) -> Dict:
        """
        Create payment with invoice allocations in one transaction.
        
        Args:
            data: Dictionary containing:
                - customer: Customer ID
                - payment_date: Date of payment (YYYY-MM-DD)
                - amount: Payment amount (Decimal)
                - payment_method: Payment method (cash, card, bank, check, credit)
                - reference: Optional reference number
                - notes: Optional notes
                - allocations: Optional list of {invoice_id, amount} objects
                - auto_allocate: Boolean - if true, uses FIFO strategy
                
        Returns:
            Created payment with allocations
            
        Requirements: 2.1, 7.1
        """
        return self.post('sales/payments/collect_with_allocation/', data)
    
    # Invoices endpoints
    def get_invoices(self, params: Dict = None) -> Dict:
        return self.get('sales/invoices/', params)
        
    def get_invoice(self, id: int) -> Dict:
        return self.get(f'sales/invoices/{id}/')
        
    def create_invoice(self, data: Dict) -> Dict:
        return self.post('sales/invoices/', data)
        
    def confirm_invoice(self, id: int) -> Dict:
        return self.post(f'sales/invoices/{id}/confirm/', {})
        
    def get_invoice_profit(self, id: int) -> Dict:
        return self.get(f'sales/invoices/{id}/profit/')
    
    # Suppliers endpoints
    def get_suppliers(self, params: Dict = None) -> Dict:
        return self.get('purchases/suppliers/', params)
        
    def create_supplier(self, data: Dict) -> Dict:
        return self.post('purchases/suppliers/', data)

    def get_supplier_statement(self, supplier_id: int, start_date: str = None, end_date: str = None) -> Dict:
        params = {}
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        return self.get(f'purchases/suppliers/{supplier_id}/statement/', params)
    
    # Purchase Orders endpoints
    def get_purchase_orders(self, params: Dict = None) -> Dict:
        return self.get('purchases/orders/', params)
        
    def create_purchase_order(self, data: Dict) -> Dict:
        return self.post('purchases/orders/', data)
        
    def approve_purchase_order(self, id: int) -> Dict:
        return self.post(f'purchases/orders/{id}/approve/', {})
        
    def receive_goods(self, id: int, data: Dict) -> Dict:
        return self.post(f'purchases/orders/{id}/receive/', data)

    # Supplier Payments endpoints
    def get_supplier_payments(self, params: Dict = None) -> Dict:
        return self.get('purchases/payments/', params)

    def get_supplier_payment(self, payment_id: int) -> Dict:
        return self.get(f'purchases/payments/{payment_id}/')

    def create_supplier_payment(self, data: Dict) -> Dict:
        return self.post('purchases/payments/', data)
    
    # Expenses endpoints
    def get_expenses(self, params: Dict = None) -> Dict:
        return self.get('expenses/expenses/', params)
        
    def create_expense(self, data: Dict) -> Dict:
        return self.post('expenses/expenses/', data)
        
    def get_expense_categories(self) -> List[Dict]:
        return self.get('expenses/categories/')
    
    # Reports endpoints
    def get_dashboard(self, start_date: str = None, end_date: str = None) -> Dict:
        params = {}
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        return self.get('reports/dashboard/', params)
        
    def get_sales_report(self, start_date: str, end_date: str, group_by: str = 'day') -> Dict:
        return self.get('reports/sales/', {
            'start_date': start_date,
            'end_date': end_date,
            'group_by': group_by
        })
        
    def get_profit_report(self, start_date: str, end_date: str) -> Dict:
        return self.get('reports/profit/', {
            'start_date': start_date,
            'end_date': end_date
        })
        
    def get_inventory_report(self) -> Dict:
        return self.get('reports/inventory/')
        
    def get_customer_report(self, start_date: str = None, end_date: str = None) -> Dict:
        params = {}
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        return self.get('reports/customers/', params)
    
    def get_receivables_report(
        self,
        customer_type: str = None,
        salesperson_id: int = None,
        start_date: str = None,
        end_date: str = None
    ) -> Dict:
        """
        Get receivables report with customer balances.
        
        Args:
            customer_type: Optional filter by customer type
            salesperson_id: Optional filter by salesperson
            start_date: Optional filter start date
            end_date: Optional filter end date
            
        Returns:
            Report with total_outstanding, customers list sorted by balance,
            and counts of unpaid/partial invoices per customer.
            
        Requirements: 4.1-4.5
        """
        params = {}
        if customer_type:
            params['customer_type'] = customer_type
        if salesperson_id:
            params['salesperson'] = salesperson_id
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        return self.get('reports/receivables/', params)
    
    def get_aging_report(self, as_of_date: str = None) -> Dict:
        """
        Get aging report categorized by overdue periods.
        
        Args:
            as_of_date: Optional date to calculate aging from (defaults to today)
            
        Returns:
            Report with aging buckets (current, 1-30, 31-60, 61-90, >90 days),
            totals per category, and invoice details.
            
        Requirements: 5.1-5.5
        """
        params = {}
        if as_of_date:
            params['as_of_date'] = as_of_date
        return self.get('reports/aging/', params)
    
    def get_suppliers_report(
        self,
        start_date: str = None,
        end_date: str = None
    ) -> Dict:
        """
        Get suppliers report with supplier statistics and purchase history.
        
        Args:
            start_date: Optional filter start date (YYYY-MM-DD)
            end_date: Optional filter end date (YYYY-MM-DD)
            
        Returns:
            Report with:
            - summary: total_suppliers, active_suppliers, total_payables, total_purchases
            - suppliers: list of suppliers with purchase totals and outstanding balances
            
        Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6
        """
        params = {}
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        return self.get('reports/suppliers/', params)
    
    def get_expenses_report(
        self,
        start_date: str = None,
        end_date: str = None,
        category_id: int = None
    ) -> Dict:
        """
        Get expenses report with expense analysis by category.
        
        Args:
            start_date: Optional filter start date (YYYY-MM-DD)
            end_date: Optional filter end date (YYYY-MM-DD)
            category_id: Optional filter by expense category ID
            
        Returns:
            Report with:
            - summary: total_expenses, expense_count, average_expense
            - by_category: list of categories with totals and percentages
            - expenses: list of individual expenses with details
            
        Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6
        """
        params = {}
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        if category_id:
            params['category'] = category_id
        return self.get('reports/expenses/', params)
    
    # =========================================================================
    # Stock Movements API Methods
    # Requirements: 6.1, 6.2
    # =========================================================================
    
    def get_stock_movements(self, params: Dict = None) -> Dict:
        """
        Get stock movements with optional filtering.
        
        Args:
            params: Optional filter parameters:
                - product: Filter by product ID
                - warehouse: Filter by warehouse ID
                - movement_type: Filter by type (in, out, adjustment, transfer, return, damage)
                - source_type: Filter by source (purchase, sale, adjustment, transfer, opening, return)
                - date_from: Filter from date (YYYY-MM-DD)
                - date_to: Filter to date (YYYY-MM-DD)
                - page: Page number for pagination
                - page_size: Number of items per page
                
        Returns:
            Paginated list of stock movements with columns:
            date, product, warehouse, type, quantity, balance_before, balance_after, reference
            
        Requirements: 6.1, 6.2
        """
        return self.get('inventory/movements/', params)
    
    def get_stock_movement(self, movement_id: int) -> Dict:
        """
        Get stock movement details.
        
        Args:
            movement_id: ID of the stock movement
            
        Returns:
            Full movement details including source document reference
            
        Requirements: 6.3
        """
        return self.get(f'inventory/movements/{movement_id}/')
    
    # =========================================================================
    # Sales Returns API Methods
    # Requirements: 5.1, 5.9
    # =========================================================================
    
    def create_sales_return(self, invoice_id: int, data: Dict) -> Dict:
        """
        Create a sales return for an invoice.
        
        Args:
            invoice_id: ID of the original invoice
            data: Return data containing:
                - return_date: Date of return (YYYY-MM-DD)
                - reason: Required - Reason for return
                - notes: Optional notes
                - items: List of items to return:
                    - invoice_item_id: ID of the invoice item
                    - quantity: Quantity to return
                    - reason: Optional reason for this item
                    
        Returns:
            Created sales return with full details
            
        Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8
        """
        return self.post(f'sales/invoices/{invoice_id}/return_items/', data)
    
    def get_sales_returns(self, params: Dict = None) -> Dict:
        """
        Get list of sales returns with optional filtering.
        
        Args:
            params: Optional filter parameters:
                - original_invoice: Filter by original invoice ID
                - page: Page number for pagination
                - page_size: Number of items per page
                - search: Search by return number, invoice number, or reason
                
        Returns:
            Paginated list of sales returns with columns:
            number, original_invoice, date, total, reason
            
        Requirements: 5.9
        """
        return self.get('sales/returns/', params)
    
    def get_sales_return(self, return_id: int) -> Dict:
        """
        Get sales return details.
        
        Args:
            return_id: ID of the sales return
            
        Returns:
            Full sales return details with items
            
        Requirements: 5.9
        """
        return self.get(f'sales/returns/{return_id}/')
    
    # =========================================================================
    # Invoice Cancel API Method
    # Requirements: 4.4
    # =========================================================================
    
    def cancel_invoice(self, invoice_id: int, reason: str) -> Dict:
        """
        Cancel an invoice and reverse all effects.
        
        Args:
            invoice_id: ID of the invoice to cancel
            reason: Required - Reason for cancellation
            
        Returns:
            Updated invoice with cancelled status
            
        Requirements: 4.4, 4.5
        - Validates invoice can be cancelled (confirmed, paid, or partial status)
        - Reverses stock movements (adds stock back)
        - Reverses customer balance changes
        - Updates invoice status to cancelled
        """
        return self.post(f'sales/invoices/{invoice_id}/cancel/', {'reason': reason})
    
    # =========================================================================
    # Categories CRUD API Methods
    # Requirements: 8.2, 8.3, 8.4
    # =========================================================================
    
    def create_category(self, data: Dict) -> Dict:
        """
        Create a new product category.
        
        Args:
            data: Category data containing:
                - name: Category name (Arabic)
                - name_en: Optional English name
                - parent: Optional parent category ID
                - description: Optional description
                
        Returns:
            Created category
            
        Requirements: 8.2
        """
        return self.post('inventory/categories/', data)
    
    def update_category(self, category_id: int, data: Dict) -> Dict:
        """
        Update an existing category.
        
        Args:
            category_id: ID of the category to update
            data: Updated category data
            
        Returns:
            Updated category
            
        Requirements: 8.3
        """
        return self.patch(f'inventory/categories/{category_id}/', data)
    
    def delete_category(self, category_id: int) -> Dict:
        """
        Delete a category (soft delete).
        
        Args:
            category_id: ID of the category to delete
            
        Returns:
            Empty response on success
            
        Raises:
            ApiException: If category has products (deletion protected)
            
        Requirements: 8.4, 8.5
        """
        return self.delete(f'inventory/categories/{category_id}/')
    
    def get_category(self, category_id: int) -> Dict:
        """
        Get category details.
        
        Args:
            category_id: ID of the category
            
        Returns:
            Category details
        """
        return self.get(f'inventory/categories/{category_id}/')
    
    # =========================================================================
    # Units CRUD API Methods
    # Requirements: 9.2, 9.3, 9.4
    # =========================================================================
    
    def get_units(self, params: Dict = None) -> List[Dict]:
        """
        Get list of units.
        
        Args:
            params: Optional filter parameters
            
        Returns:
            List of units
            
        Requirements: 9.1
        """
        return self.get('inventory/units/', params)
    
    def get_unit(self, unit_id: int) -> Dict:
        """
        Get unit details.
        
        Args:
            unit_id: ID of the unit
            
        Returns:
            Unit details
        """
        return self.get(f'inventory/units/{unit_id}/')
    
    def create_unit(self, data: Dict) -> Dict:
        """
        Create a new unit of measure.
        
        Args:
            data: Unit data containing:
                - name: Unit name (Arabic)
                - name_en: Optional English name
                - symbol: Unit symbol
                
        Returns:
            Created unit
            
        Requirements: 9.2
        """
        return self.post('inventory/units/', data)
    
    def update_unit(self, unit_id: int, data: Dict) -> Dict:
        """
        Update an existing unit.
        
        Args:
            unit_id: ID of the unit to update
            data: Updated unit data
            
        Returns:
            Updated unit
            
        Requirements: 9.3
        """
        return self.patch(f'inventory/units/{unit_id}/', data)
    
    def delete_unit(self, unit_id: int) -> Dict:
        """
        Delete a unit (soft delete).
        
        Args:
            unit_id: ID of the unit to delete
            
        Returns:
            Empty response on success
            
        Raises:
            ApiException: If unit is used by products (deletion protected)
            
        Requirements: 9.4, 9.5
        """
        return self.delete(f'inventory/units/{unit_id}/')
    
    # =========================================================================
    # Warehouses CRUD API Methods
    # Requirements: 10.2, 10.3, 10.4
    # =========================================================================
    
    def get_warehouse(self, warehouse_id: int) -> Dict:
        """
        Get warehouse details.
        
        Args:
            warehouse_id: ID of the warehouse
            
        Returns:
            Warehouse details
        """
        return self.get(f'inventory/warehouses/{warehouse_id}/')
    
    def create_warehouse(self, data: Dict) -> Dict:
        """
        Create a new warehouse.
        
        Args:
            data: Warehouse data containing:
                - code: Warehouse code
                - name: Warehouse name
                - address: Optional address
                - is_default: Whether this is the default warehouse
                
        Returns:
            Created warehouse
            
        Requirements: 10.2
        """
        return self.post('inventory/warehouses/', data)
    
    def update_warehouse(self, warehouse_id: int, data: Dict) -> Dict:
        """
        Update an existing warehouse.
        
        Args:
            warehouse_id: ID of the warehouse to update
            data: Updated warehouse data
            
        Returns:
            Updated warehouse
            
        Requirements: 10.3
        """
        return self.patch(f'inventory/warehouses/{warehouse_id}/', data)
    
    def delete_warehouse(self, warehouse_id: int) -> Dict:
        """
        Delete a warehouse (soft delete).
        
        Args:
            warehouse_id: ID of the warehouse to delete
            
        Returns:
            Empty response on success
            
        Raises:
            ApiException: If warehouse has stock (deletion protected)
            
        Requirements: 10.4, 10.5
        """
        return self.delete(f'inventory/warehouses/{warehouse_id}/')
    
    # =========================================================================
    # Expense Categories CRUD API Methods
    # Requirements: 11.2, 11.3, 11.4
    # =========================================================================
    
    def get_expense_category(self, category_id: int) -> Dict:
        """
        Get expense category details.
        
        Args:
            category_id: ID of the expense category
            
        Returns:
            Expense category details
        """
        return self.get(f'expenses/categories/{category_id}/')
    
    def create_expense_category(self, data: Dict) -> Dict:
        """
        Create a new expense category.
        
        Args:
            data: Category data containing:
                - name: Category name (Arabic)
                - name_en: Optional English name
                - parent: Optional parent category ID
                - description: Optional description
                
        Returns:
            Created expense category
            
        Requirements: 11.2
        """
        return self.post('expenses/categories/', data)
    
    def update_expense_category(self, category_id: int, data: Dict) -> Dict:
        """
        Update an existing expense category.
        
        Args:
            category_id: ID of the expense category to update
            data: Updated category data
            
        Returns:
            Updated expense category
            
        Requirements: 11.3
        """
        return self.patch(f'expenses/categories/{category_id}/', data)
    
    def delete_expense_category(self, category_id: int) -> Dict:
        """
        Delete an expense category (soft delete).
        
        Args:
            category_id: ID of the expense category to delete
            
        Returns:
            Empty response on success
            
        Raises:
            ApiException: If category has expenses (deletion protected)
            
        Requirements: 11.4, 11.5
        """
        return self.delete(f'expenses/categories/{category_id}/')
    
    # =========================================================================
    # Expenses CRUD API Methods (Enhanced)
    # Requirements: 7.3, 7.4
    # =========================================================================
    
    def get_expense(self, expense_id: int) -> Dict:
        """
        Get expense details.
        
        Args:
            expense_id: ID of the expense
            
        Returns:
            Expense details
        """
        return self.get(f'expenses/expenses/{expense_id}/')
    
    def update_expense(self, expense_id: int, data: Dict) -> Dict:
        """
        Update an existing expense.
        
        Args:
            expense_id: ID of the expense to update
            data: Updated expense data
            
        Returns:
            Updated expense
            
        Requirements: 7.3
        """
        return self.patch(f'expenses/expenses/{expense_id}/', data)
    
    def delete_expense(self, expense_id: int) -> Dict:
        """
        Delete an expense (soft delete).
        
        Args:
            expense_id: ID of the expense to delete
            
        Returns:
            Empty response on success
            
        Requirements: 7.4
        """
        return self.delete(f'expenses/expenses/{expense_id}/')
    
    # =========================================================================
    # Customers CRUD API Methods (Enhanced)
    # Requirements: 1.4
    # =========================================================================
    
    def delete_customer(self, customer_id: int) -> Dict:
        """
        Delete a customer (soft delete).
        
        Args:
            customer_id: ID of the customer to delete
            
        Returns:
            Empty response on success
            
        Raises:
            ApiException: If customer has outstanding invoices (deletion protected)
            
        Requirements: 1.4, 1.5
        """
        return self.delete(f'sales/customers/{customer_id}/')
    
    # =========================================================================
    # Suppliers CRUD API Methods (Enhanced)
    # Requirements: 3.3, 3.4
    # =========================================================================
    
    def get_supplier(self, supplier_id: int) -> Dict:
        """
        Get supplier details.
        
        Args:
            supplier_id: ID of the supplier
            
        Returns:
            Supplier details
        """
        return self.get(f'purchases/suppliers/{supplier_id}/')
    
    def update_supplier(self, supplier_id: int, data: Dict) -> Dict:
        """
        Update an existing supplier.
        
        Args:
            supplier_id: ID of the supplier to update
            data: Updated supplier data
            
        Returns:
            Updated supplier
            
        Requirements: 3.3
        """
        return self.patch(f'purchases/suppliers/{supplier_id}/', data)
    
    def delete_supplier(self, supplier_id: int) -> Dict:
        """
        Delete a supplier (soft delete).
        
        Args:
            supplier_id: ID of the supplier to delete
            
        Returns:
            Empty response on success
            
        Raises:
            ApiException: If supplier has purchase orders (deletion protected)
            
        Requirements: 3.4, 3.5
        """
        return self.delete(f'purchases/suppliers/{supplier_id}/')
    
    # =========================================================================
    # Payments API Methods (Enhanced)
    # Requirements: 13.1, 13.2, 13.3
    # =========================================================================
    
    def get_payments(self, params: Dict = None) -> Dict:
        """
        Get list of payments with optional filtering.
        
        Args:
            params: Optional filter parameters:
                - customer: Filter by customer ID
                - payment_method: Filter by payment method
                - invoice: Filter by invoice ID
                - page: Page number for pagination
                - page_size: Number of items per page
                
        Returns:
            Paginated list of payments
            
        Requirements: 13.1
        """
        return self.get('sales/payments/', params)
    
    def get_payment(self, payment_id: int) -> Dict:
        """
        Get payment details with allocations.
        
        Args:
            payment_id: ID of the payment
            
        Returns:
            Payment details with allocations list
            
        Requirements: 13.3
        """
        return self.get(f'sales/payments/{payment_id}/')
    
    def create_payment(self, data: Dict) -> Dict:
        """
        Create a new payment.
        
        Args:
            data: Payment data containing:
                - customer: Customer ID
                - payment_date: Date of payment (YYYY-MM-DD)
                - amount: Payment amount
                - payment_method: Payment method (cash, card, bank, check, credit)
                - reference: Optional reference number
                - notes: Optional notes
                - invoice: Optional single invoice ID
                
        Returns:
            Created payment
            
        Requirements: 13.2
        """
        return self.post('sales/payments/', data)
    
    # =========================================================================
    # Purchase Orders API Methods (Enhanced)
    # Requirements: 12.2, 12.4
    # =========================================================================
    
    def get_purchase_order(self, order_id: int) -> Dict:
        """
        Get purchase order details with items.
        
        Args:
            order_id: ID of the purchase order
            
        Returns:
            Full purchase order details with items
            
        Requirements: 12.2
        """
        return self.get(f'purchases/orders/{order_id}/')
    
    def update_purchase_order(self, order_id: int, data: Dict) -> Dict:
        """
        Update a purchase order (only draft status).
        
        Args:
            order_id: ID of the purchase order to update
            data: Updated order data
            
        Returns:
            Updated purchase order
            
        Requirements: 12.3
        """
        return self.patch(f'purchases/orders/{order_id}/', data)
    
    def mark_purchase_order_ordered(self, order_id: int) -> Dict:
        """
        Mark a purchase order as ordered.
        
        Args:
            order_id: ID of the purchase order
            
        Returns:
            Updated purchase order
            
        Requirements: 12.4
        """
        return self.post(f'purchases/orders/{order_id}/mark_ordered/', {})


# Global API instance
api = ApiService()
