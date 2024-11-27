"""
Core data models for expense tracking system.
"""
import copy
from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
from typing import Optional, List, Dict

from expense.expense_constants import ENGLISH_CATEGORY, ENGLISH_SUB_CATEGORIES
from logger import logger
from notion_py.helpers.notion_common import _invoke_notion_api, create_page_with_db_dict, create_db, generate_icon_url
from notion_py.notion_globals import Method, NotionPropertyType, IconType, IconColor
from variables import ACCOUNT_NUMBER_TO_PERSON_CARD, Keys


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
    """
    Represents and manages monthly expense records and database structure in Notion.
    Combines expense tracking with database creation capabilities.
    """
    id: str  # Notion database/page ID
    month: str  # Month name
    year: str  # Year as string
    month_date_start: str  # ISO date string
    month_date_end: str  # ISO date string
    parent_page_id: Optional[str] = None  # Parent page ID for database creation
    expense_tracker_db_id: Optional[str] = None  # Source expense tracker database ID
    category_expenses_dict: Dict[str, List['Expense']] = None
    category_and_subcategory_expenses_dict: Dict[str, List['Expense']] = None
    existing_relations: List[str] = None

    def __post_init__(self):
        """Initialize collections if None"""
        self.category_expenses_dict = self.category_expenses_dict or {}
        self.existing_relations = self.existing_relations or []
        self.categories = list(ENGLISH_CATEGORY.keys())
        self.sub_categories = ENGLISH_SUB_CATEGORIES

    # Expense Management Methods
    def add_expense(self, expense: 'Expense', category: str) -> None:
        """Add an expense to a category"""
        if category not in self.category_expenses_dict:
            self.category_expenses_dict[category] = []
        self.category_expenses_dict[category].append(expense)

    def get_expenses(self, category: Optional[str] = None) -> Optional[List['Expense']]:
        """Get expenses for a category or None"""
        return self.category_expenses_dict.get(category) if category else None

    def get_categories(self) -> List[str]:
        """Get list of expense categories"""
        return list(self.category_expenses_dict.keys())

    def update_existing_relations(self, relation_list: List[str]) -> None:
        """Update list of existing Notion relations"""
        self.existing_relations.extend(relation_list)

    def get_existing_relations(self) -> List[str]:
        """Get list of existing Notion relations"""
        return self.existing_relations

    # Database Creation Methods
    def create_monthly_database_with_pages(self) -> Dict[str, str]:
        """Creates a new monthly expense database in Notion with category pages"""
        if not self.parent_page_id or not self.expense_tracker_db_id:
            raise ValueError("parent_page_id and expense_tracker_db_id must be set for database creation")

        try:
            # Create main database
            database_id = self.create_monthly_database()

            # Create category pages
            category_page_ids = self.create_category_pages(database_id)

            result = {
                "database_id": database_id,
                "category_page_ids": category_page_ids
            }

            logger.info("Successfully created monthly expense structure")
            return result

        except Exception as e:
            logger.error(f"Error setting up monthly expenses: {str(e)}")
            raise

    def create_monthly_database(self) -> str:
        """Creates a new monthly expense database in Notion"""
        current_date = datetime.now()
        month_formatted = current_date.strftime("%m/%y")  # Format: MM/YY
        db_title = f"{current_date.strftime('%B')}-{current_date.year}"

        # Calculate first and last day of the month
        first_day = current_date.replace(day=1)
        if first_day.month == 12:
            last_day = first_day.replace(year=first_day.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            last_day = first_day.replace(month=first_day.month + 1, day=1) - timedelta(days=1)

        # Define database properties
        db_properties = {
            "Category": {
                "type": "title",
                "title": {}
            },
            "Month": {
                "type": "rich_text",
                "rich_text": {}
            },
            "Date": {
                "type": "date",
                "date": {}
            },
            "Expenses": {
                "type": "relation",
                "relation": {
                    "database_id": self.expense_tracker_db_id,
                    "single_property": {}
                }
            },
            "Target": {
                "type": "number",
                "number": {
                    "format": "number"
                }
            }
        }

        response = create_db(
            page_id_to_create_the_db_in=self.parent_page_id,
            db_title=db_title,
            properties_payload=db_properties
        )

        return response['id']

    def create_category_pages(self, database_id: str) -> List[str]:
        """Creates pages for each expense category"""
        page_ids = []
        current_date = datetime.now()
        month_formatted = current_date.strftime("%m/%y")  # Format: MM/YY

        # Calculate first and last day of the month for the Date range
        first_day = current_date.replace(day=1)
        if first_day.month == 12:
            last_day = first_day.replace(year=first_day.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            last_day = first_day.replace(month=first_day.month + 1, day=1) - timedelta(days=1)

        all_categories = [
            {"Insurance & Monthly Fees": generate_icon_url(IconType.REPEAT, IconColor.GRAY)},
            {"Food": generate_icon_url(IconType.DINING, IconColor.BROWN)},
            {"Banking & Finance": generate_icon_url(IconType.CASH_REGISTER, IconColor.YELLOW)},
            {"Shopping": generate_icon_url(IconType.SHOPPING_CART, IconColor.PINK)},
            {"Transportation & Auto": generate_icon_url(IconType.CAR, IconColor.ORANGE)},
            {"Home & Living": generate_icon_url(IconType.HOME, IconColor.PURPLE)},
            {"Vacation": generate_icon_url(IconType.DRINK, IconColor.RED)},
            {"Health & Wellness": generate_icon_url(IconType.FIRST_AID_KIT, IconColor.RED)},
            {"Education & Learning": generate_icon_url(IconType.GRADEBOOK, IconColor.ORANGE)},
            {"Children & Family": generate_icon_url(IconType.PEOPLE, IconColor.BLUE)},
            {"Other": generate_icon_url(IconType.TABS, IconColor.GREEN)},
            {"Insurance": generate_icon_url(IconType.VERIFIED, IconColor.BROWN)},
            {"Subscriptions": generate_icon_url(IconType.HISTORY, IconColor.LIGHT_GRAY)},
            {"Saving": generate_icon_url(IconType.ATM, IconColor.YELLOW)},
            {"Credit Card": generate_icon_url(IconType.CREDIT_CARD, IconColor.ORANGE)},
            {"Income": generate_icon_url(IconType.LIBRARY, IconColor.BLUE)},
            {"Expenses": generate_icon_url(IconType.ARROW_RIGHT_LINE, IconColor.GRAY)}
        ]

        for category_dict in all_categories:
            try:
                category, icon_url = list(category_dict.items())[0]
                page_data = {
                    "Category": category,
                    "Month": month_formatted,
                    "Date": [first_day.isoformat(), last_day.isoformat()],
                    "Icon": icon_url
                }

                # Create the page with the proper property types
                property_overrides = {
                    "Category": NotionPropertyType.TITLE,
                    "Month": NotionPropertyType.TEXT
                }

                response = create_page_with_db_dict(
                    database_id,
                    page_data,
                    property_overrides=property_overrides
                )
                page_ids.append(response['id'])
                logger.info(f"Created category page for: {category}")

            except Exception as e:
                logger.error(f"Error creating category page for {category_dict}: {str(e)}")
                continue

        return page_ids

    @classmethod
    def create_new(cls, parent_page_id: str, expense_tracker_db_id: str) -> 'MonthlyExpense':
        """
        Factory method to create a new MonthlyExpense instance with database creation capabilities
        """
        current_date = datetime.now()
        return cls(
            id="",  # Will be set after database creation
            month=current_date.strftime('%B'),
            year=str(current_date.year),
            month_date_start=current_date.replace(day=1).date().isoformat(),
            month_date_end=current_date.replace(day=1, month=current_date.month + 1).date().isoformat(),
            parent_page_id=parent_page_id,
            expense_tracker_db_id=expense_tracker_db_id
        )


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
        self.name = description
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
            if value in self.name:
                return value
        return ACCOUNT_NUMBER_TO_PERSON_CARD.get(self.account_number, self.account_number)

    def get_payload(self) -> dict:
        """Generate Notion API payload for the expense"""
        payload_dict = {
            ExpenseField.NAME: self.name,
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
        return (f"Expense (name='{self.name}', {amount}, "
                f"date={self.date}, category={self.category}, person_card='{self.person_card}')")


