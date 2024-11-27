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
    parse_payment_string, find_matching_category_page, find_matching_relation, create_category_mapping,
    prepare_page_data, generate_target_dates, get_category_definitions, calculate_category_sums,
    group_expenses_by_category_or_subcategory, determine_target_category, calculate_date_range, calculate_average,
    log_monthly_total, get_amount_from_page, get_date_info, get_property_overrides, log_creation_completion,
    load_data_from_json, group_expenses_by_category, get_target_date, find_expenses_page, extract_monthly_totals
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
            expenses_to_add = self._prepare_expenses_for_addition(check_before_adding)
            if not expenses_to_add:
                return

            self.add_expenses_to_notion(expenses_to_add)

            self.update_current_month_expenses()
            logger.info("Successfully completed adding expenses to Notion")

        except Exception as e:
            error_msg = f"Error in add_all_expenses_to_notion: {str(e)}"
            logger.error(error_msg)
            raise NotionUpdateError(error_msg) from e

    def _prepare_expenses_for_addition(self, check_before_adding: bool) -> List[Expense]:
        """Prepares the list of expenses to be added to Notion"""
        logger.info("Starting to add expenses to Notion")

        if not self._load_and_process_json():
            return []

        if not self._create_expense_objects():
            return []

        expenses_to_add = self._determine_expenses_to_add(check_before_adding)
        if not expenses_to_add:
            logger.info("No new expenses to add to Notion")
            return []

        expenses_count = len(expenses_to_add)
        logger.info(f"{expenses_count} Expense{'s' if expenses_count > 1 else ''} can be added to Notion")

        return expenses_to_add

    def _load_and_process_json(self) -> bool:
        """Loads and processes JSON data"""
        self.expense_json = load_data_from_json()
        if not self.expense_json:
            logger.info("No expense data found in JSON file")
            return False
        return True

    def _create_expense_objects(self) -> bool:
        """Creates expense objects from JSON data"""
        self.expenses_objects_to_create = self.create_expense_objects_from_json()
        if not self.expenses_objects_to_create:
            logger.info("No expense objects created from JSON")
            return False
        return True

    def _determine_expenses_to_add(self, check_before_adding: bool) -> List[Expense]:
        """Determines which expenses should be added to Notion"""
        self.existing_expenses_objects = self.get_expenses_from_notion()

        if check_before_adding:
            return self.get_notion_that_can_be_added_not_present_in_notion()
        return self.expenses_objects_to_create

    def add_expenses_to_notion(self, expenses: List[Expense]):
        """Processes a batch of expenses for addition to Notion"""
        for i, expense in enumerate(expenses):
            try:
                self._add_expense_to_notion(expense, i, len(expenses))
            except Exception as e:
                logger.error(f"Error adding expense {expense}: {str(e)}")
                continue

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

    def _update_monthly_expenses(self, monthly_expense: MonthlyExpense, expenses_list: List[Expense]):
        """Update expense relations for a monthly expense page"""
        try:
            grouped_expenses = self._group_and_map_expenses(monthly_expense, expenses_list)
            self._update_expense_relations(monthly_expense, grouped_expenses)
            logger.debug(
                f"Successfully updated monthly expenses for {monthly_expense.month} {monthly_expense.year}"
            )
        except Exception as e:
            logger.error(f"Failed to update monthly expenses: {str(e)}")

    def _group_and_map_expenses(self, monthly_expense: MonthlyExpense, expenses_list: List[Expense]) -> Dict[
        str, List[Expense]]:
        """Groups expenses and creates category mapping"""
        monthly_expense.category_and_subcategory_expenses_dict = group_expenses_by_category_or_subcategory(
            expenses_list)
        return self._map_expenses_to_relations(
            monthly_expense.category_and_subcategory_expenses_dict,
            monthly_expense.get_existing_relations()
        )

    def _map_expenses_to_relations(self, category_expenses: Dict[str, List[Expense]], monthly_categories: List[str]) -> \
            Dict[str, List[Expense]]:
        """Maps expense categories to their corresponding relations"""
        category_mapping = create_category_mapping(monthly_categories)
        mapped_expenses = {}

        for category, expenses in category_expenses.items():
            matching_relation = find_matching_relation(category, category_mapping)
            if matching_relation:
                mapped_expenses[matching_relation] = expenses
            else:
                logger.warning(f"Category {category} not found in monthly expenses. "
                               f"Available categories: {', '.join(monthly_categories)}")

        return mapped_expenses

    def _update_expense_relations(self, monthly_expense: MonthlyExpense, mapped_expenses: Dict[str, List[Expense]]):
        """Updates expense relations in Notion"""
        for relation, expenses in mapped_expenses.items():
            try:
                expense_ids = [exp.page_id for exp in expenses]
                self._update_single_relation(
                    monthly_expense.id,
                    expense_ids,
                    relation,
                    monthly_expense
                )
            except Exception as e:
                logger.error(f"Error updating relation for {relation}: {str(e)}")
                continue

    def _update_single_relation(self, page_id: str, expense_ids: List[str], relation: str,
                                monthly_expense: MonthlyExpense):
        """Updates a single relation in Notion"""
        update_page_with_relation(
            page_id,
            expense_ids,
            relation,
            name=f"monthly expense with category: {relation}"
        )
        month_id = f"{monthly_expense.month}-{monthly_expense.year}"
        logger.info(f"Updated {relation} for {month_id}")

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
        try:
            target_date = get_target_date(month_expenses)
            expenses_by_category = group_expenses_by_category(month_expenses)

            for category, expenses in expenses_by_category.items():
                self._update_category_page(category, expenses, monthly_pages, target_date)

        except Exception as e:
            logger.error(f"Failed to update monthly pages: {str(e)}")

    def _create_relation_payload(self, expense_ids: List[str], category: str,
                                 target_date: datetime, existing_average: Optional[float]) -> Dict:
        """Creates the payload for updating category relations"""
        payload = {
            "properties": {
                "Expenses": {
                    "relation": [{"id": page_id} for page_id in expense_ids]
                }
            }
        }

        if existing_average is None:
            average = self.get_month_average(category, target_date)
            if average is not None:
                payload["properties"]["4 Months Average"] = {
                    "number": average
                }

        return payload

    def _update_category_page(self, category: str, expenses: List[Expense],
                              monthly_pages: List[Dict], target_date: datetime):
        """Updates a single category page with expenses and averages"""
        try:
            # Find matching page
            category_page = find_matching_category_page(category, monthly_pages)
            if not category_page:
                return

            # Get expense IDs and check existing average
            expense_ids = [exp.page_id for exp in expenses if exp.page_id]
            existing_average = category_page['properties'].get('4 Months Average', {}).get('number')

            # Create and submit update
            payload = self._create_relation_payload(
                expense_ids,
                category,
                target_date,
                existing_average
            )

            update_page(category_page['id'], payload)
            logger.info(f"Updated {len(expense_ids)} expenses for category {category}")

        except Exception as e:
            logger.error(f"Error updating category {category}: {str(e)}")

    def process_monthly_expenses(self, month_date: datetime, existing_expenses: Optional[List[Expense]] = None) -> Dict[
        str, float]:
        """
        Core function to process expenses for a specific month.
        """
        try:
            monthly_pages = self._get_or_create_monthly_pages(month_date)
            month_expenses = self._get_filtered_month_expenses(month_date, existing_expenses)

            if not month_expenses:
                logger.info(f"No expenses found for {month_date.strftime('%B %Y')}")
                return {}

            total_expenses = self.calculate_and_update_total_expenses(monthly_pages, month_expenses)
            self.update_monthly_pages(monthly_pages, month_expenses)

            return total_expenses

        except Exception as e:
            error_msg = f"Error processing monthly expenses for {month_date.strftime('%B %Y')}: {str(e)}"
            logger.error(error_msg)
            raise NotionUpdateError(error_msg) from e

    def _get_or_create_monthly_pages(self, month_date: datetime) -> List[Dict]:
        """Gets or creates monthly pages for the given date"""
        month_key = month_date.strftime("%m/%y")
        monthly_pages = self._get_monthly_pages(month_key)

        if not monthly_pages:
            self.create_month_page_if_not_exists(month_date)
            monthly_pages = self._get_monthly_pages(month_key)

            if not monthly_pages:
                raise Exception(f"Failed to create or get monthly pages for {month_date.strftime('%B %Y')}")

        return monthly_pages

    def _get_monthly_pages(self, month_key: str) -> List[Dict]:
        """Retrieves monthly pages for a given month key"""
        filter_payload = {
            "property": "Month",
            "rich_text": {
                "equals": month_key
            }
        }
        return get_db_pages(self.monthly_category_expense_db_id, generate_payload(filter_payload))

    def _get_filtered_month_expenses(self, month_date: datetime, existing_expenses: Optional[List[Expense]] = None) -> \
            List[Expense]:
        """Gets and filters expenses for the specified month"""
        month_start = month_date.replace(day=1).date()
        expenses = existing_expenses or self.get_expenses_from_notion(filter_by=current_months_expense_filter)

        return [
            exp for exp in expenses
            if datetime.strptime(exp.date, '%Y-%m-%d').date().replace(day=1) == month_start
        ]

    def calculate_and_update_total_expenses(self, monthly_pages: List[Dict], expenses: List[Expense]) -> Dict[
        str, float]:
        """Calculates and updates total expenses by category"""
        category_sums = calculate_category_sums(expenses)
        total_amount = sum(category_sums.values())

        self._update_expenses_page(monthly_pages, total_amount)
        return dict(category_sums)

    def _update_expenses_page(self, monthly_pages: List[Dict], total_amount: float):
        """Updates the Expenses page with total amount and average"""
        expenses_page = find_expenses_page(monthly_pages)
        if not expenses_page:
            return

        update_payload = self._create_expenses_update_payload(expenses_page, total_amount)
        update_page(expenses_page['id'], update_payload)
        logger.info(f"Updated Monthly Expenses with total: {total_amount:.2f}")


    def _create_expenses_update_payload(self, page: Dict, total_amount: float) -> Dict:
        """Creates the payload for updating expenses"""
        existing_average = page['properties'].get('4 Months Average', {}).get('number')
        current_date = datetime.strptime(page['properties']['Date']['date']['start'], '%Y-%m-%d')

        payload = {
            "properties": {
                "Monthly Expenses": {
                    "number": total_amount
                }
            }
        }

        if existing_average is None:
            average = self.get_month_average("Expenses", current_date)
            if average is not None:
                payload["properties"]["4 Months Average"] = {
                    "number": average
                }

        return payload

    def get_month_average(self, category: str, current_date: datetime, months_back: int = 4) -> Optional[float]:
        """Gets the N-month average for a category"""
        try:
            date_range = calculate_date_range(current_date, months_back)
            historical_pages = self._get_historical_pages(category, *date_range)
            monthly_totals = extract_monthly_totals(category, historical_pages)

            return calculate_average(monthly_totals, category, months_back)

        except Exception as e:
            logger.error(f"Error calculating {months_back}-month average for {category}: {str(e)}")
            return None

    def _get_historical_pages(self, category: str, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Retrieves historical pages for average calculation"""
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
        return get_db_pages(self.monthly_category_expense_db_id, generate_payload(filter_payload))

    def get_expenses_by_ids(self, expense_ids: List[str]) -> List[Expense]:
        """Helper function to get expense objects from a list of IDs"""
        expenses = []
        for expense_id in expense_ids:
            matching_expenses = [exp for exp in self.existing_expenses_objects if exp.page_id == expense_id]
            expenses.extend(matching_expenses)
        return expenses

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
        target_date = target_date or datetime.now()
        date_info = get_date_info(target_date)

        existing_page = self._check_existing_pages(date_info)
        if existing_page:
            return existing_page

        return self._create_category_pages(date_info)

    def _check_existing_pages(self, date_info: Dict) -> Optional[Dict]:
        """Checks if pages already exist for the month"""
        filter_payload = {
            "and": [
                {
                    "property": "Month",
                    "rich_text": {
                        "equals": date_info['month_formatted']
                    }
                }
            ]
        }

        existing_pages = get_db_pages(self.monthly_category_expense_db_id,
                                      generate_payload(filter_payload))

        if existing_pages:
            logger.info(f"Monthly expense page for {date_info['month_name']} {date_info['year']} already exists")
            return existing_pages[0]

        return None

    def _create_category_pages(self, date_info: Dict) -> Optional[Dict]:
        """Creates pages for all categories with averages"""
        categories = get_category_definitions()
        created_pages = []

        for category_dict in categories:
            try:
                page = self._create_single_category_page(category_dict, date_info)
                if page:
                    created_pages.append(page)
            except Exception as e:
                category = list(category_dict.keys())[0]
                logger.error(f"Error creating category page for {category}: {str(e)}")
                continue

        log_creation_completion(date_info, created_pages)
        return created_pages[0] if created_pages else None

    def _create_single_category_page(self, category_dict: Dict, date_info: Dict) -> Optional[Dict]:
        """Creates a single category page with its average"""
        category, icon_url = list(category_dict.items())[0]

        # Calculate average for the category
        average = self.get_month_average(category, date_info['target_date'])

        page_data = prepare_page_data(category, icon_url, date_info, average)
        property_overrides = get_property_overrides()

        response = create_page_with_db_dict(
            self.monthly_category_expense_db_id,
            page_data,
            property_overrides=property_overrides
        )

        logger.info(f"Created category page for {category} with average: {average}")
        return response

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

            monthly_summaries = self._process_historical_months(existing_expenses, months_back)
            logger.info("Completed backfilling monthly expenses")
            return monthly_summaries

        except Exception as e:
            self._handle_backfill_error(e)

    def _handle_backfill_error(self, error: Exception):
        """Handles errors during backfill process"""
        error_msg = f"Error backfilling monthly expenses: {str(error)}"
        logger.error(error_msg)
        raise NotionUpdateError(error_msg) from error

    def _process_historical_months(self, expenses: List[Expense], months_back: int) -> Dict[str, Dict[str, float]]:
        """Processes expenses for each historical month"""
        monthly_summaries = {}
        target_dates = generate_target_dates(months_back)

        for target_date in target_dates:
            month_key = target_date.strftime("%m/%y")
            category_sums = self._process_historical_month(target_date, expenses)

            if category_sums:
                monthly_summaries[month_key] = category_sums

        return monthly_summaries

    def _process_historical_month(self, target_date: datetime, expenses: List[Expense]) -> Dict[str, float]:
        """Processes expenses for a single historical month"""
        try:
            return self.process_monthly_expenses(target_date, expenses)
        except Exception as e:
            logger.error(f"Error processing month {target_date.strftime('%B %Y')}: {str(e)}")
            return {}
