"""
Configuration file for expense tracking system containing constants and settings.
"""
from datetime import datetime, date, timedelta
from typing import Dict, List

from common import today
from variables import PRICE_VAAD_BAIT, PRICE_GAN_TAMAR, PRICE_MASHKANTA, HAFKADA_GEMEL_CHILDREN, PRICE_TSEHARON_NOYA, \
    ARIEL_SALARY_AVG

# Database paths and constants
CASPION_FILE_PATH = "/Users/ariel/Documents/caspion/caspion.json"

# Category constants
DEFAULT_CATEGORY = 'Other 🗂️'

# Status mappings
STATUS_DICT = {
    'completed': 'Completed'
}

# Expense type definitions
EXPENSE_TYPES = {
    'normal': 'Normal',
    'installments': 'Credit'
}

# Currency symbol mappings
CURRENCY_SYMBOLS = {
    'ILS': 'ILS ₪',
    'USD': 'USD $',
    'EUR': 'EUR €',
    '₪': 'ILS ₪',
    '$': 'USD $',
    '€': 'EUR €'
}

ENGLISH_SUB_CATEGORIES = ["Saving 💰", "Insurance 🛡️", "Subscriptions 🔄", "Credit Card 💳", "Expenses 💸"]

# Categories with their keywords
ENGLISH_CATEGORY: Dict[str, List[str]] = {
    "Insurance & Monthly Fees 🔄": [
        "גן", "צהרון", "ביטוח", "לאומי", "ועד", "הפקדות", "מים", 
        "מי חדרה", "חשמל", "סלולר", "סלקום", "פרטנר", "עיריית", 
        "פזגז", "פז גז", "משכנתא", "מי חדרה"
    ],
    "Food 🍽️": [
        "מזון", "צריכה", "משקאות", "מסעדות", "קפה", "מסעדה", "ברים",
        "סופרמרקט", "שופרסל", "רמי לוי", "מעדניה", "מקדונלדס", 
        "ארומה", "מסעדה", "רמי לוי", "nespresso", "מאפה"
    ],
    "Banking & Finance 💳": [
        "העברת", "כספים", "פיננסים", "שק", "שיק", "העברה", "ביט",
        "קצבת", "הלוואה", "השקעות", "BIT", "paybox", "כספומט"
    ],
    "Shopping 🛒": [
        "AMAZON", "עלי אקספרס", "איביי", "אמזון", "GOOGLE", "ALIEXPRESS",
        "KSP", "PAYPAL", "AMZN", "google", "NOTION", "אייבורי", "shein",
        "lastpass", "marketplace", "לבידו", "ביגוד", "אופנה", "הלבשה",
        "נעליים", "אקססוריז", "זארה", "קניון", "טרמינל", "פנאי", "ללין"
    ],
    "Transportation & Auto 🚗": [
        "תחבורה", "רכבים", "מוסדות", "דלק", "רכבת", "אוטובוס", "מונית",
        "סונול", 'סד"ש', 'פנגו', 'yellow', 'דור אלון', 'מוטורס',
        'מוטורוס', 'צמיג', 'סדש גלבוע'
    ],
    "Home & Living 🏠": [
        "עיצוב", "הבית", "ציוד", "ריהוט", "תחזוקה", "שיפוצים",
        "מועצה דתית", "פנים", "דואר", "MOOOB", "BOOM"
    ],
    "Vacation 🍹": ["חופשה", "air", "trip"],
    "Health & Wellness 🏥": [
        "טיפוח", "יופי", "רפואה", "פארם", "בריאות", "קופת חולים",
        "תרופות", "טיפולים", "קרוספיט", "פיט", "מרפקה"
    ],
    "Education & Learning 📚": [
        "חינוך", "קורסים", "לימודים", "ספרים", "הכשרה", "סטימצקי", "לאבלאפ"
    ],
    "Children & Family 👨‍👩‍👧‍👦": ["ילדים", "טיק", "צעצועים", "בייבי", "משפחה", "פארק"],
    "Income 🏦": [],
    "Other 🗂️": ["שונות"]
}

# Special expenses requiring date adjustment
EXPENSES_TO_ADJUST_DATE = ["משכנתא", "משכורת אריאל", "אור פיט"]

# Modified names mapping
MODIFIED_NAMES = {
    "ועד בית": [{
        "Expense": "העברה מהחשבון",
        "Charged Amount": PRICE_VAAD_BAIT  # Using actual numeric value
    }],
    "גן תמר": [{
        "Expense": "משיכת שיק",
        "Charged Amount": PRICE_GAN_TAMAR,  # Using actual numeric value
        "math_operation": "approx(5%)"
    }],
    "משכנתא": [{
        "Expense": "לאומי",
        "Charged Amount": PRICE_MASHKANTA,  # Using actual numeric value
        "math_operation": "approx(10%)"
    }],
    "צהרון נויה": [{
        "Expense": "משיכת שיק",
        "Charged Amount": PRICE_TSEHARON_NOYA,  # Using actual numeric value
        "math_operation": "approx(5%)"
    }],
    'הפקדות קופ"ג ילדים': [{
        "Expense": "הפקדות קופ",
        "Charged Amount": HAFKADA_GEMEL_CHILDREN  # Using actual numeric value
    }],
    'משכורת אריאל': [{
        "Expense": "משכורת",
        "Charged Amount": ARIEL_SALARY_AVG,  # Using actual numeric value
        "math_operation": "approx(10%)"
    }],
    'חשמל': [{
        "Expense": "אלקטרה פאוור"
    }],
    'משכורת חן': [{
        "Expense": "ספוטניק"
    }],
    'BOOM': [{
        "Expense": "MOOOB"
    }],
    'ביטוח רכב': [{
        "Expense": "9 ביטוח"
    }],
    'ביטוח בריאות ילדים': [{
        "Expense": "הפניקס ביטוח"
    }],
    'חיוב כרטיס אשראי': [
        {
            "Expense": "כרטיסי אשראי",
            "dynamic_operation": 'get_credit_card_name'
        },
        {
            "Expense": "הרשאה כאל",
            "dynamic_operation": 'get_credit_card_name'
        },
        {
            "Expense": "מקס איט",
            "dynamic_operation": 'get_credit_card_name'
        }
    ],
}

# Filters for Notion queries
current_month_year_filter = {
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

current_months_expense_filter = {
    "property": "Processed Date",
    "date": {
        "on_or_after": date(datetime.now().year, datetime.now().month, 1).isoformat()
    }
}

last_4_months_expense_filter = {
    "property": "Processed Date",
    "date": {
        "on_or_after": (today - timedelta(days=145)).isoformat()
    }
}

last_4_months_months_expense_filter = {
    "property": "Date",
    "date": {
        "on_or_after": (today - timedelta(days=145)).isoformat()
    }
}