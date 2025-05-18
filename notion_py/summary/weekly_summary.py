from datetime import date, datetime, timedelta
from typing import Dict, Optional, Tuple

from logger import logger
from notion_py.helpers.notion_common import (
    get_db_pages, create_page_with_db_dict_and_children_block,
    generate_icon_url, track_operation, create_page_with_db_dict
)
from notion_py.helpers.notion_payload import generate_payload
from notion_py.helpers.notion_children_blocks import generate_page_content_page_notion_link
from notion_py.notion_globals import IconType, IconColor, NotionAPIOperation
from variables import Keys, Projects


def get_week_dates(target_date: date = None) -> Tuple[date, date, int]:
    """
    Get start and end dates of the week containing target_date.
    Week starts on Sunday.

    Args:
        target_date: Date to find week for (defaults to today)

    Returns:
        tuple: (start_date, end_date, week_number)
    """
    if target_date is None:
        target_date = date.today()

    # Find the Sunday of the current week
    days_since_sunday = (target_date.weekday() + 1) % 7
    week_start = target_date - timedelta(days=days_since_sunday)
    week_end = week_start + timedelta(days=6)

    # Get ISO week number
    _, week_number, _ = target_date.isocalendar()

    return week_start, week_end, week_number


def format_week_string(start_date: date, end_date: date, week_number: int) -> str:
    """
    Format week string as "15-22 March (Week 15)"

    Args:
        start_date: Start of week (Sunday)
        end_date: End of week (Saturday)
        week_number: ISO week number

    Returns:
        str: Formatted week string
    """
    # Handle case where week spans two months
    if start_date.month == end_date.month:
        # Same month: "15-22 March (Week 15)"
        month_name = start_date.strftime("%B")
        return f"{start_date.day}-{end_date.day} {month_name} (Week {week_number})"
    else:
        # Different months: "30 March-5 April (Week 15)"
        start_month = start_date.strftime("%B")
        end_month = end_date.strftime("%B")
        return f"{start_date.day} {start_month}-{end_date.day} {end_month} (Week {week_number})"


def get_first_empty_weekly_summary_row() -> Optional[Dict]:
    """
    Get the first empty row in the weekly summary database.

    Returns:
        dict: First empty row data or None if no empty rows exist
    """
    try:
        # Get all rows in the database
        all_rows = get_db_pages(Keys.weekly_summary_db_id)

        empty_rows = []
        for row in all_rows:
            # Check if Week property is empty
            week_property = row['properties'].get('Week', {})
            if week_property.get('title'):
                # Has title content - check if it's actually empty
                title_content = week_property['title']
                if not title_content or (
                        len(title_content) == 1 and not title_content[0].get('plain_text',
                                                                             '').strip()):
                    empty_rows.append(row)
            else:
                # No title property or it's None
                empty_rows.append(row)

        logger.debug(
            f"Found {len(empty_rows)} truly empty weekly summary rows out of {len(all_rows)} total rows")

        if empty_rows:
            return empty_rows[0]  # Return the first empty row
        else:
            return None

    except Exception as e:
        logger.error(f"Error checking for empty weekly summary rows: {str(e)}")
        return None


def check_existing_week_entry(week_start: date, week_end: date) -> Optional[Dict]:
    """
    Check if there's already an entry for the given week dates.

    Args:
        week_start: Start date of the week
        week_end: End date of the week

    Returns:
        dict: Existing row data or None if no entry exists
    """
    try:
        # Get all rows in the database
        all_rows = get_db_pages(Keys.weekly_summary_db_id)

        for row in all_rows:
            # Check the Date property
            date_property = row['properties'].get('Date', {})
            if date_property.get('date'):
                date_info = date_property['date']
                existing_start = date_info.get('start')
                existing_end = date_info.get('end')

                if existing_start and existing_end:
                    existing_start_date = datetime.fromisoformat(existing_start).date()
                    existing_end_date = datetime.fromisoformat(existing_end).date()

                    # Check if dates match
                    if existing_start_date == week_start and existing_end_date == week_end:
                        return row

        return None

    except Exception as e:
        logger.error(f"Error checking for existing week entry: {str(e)}")
        return None


