from collections import defaultdict
from datetime import date, timedelta
from typing import List, Dict, Optional

from expense.expense_models import ExpenseField
from notion_py.summary.base_component import BaseComponent


class FinancesComponent(BaseComponent):
    def __init__(self, expense_tracker_db_id: str, target_date: Optional[date] = None):
        super().__init__(target_date)
        self.expense_tracker_db_id = expense_tracker_db_id

    def _initialize_metrics(self):
        """Initializes financial metrics for the target date"""
        current_month_expenses = self._get_pages_for_month(
            self.expense_tracker_db_id,
            self.target_date,
            date_property="Processed Date"
        )

        # Get previous month data
        previous_month = self.target_date.replace(day=1) - timedelta(days=1)
        previous_month_expenses = self._get_pages_for_month(
            self.expense_tracker_db_id,
            previous_month,
            date_property="Processed Date"
        )

        # Calculate metrics
        self._current_metrics = self._calculate_financial_metrics(current_month_expenses)
        self._previous_metrics = self._calculate_financial_metrics(previous_month_expenses)

    def get_metrics(self) -> Dict:
        """Returns financial metrics with comparisons"""
        if not self.current_metrics or not self.previous_metrics:
            self._initialize_metrics()

        return {
            'total_expenses': {
                'current': self.current_metrics['total'],
                'comparison': self._format_comparison(
                    self.current_metrics['total'],
                    self.previous_metrics['total'],
                    'in expenses',
                    is_currency=True
                )
            },
            'top_categories': self.current_metrics['top_categories'][:3],  # Top 3 categories
            'largest_expenses': self.current_metrics['largest_expenses'][:3],  # Top 3 expenses
            'category_changes': self._calculate_category_changes(self.current_metrics, self.previous_metrics)
        }

    def _calculate_financial_metrics(self, expenses: List[Dict]) -> Dict:
        """Calculates financial metrics from expense pages"""
        total = 0
        categories = defaultdict(float)
        expense_list = []

        for expense in expenses:
            props = expense['properties']
            amount = props.get(ExpenseField.CHARGED_AMOUNT, {}).get('number', 0)

            # Only include expenses (negative amounts)
            if amount >= 0:
                continue

            amount = abs(amount)
            total += amount

            # Get category using expense fields
            category = props.get(ExpenseField.CATEGORY, {}).get('select', {}).get('name', 'Other')
            categories[category] += amount

            expense_list.append({
                'name': props.get(ExpenseField.NAME, {}).get('title', [{}])[0].get('plain_text', ''),
                'amount': amount
            })

        return {
            'total': round(total, 2),
            'top_categories': [
                {'name': category, 'amount': round(amount, 2)}
                for category, amount in sorted(categories.items(), key=lambda x: x[1], reverse=True)
            ],
            'largest_expenses': sorted(expense_list, key=lambda x: x['amount'], reverse=True)[:5]  # Top 5 expenses
        }

    def _calculate_category_changes(self, current: Dict, previous: Dict) -> List[Dict]:
        """Calculates changes in spending by category"""
        changes = []
        current_categories = {cat['name']: cat['amount'] for cat in current['top_categories']}
        previous_categories = {cat['name']: cat['amount'] for cat in previous['top_categories']}

        for category, current_amount in current_categories.items():
            previous_amount = previous_categories.get(category, 0)
            if previous_amount > 0:
                percent_change = ((current_amount - previous_amount) / previous_amount) * 100
                changes.append({
                    'category': category,
                    'change': round(percent_change, 1),
                    'amount_change': round(current_amount - previous_amount, 2)
                })

        return sorted(changes, key=lambda x: abs(x['change']), reverse=True)

    def create_notion_section(self) -> dict:
        """Creates the financial section for Notion"""
        metrics = self.get_metrics()

        return {
            "object": "block",
            "type": "column_list",
            "column_list": {
                "children": [
                    # First column - Overview and totals
                    {
                        "object": "block",
                        "type": "column",
                        "column": {
                            "children": [
                                {
                                    "object": "block",
                                    "type": "heading_2",
                                    "heading_2": {
                                        "rich_text": [{"type": "text", "text": {"content": "💰 Financial Overview"}}]
                                    }
                                },
                                {
                                    "object": "block",
                                    "type": "paragraph",
                                    "paragraph": {
                                        "rich_text": [
                                            {"type": "text", "text": {
                                                "content": f"Total Expenses: ${metrics['total_expenses']['current']} ({metrics['total_expenses']['comparison']})\n"}},
                                            {"type": "text", "text": {"content": "\nTop Categories:"}}
                                        ]
                                    }
                                },
                                *self._format_category_blocks(metrics['top_categories'])
                            ]
                        }
                    },
                    # Second column - Largest expenses
                    {
                        "object": "block",
                        "type": "column",
                        "column": {
                            "children": [
                                {
                                    "object": "block",
                                    "type": "heading_2",
                                    "heading_2": {
                                        "rich_text": [{"type": "text", "text": {"content": "Largest Expenses"}}]
                                    }
                                },
                                *self._format_expense_blocks(metrics['largest_expenses'])
                            ]
                        }
                    }
                ]
            }
        }

    def _format_category_blocks(self, categories: List[Dict]) -> List[dict]:
        """Formats categories into Notion blocks"""
        return [
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": f"{category['name']}: ${category['amount']:.2f}"}
                        }
                    ]
                }
            }
            for category in categories
        ]

    def _format_expense_blocks(self, expenses: List[Dict]) -> List[dict]:
        """Formats expenses into Notion blocks"""
        return [
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": f"{expense['name']}: ${expense['amount']:.2f}"}
                        }
                    ]
                }
            }
            for expense in expenses
        ]