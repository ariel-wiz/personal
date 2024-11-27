"""
Helper functions for expense processing.
"""
import json
import os
import re
from collections import defaultdict
from datetime import datetime, timedelta, date
from typing import Dict, Optional, List, Tuple, DefaultDict

from dateutil.relativedelta import relativedelta

from logger import logger
from expense.expense_constants import MODIFIED_NAMES, ENGLISH_CATEGORY, DEFAULT_CATEGORY, ENGLISH_SUB_CATEGORIES, \
    CASPION_FILE_PATH
from expense.expense_models import ExpenseField
from notion_py.helpers.notion_common import generate_icon_url
from notion_py.notion_globals import IconType, IconColor, NotionPropertyType
from variables import CHEN_CAL, ARIEL_MAX, CHEN_MAX, ACCOUNT_NUMBER_TO_PERSON_CARD


def get_remaining_credit(memo: str, price: float, credit: str) -> Dict:
    """Calculate remaining credit for installment payments"""
    if credit != 'Credit':
        return {}

    patterns = [
        r"תשלום (\d+) מתוך (\d+)",
        r"(\d+) מתוך (\d+) - סכום העסקה"
    ]

    for pattern in patterns:
        match = re.search(pattern, memo)
        if match:
            payment_number = int(match.group(1))
            total_payments = int(match.group(2))

            if payment_number == total_payments:
                return {
                    "remaining_amount": 0,
                    "payment_number": payment_number,
                    "total_payments": total_payments
                }

            remaining_amount = price * (total_payments - payment_number) / total_payments
            return {
                "remaining_amount": remaining_amount,
                "payment_number": payment_number,
                "total_payments": total_payments
            }

    return {}


def parse_payment_string(remaining_amount_dict: Dict, memo: str, currency: str) -> str:
    """Format payment string with remaining amount info"""
    if not remaining_amount_dict:
        return memo

    if remaining_amount_dict["remaining_amount"] == 0:
        return f"תשלום אחרון {remaining_amount_dict['payment_number']}/{remaining_amount_dict['total_payments']}"

    currency_sign = currency.split(" ")[-1]
    return (f"תשלום {remaining_amount_dict['payment_number']}/{remaining_amount_dict['total_payments']}, "
            f"נשאר לשלם: {currency_sign} {round(remaining_amount_dict['remaining_amount'])}")


def get_credit_card_name(name: str, description: str, price: float) -> str:
    """Determine credit card name based on transaction details"""
    if "הרשאה כאל" in description:
        account_number = CHEN_CAL
    elif "אשראי" in description:
        account_number = description.split(" ")[0]
    else:
        account_number = ARIEL_MAX if price >= 3000 else CHEN_MAX

    return f"{name} - {ACCOUNT_NUMBER_TO_PERSON_CARD.get(account_number, description)}"


def get_name(description: str, price: float) -> str:
    """
    Get standardized name for expense based on description and price.

    Args:
        description: Original expense description
        price: Amount of the expense

    Returns:
        Standardized expense name
    """
    try:
        for name, name_dicts in MODIFIED_NAMES.items():
            for name_dict in name_dicts:
                if name_dict[ExpenseField.NAME] in description:
                    operation = name_dict.get("math_operation")
                    dynamic_operation = name_dict.get("dynamic_operation")

                    if dynamic_operation and isinstance(dynamic_operation, str):
                        try:
                            name_modifier_function = globals().get(dynamic_operation)
                            if name_modifier_function:
                                return name_modifier_function(name, description, price)
                        except (AttributeError, TypeError) as e:
                            logger.error(f"Error in dynamic operation for {description}: {e}")
                            continue

                    if ExpenseField.CHARGED_AMOUNT in name_dict:
                        try:
                            expected_amount = float(name_dict[ExpenseField.CHARGED_AMOUNT])

                            if operation and "approx" in operation:
                                try:
                                    percentage = int(operation.split("(")[1].strip('%)'))
                                    lower_bound = expected_amount * (1 - percentage / 100)
                                    upper_bound = expected_amount * (1 + percentage / 100)

                                    if lower_bound <= abs(price) <= upper_bound:
                                        return name
                                except (ValueError, TypeError) as e:
                                    logger.error(f"Error calculating bounds for {description}: {e}")
                                    continue

                            # Exact match check
                            if abs(expected_amount - abs(price)) < 0.01:  # Using small epsilon for float comparison
                                return name

                        except (ValueError, TypeError) as e:
                            logger.error(f"Error handling amount for {description}: {e}")
                            continue

                    # If no amount comparison needed, return the name
                    if ExpenseField.CHARGED_AMOUNT not in name_dict:
                        return name

        # Clean up description if no matches found
        for not_desired_word in ['בע"מ', 'בעמ']:
            description = description.replace(not_desired_word, '')
        return description.strip()

    except Exception as e:
        logger.error(f"Unexpected error in get_name for {description}: {e}")
        return description.strip()


