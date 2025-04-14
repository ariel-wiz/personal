"""
Complete Notion expense service implementation with all methods.
"""

import json
import os
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple

from dateutil.relativedelta import relativedelta

from common import parse_expense_date, adjust_month_end_dates, remove_emojis
from expense.expense_constants import (
    last_4_months_expense_filter,
    last_4_months_months_expense_filter, EXPENSE_TYPES, CURRENCY_SYMBOLS, EXPENSES_TO_ADJUST_DATE, DEFAULT_CATEGORY,
    current_months_expense_filter, BANK_SCRAPER_SCRIPT_EXEC_NAME, BANK_SCRAPER_RETRIES, BANK_SCRAPER_OUTPUT_FILE_PATH
)
from expense.expense_models import Expense, MonthlyExpense, ExpenseField
from expense.expense_helpers import (
    get_name, get_category_name, get_remaining_credit,
    parse_payment_string, find_matching_category_page, find_matching_relation, create_category_mapping,
    generate_target_dates, get_category_definitions, calculate_category_sums,
    group_expenses_by_category_or_subcategory, determine_target_category, calculate_date_range, calculate_average,
    log_monthly_total, get_amount_from_page, get_date_info, get_property_overrides, log_creation_completion,
    load_data_from_json, group_expenses_by_category, get_target_date, find_expenses_page, extract_monthly_totals,
    extract_targets_from_pages, parse_target_date
)
from notion_py.helpers.notion_common import (
    get_db_pages, generate_payload, update_page_with_relation, delete_page, create_page_with_db_dict, update_page,
    generate_icon_url
)
from logger import logger
from notion_py.notion_globals import monthly_category_expense_db, NotionPropertyType, IconType, IconColor
from notion_py.summary.summary import check_monthly_summary_exists_for_date
from variables import ACCOUNT_NUMBER_TO_PERSON_CARD, EXPENSE_IDS_TO_EXCLUDE_FROM_AVERAGE


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
    def __init__(self, expense_tracker_db_id, monthly_category_expense_db_id):
        """Initialize the Notion expense service"""
        self.expense_tracker_db_id = expense_tracker_db_id
        self.monthly_category_expense_db_id = monthly_category_expense_db_id
        self.expense_json = []
        self.expenses_objects_to_create: List[Expense] = []
        self.existing_expenses_objects: List[Expense] = []
        self.expense_ids_to_exclude_from_average = EXPENSE_IDS_TO_EXCLUDE_FROM_AVERAGE

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
            payload = generate_payload(last_4_months_months_expense_filter)
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

    def should_create_monthly_summary(self) -> bool:
        """
        Check if monthly expenses need to be updated.
        Returns True if we're in a new month and summary doesn't exist.
        """
        current_date = datetime.now()
        prev_month = current_date.replace(day=1) - timedelta(days=1)

        # If not start of month, only proceed if no summary exists
        if current_date.day > 7:
            return not check_monthly_summary_exists_for_date(prev_month)

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

    def update_averages(self, target_date: datetime, categories: Optional[List[str]] = None):
        """Single entry point for updating averages"""
        try:
            monthly_pages = self._get_or_create_monthly_pages(target_date)
            month_str = target_date.strftime('%B %Y')

            # If categories not specified, get all categories from pages
            if not categories:
                categories = [
                    page['properties']['Category']['title'][0]['plain_text']
                    for page in monthly_pages
                ]

            for category in categories:
                try:
                    page = find_matching_category_page(category, monthly_pages)
                    if not page:
                        continue

                    average = self.get_month_average(category, target_date)
                    if average is not None:
                        update_payload = {
                            "properties": {
                                "4 Months Average": {"number": average}
                            }
                        }
                        update_page(page['id'], update_payload)
                        logger.info(f"Updated {category} average to {average:.2f} for {month_str}")

                except Exception as e:
                    logger.error(f"Error updating average for {category}: {str(e)}")
                    continue

        except Exception as e:
            logger.error(f"Error updating averages: {str(e)}")
            raise

    def get_existing_expense_by_property(self, property_name: str, property_value: str) -> List[Expense]:
        """Find expenses matching a property value"""
        return [expense for expense in self.existing_expenses_objects
                if property_value in expense.get_attr(property_name)]

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
        """Add all expenses to Notion database with optimized average calculations"""
        try:
            expenses_to_add = self._prepare_expenses_for_addition(check_before_adding)
            if not expenses_to_add:
                return

            self.add_expenses_to_notion(expenses_to_add)

            # Update only current month expenses
            current_date = datetime.now()
            self.process_monthly_expenses(current_date)

            if self.needs_average_update(current_date):
                logger.info("Updating 4 months average for current month")
                self.update_averages(current_date)

            logger.info("Successfully completed adding expenses to Notion")

        except Exception as e:
            error_msg = f"Error in add_all_expenses_to_notion: {str(e)}"
            logger.error(error_msg)
            raise NotionUpdateError(error_msg) from e

    def _prepare_expenses_for_addition(self, check_before_adding: bool) -> List[Expense]:
        """Prepares the list of expenses to be added to Notion with improved error handling"""
        logger.info("Preparing expenses to add to Notion")

        try:
            # Run bank scraper with improved timeout handling
            scraper_success = self._run_bank_scraper_with_retry()
            if not scraper_success:
                logger.warning("Bank scraper did not complete successfully, but attempting to use available data")
        except Exception as e:
            logger.error(f"Error running bank scraper: {str(e)}")
            logger.warning("Continuing with existing data if available")

        # Continue with whatever data might be available
        if not self._load_and_process_json():
            logger.warning("No expense data available, skipping expense processing")
            return []

        if not self._create_expense_objects():
            logger.warning("Failed to create expense objects, skipping expense processing")
            return []

        expenses_to_add = self._determine_expenses_to_add(check_before_adding)
        if not expenses_to_add:
            logger.info("No new expenses to add to Notion")
            return []

        expenses_count = len(expenses_to_add)
        logger.info(f"{expenses_count} expense{'s' if expenses_count > 1 else ''} can be added to Notion")

        return expenses_to_add

    def _run_bank_scraper_with_retry(self):
        """
        Run bank scraper with retries based on return code.

        Return codes from _run_bank_scrapper:
        0 - Success: All accounts were successfully scraped
        1 - Partial success: Script completed but not all accounts were scraped
        2+ - Error: Script encountered an error during execution

        Returns:
            bool: True if at least some accounts were successfully scraped, False otherwise
        """
        try:
            iter_num = 0
            best_return_code = None

            while iter_num < BANK_SCRAPER_RETRIES:
                # Run the scraper and get status code
                return_code = self._run_bank_scrapper()
                logger.debug(f"Bank scraper attempt {iter_num + 1} returned code: {return_code}")

                # Track the best result we've seen (lower is better)
                if best_return_code is None or return_code < best_return_code:
                    best_return_code = return_code
                    logger.debug(f"New best return code: {best_return_code}")

                # Full success - all accounts scraped successfully
                if return_code == 0:
                    logger.info("All accounts were successfully scraped")
                    return True

                # Partial success or complete failure - retry needed
                iter_num += 1

                if iter_num < BANK_SCRAPER_RETRIES:
                    error_type = "partial success" if return_code == 1 else "complete failure"
                    logger.info(f"Retrying after {error_type}, iteration {iter_num}/{BANK_SCRAPER_RETRIES}")
                    time.sleep(iter_num * 3)  # Exponential backoff
                else:
                    logger.warning(
                        f"Max retries reached with return code {return_code}, proceeding with available data")
                    break

            # After all retries, decide what to do
            logger.debug(f"Best return code after all attempts: {best_return_code}")

            if best_return_code == 0:
                logger.info("Using complete data after retries")
                return True
            elif best_return_code == 1:
                logger.info("Using partial data after exhausting all retries")
                return True  # Return true to use partial data after max retries
            else:
                logger.warning("No usable data found after all retries")
                return False

        except Exception as e:
            logger.error(f"Bank scraper run failed: {str(e)}")
            raise

    def _run_bank_scrapper(self, print_output=True):
        """
        Run the bank scraper script and return a status code indicating the outcome.

        Return codes:
        0 - Success: All accounts were successfully scraped
        1 - Partial success: Script completed but not all accounts were scraped
        2+ - Error: Script encountered an error during execution

        Args:
            print_output (bool): Whether to print output to logs

        Returns:
            int: The status code of the scraper execution
        """
        try:
            script_path = os.path.join(os.path.dirname(__file__), BANK_SCRAPER_SCRIPT_EXEC_NAME)
            logger.info(f"Starting scraper script {script_path}...")

            # Run the script and capture output
            process = subprocess.Popen(
                [sys.executable, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Process and capture all output
            stdout, stderr = process.communicate()
            output_text = stdout + stderr

            # Try to find explicit exit code in output
            exit_code_from_output = None
            for line in stdout.splitlines() + stderr.splitlines():
                if '"level":"EXIT"' in line:
                    try:
                        # Parse the JSON object containing exit code
                        exit_data = json.loads(line)
                        if 'code' in exit_data:
                            exit_code_from_output = exit_data['code']
                            logger.debug(f"Found explicit exit code in output: {exit_code_from_output}")
                    except:
                        pass
                elif "Exiting with code:" in line:
                    try:
                        exit_code_from_output = int(line.split("Exiting with code:")[1].strip())
                        logger.debug(f"Parsed exit code from log message: {exit_code_from_output}")
                    except:
                        pass

            # Check for partial success indicators
            is_partial_success = "Only" in output_text and "accounts were successfully scraped" in output_text
            has_failures = "Failed accounts:" in output_text

            # Print output if requested
            if print_output:
                for line in stdout.splitlines():
                    logger.info(line.strip())

                for line in stderr.splitlines():
                    if line.strip():  # Only log non-empty lines
                        logger.info(line.strip())

            # Determine the correct return code
            process_code = process.returncode
            logger.debug(f"Process return code: {process_code}")
            logger.debug(f"Exit code from output: {exit_code_from_output}")
            logger.debug(f"Detected partial success: {is_partial_success}")
            logger.debug(f"Detected failures: {has_failures}")

            # Trust the explicit exit code if available, otherwise derive from output
            if exit_code_from_output is not None:
                final_code = exit_code_from_output
                logger.debug(f"Using explicit exit code: {final_code}")
            elif is_partial_success or has_failures:
                final_code = 1  # Force to partial success
                logger.debug(f"Using derived code 1 based on output content")
            else:
                final_code = process_code
                logger.debug(f"Using process return code: {final_code}")

            # Log the final decision
            if final_code == 0:
                logger.info("All accounts were successfully scraped")
            elif final_code == 1:
                logger.info("Some accounts were successfully scraped")
            else:
                logger.error(f"Scraper script exited with error code {final_code}")

            return final_code

        except Exception as e:
            logger.exception(f"Error running scraper script: {e}")
            return 2  # Return code 2 indicates an exception occurred

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

    def get_expenses_without_ids_to_remove_from_average(self, expenses: List[Expense]) -> List[Expense]:
        """Filter out expenses with IDs to remove from average"""
        return [expense for expense in expenses if str(expense.page_id).replace('-', '') not in self.expense_ids_to_exclude_from_average]

    def _update_monthly_pages(self, monthly_pages: List[Dict], month_expenses: List[Expense],
                              month_str) -> Dict[str, float]:
        """Updates monthly category pages with expenses"""
        try:
            expenses_by_category = group_expenses_by_category(month_expenses)
            category_totals = {}

            for category, expenses in expenses_by_category.items():
                try:
                    category_page = find_matching_category_page(category, monthly_pages)
                    if category_page:
                        # Filter out expenses to exclude from average
                        filtered_expenses = self.get_expenses_without_ids_to_remove_from_average(expenses)

                        if month_str == "March 2025" and "income" in category.lower():
                            print(f"Filtered expenses for {category} and month {month_str} are {filtered_expenses}")

                        expense_ids = [exp.page_id for exp in filtered_expenses if exp.page_id]
                        self._update_category_page_expenses(category, expense_ids,
                                                            category_page['id'])

                        # Calculate total using only non-excluded expenses
                        total = sum(exp.charged_amount for exp in filtered_expenses)
                        category_totals[category] = total

                        logger.debug(
                            f"{month_str} - Updated category {category} with {len(expense_ids)} expenses, total: {total}")

                except Exception as e:
                    logger.error(f"Error updating category {category}: {str(e)}")
                    continue

            return category_totals

        except Exception as e:
            logger.error(f"Failed to update monthly pages: {str(e)}")
            return {}

    def _update_category_page_expenses(self, category: str, expense_ids: List[str], page_id: str):
        """Updates only expense relations for a category page"""
        try:
            payload = {
                "properties": {
                    "Expenses": {
                        "relation": [{"id": expense_id} for expense_id in expense_ids]
                    }
                }
            }

            update_page(page_id, payload)
            expense_count = len(expense_ids)
            if expense_count > 0:
                logger.debug(f"Updated {expense_count} expenses for category {category}")
            else:
                logger.debug(f"Cleared expenses for category {category}")

        except Exception as e:
            logger.error(f"Error updating category page expenses {category}: {str(e)}")
            raise

    def recalculate_averages(self, target_date: datetime):
        """Recalculates averages for all categories for a specific month"""
        try:
            monthly_pages = self._get_or_create_monthly_pages(target_date)
            month_str = target_date.strftime('%B %Y')

            for page in monthly_pages:
                try:
                    category = page['properties']['Category']['title'][0]['plain_text']

                    # Recalculate average
                    logger.debug(f"Recalculating average for {category} ({month_str})")
                    average = self.get_month_average(category, target_date)

                    if average is not None:
                        update_payload = {
                            "properties": {
                                "4 Months Average": {"number": average}
                            }
                        }
                        update_page(page['id'], update_payload)
                        logger.info(f"Updated {category} average to {average:.2f} for {month_str}")

                except Exception as e:
                    logger.error(f"Error updating average for category {category}: {str(e)}")
                    continue

        except Exception as e:
            logger.error(f"Error recalculating averages: {str(e)}")

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

    def _update_category_page(self, category: str, expense_ids: List[str], page_id: str,
                              target_date: Optional[datetime] = None):
        """
        Updates a single category page with expenses and averages.

        Args:
            category: Category name
            expense_ids: List of expense IDs to link
            page_id: Notion page ID for the category
            target_date: Optional date for calculating averages
        """
        try:
            # Create base payload for updating relations
            payload = {
                "properties": {
                    "Expenses": {
                        "relation": [{"id": expense_id} for expense_id in expense_ids]
                    }
                }
            }

            update_page(page_id, payload)
            expense_count = len(expense_ids)
            if expense_count > 0:
                logger.info(f"Updated {expense_count} expenses for category {category.capitalize()}")
            else:
                logger.info(f"Cleared expenses for category {category}")

        except Exception as e:
            logger.error(f"Error updating category page {category}: {str(e)}")
            raise

    def process_monthly_expenses(self, target_date: datetime, existing_expenses: Optional[List[Expense]] = None) -> \
            Dict[str, float]:
        """Process monthly expenses for categories"""
        try:
            monthly_pages = self._get_or_create_monthly_pages(target_date)
            month_expenses = self._get_filtered_month_expenses(target_date, existing_expenses)
            month_str = target_date.strftime('%B %Y')

            if not month_expenses:
                logger.info(f"No expenses found for {month_str}")
                return {}

            # Update category pages and get category totals
            category_totals = self._update_monthly_pages(monthly_pages, month_expenses, month_str)

            # Calculate and update total expenses without averages
            self._update_total_expenses(monthly_pages, category_totals, month_str)

            return category_totals

        except Exception as e:
            error_msg = f"Error processing monthly expenses for {target_date.strftime('%B %Y')}: {str(e)}"
            logger.error(error_msg)
            raise NotionUpdateError(error_msg) from e

    def _update_total_expenses(self, monthly_pages: List[Dict], category_totals: Dict[str, float], month_str: str):
        """Updates total expenses without recalculating averages"""
        try:
            # Calculate total excluding certain categories
            excluded_categories = ['income', 'credit card', 'saving']
            total_amount = sum(
                amount for category, amount in category_totals.items()
                if category.lower() not in excluded_categories
            )

            # Find and update the Expenses page
            expenses_page = find_expenses_page(monthly_pages)
            if not expenses_page:
                logger.warning(f"Expenses page not found in monthly pages for {month_str}")
                return

            # Update only the total amount
            update_payload = {
                "properties": {
                    "Monthly Expenses": {
                        "number": total_amount
                    }
                }
            }
            update_page(expenses_page['id'], update_payload)

            logger.info(f"Successfully updated monthly total expenses: {total_amount:.2f} for {month_str}")

        except Exception as e:
            logger.error(f"Error updating total expenses: {str(e)} for {month_str}")

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

    def _get_filtered_month_expenses(self, target_date: datetime, existing_expenses: Optional[List[Expense]] = None) -> \
            List[Expense]:
        """Gets and filters expenses for the specified month"""
        month_start = target_date.replace(day=1).date()
        expenses = existing_expenses or self.get_expenses_from_notion(filter_by=current_months_expense_filter)

        logger.debug(f"Target date: {target_date}, Month start: {month_start}")
        logger.debug(f"Total expenses before filtering: {len(expenses)}")

        filtered_expenses = []
        for exp in expenses:
            exp_date = datetime.strptime(exp.date, '%Y-%m-%d').date()
            exp_month_start = exp_date.replace(day=1)

            if exp_month_start == month_start:
                filtered_expenses.append(exp)

        logger.debug(f"Found {len(filtered_expenses)} expenses for {target_date.strftime('%B %Y')}")
        for exp in filtered_expenses:
            logger.debug(f"Filtered expense: {exp.date} - {exp.name} - {exp.charged_amount}")

        return filtered_expenses

    def calculate_and_update_total_expenses(self, monthly_pages: List[Dict], expenses: List[Expense],
                                            month_str) -> None:
        """Updates total expenses for the month"""
        try:
            # Calculate category sums using existing helper
            category_sums = calculate_category_sums(expenses)
            total_amount = sum(category_sums.values())

            # Find and update the Expenses page
            expenses_page = find_expenses_page(monthly_pages)
            if not expenses_page:
                logger.warning(f"Expenses page not found in monthly pages for {month_str}")
                return

            # Update with total and calculate average if needed
            self._update_expenses_page(expenses_page, total_amount)

            logger.info(f"Successfully updated monthly total expenses: {total_amount:.2f} for {month_str}")

        except Exception as e:
            logger.error(f"Error updating total expenses: {str(e)} for {month_str}")

    def _update_expenses_page(self, expenses_page: Dict, total_amount: float):
        """Updates the Expenses page with total amount and average"""
        try:
            update_payload = self._create_expenses_update_payload(expenses_page, total_amount)
            update_page(expenses_page['id'], update_payload)

            logger.info(f"Updated Expenses page with total: {total_amount:.2f}")

            if "4 Months Average" in update_payload["properties"]:
                logger.info(f"Added 4-month average to Expenses page")

        except Exception as e:
            logger.error(f"Error updating Expenses page: {str(e)}")
            raise

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
        """Gets the N-month average for a category, excluding current month"""
        try:
            # For current month, use previous month as end date
            # For past months, use their own date as end date
            today = datetime.now()
            is_current_month = (current_date.year == today.year and current_date.month == today.month)

            if is_current_month:
                # If we're calculating for current month, use previous month as end date
                end_date = current_date.replace(day=1) - timedelta(days=1)  # Last day of previous month
            else:
                # For past months, use their own date
                end_date = current_date.replace(day=1) - timedelta(days=1)

            # Calculate start date
            start_date = (end_date - relativedelta(months=months_back - 1)).replace(day=1)

            logger.debug(f"Calculating {months_back}-month average for {category} from {start_date} to {end_date}")

            # Get historical pages for this category within the date range
            historical_pages = self._get_historical_pages(category, start_date, end_date)
            if not historical_pages:
                logger.info(f"No historical data found for {category} between {start_date} and {end_date}")
                return None

            monthly_totals = extract_monthly_totals(category, historical_pages, months_back)

            # Calculate the average
            if not monthly_totals:
                return None

            average = sum(monthly_totals) / len(monthly_totals)
            logger.debug(f"Found {len(monthly_totals)} months of data for {category}, average: {average:.2f}")

            return round(average, 2)

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
            # Always get fresh expenses for current month
            current_expenses = self.get_expenses_from_notion(
                filter_by=current_months_expense_filter
            )

            if not current_expenses:
                logger.info("No expenses found for current month")
                return

            # Process with fresh expenses data
            self.process_monthly_expenses(datetime.now(), current_expenses)

        except Exception as e:
            error_msg = f"Error updating current month expenses: {str(e)}"
            logger.error(error_msg)
            raise NotionUpdateError(error_msg) from e

    def _initialize_current_month(self) -> bool:
        """Initialize current month data if not already done."""
        try:
            if not self.existing_expenses_objects:
                self.existing_expenses_objects = self.get_expenses_from_notion(
                    filter_by=current_months_expense_filter
                )
                if not self.existing_expenses_objects:
                    logger.info("No expenses found for current month")
                    return True

            return True

        except Exception as e:
            logger.error(f"Error initializing current month: {str(e)}")
            return False

    def create_month_page_if_not_exists(self, target_date: Optional[datetime] = None) -> Dict:
        """Create monthly expense page with proper averages if it doesn't exist"""
        target_date = target_date or datetime.now()
        date_info = get_date_info(target_date)

        # Get tuple of (existing_page, previous_targets)
        check_result = self._check_existing_monthly_category_pages(date_info)
        existing_page, _ = check_result  # Unpack tuple but we only need existing_page here

        if existing_page:
            return existing_page

        return self._create_category_pages(date_info)

    def _check_existing_monthly_category_pages(self, date_info: Dict) -> Tuple[Optional[Dict], Dict[str, float]]:
        """
        Checks if pages already exist for the month and extracts targets from previous month.

        Returns:
            Tuple[Optional[Dict], Dict[str, float]]: Tuple containing:
                - The existing page if found, None otherwise
                - Dictionary of targets from previous month
        """
        sort = [{
            "property": "Last edited time",
            "direction": "descending"
        }]

        all_pages = get_db_pages(self.monthly_category_expense_db_id,
                                 generate_payload(sorts=sort))

        # Extract targets from previous month's pages
        targets = extract_targets_from_pages(all_pages, date_info['month_formatted'])

        # Check for existing pages for current month
        existing_pages = [
            page for page in all_pages
            if page['properties']['Month']['rich_text'][0]['plain_text'] == date_info['month_formatted']
        ]

        if existing_pages:
            logger.info(f"Monthly expense page for {date_info['month_name']} {date_info['year']} already exists")
            return existing_pages[0], targets

        return None, targets

    def _create_category_pages(self, date_info: Dict) -> Optional[Dict]:
        """Creates pages for all categories with averages and targets"""
        categories = get_category_definitions()
        created_pages = []

        # Get existing pages to check for targets
        check_result = self._check_existing_monthly_category_pages(date_info)
        existing_page, previous_targets = check_result  # Properly unpack the tuple

        if existing_page:
            return existing_page

        for category_dict in categories:
            try:
                page = self._create_single_category_page(category_dict, date_info, previous_targets)
                if page:
                    created_pages.append(page)
            except Exception as e:
                category = list(category_dict.keys())[0]
                logger.error(f"Error creating category page for {category}: {str(e)}")
                continue

        log_creation_completion(date_info, created_pages)
        return created_pages[0] if created_pages else None

    def _create_single_category_page(self, category_dict: Dict, date_info: Dict, previous_targets: Dict[str, float]) -> \
            Optional[Dict]:
        """Creates a single category page with its average and target"""
        category, icon_url = list(category_dict.items())[0]

        # Calculate average for the category
        logger.debug(f"Calculating average for {category}")
        average = self.get_month_average(category, date_info['target_date'])
        if average is not None:
            logger.info(f"Calculated {category} average: {average:.2f}")
        else:
            logger.info(f"No average available for {category}")

        # Get target from previous month if exists
        target = previous_targets.get(category)

        # Prepare page data
        page_data = {
            "Category": category,
            "Month": date_info['month_formatted'],
            "Date": [date_info['first_day'].isoformat(), date_info['last_day'].isoformat()],
            "Icon": icon_url
        }

        # Add average if exists
        if average is not None:
            page_data["4 Months Average"] = average

        # Add target if exists
        if target is not None:
            page_data["Target"] = target

        property_overrides = get_property_overrides()

        response = create_page_with_db_dict(
            self.monthly_category_expense_db_id,
            page_data,
            property_overrides=property_overrides
        )

        logger_msg = f"Created category page for {category}"
        if average is not None:
            logger_msg += f" with average: {average}"
        if target is not None:
            logger_msg += f" and target: {target}"
        logger.info(logger_msg)

        return response

    class NotionUpdateError(Exception):
        """Custom exception for Notion update errors"""
        pass

    def needs_average_update(self, target_date: datetime = None) -> bool:
        """
        Checks if any category in the target month has empty averages.

        Returns:
            bool: True if any category needs average update, False otherwise
        """
        try:
            target_date = target_date or datetime.now()
            monthly_pages = self._get_or_create_monthly_pages(target_date)

            # Check if any page has empty average
            for page in monthly_pages:
                existing_average = page['properties'].get('4 Months Average', {}).get('number')
                if existing_average is None:
                    logger.debug(f"Found missing average for {target_date.strftime('%B %Y')}")
                    return True

            logger.debug(f"All averages exist for {target_date.strftime('%B %Y')}")
            return False

        except Exception as e:
            logger.error(f"Error checking if averages need update: {str(e)}")
            return False

    def backfill_monthly_expenses(self, months_back: int = 4) -> Dict[str, Dict[str, float]]:
        """Backfills monthly expense data for past months with optimized average calculations"""
        try:
            target_dates = generate_target_dates(months_back)
            existing_expenses = self.get_expenses_from_notion(
                filter_by=last_4_months_expense_filter()
            )

            if not existing_expenses:
                return {}

            monthly_summaries = {}
            for target_date in target_dates:
                monthly_pages = self._get_or_create_monthly_pages(target_date)

                # Process expenses without averages
                category_sums = self.process_monthly_expenses(target_date, existing_expenses)
                if category_sums:
                    monthly_summaries[target_date.strftime("%m/%y")] = category_sums

                    self._update_total_expenses(monthly_pages, category_sums, target_date.strftime('%B %Y'))

            # Update averages once for all months
            for target_date in target_dates:
                self.update_averages(target_date)

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
            # Get monthly pages for this month, creating if needed
            monthly_pages = self._get_or_create_monthly_pages(target_date)
            if not monthly_pages:
                return {}

            # Get filtered expenses for this month
            month_expenses = self._get_filtered_month_expenses(target_date, expenses)

            # Even if no expenses, we should still update averages
            if not month_expenses:
                logger.info(f"No expenses found for {target_date.strftime('%B %Y')}, updating averages only")
                self._update_monthly_averages(monthly_pages, target_date)
                return {}

            # Process expenses and update pages
            return self.update_monthly_pages(monthly_pages, month_expenses, target_date.strftime('%B %Y'))

        except Exception as e:
            logger.error(f"Error processing month {target_date.strftime('%B %Y')}: {str(e)}")
            return {}

    def _update_monthly_averages(self, monthly_pages: List[Dict], target_date: datetime) -> None:
        """Updates averages for all category pages even when no expenses exist"""
        for page in monthly_pages:
            try:
                category = page['properties']['Category']['title'][0]['plain_text']

                # Recalculate and update average
                logger.debug(f"Recalculating average for {category} ({target_date.strftime('%B %Y')})")
                average = self.get_month_average(category, target_date)

                if average is not None:
                    update_payload = {
                        "properties": {
                            "4 Months Average": {"number": average}
                        }
                    }
                    update_page(page['id'], update_payload)
                    logger.info(f"Updated {category} average to {average:.2f} for {target_date.strftime('%B %Y')}")

            except Exception as e:
                logger.error(f"Error updating average for category {category}: {str(e)}")
                continue

    def update_monthly_category_expenses(self, month_year: str):
        """Update monthly category expenses for a specific month/year"""
        try:
            target_date = parse_target_date(month_year)
            if not target_date:
                return

            logger.info(f"Updating monthly categories for {target_date.strftime('%B %Y')}")

            # Use existing process_monthly_expenses function with target date
            self.process_monthly_expenses(target_date)

        except Exception as e:
            logger.error(f"Error updating monthly categories for {month_year}: {str(e)}")
