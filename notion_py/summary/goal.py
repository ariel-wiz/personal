from collections import defaultdict
from typing import Dict, Optional, List
from datetime import date

from notion_py.helpers.notion_children_blocks import create_three_column_layout, create_toggle_heading_block, \
    create_section_text_with_bullet
from notion_py.summary.base_component import BaseComponent


class GoalFields:
    """Constants for goal field names"""
    TOTAL_GOALS = "total_goals"
    COMPLETED_GOALS = "completed_goals"
    COMPLETION_RATE = "completion_rate"
    GOALS_BY_CATEGORY = "goals_by_category"
    DEADLINE_STATUS = "deadline_status"
    NAME = "name"


class GoalComponent(BaseComponent):
    def __init__(self, goals_db_id: str, target_date: Optional[date] = None):
        super().__init__(target_date, GoalFields)
        self.goals_db_id = goals_db_id

    def _initialize_metrics(self):
        """Initialize goal metrics for current and previous months"""
        self._current_metrics = self._get_month_metrics(self.target_date)
        self._previous_metrics = self._get_month_metrics(self.previous_month)

    def _get_month_metrics(self, target_date: date) -> Dict:
        """Get goal metrics for a given month"""
        goals = self._get_pages_for_month(self.goals_db_id, target_date, "Due")
        return {
            GoalFields.TOTAL_GOALS: len(goals),
            GoalFields.COMPLETED_GOALS: len([g for g in goals if self._is_goal_completed(g)]),
            GoalFields.GOALS_BY_CATEGORY: self._get_goals_by_category(goals),
            GoalFields.DEADLINE_STATUS: self._get_deadline_statuses(goals)
        }

    def create_notion_section(self) -> dict:
        """Creates Notion blocks for goals section"""
        metrics = self.get_metrics()

        goals = create_section_text_with_bullet("Goals:", metrics[GoalFields.NAME])
        # Create three column layout for goals overview
        return create_toggle_heading_block(
            "⛰️ Goals",
            [*goals],
            heading_number=2
        )

    def _is_goal_completed(self, goal: Dict) -> bool:
        """Check if a goal is marked as completed"""
        return goal['properties'].get('Done', {}).get('checkbox', False)

    def _get_goals_by_category(self, goals: List[Dict]) -> Dict[str, int]:
        """Group goals by their category/setting"""
        categories = defaultdict(int)
        for goal in goals:
            category = goal['properties'].get('Goal Setting', {}).get('title', [{}])[0].get('plain_text',
                                                                                            'Uncategorized')
            categories[category] += 1
        return dict(categories)

    def _get_deadline_statuses(self, goals: List[Dict]) -> Dict[str, int]:
        """Get count of goals by deadline status"""
        statuses = defaultdict(int)
        for goal in goals:
            status = goal['properties'].get('Deadline Status', {}).get('formula', {}).get('string', 'No Status')
            statuses[status] += 1
        return dict(statuses)
