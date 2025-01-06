from datetime import date, timedelta
from typing import List, Dict, Optional

from notion_py.helpers.notion_children_blocks import create_column_block, create_metrics_single_paragraph, create_stats_list, \
    create_two_column_section
from notion_py.helpers.notion_common import get_db_pages
from notion_py.summary.base_component import BaseComponent, DatabaseProperties


class DevelopmentComponent(BaseComponent):
    def __init__(self, book_summaries_db_id: str, daily_tasks_db_id: str, target_date: Optional[date] = None):
        super().__init__(target_date)
        self.book_summaries_db_id = book_summaries_db_id
        self.daily_tasks_db_id = daily_tasks_db_id

    def _initialize_metrics(self):
        """Initializes development metrics for the target date"""
        # Get current month data
        current_book_summaries = self._get_pages_for_month(
            self.book_summaries_db_id,
            self.target_date,
            date_property=DatabaseProperties.BookSummaries.ADDED_DATE
        )

        current_inspiration = self._get_pages_for_month(
            self.daily_tasks_db_id,
            self.target_date,
            date_property=DatabaseProperties.DailyInspiration.DUE,
            additional_filter={
                "property": DatabaseProperties.DailyInspiration.PROJECT,
                "select": {
                    "equals": "Daily Inspiration"
                }
            }
        )

        # Get previous month data
        previous_month = self.target_date.replace(day=1) - timedelta(days=1)
        previous_book_summaries = self._get_pages_for_month(
            self.book_summaries_db_id,
            previous_month,
            date_property=DatabaseProperties.BookSummaries.ADDED_DATE
        )

        previous_inspiration = self._get_pages_for_month(
            self.daily_tasks_db_id,
            previous_month,
            date_property=DatabaseProperties.DailyInspiration.DUE,
            additional_filter={
                "property": DatabaseProperties.DailyInspiration.PROJECT,
                "select": {
                    "equals": "Daily Inspiration"
                }
            }
        )

        # Calculate metrics
        self._current_metrics = {
            'books_read': len(current_book_summaries),
            'book_list': self._format_book_list(current_book_summaries),
            'inspiration_count': len(current_inspiration)
        }

        self._previous_metrics = {
            'books_read': len(previous_book_summaries),
            'book_list': self._format_book_list(previous_book_summaries),
            'inspiration_count': len(previous_inspiration)
        }

    def get_metrics(self) -> Dict:
        """Returns development metrics with comparisons"""
        if not self.current_metrics or not self.previous_metrics:
            self._initialize_metrics()

        return {
            'books_read': {
                'current': self.current_metrics['books_read'],
                'comparison': self._format_comparison(
                    self.current_metrics['books_read'],
                    self.previous_metrics['books_read'],
                    'books read'
                )
            },
            'inspiration_count': {
                'current': self.current_metrics['inspiration_count'],
                'comparison': self._format_comparison(
                    self.current_metrics['inspiration_count'],
                    self.previous_metrics['inspiration_count'],
                    'inspiration entries'
                )
            },
            'book_list': self.current_metrics['book_list']
        }

    def create_notion_section(self) -> dict:
        metrics = self.get_metrics()

        dev_metrics = [
            f"Books Read: {metrics['books_read']['current']} ({metrics['books_read']['comparison']})",
            f"Inspiration Entries: {metrics['inspiration_count']['current']} ({metrics['inspiration_count']['comparison']})"
        ]

        book_stats = [book['title'] for book in metrics['book_list']]

        left_column = create_column_block(
            "📚 Personal Development",
            [create_metrics_single_paragraph(dev_metrics)]
        )

        right_column = create_column_block(
            "Books Read",
            create_stats_list(book_stats)
        )

        return create_two_column_section(left_column, right_column)

    def _format_book_list(self, book_summaries: List[Dict]) -> List[Dict]:
        """Formats book summaries into a list of book data"""
        return [
            {
                'title': page['properties'][DatabaseProperties.BookSummaries.NAME]['title'][0]['plain_text']
            }
            for page in book_summaries
        ]

    def _format_book_blocks(self, books: List[Dict]) -> List[dict]:
        """Formats books into Notion blocks"""
        return [
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": book['title']}
                        }
                    ]
                }
            }
            for book in books
        ]