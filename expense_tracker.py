import hashlib
import json
import os
import re
from collections import Counter

from common import parse_expense_date, get_key_for_value, adjust_month_end_dates
from logger import logger
from notion_py.helpers.notion_common import get_db_pages, create_page, delete_page, update_page_with_relation
from notion_py.helpers.notion_payload import generate_create_page_payload, generate_payload
from notion_py.notion_globals import expense_tracker_db_id, last_4_months_expense_filter, date_descending_sort, \
    last_4_months_months_expense_filter, months_expenses_tracker_db_id, current_month_year_filter, \
    current_months_expense_filter
from variables import ACCOUNT_NUMBER_TO_PERSON_CARD, CHEN_CAL, ARIEL_MAX, CHEN_MAX, ARIEL_SALARY_AVG, PRICE_VAAD_BAIT, \
    PRICE_GAN_TAMAR, PRICE_TSEHARON_NOYA, HAFKADA_GEMEL_CHILDREN, PRICE_MASHKANTA

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
    REMAINING_AMOUNT = 'Remaining Amount'
    SUB_CATEGORY = 'SubCategory'


STATUS_DICT = {
    'completed': 'Completed'
}

MODIFIED_NAMES = {
    "ועד בית": [{ExpenseField.NAME: "העברה מהחשבון", ExpenseField.CHARGED_AMOUNT: PRICE_VAAD_BAIT}],
    "גן תמר": [
        {ExpenseField.NAME: "משיכת שיק", ExpenseField.CHARGED_AMOUNT: PRICE_GAN_TAMAR, "math_operation": "approx(5%)"}],
    "משכנתא": [
        {ExpenseField.NAME: "לאומי", ExpenseField.CHARGED_AMOUNT: PRICE_MASHKANTA, "math_operation": "approx(10%)"}],
    "צהרון נויה": [{ExpenseField.NAME: "משיכת שיק", ExpenseField.CHARGED_AMOUNT: PRICE_TSEHARON_NOYA,
                    "math_operation": "approx(5%)"}],
    'הפקדות קופ"ג ילדים': [{ExpenseField.NAME: "הפקדות קופ", ExpenseField.CHARGED_AMOUNT: HAFKADA_GEMEL_CHILDREN}],
    'משכורת אריאל': [
        {ExpenseField.NAME: "משכורת", ExpenseField.CHARGED_AMOUNT: ARIEL_SALARY_AVG, "math_operation": "approx(10%)"}],
    'חשמל': [{ExpenseField.NAME: "אלקטרה פאוור"}],
    'משכורת חן': [{ExpenseField.NAME: "ספוטניק"}],
    'BOOM': [{ExpenseField.NAME: "MOOOB"}],
    'ביטוח רכב': [{ExpenseField.NAME: "9 ביטוח"}],
    'ביטוח בריאות ילדים': [{ExpenseField.NAME: "הפניקס ביטוח"}],
    'חיוב כרטיס אשראי': [{ExpenseField.NAME: "כרטיסי אשראי", "dynamic_operation": 'get_credit_card_name'},
                         {ExpenseField.NAME: "הרשאה כאל", "dynamic_operation": 'get_credit_card_name'},
                         {ExpenseField.NAME: "מקס איט", "dynamic_operation": 'get_credit_card_name'}],
}

