from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Optional, List
from datetime import date, datetime

from common import today
from notion_py.helpers.notion_children_blocks import create_three_column_layout, create_toggle_heading_block, \
    create_section_text_with_bullet, create_paragraph_block, create_heading_3_block, create_bullet_list, \
    create_separator_block
from notion_py.helpers.notion_common import get_db_pages
from notion_py.summary.base_component import BaseComponent


@dataclass
class Goal:
    id: str
    name: str
    deadline: str
    done: bool
    icon: str
    deadline_status: str
    created_time: str
    last_edited_time: str
    goal_setting_id: str
    url: str

    @property
    def days_until_deadline(self) -> int:
        """Calculate days between today and the deadline"""
        deadline_date = datetime.strptime(self.deadline, '%Y-%m-%d').date()
        today = date.today()
        return (deadline_date - today).days

    @property
    def relative_deadline(self) -> str:
        """Get a human-readable relative deadline"""
        days = self.days_until_deadline
        if days < 0:
            return f"{abs(days)} days overdue"
        elif days == 0:
            return "Due today"
        else:
            return f"{days} days remaining"


def create_goals_from_notion_data(notion_data: List[dict]) -> List[Goal]:
    goals = []

    for item in notion_data:
        # Extract properties
        props = item['properties']

        # Create Goal instance
        goal = Goal(
            id=item['id'],
            name=props['Name']['title'][0]['text']['content'],
            deadline=props['Deadline']['date']['start'],
            done=props['Done']['checkbox'],
            icon=props['Icon']['rollup']['array'][0]['rich_text'][0]['text']['content'],
            deadline_status=props['Deadline Status']['formula']['string'],
            created_time=props['Created time']['created_time'],
            last_edited_time=props['Last edited time']['last_edited_time'],
            goal_setting_id=props['Goal Setting']['relation'][0]['id'],
            url=item['url']
        )
        goals.append(goal)

    return goals


class GoalFields:
    """Constants for goal field names"""
    ALL_PENDING = "all_pending"
    COMPLETED_GOALS = "completed_goals"
    DELAYED = "delayed"
    NEXT_GOALS = "next_goals"


class GoalComponent(BaseComponent):
    def __init__(self, goals_db_id: str, goals_view_link: str, target_date: Optional[date] = None):
        super().__init__(target_date, GoalFields)
        self.goals_db_id = goals_db_id
        self.goals_view_link = goals_view_link

    def _initialize_metrics(self):
        """Initialize goal metrics for current and previous months"""
        self._current_metrics = self._get_month_metrics(self.target_date)
        self._previous_metrics = self._current_metrics

    def _get_month_metrics(self, target_date: date) -> Dict:
        """Get goal metrics for a given month"""
        goal_filter = {
            "or": [
                # First group - for goals in progress
                {
                    "and": [
                        {
                            "property": "Deadline Status",
                            "formula": {
                                "string": {
                                    "is_not_empty": True
                                }
                            }
                        },
                        {
                            "property": "Deadline Status",
                            "formula": {
                                "string": {
                                    "does_not_contain": "Done"
                                }
                            }
                        }
                    ]
                },
                # Second group - for completed goals
                {
                    "and": [
                        {
                            "property": "Last edited time",
                            "date": {
                                "on_or_after": f"{target_date.isoformat()}T00:00:00Z"
                            }
                        },
                        {
                            "property": "Deadline Status",
                            "formula": {
                                "string": {
                                    "contains": "Done"
                                }
                            }
                        }
                    ]
                }
            ]
        }
        goals_page = get_db_pages(self.goals_db_id, {"filter": goal_filter})
        goals = create_goals_from_notion_data(goals_page)

        def get_deadline_date(goal):
            return datetime.strptime(goal.deadline, '%Y-%m-%d').date()

        # Total goals not done
        pending_goals = sorted(
            [goal for goal in goals if not goal.done],
            key=lambda x: x.deadline
        )

        # Format the output
        all_pending_goals = [
            f"{goal.icon} {goal.name} ➡️ {goal.deadline} ({goal.relative_deadline})"
            for goal in pending_goals
        ]

        # Completed goals
        completed_goals = sorted([
            goal for goal in goals
            if goal.done
        ],
            key=lambda x: x.deadline)
        completed_goals_names = [f"{goal.icon} {goal.name}" for goal in completed_goals]

        # Goals delayed (not done and deadline before today)
        goals_delayed = sorted([
            goal for goal in goals
            if not goal.done and get_deadline_date(goal) < today
        ],
            key=lambda x: x.deadline)
        goals_delayed_names = [f"{goal.icon} {goal.name} -> {goal.relative_deadline}" for goal in goals_delayed]

        # Next goals (not done, deadline after today, sorted by deadline)
        next_goals = sorted(
            [goal for goal in goals
             if not goal.done and get_deadline_date(goal) >= today],
            key=lambda x: x.deadline
        )
        next_goals_names = [f"{goal.icon} {goal.name} -> {goal.deadline} ({goal.relative_deadline})" for goal in
                            next_goals]

        return {
            GoalFields.ALL_PENDING: all_pending_goals,
            GoalFields.COMPLETED_GOALS: completed_goals_names,
            GoalFields.DELAYED: goals_delayed_names,
            GoalFields.NEXT_GOALS: next_goals_names
        }

    def create_notion_section(self) -> dict:
        """Creates Notion blocks for goals section"""
        metrics = self.get_metrics()
        blocks = []

        if len(metrics[GoalFields.COMPLETED_GOALS]['current']) > 0:
            completed_goals_block = [f"👏🏼👏🏼 - {goal}" for goal in metrics[GoalFields.COMPLETED_GOALS]['current']]
            blocks.append(create_toggle_heading_block(
                "✅⛰️Completed Goals",
                create_bullet_list(completed_goals_block)))
            blocks.append(create_paragraph_block(""))
            blocks.append(create_separator_block())

        if len(metrics[GoalFields.ALL_PENDING]['current']) > 0:
            for i, pending_goal in enumerate(metrics[GoalFields.ALL_PENDING]['current']):
                first_part, second_part = pending_goal.split(" ➡️")
                days_part = "(" + second_part.split("(")[1].split(")")[0] + ")"
                if "overdue" in days_part:
                    color = "red"
                else:
                    color = "default"
                color_data = [{"color": color, "words": days_part}]

                blocks.append(
                    create_paragraph_block(f"{i} - {pending_goal}", bold_word=first_part, color_list=color_data)
                )

        # Create three column layout for goals overview
        return create_toggle_heading_block(
            "⛰️ Goals - 🔗",
            [block for block in blocks if block is not None],
            heading_number=2,
            link_url={
                "url": self.goals_view_link,
                "subword": "🔗"
            }
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
