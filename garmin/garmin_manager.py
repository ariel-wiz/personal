from datetime import timedelta, datetime
from time import strptime

from common import DateOffset, today, yesterday, day_before_yesterday, get_date_offset
from garmin.garmin_api import get_garmin_info
from logger import logger
from notion_py.helpers.notion_common import generate_icon_url, get_db_pages, \
    get_pages_by_date_offset, \
    update_page_with_relation, create_page_with_db_dict, get_day_summary_by_date_str
from notion_py.notion_globals import DaySummaryCheckbox, IconType, IconColor

WAKE_UP_HOUR_GOAL = '06:00'


class DateManager:
    def __init__(self):
        self.original_today = today
        self.original_yesterday = yesterday
        self.original_day_before = day_before_yesterday

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.restore_dates()

    def set_dates_for_target(self, target_date):
        """Sets global dates based on target date"""
        global today, yesterday, day_before_yesterday
        today = target_date + timedelta(days=1)
        yesterday = target_date
        day_before_yesterday = target_date - timedelta(days=1)

    def restore_dates(self):
        """Restores original global dates"""
        global today, yesterday, day_before_yesterday
        today = self.original_today
        yesterday = self.original_yesterday
        day_before_yesterday = self.original_day_before


class GarminManager:
    def __init__(self, garmin_db_id, day_summary_db_id):
        self.garmin_db_id = garmin_db_id
        self.day_summary_db_id = day_summary_db_id

    def _create_garmin_data_dict(self, date, garmin_dict):
        """Creates formatted Garmin data dictionary for Notion"""
        return {
            "Name": date.strftime('%A %d/%m'),
            "Date": date.isoformat(),
            "Sleep Start": garmin_dict['sleep_start'],
            "Sleep End": garmin_dict['sleep_end'],
            "Sleep Feedback": garmin_dict['sleep_feedback_overall'],
            "Sleep Note": garmin_dict['sleep_feedback_note'],
            "Sleep Duration": garmin_dict['sleep_duration'],
            "Steps": garmin_dict['steps'],
            "Steps Goal": garmin_dict['daily_steps_goal'],
            "Calories": garmin_dict['total_calories'],
            "Activity Duration": garmin_dict['total_activity_duration'],
            "Activity Calories": garmin_dict['total_activity_calories'],
            "Activities": garmin_dict['activity_names'],
            "Icon": generate_icon_url(IconType.WATCH, IconColor.BLUE)
        }

    def _get_missing_dates(self, days_back=30):
        """Gets list of dates without Garmin data in the last n days"""
        existing_garmin_pages = get_db_pages(self.garmin_db_id)
        existing_dates = {page["properties"]["Date"]["date"]["start"]
                          for page in existing_garmin_pages}

        date_range = [(today - timedelta(days=i)) for i in range(1, days_back + 1)]
        return [date for date in date_range if date.isoformat() not in existing_dates]

    def _update_daily_tasks(self, garmin_page_id, garmin_dict, target_date):
        """Updates daily tasks with Garmin data"""
        # Format the date properly as a string
        date_str = target_date.isoformat()

        # Get the daily tasks for the same date as the Garmin data
        daily_tasks = get_pages_by_date_offset(self.day_summary_db_id,
                                               get_date_offset(date_str))

        if not daily_tasks:
            logger.info(f"No daily task found for {date_str}")
            return

        daily_task_id = daily_tasks[0]["id"]
        activity_names = garmin_dict.get("activity_names", "")

        other_fields = self.check_exercise_according_to_activity_names(activity_names)
        other_fields.update(self.check_wake_up_early_according_to_sleep_end({
            DaySummaryCheckbox.wake_up_early: garmin_dict['sleep_end']
        }))

        update_page_with_relation(
            daily_task_id,
            garmin_page_id,
            "Watch Metrics",
            other_fields
        )
        logger.info(f"Updated daily task with Garmin info for {target_date.strftime('%d-%m-%Y')}")

    def process_single_date(self, target_date, update_daily_tasks=True):
        """Process Garmin data for a single date"""
        # Ensure target_date is a proper date object
        if isinstance(target_date, str):
            target_date = datetime.strptime(target_date, '%Y-%m-%d').date()

        formatted_date = target_date.strftime('%A %d/%m')
        logger.info(f"Processing Garmin data for {formatted_date}")

        with DateManager() as dm:
            dm.set_dates_for_target(target_date)

            # Calculate days_ago based on target_date
            days_ago = (datetime.now().date() - target_date).days
            garmin_dict = get_garmin_info(days_ago=days_ago)

            if not garmin_dict:
                logger.info(f"No Garmin data found for {formatted_date}")
                return False

            formatted_data = self._create_garmin_data_dict(target_date, garmin_dict)
            response = create_page_with_db_dict(self.garmin_db_id, formatted_data)
            logger.info(f"Created Garmin info for {formatted_date}")

            if update_daily_tasks and garmin_dict:
                try:
                    self._update_daily_tasks(response['id'], garmin_dict, target_date)
                except Exception as e:
                    logger.error(f"Error updating daily tasks: {str(e)}")

            return True

    def update_garmin_info(self, update_daily_tasks=True, fill_history=False):
        """
        Updates Garmin information in Notion database.

        Args:
            update_daily_tasks (bool): Whether to update daily task relations
            fill_history (bool): Whether to check and fill historical gaps
        """
        if fill_history:
            dates_to_update = self._get_missing_dates()
            if not dates_to_update:
                logger.info("No missing dates found in Garmin data")
                return
            logger.info(f"Found {len(dates_to_update)} dates to update")
        else:
            # Check if yesterday exists
            yesterday_pages = get_pages_by_date_offset(self.garmin_db_id,
                                                       DateOffset.YESTERDAY)
            if yesterday_pages:
                logger.info(f"Garmin page for yesterday already exists")
                return
            dates_to_update = [yesterday]

        success_count = 0
        for target_date in dates_to_update:
            try:
                if self.process_single_date(target_date, update_daily_tasks):
                    success_count += 1
            except Exception as e:
                logger.error(f"Error processing {target_date}: {str(e)}")
                continue

        logger.info(f"Successfully processed {success_count}/{len(dates_to_update)} dates")

    def check_wake_up_early_according_to_sleep_end(self, sleep_end_dict):
        """
        Checks if wake up time is earlier than the goal time.

        Args:
            sleep_end_dict (dict): Dictionary containing wake up time

        Returns:
            dict: Checkbox update dictionary if wake up was early, empty dict otherwise
        """
        if DaySummaryCheckbox.wake_up_early in sleep_end_dict:
            wake_up_hour = sleep_end_dict[DaySummaryCheckbox.wake_up_early]

            try:
                # Convert times to datetime objects for comparison
                from datetime import datetime
                time_format = '%H:%M'

                wake_up_time = datetime.strptime(wake_up_hour, time_format)
                goal_time = datetime.strptime(WAKE_UP_HOUR_GOAL, time_format)

                if wake_up_time.time() <= goal_time.time():
                    logger.debug(f"Checking {DaySummaryCheckbox.wake_up_early} to true")
                    return {DaySummaryCheckbox.wake_up_early: {
                        "checkbox": True
                    }}
            except ValueError as e:
                logger.error(f"Error parsing time: {e}")

        return {}

    def check_exercise_according_to_activity_names(self, activity_names):
        """
        Checks if exercise should be marked based on activity status.

        Args:
            activity_names (dict): Dictionary containing activity status

        Returns:
            dict: Checkbox update dictionary if exercise was done, empty dict otherwise
        """
        activity_names_without_walking = [name for name in activity_names if name != "Walking"]
        if len(activity_names_without_walking) > 0:
            logger.debug(f"Checking {DaySummaryCheckbox.exercise} to true")
            return {DaySummaryCheckbox.exercise: {
                "checkbox": True
            }}
        return {}