ENGLISH_CATEGORY = {
    "Insurance & Monthly Fees 🔄": ["גן", "צהרון", "ביטוח", "לאומי", "ועד", "הפקדות", "מים", "מי חדרה", "חשמל", "סלולר",
                                   "סלקום", "פרטנר", "עיריית", "פזגז", "פז גז", "משכנתא"],
    "Food 🍽️": ["מזון", "צריכה", "משקאות", "מסעדות", "קפה", "מסעדה", "ברים", "סופרמרקט", "שופרסל", "רמי לוי", "מעדניה",
                "מקדונלדס", "ארומה", "מסעדה", "רמי לוי", "nespresso"],
    "Banking & Finance 💳": ["העברת", "כספים", "פיננסים", "שק", "שיק", "העברה", "ביט", "קצבת", "הלוואה", "השקעות",
                            "BIT", "paybox", "כספומט"],
    "Shopping 🛒": ["AMAZON", "עלי אקספרס", "איביי", "אמזון", "GOOGLE", "ALIEXPRESS", "KSP", "PAYPAL", "AMZN",
                   "google", "NOTION", "אייבורי", "shein", "lastpass", "marketplace", "לבידו",
                   "ביגוד", "אופנה", "הלבשה", "נעליים", "אקססוריז", "זארה", "קניון", "טרמינל", "פנאי",
                   "טרמינל", "ללין"],
    "Transportation & Auto 🚗": ["תחבורה", "רכבים", "מוסדות", "דלק", "רכבת", "אוטובוס", "מונית", "סונול", 'סד"ש',
                                'פנגו', 'yellow', 'דור אלון', 'מוטורס', 'מוטורוס', 'צמיג', 'סדש גלבוע'],
    "Home & Living 🏠": ["עיצוב", "הבית", "ציוד", "ריהוט", "תחזוקה", "שיפוצים", "מועצה דתית", "פנים", "דואר", "MOOOB",
                        "BOOM"],
    "Vacation 🍹": ["חופשה", "air", "trip"],
    "Health & Wellness 🏥": ["טיפוח", "יופי", "רפואה", "פארם", "בריאות", "קופת חולים", "תרופות", "טיפולים", "קרוספיט",
                            "פיט", "מרפקה"],
    "Education & Learning 📚": ["חינוך", "קורסים", "לימודים", "ספרים", "הכשרה", "סטימצקי", "לאבלאפ"],
    "Children & Family 👨‍👩‍👧‍👦": ["ילדים", "טיק", "צעצועים", "בייבי", "משפחה", "פארק"],
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

EXPENSES_TO_ADJUST_DATE = ["משכנתא", "משכורת אריאל"]


class MonthlyExpenses:
    def __init__(self, month, year, month_date_start, month_date_end):
        self.month = month
        self.year = year
        self.month_date_start = month_date_start
        self.month_date_end = month_date_end
        self.expenses = []
        self.incomes = []


    def add_expense(self, expense):
        self.expenses.append(expense)

    def get_expenses(self):
        return self.expenses

    def add_income(self, income):
        self.incomes.append(income)

    def get_incomes(self):
        return self.incomes

    def __str__(self):
        return f"MonthlyExpenses(month={self.month}, expenses={self.expenses})"

    def __repr__(self):
        return f"MonthlyExpenses(month={self.month}, expenses={self.expenses})"


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
                 remaining_amount=0,
                 page_id=None,
                 sub_category=""):
        self.expense_type = expense_type
        self.date = date
        self.processed_date = processed_date
        self.original_amount = original_amount
        self.original_currency = CURRENCY_SYMBOLS.get(original_currency, original_currency)
        self.charged_amount = charged_amount
        self.charged_currency = charged_currency
        self.expense_name = description
        self.memo = memo
        self.category = category
        self.status = STATUS_DICT.get(status, status)
        self.account_number = account_number
        self.remaining_amount = remaining_amount
        self.person_card = self.get_person_card()
        self.page_id = page_id
        self.sub_category = sub_category

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
        if self.remaining_amount > 0:
            payload_dict["Remaining Amount"] = self.remaining_amount

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
            ExpenseField.PAGE_ID: 'page_id'
        }

        # Get the attribute name from the mapping and return its value
        attr_name = field_map.get(field)
        if attr_name and hasattr(self, attr_name):
            return getattr(self, attr_name)
        else:
            raise ValueError(f"Field '{field}' is not a valid ExpenseField or is not set in the instance.")

    def __str__(self):
        currency = self.original_currency.split(' ')[-1]
        amount = f'amount={self.charged_amount} {currency}'
        if self.remaining_amount != 0:
            amount = f'{amount} -> remaining_amount={self.remaining_amount} {currency}'
        return (f"Expense (name='{self.expense_name}', {amount}, "
                f"date={self.date}, category={self.category}, person_card='{self.person_card}')")

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
        string_to_hash = f"{self.date}{self.original_amount}{self.charged_amount}{self.person_card}"
        return hashlib.md5(string_to_hash.encode()).hexdigest()

    def equals(self, other_expense):
        # if "מילואים" in other_expense.expense_name and "מילואים" in self.expense_name:
        # if "דמי כרטיס" in other_expense.expense_name and "דמי כרטיס" in self.expense_name:
        # if "משכנתא" in other_expense.expense_name and "משכנתא" in self.expense_name \
        #         and self.date == '2024-09-01' and other_expense.date == '2024-09-01':
        #     print("Ariel")
        if not isinstance(other_expense, Expense):
            return False
        return self.hash_code() == other_expense.hash_code()


