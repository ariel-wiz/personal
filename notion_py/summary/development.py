import calendar
from dataclasses import dataclass
from datetime import date, timedelta
from typing import List, Dict, Optional

from notion_py.helpers.notion_children_blocks import (
    create_column_block, create_metrics_single_paragraph, create_stats_list,
    create_two_column_section, create_section_text_with_bullet, create_toggle_heading_block
)
from notion_py.helpers.notion_common import get_db_pages
from notion_py.summary.base_component import BaseComponent, DatabaseProperties


@dataclass
class APIMetrics:
    """Class to hold API metrics data"""
    id: str
    date: str
    state: str
    operation: str
    extended_state: Optional[str]

    @property
    def is_success(self) -> bool:
        return "Success" in self.state

    @property
    def failure_reason(self) -> Optional[str]:
        """Get failure reason from extended state if status is failure"""
        if not self.is_success and self.extended_state:
            return self.extended_state
        return None


class DevelopmentFields:
    """Development field names"""
    BOOKS_READ = "books_read"
    BOOK_LIST = "book_list"
    API_SUCCESS_RATE = "api_success_rate"
    API_TOTAL_RUNS = "api_total_runs"
    API_SUCCESS_RUNS = "api_success_runs"
    API_FAILURES = "api_failures"
    API_STATES = "api_states"