def get_category_name(description: str, he_category: str, price: float) -> str:
    """Determine category based on description and price"""
    # Income category for positive amounts
    if price > 0:
        return 'Income 🏦'

    # Check words against category keywords
    for items_to_check in [description, he_category]:
        for item_to_check_word in items_to_check.split(' '):
            for category_en, category_list in ENGLISH_CATEGORY.items():
                for category_word in category_list:
                    if category_word.lower() in item_to_check_word.lower():
                        return category_en

    return DEFAULT_CATEGORY


def remove_emojis(text: str) -> str:
    """Remove emojis and other special characters from text"""
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F700-\U0001F77F"  # alchemical symbols
        "\U0001F780-\U0001F7FF"  # geometric shapes extended
        "\U0001F800-\U0001F8FF"  # supplemental arrows-c
        "\U0001F900-\U0001F9FF"  # supplemental symbols and pictographs
        "\U0001FA00-\U0001FA6F"  # chess symbols
        "\U0001FA70-\U0001FAFF"  # symbols and pictographs extended-a
        "\U00002702-\U000027B0"  # dingbats
        "\U000024C2-\U0001F251"  # enclosed characters
        "]+"
    )

    # Remove emojis
    text_no_emojis = emoji_pattern.sub('', text)
    # Remove zero-width joiners
    text_cleaned = re.sub(r'[\u200d]', '', text_no_emojis)
    return text_cleaned.strip()


def determine_target_category(expense) -> str:
    """Determine whether to use category or subcategory for an expense"""
    sub_category = remove_emojis(expense.sub_category).strip().lower()
    category = remove_emojis(expense.category).strip().lower()
    if sub_category and sub_category in [remove_emojis(cat.lower()) for cat in ENGLISH_SUB_CATEGORIES]:
        return sub_category
    return category


def group_expenses_by_category_or_subcategory(expenses: list) -> dict:
    """Group expenses by their target category or subcategory"""
    grouped_expenses = {}

    for expense in expenses:
        target_category = determine_target_category(expense)
        if target_category not in grouped_expenses:
            grouped_expenses[target_category] = []

        grouped_expenses[target_category].append(expense)

    return grouped_expenses


def calculate_category_sums(expenses) -> DefaultDict[str, float]:
    """Calculates sums for each expense category"""
    excluded_categories = ["income", "credit card", "saving"]
    category_sums = defaultdict(float)

    for expense in expenses:
        target_category = determine_target_category(expense)
        if target_category.lower() not in excluded_categories:
            category_sums[target_category] += expense.charged_amount

    return category_sums


def get_category_definitions() -> List[Dict]:
    """Returns list of category definitions with icons"""
    return [
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
        {"Expenses": generate_icon_url(IconType.ARROW_RIGHT_LINE, IconColor.GRAY)},
        {"Income": generate_icon_url(IconType.LIBRARY, IconColor.BLUE)}
    ]


def get_date_info(target_date: datetime) -> Dict:
    """Gets formatted date information for page creation"""
    first_day, last_day = calculate_month_boundaries(target_date)

    return {
        'month_name': target_date.strftime("%B"),
        'year': str(target_date.year),
        'month_formatted': target_date.strftime("%m/%y"),
        'first_day': first_day,
        'last_day': last_day,
        'target_date': target_date
    }


