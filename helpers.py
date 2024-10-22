from datetime import datetime, timedelta, date
from enum import Enum
from typing import Callable

from logger import logger


def create_date_range(input_date_str, range_days=7):
    # Parse the input date string to a datetime object
    input_date = datetime.strptime(input_date_str, '%Y-%m-%d').date()
    today = datetime.now().date()  # Get today's date

    date_list = []

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


class DateOffset(Enum):
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
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60

    # Return the result as a tuple (hours, minutes)
    str_time = ''
    if hours > 0 and seconds > 0:
        str_time = f"{hours:02}h{minutes:02}"
    elif hours > 0:
        str_time = f"{hours:02}h00"
    elif minutes > 0:
        str_time = f"{minutes:02}m"
    else:
        str_time = "No activity"
    return str_time


today = date.today()
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