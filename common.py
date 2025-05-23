import functools
import time as timeimport
import re
from datetime import datetime, timedelta, date, time
from typing import Callable, List, Optional, Tuple

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
    formatted_date = input_date.strftime('%A %d/%m')
    return formatted_date


class DateOffset:
    TODAY = 0
    YESTERDAY = 1
    TWO_DAYS_AGO = 2
    THREE_DAYS_AGO = 3


def add_hours_to_time(time_str):
    """
    Adjust time from GMT to Israel time, accounting for daylight saving time
    using the pytz library for accurate timezone conversions.

    Args:
        time_str: Time string in format '%Y-%m-%dT%H:%M:%S.%f'

    Returns:
        Time string in format 'HH:MM' adjusted to Israel time
    """
    import pytz

    # Parse the input string into a datetime object (UTC)
    input_time = datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%S.%f')

    # Make it aware that it's in UTC
    input_time = pytz.utc.localize(input_time)

    # Convert to Israel time
    israel_tz = pytz.timezone('Asia/Jerusalem')
    israel_time = input_time.astimezone(israel_tz)

    # Return the adjusted time in hh:mm format
    return israel_time.strftime('%H:%M')


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


def remove_emojis(text):
    # Emoji Unicode ranges
    emoji_pattern = re.compile(
        "[\U0001F600-\U0001F64F"  # emoticons
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
        "]+",
        flags=re.UNICODE,
    )
    # Remove emojis
    text_no_emojis = emoji_pattern.sub('', text)
    # Remove zero-width joiners and other invisible characters
    text_cleaned = re.sub(r'[\u200d]', '', text_no_emojis)
    # Strip whitespace
    return text_cleaned.strip()


def get_next_sunday():
    """Get the next Sunday's date (or today if today is Sunday)"""
    current_date = today
    # 6 represents Sunday in datetime's weekday() (0 = Monday, 6 = Sunday)
    if current_date.weekday() == 6:
        return current_date

    # Calculate days until next Sunday
    days_until_sunday = (6 - current_date.weekday()) % 7
    return current_date + timedelta(days=days_until_sunday)


def capitalize_text_or_list(text_or_list):
    if isinstance(text_or_list, list):
        return [text.capitalize() for text in text_or_list]
    return text_or_list.capitalize()


def calculate_average_time(times: List[time]) -> Optional[time]:
    """
    Calculates average time from a list of time objects.
    Handles times around midnight by treating early morning hours (0-4) as late night hours (24-28).
    """
    if not times:
        return None

    # Convert times to minutes past midnight, adjusting early morning times
    total_minutes = 0
    for t in times:
        minutes = t.hour * 60 + t.minute
        # If time is between 00:00 and 04:00, treat it as 24:00-28:00
        if t.hour < 4:
            minutes += 24 * 60
        total_minutes += minutes

    avg_minutes = total_minutes / len(times)

    # Convert back to 24-hour format
    hours = int(avg_minutes // 60) % 24  # Use modulo to wrap around to 24-hour format
    minutes = int(avg_minutes % 60)

    return time(hours, minutes)


def parse_duration_to_seconds(duration_str: str) -> int:
    """Converts duration string (e.g., '1h30m' or '45m') to seconds"""
    total_seconds = 0

    # Match hours
    hours_match = re.search(r'(\d+)h', duration_str)
    if hours_match:
        total_seconds += int(hours_match.group(1)) * 3600

    # Match minutes
    minutes_match = re.search(r'(\d+)m', duration_str)
    if minutes_match:
        total_seconds += int(minutes_match.group(1)) * 60

    return total_seconds


def format_duration_days(seconds: float) -> str:
    """Format duration in days and hours"""
    days = int(seconds // (24 * 3600))
    remaining_seconds = seconds % (24 * 3600)
    hours = int(remaining_seconds // 3600)

    if days > 0:
        return f"{days}d {hours}h"
    return f"{hours}h"


def calculate_month_boundaries(target_date) -> Tuple[date, date]:
    """Calculates first and last day of the month"""
    # Convert datetime to date if needed
    if isinstance(target_date, datetime):
        target_date = target_date.date()

    # Get first day of month
    first_day = target_date.replace(day=1)

    # Calculate last day
    if target_date.month == 12:
        last_day = first_day.replace(year=target_date.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        last_day = first_day.replace(month=target_date.month + 1, day=1) - timedelta(days=1)

    return first_day, last_day


def is_approaching_month_end(days_before_end_of_the_month_check=7) -> bool:
    """
    Check if we're within 7 days of the start of the next month.
    """
    current_date = today
    days_until_next_month = ((current_date.replace(day=1) + timedelta(days=32)).replace(day=1) - current_date).days
    return days_until_next_month <= days_before_end_of_the_month_check
