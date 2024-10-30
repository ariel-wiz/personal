import hashlib
import json
import os
from collections import Counter
from datetime import datetime

from common import parse_expense_date, get_key_for_value
from logger import logger
from notion_py.helpers.notion_common import get_db_pages, create_page, delete_page
from notion_py.helpers.notion_payload import generate_create_page_payload, generate_payload
from notion_py.notion_globals import expense_tracker_db_id, last_2_months_expense_filter, date_descending_sort
from variables import ACCOUNT_NUMBER_TO_PERSON_CARD, CHEN_CAL, ARIEL_MAX, CHEN_MAX, ARIEL_SALARY_AVG, PRICE_VAAD_BAIT, \
    PRICE_GAN_TAMAR, PRICE_TSEHARON_NOYA, HAFKADA_GEMEL_CHILDREN

# Define the path to the JSON file
CASPION_FILE_PATH = os.path.join(os.path.expanduser("~"), "Documents", "caspion", "caspion.json")
DEFAULT_CATEGORY = 'Other 🗂️'


class ExpenseField:
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


STATUS_DICT = {
    'completed': 'Completed'
}

MODIFIED_NAMES = {
    "ועד בית": [{ExpenseField.NAME: "העברה מהחשבון", ExpenseField.CHARGED_AMOUNT: PRICE_VAAD_BAIT}],
    "גן תמר": [{ExpenseField.NAME: "משיכת שיק", ExpenseField.CHARGED_AMOUNT: PRICE_GAN_TAMAR, "math_operation": "approx(5%)"}],
    "צהרון נויה": [{ExpenseField.NAME: "משיכת שיק", ExpenseField.CHARGED_AMOUNT: PRICE_TSEHARON_NOYA, "math_operation": "approx(5%)"}],
    'הפקדות קופ"ג ילדים': [{ExpenseField.NAME: "הפקדות קופ", ExpenseField.CHARGED_AMOUNT: HAFKADA_GEMEL_CHILDREN}],
    'משכורת אריאל': [
        {ExpenseField.NAME: "משכורת", ExpenseField.CHARGED_AMOUNT: ARIEL_SALARY_AVG, "math_operation": "approx(10%)"}],
    'חשמל': [{ExpenseField.NAME: "אלקטרה פאוור"}],
    'חיוב כרטיס אשראי': [{ExpenseField.NAME: "כרטיסי אשראי", "dynamic_operation": 'get_credit_card_name'},
                         {ExpenseField.NAME: "הרשאה כאל", "dynamic_operation": 'get_credit_card_name'},
                         {ExpenseField.NAME: "מקס איט", "dynamic_operation": 'get_credit_card_name'}],
}

ENGLISH_CATEGORY = {
    "Insurance & Monthly Fees 🔄": ["גן", "צהרון", "ביטוח", "לאומי", "ועד", "הפקדות", "מים", "מי", "חשמל", "סלולר",
                                   "סלקום", "פרטנר", "עיריית", "פזגז"],
    "Food 🍽️": ["מזון", "צריכה", "משקאות", "מסעדות", "קפה", "מסעדה", "ברים", "סופרמרקט", "שופרסל", "רמי לוי", "מעדניה",
                "מקדונלדס", "ארומה", "מסעדה"],
    "Banking & Finance 💳": ["העברת", "כספים", "פיננסים", "שק", "שיק", "העברה", "ביט", "קצבת", "הלוואה", "השקעות", "BIT", "paybox", "כספומט"],
    "Online Shopping 🛒": ["AMAZON", "עלי אקספרס", "איביי", "אמזון", "GOOGLE", "ALIEXPRESS", "KSP", "PAYPAL", "AMZN",
                          "google", "NOTION", "אייבורי", "shein", "lastpass", "marketplace"],
    "Fashion & Apparel 👔": ["ביגוד", "אופנה", "הלבשה", "נעליים", "אקססוריז", "זארה", "קניון", "טרמינל", "פנאי", "טרמינל"],
    "Transportation & Auto 🚗": ["תחבורה", "רכבים", "מוסדות", "דלק", "רכבת", "אוטובוס", "מונית", "סונול", 'סד"ש', 'פנגו', 'yellow', 'דור אלון', 'מוטורס', 'מוטורוס'],
    "Home & Living 🏠": ["עיצוב", "הבית", "ציוד", "ריהוט", "תחזוקה", "שיפוצים", "מועצה דתית", "פנים"],
    "Vacation 🍹": ["חופשה", "air", "trip"],
    "Health & Wellness 🏥": ["טיפוח", "יופי", "רפואה", "פארם", "בריאות", "קופת חולים", "תרופות", "טיפולים", "קרוספיט",
                            "פיט", "מרפקה"],
    "Education & Learning 📚": ["חינוך", "קורסים", "לימודים", "ספרים", "הכשרה", "סטימצקי"],
    "Children & Family 👨‍👩‍👧‍👦": ["ילדים", "טיק", "צעצועים", "בייבי", "משפחה"],
    "Income 🏦": [],
    "Other 🗂️": ["שונות"]
}

