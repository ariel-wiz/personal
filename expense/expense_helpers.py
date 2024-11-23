"""
Helper functions for expense processing.
"""

import re
from typing import Dict, Optional
from logger import logger
from expense.expense_constants import MODIFIED_NAMES,ENGLISH_CATEGORY, DEFAULT_CATEGORY
from expense.expense_models import ExpenseField
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
