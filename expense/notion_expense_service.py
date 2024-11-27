"""
Complete Notion expense service implementation with all methods.
"""

import json
import os
from collections import defaultdict
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from dateutil.relativedelta import relativedelta

from common import parse_expense_date, adjust_month_end_dates, remove_emojis
from expense.expense_constants import (
    CASPION_FILE_PATH,
    last_4_months_expense_filter,
    last_4_months_months_expense_filter, EXPENSE_TYPES, CURRENCY_SYMBOLS, EXPENSES_TO_ADJUST_DATE, DEFAULT_CATEGORY,
    current_months_expense_filter, current_month_year_filter, ENGLISH_SUB_CATEGORIES
)
from expense.expense_models import Expense, MonthlyExpense, ExpenseField
from expense.expense_helpers import (
    get_name, get_category_name, get_remaining_credit,
    parse_payment_string
)
from notion_py.helpers.notion_common import (
    get_db_pages, generate_payload, update_page_with_relation, delete_page, create_page_with_db_dict, update_page,
    generate_icon_url
)
from logger import logger
from notion_py.notion_globals import monthly_category_expense_db, NotionPropertyType, IconType, IconColor
from variables import ACCOUNT_NUMBER_TO_PERSON_CARD


class NotionUpdateError(Exception):
    """Custom exception for Notion update errors"""
    pass


def _get_expenses_for_month(monthly_expense: MonthlyExpense, expenses_list: List[Expense]) -> List[Expense]:
    """Get expenses for a specific month"""
    month_key = f"{monthly_expense.month}-{monthly_expense.year}"
    month_expenses = []

    for expense in expenses_list:
        expense_date = datetime.fromisoformat(expense.date)
        expense_month_key = expense_date.strftime("%B-%Y")
        if expense_month_key == month_key:
            month_expenses.append(expense)

    return month_expenses


