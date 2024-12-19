from dataclasses import dataclass
from datetime import datetime, timedelta, date
from typing import Callable, List, Dict, Optional

from common import today
from variables import Keys, Projects

tasks_db_id = Keys.tasks_db_id
day_summary_db_id = Keys.day_summary_db_id
day_summary_template_id = Keys.day_summary_template_id
recurring_db_id = Keys.recurring_db_id
zahar_nekeva_db_id = Keys.zahar_nekeva_db_id
trading_db_id = Keys.trading_db_id
garmin_db_id = Keys.garmin_db_id
daily_tasks_db_id = Keys.daily_tasks_db_id
weekly_task_page_id = Keys.weekly_task_page_id
weight_page_id = Keys.weight_page_id
birthday_db_id = Keys.birthday_db_id
api_db_id = Keys.api_db_id
daily_inspiration_project_id = Projects.daily_inspiration
expense_and_warranty_db_id = Keys.expense_and_warranty_db_id
insurance_db_id = Keys.insurance_db_id
expense_tracker_db_id = Keys.expense_tracker_db_id
book_summaries_db_id = Keys.book_summaries_db_id
monthly_category_expense_db = Keys.monthly_category_expense_db


class NotionPropertyType:
    TITLE = "title"
    TEXT = "rich_text"
    SELECT_ID = "select_id"
    SELECT_NAME = "select_name"
    MULTI_SELECT = "multi_select"
    DATE = "date"
    URL = "url"
    NUMBER = "number"
    EMOJI = "emoji"
    CHECKBOX = "checkbox"
    EMAIL = "email"
    RELATION = "relation"
    PEOPLE = "people"



class Method:
    GET = 'GET'
    POST = 'POST'
    PATCH = 'PATCH'
    DELETE = 'DELETE'


class NotionAPIStatus:
    STARTED = "Started"
    SUCCESS = "Success"
    ERROR = "Error"


class NotionAPIOperation:
    GARMIN = "Garmin"
    CREATE_DAILY_PAGES = "Create Daily Pages"
    HANDLE_DONE_TASKS = "Handle Done Tasks"
    COPY_PAGES = "Copy Pages"
    UNCHECK_DONE = "Uncheck Done"
    GET_EXPENSES = "Get Expenses"


class DaySummaryCheckbox:
    exercise = '🏃🏼\xa0Exercise'
    wake_up_early = '⏰\xa0Wake Up Early'


@dataclass
class TaskConfig:
    name: str
    get_pages_func: Callable[[], List[Dict]]
    state_property_name: str
    daily_filter: str  # New: just store the filter string
    date_property_name: Optional[str] = None
    state_suffix: str = ""
    icon: str = "📝"
    project: str = Projects.notion
    children_block: bool = True
    page_id: str = ""


class IconType:
    WATCH = 'watch-analog'
    MENORAH = 'menorah'
    CAKE = 'cake'
    SYNC = 'sync'
    PHONE_CALL = 'phone-call'
    CHECKLIST = 'checklist'
    CURRENCY = 'currency'
    SIGNATURE = 'signature'
    CHAT = 'chat'
    SERVER = 'server'
    SUN = 'sun'
    BOOK = 'book'
    REPEAT = 'repeat'
    DINING = 'dining'
    CASH_REGISTER = 'cash-register'
    SHOPPING_CART = 'shopping-cart'
    CAR = 'car'
    HOME = 'home'
    DRINK = 'drink'
    FIRST_AID_KIT = 'first-aid-kit'
    GRADEBOOK = 'gradebook'
    PEOPLE = 'people'
    LIBRARY = 'library'
    TABS = 'tabs'
    ATM = 'atm'
    VERIFIED = 'verified'
    HISTORY = 'history'
    CREDIT_CARD = 'credit-card'
    ARROW_RIGHT_LINE = 'arrow-right-line'
    GYM = 'gym'
    RUN = 'run'


class IconColor:
    BLUE = 'blue'
    GRAY = 'gray'
    LIGHT_GRAY = 'lightgray'
    YELLOW = 'yellow'
    PURPLE = 'purple'
    ORANGE = 'orange'
    GREEN = 'green'
    RED = 'red'
    BROWN = 'brown'
    PINK = 'pink'