def get_next_saturday() -> date:
    """
    Get the date of next Saturday.

    Returns:
        date: Next Saturday's date
    """
    today = date.today()
    days_until_saturday = (5 - today.weekday()) % 7
    if days_until_saturday == 0:  # If today is Saturday, get next Saturday
        days_until_saturday = 7
    return today + timedelta(days=days_until_saturday)


@track_operation(NotionAPIOperation.CREATE_WEEKLY_SUMMARY)
def create_weekly_summary_and_task(should_track=False, target_date: date = None) -> Optional[Dict]:
    """
    Update existing empty weekly summary row and create corresponding daily task.
    Only runs on Tuesdays.

    Args:
        should_track: Whether to track the operation
        target_date: Date to create summary for (defaults to current week)

    Returns:
        dict: Created task response or None
    """
    try:
        # Calculate week dates first
        week_start, week_end, week_number = get_week_dates(target_date)
        week_string = format_week_string(week_start, week_end, week_number)

        # Check if entry already exists for these dates
        existing_entry = check_existing_week_entry(week_start, week_end)
        if existing_entry:
            logger.info(f"Weekly summary already exists for {week_string} - no action needed")
            return None

        # Get the first empty row
        empty_row = get_first_empty_weekly_summary_row()

        if empty_row:
            # Update existing empty row
            summary_page_id = empty_row['id']
            update_data = {
                "Week": week_string,
                "Date": [week_start.isoformat(), week_end.isoformat()],  # Date range
            }

            # Create properties payload for update
            update_payload = {"properties": {}}
            for key, value in update_data.items():
                if key == "Week":
                    update_payload["properties"][key] = {"title": [{"text": {"content": value}}]}
                elif key == "Date":
                    update_payload["properties"][key] = {
                        "date": {"start": value[0], "end": value[1]}}

            update_page(summary_page_id, update_payload)

            # Create daily task for next Saturday
            task_name = f"Review Weekly Summary - {week_string}"

            logger.info(f"Updated weekly summary for {week_string}")

            # Create the daily task for next Saturday
            saturday_date = get_next_saturday()

            task_dict = {
                "Task": task_name,
                "Project": Projects.notion,
                "Due": saturday_date.isoformat(),
                "Icon": generate_icon_url(IconType.CHECKLIST, IconColor.BLUE)
            }

            # Create task with link to the updated summary
            children_block = generate_page_content_page_notion_link(summary_page_id)
            task_response = create_page_with_db_dict_and_children_block(
                Keys.daily_tasks_db_id,
                task_dict,
                children_block
            )

            logger.info(f"Created weekly summary task for {saturday_date}: {task_name}")
            return task_response

        else:
            # No empty rows - create error task
            task_name = "ERROR - No more empty rows in Weekly Summary database"

            logger.warning("No empty weekly summary rows available")

            # Create error task for next Saturday
            saturday_date = get_next_saturday()

            task_dict = {
                "Task": task_name,
                "Project": Projects.notion,
                "Due": saturday_date.isoformat(),
                "Icon": generate_icon_url(IconType.CHECKLIST, IconColor.RED)
            }

            # Create error task without link
            task_response = create_page_with_db_dict(Keys.daily_tasks_db_id, task_dict)

            logger.info(f"Created error task for {saturday_date}: {task_name}")
            return task_response

    except Exception as e:
        logger.error(f"Error creating weekly summary: {str(e)}")
        raise


def create_weekly_summary():
    """Standalone function for creating weekly summary (for command line usage)"""
    try:
        result = create_weekly_summary_and_task()
        if result is None:
            logger.info("No weekly summary action was needed")
        else:
            logger.info("Successfully created weekly summary and daily task")
        return result
    except Exception as e:
        logger.error(f"Error in create_weekly_summary: {str(e)}")
        raise