import re
from collections import defaultdict
from datetime import date, timedelta
from typing import List, Dict, Optional

from expense.expense_constants import ENGLISH_CATEGORY
from notion_py.helpers.notion_children_blocks import (
    create_toggle_heading_block,
    create_section_text_with_bullet, create_db_block, create_heading_3_block, create_paragraph_block,
    create_heading_2_block,
)
from notion_py.summary.base_component import BaseComponent


class FinanceFields:
    """Constants for finance field names"""
    TOTAL_EXPENSES = "total_expenses"
    TOP_CATEGORIES = "top_categories"
    LARGEST_EXPENSES = "largest_expenses"
    CATEGORY_CHANGES = "category_changes"
    MONTHLY_EXPENSES = "monthly_expenses"
    INCOME = "income"
    SAVING = "saving"
    RECURRING_EXPENSES = "recurring_expenses"


class FinancesComponent(BaseComponent):
    def __init__(self, expense_tracker_db_id: str, monthly_category_expense_db: str,
                 monthly_expenses_summary_previous_month_view_link: str, target_date: Optional[date] = None):
        super().__init__(target_date, FinanceFields)
        self.expense_tracker_db_id = expense_tracker_db_id
        self.monthly_category_expense_db_id = monthly_category_expense_db
        self.monthly_expenses_summary_previous_month_view_link = monthly_expenses_summary_previous_month_view_link

    def _initialize_metrics(self):
        """Initialize financial metrics for current and previous months"""
        self._current_metrics = self._get_month_metrics(self.target_date)

        previous_month = self.target_date.replace(day=1) - timedelta(days=1)
        self._previous_metrics = self._get_month_metrics(previous_month)

    def _get_month_metrics(self, target_date: date) -> Dict:
        """Get metrics from monthly category database for the given month"""
        month_pages = self._get_pages_for_month(
            self.monthly_category_expense_db_id,
            target_date,
            date_property="Date"
        )

        if not month_pages:
            return self._get_empty_metrics()

        return {
            **self._calculate_category_metrics(month_pages),
            FinanceFields.TOP_CATEGORIES: self._get_category_summary(month_pages)
        }

    def _get_empty_metrics(self) -> Dict:
        """Return empty metrics structure"""
        return {
            FinanceFields.TOTAL_EXPENSES: 0,
            FinanceFields.MONTHLY_EXPENSES: 0,
            FinanceFields.INCOME: 0,
            FinanceFields.RECURRING_EXPENSES: 0,
            FinanceFields.TOP_CATEGORIES: [],
            FinanceFields.LARGEST_EXPENSES: [],
            FinanceFields.CATEGORY_CHANGES: []
        }

    def _calculate_expense_metrics(self, expenses: List[Dict]) -> Dict:
        """Calculate core financial metrics"""
        total_expenses = 0
        monthly_expenses = 0
        income = 0
        recurring_expenses = 0

        for expense in expenses:
            amount = self._get_expense_amount(expense)

            if amount > 0:
                income += amount
            else:
                total_expenses += abs(amount)
                if self._is_monthly_expense(expense):
                    monthly_expenses += abs(amount)
                if self._is_recurring_expense(expense):
                    recurring_expenses += abs(amount)

        return {
            FinanceFields.TOTAL_EXPENSES: round(total_expenses, 2),
            FinanceFields.MONTHLY_EXPENSES: round(monthly_expenses, 2),
            FinanceFields.INCOME: round(income, 2),
            FinanceFields.RECURRING_EXPENSES: round(recurring_expenses, 2)
        }

    def _get_expense_amount(self, expense: Dict) -> float:
        """Get expense amount from expense record"""
        return expense['properties'].get('Charged Amount', {}).get('number', 0)

    def _is_monthly_expense(self, expense: Dict) -> bool:
        """Check if expense is a monthly expense"""
        category = expense['properties'].get('Category', {}).get('select', {}).get('name', '')
        return "Monthly" in category

    def _is_recurring_expense(self, expense: Dict) -> bool:
        """Check if expense is recurring"""
        expense_type = expense['properties'].get('Type', {}).get('select', {}).get('name', '')
        return expense_type == 'Credit'

    def _get_category_breakdown(self, expenses: List[Dict]) -> List[Dict]:
        """Get expense breakdown by category"""
        categories = defaultdict(float)

        for expense in expenses:
            amount = self._get_expense_amount(expense)
            if amount < 0:  # Only include expenses, not income
                category = self._get_expense_category(expense)
                categories[category] += abs(amount)

        return [
            {
                'name': category,
                'amount': round(amount, 2)
            }
            for category, amount in sorted(
                categories.items(),
                key=lambda x: x[1],
                reverse=True
            )
        ]

    def _get_expense_category(self, expense: Dict) -> str:
        """Get category from expense record"""
        return expense['properties'].get('Category', {}).get('select', {}).get('name', 'Other')

    def _get_largest_expenses(self, expenses: List[Dict], limit: int = 3) -> List[Dict]:
        """Get largest individual expenses"""
        expense_list = [
            {
                'name': self._get_expense_name(expense),
                'amount': abs(self._get_expense_amount(expense))
            }
            for expense in expenses
            if self._get_expense_amount(expense) < 0  # Only include expenses, not income
        ]

        return sorted(
            expense_list,
            key=lambda x: x['amount'],
            reverse=True
        )[:limit]

    def _get_expense_name(self, expense: Dict) -> str:
        """Get expense name from expense record"""
        title_array = expense['properties'].get('Expense', {}).get('title', [])
        return title_array[0].get('plain_text', '') if title_array else ''

    def _calculate_category_metrics(self, month_pages: List[Dict]) -> Dict:
        """Calculate metrics from monthly category pages"""
        total_expenses = 0
        total_income = 0
        total_saving = 0

        for page in month_pages:
            if self._is_expense_category(page):
                amount = self._get_category_amount(page)
                if amount:
                    total_expenses += amount
            elif self._is_income_category(page):
                amount = self._get_category_amount(page)
                if amount:
                    total_income += amount
            elif self._is_saving_category(page):
                amount = self._get_category_amount(page)
                if amount:
                    total_saving += amount

        return {
            FinanceFields.TOTAL_EXPENSES: round(total_expenses, 2),
            FinanceFields.INCOME: round(total_income, 2),
            FinanceFields.SAVING: round(total_saving, 2)
        }

    def _get_category_amount(self, page: Dict) -> float:
        """Get total amount from category page"""
        return page['properties'].get('Total', {}).get('formula', {}).get('number', 0)

    def _is_expense_category(self, page: Dict) -> bool:
        """Check if page is an expense category"""
        return self.is_category(page, "Expenses")

    def _is_income_category(self, page: Dict) -> bool:
        """Check if page is an income category"""
        return self.is_category(page, "Income")

    def _is_saving_category(self, page: Dict) -> bool:
        """Check if page is an income category"""
        return self.is_category(page, "Saving")

    def is_category(self, page: Dict, category_name) -> bool:
        """Check if page is an income category"""
        category = page['properties']['Category']['title'][0]['plain_text']
        return category == category_name

    def _get_category_summary(self, month_pages: List[Dict]) -> List[Dict]:
        """Get summary of all categories with their totals and performance"""
        return [{
            'name': page['properties']['Category']['title'][0]['plain_text'],
            'amount': self._get_category_amount(page),
            'percentage': self._get_category_percentage(page),
            'average': self._get_category_average(page),
            'icon': page['properties'].get('Icon', {}).get('formula', {}).get('string', '📌')
        } for page in month_pages]

    def _get_category_percentage(self, page: Dict) -> Optional[float]:
        """Get percentage change from 4-month average"""
        return page['properties'].get('Percentage', {}).get('formula', {}).get('number')

    def _get_category_average(self, page: Dict) -> Optional[float]:
        """Get 4-month average amount"""
        return page['properties'].get('4 Months Average', {}).get('number')

    def _get_category_icon(self, category: str) -> str:
        """Get icon from the category name or special mapping"""
        # Special cases first
        special_mapping = {
            "Expenses": "💸",
            "Saving": "💰",
            "Credit Card": "💳"
        }

        if category in special_mapping:
            return special_mapping[category]

        # Strip any emoji from category name for matching
        clean_category = category.split(' ')[0].strip()

        # Find matching category in ENGLISH_CATEGORY
        for full_category, _ in ENGLISH_CATEGORY.items():
            if clean_category in full_category:
                return full_category.split(' ')[-1]
        return "📌"

    def get_main_categories_list(self):
        metrics = self.get_metrics()

        # Separate main categories and other categories
        main_categories = []

        for category in metrics[FinanceFields.TOP_CATEGORIES]['current']:
            if not category['amount']:
                continue

            # Format strings with integers
            amount_str = f"₪{int(abs(category['amount'])):,}"
            avg_str = f"₪{int(abs(category['average'])):,}" if category['average'] else "No average"

            # Calculate performance indicator
            percentage = category['percentage']
            if percentage is not None:
                is_expense = category['name'] == "Expenses"
                is_above_average = percentage > 100

                # For expenses, flip the interpretation
                if is_expense:
                    is_above_average = not is_above_average

                arrow = "⬆️" if is_above_average else "⬇️"
                comparison = "above" if is_above_average else "below"
                performance = f"{arrow} {int(abs(percentage))}% {comparison} average"

                # Determine color
                if abs(percentage) > 5:  # Only color if difference is significant
                    if category['name'] in ['Income', 'Saving']:
                        color = "green" if is_above_average else "red"
                    else:
                        color = "red" if is_above_average else "green"
                else:
                    color = None

                # Bold the percentage part
                bold_part = f"{int(abs(percentage))}% {comparison} average"
            else:
                performance = "➖ On average"
                color = None

            # Format bullet point
            icon = self._get_category_icon(category['name'])

            # Sort into main or other categories
            if category['name'] in ['Income', 'Expenses', 'Saving']:
                main_categories.append({"category": category['name'],
                                        "amount": amount_str,
                                        "average": avg_str,
                                        "performance": performance,
                                        "icon": icon,
                                        "color": color})

        return main_categories

    def get_summary_category_block(self):
        metrics = self.get_metrics()
        current_ratio = metrics[FinanceFields.INCOME]['current'] - metrics[FinanceFields.TOTAL_EXPENSES]['current']
        previous_ratio = metrics[FinanceFields.INCOME]['previous'] - metrics[FinanceFields.TOTAL_EXPENSES]['previous']
        #
        # current_expense = metrics[FinanceFields.TOTAL_EXPENSES]['current']
        # previous_expense = metrics[FinanceFields.TOTAL_EXPENSES]['previous']
        #
        # current_saving = metrics[FinanceFields.SAVING]['current']
        # previous_saving = metrics[FinanceFields.SAVING]['previous']

        title = "Financial Summary"
        arrow = "⬆️" if current_ratio > previous_ratio else "⬇️"
        ratio_str = f"+{int(abs(current_ratio)):,} ₪"
        previous_ratio_str = f"{int(abs(previous_ratio)):,} ₪"
        previous_ratio_avg_str = f"{arrow} Average: {previous_ratio_str}"

        callout_element = {
            "title": title,
            "emoji": "💰",
            "list": [create_heading_2_block(ratio_str),
                     create_paragraph_block(previous_ratio_avg_str,
                                            bold_word=previous_ratio_str)],
            "color_background": "green" if current_ratio > 0 else "red"
            }

        return self.generate_callout_block(callout_element)



    def get_main_categories_blocks(self) -> List[Dict]:
        main_categories = self.get_main_categories_list()
        element_to_add = []

        for element in main_categories:
            category = element['category']
            amount = element['amount']
            avg = element['average']
            performance = element['performance']
            icon = element['icon']
            color = element['color']

            performance_icon = "⬆️" if "above" in performance else "⬇️"

            element_dict = {
                "title": category,
                "emoji": icon,
                "list": [create_heading_2_block(amount, color=color),
                         create_paragraph_block(f"{performance_icon} Average: {avg}",
                                                bold_word=avg)]
            }
            element_to_add.append(element_dict)

        return self.generate_column_callouts(element_to_add, column_size=3)

    def create_notion_section(self) -> dict:
        """Create Notion section for financial summary"""
        metrics = self.get_metrics()

        # Separate main categories and other categories
        main_categories = []
        other_categories = []

        for category in metrics[FinanceFields.TOP_CATEGORIES]['current']:
            if not category['amount']:
                continue

            # Format strings with integers
            amount_str = f"₪{int(abs(category['amount'])):,}"
            avg_str = f"₪{int(abs(category['average'])):,}" if category['average'] else "No average"

            # Calculate performance indicator
            percentage = category['percentage']
            if percentage is not None:
                is_expense = category['name'] == "Expenses"
                is_above_average = percentage > 100

                # For expenses, flip the interpretation
                if is_expense:
                    is_above_average = not is_above_average

                arrow = "⬆️" if is_above_average else "⬇️"
                comparison = "above" if is_above_average else "below"
                performance = f"{arrow} {int(abs(percentage))}% {comparison} average"

                # Determine color
                if abs(percentage) > 5:  # Only color if difference is significant
                    if category['name'] in ['Income', 'Saving']:
                        color = "green" if is_above_average else "red"
                    else:
                        color = "red" if is_above_average else "green"
                else:
                    color = None

                # Bold the percentage part
                bold_part = f"{int(abs(percentage))}% {comparison} average"
            else:
                performance = "➖ On average"
                color = None
                bold_part = None
                percentage = 0  # For sorting purposes

            # Format bullet point
            icon = self._get_category_icon(category['name'])
            bullet = f"{icon} {category['name']}: {amount_str} (Avg: {avg_str}) • {performance}"

            # Sort into main or other categories
            if category['name'] in ['Income', 'Expenses', 'Saving']:
                main_categories.append((bullet, bold_part, color))
            else:
                # Store the actual percentage value for sorting
                other_categories.append((bullet, bold_part, color, abs(percentage) if percentage is not None else 0))

        # Sort other categories by the stored percentage value
        other_categories.sort(key=lambda x: x[3], reverse=True)

        # Create blocks list
        blocks = []

        # Add main categories as paragraphs
        for bullet, bold_part, color in main_categories:
            shekel_price = self.extract_first_price(bullet)
            color_data = [{"color": color, "words": bold_part}]

            blocks.append(
                create_paragraph_block(bullet, bold_word=bold_part, color_list=color_data, code_words=shekel_price))

        # Add other categories in a toggle if there are any
        if other_categories:
            category_blocks = []

            for bullet, bold_part, color, _ in other_categories:  # Ignore the percentage used for sorting
                shekel_price = self.extract_first_price(bullet)
                color_data = [{"color": color, "words": bold_part}]

                category_blocks.append(
                    create_paragraph_block(bullet, bold_word=bold_part, color_list=color_data, code_words=shekel_price)
                )

            blocks.append(
                create_toggle_heading_block(
                    "Other Categories",
                    category_blocks
                )
            )

        return create_toggle_heading_block(
            "💰 Financial Overview - 🔗",
            [block for block in blocks if block is not None],
            heading_number=2,
            link_url={
                "url": self.monthly_expenses_summary_previous_month_view_link,
                "subword": "🔗"
            }
        )

    def extract_first_price(self, text):
        """Extracts the first price with the shekel sign (₪) including commas."""
        match = re.search(r'₪\d{1,3}(?:,\d{3})*(?=\b)', text)  # Matches prices like ₪237 or ₪15,080
        return match.group().strip() if match else None
