from datetime import datetime, timedelta, date

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

class NotionPropertyType:
    TITLE = "title"
    TEXT = "rich_text"
    SELECT_ID = "select_id"
    SELECT_NAME = "select_name"
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
    CREATE_PAGES = "Create Pages"
    UNCHECK_DONE = "Uncheck Done"
    COPY_BIRTHDAYS = "Copy Birthdays"


class FieldMap:
    exercise = '🏃🏼\xa0Exercise'


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
daily_birthday_filter = {
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
day_summary_sorts = [{
    "property": "Date",
    "direction": "descending"
}]


