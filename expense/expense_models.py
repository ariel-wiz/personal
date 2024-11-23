"""
Core data models for expense tracking system.
"""

from dataclasses import dataclass
from datetime import datetime
import hashlib
from typing import Optional, List, Dict
from variables import ACCOUNT_NUMBER_TO_PERSON_CARD


class ExpenseField:
    """Constants for expense field names"""
    NAME = 'Expense'
    ACCOUNT_NUMBER = 'Account Number'
    PERSON_CARD = 'Person Card'
    STATUS = 'Status'
    PROCESSED_DATE = 'Processed Date'
    CATEGORY = 'Category'
    MEMO = 'Memo'
    CHARGED_AMOUNT = 'Charged Amount'
    ORIGINAL_AMOUNT = 'Original Amount'
    DATE = 'Date'
    CHARGED_CURRENCY = 'Charged Currency'
    ORIGINAL_CURRENCY = 'Original Currency'
    PAGE_ID = 'page_id'
    TYPE = 'Type'
    REMAINING_AMOUNT = 'Remaining Amount'
    SUB_CATEGORY = 'SubCategory'
    ORIGINAL_NAME = 'Original Name'


@dataclass
class MonthlyExpense:
    """Represents monthly expense records"""
    id: str
    month: str
    year: str
    month_date_start: str
    month_date_end: str
    category_expenses_dict: Dict[str, List['Expense']] = None
    existing_relations: List[str] = None

    def __post_init__(self):
        self.category_expenses_dict = self.category_expenses_dict or {}
        self.existing_relations = self.existing_relations or []

    def add_expense(self, expense: 'Expense', category: str):
        if category not in self.category_expenses_dict:
            self.category_expenses_dict[category] = []
        self.category_expenses_dict[category].append(expense)

    def get_expenses(self, category: Optional[str] = None) -> Optional[List['Expense']]:
        return self.category_expenses_dict.get(category) if category else None

    def get_categories(self) -> List[str]:
        return list(self.category_expenses_dict.keys())

    def update_existing_relations(self, relation_list: List[str]):
        self.existing_relations.extend(relation_list)

    def get_existing_relations(self) -> List[str]:
        return self.existing_relations


class Expense:
    """Represents individual expense records"""

    def __init__(self,
                 expense_type: str,
                 date: str,
                 processed_date: str,
                 original_amount: float,
                 original_currency: str,
                 charged_amount: float,
                 charged_currency: str,
                 description: str,
                 memo: str,
                 category: str,
                 status: str,
                 account_number: str,
                 remaining_amount: float = 0,
                 page_id: Optional[str] = None,
                 sub_category: str = "",
                 original_name: str = ""):
        self.expense_type = expense_type
        self.date = date
        self.processed_date = processed_date
        self.original_amount = original_amount
        self.original_currency = original_currency
        self.charged_amount = charged_amount
        self.charged_currency = charged_currency
        self.expense_name = description
        self.memo = memo
        self.category = category
        self.status = status
        self.account_number = account_number
        self.remaining_amount = remaining_amount
        self.person_card = self.get_person_card()
        self.page_id = page_id
        self.sub_category = sub_category
        self.original_name = original_name

    def get_attr(self, field: str) -> any:
        """Get attribute value by field name"""
        attr_map = {
            ExpenseField.NAME: 'expense_name',
            ExpenseField.ACCOUNT_NUMBER: 'account_number',
            ExpenseField.PERSON_CARD: 'person_card',
            ExpenseField.STATUS: 'status',
            ExpenseField.PROCESSED_DATE: 'processed_date',
            ExpenseField.CATEGORY: 'category',
            ExpenseField.TYPE: 'expense_type',
            ExpenseField.MEMO: 'memo',
            ExpenseField.CHARGED_AMOUNT: 'charged_amount',
            ExpenseField.ORIGINAL_AMOUNT: 'original_amount',
            ExpenseField.DATE: 'date',
            ExpenseField.CHARGED_CURRENCY: 'charged_currency',
            ExpenseField.ORIGINAL_CURRENCY: 'original_currency',
            ExpenseField.REMAINING_AMOUNT: 'remaining_amount',
            ExpenseField.PAGE_ID: 'page_id',
            ExpenseField.ORIGINAL_NAME: 'original_name'
        }

        attr_name = attr_map.get(field)
        if attr_name and hasattr(self, attr_name):
            return getattr(self, attr_name)
        raise AttributeError(f"'{self.__class__.__name__}' has no attribute mapping for '{field}'")

    def get_person_card(self) -> str:
        for key, value in ACCOUNT_NUMBER_TO_PERSON_CARD.items():
            if value in self.expense_name:
                return value
        return ACCOUNT_NUMBER_TO_PERSON_CARD.get(self.account_number, self.account_number)

    def get_payload(self) -> dict:
        """Generate Notion API payload for the expense"""
        payload_dict = {
            ExpenseField.NAME: self.expense_name,
            ExpenseField.PERSON_CARD: self.person_card,
            ExpenseField.STATUS: self.status,
            ExpenseField.PROCESSED_DATE: str(self.processed_date),
            ExpenseField.CATEGORY: self.category,
            ExpenseField.MEMO: self.memo,
            ExpenseField.CHARGED_AMOUNT: self.charged_amount,
            ExpenseField.ORIGINAL_AMOUNT: self.original_amount,
            ExpenseField.DATE: str(self.date),
            ExpenseField.CHARGED_CURRENCY: self.charged_currency,
            ExpenseField.ORIGINAL_CURRENCY: self.original_currency,
            ExpenseField.TYPE: self.expense_type,
            ExpenseField.ORIGINAL_NAME: self.original_name
        }

        if self.remaining_amount > 0:
            payload_dict[ExpenseField.REMAINING_AMOUNT] = self.remaining_amount

        return payload_dict

    def hash_code(self) -> str:
        """Generate unique hash for expense comparison"""
        string_to_hash = f"{self.date}{self.original_amount}{self.charged_amount}{self.person_card}"
        return hashlib.md5(string_to_hash.encode()).hexdigest()

    def equals(self, other: 'Expense') -> bool:
        if not isinstance(other, Expense):
            return False
        return self.hash_code() == other.hash_code()

    def __str__(self) -> str:
        currency = self.charged_currency.split(' ')[-1]
        amount = f'amount={self.charged_amount} {currency}'
        if self.remaining_amount != 0:
            amount = f'{amount} -> remaining_amount={self.remaining_amount} {currency}'
        return (f"Expense (name='{self.expense_name}', {amount}, "
                f"date={self.date}, category={self.category}, person_card='{self.person_card}')")