EXPENSE_TYPES = {
    'normal': 'Normal',
    'installments': 'Credit'
}

CURRENCY_SYMBOLS = {
    'ILS': 'ILS ₪',
    'USD': 'USD $',
    'EUR': 'EUR €',
    '₪': 'ILS ₪',
    '$': 'USD $',
    '€': 'EUR €'
}


class Expense:
    def __init__(self,
                 expense_type,
                 date,
                 processed_date,
                 original_amount,
                 original_currency,
                 charged_amount,
                 charged_currency,
                 description,
                 memo,
                 category,
                 status,
                 account_number,
                 page_id=None):
        self.expense_type = EXPENSE_TYPES.get(expense_type, expense_type)
        self.date = parse_expense_date(date)
        self.processed_date = parse_expense_date(processed_date)
        self.original_amount = original_amount
        self.original_currency = CURRENCY_SYMBOLS.get(original_currency, original_currency)
        self.charged_amount = charged_amount
        self.charged_currency = CURRENCY_SYMBOLS.get(charged_currency, charged_currency)
        self.expense_name = description
        self.memo = memo
        self.category = category
        self.status = STATUS_DICT.get(status, status)
        self.account_number = account_number
        self.person_card = self.get_person_card()
        self.page_id = page_id

    def get_person_card(self):
        for key, value in ACCOUNT_NUMBER_TO_PERSON_CARD.items():
            if value in self.expense_name:
                return value
        return ACCOUNT_NUMBER_TO_PERSON_CARD.get(self.account_number, self.account_number)

    def get_payload(self):
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
            ExpenseField.TYPE: self.expense_type
        }
        return generate_create_page_payload(expense_tracker_db_id, payload_dict)

    def add_to_notion(self, index=None, total=None):
        payload = self.get_payload()
        create_page(payload)
        if index is not None and total is not None:
            logger.info(f"{index + 1}/{total} - Successfully added expense {self} to Notion.")
        else:
            logger.info(f"Successfully added expense {self} to Notion.")
        return

    def delete_from_notion(self, index=None, total=None):
        delete_page(self.page_id)
        if index is not None and total is not None:
            logger.info(f"{index + 1}/{total} - Successfully added expense {self} to Notion.")
        else:
            logger.info(f"Successfully added expense {self} to Notion.")
        return

    def get_attr(self, field):
        # Map ExpenseField values to Expense attribute names
        field_map = {
            ExpenseField.NAME: 'description',
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
            ExpenseField.PAGE_ID: 'page_id'
        }

        # Get the attribute name from the mapping and return its value
        attr_name = field_map.get(field)
        if attr_name and hasattr(self, attr_name):
            return getattr(self, attr_name)
        else:
            raise ValueError(f"Field '{field}' is not a valid ExpenseField or is not set in the instance.")

    def __str__(self):
        return (f"Expense (name='{self.expense_name}', amount={self.original_amount} {self.original_currency}, "
                f"date={self.date}, person_card='{self.person_card}')")

    def __repr__(self):
        return (f"Expense(expense_type={self.expense_type}, date={self.date}, "
                f"processed_date={self.processed_date}, original_amount={self.original_amount}, "
                f"original_currency={self.original_currency}, charged_amount={self.charged_amount}, "
                f"charged_currency={self.charged_currency}, description='{self.expense_name}', "
                f"memo='{self.memo}', category='{self.category}', "
                f"status='{self.status}', account_number='{self.account_number}', "
                f"person_card='{self.person_card}', page_id='{self.page_id}')")

    def hash_code(self):
        # Create a hash code from the name, date, and original amount
        return hashlib.md5((str(self)).encode()).hexdigest()

    def equals(self, other_expense):
        if not isinstance(other_expense, Expense):
            return False
        return self.hash_code() == other_expense.hash_code()


