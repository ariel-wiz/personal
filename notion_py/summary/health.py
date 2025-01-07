import calendar
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import List, Dict, Optional

from common import calculate_average_time, seconds_to_hours_minutes, parse_duration_to_seconds
from notion_py.helpers.notion_children_blocks import create_column_block, create_metrics_single_paragraph, \
    create_stats_list, \
    create_two_column_section, create_paragraph_block, create_table_block, create_heading_2_block, \
    create_heading_3_block, create_toggle_heading_block
from notion_py.summary.base_component import BaseComponent


class HealthFields:
    """Health field names"""
    TOTAL_WORKOUTS = "total_workouts"
    AVG_STEPS = "avg_steps"
    AVG_SLEEP_DURATION = "avg_sleep_duration"
    ACTIVITIES = "activities"
    AVG_BED_TIME = "avg_bed_time"
    AVG_WAKE_TIME = "avg_wake_time"
    MISSING_DAYS = "missing_days"
    AVG_CALORIES = "avg_calories"


class HealthComponent(BaseComponent):
    def __init__(self, garmin_db_id, target_date: Optional[date] = None):
        super().__init__(target_date, HealthFields)
        self.garmin_db_id = garmin_db_id

    def _initialize_metrics(self):
        """Initializes health metrics for the target date"""
        current_month_pages = self._get_pages_for_month(self.garmin_db_id, self.target_date, date_property="Date")
        previous_month = self.target_date.replace(day=1) - timedelta(days=1)
        previous_month_pages = self._get_pages_for_month(self.garmin_db_id, previous_month, date_property="Date")

        # Current month metrics
        self._current_metrics = self._calculate_health_metrics(current_month_pages)
        self._previous_metrics = self._calculate_health_metrics(previous_month_pages)

    def _calculate_health_metrics(self, pages: List[Dict]) -> Dict:
        """Calculates health metrics from Garmin pages"""
        total_workouts = 0
        total_steps = 0
        total_sleep_seconds = 0
        days_count = 0
        activities = defaultdict(lambda: {'sessions': 0, 'duration': 0})
        sleep_times = []
        wake_times = []
        calories = []

        # Get total days in month
        if pages:
            first_date = datetime.strptime(pages[0]['properties']['Date']['date']['start'], '%Y-%m-%d')
            total_days = calendar.monthrange(first_date.year, first_date.month)[1]
            tracked_days = len(pages)
            missing_days = total_days - tracked_days
        else:
            missing_days = 0

        for page in pages:
            props = page['properties']

            if props.get('Calories', {}).get('number'):
                calories.append(props['Calories']['number'])

            # Track sleep/wake times
            if props.get('Sleep Start', {}).get('rich_text'):
                sleep_time = props['Sleep Start']['rich_text'][0]['plain_text']
                sleep_times.append(datetime.strptime(sleep_time, '%H:%M').time())

            if props.get('Sleep End', {}).get('rich_text'):
                wake_time = props['Sleep End']['rich_text'][0]['plain_text']
                wake_times.append(datetime.strptime(wake_time, '%H:%M').time())

            # Count activities
            if props.get('Activities', {}).get('multi_select'):
                for activity in props['Activities']['multi_select']:
                    activities[activity['name']]['sessions'] += 1
                    if props.get('Activity Duration', {}).get('rich_text'):
                        duration_str = props['Activity Duration']['rich_text'][0]['plain_text']
                        duration_seconds = parse_duration_to_seconds(duration_str)
                        activities[activity['name']]['duration'] += duration_seconds

            # Track steps
            if props.get('Steps', {}).get('number'):
                total_steps += props['Steps']['number']
                days_count += 1

            # Track sleep
            if props.get('Sleep Duration', {}).get('rich_text'):
                sleep_str = props['Sleep Duration']['rich_text'][0]['plain_text']
                sleep_seconds = parse_duration_to_seconds(sleep_str)
                if sleep_seconds:
                    total_sleep_seconds += sleep_seconds
                    if not props.get('Activities'):  # Only count days without activities
                        days_count += 1

        # Format activities for output
        formatted_activities = [
            {
                'name': name,
                'sessions': stats['sessions'],
                'duration': seconds_to_hours_minutes(stats['duration'])
            }
            for name, stats in activities.items()
        ]

        avg_sleep_time = calculate_average_time(sleep_times) if sleep_times else None
        avg_wake_time = calculate_average_time(wake_times) if wake_times else None

        return {
            HealthFields.TOTAL_WORKOUTS: sum(activity['sessions'] for activity in formatted_activities),
            HealthFields.AVG_STEPS: round(total_steps / days_count) if days_count > 0 else 0,
            HealthFields.AVG_CALORIES: round(sum(calories) / len(calories)) if calories else 0,
            HealthFields.AVG_SLEEP_DURATION: seconds_to_hours_minutes(total_sleep_seconds / days_count) if days_count > 0 else "0h",
            HealthFields.ACTIVITIES: sorted(formatted_activities, key=lambda x: x['sessions'], reverse=True),
            HealthFields.AVG_BED_TIME: avg_sleep_time.strftime('%H:%M') if avg_sleep_time else "N/A",
            HealthFields.AVG_WAKE_TIME: avg_wake_time.strftime('%H:%M') if avg_wake_time else "N/A",
            HealthFields.MISSING_DAYS: missing_days
        }

    def create_notion_section(self):
        metrics = self.get_metrics()

        main_metrics_headers = ["Metric", "Value", "Change"]

        main_metrics = [
            ["🏃 Workouts", metrics[HealthFields.TOTAL_WORKOUTS]['current'], self.format_change_value(HealthFields.TOTAL_WORKOUTS)],
            ["👣 Average Steps", metrics[HealthFields.AVG_STEPS]['current'], self.format_change_value(HealthFields.AVG_STEPS)],
            ["💦 Average Calories", metrics[HealthFields.AVG_CALORIES]['current'], self.format_change_value(HealthFields.AVG_CALORIES)],
            ["😴 Sleep Duration", metrics[HealthFields.AVG_SLEEP_DURATION]['current'], f"⏰ Previous: {metrics[HealthFields.AVG_SLEEP_DURATION]['previous']}"],
            ["🌙 Bedtime", metrics[HealthFields.AVG_BED_TIME]['current'], f"⏰ Previous: {metrics[HealthFields.AVG_BED_TIME]['previous']}"],
            ["☀️ Wake Time", metrics[HealthFields.AVG_WAKE_TIME]['current'], f"⏰ Previous: {metrics[HealthFields.AVG_WAKE_TIME]['previous']}"],
            ["📅 Missing Days", metrics[HealthFields.MISSING_DAYS]['current'], f"📅 Previous: {metrics[HealthFields.MISSING_DAYS]['previous']}"]
        ]

        activities_stats = [
            f"{activity['name']}: {activity['sessions']} sessions ({activity['duration']})"
            for activity in self.current_metrics.get('activities', [])
        ]

        blocks = [
                   create_table_block(main_metrics_headers, main_metrics),
                   create_heading_3_block("Activities Breakdown"),
               ] + create_stats_list(activities_stats)

        return create_toggle_heading_block("🏃‍♂️ Health & Activity", blocks, heading_number=2)
