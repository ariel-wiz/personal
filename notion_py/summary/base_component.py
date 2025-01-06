from datetime import date, timedelta
from typing import Dict, List, Optional

from common import today
from notion_py.helpers.notion_common import get_db_pages
from logger import logger


class DatabaseProperties:
    """Database property name mappings"""

    class Garmin:
        DATE = "Date"
        ACTIVITIES = "Activities"
        STEPS = "Steps"
        SLEEP_DURATION = "Sleep Duration"
        ACTIVITY_DURATION = "Activity Duration"

    class Tasks:
        DUE = "Due"
        DONE = "Done"
        PROJECT = "Project"

    class BookSummaries:
        COPIED_TO_DAILY = "Copied to Daily"
        NAME = "Name"
        ADDED_DATE = "Edited"

    class MonthlySummary:
        NAME = "Name"
        DATE = "Due"

    class DailyInspiration:
        DUE = "Due"
        PROJECT = "Project"


class BaseComponent:
    def __init__(self, target_date: Optional[date] = None, field_class=None):
        self._current_metrics = None
        self._previous_metrics = None
        self.target_date = self._get_target_date(target_date)
        self.field_class = field_class

    def _get_target_date(self, target_date: Optional[date] = None) -> date:
        if target_date is None:
            if today.month == 1:
                return date(today.year - 1, 12, 1)
            else:
                return date(today.year, today.month - 1, 1)
        else:
            return target_date

    def _initialize_metrics(self):
        raise NotImplementedError()

    def get_metrics(self) -> Dict:
        """Aggregates health metrics from Garmin data"""
        if not self.current_metrics or not self.previous_metrics:
            self._initialize_metrics()

        fields_to_get = [value for key, value in vars(self.field_class).items() if not key.startswith("__")]
        metrics = self.generate_metrics(fields_to_get)
        return metrics

    def create_notion_section(self) -> dict:
        raise NotImplementedError()

    @property
    def current_metrics(self):
        if not self._current_metrics:
            self._initialize_metrics()
        return self._current_metrics

    @current_metrics.setter
    def current_metrics(self, value):
        self._current_metrics = value

    @property
    def previous_metrics(self):
        if not self._previous_metrics:
            self._initialize_metrics()
        return self._previous_metrics

    @previous_metrics.setter
    def previous_metrics(self, value):
        self._previous_metrics = value

    def _get_pages_for_month(self, db_id: str, target_date: date, date_property: str = "Date",
                             additional_filter: Dict = None) -> List[Dict]:
        """
        Gets all pages from a database for a specific month

        Args:
            db_id: Notion database ID
            target_date: Target date to get pages for
            date_property: Name of the date property in the database
            additional_filter: Optional additional filter to apply
        """
        start_date = target_date.replace(day=1)
        if start_date.month == 12:
            end_date = target_date.replace(year=start_date.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end_date = target_date.replace(month=start_date.month + 1, day=1) - timedelta(days=1)

        date_filter = {
            "and": [
                {
                    "property": date_property,
                    "date": {
                        "on_or_after": start_date.isoformat()
                    }
                },
                {
                    "property": date_property,
                    "date": {
                        "on_or_before": end_date.isoformat()
                    }
                }
            ]
        }

        if additional_filter:
            date_filter["and"].append(additional_filter)

        try:
            return get_db_pages(db_id, {"filter": date_filter})
        except Exception as e:
            logger.error(f"Error getting pages from database {db_id}: {str(e)}")
            return []

    def _format_comparison(self, current_value: float, previous_value: float,
                           metric_name: str, is_currency: bool = False,
                           reverse_comparison: bool = False) -> str:
        """
        Formats comparison between current and previous values
        Args:
            reverse_comparison: If True, treats decrease as positive (e.g., for completion times)
        """
        if previous_value == 0:
            return "no previous data"

        change = ((current_value - previous_value) / previous_value) * 100
        prefix = "$" if is_currency else ""

        # Adjust change direction if reverse_comparison is True
        if reverse_comparison:
            change = -change

        if change > 0:
            return f"↑ {prefix}{abs(current_value - previous_value):.2f} ({change:.1f}% increase)"
        elif change < 0:
            return f"↓ {prefix}{abs(current_value - previous_value):.2f} ({abs(change):.1f}% decrease)"
        return "no change"

    def format_change_value(self, metric_name: str, format_type: str = "number") -> str:
        """
        Format change value with appropriate indicators and percentages

        Args:
            metric_name: Name of the metric in the dictionary
            metrics: Dictionary containing current and previous values
            format_type: Type of formatting ("number", "time", "percentage")
        """
        current = self.current_metrics[metric_name]
        previous = self.previous_metrics[metric_name]

        if previous == 0:
            return "No previous data"

        # Calculate absolute change and percentage
        abs_change = current - previous
        pct_change = ((current - previous) / previous) * 100

        # Determine direction
        is_increase = abs_change > 0
        direction = "↑" if is_increase else "↓"

        # Format the change string
        change_str = f"{abs(abs_change):.2f}"

        # Create the full comparison string
        comparison = f"{direction} {change_str} ({abs(pct_change):.1f}% {'increase' if is_increase else 'decrease'})"

        return comparison

    def generate_metrics(self, metrics_list):
        result = {}

        for metric in metrics_list:
            result[metric] = {
                'current': self.current_metrics.get(metric, 0),
                'previous': self.previous_metrics.get(metric, 0),
            }

        return result