class ExpenseManager:
    def __init__(self):
        self.expense_json = []
        self.expenses_objects_to_create = []
        self.existing_expenses_objects = []

    def load_data_from_json(self):
        if os.path.exists(CASPION_FILE_PATH):
            with open(CASPION_FILE_PATH, 'r') as f:
                json_file = json.load(f)
                logger.info(f"Successfully loaded JSON file of size {len(json_file)} from {CASPION_FILE_PATH}")
                return json_file
        return {}

    def create_expense_objects(self):
        expenses_list = []
        if self.expense_json:
            for expense in self.expense_json:
                expense_name = get_name(expense['description'], abs(expense['chargedAmount']))
                category = get_category_name(expense_name, expense.get('category', ''),
                                             expense['chargedAmount'])
                try:
                    mapped_data = {
                        'expense_type': expense['type'],
                        'date': expense['date'],
                        'processed_date': expense['processedDate'],
                        'original_amount': abs(expense['originalAmount']),
                        'original_currency': expense['originalCurrency'],
                        'charged_amount': abs(expense['chargedAmount']),
                        'charged_currency': expense.get('chargedCurrency', 'ILS'),
                        'description': expense_name,
                        'category': category,
                        'memo': expense.get('memo', ''),
                        'status': expense['status'],
                        'account_number': expense['accountNumber']
                    }

                    # Create an instance of Expense
                    expense = Expense(**mapped_data)
                    expenses_list.append(expense)
                except Exception as e:
                    logger.error(f"Error creating Expense object {json.loads(expense)}: {e}")
                    continue
        expenses_list.sort(key=lambda x: x.date, reverse=True)
        return expenses_list

    def get_existing_by_property(self, property_name, property_value):
        # Get all expenses with a specific property value
        return [expense for expense in self.existing_expenses_objects if
                property_value in expense.get_attr(property_name)]

    def get_all_attr(self, field):
        # Get all attribute values for the specified field
        attr_values = [expense.get_attr(field) for expense in self.expenses_objects_to_create]
        # Use Counter to count occurrences of each attribute value
        count_dict = Counter(attr_values)
        # Sort the dictionary by the number of entries (counts) in descending order
        sorted_count = dict(sorted(count_dict.items(), key=lambda item: item[1], reverse=True))
        return sorted_count

    def add_all_expenses_to_notion(self, check_before_adding=True):
        self.expense_json = self.load_data_from_json()
        self.expenses_objects_to_create = self.create_expense_objects()
        self.existing_expenses_objects = self.get_all_expenses_from_notion()

        if check_before_adding:
            expenses_to_add = self.get_notion_that_can_be_added_not_present_in_notion()
        else:
            expenses_to_add = self.expenses_objects_to_create

        expenses_to_add_len = len(expenses_to_add)
        for i, expense in enumerate(expenses_to_add):
            expense.add_to_notion(index=i, total=expenses_to_add_len)

    def get_all_expenses_from_notion(self):
        return self.get_expenses_from_notion(filter_by={})

    def get_expenses_from_notion(self, filter_by=None):
        expenses_objects_from_notion = []
        if filter_by is None:
            payload = generate_payload(last_2_months_expense_filter, date_descending_sort)
        else:
            payload = generate_payload(filter_by, date_descending_sort)
        expenses_notion_pages = get_db_pages(expense_tracker_db_id, payload)

        for expenses_notion_page in expenses_notion_pages:
            expense = self.create_expense_obj_from_notion(expenses_notion_page)
            expenses_objects_from_notion.append(expense)

        return expenses_objects_from_notion

    def create_expense_obj_from_notion(self, notion_page):
        """
        Creates an Expense object from Notion page data.

        Args:
            notion_page (dict): The Notion page response containing expense data

        Returns:
            Expense: An Expense object populated with the Notion data
        """
        try:
            properties = notion_page['properties']

            page_id = notion_page['id']
            # Extract person card and find corresponding account number
            person_card_name = (properties[ExpenseField.PERSON_CARD]['select']['name']
                                if properties[ExpenseField.PERSON_CARD]['select']
                                else None)

            # Find account number by reverse lookup in ACCOUNT_NUMBER_TO_PERSON_CARD
            account_number = None
            for acc_num, card in ACCOUNT_NUMBER_TO_PERSON_CARD.items():
                if card == person_card_name:
                    account_number = acc_num
                    break

            category_name = properties[ExpenseField.CATEGORY]['select']['name'] \
                if ExpenseField.CATEGORY in properties else DEFAULT_CATEGORY
            category = category_name

            status = (get_key_for_value(STATUS_DICT, properties[ExpenseField.STATUS]['select']['name'])
                      if ExpenseField.STATUS in properties
                      else properties[ExpenseField.STATUS]['select']['name'])

            # Extract currencies and map to symbols
            original_currency = (
                get_key_for_value(CURRENCY_SYMBOLS, properties[ExpenseField.ORIGINAL_CURRENCY]['select']['name'])
                if properties[ExpenseField.ORIGINAL_CURRENCY]['select']['name'] in list(CURRENCY_SYMBOLS.values())
                else properties[ExpenseField.ORIGINAL_CURRENCY]['select']['name'])
            charged_currency = (
                get_key_for_value(CURRENCY_SYMBOLS, properties[ExpenseField.CHARGED_CURRENCY]['select']['name'])
                if properties[ExpenseField.CHARGED_CURRENCY]['select']['name'] in list(CURRENCY_SYMBOLS.values())
                else properties[ExpenseField.CHARGED_CURRENCY]['select']['name'])

            # Default to 'normal' expense type if not specified
            expense_type = (get_key_for_value(EXPENSE_TYPES, properties[ExpenseField.TYPE]['select']['name'])
                            if ExpenseField.TYPE in properties and properties[ExpenseField.TYPE]['select']
                            else None)

            # Extract other basic fields
            date = properties[ExpenseField.DATE]['date']['start'] if properties[ExpenseField.DATE][
                'date'] else None
            processed_date = (properties[ExpenseField.PROCESSED_DATE]['date']['start']
                              if properties[ExpenseField.PROCESSED_DATE]['date']
                              else None)
            original_amount = properties[ExpenseField.ORIGINAL_AMOUNT]['number'] if \
                properties[ExpenseField.ORIGINAL_AMOUNT]['number'] else 0
            charged_amount = properties[ExpenseField.CHARGED_AMOUNT]['number'] if \
                properties[ExpenseField.CHARGED_AMOUNT][
                    'number'] else 0
            description = properties[ExpenseField.NAME]['title'][0]['plain_text'] if properties[ExpenseField.NAME][
                'title'] else ""
            memo = (properties[ExpenseField.MEMO]['rich_text'][0]['plain_text']
                    if properties[ExpenseField.MEMO]['rich_text'] and properties[ExpenseField.MEMO]['rich_text']
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
                page_id=page_id
            )
        except Exception as e:
            print(f"Error creating Expense object from Notion page: {e}")

    def remove_duplicates(self):
        unique_expenses = []
        expenses_to_remove = []
        all_notion_expenses = self.get_all_expenses_from_notion()
        for expense in all_notion_expenses:
            for unique_expense in unique_expenses:
                if expense.equals(unique_expense):
                    expenses_to_remove.append(expense)
            unique_expenses.append(expense)

        expense_with_unique_page_ids = set([expense.page_id for expense in expenses_to_remove])
        if len(expense_with_unique_page_ids) > 0:
            logger.info(f"Found {len(expense_with_unique_page_ids)} duplicate expenses to remove.")
        else:
            logger.info("No duplicate expenses found.")
            return

        for i, page_id in enumerate(expense_with_unique_page_ids):
            delete_page(page_id)
            logger.info(f"{i + 1}/{len(expense_with_unique_page_ids)} - Successfully removed duplicate expense.")

    def get_notion_that_can_be_added_not_present_in_notion(self):
        expenses_not_in_notion = []
        for expense in self.expenses_objects_to_create:
            if not self.is_expense_obj_in_notion(expense):
                expenses_not_in_notion.append(expense)
        return expenses_not_in_notion

    def is_expense_obj_in_notion(self, expense):
        try:
            for existing_expense in self.existing_expenses_objects:
                if expense.equals(existing_expense):
                    logger.debug(f"The expense {expense} exists in Notion.")
                    return True
            return False
        except Exception as e:
            logger.error(f"Error checking if expense is in Notion: {e}")
            return False