class ExpenseManager:
    def __init__(self):
        self.expense_json = []
        self.monthly_expenses = []
        self.expenses_objects_to_create = []
        self.existing_expenses_objects = []

    def load_data_from_json(self):
        if os.path.exists(CASPION_FILE_PATH):
            with open(CASPION_FILE_PATH, 'r') as f:
                json_file = json.load(f)
                logger.info(f"Successfully loaded JSON file of size {len(json_file)} from {CASPION_FILE_PATH}")
                return json_file
        return {}

    def create_expense_objects_from_json(self):
        expenses_list = []
        if self.expense_json:
            for expense in self.expense_json:
                expense_name = get_name(expense['description'], abs(expense['chargedAmount']))
                category = get_category_name(expense_name, expense.get('category', ''),
                                             expense['chargedAmount'])
                expense_type = EXPENSE_TYPES.get(expense['type'], expense['type'])
                original_amount = abs(expense['originalAmount'])
                charged_currency = CURRENCY_SYMBOLS.get(expense.get('chargedCurrency', 'ILS'))

                remaining_credit_dict = get_remaining_credit(expense.get('memo', ''), original_amount, expense_type)
                updated_memo = parse_payment_string(remaining_credit_dict, expense.get('memo', ''), charged_currency)
                remaining_amount = remaining_credit_dict.get('remaining_amount', 0) if remaining_credit_dict.get('remaining_amount', 0) > 0 else 0

                date = parse_expense_date(expense['date'])
                processed_date = parse_expense_date(expense['processedDate'])
                if expense_name in EXPENSES_TO_ADJUST_DATE:
                    date = adjust_month_end_dates(date)
                    processed_date = adjust_month_end_dates(processed_date)

                try:
                    mapped_data = {
                        'expense_type': expense_type,
                        'date': date,
                        'processed_date': processed_date,
                        'original_amount': original_amount,
                        'original_currency': expense['originalCurrency'],
                        'charged_amount': abs(expense['chargedAmount']),
                        'charged_currency': charged_currency,
                        'description': expense_name,
                        'category': category,
                        'memo': updated_memo,
                        'status': expense['status'],
                        'account_number': expense['accountNumber'],
                        'remaining_amount': remaining_amount,
                    }

                    # Create an instance of Expense
                    expense = Expense(**mapped_data)
                    expenses_list.append(expense)
                except Exception as e:
                    logger.error(f"Error creating Expense object {json.loads(expense)}: {e}")
                    continue
        expenses_list.sort(key=lambda x: x.date, reverse=True)
        logger.debug(f"Successfully created {len(expenses_list)} Expense objects from JSON.")
        return expenses_list

    def get_existing_by_property(self, property_name, property_value):
        # Get all expenses with a specific property value
        return [expense for expense in self.existing_expenses_objects if
                property_value in expense.get_attr(property_name)]

    def get_all_attr(
            self,
            field: str,
            value=None,
            expense_list_name: str = "expenses_objects_to_create"):
        """
        Get either all attribute values and their counts for a field,
        or all expenses that match a specific field value.

        Args:
            field (str): The field to check
            value (Any, optional): If provided, returns expenses matching this value
            expense_list_name (str, optional): Name of the property containing expenses list.
                                             Defaults to "expenses_objects_to_create"

        Returns:
            Union[Dict[Any, int], List[Any]]: Either a dictionary of counts or list of matching expenses

        Raises:
            ValueError: If field is empty or invalid
            AttributeError: If expenses don't have the specified field
            AttributeError: If the specified expense_list_name doesn't exist
        """
        if not field:
            raise ValueError("Field parameter cannot be empty")

        try:
            # Get the expense list dynamically using getattr
            if not hasattr(self, expense_list_name):
                raise AttributeError(f"Property '{expense_list_name}' not found")

            expenses = getattr(self, expense_list_name)

            if value is not None:
                # Return all expenses where field matches value
                matching_expenses = []
                for expense in expenses:
                    try:
                        if value in expense.get_attr(field):
                            matching_expenses.append(expense)
                    except AttributeError:
                        continue  # Skip expenses that don't have this field

                return matching_expenses
            else:
                # Get all valid attribute values
                attr_values = []
                for expense in expenses:
                    try:
                        attr_value = expense.get_attr(field)
                        if attr_value is not None:  # Skip None values
                            attr_values.append(attr_value)
                    except AttributeError:
                        continue

                # Count and sort values
                count_dict = Counter(attr_values)
                sorted_count = dict(sorted(
                    count_dict.items(),
                    key=lambda item: (item[1], str(item[0])),
                    reverse=True
                ))

                return sorted_count

        except Exception as e:
            logger.error(f"Error processing field '{field}' from '{expense_list_name}': {str(e)}")
            raise

    def add_all_expenses_to_notion(self, check_before_adding=True):
        self.expense_json = self.load_data_from_json()
        self.expenses_objects_to_create = self.create_expense_objects_from_json()
        self.existing_expenses_objects = self.get_expenses_from_notion()

        # epok_to_add = self.get_all_attr(ExpenseField.NAME, value="אפוק")
        # existing_epok = self.get_all_attr(ExpenseField.NAME, value="אפוק", expense_list_name="existing_expenses_objects")

        if check_before_adding:
            expenses_to_add = self.get_notion_that_can_be_added_not_present_in_notion()
        else:
            expenses_to_add = self.expenses_objects_to_create

        if not expenses_to_add:
            logger.info("No new expenses to add to Notion.")
            return

        expenses_to_add_len = len(expenses_to_add)
        logger.info(f"{expenses_to_add_len} Expense{'s' if expenses_to_add_len >1 else ''} can be added to Notion.")
        for i, expense in enumerate(expenses_to_add):
            expense.add_to_notion(index=i, total=expenses_to_add_len)

    """
    This function is currently not used as there is a limitation of 100 relations that can be added into a single page 
    in notion
    """
    def update_current_month_expenses(self):
        monthly_expenses = []
        monthly_saving = []
        monthly_incomes = []
        self.get_current_month_expenses_from_notion()
        for expense in self.existing_expenses_objects:
            if "income" in expense.category.lower():
                monthly_incomes.append(expense)
            elif "saving" in expense.sub_category.lower():
                monthly_saving.append(expense)
            else:
                monthly_expenses.append(expense)

        monthly_expenses_id = [expense.page_id for expense in monthly_expenses]

        update_page_with_relation(months_expenses_tracker_db_id, monthly_expenses_id, 'Expenses')

    def create_empty_monthly_expenses(self, properties):
        month = properties['Month']['title'][0]['plain_text']
        year = properties['Year']['rich_text'][0]['plain_text']
        month_date_start = properties['Date']['date']['start']
        month_date_end = properties['Date']['date']['end']
        return MonthlyExpenses(month, year, month_date_start, month_date_end)

    def get_current_month_expenses_from_notion(self):
        self.existing_expenses_objects = self.get_expenses_from_notion(current_months_expense_filter)
        self.monthly_expenses = self.get_monthly_expenses_from_notion(current_month_year_filter)

    def get_monthly_expenses_from_notion(self, filter_by=None):
        monthly_expenses_from_notion = []
        if filter_by is None:
            payload = generate_payload(last_4_months_months_expense_filter, date_descending_sort)
        else:
            payload = generate_payload(filter_by, date_descending_sort)
        months_expenses_notion_pages = get_db_pages(months_expenses_tracker_db_id, payload)

        if not self.existing_expenses_objects:
            self.existing_expenses_objects = self.get_all_expenses_from_notion()

        for months_expenses_notion_page in months_expenses_notion_pages:
            monthly_expenses = self.create_empty_monthly_expenses(months_expenses_notion_page['properties'])

            for expense_page_id in months_expenses_notion_page['properties']['Expenses']['relation']:
                expense_object = self.get_existing_by_property(ExpenseField.PAGE_ID, expense_page_id['id'])
                if not expense_object:
                    logger.error(f"Could not find expense object with page_id {expense_page_id['id']}")
                    continue
                monthly_expenses.add_expense(expense_object[0])

            for income_page_id in months_expenses_notion_page['properties']['Income']['relation']:
                income_object = self.get_existing_by_property(ExpenseField.PAGE_ID, income_page_id['id'])
                if not income_object:
                    logger.error(f"Could not find income object with page_id {income_page_id['id']}")
                    continue
                monthly_expenses.add_income(income_object[0])

            monthly_expenses_from_notion.append(monthly_expenses)

        return monthly_expenses_from_notion

    def get_all_expenses_from_notion(self):
        return self.get_expenses_from_notion(filter_by={})

    def get_expenses_from_notion(self, filter_by=None):
        expenses_objects_from_notion = []
        if filter_by is None:
            payload = generate_payload(last_4_months_expense_filter, date_descending_sort)
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
            remaining_amount = properties[ExpenseField.REMAINING_AMOUNT]['number'] if \
                properties[ExpenseField.REMAINING_AMOUNT]['number'] else 0

            description = properties[ExpenseField.NAME]['title'][0]['plain_text'] if properties[ExpenseField.NAME][
                'title'] else ""
            memo = (properties[ExpenseField.MEMO]['rich_text'][0]['plain_text']
                    if properties[ExpenseField.MEMO]['rich_text'] and properties[ExpenseField.MEMO]['rich_text']
                    else "")

            sub_category = properties[ExpenseField.SUB_CATEGORY]['formula']['string'] if \
                properties[ExpenseField.SUB_CATEGORY]['formula'] else ""

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
                sub_category=sub_category
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

    def add_relation_to_months(self):
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
                            logger.error(
                                f"Error calling dynamic_operation function {dynamic_operation} for {description}.")
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
                    if "אלקטרה" in description:
                        print("")

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
        if price >= 3000:
            account_number = ARIEL_MAX
        else:
            account_number = CHEN_MAX

    name = f"{name} - {ACCOUNT_NUMBER_TO_PERSON_CARD.get(account_number, description)}"
    return name


