import os
from datetime import datetime, timedelta, date
from typing import Callable

from logger import logger

TIMEZONE_OFFSET = 2


def create_date_range(input_date_str, range_days=7):
    # Parse the input date string to a datetime object
    input_date = datetime.strptime(input_date_str, '%Y-%m-%d').date()
    today = datetime.now().date()  # Get today's date

    if input_date >= today:
        # If input date is today or in the future, create next 7 days starting from input date
        date_list = [(input_date + timedelta(days=i)).isoformat() for i in range(range_days)]
        date_list = date_list[1:]
    else:
        # If input date is in the past, create dates from today to 7 days past input date
        date_list = [(today + timedelta(days=i)).isoformat() for i in range((input_date - today).days + range_days)]

    return date_list


def get_day_number(input_date_str):
    # Parse the input date string to a datetime object
    input_date = datetime.strptime(input_date_str, '%Y-%m-%d').date()

    # Get the weekday number (0 for Monday to 6 for Sunday)
    weekday_number = input_date.weekday()

    # Adjust so that Sunday is 0, Monday is 1, and so on
    day_number = (weekday_number + 1) % 7

    return day_number


def get_day_number_formatted(input_date_str):
    day_dict = {
        0: "1️⃣",
        1: "2️⃣",
        2: "3️⃣",
        3: "4️⃣",
        4: "5️⃣",
        5: "😎",
        6: "🤩"
    }
    day_number = get_day_number(input_date_str)
    return day_dict[day_number]


def create_day_summary_name(date_str):
    # day_formatted = get_day_number_formatted(date_str)
    # Parse the input date string to a datetime object
    input_date = datetime.strptime(date_str, '%Y-%m-%d').date()

    # Format the date as '17 October'
    formatted_date = input_date.strftime('%A %d %B')
    return formatted_date


class DateOffset:
    TODAY = 0
    YESTERDAY = 1
    TWO_DAYS_AGO = 2
    THREE_DAYS_AGO = 3


def add_hours_to_time(time_str):
    # Parse the input string into a datetime object
    input_time = datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%S.%f')

    # Add 3 hours using timedelta
    adjusted_time = input_time + timedelta(hours=3)

    # Return the adjusted time in hh:mm format
    return adjusted_time.strftime('%H:%M')


def seconds_to_hours_minutes(seconds):
    # Calculate hours and minutes from total seconds
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)

    # Return the result as a formatted string
    if hours > 0 and seconds > 0:
        str_time = f"{hours:01d}h{minutes:02d}m"
    elif hours > 0:
        str_time = f"{hours:01d}h"
    elif minutes > 0:
        str_time = f"{minutes:02d}m"
    else:
        str_time = "No activity"
    return str_time


today = date.today()
tomorrow = today + timedelta(days=1)
yesterday = today - timedelta(days=1)
day_before_yesterday = today - timedelta(days=2)


def replace_none_with_list_or_string(d, replacements):
    # Check if replacements is not iterable (e.g., int, float), then treat it directly
    if isinstance(replacements, (int, float)):
        replacement_iter = iter([replacements])  # Create an iterator with the single number value
    elif isinstance(replacements, str):
        replacement_iter = iter([replacements])  # Convert string to an iterator with a single element
    else:
        replacement_iter = iter(replacements)  # Otherwise, use the replacements as is (e.g., list)

    def recursive_replace(item):
        if isinstance(item, dict):
            new_dict = {k: recursive_replace(v) for k, v in item.items()}
            return new_dict
        elif isinstance(item, list):
            return [recursive_replace(i) for i in item]
        elif item is None:
            return next(replacement_iter, None)
        else:
            return item

    return recursive_replace(d)


def should_the_date_change(property):
    task_name = property.get('Task')['title'][0]['plain_text']
    try:
        due_property = property.get('Due')
        current_date = due_property["date"]["start"]
        hour = current_date.split("T")[1].split(".")[0]

        if hour == '00:00:00':
            return True
        return False

    except Exception as e:
        logger.info(f"Error: {e} while changing the date for task {task_name}")
        return False


def create_tracked_lambda(func: Callable, *default_args, **default_kwargs):
    """Helper function to create a trackable lambda function"""
    def wrapped(*args, should_track=False, **kwargs):
        combined_args = args if args else default_args
        combined_kwargs = {**default_kwargs, **kwargs}
        return func(*combined_args, should_track=should_track, **combined_kwargs)
    return wrapped


def get_state_prefix(full_str, str_to_split):
    # Split by 'end of warranty' and take the first part
    prefix = full_str.split(str_to_split)[0].strip()
    return prefix


# "כיור וברז בלאנקו end of warranty in 6 days"
def find_state_items(items_list, full_text, str_to_split):
    # Get the search pattern from the full text
    search_text = get_state_prefix(full_text, str_to_split)

    # Look for items that match the prefix
    for item in items_list:
        item = str(item).strip()
        if search_text in item:
            return item
    return ""


def get_date_offset(date_str: str):
    # Parse the input string to a date object
    input_date = datetime.strptime(date_str, "%Y-%m-%d").date()

    # Calculate the difference in days
    delta_days = (today - input_date).days

    return delta_days


def create_shabbat_dates(date_str: str, start_hour: str, end_hour: str) -> tuple:
    # Convert the date and start_hour to a datetime object
    start_datetime = datetime.strptime(f"{date_str} {start_hour}", "%Y-%m-%d %H:%M")

    # Subtract 3 hours from the start time
    start_datetime_offset = start_datetime - timedelta(hours=TIMEZONE_OFFSET)

    # Create the first ISO format date (date + start hour - 3 hours)
    iso_start_date = start_datetime_offset.isoformat()

    # Convert the date and end_hour to a datetime object and add 1 day to the date
    end_datetime = datetime.strptime(f"{date_str} {end_hour}", "%Y-%m-%d %H:%M") + timedelta(days=1)

    # Subtract 3 hours from the end time
    end_datetime_offset = end_datetime - timedelta(hours=TIMEZONE_OFFSET)

    # Create the second ISO format date (date + 1 day + end hour - 3 hours)
    iso_end_date = end_datetime_offset.isoformat()

    return [iso_start_date, iso_end_date]


def parse_expense_date(date_str, include_hour=False):
    # Parse the date string in ISO 8601 format to a datetime object
    date_obj = datetime.fromisoformat(date_str.replace("Z", "+00:00"))

    if include_hour:
        # Apply the timezone offset by subtracting the TIMEZONE_OFFSET
        adjusted_date = date_obj - timedelta(hours=TIMEZONE_OFFSET)
        return adjusted_date.isoformat()

    # Return the adjusted date in ISO 8601 format
    return date_obj.date().isoformat()


def adjust_month_end_dates(date_iso):
    date_obj = datetime.fromisoformat(date_iso)

    # Get the last day of the current month
    if date_obj.month == 12:
        next_month = datetime(date_obj.year + 1, 1, 1)
    else:
        next_month = datetime(date_obj.year, date_obj.month + 1, 1)
    last_day = (next_month - timedelta(days=1)).day

    # Check if date is within last 3 days of the month
    if date_obj.day > (last_day - 3):
        # Adjust to first day of next month
        if date_obj.month == 12:
            adjusted_date = datetime(date_obj.year + 1, 1, 1)
        else:
            adjusted_date = datetime(date_obj.year, date_obj.month + 1, 1)
        return adjusted_date.date().isoformat()

    # If not in last 3 days, return original date
    return date_iso

def get_key_for_value(dict, value):
    return [key for key, val in dict.items() if val == value][0]