def get_name(description, price):
    for name, name_dicts in MODIFIED_NAMES.items():
        for name_dict in name_dicts:
            if name_dict[ExpenseField.NAME] in description:
                operation = name_dict.get("math_operation")
                dynamic_operation = name_dict.get("dynamic_operation")

                if dynamic_operation:
                    # Check if the dynamic_operation is a function name
                    if isinstance(dynamic_operation, str):
                        try:
                            # Try to find the function by name and invoke it with "a" and "b" as arguments
                            name_modifier_function = globals().get(dynamic_operation)
                            if name_modifier_function:
                                name = name_modifier_function(name, description, price)
                                return name
                        except (AttributeError, TypeError):
                            # If the function doesn't exist or can't be called, skip this name_dict
                            logger.error(f"Error calling dynamic_operation function {dynamic_operation} for {description}.")
                            pass

                if ExpenseField.CHARGED_AMOUNT in name_dict:
                    expected_amount = name_dict[ExpenseField.CHARGED_AMOUNT]

                    if operation:
                        if "approx" in operation:
                            # Approximate range logic
                            percentage = int(operation.split("(")[1].strip('%)'))  # Get the percentage value
                            lower_bound = expected_amount * (1 - percentage / 100)
                            upper_bound = expected_amount * (1 + percentage / 100)

                            if lower_bound <= abs(price) <= upper_bound:
                                return name

                        elif operation == '>':
                            # Check if price is greater than expected amount
                            if abs(price) > expected_amount:
                                return name

                        elif operation == '<':
                            # Check if price is less than expected amount
                            if abs(price) < expected_amount:
                                return name

                    # If no CHARGED_AMOUNT or operation, return name if description matches
                    if ExpenseField.CHARGED_AMOUNT not in name_dict or \
                            (ExpenseField.CHARGED_AMOUNT in name_dict and abs(
                                int(name_dict[ExpenseField.CHARGED_AMOUNT])) == abs(
                                price)):
                        return name

    for not_desired_word in ['בע"מ', 'בעמ']:
        if not_desired_word in description:
            description = description.replace(not_desired_word, '')
    return description


def get_category_name(description, he_category, price):
    # Split the input name to check each word
    if price > 0:
        return 'Income 🏦'
    for items_to_check in [description, he_category]:
        for item_to_check_word in items_to_check.split(' '):
            for category_en, category_list in ENGLISH_CATEGORY.items():
                for category_word in category_list:
                    if category_word.lower() in item_to_check_word.lower():
                        return category_en
    return DEFAULT_CATEGORY


def get_credit_card_name(name, description, price):
    if "הרשאה כאל" in description:
        account_number = CHEN_CAL
    elif "אשראי" in description:
        account_number = description.split(" ")[0]
    else:
        if price >= 5000:
            account_number = ARIEL_MAX
        else:
            account_number = CHEN_MAX

    name = f"{name} - {ACCOUNT_NUMBER_TO_PERSON_CARD.get(account_number, description)}"
    return name


expense_manager = ExpenseManager()
expense_manager.add_all_expenses_to_notion(check_before_adding=True)