class NotionExpenseService:
    def __init__(self, expense_tracker_db_id, months_expenses_tracker_db_id, monthly_category_expense_db_id):
        """Initialize the Notion expense service"""
        self.expense_tracker_db_id = expense_tracker_db_id
        self.months_expenses_tracker_db_id = months_expenses_tracker_db_id
        self.monthly_category_expense_db_id = monthly_category_expense_db_id
        self.expense_json = []
        self.monthly_expenses: List[MonthlyExpense] = []
        self.expenses_objects_to_create: List[Expense] = []
        self.existing_expenses_objects: List[Expense] = []
        self.current_month_expenses: Optional[MonthlyExpense] = None

    def load_data_from_json(self) -> Dict:
        """Load expense data from JSON file"""
        if os.path.exists(CASPION_FILE_PATH):
            with open(CASPION_FILE_PATH, 'r') as f:
                json_file = json.load(f)
                logger.info(f"Successfully loaded JSON file of size {len(json_file)} from {CASPION_FILE_PATH}")
                return json_file
        return {}

    def create_expense_objects_from_json(self) -> List[Expense]:
        """Convert JSON data to Expense objects"""
        expenses_list = []

        if not self.expense_json:
            return expenses_list

        for expense_data in self.expense_json:
            try:
                # Extract basic information
                original_name = expense_data['description']
                expense_name = get_name(expense_data['description'], abs(expense_data['chargedAmount']))
                category = get_category_name(expense_name, expense_data.get('category', ''),
                                             expense_data['chargedAmount'])

                # Process credit/installment information
                expense_type = EXPENSE_TYPES.get(expense_data['type'], expense_data['type'])
                remaining_credit_dict = get_remaining_credit(
                    expense_data.get('memo', ''),
                    abs(expense_data['originalAmount']),
                    expense_type
                )

                # Update memo with payment information
                charged_currency = CURRENCY_SYMBOLS.get(expense_data.get('chargedCurrency', 'ILS'))
                memo = parse_payment_string(
                    remaining_credit_dict,
                    expense_data.get('memo', ''),
                    charged_currency
                )

                # Get remaining amount
                remaining_amount = (remaining_credit_dict.get('remaining_amount', 0)
                                    if remaining_credit_dict.get('remaining_amount', 0) > 0 else 0)

                # Process dates with validation
                try:
                    date = parse_expense_date(expense_data['date'])
                    processed_date = parse_expense_date(expense_data['processedDate'])

                    if expense_name in EXPENSES_TO_ADJUST_DATE:
                        date = adjust_month_end_dates(date)
                        processed_date = adjust_month_end_dates(processed_date)
                except Exception as date_error:
                    logger.error(f"Error processing dates for expense {expense_name}: {str(date_error)}")
                    continue

                # Create Expense object with all required fields
                expense = Expense(
                    expense_type=expense_type,
                    date=date,
                    processed_date=processed_date,
                    original_amount=abs(expense_data['originalAmount']),
                    original_currency=expense_data['originalCurrency'],
                    charged_amount=abs(expense_data['chargedAmount']),
                    charged_currency=charged_currency,
                    description=expense_name,
                    category=category,
                    memo=memo,
                    status=expense_data['status'],
                    account_number=expense_data['accountNumber'],
                    remaining_amount=remaining_amount,
                    original_name=original_name,
                    sub_category="",  # Default empty string for sub_category
                    page_id=None  # Will be set when added to Notion
                )

                expenses_list.append(expense)
                logger.debug(f"Successfully created expense object for {expense_name}")

            except KeyError as ke:
                logger.error(f"Missing required field in expense data: {ke}")
                continue
            except Exception as e:
                logger.error(f"Error creating Expense object {expense_data.get('description', 'Unknown')}: {str(e)}")
                continue

        expenses_list.sort(key=lambda x: x.date, reverse=True)
        if len(self.expense_json) != len(expenses_list):
            logger.warning(f"{len(self.expense_json) - len(expenses_list)} expenses were not created!!\n"
                           f"Check debug logs for more information.")
        else:
            logger.info(f"Successfully created all {len(expenses_list)} Expense objects from JSON.")
        return expenses_list

    def get_expenses_from_notion(self, filter_by: Optional[Dict] = None) -> List[Expense]:
        """Get expenses from Notion database"""
        expenses_objects_from_notion = []

        if filter_by is None:
            payload = generate_payload(last_4_months_expense_filter)
        else:
            payload = generate_payload(filter_by)

        expenses_notion_pages = get_db_pages(self.expense_tracker_db_id, payload)

        for page in expenses_notion_pages:
            try:
                expense = self.create_expense_obj_from_notion(page)
                expenses_objects_from_notion.append(expense)
            except Exception as e:
                logger.error(f"Error processing Notion page: {str(e)}")
                continue

        return expenses_objects_from_notion

    def get_all_expenses_from_notion(self) -> List[Expense]:
        """Get all expenses from Notion without filtering"""
        return self.get_expenses_from_notion(filter_by={})

    def create_expense_obj_from_notion(self, notion_page: Dict) -> Expense:
        """Create Expense object from Notion page data"""
        properties = notion_page['properties']

        # Extract basic fields
        page_id = notion_page['id']
        person_card = (properties[ExpenseField.PERSON_CARD]['select']['name']
                       if properties[ExpenseField.PERSON_CARD]['select']
                       else None)

        # Find account number
        account_number = None
        for acc_num, card in ACCOUNT_NUMBER_TO_PERSON_CARD.items():
            if card == person_card:
                account_number = acc_num
                break

        # Get category
        category = (properties[ExpenseField.CATEGORY]['select']['name']
                    if ExpenseField.CATEGORY in properties
                    else DEFAULT_CATEGORY)

        # Get status
        status = (properties[ExpenseField.STATUS]['select']['name']
                  if ExpenseField.STATUS in properties
                  else None)

        # Get currencies
        original_currency = properties[ExpenseField.ORIGINAL_CURRENCY]['select']['name']
        charged_currency = properties[ExpenseField.CHARGED_CURRENCY]['select']['name']

        # Get expense type
        expense_type = (properties[ExpenseField.TYPE]['select']['name']
                        if ExpenseField.TYPE in properties and properties[ExpenseField.TYPE]['select']
                        else 'normal')

        # Get dates
        date = (properties[ExpenseField.DATE]['date']['start']
                if properties[ExpenseField.DATE]['date']
                else None)
        processed_date = (properties[ExpenseField.PROCESSED_DATE]['date']['start']
                          if properties[ExpenseField.PROCESSED_DATE]['date']
                          else None)

        # Get amounts
        original_amount = (properties[ExpenseField.ORIGINAL_AMOUNT]['number']
                           if properties[ExpenseField.ORIGINAL_AMOUNT]['number']
                           else 0)
        charged_amount = (properties[ExpenseField.CHARGED_AMOUNT]['number']
                          if properties[ExpenseField.CHARGED_AMOUNT]['number']
                          else 0)
        remaining_amount = (properties[ExpenseField.REMAINING_AMOUNT]['number']
                            if ExpenseField.REMAINING_AMOUNT in properties and
                               properties[ExpenseField.REMAINING_AMOUNT]['number']
                            else 0)

        # Get text fields
        description = (properties[ExpenseField.NAME]['title'][0]['plain_text']
                       if properties[ExpenseField.NAME]['title']
                       else "")
        memo = (properties[ExpenseField.MEMO]['rich_text'][0]['plain_text']
                if properties[ExpenseField.MEMO]['rich_text']
                else "")
        sub_category = (properties[ExpenseField.SUB_CATEGORY]['formula']['string']
                        if ExpenseField.SUB_CATEGORY in properties and
                           properties[ExpenseField.SUB_CATEGORY]['formula']
                        else "")
        original_name = (properties[ExpenseField.ORIGINAL_NAME]['rich_text'][0]['plain_text']
                         if ExpenseField.ORIGINAL_NAME in properties and
                            properties[ExpenseField.ORIGINAL_NAME]['rich_text']
                         else "")

        return Expense(
            expense_type=expense_type,
            date=date,
            processed_date=processed_date,
            original_amount=original_amount,
            original_currency=original_currency,
            charged_amount=charged_amount,
            charged_currency=charged_currency,
            description=description,
            memo=memo,
            category=category,
            status=status,
            account_number=account_number,
            remaining_amount=remaining_amount,
            page_id=page_id,
            sub_category=sub_category,
            original_name=original_name
        )

    def get_monthly_expenses_from_notion(self, filter_by: Optional[Dict] = None) -> List[MonthlyExpense]:
        """Get monthly expenses from Notion"""
        monthly_expenses_list = []

        if filter_by is None:
            payload = generate_payload(last_4_months_months_expense_filter)
        else:
            payload = generate_payload(filter_by)

        months_expenses_notion_pages = get_db_pages(self.months_expenses_tracker_db_id, payload)

        if not self.existing_expenses_objects:
            self.existing_expenses_objects = self.get_all_expenses_from_notion()

        for page in months_expenses_notion_pages:
            try:
                monthly_expense = self.create_empty_monthly_expenses_object(page)
                monthly_expense.update_existing_relations(
                    [column for column in page['properties']
                     if page['properties'][column]['type'] == 'relation']
                )

                for relation in monthly_expense.get_existing_relations():
                    for expense_ref in page['properties'][relation]['relation']:
                        expense_object = self.get_existing_expense_by_property(
                            ExpenseField.PAGE_ID,
                            expense_ref['id']
                        )
                        if expense_object:
                            monthly_expense.add_expense(expense_object[0], expense_object[0].category)

                monthly_expenses_list.append(monthly_expense)

            except Exception as e:
                logger.error(f"Error processing monthly expense page: {str(e)}")
                continue

        return monthly_expenses_list

    def get_existing_expense_by_property(self, property_name: str, property_value: str) -> List[Expense]:
        """Find expenses matching a property value"""
        return [expense for expense in self.existing_expenses_objects
                if property_value in expense.get_attr(property_name)]

    def create_empty_monthly_expenses_object(self, notion_page: Dict) -> MonthlyExpense:
        """Create empty MonthlyExpense object from Notion page"""
        return MonthlyExpense(
            id=notion_page['id'],
            month=notion_page['properties']['Month']['title'][0]['plain_text'],
            year=notion_page['properties']['Year']['rich_text'][0]['plain_text'],
            month_date_start=notion_page['properties']['Date']['date']['start'],
            month_date_end=notion_page['properties']['Date']['date']['end']
        )

    def get_notion_that_can_be_added_not_present_in_notion(self) -> List[Expense]:
        """Get expenses that can be added to Notion"""
        return [expense for expense in self.expenses_objects_to_create
                if not self.is_expense_obj_in_notion(expense)]

    def is_expense_obj_in_notion(self, expense: Expense) -> bool:
        """Check if expense exists in Notion"""
        try:
            return any(expense.equals(existing_expense)
                       for existing_expense in self.existing_expenses_objects)
        except Exception as e:
            logger.error(f"Error checking if expense is in Notion: {str(e)}")
            return False

    def add_all_expenses_to_notion(self, check_before_adding: bool = True):
        """
        Add all expenses to Notion database.

        Args:
            check_before_adding: If True, checks if expense exists before adding
        """
        try:
            logger.info("Starting to add expenses to Notion")
            # Load and process JSON data
            self.expense_json = self.load_data_from_json()
            if not self.expense_json:
                logger.info("No expense data found in JSON file")
                return

            # Create expense objects
            self.expenses_objects_to_create = self.create_expense_objects_from_json()
            if not self.expenses_objects_to_create:
                logger.info("No expense objects created from JSON")
                return

            # Get existing expenses from Notion
            self.existing_expenses_objects = self.get_expenses_from_notion()

            # Determine which expenses to add
            if check_before_adding:
                expenses_to_add = self.get_notion_that_can_be_added_not_present_in_notion()
            else:
                expenses_to_add = self.expenses_objects_to_create

            if not expenses_to_add:
                logger.info("No new expenses to add to Notion")
                return

            # Add expenses to Notion
            expenses_to_add_len = len(expenses_to_add)
            logger.info(
                f"{expenses_to_add_len} Expense{'s' if expenses_to_add_len > 1 else ''} can be added to Notion")

            for i, expense in enumerate(expenses_to_add):
                try:
                    self._add_expense_to_notion(expense, i, expenses_to_add_len)
                except Exception as e:
                    logger.error(f"Error adding expense {expense}: {str(e)}")
                    continue

            # Update monthly summaries
            self.update_current_month_expenses()
            logger.info("Successfully completed adding expenses to Notion")

        except Exception as e:
            error_msg = f"Error in add_all_expenses_to_notion: {str(e)}"
            logger.error(error_msg)
            raise NotionUpdateError(error_msg) from e

    def _add_expense_to_notion(self, expense: Expense, index: int, total: int):
        """
        Add a single expense to Notion.

        Args:
            expense: Expense object to add
            index: Current index for progress tracking
            total: Total number of expenses being added
        """
        try:
            # Create the expense payload
            payload = expense.get_payload()

            # Add to Notion
            response = create_page_with_db_dict(self.expense_tracker_db_id, payload)
            expense.page_id = response['id']  # Store the created page ID

            logger.info(f"{index + 1}/{total} - Successfully added expense {expense} to Notion")
            return response

        except Exception as e:
            raise NotionUpdateError(f"Failed to add expense to Notion: {str(e)}") from e

    def remove_duplicates(self):
        """Remove duplicate expenses from Notion"""
        try:
            unique_expenses = []
            expenses_to_remove = []

            # Get all existing expenses
            all_notion_expenses = self.get_all_expenses_from_notion()

            # Find duplicates
            for expense in all_notion_expenses:
                for unique_expense in unique_expenses:
                    if expense.equals(unique_expense):
                        expenses_to_remove.append(expense)
                unique_expenses.append(expense)

            # Get unique page IDs to remove
            expense_with_unique_page_ids = set([expense.page_id for expense in expenses_to_remove])

            if not expense_with_unique_page_ids:
                logger.info("No duplicate expenses found")
                return

            # Remove duplicates
            logger.info(f"Found {len(expense_with_unique_page_ids)} duplicate expenses to remove")

            for i, page_id in enumerate(expense_with_unique_page_ids):
                try:
                    delete_page(page_id)
                    logger.info(
                        f"{i + 1}/{len(expense_with_unique_page_ids)} - Successfully removed duplicate expense")
                except Exception as e:
                    logger.error(f"Error removing duplicate expense {page_id}: {str(e)}")
                    continue

        except Exception as e:
            error_msg = f"Error removing duplicates: {str(e)}"
            logger.error(error_msg)
            raise NotionUpdateError(error_msg) from e

    def get_expense_summaries(self) -> Dict[str, float]:
        """
        Get summary statistics for current month's expenses.

        Returns:
            Dict containing summary statistics
        """
        if not self.current_month_expenses:
            return {}

        summaries = {
            'total_expenses': 0,
            'categories': {},
            'currencies': {},
            'max_expense': 0,
            'max_expense_name': '',
            'expense_count': 0
        }

        try:
            for category, expenses in self.current_month_expenses.category_expenses_dict.items():
                category_total = 0
                for expense in expenses:
                    amount = expense.charged_amount
                    summaries['total_expenses'] += amount
                    category_total += amount

                    # Track by currency
                    currency = expense.charged_currency
                    if currency not in summaries['currencies']:
                        summaries['currencies'][currency] = 0
                    summaries['currencies'][currency] += amount

                    # Track max expense
                    if amount > summaries['max_expense']:
                        summaries['max_expense'] = amount
                        summaries['max_expense_name'] = expense.name

                    summaries['expense_count'] += 1

                summaries['categories'][category] = category_total

            # Calculate averages
            if summaries['expense_count'] > 0:
                summaries['average_expense'] = (
                        summaries['total_expenses'] / summaries['expense_count']
                )

            return summaries

        except Exception as e:
            logger.error(f"Error calculating expense summaries: {str(e)}")
            return summaries

    def get_monthly_comparison(self, months_back: int = 3) -> Dict[str, Dict]:
        """
        Compare current month's expenses with previous months.

        Args:
            months_back: Number of previous months to compare

        Returns:
            Dict containing month-by-month comparison data
        """
        comparison = {}

        try:
            # Get historical monthly expenses
            historical_expenses = self.get_monthly_expenses_from_notion(
                months_back=months_back
            )

            for monthly_expense in historical_expenses:
                month_key = f"{monthly_expense.month}-{monthly_expense.year}"
                comparison[month_key] = {
                    'total': 0,
                    'categories': {},
                    'expense_count': 0
                }

                for category, expenses in monthly_expense.category_expenses_dict.items():
                    category_total = sum(exp.charged_amount for exp in expenses)
                    comparison[month_key]['categories'][category] = category_total
                    comparison[month_key]['total'] += category_total
                    comparison[month_key]['expense_count'] += len(expenses)

            return comparison

        except Exception as e:
            logger.error(f"Error generating monthly comparison: {str(e)}")
            return comparison

    def _update_monthly_expenses(self, monthly_expense: MonthlyExpense, expenses_list: List[Expense]):
        """Update expense relations for a monthly expense page"""
        monthly_expense.category_and_subcategory_expenses_dict = self._group_expenses_by_category_or_subcategory(
            expenses_list)
        category_expenses = monthly_expense.category_and_subcategory_expenses_dict
        monthly_categories = monthly_expense.get_existing_relations()
        monthly_expenses_page_id = monthly_expense.id

        # Create mapping of cleaned category names to original relation names
        # category_mapping = {
        #     remove_emojis(rel).strip().lower(): rel
        #     for rel in monthly_categories
        # }
        #
        # for category, expenses in category_expenses.items():
        #     # Clean the category name for comparison
        #     clean_category = remove_emojis(category).strip().lower()
        #
        #     # Try to find a matching relation
        #     matching_relation = None
        #     for mapped_category, relation in category_mapping.items():
        #         if clean_category in mapped_category or mapped_category in clean_category:
        #             matching_relation = relation
        #             break
        #
        #     if not matching_relation:
        #         logger.warning(f"Category {category} not found in monthly expenses. "
        #                        f"Available categories: {', '.join(monthly_categories)}")
        #         continue
        #
        #     # Update the relation
        #     category_expenses_list_page_id = [exp.page_id for exp in expenses]
        #     try:
        #         update_page_with_relation(
        #             monthly_expenses_page_id,
        #             category_expenses_list_page_id,
        #             matching_relation,
        #             name=f"monthly expense with category: {matching_relation}"
        #         )
        #         month_id = f"{monthly_expense.month}-{monthly_expense.year}"
        #         logger.info(f"Updated {matching_relation} for {month_id}")
        #     except Exception as e:
        #         logger.error(f"Error updating relation for category {category}: {str(e)}")
        #         continue
        #
        # logger.debug(
        #     f"Successfully updated monthly expenses for "
        #     f"{self.current_month_expenses.month} {self.current_month_expenses.year}"
        # )

    def _get_current_month_pages(self) -> list:
        """Get pages from the monthly database for current month/year"""
        filter_payload = {
            "and": [
                {
                    "property": "Month",
                    "rich_text": {
                        "equals": datetime.now().strftime("%B")
                    }
                },
                {
                    "property": "Year",
                    "rich_text": {
                        "equals": str(datetime.now().year)
                    }
                }
            ]
        }
        return get_db_pages(self.months_expenses_tracker_db_id, generate_payload(filter_payload))

    def _get_monthly_category_page_mapping(self, month_expenses, monthly_category_db_id: str) -> dict:
        """
        Create mapping of cleaned category names to original names and page IDs.
        Returns a dict with lowercase stripped categories as keys, and tuples of (original_name, page_id) as values.
        """
        db_pages = get_db_pages(monthly_category_db_id)
        if not db_pages:
            month_expenses.create_category_pages(monthly_category_db_id)
            db_pages = get_db_pages(monthly_category_db_id)

        mapping = {}
        for page in db_pages:
            original_name = page['properties']['Category']['title'][0]['plain_text']
            cleaned_name = remove_emojis(original_name).strip().lower()
            mapping[cleaned_name] = (original_name, page['id'])

        return mapping

    def _group_expenses_by_category_or_subcategory(self, expenses: list) -> dict:
        """Group expenses by their target category or subcategory"""
        grouped_expenses = {}

        for expense in expenses:
            target_category = self._determine_target_category(expense)
            if target_category not in grouped_expenses:
                grouped_expenses[target_category] = []

            grouped_expenses[target_category].append(expense)

        return grouped_expenses

    def _determine_target_category(self, expense) -> str:
        """Determine whether to use category or subcategory for an expense"""
        sub_category = remove_emojis(expense.sub_category).strip().lower()
        category = remove_emojis(expense.category).strip().lower()
        if sub_category and sub_category in [remove_emojis(cat.lower()) for cat in ENGLISH_SUB_CATEGORIES]:
            return sub_category
        return category

    def _update_category_page(self, category: str, expenses: list, page_id: str) -> None:
        """
        Update a single category page with its expenses.

        Args:
            category: Original category name with proper case and emojis
            expenses: List of expense objects to link
            page_id: Notion page ID for the category
        """
        expense_ids = [exp.page_id for exp in expenses if exp.page_id]

        relation_payload = {
            "properties": {
                "Expenses": {
                    "relation": [{"id": page_id} for page_id in expense_ids]
                }
            }
        }

        try:
            update_page(page_id, relation_payload)
            expense_count = len(expense_ids)
            if expense_count > 0:
                logger.info(f"Updated {expense_count} expenses for category {category}")
            else:
                logger.info(f"Cleared expenses for category {category}")
        except Exception as e:
            logger.error(f"Error updating category page {category}: {str(e)}")
            raise

    def update_monthly_pages(self, monthly_pages: List[Dict], month_expenses: List[Expense]):
        """Updates monthly category pages with their respective expense relations and averages."""
        target_date = datetime.strptime(month_expenses[0].date, '%Y-%m-%d') if month_expenses else datetime.now()

        # Group expenses by category
        expenses_by_category = defaultdict(list)
        for expense in month_expenses:
            target_category = self._determine_target_category(expense)
            expenses_by_category[target_category].append(expense)

        # Update each category page
        for category, expenses in expenses_by_category.items():
            try:
                # Find matching category page
                category_pages = []
                for page in monthly_pages:
                    try:
                        page_category = page['properties']['Category']['title'][0]['plain_text']
                        if remove_emojis(page_category).strip().lower() == remove_emojis(category).strip().lower():
                            category_pages.append(page)
                    except (KeyError, IndexError) as e:
                        logger.error(f"Error accessing category for page: {e}")
                        continue

                if not category_pages:
                    logger.warning(f"No matching page found for category {category}")
                    continue

                category_page = category_pages[0]
                expense_ids = [exp.page_id for exp in expenses if exp.page_id]

                # Check if 4-month average already exists
                existing_average = category_page['properties'].get('4 Months Average', {}).get('number')

                relation_payload = {
                    "properties": {
                        "Expenses": {
                            "relation": [{"id": page_id} for page_id in expense_ids]
                        }
                    }
                }

                # Only calculate average if it doesn't exist
                if existing_average is None:
                    average = self.get_month_average(category, target_date)
                    if average is not None:
                        relation_payload["properties"]["4 Months Average"] = {
                            "number": average
                        }

                update_page(category_page['id'], relation_payload)
                logger.info(f"Updated {len(expense_ids)} expenses for category {category}")

            except Exception as e:
                logger.error(f"Error updating category {category}: {str(e)}")
                continue

    def process_monthly_expenses(self, month_date: datetime, existing_expenses: Optional[List[Expense]] = None) -> Dict[
        str, float]:
        """
        Core function to process expenses for a specific month.
        Args:
            month_date: The date of the month to process
            existing_expenses: Optional list of pre-fetched expenses

        Returns:
            Dict containing category sums for the month
        """
        try:
            month_key = month_date.strftime("%m/%y")
            month_start = month_date.replace(day=1).date()
            logger.info(f"Processing expenses for {month_date.strftime('%B %Y')}")

            # Get or create monthly pages with averages
            filter_payload = {
                "property": "Month",
                "rich_text": {
                    "equals": month_key
                }
            }
            monthly_pages = get_db_pages(self.monthly_category_expense_db_id, generate_payload(filter_payload))

            if not monthly_pages:
                self.create_month_page_if_not_exists(month_date)
                monthly_pages = get_db_pages(self.monthly_category_expense_db_id, generate_payload(filter_payload))

            if not monthly_pages:
                raise Exception(f"Failed to create or get monthly pages for {month_date.strftime('%B %Y')}")

            # Get expenses if not provided
            if existing_expenses is None:
                existing_expenses = self.get_expenses_from_notion(
                    filter_by=current_months_expense_filter
                )

            # Filter expenses for this month
            month_expenses = [
                exp for exp in existing_expenses
                if datetime.strptime(exp.date, '%Y-%m-%d').date().replace(day=1) == month_start
            ]

            if not month_expenses:
                logger.info(f"No expenses found for {month_date.strftime('%B %Y')}")
                return {}

            # Calculate total expenses
            total_expenses = self.calculate_and_update_total_expenses(monthly_pages, month_expenses)

            # Process category pages
            self.update_monthly_pages(monthly_pages, month_expenses)

            return total_expenses

        except Exception as e:
            error_msg = f"Error processing monthly expenses for {month_date.strftime('%B %Y')}: {str(e)}"
            logger.error(error_msg)
            raise NotionUpdateError(error_msg) from e

    def get_month_average(self, category: str, current_date: datetime, months_back: int = 4) -> Optional[float]:
        """
        Gets the N-month average for a category based on historical data.

        Args:
            category: Category name to calculate average for
            current_date: Current month's date
            months_back: Number of months to look back for average calculation (default: 4)

        Returns:
            Optional[float]: The calculated average or None if no data available
        """
        try:
            end_date = (current_date.replace(day=1) - timedelta(days=1)).replace(day=1)
            start_date = (end_date - relativedelta(months=months_back - 1))

            filter_payload = {
                "and": [
                    {
                        "property": "Date",
                        "date": {
                            "on_or_after": start_date.isoformat(),
                            "on_or_before": end_date.isoformat()
                        }
                    },
                    {
                        "property": "Category",
                        "title": {
                            "equals": category
                        }
                    }
                ]
            }

            historical_pages = get_db_pages(self.monthly_category_expense_db_id, generate_payload(filter_payload))

            monthly_totals = []
            for page in historical_pages:
                amount = None
                if category == "Expenses":
                    amount = page['properties'].get('Monthly Expenses', {}).get('number')
                else:
                    amount = page['properties'].get('Total', {}).get('formula', {}).get('number')

                if amount:
                    monthly_totals.append(amount)
                    month_date = datetime.strptime(page['properties']['Date']['date']['start'], '%Y-%m-%d')
                    logger.debug(f"Found total {amount} for {month_date.strftime('%B %Y')}")

            if not monthly_totals:
                logger.info(f"No historical data found for {category}")
                return None

            actual_months = len(monthly_totals)
            average = sum(monthly_totals) / actual_months
            logger.info(f"Calculated {actual_months}-month average for {category}: {average:.2f} "
                        f"(requested {months_back} months)")
            return round(average, 2)

        except Exception as e:
            logger.error(f"Error calculating {months_back}-month average for {category}: {str(e)}")
            return None

    def calculate_and_update_total_expenses(self, monthly_pages: List[Dict], expenses: List[Expense]) -> Dict[
        str, float]:
        """
        Calculates total expenses and updates the Generated Expense field for the Expenses category.
        Returns total expenses by category.
        """
        excluded_categories = ["income", "credit card", "saving"]
        category_sums = defaultdict(float)

        # Calculate sums by category
        for expense in expenses:
            target_category = self._determine_target_category(expense)
            if target_category.lower() not in excluded_categories:
                category_sums[target_category] += expense.charged_amount

        # Find and update Expenses page
        total_amount = sum(category_sums.values())
        for page in monthly_pages:
            try:
                if page['properties']['Category']['title'][0]['plain_text'].strip() == "Expenses":
                    # Check if 4-month average already exists
                    existing_average = page['properties'].get('4 Months Average', {}).get('number')
                    current_date = datetime.strptime(page['properties']['Date']['date']['start'], '%Y-%m-%d')

                    update_payload = {
                        "properties": {
                            "Monthly Expenses": {
                                "number": total_amount
                            }
                        }
                    }

                    # Only calculate average if it doesn't exist
                    if existing_average is None:
                        average = self.get_month_average("Expenses", current_date)
                        if average is not None:
                            update_payload["properties"]["4 Months Average"] = {
                                "number": average
                            }

                    update_page(page['id'], update_payload)
                    logger.info(f"Updated Monthly Expenses with total: {total_amount:.2f}")
                    break

            except (KeyError, IndexError) as e:
                logger.error(f"Error accessing category for page: {e}")
                continue

        return dict(category_sums)

    def calculate_previous_months_average(self, target_date: datetime, category: str, months_to_average: int = 4) -> \
    Optional[float]:
        """
        Calculates average expense for a category based on previous months' totals.
        Uses the Total formula column from Notion instead of recalculating from expenses.

        Args:
            target_date: The target month's date
            category: Category to calculate average for
            months_to_average: Number of months to include in average (default 4)

        Returns:
            Optional[float]: Average monthly expense for the category, or None if no data
        """
        try:
            # Get the start of the previous month
            end_date = (target_date.replace(day=1) - timedelta(days=1)).replace(day=1)
            start_date = (end_date - relativedelta(months=months_to_average - 1))

            logger.info(
                f"Calculating average for {category} between {start_date.strftime('%B %Y')} and {end_date.strftime('%B %Y')}")

            # Get monthly pages for the date range
            filter_payload = {
                "and": [
                    {
                        "property": "Date",
                        "date": {
                            "on_or_after": start_date.isoformat()
                        }
                    },
                    {
                        "property": "Date",
                        "date": {
                            "on_or_before": end_date.isoformat()
                        }
                    },
                    {
                        "property": "Category",
                        "title": {
                            "equals": category
                        }
                    }
                ]
            }

            historical_pages = get_db_pages(self.months_expenses_tracker_db_id, generate_payload(filter_payload))
            logger.info(f"Found {len(historical_pages)} historical pages for {category}")

            if not historical_pages:
                logger.info(f"No historical data found for {category} before {target_date.strftime('%B %Y')}")
                return None

            # Collect monthly totals from the Total formula column
            monthly_sums = []
            for page in historical_pages:
                try:
                    total = page['properties'].get('Total', {}).get('formula', {}).get('number')
                    if total:
                        monthly_sums.append(total)
                        month_date = datetime.strptime(page['properties']['Date']['date']['start'], '%Y-%m-%d')
                        logger.info(f"Found total {total} for {month_date.strftime('%B %Y')}")
                except (KeyError, TypeError) as e:
                    logger.error(f"Error accessing Total for page: {e}")
                    continue

            if not monthly_sums:
                logger.info(f"No non-zero totals found for {category} in previous months")
                return None

            # Calculate average based on actual number of months with data
            actual_months = len(monthly_sums)
            average = sum(monthly_sums) / actual_months
            logger.info(f"Calculated {actual_months}-month average for {category}: {average:.2f}")
            return average

        except Exception as e:
            logger.error(f"Error calculating average for {category}: {str(e)}")
            return None

    def get_expenses_by_ids(self, expense_ids: List[str]) -> List[Expense]:
        """Helper function to get expense objects from a list of IDs"""
        expenses = []
        for expense_id in expense_ids:
            matching_expenses = [exp for exp in self.existing_expenses_objects if exp.page_id == expense_id]
            expenses.extend(matching_expenses)
        return expenses

    def calculate_category_averages(self, months_to_average: int = 4) -> Dict[str, float]:
        """
        Calculates average expenses by category for the last N months.

        Args:
            months_to_average: Number of months to include in average calculation

        Returns:
            Dict mapping category names to their average monthly expenses
        """
        try:
            current_date = datetime.now()

            # Get expenses for the period
            start_date = (current_date - relativedelta(months=months_to_average)).replace(day=1)
            filter_payload = {
                "property": "Processed Date",
                "date": {
                    "on_or_after": start_date.isoformat()
                }
            }
            historical_expenses = self.get_expenses_from_notion(filter_by=filter_payload)

            if not historical_expenses:
                logger.info("No historical expenses found for averaging")
                return {}

            # Group expenses by month and category
            monthly_category_sums = defaultdict(lambda: defaultdict(float))
            EXCLUDED_CATEGORIES = ["Income 🏦", "Credit Card 💳", "Saving 💰"]

            for expense in historical_expenses:
                expense_date = datetime.strptime(expense.date, '%Y-%m-%d')
                month_key = expense_date.strftime('%Y-%m')
                target_category = self._determine_target_category(expense)

                if target_category not in EXCLUDED_CATEGORIES:
                    monthly_category_sums[month_key][target_category] += expense.charged_amount

            # Calculate averages
            category_totals = defaultdict(list)
            for month_sums in monthly_category_sums.values():
                for category, amount in month_sums.items():
                    category_totals[category].append(amount)

            category_averages = {
                category: sum(amounts) / len(amounts)
                for category, amounts in category_totals.items()
            }

            return category_averages

        except Exception as e:
            error_msg = f"Error calculating category averages: {str(e)}"
            logger.error(error_msg)
            raise NotionUpdateError(error_msg) from e

    def update_current_month_expenses(self):
        """Updates the current month's expense relations and category pages."""
        try:
            if not self._initialize_current_month():
                return

            self.process_monthly_expenses(datetime.now(), self.existing_expenses_objects)

        except Exception as e:
            error_msg = f"Error updating current month expenses: {str(e)}"
            logger.error(error_msg)
            raise NotionUpdateError(error_msg) from e

    def _initialize_current_month(self) -> bool:
        """Initialize current month data if not already done"""
        if not self.current_month_expenses:
            self.current_month_expenses = self.get_current_month_expenses()
            if not self.current_month_expenses:
                logger.error("Failed to get or create current month expenses")
                return False

        if not self.existing_expenses_objects:
            self.existing_expenses_objects = self.get_expenses_from_notion(
                filter_by=current_months_expense_filter
            )
            if not self.existing_expenses_objects:
                logger.info("No expenses found for current month")
                return False

        return True

    def _get_current_month_expenses(self) -> list:
        """Get expenses for the current month"""
        month_expenses = _get_expenses_for_month(
            self.current_month_expenses,
            self.existing_expenses_objects
        )

        if not month_expenses:
            logger.info("No expenses found for current month")
            return []

        return month_expenses

    def check_duplicate_expense_relations(self, monthly_expense: MonthlyExpense) -> List[Dict]:
        """Check for duplicate expense relations"""
        expense_locations = {}
        duplicates = []
        monthly_relations = monthly_expense.get_existing_relations()
        month_id = f"{monthly_expense.month}-{monthly_expense.year}"

        for relation_name in monthly_relations:
            expenses = monthly_expense.get_expenses(relation_name)
            if not expenses:
                continue

            for expense in expenses:
                expense_id = expense.page_id

                if expense_id in expense_locations:
                    existing_info = expense_locations[expense_id]
                    if not existing_info.get('reported', False):
                        duplicate_info = {
                            'expense': expense,
                            'columns': [existing_info['column'], relation_name],
                            'month_id': month_id
                        }
                        duplicates.append(duplicate_info)

                        logger.warning(
                            f"Duplicate expense found in {month_id}:\n"
                            f"  Expense: {expense}\n"
                            f"  Found in columns: '{existing_info['column']}' and '{relation_name}'"
                        )

                        existing_info['reported'] = True
                else:
                    expense_locations[expense_id] = {
                        'expense': expense,
                        'column': relation_name,
                        'reported': False
                    }

        if not duplicates:
            logger.info(f"No duplicate expenses found in {monthly_expense.month}-{monthly_expense.year}")

        return duplicates

    def get_current_month_expenses(self) -> MonthlyExpense:
        """
        Returns the MonthlyExpense object for the current month, creating it if necessary.

        Returns:
            MonthlyExpense: Object representing current month's expenses
        """
        # Get current month's expenses
        self.existing_expenses_objects = self.get_expenses_from_notion(
            current_months_expense_filter)

        # Get or create current month's page
        monthly_pages = self.get_monthly_expenses_from_notion(
            current_month_year_filter)

        if not monthly_pages:
            # Create new month page if it doesn't exist
            month_page = self.create_month_page_if_not_exists()
            monthly_expense = self.create_empty_monthly_expenses_object(month_page)
        else:
            monthly_expense = monthly_pages[0]

        # Cache the current month expenses
        self.current_month_expenses = monthly_expense

        return monthly_expense

    def update_historical_monthly_pages(self, months_back: int = 4):
        """Update monthly balance pages for historical expenses"""
        current_date = datetime.now()

        # Create necessary monthly pages
        for i in range(months_back):
            target_date = current_date - timedelta(days=30 * i)
            self.create_month_page_if_not_exists(target_date)

        # Get historical expenses
        self.existing_expenses_objects = self.get_expenses_from_notion(
            filter_by=last_4_months_expense_filter)

        # Get monthly pages
        self.monthly_expenses = self.get_monthly_expenses_from_notion(
            filter_by=last_4_months_months_expense_filter)

        # Update each monthly page
        for monthly_expense in self.monthly_expenses:
            month_expenses = _get_expenses_for_month(
                monthly_expense,
                self.existing_expenses_objects
            )
            if month_expenses:
                self._update_monthly_expenses(monthly_expense, month_expenses)

    def create_month_page_if_not_exists(self, target_date: Optional[datetime] = None) -> Dict:
        """Create monthly expense page with proper averages if it doesn't exist"""
        if target_date is None:
            target_date = datetime.now()

        month_name = target_date.strftime("%B")
        year = str(target_date.year)
        month_formatted = target_date.strftime("%m/%y")  # Format: MM/YY

        # Calculate first and last day of the month without time
        first_day = target_date.replace(day=1).date()
        if first_day.month == 12:
            last_day = first_day.replace(year=first_day.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            next_month = first_day.replace(month=first_day.month + 1)
            last_day = (next_month - timedelta(days=1))

        # Check if pages already exist for this month
        filter_payload = {
            "and": [
                {
                    "property": "Month",
                    "rich_text": {
                        "equals": month_formatted
                    }
                }
            ]
        }

        existing_pages = get_db_pages(self.monthly_category_expense_db_id,
                                      generate_payload(filter_payload))

        if existing_pages:
            logger.info(f"Monthly expense page for {month_name} {year} already exists")
            return existing_pages[0]

        # Define categories with their icons and calculate their averages
        categories = [
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
            {"Insurance & Monthly Fees": generate_icon_url(IconType.REPEAT, IconColor.GRAY)},
            {"Expenses": generate_icon_url(IconType.ARROW_RIGHT_LINE, IconColor.GRAY)},
            {"Income": generate_icon_url(IconType.LIBRARY, IconColor.BLUE)}
        ]

        # Create pages for each category with pre-calculated averages
        created_pages = []
        for category_dict in categories:
            try:
                category, icon_url = list(category_dict.items())[0]

                # Calculate average for the category
                average = self.get_month_average(category, target_date)

                page_data = {
                    "Category": category,
                    "Month": month_formatted,
                    "Date": [first_day.isoformat(), last_day.isoformat()],
                    "Icon": icon_url
                }

                # Add average if available
                if average is not None:
                    page_data["4 Months Average"] = average

                property_overrides = {
                    "Category": NotionPropertyType.TITLE,
                    "Month": NotionPropertyType.TEXT,
                    "Date": NotionPropertyType.DATE
                }

                response = create_page_with_db_dict(
                    self.monthly_category_expense_db_id,
                    page_data,
                    property_overrides=property_overrides
                )
                created_pages.append(response)
                logger.info(f"Created category page for {category} with average: {average}")

            except Exception as e:
                logger.error(f"Error creating category page for {category}: {str(e)}")
                continue

        logger.info(f"Created new monthly expense pages for {month_name} {year} with all categories and averages")
        return created_pages[0] if created_pages else None

    class NotionUpdateError(Exception):
        """Custom exception for Notion update errors"""
        pass

    def backfill_monthly_expenses(self, months_back: int = 4) -> Dict[str, Dict[str, float]]:
        """
        Backfills monthly expense data for past months.
        Args:
            months_back: Number of months to go back
        Returns:
            Dict mapping months to their category sums
        """
        try:
            current_date = datetime.now()
            monthly_summaries = {}

            # Get all expenses for the period
            existing_expenses = self.get_expenses_from_notion(
                filter_by=last_4_months_expense_filter
            )

            if not existing_expenses:
                logger.info("No expenses found to backfill")
                return monthly_summaries

            # Process each month in chronological order (oldest first)
            for i in range(months_back - 1, -1, -1):
                target_date = (current_date - relativedelta(months=i))
                month_key = target_date.strftime("%m/%y")

                category_sums = self.process_monthly_expenses(target_date, existing_expenses)
                if category_sums:
                    monthly_summaries[month_key] = category_sums

            logger.info("Completed backfilling monthly expenses")
            return monthly_summaries

        except Exception as e:
            error_msg = f"Error backfilling monthly expenses: {str(e)}"
            logger.error(error_msg)
            raise NotionUpdateError(error_msg) from e
