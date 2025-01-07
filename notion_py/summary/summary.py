from dataclasses import dataclass
from datetime import date
from typing import Dict, Optional

from logger import logger
from notion_py.helpers.notion_children_blocks import create_heading_1_block, create_separator_block, \
    create_three_column_layout, create_heading_2_block, create_callout_block, create_paragraph_block, \
    create_toggle_heading_block
from notion_py.helpers.notion_common import (
    create_page_with_db_dict_and_children_block,
    generate_icon_url,
    track_operation
)
from notion_py.notion_globals import (
    NotionAPIOperation, IconType, IconColor
)
from notion_py.summary.development import DevelopmentComponent
from notion_py.summary.finances import FinancesComponent
from notion_py.summary.goal import GoalComponent
from notion_py.summary.health import HealthComponent
from notion_py.summary.tasks import TasksComponent
from variables import Keys


@dataclass
class MonthlySummary:
    """Class to hold monthly summary data"""
    target_date: date
    health_component: HealthComponent
    tasks_component: TasksComponent
    finances_component: FinancesComponent
    development_component: DevelopmentComponent
    goal_component: GoalComponent

    def generate_summary(self) -> Dict:
        """Generates the complete monthly summary data"""
        return {
            'month': self.target_date.strftime("%B"),
            'year': str(self.target_date.year),
            'health_metrics': self.health_component.get_metrics(),
            'task_metrics': self.tasks_component.get_metrics(),
            'financial_metrics': self.finances_component.get_metrics(),
            'development_metrics': self.development_component.get_metrics(),
            'goal_metrics': self.goal_component.get_metrics()
        }

    def generate_children_block(self) -> dict:
        """Generates Notion blocks for the monthly summary"""
        daily_inspiration_rate = self.tasks_component.get_daily_inspiration_rate()
        return {
            "children": [
                self.create_intro_section_block(int(daily_inspiration_rate['current']), int(daily_inspiration_rate['previous'])),
                self.create_my_input_section_block(),
                create_separator_block(),
                create_separator_block(),
                create_paragraph_block(""),

                self.goal_component.create_notion_section(),
                create_separator_block(),
                create_paragraph_block(""),

                self.health_component.create_notion_section(),
                create_separator_block(),
                create_paragraph_block(""),

                self.tasks_component.create_notion_section(),
                create_separator_block(),
                create_paragraph_block(""),

                self.finances_component.create_notion_section(),
                create_separator_block(),
                create_paragraph_block(""),

                # self.development_component.create_notion_section()
            ]
        }

    def create_intro_section_block(self, daily_inspiration_rate, previous_inspiration_rate):
        icon = "🆙" if daily_inspiration_rate >= previous_inspiration_rate else "🔽"
        daily_inspiration_str = f"{daily_inspiration_rate}%"
        previous_inspiration_str = f"{previous_inspiration_rate}%"
        return create_three_column_layout(
            create_callout_block([create_heading_2_block(daily_inspiration_str),
                                  create_paragraph_block(f"{icon} Previous rate: {previous_inspiration_str}",
                                                         bold_word=previous_inspiration_str)],
                                 "Open Notion Daily"),
            create_paragraph_block(""),
            create_paragraph_block(""))

    def create_my_input_section_block(self):
        return create_toggle_heading_block(
            "👮🏼 My monthly input",
            [create_paragraph_block("")],
            heading_number=2
        )


@track_operation(NotionAPIOperation.CREATE_MONTHLY_SUMMARY)
def create_monthly_summary_page(target_date: Optional[date] = None) -> Dict:
    """Creates a monthly summary page in Notion

    Args:
        target_date: Optional target date (defaults to previous month)
    """
    if target_date is None:
        # Default to creating summary for previous month
        today = date.today()
        if today.month == 1:
            target_date = date(today.year - 1, 12, 1)
        else:
            target_date = date(today.year, today.month - 1, 1)

    try:
        # Initialize components
        health_component = HealthComponent(Keys.garmin_db_id, target_date=target_date)
        tasks_component = TasksComponent(Keys.daily_tasks_db_id, Keys.tasks_db_id, target_date=target_date)
        finances_component = FinancesComponent(Keys.expense_tracker_db_id, Keys.monthly_category_expense_db,
                                               Keys.monthly_expenses_summary_previous_month_view_link,
                                               target_date=target_date)
        development_component = DevelopmentComponent(Keys.book_summaries_db_id, Keys.daily_tasks_db_id,
                                                     target_date=target_date)
        goal_component = GoalComponent(Keys.goals_db_id, Keys.goals_view_link, target_date=target_date)

        # Create summary object
        summary = MonthlySummary(
            target_date=target_date,
            health_component=health_component,
            tasks_component=tasks_component,
            finances_component=finances_component,
            development_component=development_component,
            goal_component=goal_component
        )

        # Create page
        page_data = {
            "Name": f"Monthly Summary - {target_date.strftime('%B %Y')}",
            "Date": target_date.isoformat(),
            "Icon": generate_icon_url(IconType.CHECKLIST, IconColor.BLUE)
        }

        response = create_page_with_db_dict_and_children_block(
            Keys.monthly_summaries_db_id,
            page_data,
            summary.generate_children_block()
        )

        logger.info(f"Successfully created monthly summary for {target_date.strftime('%B %Y')}")
        return response

    except Exception as e:
        logger.error(f"Error creating monthly summary page: {str(e)}")
        raise