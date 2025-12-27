"""
Tests for Expense model.
"""
import pytest
from decimal import Decimal
from apps.expenses.models import Expense, ExpenseCategory


@pytest.mark.django_db
class TestExpenseModel:
    """Test suite for Expense model."""
    
    @pytest.fixture(autouse=True)
    def setup_data(self, today):
        """Setup test data."""
        self.category = ExpenseCategory.objects.create(
            name='Office Supplies',
            description='Office supplies and stationery'
        )
        self.today = today
    
    def test_create_expense(self):
        """Test creating an expense."""
        expense = Expense.objects.create(
            category=self.category,
            expense_date=self.today,
            amount=Decimal('500.00'),
            description='Office supplies purchase'
        )
        assert expense.category == self.category
        assert expense.expense_date == self.today
        assert expense.amount == Decimal('500.00')
        assert expense.description == 'Office supplies purchase'
    
    def test_expense_auto_generate_number(self):
        """Test expense number auto-generation."""
        expense = Expense.objects.create(
            category=self.category,
            expense_date=self.today,
            amount=Decimal('500.00'),
            description='Test expense'
        )
        assert expense.expense_number is not None
        assert expense.expense_number.startswith('EXP')
    
    def test_expense_string_representation(self):
        """Test expense string representation."""
        expense = Expense.objects.create(
            expense_number='EXP001',
            category=self.category,
            expense_date=self.today,
            amount=Decimal('500.00'),
            description='Office supplies purchase for the month'
        )
        assert str(expense) == 'EXP001 - Office supplies purchase for the month'
    
    def test_expense_total_amount_calculation(self):
        """Test total_amount auto-calculation."""
        expense = Expense.objects.create(
            category=self.category,
            expense_date=self.today,
            amount=Decimal('500.00'),
            tax_amount=Decimal('75.00'),
            description='Test expense'
        )
        # total_amount should be amount + tax_amount
        assert expense.total_amount == Decimal('575.00')
    
    def test_expense_payment_methods(self):
        """Test all payment methods."""
        methods = [
            Expense.PaymentMethod.CASH,
            Expense.PaymentMethod.BANK,
            Expense.PaymentMethod.CHECK,
            Expense.PaymentMethod.CARD
        ]
        
        for method in methods:
            expense = Expense.objects.create(
                category=self.category,
                expense_date=self.today,
                amount=Decimal('500.00'),
                payment_method=method,
                description='Test expense'
            )
            assert expense.payment_method == method
    
    def test_expense_approval(self, admin_user):
        """Test expense approval."""
        expense = Expense.objects.create(
            category=self.category,
            expense_date=self.today,
            amount=Decimal('500.00'),
            description='Test expense',
            approved_by=admin_user,
            is_approved=True
        )
        assert expense.approved_by == admin_user
        assert expense.is_approved is True
    
    def test_expense_optional_fields(self):
        """Test expense optional fields."""
        expense = Expense.objects.create(
            category=self.category,
            expense_date=self.today,
            amount=Decimal('500.00'),
            description='Test expense',
            payee='ABC Company',
            reference='REF123'
        )
        assert expense.payee == 'ABC Company'
        assert expense.reference == 'REF123'


@pytest.mark.django_db
class TestExpenseCategoryModel:
    """Test suite for ExpenseCategory model."""
    
    def test_create_expense_category(self):
        """Test creating an expense category."""
        category = ExpenseCategory.objects.create(
            name='Office Supplies',
            description='Office supplies and stationery'
        )
        assert category.name == 'Office Supplies'
        assert category.description == 'Office supplies and stationery'
    
    def test_expense_category_string_representation(self):
        """Test expense category string representation."""
        category = ExpenseCategory.objects.create(name='Office Supplies')
        assert str(category) == 'Office Supplies'
    
    def test_expense_category_hierarchy(self):
        """Test expense category parent-child relationship."""
        parent = ExpenseCategory.objects.create(name='Operating Expenses')
        child = ExpenseCategory.objects.create(
            name='Office Supplies',
            parent=parent
        )
        assert child.parent == parent
        assert child in parent.children.all()