default_tasks_filter = {
    "and": [
        {"and": [
            {"property": "State",
             "formula": {
                 "string": {
                     "is_not_empty": True
                 }}},
            {"property": "State",
             "formula": {
                 "string": {
                     "does_not_contain": "Done"
                 }}}]},
        {"property": "Follow up",
         "checkbox": {
             "equals": False
         }}
    ]
}
daily_birthday_category_filter = {
    "and": [
        {"property": "State",
         "formula": {
             "string": {
                 "does_not_contain": "Done"
             }}},
        {"property": "Category",
         "formula": {
             "string": {
                 "contains": "Birthdays"
             }}}
    ]
}
daily_notion_category_filter = {
    "and": [
        {"property": "State",
         "formula": {
             "string": {
                 "does_not_contain": "Done"
             }}},
        {"property": "Category",
         "formula": {
             "string": {
                 "contains": "Notion"
             }}}
    ]
}
daily_notion_category_filter_with_done_last_week = {
    "and": [
        {
            "property": "Last edited time",
            "date": {
                "past_week": {}
            }
        },
        {
            "property": "Category",
            "formula": {
                "string": {
                    "contains": "Notion"
                }
            }
        },
        {
            "property": "State",
            "formula": {
                "string": {
                    "contains": "Done"
                }
            }
        }
    ]
}

next_month_filter = {
    "and": [
        {
            "property": "Date",
            "date": {
                "on_or_after": datetime.now().date().isoformat()
            }
        },
        {
            "property": "Date",
            "date": {
                "on_or_before": (datetime.now() + timedelta(days=30)).date().isoformat()
            }
        }
    ]
}
on_or_after_today_filter = {
    "property": "Date",
    "date": {
        "on_or_after": datetime.now().date().isoformat()
    }
}

next_filter = {
    "and": [
        {"property": "State",
         "formula": {
             "string": {
                 "is_not_empty": True
             }}},
        {"property": "State",
         "formula": {
             "string": {
                 "does_not_contain": "Done"
             }}}]}
all_calendar_filter = {
    "and": [
        {
            "property": "Due",
            "date": {
                "on_or_after": date.today().isoformat()
            }
        },
        {"property": "is_calendar",
         "formula": {
             "string": {
                 "is_not_empty": True
             }
         }}
    ]
}
default_tasks_sorts = [
    {
        "property": "Due",
        "direction": "ascending"
    },
    {
        "property": "Category",
        "direction": "ascending"
    },
    {
        "property": "Project",
        "direction": "ascending"
    }

]
first_created_sorts = [{
    "property": "Created time",
    "direction": "descending"
}]
expense_and_warranty_filter = {
    "property": "WarrantyState",
    "formula": {
        "string": {
            "is_not_empty": True
        }}
}
daily_inspiration_filter = {"property": "Category",
                            "formula": {
                                "string": {
                                    "contains": "Daily Inspiration"
                                }}}
insurances_filter = {
    "property": "InsuranceState",
    "formula": {
        "string": {
            "is_not_empty": True
        }}
}
daily_recurring_filter = {
    "property": "DailyState",
    "formula": {
        "string": {
            "is_not_empty": True
        }}
}
recursive_filter = {
    "property": "State",
    "formula": {
        "string": {
            "is_not_empty": True
        }}
}
recursive_sorts = [
    {
        "property": "Delay",
        "direction": "descending"
    },
    {
        "property": "Next Due",
        "direction": "ascending"
    }
]
date_descending_sort = [{
    "property": "Date",
    "direction": "descending"
}]

last_4_months_expense_filter = {
    "property": "Processed Date",
    "date": {
        "on_or_after": (today - timedelta(days=145)).isoformat()
    }
}

current_months_expense_filter = {
    "property": "Processed Date",
    "date": {
        "on_or_after": date(datetime.now().year, datetime.now().month, 1).isoformat()
    }
}

last_4_months_months_expense_filter = {
    "property": "Date",
    "date": {
        "on_or_after": (today - timedelta(days=145)).isoformat()
    }
}

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

book_summaries_not_copied_to_daily_filter = {
    "property": "Copied to Daily",
    "checkbox": {
        "equals": False
    }
}
