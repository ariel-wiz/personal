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
birthday_db_id = Keys.birthday_db_id
api_db_id = Keys.api_db_id
daily_inspiration_project_id = Projects.daily_inspiration
expense_and_warranty_db_id = Keys.expense_and_warranty_db_id
insurance_db_id = Keys.insurance_db_id
expense_tracker_db_id = Keys.expense_tracker_db_id


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


class FieldMap:
    exercise = '🏃🏼\xa0Exercise'


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

last_2_months_expense_filter = {
    "property": "Processed Date",
    "date": {
        "on_or_after": (today - timedelta(days=62)).isoformat()
    }
}