def get_remaining_credit(memo, price, credit):
    if credit != EXPENSE_TYPES['installments']:
        return {}

    # Use regex to extract the payment number and total payments
    pattern1 = r"תשלום (\d+) מתוך (\d+)"
    pattern2 = r"(\d+) מתוך (\d+) - סכום העסקה"

    match1 = re.search(pattern1, memo)
    match2 = re.search(pattern2, memo)

    if match1:
        payment_number = int(match1.group(1))
        total_payments = int(match1.group(2))
    elif match2:
        payment_number = int(match2.group(1))
        total_payments = int(match2.group(2))
    else:
        return {}

    if payment_number == total_payments:
        return {"remaining_amount": 0, "payment_number": payment_number, "total_payments": total_payments}
    else:
        remaining_amount = price * (total_payments - payment_number) / total_payments
        return {"remaining_amount": remaining_amount, "payment_number": payment_number, "total_payments": total_payments}


def parse_payment_string(remaining_amount_dict, memo, currency):
    if not remaining_amount_dict:
        return memo

    if remaining_amount_dict["remaining_amount"] == 0:
        return f"תשלום אחרון {remaining_amount_dict['payment_number']}/{remaining_amount_dict['total_payments']}"
    else:
        currency_sign = currency.split(" ")[-1]
        return f"תשלום {remaining_amount_dict['payment_number']}/{remaining_amount_dict['total_payments']}, " \
               f"נשאר לשלם: {currency_sign} {round(remaining_amount_dict['remaining_amount'])}"


# parse_payment_str = parse_payment_string("תשלום 1 מתוך 3", "Credit", 1000)
# print("Ariel")

# expense_manager = ExpenseManager()
# expense_manager.add_all_expenses_to_notion(check_before_adding=True)

# expense_manager.remove_duplicates()

# expense_manager = ExpenseManager()
# expense_manager.update_current_month_expenses()