class DevelopmentComponent(BaseComponent):
    def __init__(self, book_summaries_db_id: str, api_db_id: str, api_status_view_link: str,
                 target_date: Optional[date] = None):
        super().__init__(target_date, DevelopmentFields)
        self.book_summaries_db_id = book_summaries_db_id,
        self.api_db_id = api_db_id
        self.api_status_view_link = api_status_view_link

    def _initialize_metrics(self):
        """Initialize metrics for current and previous months"""
        self._current_metrics = self._get_month_metrics(self.target_date)
        self._previous_metrics = self._get_month_metrics(self.previous_month)

    def _get_month_metrics(self, target_date: date) -> Dict:
        """Get metrics for a specific month"""
        book_metrics = self._get_book_metrics(target_date)
        api_metrics = self._get_api_metrics(target_date)

        return {**book_metrics, **api_metrics}

    def _get_book_metrics(self, target_date: date) -> Dict:
        """Calculate book-related metrics"""
        book_summaries = self._get_pages_for_month(
            self.book_summaries_db_id,
            target_date,
            date_property=DatabaseProperties.BookSummaries.ADDED_DATE
        )

        return {
            DevelopmentFields.BOOKS_READ: len(book_summaries),
            DevelopmentFields.BOOK_LIST: self._format_book_list(book_summaries)
        }

    def _get_api_metrics(self, target_date: date) -> Dict:
        """Calculate API-related metrics for the month"""
        api_pages = self._get_pages_for_month(
            self.api_db_id,
            target_date,
            date_property="Date"
        )

        total_days = calendar.monthrange(target_date.year, target_date.month)[1]
        daily_states = {}
        daily_failures = []

        for page in api_pages:
            date = page['properties']['Date']['date']['start']
            state = self._determine_daily_state(page['properties'])
            daily_states[date] = state

            # Only process failures
            if state == 'Failure':
                failure_details = {
                    'date': date,
                    'operations': self._extract_error_operations(page['properties'])
                }
                if failure_details['operations']:
                    daily_failures.append(failure_details)

        return {
            'api_success_rate': self._calculate_rate(
                len([s for s in daily_states.values() if s == 'Success']),
                total_days
            ),
            'api_total_runs': total_days,
            'api_success_runs': len([s for s in daily_states.values() if s == 'Success']),
            'api_failures': daily_failures,
            'api_states': [{'date': d, 'state': s} for d, s in daily_states.items()]
        }

    def _extract_error_operations(self, properties: Dict) -> str:
        """Extract only the error/failure operations from properties"""
        operations = [
            'Garmin', 'Create Daily Pages', 'Copy Pages',
            'Handle Done Tasks', 'Uncheck Done', 'Get Expenses'
        ]

        error_ops = []

        for operation in operations:
            if operation not in properties:
                continue

            operation_data = properties[operation].get('select')
            if not operation_data:
                continue

            state = operation_data.get('name')
            if state in ['Error', 'Failure']:
                error_ops.append(f"{operation}: {state}")

        return ', '.join(error_ops) if error_ops else None

    def _determine_daily_state(self, properties: Dict) -> str:
        """Determine the overall state for a day based on all operations.
        Priority: Failure/Error > Success > No Data"""
        operations = [
            'Garmin', 'Create Daily Pages', 'Copy Pages',
            'Handle Done Tasks', 'Uncheck Done', 'Get Expenses'
        ]

        states = []

        for operation in operations:
            if operation not in properties:
                continue

            operation_data = properties[operation].get('select')
            if not operation_data:  # Skip if no select data
                continue

            state = operation_data.get('name')
            if not state:  # Skip if no state name
                continue

            states.append(state)

        # Determine overall state based on priority
        if not states:
            return 'No Data'

        # Any Error or Failure state should make the day a Failure
        if any(state in ['Error', 'Failure'] for state in states):
            return 'Failure'

        # If we have any Success and no Errors/Failures, it's a Success
        if any(state == 'Success' for state in states):
            return 'Success'

        return 'No Data'

    def _get_empty_api_metrics(self) -> Dict:
        """Return empty API metrics structure"""
        return {
            DevelopmentFields.API_SUCCESS_RATE: 0,
            DevelopmentFields.API_TOTAL_RUNS: 0,
            DevelopmentFields.API_SUCCESS_RUNS: 0,
            DevelopmentFields.API_FAILURES: [],
            DevelopmentFields.API_STATES: []
        }

    def _create_api_metrics_from_notion(self, notion_data: List[dict]) -> List[APIMetrics]:
        """Create APIMetrics objects from Notion data"""
        metrics = []
        for item in notion_data:
            props = item['properties']

            # Get all operation states (like Garmin, Create Daily Pages, etc)
            operations = {
                name: props[name]['select']['name']
                for name in props
                if props[name].get('select') and 'name' in props[name]['select']
            }

            for operation, state in operations.items():
                if state in ['Success', 'Error', 'Started']:  # Only process API states
                    metrics.append(APIMetrics(
                        id=item['id'],
                        date=props['Date']['date']['start'],
                        state=state,
                        operation=operation,
                        extended_state=props['ExtendedState']['rich_text'][0]['plain_text']
                        if props.get('ExtendedState', {}).get('rich_text') else None
                    ))

        return metrics

    def _calculate_rate(self, count: int, total: int) -> float:
        """Calculate percentage rate"""
        return round((count / total * 100) if total > 0 else 0, 1)

    def _format_book_list(self, book_summaries: List[Dict]) -> List[Dict]:
        """Format book summaries into a list of book data"""
        return [
            {
                'title': page['properties'][DatabaseProperties.BookSummaries.NAME]['title'][0]['plain_text']
            }
            for page in book_summaries
        ]

    def get_daily_api_success_rate(self) -> Dict:
        """Get completion rate for Daily Inspiration tasks"""
        metrics = self.get_metrics()
        return {
            "current": metrics[DevelopmentFields.API_SUCCESS_RATE]['current'],
            "previous": metrics[DevelopmentFields.API_SUCCESS_RATE]['previous'],
            "change": metrics[DevelopmentFields.API_SUCCESS_RATE]['comparison']
        }

    def create_notion_section(self) -> dict:
        """Create Notion section for development summary"""
        metrics = self.get_metrics()

        # Book metrics
        book_metrics = [
            f"📚 Books Read: {metrics[DevelopmentFields.BOOKS_READ]['current']} "
            f"({self.format_change_value(DevelopmentFields.BOOKS_READ)})"
        ]

        # Add book list if any
        if metrics[DevelopmentFields.BOOK_LIST]['current']:
            book_metrics.extend([
                f"- {book['title']}"
                for book in metrics[DevelopmentFields.BOOK_LIST]['current']
            ])

        # API metrics
        api_metrics = [
            f"Success Rate: {metrics[DevelopmentFields.API_SUCCESS_RATE]['current']}% "
            f"({self.format_change_value(DevelopmentFields.API_SUCCESS_RATE)})",

            f"Total Runs: {metrics[DevelopmentFields.API_TOTAL_RUNS]['current']} "
            f"({self.format_change_value(DevelopmentFields.API_TOTAL_RUNS)})"
        ]

        # Add failure details if any
        if metrics[DevelopmentFields.API_FAILURES]['current']:
            api_metrics.extend([
                                   "Failures:"
                               ] + [
                                   f"- {failure['date']}: {failure['operations']}"
                                   for failure in metrics[DevelopmentFields.API_FAILURES]['current']
                               ])

        return create_toggle_heading_block(
            "📚 Development & API Status - 🔗",
            [
                *create_section_text_with_bullet("Book Progress:", book_metrics),
                *create_section_text_with_bullet("🔄 API Status:", api_metrics)
            ],
            heading_number=2,
            link_url={
                "url": self.api_status_view_link,
                "subword": "🔗"
            }
        )

    def get_metrics(self) -> Dict:
        """Returns development metrics with comparisons"""
        if not self.current_metrics or not self.previous_metrics:
            self._initialize_metrics()

        # Fields to include in metrics
        fields = [
            DevelopmentFields.BOOKS_READ,
            DevelopmentFields.BOOK_LIST,
            DevelopmentFields.API_SUCCESS_RATE,
            DevelopmentFields.API_TOTAL_RUNS,
            DevelopmentFields.API_SUCCESS_RUNS,
            DevelopmentFields.API_FAILURES,
            DevelopmentFields.API_STATES
        ]

        return {
            field: {
                'current': self.current_metrics.get(field),
                'previous': self.previous_metrics.get(field),
                'comparison': self.format_change_value(field)
                if field in [DevelopmentFields.BOOKS_READ, DevelopmentFields.API_SUCCESS_RATE,
                             DevelopmentFields.API_TOTAL_RUNS, DevelopmentFields.API_SUCCESS_RUNS]
                else None
            }
            for field in fields
        }