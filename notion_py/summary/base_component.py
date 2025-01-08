from datetime import date, timedelta
from typing import Dict, List, Optional

from common import today, seconds_to_hours_minutes, parse_duration_to_seconds, calculate_month_boundaries
from notion_py.helpers.notion_children_blocks import create_three_column_layout, create_callout_block, \
    create_paragraph_block, create_separator_block
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
        self.previous_month = self.target_date.replace(day=1) - timedelta(days=1)

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

    def get_notion_section(self) -> list:
        return [
            create_separator_block(),
            self.create_notion_section(),
            create_paragraph_block("")
        ]

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
        first_day, last_day = calculate_month_boundaries(target_date)

        # Create date filter for the entire month
        date_filter = {
            "and": [
                {
                    "property": date_property,
                    "date": {
                        "on_or_after": first_day.isoformat()
                    }
                },
                {
                    "property": date_property,
                    "date": {
                        "on_or_before": last_day.isoformat()
                    }
                }
            ]
        }
        # Add any additional filters
        if additional_filter:
            date_filter["and"].append(additional_filter)

        try:
            pages = get_db_pages(db_id, {"filter": date_filter})
            logger.debug(f"Retrieved {len(pages)} pages for {target_date.strftime('%B %Y')}")
            return pages
        except Exception as e:
            logger.error(f"Error getting pages from database {db_id}: {str(e)}")
            return []

    def _format_comparison(self, current_value: float, previous_value: float,
                           metric_name: str, is_currency: bool = False,
                           reverse_comparison: bool = False) -> str:
        """Formats comparison between current and previous values"""
        if previous_value == 0:
            return "no previous data"

        change = current_value - previous_value
        percentage = (change / previous_value) * 100

        # Adjust change direction if reverse_comparison is True
        if reverse_comparison:
            change = -change
            percentage = -percentage

        prefix = "$" if is_currency else ""
        direction = "↑" if change > 0 else "↓"

        return f"{direction} {prefix}{abs(change):.1f} ({abs(percentage):.1f}% {'increase' if change > 0 else 'decrease'})"

    def format_change_value(self, metric_name: str, format_type: str = "number",
                            invert_comparison: bool = False) -> str:
        """
        Format change value with appropriate indicators and percentages.
        """
        current = self.current_metrics[metric_name]
        previous = self.previous_metrics[metric_name]

        # Handle dictionary metrics (like daily inspiration rate)
        if isinstance(current, dict) and 'rate' in current:
            current = current['rate']
        if isinstance(previous, dict) and 'rate' in previous:
            previous = previous['rate']

        if previous == 0:
            return "no previous data"

        # Convert time format if needed
        if format_type == "time":
            current = parse_duration_to_seconds(current)
            previous = parse_duration_to_seconds(previous)

        # Calculate absolute change and percentage
        abs_change = current - previous
        pct_change = ((current - previous) / previous) * 100

        # Determine if this is an improvement
        if invert_comparison:
            is_improvement = pct_change < 0  # Lower is better
            pct_change = -pct_change  # Invert the percentage
        else:
            is_improvement = pct_change > 0  # Higher is better

        # Format the change value based on type
        if format_type == "time":
            change_str = seconds_to_hours_minutes(abs(abs_change))
        else:
            change_str = f"{abs(abs_change):.2f}"

        # Determine the direction indicator and word
        direction = "↑" if is_improvement else "↓"
        change_word = "faster" if format_type == "time" else "increase" if is_improvement else "decrease"

        # Create the full comparison string
        return f"{direction} {change_str} ({abs(pct_change):.1f}% {change_word})"

    def generate_metrics(self, metrics_list):
        result = {}

        for metric in metrics_list:
            result[metric] = {
                'current': self.current_metrics.get(metric, 0),
                'previous': self.previous_metrics.get(metric, 0),
            }

        return result

    def generate_callout_block(self, element, bold_title=False):
        return create_callout_block(
            element['list'],  # The list is passed as children
            element['title'],
            emoji=element.get('emoji'),
            bold_title=bold_title,
            color_background=element.get('color_background'),
        )

    def generate_column_callouts(self, callout_elements_list, column_size=3):
        """
        Generate blocks of callouts arranged in columns.
        Each callout should be a top-level block within a column.
        """
        result_blocks = []
        current_blocks = []

        for element in callout_elements_list:
            current_blocks.append(self.generate_callout_block(element, bold_title=True))

            # When we have enough blocks for a row
            if len(current_blocks) == column_size:
                result_blocks.append(create_three_column_layout(*current_blocks))
                current_blocks = []

        # Handle any remaining blocks
        if current_blocks:
            while len(current_blocks) < column_size:
                current_blocks.append(create_paragraph_block(""))
            result_blocks.append(create_three_column_layout(*current_blocks))

        return result_blocks