def calculate_month_boundaries(target_date: datetime) -> Tuple[date, date]:
    """Calculates first and last day of the month"""
    first_day = target_date.replace(day=1).date()

    if first_day.month == 12:
        last_day = first_day.replace(year=first_day.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        next_month = first_day.replace(month=first_day.month + 1)
        last_day = (next_month - timedelta(days=1))

    return first_day, last_day


def generate_target_dates(months_back: int) -> List[datetime]:
    """Generates list of target dates in chronological order"""
    current_date = datetime.now()
    return [
        (current_date - relativedelta(months=i))
        for i in range(months_back - 1, -1, -1)
    ]


def prepare_page_data(category: str, icon_url: str, date_info: Dict, average: Optional[float]) -> Dict:
    """Prepares data for page creation"""
    page_data = {
        "Category": category,
        "Month": date_info['month_formatted'],
        "Date": [date_info['first_day'].isoformat(), date_info['last_day'].isoformat()],
        "Icon": icon_url
    }

    if average is not None:
        page_data["4 Months Average"] = average

    return page_data


def create_category_mapping(categories: List[str]) -> Dict[str, str]:
    """Creates a mapping of cleaned category names to original names"""
    return {
        remove_emojis(rel).strip().lower(): rel
        for rel in categories
    }


def find_matching_relation(category: str, category_mapping: Dict[str, str]) -> Optional[str]:
    """Finds matching relation for a category"""
    clean_category = remove_emojis(category).strip().lower()

    for mapped_category, relation in category_mapping.items():
        if clean_category in mapped_category or mapped_category in clean_category:
            return relation
    return None


def find_matching_category_page(category: str, monthly_pages: List[Dict]) -> Optional[Dict]:
    """Finds the matching category page from monthly pages"""
    clean_category = remove_emojis(category).strip().lower()

    for page in monthly_pages:
        try:
            page_category = page['properties']['Category']['title'][0]['plain_text']
            if remove_emojis(page_category).strip().lower() == clean_category:
                return page
        except (KeyError, IndexError) as e:
            logger.error(f"Error accessing category for page: {e}")
            continue

    logger.warning(f"No matching page found for category {category}")
    return None


def calculate_date_range(current_date: datetime, months_back: int) -> Tuple[datetime, datetime]:
    """Calculates start and end dates for average calculation"""
    end_date = (current_date.replace(day=1) - timedelta(days=1)).replace(day=1)
    start_date = (end_date - relativedelta(months=months_back - 1))
    return start_date, end_date


def get_amount_from_page(category: str, page: Dict) -> Optional[float]:
    """Extracts amount from a page based on category"""
    if category == "Expenses":
        return page['properties'].get('Monthly Expenses', {}).get('number')
    return page['properties'].get('Total', {}).get('formula', {}).get('number')


def log_monthly_total(amount: float, page: Dict):
    """Logs monthly total amount"""
    month_date = datetime.strptime(page['properties']['Date']['date']['start'], '%Y-%m-%d')
    logger.debug(f"Found total {amount} for {month_date.strftime('%B %Y')}")


def calculate_average(totals: List[float], category: str, months_back: int) -> Optional[float]:
    """Calculates average from monthly totals"""
    if not totals:
        logger.info(f"No historical data found for {category}")
        return None

    actual_months = len(totals)
    average = sum(totals) / actual_months

    logger.info(f"Calculated {actual_months}-month average for {category}: {average:.2f} "
                f"(requested {months_back} months)")

    return round(average, 2)


def get_property_overrides() -> Dict:
    """Returns property type overrides for page creation"""
    return {
        "Category": NotionPropertyType.TITLE,
        "Month": NotionPropertyType.TEXT,
        "Date": NotionPropertyType.DATE
    }


def log_creation_completion(date_info: Dict, created_pages: List[Dict]):
    """Logs completion of page creation"""
    if created_pages:
        logger.info(
            f"Created new monthly expense pages for {date_info['month_name']} "
            f"{date_info['year']} with all categories and averages"
        )


def load_data_from_json() -> Dict:
    """Load expense data from JSON file"""
    if os.path.exists(CASPION_FILE_PATH):
        with open(CASPION_FILE_PATH, 'r') as f:
            json_file = json.load(f)
            logger.info(f"Successfully loaded JSON file of size {len(json_file)} from {CASPION_FILE_PATH}")
            return json_file
    return {}


def group_expenses_by_category(expenses):
    """Groups expenses by their target category"""
    expenses_by_category = defaultdict(list)
    for expense in expenses:
        target_category = determine_target_category(expense)
        expenses_by_category[target_category].append(expense)
    return expenses_by_category


def get_target_date(month_expenses) -> datetime:
    """Gets target date from expenses or returns current date"""
    return (
        datetime.strptime(month_expenses[0].date, '%Y-%m-%d')
        if month_expenses
        else datetime.now()
    )


def find_expenses_page(monthly_pages: List[Dict]) -> Optional[Dict]:
    """Finds the Expenses page from monthly pages"""
    for page in monthly_pages:
        try:
            if page['properties']['Category']['title'][0]['plain_text'].strip() == "Expenses":
                return page
        except (KeyError, IndexError) as e:
            logger.error(f"Error accessing category for page: {e}")
    return None


def extract_monthly_totals(category: str, pages: List[Dict]) -> List[float]:
    """Extracts monthly totals from historical pages"""
    monthly_totals = []

    for page in pages:
        amount = get_amount_from_page(category, page)
        if amount:
            monthly_totals.append(amount)
            log_monthly_total(amount, page)

    return monthly_totals

